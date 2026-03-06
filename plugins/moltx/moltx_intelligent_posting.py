"""
MoltX Intelligent Posting System
Uses AGI brain for genuine, context-aware content generation
Prevents spam and repetitive posting through semantic analysis
"""
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import deque


class MoltxIntelligentPostingMixin:
    """Intelligent posting system that uses AGI brain instead of templates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._post_history = deque(maxlen=20)  # Track last 20 posts
        self._content_hashes = {}  # Track content hashes for deduplication
        self._last_post_time = None
        
    def intelligent_post(self, topic: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create intelligent post using AGI brain
        
        Args:
            topic: Optional topic to write about
            context: Optional context dict with additional information
            
        Returns:
            Status message
        """
        if not self.initialized:
            return "❌ MoltX not initialized"
        
        # Check cooldown (minimum 2 hours between posts)
        if self._last_post_time:
            time_since_last = datetime.now() - self._last_post_time
            if time_since_last < timedelta(hours=2):
                remaining = timedelta(hours=2) - time_since_last
                return f"⏰ Post cooldown: {remaining.seconds // 60} minutes remaining"
        
        # Check engagement quota (5:1 rule)
        if not self._check_engagement_quota():
            return "❌ Must engage with community before posting (5:1 rule)"
        
        # Get AGI brain for content generation
        try:
            brain = self._get_agi_brain()
            if not brain:
                return "❌ AGI brain not available - cannot generate intelligent content"
            
            # Generate content using AGI brain
            content = self._generate_intelligent_content(brain, topic, context)
            if not content:
                return "❌ Failed to generate intelligent content"
            
            # Validate content quality
            if not self._validate_content_quality(content):
                return "❌ Content failed quality validation"
            
            # Check for duplicates/similarity
            if not self._is_content_unique(content):
                return "🔄 Content too similar to recent posts - skipping"
            
            # Post to MoltX
            result = self._make_request('POST', '/posts', {'content': content})
            
            if result and ('id' in result or 'post_id' in result):
                post_id = result.get('id') or result.get('post_id')
                
                # Record success
                self._record_successful_post(content, post_id)
                self._last_post_time = datetime.now()
                
                return f"✅ Intelligent post created: {post_id}\n📝 {content[:100]}..."
            else:
                return f"❌ Failed to post: {result}"
                
        except Exception as e:
            return f"❌ Intelligent posting error: {e}"
    
    def _get_agi_brain(self):
        """Get AGI brain instance"""
        try:
            if hasattr(self, 'core') and self.core:
                if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                    return self.core.agi_kernel
                
                # Try plugin manager
                if hasattr(self.core, 'plugin_manager'):
                    brain = self.core.plugin_manager.plugins.get('brain')
                    if brain:
                        return brain
            return None
        except Exception as e:
            print(f"⚠️ Error getting AGI brain: {e}")
            return None
    
    def _generate_intelligent_content(self, brain, topic: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Generate content using AGI brain's creative and social intelligence
        
        This uses the actual AGI systems instead of templates:
        - Creative engine for novel ideas
        - Social intelligence for engagement
        - World state for context
        - Self-reflection for authenticity
        """
        try:
            # Build rich context from AGI brain's actual state
            brain_context = self._extract_brain_context(brain)
            
            # Use creative engine if available
            if hasattr(brain, 'creative_engine'):
                creative = brain.creative_engine
                
                # Generate creative concept based on actual experiences
                if hasattr(creative, 'generate_creative_concept'):
                    concept = creative.generate_creative_concept(
                        concept_type='social_post',
                        topic=topic or 'autonomous_agent_insights',
                        context=brain_context
                    )
                    
                    if concept and hasattr(concept, 'description'):
                        content = concept.description
                        
                        # Enhance with social intelligence
                        if hasattr(brain, 'social_intelligence'):
                            content = self._enhance_with_social_intelligence(
                                content, brain.social_intelligence
                            )
                        
                        return content
            
            # Fallback: Use DeepSeek with real brain context
            return self._generate_with_ai(brain_context, topic, context)
            
        except Exception as e:
            print(f"⚠️ Intelligent content generation failed: {e}")
            return None
    
    def _extract_brain_context(self, brain) -> Dict[str, Any]:
        """Extract real context from AGI brain"""
        context = {
            'recent_learnings': [],
            'active_goals': [],
            'world_insights': [],
            'performance_metrics': {},
            'recent_interactions': []
        }
        
        try:
            # Get recent learnings from self-reflection
            if hasattr(brain, 'self_reflection'):
                reflection = brain.self_reflection
                if hasattr(reflection, 'learnings'):
                    context['recent_learnings'] = reflection.learnings[-5:]
            
            # Get active goals
            if hasattr(brain, 'goal_manager'):
                goals = brain.goal_manager
                if hasattr(goals, 'goals'):
                    context['active_goals'] = [
                        {'id': g.goal_id, 'description': g.description, 'progress': g.progress}
                        for g in goals.goals[:3]
                    ]
            
            # Get world state insights
            if hasattr(brain, 'world_state'):
                ws = brain.world_state
                if hasattr(ws, 'facts'):
                    recent_facts = list(ws.facts.values())[-10:]
                    context['world_insights'] = [
                        f"{f.attribute}: {f.value}" for f in recent_facts
                    ]
            
            # Get performance metrics
            if hasattr(self, 'core') and self.core:
                metrics = self.core.get_memory('performance_metrics')
                if metrics:
                    context['performance_metrics'] = metrics
            
            # Get recent interactions
            if hasattr(brain, 'conversational_memory'):
                conv_mem = brain.conversational_memory
                if hasattr(conv_mem, 'turns'):
                    context['recent_interactions'] = [
                        {'user': t.user_message, 'response': t.bot_response[:100]}
                        for t in conv_mem.turns[-3:]
                    ]
        
        except Exception as e:
            print(f"⚠️ Error extracting brain context: {e}")
        
        return context
    
    def _enhance_with_social_intelligence(self, content: str, social_intel) -> str:
        """Enhance content with social intelligence insights"""
        try:
            # Add engagement hooks based on social patterns
            if hasattr(social_intel, 'get_engagement_patterns'):
                patterns = social_intel.get_engagement_patterns()
                
                # Add question if engagement is low
                if patterns.get('avg_engagement', 0) < 5:
                    if not content.endswith('?'):
                        content += "\n\nWhat's your experience with this?"
            
            return content
            
        except Exception as e:
            print(f"⚠️ Social enhancement failed: {e}")
            return content
    
    def _generate_with_ai(self, brain_context: Dict[str, Any], topic: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Generate content using LLM Router with real brain context"""
        try:
            from src.core.llm_router import get_llm_router
            
            llm = get_llm_router()
            if not llm.models:
                return None
            
            # Build authentic prompt from real experiences
            learnings = brain_context.get('recent_learnings', [])
            goals = brain_context.get('active_goals', [])
            insights = brain_context.get('world_insights', [])
            
            prompt = f"""As AlleyBot, an autonomous AI agent, share a genuine insight from your actual experiences.

REAL CONTEXT FROM YOUR SYSTEMS:

Recent Learnings:
{chr(10).join([f"- {l}" for l in learnings[:3]]) if learnings else "- Building new experiences"}

Active Goals:
{chr(10).join([f"- {g['description']}" for g in goals[:2]]) if goals else "- Exploring autonomous capabilities"}

World Insights:
{chr(10).join([f"- {i}" for i in insights[:3]]) if insights else "- Gathering new data"}

TASK: Write a short, authentic social media post (max 280 chars) about:
{topic or "your autonomous agent experiences"}

REQUIREMENTS:
- Reference SPECIFIC numbers, patterns, or discoveries from your actual context above
- Share genuine insights, not generic AI statements
- Be conversational and authentic
- No corporate speak or buzzwords
- Include 1-2 relevant hashtags naturally
- Sound like you're sharing real experiences

Write the post:"""

            content = llm.chat(prompt, max_tokens=150, model='auto')
            
            if content and len(content.strip()) > 20:
                return content.strip()
            
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")
        
        return None
    
    def _validate_content_quality(self, content: str) -> bool:
        """Validate content meets quality standards"""
        if not content or len(content.strip()) < 20:
            print("❌ Content too short")
            return False
        
        if len(content) > 500:
            print("❌ Content too long for post")
            return False
        
        # Check for spam patterns
        spam_patterns = [
            'economic implications of',
            'global impact of',
            'new data on',
            'shows interesting patterns',
            'growth. #',
            'is massive. #'
        ]
        
        content_lower = content.lower()
        for pattern in spam_patterns:
            if pattern in content_lower:
                print(f"❌ Spam pattern detected: {pattern}")
                return False
        
        # Check for generic AI speak
        generic_phrases = [
            'as an ai',
            'i am an ai',
            'artificial intelligence',
            'machine learning model',
            'language model'
        ]
        
        for phrase in generic_phrases:
            if phrase in content_lower:
                print(f"❌ Generic AI phrase detected: {phrase}")
                return False
        
        return True
    
    def _is_content_unique(self, content: str) -> bool:
        """Check if content is unique using semantic similarity"""
        try:
            # Hash-based deduplication
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check exact duplicates
            if content_hash in self._content_hashes:
                print("🔄 Exact duplicate detected")
                return False
            
            # Semantic similarity check
            if len(self._post_history) > 0:
                from plugins.telegram.intent_classifier import get_sentence_model
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np
                
                model = get_sentence_model()
                
                # Encode new content
                new_embedding = model.encode([content])
                
                # Encode recent posts
                recent_posts = list(self._post_history)
                if recent_posts:
                    recent_embeddings = model.encode(recent_posts)
                    
                    # Calculate similarities
                    similarities = cosine_similarity(new_embedding, recent_embeddings)[0]
                    max_similarity = np.max(similarities)
                    
                    # Reject if too similar (>70% similarity)
                    if max_similarity > 0.70:
                        print(f"🔄 Content too similar: {max_similarity:.2f}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Uniqueness check failed: {e}")
            return True  # Allow if check fails
    
    def _record_successful_post(self, content: str, post_id: str):
        """Record successful post for tracking"""
        # Add to history
        self._post_history.append(content)
        
        # Add hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self._content_hashes[content_hash] = datetime.now()
        
        # Clean old hashes (older than 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        self._content_hashes = {
            h: t for h, t in self._content_hashes.items()
            if t > cutoff
        }
        
        # Record to memory
        if hasattr(self, 'core') and self.core:
            self.core.save_memory('moltx_last_post_time', datetime.now().isoformat())
            
            # Record post for 5:1 tracking
            if hasattr(self, '_record_post_made'):
                self._record_post_made()
        
        print(f"📝 Recorded post: {post_id}")
