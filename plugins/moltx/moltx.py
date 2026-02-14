"""
MoltX Plugin - Integrates AlleyBot with Moltx.io
Twitter for AI Agents - Social media & microblogging platform

Split into mixins for maintainability:
- moltx_api.py: Core API client, credentials, registration, profile, media
- moltx_content.py: Post creation, AI generation, trending topics, repost
- moltx_engagement.py: Feed, follow/like, notifications, heartbeat, communities
- moltx_messaging.py: DMs, DM replies, AI DM generation, DM logging
"""
from plugin_manager import AlleyBotPlugin
from config import MOLTX_API_KEY
from plugins.moltx.moltx_api import MoltxAPIMixin
from plugins.moltx.moltx_wallet import MoltxWalletMixin
from plugins.moltx.moltx_content import MoltxContentMixin
from plugins.moltx.moltx_engagement import MoltxEngagementMixin
from plugins.moltx.moltx_messaging import MoltxMessagingMixin
from plugins.moltx.moltx_discovery import MoltxDiscoveryMixin


class MoltxPlugin(MoltxAPIMixin, MoltxWalletMixin, MoltxContentMixin, MoltxEngagementMixin, MoltxMessagingMixin, MoltxDiscoveryMixin, AlleyBotPlugin):
    """Plugin for Moltx.io - Twitter for AI Agents"""

    def __init__(self, config):
        super().__init__(config)
        print(f"🔍 MoltxPlugin.__init__ called")
        print(f"🔍 MOLTX_API_KEY from config module: {MOLTX_API_KEY[:20] if MOLTX_API_KEY else 'NOT SET'}")
        self._init_api(MOLTX_API_KEY)

    def initialize(self, api, core):
        """Initialize Moltx plugin"""
        super().initialize(api, core)
        self._init_api_connection()

        # API key recovery via X tweet verification (first boot protocol step)
        if not self.initialized and hasattr(self.core, 'config'):
            tweet_url = self.core.config.get('MOLTX_VERIFICATION_TWEET_URL')
            if tweet_url:
                print(f"🔑 Attempting API key recovery via X tweet: {tweet_url}")
                recovery_result = self.claim_agent(tweet_url)
                print(f"Recovery result: {recovery_result}")
                # Re-init after potential key set
                self._init_api_connection()

        # First boot protocol
        if not self.agent_id:
            self.perform_first_boot()

        # EVM wallet linking (mandatory for write operations per v0.22.1)
        self._init_wallet()
        if self.initialized and not self.evm_wallet_linked:
            self.auto_link_wallet()

        # Heartbeat protocol
        if self.initialized and hasattr(self, 'send_heartbeat'):
            self.send_heartbeat()
            print("❤️ Heartbeat sent on init")

        # Ensure X handle is set on profile metadata
        if self.initialized:
            try:
                x_handle = self.core.config.get('moltx_x_handle', 'degenapedev')
                if hasattr(self, 'set_x_handle'):
                    self.set_x_handle(x_handle)
            except Exception as e:
                print(f"⚠️  Could not set X handle: {e}")

    def perform_first_boot(self):
        """First boot protocol: register, setup profile, wallet, heartbeat"""
        print("🚀 Starting Moltx first boot protocol...")
        
        # Step 1: Register agent if not exists
        if not self.agent_id:
            reg_result = self.register_agent(
                name="alleybot",
                display_name="AlleyBot Agent",
                description="🤖 AI Agent powered by AlleyBot on Moltx.io - Twitter for AI Agents",
                avatar_emoji="🤖"
            )
            success = False
            if isinstance(reg_result, dict) and reg_result.get('success'):
                success = True
            elif isinstance(reg_result, str) and ('✅' in reg_result or 'success' in reg_result.lower()):
                success = True
            if success:
                print("✅ Agent registered successfully")
            else:
                print(f"⚠️  Registration result: {reg_result}")
        
        # Step 2: Check claim status
        if hasattr(self, 'claim_status') and self.claim_status != 'claimed':
            print("⚠️  Agent not claimed. Run: !moltx claim <your_verification_tweet_url>")
            print("   Tweet should verify your X account owns this agent.")
        
        # Step 3: Update profile metadata
        profile_result = self.update_profile(
            display_name="AlleyBot Agent",
            description="🤖 Autonomous AI agent exploring Moltx.io | Tweets, engages, discovers",
            avatar_emoji="🤖"
        )
        print(f"📝 Profile updated: {profile_result}")
        
        # Step 4: Heartbeat
        if hasattr(self, 'send_heartbeat'):
            self.send_heartbeat()
        
        print("✅ First boot protocol complete")

    # --- Command wrappers (thin delegates) ---

    def claim_command(self, tweet_url):
        """Command to claim agent with X/Twitter verification (also recovers API access)"""
        return self.claim_agent(tweet_url)

    def recover_key_command(self, tweet_url):
        """API key recovery via X tweet verification"""
        result = self.claim_agent(tweet_url)
        if 'success' in str(result).lower():
            self._init_api_connection()
            return f"✅ API key recovered! Result: {result}"
        return f"❌ Recovery failed: {result}"

    def heartbeat_command(self):
        """Send manual heartbeat to Moltx"""
        if not self.initialized:
            return "❌ Moltx not initialized"
        if not hasattr(self, 'send_heartbeat'):
            return "❌ Heartbeat method unavailable"
        result = self.send_heartbeat()
        return f"❤️ Heartbeat sent: {result}"

    def status_command(self):
        """Command to get Moltx status"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        output = f"🐦 Moltx v0.22.1 Status for @{self.agent_name}\n\n"
        output += f"📝 Agent ID: {self.agent_id}\n"
        output += f"🔑 Claim Status: {getattr(self, 'claim_status', 'unknown')}\n"
        if hasattr(self, 'evm_wallet_linked') and self.evm_wallet_linked:
            output += f"🔗 EVM Wallet: {self.evm_wallet_address[:10]}...{self.evm_wallet_address[-6:]}\n"
        else:
            output += f"⚠️  EVM Wallet: Not linked (required for write ops)\n"
        output += f"📊 Posts Created: {len(self._get_activity('create_post'))}\n"
        output += f"💬 Comments Made: {len(self._get_activity('create_comment'))}\n"
        output += f"🤝 Agents Following: {len(self._get_activity('follow_agent'))}\n"
        output += f"❤️ Posts Liked: {len(self._get_activity('like_post'))}\n"
        return output

    def _get_activity(self, activity_type):
        """Get activity log from memory"""
        if not hasattr(self, 'core') or not self.core:
            return []
        try:
            activities = self.core.get_memory('moltx_activities') or []
            return [a for a in activities if a.get('type') == activity_type]
        except Exception:
            return []

    def _record_activity(self, activity_type, data):
        """Record activity to memory"""
        if not hasattr(self, 'core') or not self.core:
            return
        try:
            activities = self.core.get_memory('moltx_activities') or []
            activities.append({
                'type': activity_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            # Keep last 100 activities
            self.core.save_memory('moltx_activities', activities[-100:])
        except Exception as e:
            print(f"⚠️  Could not record activity: {e}")

    def profile_command(self, display_name=None, description=None, avatar_emoji=None):
        """Command to update agent profile metadata (display_name, description, avatar_emoji)"""
        if display_name is not None:
            if not isinstance(display_name, str) or len(display_name.strip()) == 0 or display_name == '{}':
                print(f"⚠️  Invalid display_name parameter: {display_name}")
                return "❌ Invalid display name. Profile not updated."

        if description is not None:
            if not isinstance(description, str) or len(description.strip()) == 0 or description == '{}':
                print(f"⚠️  Invalid description parameter: {description}")
                return "❌ Invalid description. Profile not updated."

        if avatar_emoji is not None:
            if not isinstance(avatar_emoji, str) or len(avatar_emoji.strip()) == 0 or avatar_emoji == '{}':
                print(f"⚠️  Invalid avatar_emoji parameter: {avatar_emoji}")
                return "❌ Invalid avatar emoji. Profile not updated."

        if display_name is None and description is None and avatar_emoji is None:
            return "❌ No valid profile updates provided"

        return self.update_profile(display_name, description, avatar_emoji)

    def register_command(self, name, display_name=None, description=None, avatar_emoji="🦞"):
        """Command to register agent"""
        return self.register_agent(name, display_name, description, avatar_emoji)

    def avatar_command(self, image_path):
        """Command to upload avatar image"""
        return self.upload_avatar(image_path)

    def banner_command(self, image_path):
        """Command to upload banner image"""
        return self.upload_banner(image_path)

    def post_command(self, *args):
        """Command to create post"""
        content = ' '.join(args) if args else ''
        return self.create_post(content)

    def create_article_command(self, *args):
        """Command to create article. Usage: moltx_article <title> | <content> [cover_url] [hashtags]"""
        if not args:
            return "❌ Usage: moltx_article <title> | <content> [cover_url] [hashtags]"
        
        text = ' '.join(args)
        parts = text.split('|', 1)
        if len(parts) < 2:
            return "❌ Article requires title | content"
        
        title = parts[0].strip()
        rest = parts[1].strip()
        
        # Parse optional cover_url and hashtags
        cover_url = None
        hashtags = None
        rest_parts = rest.split()
        
        # Check for URL in rest
        for i, part in enumerate(rest_parts):
            if part.startswith('http'):
                cover_url = part
                rest_parts.pop(i)
                rest = ' '.join(rest_parts)
                break
        
        # Parse hashtags
        hashtag_parts = [p[1:] for p in rest_parts if p.startswith('#')]
        if hashtag_parts:
            hashtags = hashtag_parts
            content = rest.replace(' #' + ' #'.join(hashtag_parts), '').strip()
        else:
            content = rest
        
        result = self.create_article(title, content, cover_url, hashtags)
        
        if result.get('success'):
            return f"✅ Article created: {result.get('title')}\n🔗 URL: {result.get('url')}"
        return f"❌ Failed to create article: {result.get('error')}"

    def search_posts_command(self, *args):
        """Command to search posts. Usage: moltx_search_posts <query> [limit]"""
        if not args:
            return "❌ Usage: moltx_search_posts <query> [limit]"
        
        query = args[0]
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
        
        result = self.search_posts(query, limit)
        if result.get('success'):
            posts = result.get('posts', [])
            output = f"🔍 Search results for '{query}' ({len(posts)} posts):\n\n"
            for post in posts[:5]:
                author = post.get('author_name', 'Unknown')
                content = post.get('content', '')[:80]
                output += f"🐦 @{author}: {content}...\n"
            return output
        return f"❌ Search failed: {result.get('error')}"

    def search_agents_command(self, *args):
        """Command to search agents. Usage: moltx_search_agents <query> [limit]"""
        if not args:
            return "❌ Usage: moltx_search_agents <query> [limit]"
        
        query = args[0]
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
        
        result = self.search_agents(query, limit)
        if result.get('success'):
            agents = result.get('agents', [])
            output = f"🔍 Agent search results for '{query}' ({len(agents)} agents):\n\n"
            for agent in agents[:5]:
                name = agent.get('name', 'Unknown')
                display = agent.get('display_name', name)
                output += f"👤 @{name} ({display})\n"
            return output
        return f"❌ Agent search failed: {result.get('error')}"

    def trending_hashtags_command(self, *args):
        """Command to get trending hashtags. Usage: moltx_trending_hashtags [limit]"""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        
        result = self.get_trending_hashtags(limit)
        if result and result.get('success'):
            hashtags = result.get('hashtags', [])[:10]
            output = f"🔥 Top {len(hashtags)} Trending Hashtags:\n\n"
            for i, tag in enumerate(hashtags, 1):
                output += f"{i}. #{tag}\n"
            return output
        return "❌ Failed to fetch trending hashtags"