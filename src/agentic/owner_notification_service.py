"""
Owner Notification Service - Smart alerts for autonomous operation

This service decides what AlleyBot should tell the owner about,
and how/when to deliver those notifications.

Key design principles:
- AlleyBot operates autonomously by default
- Only meaningful events trigger notifications
- Respect owner attention (no spam)
- Critical events require immediate delivery
- Normal events can be batched into digests

This enables the "autonomous on his own, update me when needed" mode.
"""

import os
import json
import sqlite3
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from src.agentic.contracts import (
    OwnerNotification,
    NotificationPriority,
    ActionOutcome,
    WorkItem,
)


class OwnerNotificationService:
    """
    Intelligent owner notification system for autonomous AlleyBot.
    
    This service manages the flow of information from AlleyBot to owner:
    - Decides what's worth notifying about
    - Prioritizes notifications
    - Batches lower-priority items
    - Handles immediate alerts for critical events
    - Respects quiet hours and notification preferences
    
    Usage:
        service = get_owner_notification_service()
        
        # From anywhere in AlleyBot:
        await service.notify(
            title="High-impact action completed",
            message="Posted market analysis to MoltX",
            priority=NotificationPriority.NORMAL,
            source_action="moltx:post"
        )
    """
    
    # Minimum time between non-critical notifications (minutes)
    DEFAULT_DIGEST_INTERVAL_MINUTES = 30
    
    # Maximum batch size before forcing delivery
    MAX_BATCH_SIZE = 10
    
    # Quiet hours (optional, 24h format)
    DEFAULT_QUIET_START = 22  # 10 PM
    DEFAULT_QUIET_END = 8     # 8 AM
    
    def __init__(
        self,
        telegram_plugin=None,
        db_path: str = "data/notifications.db",
    ):
        """
        Initialize owner notification service.
        
        Args:
            telegram_plugin: Telegram plugin instance for delivery
            db_path: SQLite DB for notification persistence
        """
        self.telegram = telegram_plugin
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # Settings from environment
        self.enabled = os.getenv("OWNER_NOTIFICATIONS_ENABLED", "true").lower() == "true"
        self.notify_only_mode = os.getenv("OWNER_NOTIFY_ONLY_MODE", "true").lower() == "true"
        self.digest_interval = int(os.getenv("NOTIFICATION_DIGEST_INTERVAL_MINUTES", self.DEFAULT_DIGEST_INTERVAL_MINUTES))
        self.quiet_start = int(os.getenv("NOTIFICATION_QUIET_START", self.DEFAULT_QUIET_START))
        self.quiet_end = int(os.getenv("NOTIFICATION_QUIET_END", self.DEFAULT_QUIET_END))
        
        # Pending notifications queue
        self._pending: List[OwnerNotification] = []
        self._last_digest_time = datetime.now()
        
        # Start background digest task
        self._digest_task: Optional[asyncio.Task] = None
        
        print(f"✅ Owner Notification Service initialized")
        print(f"   Mode: {'notify-only' if self.notify_only_mode else 'chatty'}")
        print(f"   Enabled: {self.enabled}")
        print(f"   Digest interval: {self.digest_interval}min")
    
    def _init_database(self) -> None:
        """Initialize SQLite schema for notification persistence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    source_action TEXT,
                    source_work_item TEXT,
                    requires_acknowledgement INTEGER,
                    requires_approval INTEGER,
                    batched INTEGER,
                    digest_group TEXT,
                    delivered INTEGER,
                    delivered_at TEXT,
                    acknowledged INTEGER,
                    acknowledged_at TEXT
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON notifications(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_delivered ON notifications(delivered)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON notifications(timestamp)")
            conn.commit()
    
    def _row_to_notification(self, row: tuple) -> OwnerNotification:
        """Convert DB row to OwnerNotification."""
        (
            id_, timestamp, priority, title, message, details,
            source_action, source_work_item, requires_ack, requires_approval,
            batched, digest_group, delivered, delivered_at, acknowledged, acknowledged_at
        ) = row
        
        return OwnerNotification(
            id=id_,
            timestamp=timestamp,
            priority=NotificationPriority(priority),
            title=title,
            message=message,
            details=json.loads(details) if details else {},
            source_action=source_action,
            source_work_item=source_work_item,
            requires_acknowledgement=bool(requires_ack),
            requires_approval=bool(requires_approval),
            batched=bool(batched),
            digest_group=digest_group,
            delivered=bool(delivered),
            delivered_at=delivered_at,
            acknowledged=bool(acknowledged),
            acknowledged_at=acknowledged_at,
        )
    
    def _notification_to_row(self, n: OwnerNotification) -> tuple:
        """Convert OwnerNotification to DB row."""
        return (
            n.id, n.timestamp, n.priority.value, n.title, n.message,
            json.dumps(n.details) if n.details else None,
            n.source_action, n.source_work_item,
            int(n.requires_acknowledgement), int(n.requires_approval),
            int(n.batched), n.digest_group,
            int(n.delivered), n.delivered_at,
            int(n.acknowledged), n.acknowledged_at,
        )
    
    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        now = datetime.now().hour
        if self.quiet_start > self.quiet_end:  # Crosses midnight
            return now >= self.quiet_start or now < self.quiet_end
        return self.quiet_start <= now < self.quiet_end
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    
    async def notify(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        details: Optional[Dict[str, Any]] = None,
        source_action: Optional[str] = None,
        source_work_item: Optional[str] = None,
        requires_acknowledgement: bool = False,
        requires_approval: bool = False,
    ) -> bool:
        """
        Send or queue an owner notification.
        
        Args:
            title: Short title/summary
            message: Full message content
            priority: CRITICAL, HIGH, NORMAL, or LOW
            details: Additional structured data
            source_action: What action triggered this
            source_work_item: Associated work item if any
            requires_acknowledgement: Owner must acknowledge
            requires_approval: Owner must approve before proceeding
            
        Returns:
            True if notification was sent/queued successfully
        """
        if not self.enabled:
            return False
        
        # Create notification record
        notification = OwnerNotification(
            id=f"notif_{uuid.uuid4().hex[:10]}",
            timestamp=datetime.now().isoformat(),
            priority=priority,
            title=title,
            message=message,
            details=details or {},
            source_action=source_action,
            source_work_item=source_work_item,
            requires_acknowledgement=requires_acknowledgement,
            requires_approval=requires_approval,
        )
        
        # Persist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO notifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                self._notification_to_row(notification)
            )
            conn.commit()
        
        # Route based on priority
        if priority in (NotificationPriority.CRITICAL, NotificationPriority.HIGH):
            return await self._send_immediate(notification)
        
        # Queue for digest
        notification.batched = True
        self._pending.append(notification)
        
        # Check if digest should be sent
        if len(self._pending) >= self.MAX_BATCH_SIZE:
            await self._send_digest()
        
        return True
    
    async def notify_from_action(
        self,
        outcome: ActionOutcome,
        work_item: Optional[WorkItem] = None,
    ) -> bool:
        """
        Auto-generate notification from action outcome.
        
        Decides if/when to notify based on action impact and outcome.
        """
        if not self.enabled:
            return False
        
        # Determine priority from action outcome
        priority = self._determine_action_priority(outcome)
        
        if not priority:
            return False  # Not worth notifying
        
        title = f"Action: {outcome.action_id}"
        if outcome.success:
            title = f"✅ Completed: {outcome.action_type}"
            message = f"Successfully executed {outcome.action_id}"
        else:
            title = f"❌ Failed: {outcome.action_type}"
            message = f"Action {outcome.action_id} failed: {outcome.error or 'Unknown error'}"
        
        return await self.notify(
            title=title,
            message=message,
            priority=priority,
            details={
                "success": outcome.success,
                "execution_time_ms": outcome.execution_time_ms,
                "stage": outcome.stage,
            },
            source_action=outcome.action_id,
            source_work_item=work_item.id if work_item else None,
        )
    
    def _determine_action_priority(
        self,
        outcome: ActionOutcome,
    ) -> Optional[NotificationPriority]:
        """
        Determine if an action outcome warrants notification.
        
        Returns priority or None if no notification needed.
        """
        # Always notify on failure
        if not outcome.success:
            # Check if it's a critical stage failure
            if outcome.stage in ('agi_validation', 'symod_verification', 'synergy_validation'):
                return NotificationPriority.HIGH
            return NotificationPriority.NORMAL
        
        # Success - only notify for meaningful actions
        action_type = outcome.action_type.lower()
        
        # High-impact action types
        high_impact_types = [
            'post', 'engage', 'debate', 'trade', 'buy', 'sell',
            'transfer', 'upgrade', 'self_improve', 'auto_fix',
        ]
        
        if any(t in action_type for t in high_impact_types):
            # Check prediction evaluation for unexpected outcomes
            if outcome.prediction_evaluation:
                mismatch = outcome.prediction_evaluation.get('mismatch_score', 0)
                if mismatch > 0.5:  # Unexpected outcome
                    return NotificationPriority.HIGH
            
            return NotificationPriority.NORMAL
        
        # Low priority for routine actions
        routine_types = ['analyze', 'check', 'monitor', 'ping']
        if any(t in action_type for t in routine_types):
            return NotificationPriority.LOW
        
        # Don't notify for very low-level actions
        return None
    
    async def _send_immediate(self, notification: OwnerNotification) -> bool:
        """Send notification immediately (for CRITICAL/HIGH)."""
        if self._is_quiet_hours() and notification.priority != NotificationPriority.CRITICAL:
            # Defer to digest during quiet hours (unless critical)
            notification.batched = True
            self._pending.append(notification)
            print(f"⏳ [Quiet hours] Deferred notification: {notification.title}")
            return True
        
        if not self.telegram:
            print(f"⚠️ No Telegram plugin for notification: {notification.title}")
            return False
        
        try:
            # Build formatted message
            emoji = "🚨" if notification.priority == NotificationPriority.CRITICAL else "⚠️"
            text = f"{emoji} **{notification.title}**\n\n{notification.message}"
            
            if notification.details:
                text += f"\n\nDetails: {json.dumps(notification.details, indent=2)[:200]}"
            
            # Send via Telegram
            if hasattr(self.telegram, 'send_message_to_owner_sync'):
                self.telegram.send_message_to_owner_sync(text)
            elif hasattr(self.telegram, 'send_alert'):
                self.telegram.send_alert(
                    category=notification.priority.value.upper(),
                    message=text,
                    priority=notification.priority.value,
                )
            
            # Mark delivered
            notification.delivered = True
            notification.delivered_at = datetime.now().isoformat()
            self._update_notification(notification)
            
            print(f"📤 Sent {notification.priority.value} notification: {notification.title}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
            return False
    
    async def _send_digest(self) -> bool:
        """Send batched digest of pending notifications."""
        if not self._pending:
            return True
        
        if not self.telegram:
            print(f"⚠️ No Telegram plugin for digest")
            return False
        
        # Check if enough time has passed
        now = datetime.now()
        minutes_since_last = (now - self._last_digest_time).total_seconds() / 60
        
        if minutes_since_last < self.digest_interval and len(self._pending) < self.MAX_BATCH_SIZE:
            return True  # Wait for more items or interval
        
        try:
            # Build digest message
            sections = []
            
            # Group by priority
            high_items = [n for n in self._pending if n.priority == NotificationPriority.HIGH]
            normal_items = [n for n in self._pending if n.priority == NotificationPriority.NORMAL]
            low_items = [n for n in self._pending if n.priority == NotificationPriority.LOW]
            
            if high_items:
                sections.append("⚠️ **High Priority**")
                for n in high_items[:3]:  # Max 3 high
                    sections.append(f"• {n.title}")
            
            if normal_items:
                sections.append(f"\n📋 **Updates ({len(normal_items)})**")
                for n in normal_items[:5]:  # Max 5 normal
                    sections.append(f"• {n.title}")
            
            if low_items:
                sections.append(f"\n💤 **Low Priority ({len(low_items)})**")
            
            text = "🦞 **AlleyBot Digest**\n" + "\n".join(sections)
            
            # Send
            if hasattr(self.telegram, 'send_message_to_owner_sync'):
                self.telegram.send_message_to_owner_sync(text)
            
            # Mark all as delivered
            for n in self._pending:
                n.delivered = True
                n.delivered_at = now.isoformat()
                self._update_notification(n)
            
            print(f"📤 Sent digest with {len(self._pending)} notifications")
            self._pending = []
            self._last_digest_time = now
            return True
            
        except Exception as e:
            print(f"❌ Failed to send digest: {e}")
            return False
    
    def _update_notification(self, notification: OwnerNotification) -> None:
        """Update notification in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE notifications SET
                    delivered = ?, delivered_at = ?, acknowledged = ?, acknowledged_at = ?
                WHERE id = ?""",
                (
                    int(notification.delivered), notification.delivered_at,
                    int(notification.acknowledged), notification.acknowledged_at,
                    notification.id
                )
            )
            conn.commit()
    
    # ------------------------------------------------------------------
    # Convenience Methods
    # ------------------------------------------------------------------
    
    async def notify_critical(self, title: str, message: str, **kwargs) -> bool:
        """Send critical priority notification."""
        return await self.notify(title, message, NotificationPriority.CRITICAL, **kwargs)
    
    async def notify_high(self, title: str, message: str, **kwargs) -> bool:
        """Send high priority notification."""
        return await self.notify(title, message, NotificationPriority.HIGH, **kwargs)
    
    async def notify_normal(self, title: str, message: str, **kwargs) -> bool:
        """Send normal priority notification."""
        return await self.notify(title, message, NotificationPriority.NORMAL, **kwargs)
    
    async def notify_low(self, title: str, message: str, **kwargs) -> bool:
        """Send low priority notification."""
        return await self.notify(title, message, NotificationPriority.LOW, **kwargs)
    
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    
    async def start_digest_loop(self) -> None:
        """Start background task for periodic digest sending."""
        if self._digest_task:
            return
        
        async def digest_loop():
            while True:
                await asyncio.sleep(60 * self.digest_interval)
                if self._pending:
                    await self._send_digest()
        
        self._digest_task = asyncio.create_task(digest_loop())
        print("🔄 Started notification digest loop")
    
    def stop_digest_loop(self) -> None:
        """Stop background digest task."""
        if self._digest_task:
            self._digest_task.cancel()
            self._digest_task = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE delivered = 0"
            ).fetchone()[0]
            by_priority = conn.execute(
                "SELECT priority, COUNT(*) FROM notifications GROUP BY priority"
            ).fetchall()
        
        return {
            "total": total,
            "pending_delivery": pending,
            "queued": len(self._pending),
            "by_priority": {p: c for p, c in by_priority},
            "enabled": self.enabled,
            "notify_only_mode": self.notify_only_mode,
            "digest_interval": self.digest_interval,
        }


# Singleton instance
_owner_notification_service: Optional[OwnerNotificationService] = None


def get_owner_notification_service(
    telegram_plugin=None,
    db_path: str = "data/notifications.db",
) -> OwnerNotificationService:
    """Get or create singleton."""
    global _owner_notification_service
    if _owner_notification_service is None:
        _owner_notification_service = OwnerNotificationService(telegram_plugin, db_path)
    return _owner_notification_service


def reset_owner_notification_service() -> None:
    """Reset singleton."""
    global _owner_notification_service
    _owner_notification_service = None
