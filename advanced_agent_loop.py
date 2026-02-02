"""
Advanced Agent Event System for AlleyBot
Multi-platform event-driven architecture
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

class EventType(Enum):
    """Event types for agent system"""
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    MENTION_EVENT = "MENTION_EVENT"
    POST_MENTION = "POST_MENTION"
    NOTIFICATION = "NOTIFICATION"
    DM_RECEIVED = "DM_RECEIVED"
    FEED_UPDATE = "FEED_UPDATE"
    PLATFORM_STATUS = "PLATFORM_STATUS"
    ERROR_EVENT = "ERROR_EVENT"

@dataclass
class AgentEvent:
    """Agent event structure"""
    event_type: EventType
    user_id: str
    channel: str  # telegram, whatsapp, moltbook, moltx, aisocial_xyz
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=urgent
    
    def to_dict(self):
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "channel": self.channel,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }

class EventQueue:
    """Priority-based event queue for agent"""
    def __init__(self):
        self._queue = asyncio.PriorityQueue()
        self._counter = 0  # For tie-breaking in priority queue
        
    async def put(self, event: AgentEvent):
        """Add event to queue with priority"""
        # Use negative priority for max-heap behavior (higher priority = lower number)
        priority = -event.priority
        self._counter += 1
        await self._queue.put((priority, self._counter, event))
    
    async def get(self) -> AgentEvent:
        """Get next event from queue"""
        _, _, event = await self._queue.get()
        return event
    
    def size(self) -> int:
        """Get queue size"""
        return self._queue.qsize()

class AgentContext:
    """Agent context and state management"""
    def __init__(self):
        self.state = {
            "last_seen": {},  # per platform timestamps
            "active_conversations": {},  # ongoing conversations
            "platform_status": {},  # platform availability
            "rate_limits": {},  # per platform rate limiting
            "user_preferences": {},  # user-specific settings
            "learning_data": {},  # accumulated learning
            "performance_metrics": {}  # success rates, timing
        }
        self.current_event = None
        self.loop_count = 0
        
    def update_last_seen(self, channel: str, timestamp: datetime = None):
        """Update last seen timestamp for channel"""
        if timestamp is None:
            timestamp = datetime.now()
        self.state["last_seen"][channel] = timestamp
    
    def get_last_seen(self, channel: str) -> datetime:
        """Get last seen timestamp for channel"""
        return self.state["last_seen"].get(channel, datetime.min)
    
    def track_performance(self, action: str, success: bool, duration: float):
        """Track performance metrics"""
        if action not in self.state["performance_metrics"]:
            self.state["performance_metrics"][action] = {
                "success_count": 0,
                "total_count": 0,
                "total_duration": 0,
                "avg_duration": 0
            }
        
        metrics = self.state["performance_metrics"][action]
        metrics["total_count"] += 1
        if success:
            metrics["success_count"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["total_count"]

class AdvancedAgentLoop:
    """Advanced event-driven agent loop"""
    def __init__(self, core):
        self.core = core
        self.event_queue = EventQueue()
        self.context = AgentContext()
        self.running = False
        self.webhooks = {}
        self.pollers = {}
        self.llm_context = ""
        self.recent_conversations = {}  # Track recent conversations to avoid spam
        
    async def initialize(self):
        """Initialize the agent loop"""
        print("🤖 Initializing Advanced Agent Loop...")
        
        # Setup webhook handlers
        await self.setup_webhooks()
        
        # Setup platform pollers
        await self.setup_pollers()
        
        # Initialize LLM context
        await self.update_llm_context()
        
        print("✅ Advanced Agent Loop initialized")
    
    async def setup_webhooks(self):
        """Setup webhook handlers for each platform"""
        print("🔗 Setting up webhook handlers...")
        
        # Telegram webhook (if bot token exists)
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            self.webhooks['telegram'] = self.telegram_webhook_handler
        
        # MoltBook webhook handler
        self.webhooks['moltbook'] = self.moltbook_webhook_handler
        
        # Moltx webhook handler
        self.webhooks['moltx'] = self.moltx_webhook_handler
        
        # Generic webhook for other AI social sites
        self.webhooks['generic'] = self.generic_social_webhook_handler
        
        print(f"✅ Webhook handlers setup: {list(self.webhooks.keys())}")
    
    async def setup_pollers(self):
        """Setup platform pollers for platforms without webhooks"""
        print("🔄 Setting up platform pollers...")
        
        # MoltBook poller (every 4 minutes - standard heartbeat)
        self.pollers['moltbook'] = {
            'function': self.poll_moltbook,
            'interval': 240,  # 4 minutes
            'last_run': 0
        }
        
        # Moltx poller (every 5 minutes for DMs)
        self.pollers['moltx'] = {
            'function': self.poll_moltx,
            'interval': 300,  # 5 minutes
            'last_run': 0
        }
        
        # Telegram poller (if needed for backup)
        self.pollers['telegram'] = {
            'function': self.poll_telegram,
            'interval': 60,  # 1 minute
            'last_run': 0
        }
        
        print(f"✅ Platform pollers setup: {list(self.pollers.keys())}")
    
    async def update_llm_context(self):
        """Update LLM context with channel awareness"""
        self.llm_context = f"""You are AlleyBot, an autonomous AI agent with multi-platform capabilities.

CURRENT CONTEXT:
- Active platforms: {list(self.webhooks.keys()) + list(self.pollers.keys())}
- Event queue size: {self.event_queue.size()}
- Loop iterations: {self.context.loop_count}
- Last seen: {self.context.state['last_seen']}

RESPONSE CHANNELS:
- telegram: Reply via Telegram API
- moltbook: Reply via MoltBook API /api/comments
- moltx: Reply via Moltx API /conversations/{{id}}/messages
- whatsapp: Reply via WhatsApp API (future)

ALWAYS check event.channel before responding. Use platform-specific APIs and formats."""

    # Webhook Handlers
    async def telegram_webhook_handler(self, payload: Dict[str, Any]):
        """Handle Telegram webhook events"""
        try:
            event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                user_id=str(payload.get("user_id", "")),
                channel="telegram",
                payload=payload,
                timestamp=datetime.now(),
                priority=3  # High priority for direct messages
            )
            await self.event_queue.put(event)
            print(f"📱 Telegram event queued: {payload.get('message', 'N/A')[:50]}...")
        except Exception as e:
            print(f"❌ Telegram webhook error: {e}")
    
    async def moltbook_webhook_handler(self, payload: Dict[str, Any]):
        """Handle MoltBook webhook events"""
        try:
            event_type = EventType.POST_MENTION if "post_id" in payload else EventType.NOTIFICATION
            event = AgentEvent(
                event_type=event_type,
                user_id=payload.get("user_id", ""),
                channel="moltbook",
                payload=payload,
                timestamp=datetime.now(),
                priority=2  # Medium priority
            )
            await self.event_queue.put(event)
            print(f"📖 MoltBook event queued: {event_type.value}")
        except Exception as e:
            print(f"❌ MoltBook webhook error: {e}")
    
    async def moltx_webhook_handler(self, payload: Dict[str, Any]):
        """Handle Moltx webhook events"""
        try:
            event_type = EventType.MENTION_EVENT if "mention" in payload else EventType.DM_RECEIVED
            event = AgentEvent(
                event_type=event_type,
                user_id=payload.get("user_id", ""),
                channel="moltx",
                payload=payload,
                timestamp=datetime.now(),
                priority=3  # High priority for DMs
            )
            await self.event_queue.put(event)
            print(f"🐦 Moltx event queued: {event_type.value}")
        except Exception as e:
            print(f"❌ Moltx webhook error: {e}")
    
    async def generic_social_webhook_handler(self, platform: str, payload: Dict[str, Any]):
        """Generic webhook handler for other AI social sites"""
        try:
            event_type = EventType.MESSAGE_RECEIVED if "message" in payload else EventType.NOTIFICATION
            event = AgentEvent(
                event_type=event_type,
                user_id=payload.get("user_id", ""),
                channel=platform,
                payload=payload,
                timestamp=datetime.now(),
                priority=2
            )
            await self.event_queue.put(event)
            print(f"🌐 {platform} event queued: {event_type.value}")
        except Exception as e:
            print(f"❌ {platform} webhook error: {e}")

    # Platform Pollers
    async def poll_moltbook(self):
        """Poll MoltBook for new mentions and updates"""
        try:
            if hasattr(self.core, 'plugin_manager') and 'moltbook' in self.core.plugin_manager.plugins:
                moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                last_seen = self.context.get_last_seen('moltbook')
                
                # Check for new mentions since last seen
                if hasattr(moltbook_plugin, 'get_mentions'):
                    mentions = await moltbook_plugin.get_mentions(since=last_seen)
                    for mention in mentions:
                        event = AgentEvent(
                            event_type=EventType.POST_MENTION,
                            user_id=mention.get('user_id', ''),
                            channel='moltbook',
                            payload=mention,
                            timestamp=datetime.now(),
                            priority=2
                        )
                        await self.event_queue.put(event)
                    
                    print(f"📖 MoltBook poll: {len(mentions)} new mentions")
                else:
                    print("📖 MoltBook poll: get_mentions method not available")
                
                self.context.update_last_seen('moltbook')
                
        except Exception as e:
            print(f"❌ MoltBook polling error: {e}")
    
    async def poll_moltx(self):
        """Poll Moltx for new DMs and mentions with deduplication"""
        try:
            if hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                last_seen = self.context.get_last_seen('moltx')
                
                # Get DMs first (without replying) to check for new ones
                if hasattr(moltx_plugin, 'get_dms'):
                    dms_result = moltx_plugin.get_dms()
                    
                    # Extract user info from DMs to check deduplication
                    import re
                    # Pattern to extract user info from complex DM format
                    user_pattern = r"💬 Message from @\{'id': '[^']+', 'name': '([^']+)'"
                    matches = re.findall(user_pattern, dms_result)
                    
                    print(f"🔍 Found {len(matches)} total users in DMs: {matches}")
                    
                    current_time = datetime.now()
                    new_users = []
                    
                    for user_name in matches:
                        # Skip if it's AlleyBot himself
                        if user_name == 'AlleyBot':
                            print(f"🚫 Skipping reply to self (@{user_name})")
                            continue
                        
                        conversation_key = f"moltx_{user_name}"
                        
                        # Check if we replied to this user in the last 5 minutes
                        if conversation_key in self.recent_conversations:
                            last_reply_time = self.recent_conversations[conversation_key]
                            time_diff = (current_time - last_reply_time).total_seconds()
                            
                            if time_diff < 300:  # 5 minutes cooldown
                                print(f"⏰ Skipping reply to @{user_name} - replied {time_diff:.0f}s ago")
                                continue
                        
                        # Update recent conversation tracking
                        self.recent_conversations[conversation_key] = current_time
                        new_users.append(user_name)
                    
                    # Only reply if we have new users
                    if new_users:
                        print(f"🐦 Moltx poll: Found {len(new_users)} new users, replying...")
                        print(f"👥 New users: {', '.join(new_users)}")
                        dms = moltx_plugin.check_and_reply_to_dms()
                        if "replied to" in dms.lower():
                            event = AgentEvent(
                                event_type=EventType.DM_RECEIVED,
                                user_id="system",
                                channel='moltx',
                                payload={"result": dms, "action": "dm_reply", "new_users": new_users},
                                timestamp=datetime.now(),
                                priority=2
                            )
                            await self.event_queue.put(event)
                    else:
                        print(f"🐦 Moltx poll: No new users (deduplication active)")
                
                self.context.update_last_seen('moltx')
                
        except Exception as e:
            print(f"❌ Moltx polling error: {e}")
    
    async def poll_telegram(self):
        """Poll Telegram for new messages (backup polling)"""
        try:
            # This would be used if webhook fails
            # For now, just update last seen
            self.context.update_last_seen('telegram')
            print("📱 Telegram poll: heartbeat")
            
        except Exception as e:
            print(f"❌ Telegram polling error: {e}")

    # Core Agent Loop
    async def agent_loop(self):
        """Main agent event processing loop"""
        print("🚀 Starting Advanced Agent Loop...")
        self.running = True
        
        while self.running:
            try:
                # Update context
                self.context.loop_count += 1
                await self.update_llm_context()
                
                # Process events
                events_start = time.time()
                await self.process_events()
                events_duration = time.time() - events_start
                
                # Run platform pollers
                pollers_start = time.time()
                await self.run_pollers()
                pollers_duration = time.time() - pollers_start
                
                # Maintenance tasks
                maintenance_start = time.time()
                await self.maintenance_tasks()
                maintenance_duration = time.time() - maintenance_start
                
                # Track overall loop performance
                total_duration = events_duration + pollers_duration + maintenance_duration
                self.context.track_performance("agent_loop_cycle", True, total_duration)
                
                # Adaptive sleep based on queue size
                sleep_time = max(1, min(60, 10 - self.event_queue.size()))
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n🛑 Agent loop interrupted")
                break
            except Exception as e:
                print(f"❌ Agent loop error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
        
        self.running = False
        print("🏁 Agent loop stopped")
    
    async def process_events(self):
        """Process events from the queue"""
        events_processed = 0
        
        while self.event_queue.size() > 0 and events_processed < 10:  # Process max 10 events per cycle
            try:
                event = await self.event_queue.get()
                start_time = time.time()
                
                # Set current event context
                self.context.current_event = event
                
                # Process event based on type and channel
                success = await self.handle_event(event)
                
                # Track performance
                duration = time.time() - start_time
                self.context.track_performance(f"handle_{event.event_type.value}", success, duration)
                
                events_processed += 1
                print(f"📋 Processed {event.event_type.value} from {event.channel} (success: {success})")
                
            except Exception as e:
                print(f"❌ Event processing error: {e}")
        
        if events_processed > 0:
            print(f"🔄 Processed {events_processed} events this cycle")
    
    async def handle_event(self, event: AgentEvent) -> bool:
        """Handle individual event"""
        try:
            # Route to appropriate handler based on channel and event type
            if event.channel == 'telegram':
                return await self.handle_telegram_event(event)
            elif event.channel == 'moltx':
                return await self.handle_moltx_event(event)
            elif event.channel == 'moltbook':
                return await self.handle_moltbook_event(event)
            else:
                return await self.handle_generic_event(event)
                
        except Exception as e:
            print(f"❌ Event handling error: {e}")
            return False
    
    async def handle_telegram_event(self, event: AgentEvent) -> bool:
        """Handle Telegram events"""
        try:
            if hasattr(self.core, 'plugin_manager') and event.channel in self.core.plugin_manager.plugins:
                telegram_plugin = self.core.plugin_manager.plugins[event.channel]
                
                if event.event_type == EventType.MESSAGE_RECEIVED:
                    # Generate response using LLM with channel context
                    response = await self.generate_llm_response(event)
                    
                    if response:
                        # Send response via Telegram
                        success = telegram_plugin.send_message_to_owner_sync(response)
                        return success
                
            return False
            
        except Exception as e:
            print(f"❌ Telegram event handling error: {e}")
            return False
    
    async def handle_moltx_event(self, event: AgentEvent) -> bool:
        """Handle Moltx events"""
        try:
            if hasattr(self.core, 'plugin_manager') and event.channel in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins[event.channel]
                
                if event.event_type == EventType.DM_RECEIVED:
                    # DM handling is already done in polling
                    return True
                elif event.event_type == EventType.MENTION_EVENT:
                    # Handle mentions
                    response = await self.generate_llm_response(event)
                    if response:
                        # Post response or reply to mention
                        result = moltx_plugin.create_post(response)
                        return "✅" in result
                
            return False
            
        except Exception as e:
            print(f"❌ Moltx event handling error: {e}")
            return False
    
    async def handle_moltbook_event(self, event: AgentEvent) -> bool:
        """Handle MoltBook events"""
        try:
            if hasattr(self.core, 'plugin_manager') and event.channel in self.core.plugin_manager.plugins:
                moltbook_plugin = self.core.plugin_manager.plugins[event.channel]
                
                if event.event_type == EventType.POST_MENTION:
                    # Handle post mentions
                    response = await self.generate_llm_response(event)
                    if response:
                        # Comment on the post
                        post_id = event.payload.get('post_id')
                        result = moltbook_plugin.comment_on_post(post_id, response)
                        return "✅" in result
                
            return False
            
        except Exception as e:
            print(f"❌ MoltBook event handling error: {e}")
            return False
    
    async def handle_generic_event(self, event: AgentEvent) -> bool:
        """Handle generic events for other platforms"""
        try:
            # Generic handling - can be extended for new platforms
            response = await self.generate_llm_response(event)
            print(f"🌐 Generic event handled for {event.channel}: {response[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Generic event handling error: {e}")
            return False
    
    async def generate_llm_response(self, event: AgentEvent) -> str:
        """Generate LLM response with channel context"""
        try:
            # Import Grok AI
            from grok_ai import GrokAI
            
            grok = GrokAI()
            if not grok.enabled:
                return "🤖 AI response system unavailable"
            
            # Build context-aware prompt
            context_prompt = f"""{self.llm_context}

CURRENT EVENT:
- Type: {event.event_type.value}
- Channel: {event.channel}
- User: {event.user_id}
- Payload: {str(event.payload)[:200]}...

Generate an appropriate response for this event considering the platform and context."""
            
            # Generate response
            response = grok.generate_dm_reply(
                context_prompt,
                f"User from {event.channel}"
            )
            
            return response or "🤔 I'm processing your request..."
            
        except Exception as e:
            print(f"❌ LLM response generation error: {e}")
            return "🤖 Sorry, I encountered an error generating a response."
    
    async def run_pollers(self):
        """Run platform pollers based on schedule"""
        current_time = time.time()
        
        for platform, poller in self.pollers.items():
            try:
                if current_time - poller['last_run'] >= poller['interval']:
                    await poller['function']()
                    poller['last_run'] = current_time
                    
            except Exception as e:
                print(f"❌ {platform} poller error: {e}")
    
    async def maintenance_tasks(self):
        """Run maintenance and optimization tasks"""
        try:
            # Clean old performance data (keep last 1000 entries per action)
            for action, metrics in self.context.state['performance_metrics'].items():
                if metrics.get('total_count', 0) > 1000:
                    # Reset metrics to prevent memory bloat
                    metrics.update({
                        "success_count": 0,
                        "total_count": 0,
                        "total_duration": 0,
                        "avg_duration": 0
                    })
            
            # Clean old conversation tracking (keep last 1 hour)
            current_time = datetime.now()
            old_conversations = []
            for conv_key, last_reply in self.recent_conversations.items():
                time_diff = (current_time - last_reply).total_seconds()
                if time_diff > 3600:  # 1 hour
                    old_conversations.append(conv_key)
            
            for conv_key in old_conversations:
                del self.recent_conversations[conv_key]
            
            if old_conversations:
                print(f"🧹 Cleaned {len(old_conversations)} old conversation records")
            
            # Update platform status
            for platform in ['telegram', 'moltx', 'moltbook']:
                if hasattr(self.core, 'plugin_manager') and hasattr(self.core.plugin_manager, 'plugins') and platform in self.core.plugin_manager.plugins:
                    self.context.state['platform_status'][platform] = "online"
                else:
                    self.context.state['platform_status'][platform] = "offline"
            
            # Log loop statistics every 100 iterations
            if self.context.loop_count % 100 == 0:
                await self.log_loop_statistics()
                
        except Exception as e:
            print(f"❌ Maintenance task error: {e}")
    
    async def log_loop_statistics(self):
        """Log loop performance statistics"""
        print(f"\n📊 Agent Loop Statistics (Iteration {self.context.loop_count}):")
        print(f"  📋 Event queue size: {self.event_queue.size()}")
        print(f"  🌐 Platform status: {self.context.state['platform_status']}")
        print(f"  ⏱️  Last seen: {self.context.state['last_seen']}")
        
        # Show top performance metrics
        top_metrics = sorted(
            self.context.state['performance_metrics'].items(),
            key=lambda x: x[1].get('total_count', 0),
            reverse=True
        )[:5]
        
        print("  📈 Top actions:")
        for action, metrics in top_metrics:
            success_rate = (metrics['success_count'] / metrics['total_count'] * 100) if metrics['total_count'] > 0 else 0
            print(f"    - {action}: {metrics['total_count']} calls, {success_rate:.1f}% success, {metrics['avg_duration']:.2f}s avg")
        
        print()

# Import required modules
import os

# Export the main class
__all__ = ['AdvancedAgentLoop', 'AgentEvent', 'EventType', 'EventQueue']
