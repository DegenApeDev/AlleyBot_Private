"""
Smart Reply Mixin
Memory-enriched AI reply generation that uses context from all sources.
Replaces the generic prompts with context-aware, personalized responses.
"""
import os
from typing import Optional, Dict, Any


class SmartReplyMixin:
    """Mixin for memory-powered intelligent replies"""

    def _init_smart_reply(self):
        """Initialize smart reply state"""
        self.user_profiles: Dict[str, Dict] = {}
        self._load_user_profiles()

    def _load_user_profiles(self):
        """Load user interaction profiles from memory"""
        try:
            profiles = self.core.get_memory('brain_user_profiles')
            if profiles and isinstance(profiles, dict):
                self.user_profiles = profiles
        except Exception:
            pass

    def _save_user_profiles(self):
        """Save user profiles"""
        try:
            self.core.save_memory('brain_user_profiles', self.user_profiles)
        except Exception:
            pass

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
        import datetime
        profile = self._get_user_profile(username)
        profile['interactions'] += 1
        profile['last_seen'] = datetime.datetime.now().isoformat()
        if topic and topic not in profile['topics']:
            profile['topics'].append(topic)
            profile['topics'] = profile['topics'][-10:]  # Keep last 10 topics
        self._save_user_profiles()

    def generate_smart_reply(self, comment_content: str, commenter_name: str,
                             post_context: str = '', platform: str = 'moltx') -> Optional[str]:
        """Generate a context-aware, memory-enriched reply"""

        # Build enriched context
        user_profile = self._get_user_profile(commenter_name)
        context_summary = self.build_context_summary()

        # Build user history context
        user_context = ""
        if user_profile['interactions'] > 0:
            user_context = f"\nYou've interacted with @{commenter_name} {user_profile['interactions']} times before."
            if user_profile['topics']:
                user_context += f" They're interested in: {', '.join(user_profile['topics'][-3:])}."

        # Search memory for relevant past interactions
        memory_context = ""
        try:
            if hasattr(self.core, 'enhanced_memory') and self.core.enhanced_memory:
                mem = self.core.enhanced_memory
                if hasattr(mem, 'semantic_search'):
                    results = mem.semantic_search(
                        f"{commenter_name} {comment_content[:50]}",
                        top_k=3
                    )
                    if results:
                        memory_context = "\nRelevant memories:\n" + "\n".join(
                            f"- {r.get('content', '')[:100]}" for r in results
                        )
        except Exception:
            pass

        # On-chain context for crypto-related comments
        onchain_context = ""
        crypto_keywords = ['token', 'wallet', 'eth', 'alley', 'base', 'chain', 'defi', 'nft', 'crypto', 'balance']
        if any(kw in comment_content.lower() for kw in crypto_keywords):
            try:
                onchain = self.core.plugin_manager.plugins.get('onchain')
                if onchain and onchain.web3_provider and onchain.web3_provider.connected:
                    eth = onchain.web3_provider.get_eth_balance()
                    if eth.get('success'):
                        onchain_context = f"\nOn-chain: AlleyBot has {eth['balance_eth']:.4f} ETH on Base."
                    for sym, info in onchain.tracked_tokens.items():
                        tok = onchain.web3_provider.get_token_balance(info['address'])
                        if tok.get('success') and tok['balance'] > 0:
                            onchain_context += f" {tok['balance']:,.0f} {sym}."
            except Exception:
                pass

        # Try Grok first (better reasoning), then DeepSeek
        reply = self._generate_with_grok(
            comment_content, commenter_name, post_context,
            platform, user_context, memory_context, onchain_context
        )

        if not reply:
            reply = self._generate_with_deepseek(
                comment_content, commenter_name, post_context,
                platform, user_context, memory_context, onchain_context
            )

        if reply:
            # Update user profile
            topic = self._extract_topic(comment_content)
            self._update_user_profile(commenter_name, 'reply', topic)

            # Store interaction in memory
            try:
                if hasattr(self.core, 'add_semantic_memory'):
                    self.core.add_semantic_memory(
                        f"Replied to @{commenter_name} on {platform}: {reply[:100]}",
                        memory_type='social_interaction',
                        metadata={'user': commenter_name, 'platform': platform}
                    )
            except Exception:
                pass

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
            print(f"⚠️  Grok smart reply failed: {e}")
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
            print(f"⚠️  DeepSeek smart reply failed: {e}")
            return None

    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text"""
        keywords = ['ai', 'agent', 'crypto', 'defi', 'token', 'blockchain',
                     'development', 'community', 'trading', 'nft', 'dao',
                     'moltx', 'moltbook', 'alleybot', 'base', 'ethereum']
        found = [kw for kw in keywords if kw in text.lower()]
        return found[0] if found else 'general'

    def smart_reply_command(self, *args):
        """Generate a smart reply. Usage: brain_reply <username> <comment>"""
        if len(args) < 2:
            return "❌ Usage: brain_reply <username> <comment_text>"
        username = args[0]
        comment = ' '.join(args[1:])
        reply = self.generate_smart_reply(comment, username)
        if reply:
            return f"💬 Smart reply to @{username}:\n{reply}"
        return "❌ Failed to generate reply"
