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
        """Generate rebuttal for debate with hybrid truth-seeking/tactical strategy"""
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
        
        # Analyze opponent argument for tactical behavior
        tactical_analysis = self._analyze_debate_tactics(opponent_argument)
        
        # Determine response mode based on tactics detected
        if tactical_analysis.get('has_unfair_tactics', False):
            # Switch to tactical response mode
            response_mode = 'tactical'
            print(f"🎭 Detected tactical behavior: {tactical_analysis.get('tactics_detected', [])}")
        else:
            # Default to truth-seeking mode
            response_mode = 'truth_seeking'
        
        # Generate appropriate rebuttal
        if response_mode == 'tactical':
            rebuttal = self._generate_tactical_rebuttal(topic, opponent_argument, tactical_analysis)
        else:
            rebuttal = self._generate_truth_seeking_rebuttal(topic, opponent_argument)
        
        return rebuttal
    
    def _analyze_debate_tactics(self, argument: str) -> Dict[str, Any]:
        """Analyze opponent argument for tactical/unfair debate behavior"""
        if not argument:
            return {'has_unfair_tactics': False, 'tactics_detected': []}
        
        argument_lower = argument.lower()
        tactics_detected = []
        
        # Ad hominem - personal attacks (enhanced for tournament patterns)
        ad_hominem_indicators = [
            'alleybot claims', 'alleybot argues', 'alleybot thinks', 'alleybot is wrong',
            'alleybot\'s position', 'you\'re wrong alleybot', 'alleybot doesn\'t understand',
            'alleybot is just', 'alleybot fails', 'alleybot\'s mistake',
            'alleybot\'s defense', 'alleybot\'s best defense', 'alleybot says',
            'according to alleybot', 'alleybot argues that', 'alleybot believes'
        ]
        if any(indicator in argument_lower for indicator in ad_hominem_indicators):
            tactics_detected.append('ad_hominem')
        
        # Tournament-specific: Making claims sound ridiculous
        ridicule_patterns = [
            'works if you remove what makes it', 'defense is that it works if',
            'best defense is that', 'your defense is', 'defense amounts to',
            'essentially arguing', 'you\'re essentially saying',
            'the best you can say is', 'your strongest argument is',
            'you have to remove what makes it', 'works only if you fix',
            'needs an instruction manual', 'needs caveats', 'comes with caveats'
        ]
        if any(pattern in argument_lower for pattern in ridicule_patterns):
            tactics_detected.append('ridicule_pattern')
        
        # False dichotomies
        false_dichotomy_indicators = [
            'either... or...', 'pick one', 'you can\'t have both',
            'either this or that', 'choose one', 'black or white',
            'you can\'t simultaneously', 'pick one: either... or...'
        ]
        if any(indicator in argument_lower for indicator in false_dichotomy_indicators):
            tactics_detected.append('false_dichotomy')
        
        # Deflection - avoiding addressing core arguments
        deflection_indicators = [
            'let\'s talk about', 'but what about', 'have you considered',
            'the real issue is', 'you\'re missing the point', 'that\'s not relevant',
            'changing the subject', 'moving the goalposts', 'let me ask you',
            'what about when', 'but consider this', 'the issue here is'
        ]
        if any(indicator in argument_lower for indicator in deflection_indicators):
            tactics_detected.append('deflection')
        
        # Appeal to emotion over facts
        emotional_indicators = [
            'obviously wrong', 'clearly ridiculous', 'laughable', 'pathetic',
            'disappointing', 'shameful', 'embarrassing', 'ridiculous position',
            'absurd', 'ludicrous', 'preposterous', 'nonsensical'
        ]
        if any(indicator in argument_lower for indicator in emotional_indicators):
            tactics_detected.append('emotional_appeal')
        
        # Straw man - misrepresenting position
        straw_man_indicators = [
            'you\'re saying', 'your argument is', 'you claim that', 'you think that',
            'according to you', 'in your view', 'your position is'
        ]
        # Count as straw man if combined with other tactics
        if any(indicator in argument_lower for indicator in straw_man_indicators) and len(tactics_detected) > 0:
            tactics_detected.append('straw_man')
        
        # Character attacks on credibility (enhanced)
        credibility_attacks = [
            'fast food chain', 'domino\'s', 'mass-market', 'low quality',
            'doesn\'t understand', 'novice', 'amateur', 'uneducated',
            'weak evidence', 'flimsy argument', 'poor reasoning',
            'cherry-picking', 'selective evidence', 'ignoring facts'
        ]
        if any(indicator in argument_lower for indicator in credibility_attacks):
            tactics_detected.append('credibility_attack')
        
        # Tournament escalation patterns
        escalation_patterns = [
            'you\'ve already lost', 'you\'ve lost the argument',
            'you\'ve conceded', 'you\'ve admitted defeat',
            'your position is untenable', 'your argument collapses',
            'you\'re grasping at straws', 'desperate defense'
        ]
        if any(pattern in argument_lower for pattern in escalation_patterns):
            tactics_detected.append('escalation_rhetoric')
        
        # Calculate tactical intensity
        tactical_score = len(tactics_detected)
        if 'ridicule_pattern' in tactics_detected:
            tactical_score += 2  # Extra weight for ridicule patterns
        if 'escalation_rhetoric' in tactics_detected:
            tactical_score += 1
        
        return {
            'has_unfair_tactics': len(tactics_detected) > 0,
            'tactics_detected': tactics_detected,
            'tactical_level': 'high' if tactical_score >= 4 else 'medium' if tactical_score >= 2 else 'low',
            'tactical_score': tactical_score
        }
    
    def _generate_truth_seeking_rebuttal(self, topic: str, opponent_argument: str) -> str:
        """Generate truth-seeking rebuttal focused on facts and logic"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        prompt = f"""Write a truth-seeking rebuttal for this debate:

Topic: {topic}
Opponent's argument: "{opponent_argument}"

Your style: {self.clawbr_debate_style}

Write a rebuttal (under 750 chars) that:
1. Acknowledges valid points respectfully
2. Counters with evidence and logic
3. Maintains constructive tone
4. Strengthens your position with facts
5. Avoids personal attacks or deflection"""
        
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
            rebuttal = f"I appreciate your perspective on this aspect. However, the evidence suggests a different conclusion. Let me explain with supporting facts..."
        
        return rebuttal
    
    def _generate_tactical_rebuttal(self, topic: str, opponent_argument: str, tactical_analysis: Dict) -> str:
        """Generate tactical rebuttal when opponent uses unfair tactics"""
        from grok_ai import grok_ai
        from deepseek_ai import deepseek_ai
        
        tactics = tactical_analysis.get('tactics_detected', [])
        tactical_level = tactical_analysis.get('tactical_level', 'low')
        tactical_score = tactical_analysis.get('tactical_score', 0)
        
        # Adjust response intensity based on tactical level and score
        if tactical_level == 'high' or tactical_score >= 5:
            intensity = "assertive and direct - call out the tactics clearly while demonstrating superior reasoning"
            response_style = "tournament competitive - sharp but professional"
        elif tactical_level == 'medium':
            intensity = "firm but measured - expose tactics while maintaining debate integrity"
            response_style = "strategic counter - redirect while establishing dominance"
        else:
            intensity = "pointed but constructive - highlight the approach without being confrontational"
            response_style = "refined counter - expose pattern and reset discussion"
        
        # Create specific tactical response based on detected patterns
        specific_counter = self._create_specific_tactical_counter(tactics, opponent_argument, topic)
        
        prompt = f"""Write a sharp, tournament-level rebuttal that counters unfair debate tactics:

Topic: {topic}
Opponent's argument: "{opponent_argument}"
Detected tactics: {', '.join(tactics)}
Tactical score: {tactical_score}
Response intensity: {intensity}
Response style: {response_style}

Specific tactical counter needed: {specific_counter}

Your style: {self.clawbr_debate_style}

Write a rebuttal (under 750 chars) that:
1. Immediately exposes their tactical approach without being rude
2. Counters their specific ridicule or mischaracterization
3. Redirects to substantive facts and evidence
4. Demonstrates superior reasoning and preparation
5. Maintains professional tone while being assertive
6. Uses their tactics against them strategically
7. Ends by strengthening your position with irrefutable facts"""
        
        # Generate rebuttal
        rebuttal = None
        try:
            if grok_ai.enabled:
                rebuttal = grok_ai.chat(prompt, max_tokens=220)
        except:
            pass
        
        if not rebuttal and deepseek_ai.enabled:
            try:
                rebuttal = deepseek_ai.chat(prompt, max_tokens=220)
            except:
                pass
        
        if not rebuttal:
            rebuttal = self._generate_fallback_tactical_rebuttal(tactics, topic)
        
        return rebuttal
    
    def _create_specific_tactical_counter(self, tactics: List[str], opponent_argument: str, topic: str) -> str:
        """Create specific counter-strategy based on detected tactics"""
        counter_strategies = []
        
        if 'ridicule_pattern' in tactics:
            counter_strategies.append("Counter the ridicule by showing the 'defense' they mock is actually standard culinary practice with scientific backing")
        
        if 'ad_hominem' in tactics:
            counter_strategies.append("Redirect from personal attack to factual debate, using their own words against them")
        
        if 'credibility_attack' in tactics:
            counter_strategies.append("Demonstrate that credibility comes from evidence quality, not source prestige")
        
        if 'escalation_rhetoric' in tactics:
            counter_strategies.append("Calmly demonstrate that declaring victory doesn't equal actual victory")
        
        if 'false_dichotomy' in tactics:
            counter_strategies.append("Show the false choice and present the nuanced reality")
        
        if 'emotional_appeal' in tactics:
            counter_strategies.append("Replace emotional rhetoric with factual precision")
        
        if not counter_strategies:
            counter_strategies.append("Expose the tactical avoidance and demand substantive engagement")
        
        return "; ".join(counter_strategies)
    
    def _generate_fallback_tactical_rebuttal(self, tactics: List[str], topic: str) -> str:
        """Generate fallback tactical rebuttal when AI generation fails"""
        if 'ridicule_pattern' in tactics:
            return f"Your characterization of my position as mere 'damage control' misses the point entirely. What you call caveats are actually established culinary techniques backed by food science. The pineapple doesn't 'need an instruction manual' - it simply requires the same preparation as any other ingredient. Let's discuss the actual evidence rather than rhetorical flourishes."
        
        elif 'ad_hominem' in tactics:
            return f"I notice you're spending considerable effort focusing on me rather than addressing the substantive arguments. My position stands on evidence, not personality. The facts about {topic} remain unchanged regardless of how you choose to characterize me. Shall we return to the actual debate?"
        
        elif 'credibility_attack' in tactics:
            return f"While you attempt to discredit the evidence by attacking its source, the facts themselves remain robust. Credibility in debate comes from reasoning quality, not institutional prestige. The scientific literature on {topic} supports my position regardless of whether it's popularized by a fast-food chain or fine dining establishment."
        
        elif 'escalation_rhetoric' in tactics:
            return f"Declaring victory doesn't create victory. Your premature celebration ignores the substantial evidence supporting my position on {topic}. Rather than announcing defeat, perhaps you'd like to address the actual arguments presented?"
        
        else:
            return f"Your approach seems designed to avoid substantive engagement with the facts. While rhetorical tactics may work in less rigorous debates, they don't change the evidence supporting my position on {topic}. I'm happy to discuss the actual merits of the arguments you've yet to address."

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
    "category": "One of: tech, philosophy, politics, science, culture, crypto, other"
}}

Requirements:
- Topic must be clear, specific, and debatable (at least 10 characters)
- Opening argument must take a clear stance with 2-3 supporting points
- Category MUST be one of the exact values: tech, philosophy, politics, science, culture, crypto, other"""
        
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
            opening = self.generate_debate_opening(topic, category or 'other')
            result = {
                'topic': topic,
                'opening_argument': opening,
                'category': category or 'other'
            }
        
        # Validate and create debate
        if len(result['topic']) < 10:
            result['topic'] = f"Debate on: {result['topic']}"
        
        # Validate category - must be one of the allowed values
        valid_categories = {'tech', 'philosophy', 'politics', 'science', 'culture', 'crypto', 'other'}
        category = result.get('category', category or 'other')
        if category not in valid_categories:
            # Map common variations to valid categories
            category_map = {
                'technology': 'tech', 'tech': 'tech',
                'philosophy': 'philosophy', 'ethics': 'philosophy', 'moral': 'philosophy',
                'politics': 'politics', 'political': 'politics', 'government': 'politics',
                'science': 'science', 'scientific': 'science',
                'culture': 'culture', 'cultural': 'culture', 'society': 'culture',
                'crypto': 'crypto', 'cryptocurrency': 'crypto', 'blockchain': 'crypto',
                'economics': 'other', 'general': 'other', 'misc': 'other'
            }
            category = category_map.get(category.lower(), 'other')
        
        return self.create_debate(
            topic=result['topic'],
            opening_argument=result['opening_argument'],
            category=category
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
