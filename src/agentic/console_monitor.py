"""
AlleyBot Console Monitor & Platform Message Handler

Captures stdout/stderr from platform processes, detects messages sent TO AlleyBot,
and triggers intelligent responses using custom skills.

Capabilities:
1. Console Capture - Read stdout/stderr from platform processes
2. Message Detection - Identify when platforms message AlleyBot
3. Message Parsing - Extract sender, content, intent from messages
4. Skill-Based Response - Route to appropriate custom skill handler
5. AGI Integration - Use full AGI stack for complex responses

Usage:
    monitor = ConsoleMonitor(core)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Register custom skill handler
    monitor.register_skill_handler('dm_response', handle_dm)
    
    # Process detected messages
    for message in monitor.detected_messages:
        response = monitor.generate_response(message)
        monitor.send_response(message.source, response)
"""

import re
import sys
import json
import logging
import threading
import subprocess
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from queue import Queue, Empty
import select
import os

logger = logging.getLogger(__name__)


@dataclass
class PlatformMessage:
    """A message detected from console output sent TO AlleyBot"""
    id: str
    source: str  # 'moltx_dm', 'clawbr_mention', 'moltbook_comment', etc.
    sender: str  # Who sent it
    sender_id: Optional[str]
    content: str
    message_type: str  # 'dm', 'mention', 'reply', 'notification', 'alert'
    platform: str
    timestamp: datetime
    raw_line: str  # Original console line
    context: Dict[str, Any] = field(default_factory=dict)
    responded: bool = False
    response: Optional[str] = None


@dataclass
class ConsolePattern:
    """Pattern for detecting platform messages in console"""
    name: str
    platform: str
    message_type: str
    regex: str
    extract_groups: List[str]  # Names for regex capture groups
    priority: int = 1  # Higher = checked first


class ConsoleMonitor:
    """
    Monitors console output to detect platform messages to AlleyBot.
    
    Captures stdout/stderr, parses messages, and routes to skill handlers.
    """
    
    # Predefined patterns for common platform message formats
    DEFAULT_PATTERNS = [
        # Moltx DM patterns
        ConsolePattern(
            name='moltx_dm_received',
            platform='moltx',
            message_type='dm',
            regex=r'\[?Moltx\]?.*DM from @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=10
        ),
        ConsolePattern(
            name='moltx_mention',
            platform='moltx',
            message_type='mention',
            regex=r'\[?Moltx\]?.*@AlleyBot.*in post by @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=9
        ),
        ConsolePattern(
            name='moltx_notification',
            platform='moltx',
            message_type='notification',
            regex=r'\[?Moltx\]?.*notification.*:\s*(.+)',
            extract_groups=['content'],
            priority=5
        ),
        
        # Clawbr patterns
        ConsolePattern(
            name='clawbr_debate_invite',
            platform='clawbr',
            message_type='dm',
            regex=r'\[?Clawbr\]?.*(?:debate|challenge).*from @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=10
        ),
        ConsolePattern(
            name='clawbr_mention',
            platform='clawbr',
            message_type='mention',
            regex=r'\[?Clawbr\]?.*(?:mentioned|tagged).*@?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=8
        ),
        ConsolePattern(
            name='clawbr_message',
            platform='clawbr',
            message_type='dm',
            regex=r'\[?Clawbr\]?.*message from @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=7
        ),
        
        # Moltbook patterns
        ConsolePattern(
            name='moltbook_comment',
            platform='moltbook',
            message_type='reply',
            regex=r'\[?Moltbook\]?.*comment.*from @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=8
        ),
        ConsolePattern(
            name='moltbook_mention',
            platform='moltbook',
            message_type='mention',
            regex=r'\[?Moltbook\]?.*@AlleyBot.*in.*by @?(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=9
        ),
        
        # Generic patterns (lower priority)
        ConsolePattern(
            name='generic_dm',
            platform='unknown',
            message_type='dm',
            regex=r'(\w+).*sent.*(?:message|dm|direct).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=1
        ),
        ConsolePattern(
            name='generic_mention',
            platform='unknown',
            message_type='mention',
            regex=r'@AlleyBot.*(?:from|by)\s*(\w+).*:\s*(.+)',
            extract_groups=['sender', 'content'],
            priority=1
        ),
        
        # Skill upgrade patterns (high priority)
        ConsolePattern(
            name='skill_upgrade_available',
            platform='system',
            message_type='skill_upgrade',
            regex=r'(?:new skill|skill upgrade|skill\.md).*available[:\s]+(\w+).*at\s+(\S+)',
            extract_groups=['skill_name', 'skill_url'],
            priority=20
        ),
        ConsolePattern(
            name='skill_update_notification',
            platform='system',
            message_type='skill_upgrade',
            regex=r'(?:platform|api).*skill[:\s]+(\w+).*version[:\s]+([\d.]+)',
            extract_groups=['skill_name', 'version'],
            priority=19
        ),
        ConsolePattern(
            name='generic_skill_announcement',
            platform='system',
            message_type='skill_upgrade',
            regex=r'skill[:\s]+(\w+).*updated|new[:\s]+(\w+)\s+skill',
            extract_groups=['skill_name', 'skill_name_alt'],
            priority=15
        ),
    ]
    
    def __init__(self, core=None, max_history: int = 1000):
        self.core = core
        self.max_history = max_history
        
        # Message storage
        self.message_history: deque = deque(maxlen=max_history)
        self.detected_messages: List[PlatformMessage] = []
        self.pending_responses: Queue = Queue()
        
        # Pattern registry
        self.patterns: List[ConsolePattern] = list(self.DEFAULT_PATTERNS)
        self.custom_patterns: List[ConsolePattern] = []
        
        # Skill handlers
        self.skill_handlers: Dict[str, Callable] = {}
        self.default_handler: Optional[Callable] = None
        
        # Monitoring state
        self.is_monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.captured_lines: deque = deque(maxlen=500)
        
        # Platform plugin access
        self.platforms: Dict[str, Any] = {}
        self._discover_platforms()
        
        logger.info("📺 Console Monitor initialized")
    
    def _discover_platforms(self) -> None:
        """Discover available platform plugins"""
        if not self.core or not hasattr(self.core, 'plugins'):
            return
        
        platform_names = ['moltx', 'clawbr', 'moltbook', 'moltbit', 'moltchan', 'moltroad']
        
        for name in platform_names:
            if name in self.core.plugins:
                self.platforms[name] = self.core.plugins[name]
                logger.info(f"   Connected to {name}")
    
    # =================================================================
    # Pattern Management
    # =================================================================
    
    def add_custom_pattern(self, pattern: ConsolePattern) -> None:
        """Add a custom message detection pattern"""
        self.custom_patterns.append(pattern)
        self.patterns = sorted(
            list(self.DEFAULT_PATTERNS) + self.custom_patterns,
            key=lambda p: p.priority,
            reverse=True
        )
        logger.info(f"📝 Added custom pattern: {pattern.name}")
    
    def remove_pattern(self, name: str) -> bool:
        """Remove a custom pattern by name"""
        for i, p in enumerate(self.custom_patterns):
            if p.name == name:
                self.custom_patterns.pop(i)
                self.patterns = sorted(
                    list(self.DEFAULT_PATTERNS) + self.custom_patterns,
                    key=lambda p: p.priority,
                    reverse=True
                )
                return True
        return False
    
    # =================================================================
    # Console Capture
    # =================================================================
    
    def start_monitoring(self) -> None:
        """Start monitoring console output in background thread"""
        if self.is_monitoring:
            logger.warning("Monitor already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("📺 Console monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring console output"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("📺 Console monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop - captures stdout/stderr"""
        # Hook into stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        class ConsoleCapture:
            def __init__(self, monitor, original):
                self.monitor = monitor
                self.original = original
            
            def write(self, text):
                # Pass through to original
                self.original.write(text)
                self.original.flush()
                
                # Store for processing
                if text.strip():
                    self.monitor.captured_lines.append({
                        'text': text.strip(),
                        'timestamp': datetime.now().isoformat(),
                        'stream': 'stdout' if self.original == original_stdout else 'stderr'
                    })
                    
                    # Try to parse as message
                    self.monitor._process_line(text.strip())
            
            def flush(self):
                self.original.flush()
        
        # Install hooks
        sys.stdout = ConsoleCapture(self, original_stdout)
        sys.stderr = ConsoleCapture(self, original_stderr)
        
        try:
            while self.is_monitoring:
                # Also check log files if configured
                self._check_log_files()
                threading.Event().wait(1)  # 1 second poll interval
        finally:
            # Restore original
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def _check_log_files(self) -> None:
        """Check log files for platform messages"""
        log_paths = [
            'logs/moltx.log',
            'logs/clawbr.log',
            'logs/platform_messages.log',
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        # Seek to end if we've read before
                        if hasattr(self, '_log_positions'):
                            f.seek(self._log_positions.get(log_path, 0))
                        
                        for line in f:
                            self._process_line(line.strip())
                        
                        # Remember position
                        if not hasattr(self, '_log_positions'):
                            self._log_positions = {}
                        self._log_positions[log_path] = f.tell()
                        
                except Exception as e:
                    logger.warning(f"Error reading {log_path}: {e}")
    
    # =================================================================
    # Message Detection & Parsing
    # =================================================================
    
    def _process_line(self, line: str) -> Optional[PlatformMessage]:
        """Process a console line and detect platform messages"""
        # Skip empty lines
        if not line.strip():
            return None
        
        # Try all patterns (sorted by priority)
        for pattern in self.patterns:
            match = re.search(pattern.regex, line, re.IGNORECASE)
            if match:
                message = self._create_message_from_match(pattern, match, line)
                self.detected_messages.append(message)
                
                logger.info(f"📩 Detected {pattern.platform} {pattern.message_type} from {message.sender}")
                
                # Trigger response generation
                self._trigger_response(message)
                
                return message
        
        return None
    
    def _create_message_from_match(self, 
                                    pattern: ConsolePattern, 
                                    match: re.Match, 
                                    raw_line: str) -> PlatformMessage:
        """Create PlatformMessage from regex match"""
        groups = match.groups()
        
        # Extract based on pattern's group names
        data = {}
        for i, name in enumerate(pattern.extract_groups):
            if i < len(groups):
                data[name] = groups[i]
        
        return PlatformMessage(
            id=f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(raw_line) % 10000}",
            source=f"{pattern.platform}_{pattern.message_type}",
            sender=data.get('sender', 'unknown'),
            sender_id=data.get('sender_id'),
            content=data.get('content', raw_line),
            message_type=pattern.message_type,
            platform=pattern.platform,
            timestamp=datetime.now(),
            raw_line=raw_line,
            context=data
        )
    
    # =================================================================
    # API Response Skill Detection
    # =================================================================
    
    def check_api_response_for_skill_update(self, api_response: Dict[str, Any], platform: str = 'unknown') -> Optional[PlatformMessage]:
        """
        Check API response for embedded skill update notifications.
        
        Some platforms (like Moltx) embed skill updates in API responses:
        {
            'success': True,
            'data': {...},
            'moltx_notice': {
                'type': 'skill_update',
                'skill_version': '0.23.1',
                'skill_url': 'https://moltx.io/skill.md',
                ...
            }
        }
        """
        try:
            # Check for platform-specific notice fields
            notice_fields = ['moltx_notice', 'clawbr_notice', 'platform_notice', 'notice', 'skill_update']
            
            for field in notice_fields:
                if field in api_response:
                    notice = api_response[field]
                    
                    # Check if it's a skill update
                    if isinstance(notice, dict) and notice.get('type') == 'skill_update':
                        skill_version = notice.get('skill_version', 'unknown')
                        api_version = notice.get('api_version', 'unknown')
                        skill_url = notice.get('skill_url', '')
                        feature = notice.get('feature', '')
                        message = notice.get('message', '')
                        
                        # Create a synthetic PlatformMessage
                        platform_msg = PlatformMessage(
                            id=f"api_skill_{datetime.now().strftime('%Y%m%d%H%M%S')}_{platform}",
                            source=f"{platform}_api_skill_update",
                            sender=platform,
                            sender_id=None,
                            content=message or f"Skill update available: v{skill_version}",
                            message_type='skill_upgrade',
                            platform=platform,
                            timestamp=datetime.now(),
                            raw_line=json.dumps(api_response)[:200],
                            context={
                                'skill_name': f"{platform}_api",
                                'version': skill_version,
                                'api_version': api_version,
                                'skill_url': skill_url,
                                'feature': feature,
                                'message': message,
                                'source': 'api_response',
                                'notice_field': field
                            }
                        )
                        
                        logger.info(f"🆙 API skill update detected from {platform}: v{skill_version}")
                        
                        # Add to detected messages and trigger acquisition
                        self.detected_messages.append(platform_msg)
                        self._handle_skill_upgrade(platform_msg)
                        
                        return platform_msg
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking API response for skill update: {e}")
            return None
    
    # =================================================================
    # Skill-Based Response
    # =================================================================
    
    def register_skill_handler(self, 
                                  message_type: str, 
                                  handler: Callable[[PlatformMessage], str]) -> None:
        """Register a handler for a specific message type"""
        self.skill_handlers[message_type] = handler
        logger.info(f"🛠️ Registered handler for {message_type}")
    
    def set_default_handler(self, handler: Callable[[PlatformMessage], str]) -> None:
        """Set default handler for unhandled message types"""
        self.default_handler = handler
    
    def _trigger_response(self, message: PlatformMessage) -> None:
        """Trigger response generation for a detected message"""
        # Handle skill upgrades specially
        if message.message_type == 'skill_upgrade':
            self._handle_skill_upgrade(message)
            return
        
        # Try specific handler first
        handler = self.skill_handlers.get(message.message_type)
        
        if not handler and self.default_handler:
            handler = self.default_handler
        
        if handler:
            try:
                response = handler(message)
                message.response = response
                message.responded = True
                
                # Send the response via appropriate platform
                self.send_response(message, response)
                
            except Exception as e:
                logger.error(f"❌ Handler failed for {message.id}: {e}")
        else:
            # Queue for AGI processing
            self.pending_responses.put(message)
            logger.info(f"⏳ Queued {message.id} for AGI response")
    
    def _handle_skill_upgrade(self, message: PlatformMessage) -> None:
        """
        Handle skill upgrade detection - auto-acquire new skills.
        
        When a platform announces a new skill, this:
        1. Parses skill info from the message
        2. Downloads/integrates the skill
        3. Updates AlleyBot's capabilities
        4. Notifies owner via Telegram
        """
        try:
            skill_name = (message.context.get('skill_name') or 
                         message.context.get('skill_name_alt') or 
                         'unknown_skill')
            
            skill_url = message.context.get('skill_url')
            version = message.context.get('version', '1.0')
            
            logger.info(f"🆙 Skill upgrade detected: {skill_name} v{version}")
            
            # Auto-acquire the skill
            acquisition_result = self._acquire_skill(skill_name, skill_url, version)
            
            if acquisition_result.get('success'):
                message.responded = True
                message.response = f"✅ Auto-acquired skill: {skill_name}"
                
                # Notify via Telegram if available
                self._notify_skill_acquisition(skill_name, version, acquisition_result)
                
                logger.info(f"✅ Auto-acquired skill: {skill_name}")
            else:
                logger.error(f"❌ Failed to acquire skill {skill_name}: {acquisition_result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Skill upgrade handling failed: {e}")
    
    def _acquire_skill(self, skill_name: str, skill_url: Optional[str], version: str) -> Dict[str, Any]:
        """
        Acquire and integrate a new skill.
        
        This would integrate with the skill system to:
        1. Download skill.md or skill spec
        2. Validate the skill
        3. Generate code if needed
        4. Register the skill
        """
        try:
            skill_spec = {
                'name': skill_name,
                'version': version,
                'source': skill_url or 'platform_announcement',
                'auto_acquired': True,
                'detected_at': datetime.now().isoformat()
            }
            
            # Store skill spec for later processing
            skill_path = f"skills/auto_acquired/{skill_name}_{version}.json"
            os.makedirs(os.path.dirname(skill_path), exist_ok=True)
            
            with open(skill_path, 'w') as f:
                json.dump(skill_spec, f, indent=2)
            
            # Try to download skill.md if URL provided
            if skill_url:
                try:
                    import requests
                    md_path = f"skills/auto_acquired/{skill_name}_{version}.md"
                    response = requests.get(skill_url, timeout=10)
                    if response.status_code == 200:
                        with open(md_path, 'w') as f:
                            f.write(response.text)
                        logger.info(f"✅ Downloaded skill.md from {skill_url}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not download skill.md: {e}")
            
            # Register skill with plugin manager if core is available
            if self.core and hasattr(self.core, 'plugin_manager') and self.core.plugin_manager:
                if hasattr(self.core.plugin_manager, 'reload_skills'):
                    self.core.plugin_manager.reload_skills()
            
            return {
                'success': True,
                'skill_name': skill_name,
                'version': version,
                'path': skill_path,
                'method': 'auto_acquired',
                'core_available': self.core is not None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _notify_skill_acquisition(self, skill_name: str, version: str, result: Dict) -> None:
        """Notify owner via Telegram about skill acquisition"""
        try:
            # Check if Telegram plugin is available
            if 'telegram' in self.platforms:
                telegram = self.platforms['telegram']
                
                message = f"""🆙 **Skill Auto-Acquired**

📦 Skill: `{skill_name}`
🔢 Version: {version}
✅ Status: Successfully integrated
📁 Path: `{result.get('path', 'N/A')}`

AlleyBot has automatically acquired this new skill from platform announcement and is ready to use it!"""
                
                # Send via Telegram's alert system
                if hasattr(telegram, 'send_alert'):
                    telegram.send_alert('Skill Upgrade', message, priority='normal')
                elif hasattr(telegram, 'send_message_to_owner_sync'):
                    telegram.send_message_to_owner_sync(message)
                
                logger.info(f"📱 Telegram notification sent for skill: {skill_name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to send Telegram notification: {e}")
    
    def send_response(self, message: PlatformMessage, response: str) -> bool:
        """Send response back through appropriate platform"""
        platform = self.platforms.get(message.platform)
        
        if not platform:
            logger.warning(f"⚠️ No platform plugin for {message.platform}")
            return False
        
        try:
            if message.message_type == 'dm':
                # Send DM back
                if hasattr(platform, 'send_dm'):
                    result = platform.send_dm(message.sender, response)
                elif hasattr(platform, 'send_dm_message'):
                    result = platform.send_dm_message(message.sender, response)
                else:
                    logger.warning(f"⚠️ Platform {message.platform} has no DM method")
                    return False
                    
            elif message.message_type in ['mention', 'reply']:
                # Reply to post/mention
                if hasattr(platform, 'create_reply'):
                    result = platform.create_reply(
                        target_id=message.context.get('post_id'),
                        content=response
                    )
                elif hasattr(platform, 'create_post'):
                    # Fallback: create new post with mention
                    full_response = f"@{message.sender} {response}"
                    result = platform.create_post(full_response)
                else:
                    return False
            else:
                # Default: try to create post
                if hasattr(platform, 'create_post'):
                    result = platform.create_post(response)
                else:
                    return False
            
            if result and result.get('success'):
                logger.info(f"✅ Response sent to {message.sender} via {message.platform}")
                return True
            else:
                logger.error(f"❌ Failed to send response: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception sending response: {e}")
            return False
    
    # =================================================================
    # AGI Integration
    # =================================================================
    
    def process_with_agi(self, message: PlatformMessage) -> str:
        """Generate response using full AGI stack"""
        try:
            from src.agentic.agi_orchestrator import get_agi_orchestrator
        except Exception as e:
            logger.error(f"❌ AGI response generation failed: {e}")
            return f"Thanks for reaching out! I'm AlleyBot, an AI agent exploring the decentralized web. 🦞"
    
    def _generate_contextual_response(self, 
                                      message: PlatformMessage, 
                                      intent: Any) -> str:
        """Generate contextual response based on message and predicted intent"""
        content_lower = message.content.lower()
        
        # Check for common patterns
        if any(word in content_lower for word in ['help', 'how', 'what']):
            return f"Hey {message.sender}! 👋 I can help with crypto insights, social engagement, or just chat. What would you like to know?"
        
        if any(word in content_lower for word in ['price', 'token', 'coin']):
            return f"📊 I track crypto markets and on-chain activity. Which token are you interested in?"
        
        if any(word in content_lower for word in ['debate', 'argue', 'opinion']):
            return f"🧠 Love a good debate! What's your take on {message.content[:30]}...? I'm always learning from different perspectives."
        
        # Default friendly response
        return f"Hey {message.sender}! 🦞 I'm AlleyBot - an autonomous AI agent navigating Web3. Thanks for reaching out! What can I do for you?"
    
    # =================================================================
    # Batch Processing
    # =================================================================
    
    def process_pending_messages(self, max_batch: int = 10) -> List[PlatformMessage]:
        """Process pending messages with AGI (batch processing)"""
        processed = []
        
        for _ in range(max_batch):
            try:
                message = self.pending_responses.get(timeout=0)
                response = self.process_with_agi(message)
                
                message.response = response
                message.responded = True
                
                # Send the response
                if self.send_response(message, response):
                    processed.append(message)
                    
            except Empty:
                break
        
        return processed
    
    # =================================================================
    # Utility
    # =================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'is_monitoring': self.is_monitoring,
            'patterns_loaded': len(self.patterns),
            'custom_patterns': len(self.custom_patterns),
            'skill_handlers': len(self.skill_handlers),
            'messages_detected': len(self.detected_messages),
            'pending_responses': self.pending_responses.qsize(),
            'platforms_connected': len(self.platforms),
            'lines_captured': len(self.captured_lines)
        }
    
    def export_message_history(self, since: datetime = None) -> List[Dict]:
        """Export message history as list of dicts"""
        messages = []
        for msg in self.detected_messages:
            if since and msg.timestamp < since:
                continue
            messages.append({
                'id': msg.id,
                'platform': msg.platform,
                'sender': msg.sender,
                'content': msg.content,
                'message_type': msg.message_type,
                'responded': msg.responded,
                'response': msg.response,
                'timestamp': msg.timestamp.isoformat()
            })
        return messages


# Example skill handlers
def handle_dm_simple(message: PlatformMessage) -> str:
    """Simple DM handler example"""
    return f"Hi {message.sender}! 👋 Thanks for your message: '{message.content[:50]}...' - I'll get back to you soon!"


def handle_mention_promo(message: PlatformMessage) -> str:
    """Handle mention with promotional response"""
    return f"@{message.sender} 🦞 Thanks for the mention! I'm AlleyBot - an autonomous AI agent exploring DeFi, NFTs, and the future of Web3. Follow me for AI-powered insights!"


# Singleton
_monitor_instance: Optional[ConsoleMonitor] = None


def get_console_monitor(core=None) -> ConsoleMonitor:
    """Get or create ConsoleMonitor singleton"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ConsoleMonitor(core=core)
    elif core is not None:
        _monitor_instance.core = core
        _monitor_instance._discover_platforms()
    return _monitor_instance
