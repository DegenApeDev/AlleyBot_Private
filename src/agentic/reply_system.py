"""
Reply System - Intelligent AI-powered reply generation for AGI Kernel

Extracted from plugins/brain/smart_reply.py to centralize intelligence.
Generates context-aware, memory-enriched replies with SyMod validation.

Key Features:
- Memory-enriched reply generation
- User profile tracking and personalization
- Multi-AI support (Grok, DeepSeek)
- SyMod C2V validation for truth checking
- On-chain context integration
- Semantic memory search for relevant past interactions

SOP Compliance:
- This is an AGI Kernel component (src/agentic/), not a plugin
- No decision logic - just reply generation
- Uses unified memory (no persistent state)
- Follows existing pattern from context_system.py
"""

import datetime
from typing import Optional, Dict, Any

# SyMod C2V Bridge integration
try:
    from src.synergy import get_c2v_bridge
    C2V_AVAILABLE = True
except ImportError:
    C2V_AVAILABLE = False


class ReplySystem:
    """
    Intelligent reply generation system for AGI Kernel.
    
    Generates context-aware replies using memory, user profiles, and AI.
    """
    
    def __init__(self, agi_kernel, plugin_manager):
        """
        Initialize reply system.
        
        Args:
            agi_kernel: AGI Kernel instance
            plugin_manager: Plugin manager for accessing platform plugins
        """
        self.agi = agi_kernel
        self.plugin_manager = plugin_manager
        self.core = agi_kernel.core if hasattr(agi_kernel, 'core') else None
        
        # User profiles for personalization
        self.user_profiles: Dict[str, Dict] = {}
        self._load_user_profiles()
        
        print("💬 Reply System initialized")
    
    def _load_user_profiles(self):
        """Load user interaction profiles from unified memory"""
        try:
            if not self.agi or not hasattr(self.agi, 'unified_memory'):
                return
            
            profiles = self.agi.unified_memory.get('brain_user_profiles')
            if profiles and isinstance(profiles, dict):
                self.user_profiles = profiles
        except Exception as e:
            import logging
            logging.debug(f"Could not load user profiles: {e}")
    
    def _save_user_profiles(self):
        """Save user profiles to unified memory"""
        try:
            if self.agi and hasattr(self.agi, 'unified_memory'):
                self.agi.unified_memory.set('brain_user_profiles', self.user_profiles)
        except Exception as e:
            import logging
            logging.debug(f"Could not save user profiles: {e}")
    
    def _get_user_profile(self, username: str) -> Dict:
        """Get or create a profile for a user we've interacted with"""
        if username not in self.user_profiles:
            self.user_profiles[username] = {
                'username': username,
                'interactions': 0,
                'topics': [],
                'sentiment': 'neutral',
                'last_seen': None,
            }
        return self.user_profiles[username]
    
    def _update_user_profile(self, username: str, interaction_type: str, topic: str = ''):
        """Update user profile after an interaction"""
        profile = self._get_user_profile(username)
        profile['interactions'] += 1
        profile['last_seen'] = datetime.datetime.now().isoformat()
        if topic and topic not in profile['topics']:
            profile['topics'].append(topic)
            profile['topics'] = profile['topics'][-10:]  # Keep last 10 topics
        self._save_user_profiles()
    
    def generate_smart_reply(self, comment_content: str, commenter_name: str,
                             post_context: str = '', platform: str = 'moltx') -> Optional[str]:
        """
        Generate a context-aware, memory-enriched reply.
        
        Args:
            comment_content: The comment to reply to
            commenter_name: Username of commenter
            post_context: Context of the original post
            platform: Platform name (moltx, moltbook, etc.)
        
        Returns:
            Generated reply text or None if generation failed
        """
        
        # Build enriched context
        user_profile = self._get_user_profile(commenter_name)
        
        # Get context summary from context system if available
        context_summary = ""
        if self.agi and hasattr(self.agi, 'context_system'):
            context_summary = self.agi.context_system.build_context_summary()
        
        # Build user history context
        user_context = ""
        if user_profile['interactions'] > 0:
            user_context = f"\nYou've interacted with @{commenter_name} {user_profile['interactions']} times before."
            if user_profile['topics']:
                user_context += f" They're interested in: {', '.join(user_profile['topics'][-3:])}."
        
        # Search memory for relevant past interactions
        memory_context = ""
        try:
            if self.agi and hasattr(self.agi, 'unified_memory'):
                mem = self.agi.unified_memory
                if hasattr(mem, 'semantic_search'):
                    results = mem.semantic_search(
                        f"{commenter_name} {comment_content[:50]}",
                        top_k=3
                    )
                    if results:
                        memory_context = "\nRelevant memories:\n" + "\n".join(
                            f"- {r.get('content', '')[:100]}" for r in results
                        )
        except Exception as e:
            import logging
            logging.debug(f"Could not fetch memory context: {e}")
        
        # On-chain context for crypto-related comments
        onchain_context = ""
        crypto_keywords = ['token', 'wallet', 'eth', 'alley', 'base', 'chain', 'defi', 'nft', 'crypto', 'balance']
        if any(kw in comment_content.lower() for kw in crypto_keywords):
            try:
                if self.plugin_manager and hasattr(self.plugin_manager, 'plugins'):
                    onchain = self.plugin_manager.plugins.get('onchain')
                    if onchain and hasattr(onchain, 'web3_provider'):
                        provider = onchain.web3_provider
                        if provider and getattr(provider, 'connected', False):
                            eth = provider.get_eth_balance()
                            if eth.get('success'):
                                onchain_context = f"\nOn-chain: AlleyBot has {eth['balance_eth']:.4f} ETH on Base."
                            if hasattr(onchain, 'tracked_tokens'):
                                for sym, info in onchain.tracked_tokens.items():
                                    tok = provider.get_token_balance(info['address'])
                                    if tok.get('success') and tok['balance'] > 0:
                                        onchain_context += f" {tok['balance']:,.0f} {sym}."
            except Exception as e:
                import logging
                logging.debug(f"Could not fetch onchain context: {e}")
        
        # MEMORY-FIRST APPROACH: Use AlleyBot's own intelligence before Grok
        # Try memory-based reply first (sentence transformers + local context)
        reply = self._generate_memory_based_reply(
            comment_content, commenter_name, post_context,
            platform, user_context, memory_context, onchain_context
        )
        
        # Only use Grok if memory-based approach fails or for complex reasoning
        if not reply:
            reply = self._generate_with_grok(
                comment_content, commenter_name, post_context,
                platform, user_context, memory_context, onchain_context
            )
        
        # DeepSeek as final fallback
        if not reply:
            reply = self._generate_with_deepseek(
                comment_content, commenter_name, post_context,
                platform, user_context, memory_context, onchain_context
            )
        
        if reply:
            # SYMOD VALIDATION: Check for cognitive dissonance, scams, manipulation
            if C2V_AVAILABLE:
                reply = self._validate_with_symod(reply, comment_content)
            
            # Update user profile
            topic = self._extract_topic(comment_content)
            self._update_user_profile(commenter_name, 'reply', topic)
            
            # Store interaction in episodic memory
            try:
                if self.agi and hasattr(self.agi, 'episodic_memory'):
                    self.agi.episodic_memory.record_episode(
                        action_type='social_reply',
                        context={'user': commenter_name, 'platform': platform},
                        outcome={'success': True, 'reply': reply[:100]}
                    )
            except Exception as e:
                import logging
                logging.debug(f"Could not log episodic memory: {e}")
        
        return reply
    
    def _generate_memory_based_reply(self, comment: str, author: str, post_ctx: str,
                                      platform: str, user_ctx: str, mem_ctx: str,
                                      chain_ctx: str) -> Optional[str]:
        """
        Generate reply using AlleyBot's own memory and sentence transformers.
        
        This is the PRIMARY reply method - uses local intelligence first.
        Only falls back to Grok for complex reasoning if this fails.
        """
        try:
            # Get sentence transformer model
            from plugins.telegram.intent_classifier import get_sentence_model
            model = get_sentence_model()
            if not model:
                return None
            
            # Search memory for similar interactions
            if not self.agi or not hasattr(self.agi, 'unified_memory'):
                return None
            
            mem = self.agi.unified_memory
            if not hasattr(mem, 'semantic_search'):
                return None
            
            # Find similar past interactions using sentence transformers
            query = f"{author} {comment} {post_ctx[:100]}"
            similar_memories = mem.semantic_search(query, top_k=5)
            
            if not similar_memories or len(similar_memories) < 2:
                return None  # Not enough context, fall back to Grok
            
            # Build reply from memory patterns
            reply_patterns = []
            for memory in similar_memories:
                content = memory.get('content', '')
                # Extract reply patterns from past successful interactions
                if 'reply' in content.lower() or 'response' in content.lower():
                    reply_patterns.append(content[:200])
            
            if not reply_patterns:
                return None
            
            # Synthesize reply from memory patterns
            # Use most relevant memory as base, adapt to current context
            base_reply = reply_patterns[0]
            
            # Simple template-based adaptation
            # Extract key phrases and adapt to current comment
            reply_template = self._extract_reply_template(base_reply, comment)
            
            if reply_template and len(reply_template) > 20:
                # Add context awareness
                if user_ctx:
                    reply_template = f"{reply_template} {self._personalize_reply(reply_template, author)}"
                
                # Keep it concise
                if len(reply_template) > 280:
                    reply_template = reply_template[:277] + "..."
                
                print(f"💭 Generated memory-based reply (using {len(similar_memories)} similar interactions)")
                return reply_template
            
            return None
            
        except Exception as e:
            import logging
            logging.debug(f"Memory-based reply generation failed: {e}")
            return None
    
    def _extract_reply_template(self, memory_content: str, current_comment: str) -> Optional[str]:
        """Extract and adapt reply template from memory"""
        # Simple extraction - look for conversational patterns
        # This is a basic implementation - can be enhanced with better NLP
        
        # Remove metadata/timestamps
        content = memory_content.split('\n')[0] if '\n' in memory_content else memory_content
        
        # If it looks like a reply (starts with @, has conversational markers)
        if any(marker in content.lower() for marker in ['@', 'thanks', 'interesting', 'agree', 'think']):
            return content
        
        return None
    
    def _personalize_reply(self, reply: str, username: str) -> str:
        """Add personalization based on user history"""
        profile = self._get_user_profile(username)
        
        if profile['interactions'] > 5:
            return f"(We've chatted {profile['interactions']} times!)"
        elif profile['interactions'] > 0:
            return ""
        
        return ""
    
    def _validate_with_symod(self, reply: str, comment: str) -> str:
        """
        Validate reply through SyMod C2V Bridge for truth checking.
        
        Regenerates reply if it shows cognitive dissonance or field collapse.
        """
        try:
            c2v = get_c2v_bridge()
            
            # Get current block height for validation context
            block_height = 0
            try:
                if self.plugin_manager and hasattr(self.plugin_manager, 'plugins'):
                    onchain = self.plugin_manager.plugins.get('onchain')
                    if onchain and hasattr(onchain, 'get_latest_block'):
                        block_height = onchain.get_latest_block()
            except Exception as e:
                import logging
                logging.debug(f"Could not get block height: {e}")
            
            validation = c2v.validate_debate_argument(
                argument_text=reply,
                opponent_argument=comment,
                block_height=block_height
            )
            
            # If validation shows cognitive dissonance or field collapse, regenerate
            if not validation['valid'] or validation['synergy_field_status'] == "Collapse":
                print(f"⚠️ Reply failed SyMod validation: {validation['reasoning_trace']}")
                print("🔄 Regenerating with corrected context...")
                
                # Add correction context and regenerate
                correction_prompt = f"\n\nSYMOD CORRECTION: The previous reply showed {validation['synergy_field_status']}. "
                correction_prompt += f"Issue: {validation['reasoning_trace'][:100]}... "
                correction_prompt += "Generate a reply that is mathematically consistent and authentic."
                
                # Try regeneration once (simplified - just add correction to comment)
                corrected_reply = self._generate_with_grok(
                    comment + correction_prompt, 
                    "user", "",
                    "moltx", "", "", ""
                )
                
                if corrected_reply:
                    # Re-validate
                    validation2 = c2v.validate_debate_argument(corrected_reply, comment, block_height)
                    if validation2['valid']:
                        print(f"✅ Regenerated reply passed SyMod validation (confidence: {validation2['confidence']:.2%})")
                        return corrected_reply
                    else:
                        print(f"⚠️ Regenerated reply still failed validation, using original")
            else:
                print(f"✅ Reply passed SyMod validation (field: {validation['synergy_field_status']}, confidence: {validation['confidence']:.2%})")
                
        except Exception as e:
            print(f"⚠️ SyMod validation error: {e}")
        
        return reply
    
    def _generate_with_grok(self, comment: str, author: str, post_ctx: str,
                            platform: str, user_ctx: str, mem_ctx: str,
                            chain_ctx: str) -> Optional[str]:
        """Generate reply using Grok with full context"""
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return None
            
            prompt = f"""Reply to this comment on {platform}:

Comment from @{author}: "{comment}"
Post context: {post_ctx[:200] if post_ctx else 'General discussion'}
{user_ctx}
{mem_ctx}
{chain_ctx}

Requirements:
- Be conversational, authentic, and helpful
- Reference their specific points
- If you have history with this user, acknowledge the relationship
- If crypto/on-chain context is relevant, weave it in naturally
- Keep under 280 characters
- Include 1-2 relevant emojis
- Sound like AlleyBot: intelligent, friendly, knowledgeable AI agent
- Do NOT be generic or use filler phrases like "Interesting perspective"

Reply:"""
            
            data = {
                "model": grok_ai.model,
                "messages": [
                    {"role": "system", "content": "You are AlleyBot, an intelligent AI agent. Generate authentic, context-aware replies. Never be generic."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.7,
            }
            
            response = grok_ai._make_api_request(data)
            text = grok_ai._extract_text(response)
            if text:
                return grok_ai._clean_output(text)
            return None
            
        except Exception as e:
            print(f"⚠️ Grok smart reply failed: {e}")
            return None
    
    def _generate_with_deepseek(self, comment: str, author: str, post_ctx: str,
                                platform: str, user_ctx: str, mem_ctx: str,
                                chain_ctx: str) -> Optional[str]:
        """Generate reply using DeepSeek with full context"""
        try:
            from deepseek_ai import deepseek_ai
            if not deepseek_ai.enabled:
                return None
            
            reply = deepseek_ai.generate_reply_to_comment(
                original_comment=comment,
                commenter_name=author,
                post_context=f"{post_ctx}{user_ctx}{chain_ctx}"
            )
            return reply
            
        except Exception as e:
            print(f"⚠️ DeepSeek smart reply failed: {e}")
            return None
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text"""
        keywords = ['ai', 'agent', 'crypto', 'defi', 'token', 'blockchain',
                     'development', 'community', 'trading', 'nft', 'dao',
                     'moltx', 'moltbook', 'alleybot', 'base', 'ethereum']
        found = [kw for kw in keywords if kw in text.lower()]
        return found[0] if found else 'general'


def create_reply_system(agi_kernel, plugin_manager):
    """Factory function to create reply system"""
    return ReplySystem(agi_kernel, plugin_manager)
