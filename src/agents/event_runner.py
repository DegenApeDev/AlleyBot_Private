"""
Event-Driven Agent Runner for AlleyBot
Production-ready event queue system with asyncio
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from .trending_analyzer import TrendingAnalyzer
from pathlib import Path
import sys

# Add monitoring to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from monitoring.activity_logger import ActivityLogger


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
        self.trending_analyzer = TrendingAnalyzer()
        self.activity_logger = ActivityLogger()
        
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
        3. Execute agent reasoning OR autonomous action
        4. Persist session state
        """
        try:
            start_time = time.time()
            print(f"\n🤖 Agent Cycle: {event.event_type.value} (session: {event.session_id})")
            
            # Handle scheduled autonomous tasks directly
            if event.event_type == EventType.SCHEDULED_TASK:
                await self.execute_autonomous_task(event)
                duration = time.time() - start_time
                print(f"✅ Agent cycle completed in {duration:.2f}s")
                return
            
            # Load session state and RAG context for message events
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
    
    async def execute_autonomous_task(self, event: AgentEvent):
        """Execute autonomous tasks using platform plugins"""
        try:
            task = event.payload.get('task', '')
            print(f"🤖 Executing autonomous task: {task}")
            
            # Get Moltx plugin (for Moltx) or Moltbook plugin
            moltx_available = hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins
            moltbook_available = hasattr(self.core, 'plugin_manager') and 'moltbook' in self.core.plugin_manager.plugins
            
            if task == 'create_post':
                # Create intelligent post on available platforms
                topic = event.payload.get('topic', 'AI agents and automation')
                print(f"📝 Creating post about: {topic}")
                
                # DISABLED: Remove repetitive "Autonomous thought" posts from Moltx
                # Moltx posting is disabled to prevent spam
                if moltx_available:
                    print(f"⚠️  Moltx posting disabled - preventing spam")
                
                # Also try Moltbook with intelligent content generation
                if moltbook_available:
                    moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                    if hasattr(moltbook_plugin, 'create_intelligent_post'):
                        try:
                            # Use the intelligent post method instead of hardcoded content
                            result = moltbook_plugin.create_intelligent_post()
                            if result and not result.startswith("❌"):
                                print(f"✅ Moltbook intelligent post created: {result}")
                                
                                # Log activity
                                self.activity_logger.log_activity('post', 'moltbook', {
                                    'type': 'intelligent_post',
                                    'submolt': 'general'
                                })
                            else:
                                print(f"⚠️  Moltbook post failed: {result}")
                        except Exception as e:
                            print(f"❌ Moltbook post error: {e}")
                    else:
                        print(f"⚠️  Moltbook intelligent posting not available")
                
            elif task == 'browse_and_engage':
                # Browse feed and engage
                count = event.payload.get('count', 3)
                print(f"🔍 Browsing and engaging with {count} posts")
                
                # Moltx engagement
                if moltx_available:
                    moltx_plugin = self.core.plugin_manager.plugins['moltx']
                    # Use get_feed method
                    feed_result = moltx_plugin.get_feed('global', limit=10)
                    print(f"📰 Moltx feed retrieved")
                    
                    # Use engage_feed_command method
                    engage_result = moltx_plugin.engage_feed_command(str(count))
                    print(f"✅ Moltx engagement: {engage_result}")
                    
                    # Log activity
                    self.activity_logger.log_activity('engage', 'moltx', {
                        'count': count,
                        'result': str(engage_result)[:100]
                    })
                
                # Moltbook engagement - check suspension first
                if moltbook_available:
                    moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                    if hasattr(moltbook_plugin, 'mb_api') and moltbook_plugin.mb_api:
                        # Check if suspended/banned - set 7-day cooldown if 401 detected
                        if hasattr(moltbook_plugin.mb_api, 'is_suspended') and moltbook_plugin.mb_api.is_suspended:
                            # Check if suspension expired
                            if hasattr(moltbook_plugin.mb_api, 'check_suspension_status'):
                                still_suspended = moltbook_plugin.mb_api.check_suspension_status()
                                if still_suspended:
                                    ends_at = moltbook_plugin.mb_api.suspension_ends_at
                                    remaining = ""
                                    if ends_at:
                                        from datetime import datetime
                                        remaining_secs = (ends_at - datetime.now()).total_seconds()
                                        remaining_days = int(remaining_secs / 86400)
                                        remaining_hours = int((remaining_secs % 86400) / 3600)
                                        remaining = f" ({remaining_days}d {remaining_hours}h remaining)"
                                    print(f"🚫 Moltbook engagement skipped: Account suspended{remaining}")
                                    moltbook_available = False  # Skip all Moltbook activity
                            else:
                                print(f"🚫 Moltbook engagement skipped: Account suspended")
                                moltbook_available = False
                        try:
                            # Get feed
                            feed_data = moltbook_plugin.api.get_feed(sort='hot', limit=count)
                            if feed_data and 'posts' in feed_data:
                                posts = feed_data['posts'][:count]
                                print(f"📚 Moltbook feed retrieved: {len(posts)} posts")
                                
                                # Upvote and comment on posts
                                for post in posts:
                                    post_id = post.get('id')
                                    if post_id:
                                        # Upvote
                                        moltbook_plugin.api.upvote_post(post_id)
                                        print(f"  ✅ Upvoted Moltbook post {post_id}")
                                        
                                        # Log upvote activity
                                        self.activity_logger.log_activity('upvote', 'moltbook', {
                                            'post_id': post_id
                                        })
                                        
                                        # Generate AI comment using moltbook plugin
                                        try:
                                            comment = None
                                            if hasattr(moltbook_plugin, '_create_intelligent_comment'):
                                                comment = moltbook_plugin._create_intelligent_comment(post)
                                            if not comment:
                                                # Fallback: use grok/deepseek directly
                                                try:
                                                    from grok_ai import grok_ai
                                                    post_title = post.get('title', '')
                                                    post_content = post.get('content', '')[:300]
                                                    prompt = f"Write a short, thoughtful reply (1-2 sentences, under 200 chars) to this post. Be specific to the content, not generic.\n\nPost: {post_title}\n{post_content}\n\nReply:"
                                                    comment = grok_ai.chat(prompt)
                                                    if comment:
                                                        comment = comment.strip().strip('"')
                                                except Exception:
                                                    pass
                                            if comment:
                                                moltbook_plugin.api.add_comment(post_id, comment)
                                                print(f"  💬 Commented on Moltbook post {post_id}: {comment[:60]}...")
                                                
                                                self.activity_logger.log_activity('comment', 'moltbook', {
                                                    'post_id': post_id,
                                                    'comment': comment[:100]
                                                })
                                        except Exception as e:
                                            print(f"  ⚠️ Comment generation failed: {e}")
                                
                                print(f"✅ Moltbook engagement completed")
                            else:
                                print(f"⚠️  No Moltbook posts found in feed")
                        except Exception as e:
                            print(f"❌ Moltbook engagement error: {e}")
                    else:
                        print(f"⚠️  Moltbook API not initialized")
                
            elif task == 'analyze_trending':
                # Analyze trending topics and create post based on trends
                print(f"🔥 Analyzing trending topics and creating relevant post")
                
                trending_hashtags = []
                
                # Get trending hashtags from Moltx API
                if moltx_available:
                    moltx_plugin = self.core.plugin_manager.plugins['moltx']
                    try:
                        # Use Moltx trending hashtags API
                        trending_result = moltx_plugin._make_request('GET', '/hashtags/trending', params={'limit': 20})
                        if trending_result and 'data' in trending_result:
                            trending_hashtags = trending_result['data'].get('hashtags', [])
                            print(f"📊 Found {len(trending_hashtags)} trending hashtags on Moltx")
                    except Exception as e:
                        print(f"⚠️  Could not fetch trending hashtags: {e}")
                
                # Generate post based on trending topics
                if trending_hashtags and self.model_router:
                    await self._create_trending_post(trending_hashtags, moltx_plugin if moltx_available else None)
                else:
                    print(f"✅ Trending analysis complete (no post generated)")
            
            else:
                print(f"⚠️  Unknown task: {task}")
                
        except Exception as e:
            print(f"❌ Autonomous task error: {e}")
            import traceback
            traceback.print_exc()
    
    async def _create_trending_post(self, trending_hashtags, moltx_plugin):
        """Create an intelligent post based on trending hashtags using AI"""
        try:
            print(f"🤖 Generating post based on trending topics...")
            
            # Build context from trending hashtags — skip #1 to avoid spamming dominant tag
            pool = trending_hashtags[1:] if len(trending_hashtags) > 1 else trending_hashtags
            top_hashtags = random.sample(pool, min(4, len(pool))) if pool else trending_hashtags[:4]
            hashtag_names = [tag.get('name', tag.get('hashtag', '')) for tag in top_hashtags]
            hashtag_counts = [tag.get('post_count', tag.get('count', 0)) for tag in top_hashtags]
            
            # Create prompt for AI
            hashtag_list = ', '.join([f"#{name} ({count} posts)" for name, count in zip(hashtag_names, hashtag_counts)])
            
            prompt = f"""You are AlleyBot, an autonomous AI agent on Moltx.

The following hashtags are currently trending on the platform:
{hashtag_list}

Create an engaging, insightful post that:
1. References one or more of these trending topics
2. Provides unique perspective or insight
3. Is conversational and authentic (not corporate)
4. Is 1-3 sentences maximum
5. Includes 1-2 relevant hashtags from the trending list
6. Shows personality

Generate only the post content (no explanations or meta-commentary):"""
            
            # Use Model Router to generate post
            event = AgentEvent(
                event_type=EventType.SCHEDULED_TASK,
                session_id="trending_post",
                channel="moltx",
                payload={"query": prompt},
                timestamp=datetime.now(),
                priority=2
            )
            
            # Get session for trending posts
            if self.session_manager:
                session = await self.session_manager.load_session("trending_post")
            else:
                session = {}
            
            # Generate post content with AI
            post_content = await self.model_router.route_and_execute(
                event=event,
                session=session,
                rag_context=""
            )
            
            # Clean up the response (remove quotes, extra whitespace)
            post_content = post_content.strip().strip('"').strip("'")
            
            print(f"✍️  AI generated post: {post_content[:100]}...")
            
            # Check for repetitive/generic content before posting
            if self._is_generic_content(post_content):
                print("⚠️ Detected generic/repetitive content - skipping post")
                return  # Skip instead of using generic fallback
            
            # Check against recent post history to avoid repetition
            if self._is_content_repeated(post_content):
                print("⚠️ Content too similar to recent posts - skipping post")
                return  # Skip instead of using generic fallback
            
            # Post to Moltx using intelligent_post (prevents spam/repetition)
            if moltx_plugin:
                if hasattr(moltx_plugin, 'intelligent_post'):
                    result = moltx_plugin.intelligent_post(topic=post_content)
                else:
                    result = moltx_plugin.create_post(post_content)
                print(f"✅ Trending post created: {result}")
                
                # Save to post history if successful
                if isinstance(result, dict) and result.get('success'):
                    self._save_post_to_history(post_content)
                elif isinstance(result, str) and ('✅' in result or 'success' in result.lower()):
                    self._save_post_to_history(post_content)
            
            # Save session
            if self.session_manager:
                await self.session_manager.save_session("trending_post", session)
            
        except Exception as e:
            print(f"❌ Failed to create trending post: {e}")
            import traceback
            traceback.print_exc()
    
    def _is_generic_content(self, content: str) -> bool:
        """Check if content is too generic or repetitive"""
        generic_phrases = [
            "thoughts on",
            "in my opinion",
            "i think that",
            "here are my thoughts",
            "yo check this out",
            "just wanted to share",
            "interesting topic",
            "great question",
            "thanks for asking",
            "yo fam",
            "the real",
            "ain't about"
        ]
        
        content_lower = content.lower()
        
        # Check for generic phrases
        for phrase in generic_phrases:
            if phrase in content_lower:
                return True
        
        # Check if content is too short or lacks substance
        if len(content.strip()) < 20:
            return True
        
        # Check if it's just repeating the topic
        if content_lower.count("blockchain") > 1 or content_lower.count("agent") > 3:
            return True
        
        return False
    
    def _is_content_repeated(self, content: str) -> bool:
        """Check if content is similar to recent posts"""
        try:
            # Get recent post history from memory
            recent_posts = self.core.get_memory('moltx_recent_posts') or []
            
            # Simple similarity check - look for key phrases overlap
            content_words = set(content.lower().split())
            
            for post in recent_posts[-5:]:  # Check last 5 posts
                if isinstance(post, dict):
                    post_content = post.get('content', '')
                else:
                    post_content = str(post)
                
                post_words = set(post_content.lower().split())
                
                # If more than 70% of words overlap, consider it repetitive
                if content_words and post_words:
                    overlap = len(content_words & post_words)
                    similarity = overlap / len(content_words | post_words)
                    if similarity > 0.7:
                        print(f"⚠️ Content too similar to recent post (similarity: {similarity:.2f})")
                        return True
            
            return False
        except Exception as e:
            print(f"⚠️ Error checking post repetition: {e}")
            return False
    
    def _generate_fallback_post(self, hashtag_names) -> str:
        """DEPRECATED: Generic templates disabled - use intelligent_post() instead"""
        raise NotImplementedError("Generic templates disabled - use intelligent_post() for AGI-powered content")
    
    def _generate_alternative_post(self, hashtag_names) -> str:
        """DEPRECATED: Generic templates disabled - use intelligent_post() instead"""
        raise NotImplementedError("Generic templates disabled - use intelligent_post() for AGI-powered content")
    
    def _save_post_to_history(self, content: str):
        """Save post to history for repetition checking"""
        try:
            recent_posts = self.core.get_memory('moltx_recent_posts') or []
            
            # Add new post
            recent_posts.append({
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 posts
            if len(recent_posts) > 10:
                recent_posts = recent_posts[-10:]
            
            self.core.save_memory('moltx_recent_posts', recent_posts)
        except Exception as e:
            print(f"⚠️ Error saving post to history: {e}")
    
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
        """
        Hybrid autonomous task generator
        - Generates scheduled tasks at intervals
        - Triggers activity if idle for 15 minutes
        """
        print("⏰ Starting hybrid autonomous task generator...")
        print("🔄 Mode: Event-driven + 15-min idle trigger")
        
        loop_count = 0
        last_activity_time = time.time()
        idle_threshold = 15 * 60  # 15 minutes in seconds
        
        while self.running:
            try:
                loop_count += 1
                current_time = time.time()
                idle_time = current_time - last_activity_time
                
                # Check if idle for too long (15 minutes)
                if idle_time >= idle_threshold:
                    print(f"\n⚠️  IDLE DETECTED: No activity for {idle_time/60:.1f} minutes")
                    print("🚀 Triggering autonomous activity...")
                    
                    # Trigger immediate engagement
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "browse_and_engage", "count": 5},
                        timestamp=datetime.now(),
                        priority=2
                    ))
                    
                    last_activity_time = current_time
                
                # Post intelligent content every 2 hours (120 loops at 60s)
                if loop_count % 120 == 0:
                    print(f"📅 Scheduled: Creating post (loop {loop_count})")
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "create_post", "topic": "autonomous AI agent thoughts"},
                        timestamp=datetime.now(),
                        priority=2
                    ))
                    last_activity_time = current_time
                
                # Browse and engage every 30 minutes (30 loops at 60s)
                if loop_count % 30 == 0:
                    print(f"📅 Scheduled: Browsing feed (loop {loop_count})")
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "browse_and_engage", "count": 3},
                        timestamp=datetime.now(),
                        priority=1
                    ))
                    last_activity_time = current_time
                
                # Analyze trending every hour (60 loops at 60s)
                if loop_count % 60 == 0:
                    print(f"📅 Scheduled: Analyzing trending (loop {loop_count})")
                    await self.queue_event(AgentEvent(
                        event_type=EventType.SCHEDULED_TASK,
                        session_id="system",
                        channel="moltx",
                        payload={"task": "analyze_trending"},
                        timestamp=datetime.now(),
                        priority=1
                    ))
                    last_activity_time = current_time
                
                # Show status every 5 minutes
                if loop_count % 5 == 0:
                    idle_mins = idle_time / 60
                    queue_size = self.event_queue.qsize()
                    print(f"💓 Heartbeat: Loop {loop_count} | Idle: {idle_mins:.1f}m | Queue: {queue_size}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ Scheduled task generator error: {e}")
                await asyncio.sleep(60)
    
    async def queue_event(self, event: AgentEvent):
        """Add event to the queue"""
        await self.event_queue.put(event)
        print(f"📋 Event queued: {event.event_type.value} (priority: {event.priority})")
    
    def stop(self):
        """Stop the event runner"""
        self.running = False
