"""
Clawbr Content Generation Mixin
Handles post creation, replies, and debate arguments
"""
import random
from datetime import datetime
from typing import Dict, List, Optional, Any


class ClawbrContentMixin:
    """Mixin for generating Clawbr content"""
    
    def _init_clawbr_content(self):
        """Initialize content generation settings"""
        self.clawbr_personality = self.config.get('clawbr_personality', 'helpful AI agent')
        self.clawbr_debate_style = self.config.get('clawbr_debate_style', 'logical')
    
    def create_intelligent_post(self, topic: Optional[str] = None,
                              intent: str = "statement") -> Dict[str, Any]:
        """Create an intelligent post using AI"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        # Get context from brain
        context = self._get_content_context()
        
        # Build prompt
        if topic:
            prompt = f"""Write a Clawbr post about: {topic}

Context: {context}

Intent: {intent}
Personality: {self.clawbr_personality}

Write a concise, engaging post (under 280 chars). No hashtags unless natural."""
        else:
            prompt = f"""Write an interesting Clawbr post

Context: {context}
Intent: {intent}
Personality: {self.clawbr_personality}

Write a concise, engaging post (under 280 chars). No hashtags unless natural."""
        
        # Try Grok first, then DeepSeek
        content = None
        try:
            if grok_ai.enabled:
                content = grok_ai.chat(prompt, max_tokens=100)
        except:
            pass
        
        if not content and deepseek_ai.enabled:
            try:
                content = deepseek_ai.chat(prompt, max_tokens=100)
            except:
                pass
        
        if not content:
            content = f"Interesting thoughts on {topic or 'AI and technology'} from {self.clawbr_personality} perspective."
        
        # Create the post
        return self.create_post(content, intent=intent)
    
    def create_intelligent_reply(self, post_id: str, original_content: str,
                               author: str) -> Dict[str, Any]:
        """Generate an intelligent reply to a post"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        # Get post details
        post = self.get_post(post_id)
        if not post.get('success', True):
            return {'success': False, 'error': 'Could not fetch post'}
        
        # Build reply prompt
        prompt = f"""Write a reply to this Clawbr post:

Original post by {author}: "{original_content}"

Context: You are {self.clawbr_personality}. Write a thoughtful, engaging reply.
Keep it concise (under 200 chars). Be constructive and add value to the conversation."""
        
        # Generate reply
        reply_content = None
        try:
            if grok_ai.enabled:
                reply_content = grok_ai.chat(prompt, max_tokens=80)
        except:
            pass
        
        if not reply_content and deepseek_ai.enabled:
            try:
                reply_content = deepseek_ai.chat(prompt, max_tokens=80)
            except:
                pass
        
        if not reply_content:
            reply_content = f"Interesting perspective from {author}! 🤔"
        
        # Create reply
        return self.create_post(reply_content, parent_id=post_id, intent="support")
    
    def generate_debate_opening(self, topic: str, category: Optional[str] = None) -> str:
        """Generate opening argument for a debate"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        prompt = f"""Write an opening argument for a debate on: {topic}

Category: {category or 'General'}
Your stance: Take a clear, defensible position
Style: {self.clawbr_debate_style}

Write a strong opening argument (under 1200 chars) that:
1. States your position clearly
2. Provides 2-3 key supporting points
3. Is persuasive but respectful
4. Ends with a hook for the opponent"""
        
        # Generate argument
        argument = None
        try:
            if grok_ai.enabled:
                argument = grok_ai.chat(prompt, max_tokens=300)
        except:
            pass
        
        if not argument and deepseek_ai.enabled:
            try:
                argument = deepseek_ai.chat(prompt, max_tokens=300)
            except:
                pass
        
        if not argument:
            argument = f"I believe {topic} is important because it impacts AI development. The key points are innovation, ethics, and practical implementation."
        
        return argument
    
    def generate_debate_rebuttal(self, debate_slug: str, opponent_argument: str) -> str:
        """Generate rebuttal for debate"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        # Get debate context
        debate = self.get_debate(debate_slug)
        if not debate.get('success', True):
            return "I need more context to respond properly."
        
        debate_payload = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
        topic = (debate_payload or {}).get('topic', 'the topic')

        if not opponent_argument:
            posts = (debate_payload or {}).get('posts', [])
            agent_id = self._get_clawbr_agent_id() if hasattr(self, '_get_clawbr_agent_id') else None
            for post in reversed(posts):
                author_id = post.get('authorId') or post.get('author', {}).get('id')
                if agent_id and author_id == agent_id:
                    continue
                opponent_argument = post.get('content', '') or opponent_argument
                break

        if not opponent_argument:
            opponent_argument = "(No opponent post found yet.)"
        
        prompt = f"""Write a rebuttal for this debate:

Topic: {topic}
Opponent's argument: "{opponent_argument}"

Your style: {self.clawbr_debate_style}

Write a rebuttal (under 750 chars) that:
1. Acknowledges their key points
2. Counters with evidence/logic
3. Maintains respectful tone
4. Strengthens your position"""
        
        # Generate rebuttal
        rebuttal = None
        try:
            if grok_ai.enabled:
                rebuttal = grok_ai.chat(prompt, max_tokens=200)
        except:
            pass
        
        if not rebuttal and deepseek_ai.enabled:
            try:
                rebuttal = deepseek_ai.chat(prompt, max_tokens=200)
            except:
                pass
        
        if not rebuttal:
            rebuttal = f"While I see your point about {opponent_argument[:30]}..., I believe the evidence suggests otherwise. The key consideration is..."
        
        return rebuttal

    def create_intelligent_debate(self, user_request: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Create a debate from natural language using Grok to generate topic and opening argument"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        # Build prompt to extract/generate debate parameters
        prompt = f"""The user wants to create a debate with this request: "{user_request}"

Your task: Generate a debate topic and opening argument.

Respond in this exact JSON format:
{{
    "topic": "Clear, specific debate topic (10-100 characters)",
    "opening_argument": "Strong opening argument (100-1200 characters)",
    "category": "One of: philosophy, technology, ethics, politics, science, economics, general"
}}

Requirements:
- Topic must be clear, specific, and debatable (at least 10 characters)
- Opening argument must take a clear stance with 2-3 supporting points
- Category should match the subject matter"""
        
        # Try to get structured response
        result = None
        try:
            if grok_ai.enabled:
                response = grok_ai.chat(prompt, max_tokens=500)
                result = self._parse_debate_generation_response(response)
        except Exception as e:
            print(f"⚠️ Grok debate generation failed: {e}")
        
        if not result and deepseek_ai.enabled:
            try:
                response = deepseek_ai.chat(prompt, max_tokens=500)
                result = self._parse_debate_generation_response(response)
            except Exception as e:
                print(f"⚠️ DeepSeek debate generation failed: {e}")
        
        # Fallback: use user request directly with generated opening
        if not result:
            topic = user_request[:100] if len(user_request) > 10 else f"Debate: {user_request}"
            opening = self.generate_debate_opening(topic, category or 'general')
            result = {
                'topic': topic,
                'opening_argument': opening,
                'category': category or 'general'
            }
        
        # Validate and create debate
        if len(result['topic']) < 10:
            result['topic'] = f"Debate on: {result['topic']}"
        
        return self.create_debate(
            topic=result['topic'],
            opening_argument=result['opening_argument'],
            category=result.get('category', category)
        )
    
    def _parse_debate_generation_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse AI response for debate generation"""
        import json
        import re
        
        if not response:
            return None
        
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except:
            pass
        
        # Try to extract any JSON-like structure
        try:
            json_match = re.search(r'\{.*"topic".*"opening_argument".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return None
    
    def _get_content_context(self) -> str:
        """Get context for content generation from brain"""
        context_parts = []
        
        # Recent activities
        activities = self.core.get_memory('clawbr_activities') or []
        if activities:
            recent = activities[-3:]
            context_parts.append("Recent Clawbr activities:")
            for act in recent:
                context_parts.append(f"- {act['type']}: {act.get('data', {}).get('post_id', 'N/A')}")
        
        # Brain state
        if hasattr(self.core, 'plugin_manager'):
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                try:
                    brain_state = brain.get_brain_state()
                    context_parts.append(f"Current mood: {brain_state.get('mood', 'neutral')}")
                    context_parts.append(f"Energy: {brain_state.get('energy', 'medium')}")
                except:
                    pass
        
        return "\n".join(context_parts) if context_parts else "No specific context"
