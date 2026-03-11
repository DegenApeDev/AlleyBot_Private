"""
Work Item Service - Durable execution control for AlleyBot

This service provides persistent work item management that survives
restarts, enabling true continuity of goals and intentions.

Work items are the primary unit of meaningful autonomous work.
They represent durable intentions that AlleyBot pursues across
cycles, not just reactive responses.

This service integrates with:
- AGI Kernel for capability evaluation
- ActionRouter for execution
- Memory system for persistence
- Owner notification for high-impact work
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from src.agentic.contracts import WorkItem, WorkItemState, CapabilityJudgment


class WorkItemService:
    """
    Durable work item management for persistent autonomous execution.
    
    This service manages the lifecycle of work items from creation
    through completion, including:
    - Creation from goals, opportunities, or events
    - State transitions (active, blocked, waiting, completed)
    - Capability evaluation (can execute now?)
    - Priority management and scheduling
    - Persistence across restarts
    - Integration with action execution
    """
    
    def __init__(self, db_path: str = "data/work_items.db"):
        """
        Initialize work item service with SQLite persistence.
        
        Args:
            db_path: Path to SQLite database for work item storage
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # In-memory cache for active work
        self._active_items: Dict[str, WorkItem] = {}
        self._load_active_items()
        
        print(f"✅ Work Item Service initialized - DB: {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialize SQLite schema for work item persistence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    state TEXT NOT NULL,
                    work_type TEXT,
                    goal_id TEXT,
                    parent_id TEXT,
                    priority INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT,
                    due_at TEXT,
                    capability_judgment TEXT,
                    attempts INTEGER DEFAULT 0,
                    last_attempt_at TEXT,
                    last_error TEXT,
                    source_signal TEXT,
                    required_plugins TEXT,
                    required_context TEXT,
                    completion_criteria TEXT,
                    success_metrics TEXT
                )
            """)
            
            # Index for efficient queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON work_items(state)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON work_items(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_goal_id ON work_items(goal_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_updated ON work_items(updated_at)")
            
            conn.commit()
    
    def _load_active_items(self) -> None:
        """Load active and blocked work items into memory cache."""
        items = self.get_items_by_states([WorkItemState.ACTIVE, WorkItemState.BLOCKED])
        self._active_items = {item.id: item for item in items}
        print(f"📋 Loaded {len(self._active_items)} active/blocked work items")
    
    def _row_to_work_item(self, row: tuple) -> WorkItem:
        """Convert database row to WorkItem dataclass."""
        (
            id_, title, description, state, work_type, goal_id, parent_id,
            priority, created_at, updated_at, due_at, capability_judgment,
            attempts, last_attempt_at, last_error, source_signal,
            required_plugins, required_context, completion_criteria, success_metrics
        ) = row
        
        return WorkItem(
            id=id_,
            title=title,
            description=description or "",
            state=WorkItemState(state),
            work_type=work_type or "goal",
            goal_id=goal_id,
            parent_id=parent_id,
            priority=priority,
            created_at=created_at,
            updated_at=updated_at,
            due_at=due_at,
            capability_judgment=json.loads(capability_judgment) if capability_judgment else None,
            attempts=attempts,
            last_attempt_at=last_attempt_at,
            last_error=last_error,
            source_signal=json.loads(source_signal) if source_signal else None,
            required_plugins=json.loads(required_plugins) if required_plugins else [],
            required_context=json.loads(required_context) if required_context else {},
            completion_criteria=completion_criteria,
            success_metrics=json.loads(success_metrics) if success_metrics else {},
        )
    
    def _work_item_to_row(self, item: WorkItem) -> tuple:
        """Convert WorkItem to database row tuple."""
        return (
            item.id,
            item.title,
            item.description,
            item.state.value,
            item.work_type,
            item.goal_id,
            item.parent_id,
            item.priority,
            item.created_at,
            item.updated_at,
            item.due_at,
            json.dumps(item.capability_judgment) if item.capability_judgment else None,
            item.attempts,
            item.last_attempt_at,
            item.last_error,
            json.dumps(item.source_signal) if item.source_signal else None,
            json.dumps(item.required_plugins) if item.required_plugins else None,
            json.dumps(item.required_context) if item.required_context else None,
            item.completion_criteria,
            json.dumps(item.success_metrics) if item.success_metrics else None,
        )
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    
    def create_work_item(
        self,
        title: str,
        description: str,
        work_type: str = "goal",
        goal_id: Optional[str] = None,
        priority: int = 1,
        source_signal: Optional[Dict] = None,
        required_plugins: Optional[List[str]] = None,
        due_at: Optional[str] = None,
    ) -> WorkItem:
        """
        Create a new work item.
        
        Args:
            title: Short title of the work
            description: Detailed description
            work_type: Type of work (goal, opportunity, maintenance, etc.)
            goal_id: Associated goal ID if any
            priority: Priority (1 = highest)
            source_signal: What triggered this work item
            required_plugins: Plugins needed to execute
            due_at: Optional due date (ISO format)
            
        Returns:
            Created WorkItem
        """
        now = datetime.now().isoformat()
        
        item = WorkItem(
            id=f"wi_{uuid.uuid4().hex[:12]}",
            title=title,
            description=description,
            state=WorkItemState.ACTIVE,
            work_type=work_type,
            goal_id=goal_id,
            priority=priority,
            created_at=now,
            updated_at=now,
            due_at=due_at,
            source_signal=source_signal,
            required_plugins=required_plugins or [],
        )
        
        # Persist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO work_items VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )""",
                self._work_item_to_row(item)
            )
            conn.commit()
        
        # Add to cache
        self._active_items[item.id] = item
        
        print(f"📌 Created work item: {item.id} - {title}")
        return item
    
    def get_item(self, item_id: str) -> Optional[WorkItem]:
        """Get a specific work item by ID."""
        # Check cache first
        if item_id in self._active_items:
            return self._active_items[item_id]
        
        # Load from database
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM work_items WHERE id = ?",
                (item_id,)
            ).fetchone()
            
            if row:
                return self._row_to_work_item(row)
        
        return None
    
    def get_items_by_states(self, states: List[WorkItemState]) -> List[WorkItem]:
        """Get all work items in specified states."""
        state_values = [s.value for s in states]
        
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ",".join("?" * len(state_values))
            rows = conn.execute(
                f"SELECT * FROM work_items WHERE state IN ({placeholders}) ORDER BY priority, created_at",
                state_values
            ).fetchall()
            
            return [self._row_to_work_item(row) for row in rows]
    
    def get_active_items(self) -> List[WorkItem]:
        """Get all active work items, sorted by priority."""
        return self.get_items_by_states([WorkItemState.ACTIVE])
    
    def get_executable_items(self) -> List[WorkItem]:
        """
        Get work items that are ready to execute.
        
        Filters for:
        - ACTIVE state
        - capability_judgment.can_execute_now = True
        Sorted by priority
        """
        active = self.get_active_items()
        executable = []
        
        for item in active:
            if item.capability_judgment:
                if item.capability_judgment.get("can_execute_now", False):
                    executable.append(item)
        
        return executable
    
    def update_item_state(
        self,
        item_id: str,
        new_state: WorkItemState,
        error: Optional[str] = None,
    ) -> Optional[WorkItem]:
        """
        Update work item state.
        
        Args:
            item_id: Work item ID
            new_state: New state to transition to
            error: Optional error message if transitioning to BLOCKED
            
        Returns:
            Updated WorkItem or None if not found
        """
        item = self.get_item(item_id)
        if not item:
            return None
        
        old_state = item.state
        item.state = new_state
        item.updated_at = datetime.now().isoformat()
        
        if new_state == WorkItemState.BLOCKED and error:
            item.last_error = error
        
        if new_state == WorkItemState.ACTIVE:
            item.last_error = None  # Clear error when unblocking
        
        # Update attempts
        if new_state == WorkItemState.COMPLETED:
            item.attempts += 1
            item.last_attempt_at = datetime.now().isoformat()
        
        # Persist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE work_items SET
                    state = ?, updated_at = ?, last_error = ?, attempts = ?, last_attempt_at = ?
                WHERE id = ?""",
                (item.state.value, item.updated_at, item.last_error, item.attempts, item.last_attempt_at, item.id)
            )
            conn.commit()
        
        # Update cache
        if new_state in (WorkItemState.ACTIVE, WorkItemState.BLOCKED):
            self._active_items[item.id] = item
        elif item.id in self._active_items:
            del self._active_items[item.id]
        
        print(f"📋 Work item {item.id}: {old_state.value} -> {new_state.value}")
        return item
    
    def update_capability_judgment(
        self,
        item_id: str,
        judgment: Dict[str, Any],
    ) -> Optional[WorkItem]:
        """
        Update capability judgment for a work item.
        
        Args:
            item_id: Work item ID
            judgment: Capability judgment from AGI Kernel
            
        Returns:
            Updated WorkItem or None
        """
        item = self.get_item(item_id)
        if not item:
            return None
        
        item.capability_judgment = judgment
        item.updated_at = datetime.now().isoformat()
        
        # Auto-transition based on judgment
        if judgment.get("can_execute_now", False) and item.state == WorkItemState.BLOCKED:
            item.state = WorkItemState.ACTIVE
            item.last_error = None
            print(f"📋 Work item {item.id} auto-unblocked (now executable)")
        
        if judgment.get("needs_new_skill") and not judgment.get("upgrade_eligible", False):
            if item.state == WorkItemState.ACTIVE:
                item.state = WorkItemState.WAITING
                print(f"📋 Work item {item.id} auto-waiting (needs new skill)")
        
        # Persist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE work_items SET
                    capability_judgment = ?, state = ?, updated_at = ?, last_error = ?
                WHERE id = ?""",
                (json.dumps(judgment), item.state.value, item.updated_at, item.last_error, item.id)
            )
            conn.commit()
        
        # Update cache
        if item.state in (WorkItemState.ACTIVE, WorkItemState.BLOCKED):
            self._active_items[item.id] = item
        elif item.id in self._active_items:
            del self._active_items[item.id]
        
        return item
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a work item (use with caution)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM work_items WHERE id = ?", (item_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                if item_id in self._active_items:
                    del self._active_items[item_id]
                print(f"🗑️ Deleted work item: {item_id}")
                return True
        
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of work items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT state, COUNT(*) FROM work_items GROUP BY state
            """)
            state_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total": sum(state_counts.values()),
            "by_state": state_counts,
            "active": state_counts.get(WorkItemState.ACTIVE.value, 0),
            "blocked": state_counts.get(WorkItemState.BLOCKED.value, 0),
            "waiting": state_counts.get(WorkItemState.WAITING.value, 0),
            "completed": state_counts.get(WorkItemState.COMPLETED.value, 0),
            "executable": len(self.get_executable_items()),
            "cache_size": len(self._active_items),
        }
    
    def get_next_executable(self) -> Optional[WorkItem]:
        """
        Get the highest-priority executable work item.
        
        Returns None if no executable items exist.
        """
        executable = self.get_executable_items()
        if not executable:
            return None
        
        # Return highest priority (lowest number)
        return min(executable, key=lambda x: x.priority)


# Singleton instance
_work_item_service: Optional[WorkItemService] = None


def get_work_item_service(db_path: str = "data/work_items.db") -> WorkItemService:
    """Get or create work item service singleton."""
    global _work_item_service
    if _work_item_service is None:
        _work_item_service = WorkItemService(db_path)
    return _work_item_service


def reset_work_item_service() -> None:
    """Reset singleton (mainly for testing)."""
    global _work_item_service
    _work_item_service = None
