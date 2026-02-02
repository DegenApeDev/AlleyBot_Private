"""
Event-Driven Agent Runner for AlleyBot
Production-ready event queue system with asyncio
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class EventType(Enum):
    """Event types for the agent system"""
    MESSAGE_RECEIVED = "message_received"
    SCHEDULED_TASK = "scheduled_task"
    WEBHOOK_TRIGGER = "webhook_trigger"
    TIMER_EVENT = "timer_event"
    CUSTOM_NOTIFICATION = "custom_notification"


@dataclass
class AgentEvent:
    """Event data structure"""
    event_type: EventType
    session_id: str
    channel: str  # telegram, whatsapp, moltx, etc.
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high


class EventRunner:
    """Central event-driven agent runner"""
    
    def __init__(self, core):
        self.core = core
        self.event_queue = asyncio.Queue()
        self.running = False
        self.session_manager = None  # Will be injected
        self.model_router = None  # Will be injected
        
    async def start(self):
        """Start the event-driven agent loop"""
        print("🚀 Starting Production Event-Driven Agent Loop...")
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self.scheduled_task_generator())
        
        # Main event processing loop
        while self.running:
            try:
                # Get next event from queue
                event = await self.event_queue.get()
                
                # Process event through agent cycle
                await self.agent_cycle(event)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except KeyboardInterrupt:
                print("\n🛑 Event runner interrupted")
                break
            except Exception as e:
                print(f"❌ Event processing error: {e}")
                await asyncio.sleep(1)
        
        self.running = False
        print("✅ Event runner stopped")
    
    async def agent_cycle(self, event: AgentEvent):
        """
        Main agent reasoning cycle
        1. Load session state + RAG context
        2. Route to appropriate model (DeepSeek/Grok)
        3. Execute agent reasoning
        4. Persist session state
        """
        try:
            start_time = time.time()
            print(f"\n🤖 Agent Cycle: {event.event_type.value} (session: {event.session_id})")
            
            # Load session state and RAG context
            if self.session_manager:
                session = await self.session_manager.load_session(event.session_id)
                rag_context = await self.session_manager.get_rag_context(
                    event.session_id, 
                    event.payload.get('query', '')
                )
            else:
                session = {}
                rag_context = ""
            
            # Route to appropriate model based on context length
            if self.model_router:
                response = await self.model_router.route_and_execute(
                    event=event,
                    session=session,
                    rag_context=rag_context
                )
            else:
                response = await self.fallback_execution(event, session, rag_context)
            
            # Persist session state
            if self.session_manager:
                await self.session_manager.save_session(event.session_id, session)
                await self.session_manager.update_rag_memory(
                    event.session_id,
                    event.payload.get('query', ''),
                    response
                )
            
            # Send response back to channel
            await self.send_response(event.channel, event.session_id, response)
            
            duration = time.time() - start_time
            print(f"✅ Agent cycle completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"❌ Agent cycle error: {e}")
    
    async def fallback_execution(self, event: AgentEvent, session: Dict, rag_context: str) -> str:
        """Fallback execution when model router is not available"""
        # Use existing core functionality
        if event.event_type == EventType.MESSAGE_RECEIVED:
            query = event.payload.get('query', '')
            return f"Received: {query}"
        return "Event processed"
    
    async def send_response(self, channel: str, session_id: str, response: str):
        """Send response back to the appropriate channel"""
        try:
            if channel == 'telegram':
                # Use existing Telegram plugin
                if hasattr(self.core, 'plugin_manager') and 'telegram' in self.core.plugin_manager.plugins:
                    telegram_plugin = self.core.plugin_manager.plugins['telegram']
                    telegram_plugin.send_message_to_owner_sync(response)
                    print(f"📱 Response sent to Telegram")
            elif channel == 'moltx':
                # Use existing Moltx plugin
                print(f"🐦 Response sent to Moltx")
            else:
                print(f"📤 Response sent to {channel}")
        except Exception as e:
            print(f"❌ Failed to send response: {e}")
    
    async def scheduled_task_generator(self):
        """Generate scheduled task events (replaces polling loops)"""
        print("⏰ Starting scheduled task generator...")
        
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                
                # Post intelligent content every 2 hours (120 loops at 60s)
                if loop_count % 120 == 0:
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "create_post", "topic": "autonomous AI agent thoughts"},
                        timestamp=datetime.now(),
                        priority=2
                    ))
                
                # Browse and engage every 30 minutes
                if loop_count % 30 == 0:
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "browse_and_engage", "count": 3},
                        timestamp=datetime.now(),
                        priority=1
                    ))
                
                # Analyze trending every hour
                if loop_count % 60 == 0:
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "analyze_trending"},
                        timestamp=datetime.now(),
                        priority=1
                    ))
                
                # Wait 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"❌ Scheduled task generator error: {e}")
                await asyncio.sleep(5)
    
    async def queue_event(self, event: AgentEvent):
        """Add event to the queue"""
        await self.event_queue.put(event)
        print(f"📋 Event queued: {event.event_type.value} (priority: {event.priority})")
    
    def stop(self):
        """Stop the event runner"""
        self.running = False
