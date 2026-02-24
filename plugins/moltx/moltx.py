"""
MoltX Plugin - Integrates AlleyBot with Moltx.io
Twitter for AI Agents - Social media & microblogging platform

Split into mixins for maintainability:
- moltx_api.py: Core API client, credentials, registration, profile, media
- moltx_content.py: Post creation, AI generation, trending topics, repost
- moltx_engagement.py: Feed, follow/like, notifications, heartbeat, communities
- moltx_messaging.py: DMs, DM replies, AI DM generation, DM logging
"""
from datetime import datetime
from plugin_manager import AlleyBotPlugin
from config import MOLTX_API_KEY
from plugins.moltx.moltx_api import MoltxAPIMixin
from plugins.moltx.moltx_wallet import MoltxWalletMixin
from plugins.moltx.moltx_content import MoltxContentMixin
from plugins.moltx.moltx_engagement import MoltxEngagementMixin
from plugins.moltx.moltx_messaging import MoltxMessagingMixin
from plugins.moltx.moltx_discovery import MoltxDiscoveryMixin
from plugins.moltx.moltx_symod_interface import (
    symod_start_command,
    symod_stop_command,
    symod_status_command,
    symod_cycle_command,
    symod_config_command
)


class MoltxPlugin(MoltxAPIMixin, MoltxWalletMixin, MoltxContentMixin, MoltxEngagementMixin, 
                  MoltxMessagingMixin, MoltxDiscoveryMixin, AlleyBotPlugin):
    """Plugin for Moltx.io - Twitter for AI Agents with SyMod-driven AGI capabilities"""

    def __init__(self, config):
        super().__init__(config)
        print(f"🔍 MoltxPlugin.__init__ called")
        print(f"🔍 MOLTX_API_KEY from config module: {MOLTX_API_KEY[:20] if MOLTX_API_KEY else 'NOT SET'}")
        self._init_api(MOLTX_API_KEY)
        
        # SyMod interface is lazy-loaded on first command use

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
            print(f"🔌 Attempting EVM wallet auto-link for @{self.agent_name}...")
            link_result = self.auto_link_wallet()
            if not link_result:
                print(f"⚠️  Wallet auto-link failed - you can retry with /moltx_link_wallet")

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

    def link_wallet_command(self):
        """Manually trigger EVM wallet linking via EIP-712"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        if not hasattr(self, 'private_key') or not self.private_key:
            return "❌ No private key configured. Set BASE_WALLET_PRIVATE_KEY in .env"
        
        if not hasattr(self, 'agent_name') or not self.agent_name:
            return "❌ No agent name available"
        
        print(f"🔌 Attempting wallet link for @{self.agent_name}...")
        result = self.auto_link_wallet()
        
        if result and self.evm_wallet_linked:
            return f"✅ Wallet linked successfully!\n🔗 Address: {self.evm_wallet_address}"
        else:
            return f"❌ Wallet linking failed. Check logs for details.\n📍 Configured address: {getattr(self, 'evm_wallet_address', 'N/A')}"

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

    def feed_command(self, *args):
        """Command to fetch and format feed output for Telegram/NL callers."""
        feed_type = 'global'
        limit = 10

        if args:
            if isinstance(args[0], str) and args[0] in {'global', 'following', 'mentions'}:
                feed_type = args[0]
                if len(args) > 1 and str(args[1]).isdigit():
                    limit = max(1, min(int(args[1]), 20))
            elif str(args[0]).isdigit():
                limit = max(1, min(int(args[0]), 20))

        result = self.get_feed(feed_type=feed_type, limit=limit)
        if isinstance(result, str):
            return result

        posts = []
        if isinstance(result, dict):
            data = result.get('data', {})
            posts = (
                result.get('posts')
                or data.get('posts', [])
                or result.get('items', [])
                or []
            )
        elif isinstance(result, list):
            posts = result

        if not posts:
            return f"🐦 {feed_type.title()} Feed: no posts found"

        output = f"🐦 {feed_type.title()} Feed ({len(posts)} posts):\n\n"
        for post in posts[:limit]:
            if not isinstance(post, dict):
                output += f"🐦 {str(post)[:100]}\n\n"
                continue

            agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
            content = post.get('content') or post.get('text') or post.get('body') or 'No content'
            likes = post.get('likes_count') or post.get('like_count') or post.get('likes') or 0
            replies = post.get('replies_count') or post.get('reply_count') or post.get('replies') or 0
            post_id = post.get('id') or post.get('post_id') or 'unknown'

            output += f"🐦 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
            output += f"   ❤️ {likes} likes | 💬 {replies} replies | 🆔 {post_id}\n\n"

        return output

    def engage_feed_command(self, count='3'):
        """Dynamic engagement: check trending, find interesting topics, like AND comment on quality posts."""
        import random
        
        try:
            target_count = int(count)
        except (TypeError, ValueError):
            target_count = 3
        target_count = max(2, min(target_count, 15))  # Allow more engagements

        print(f"🤖 Dynamic Engage: Starting intelligent engagement cycle...")
        
        all_posts = []
        sources = []
        
        # 1. Check diverse topics (not just trending blockchain)
        print(f"🔥 Dynamic Engage: Checking diverse topics...")
        try:
            # Get trending hashtags but mix with diverse categories
            trending = self.get_trending_hashtags(limit=5)
            hashtags = []
            if isinstance(trending, dict):
                hashtags = trending.get('hashtags', []) or trending.get('data', {}).get('hashtags', [])
            
            # Mix trending with diverse topics
            if hashtags:
                # Pick 1-2 trending hashtags to explore
                explore_tags = hashtags[:2] if len(hashtags) >= 2 else hashtags
                for tag in explore_tags:
                    tag_name = tag.get('name', tag) if isinstance(tag, dict) else tag
                    print(f"🔥 Dynamic Engage: Exploring trending #{tag_name}...")
                    posts = self.get_hashtag_posts(tag_name, limit=5)
                    if isinstance(posts, dict) and 'posts' in posts:
                        for p in posts['posts']:
                            p['_source'] = f'trending:#{tag_name}'
                        all_posts.extend(posts['posts'])
                        sources.append(f'trending:#{tag_name}')
            
            # Add diverse topic exploration
            if hasattr(self, 'content_categories'):
                categories = list(self.content_categories.keys())
                for category in random.sample(categories, min(3, len(categories))):
                    topics = self.content_categories[category]
                    topic = random.choice(topics)
                    print(f"🎯 Dynamic Engage: Exploring {category} topic: {topic}")
                    search_result = self.search_posts(topic, limit=3)
                    if isinstance(search_result, dict) and search_result.get('success'):
                        search_posts = search_result.get('posts', [])
                        for p in search_posts:
                            p['_source'] = f'category:{category}'
                        all_posts.extend(search_posts)
                        sources.append(f'category:{category}')
                        
        except Exception as e:
            print(f"⚠️ Dynamic Engage: Topic exploration failed: {e}")
        
        # 2. Get global feed
        print(f"📰 Dynamic Engage: Fetching global feed...")
        feed_result = self.get_feed(feed_type='global', limit=15)
        if isinstance(feed_result, dict):
            feed_posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
            for p in feed_posts:
                p['_source'] = 'feed:global'
            all_posts.extend(feed_posts)
            sources.append('feed:global')
        
        # 3. Search for interesting AI/crypto topics (diversified)
        interesting_topics = [
            'AI agents', 'crypto', 'DeFi', 'autonomous', 'AGI', 'web3',
            'machine learning', 'blockchain', 'DAOs', 'NFTs', 'metaverse',
            'quantum computing', 'biotech', 'robotics', 'privacy', 'ethics'
        ]
        topic = random.choice(interesting_topics)
        print(f"🔍 Dynamic Engage: Searching for '{topic}'...")
        try:
            search_result = self.search_posts(topic, limit=5)
            if isinstance(search_result, dict) and search_result.get('success'):
                search_posts = search_result.get('posts', [])
                for p in search_posts:
                    p['_source'] = f'search:{topic}'
                all_posts.extend(search_posts)
                sources.append(f'search:{topic}')
        except Exception as e:
            print(f"⚠️ Dynamic Engage: Search failed: {e}")
        
        # 4. Deduplicate posts by ID
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            pid = post.get('id') or post.get('post_id')
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_posts.append(post)
        
        print(f"🔍 Dynamic Engage: Found {len(unique_posts)} unique posts from {len(sources)} sources")
        
        if not unique_posts:
            return "❌ Dynamic Engage: No posts available to engage"
        
        # 5. Score posts by engagement potential (interesting content)
        scored_posts = []
        for post in unique_posts:
            score = 0
            content = post.get('content', '')
            likes = post.get('likes_count', 0)
            replies = post.get('replies_count', 0)
            source = post.get('_source', 'unknown')
            
            # Prefer posts with some engagement but not viral (2-20 likes)
            if 2 <= likes <= 20:
                score += 3
            elif likes > 20:
                score += 1  # Viral posts are harder to get noticed on
            
            # Prefer posts with replies (conversations)
            if replies >= 1:
                score += 2
            
            # Prefer diverse topic posts (not just trending)
            if 'category:' in source:
                score += 3  # Bonus for diverse categories
            elif 'trending' in source:
                score += 2
            elif 'search' in source:
                score += 1
            
            # Prefer posts with content (not empty)
            content_len = len(content) if content else 0
            if content_len > 20:
                score += 1
            
            # Prefer AI/crypto related content but also other topics
            diverse_keywords = ['ai', 'agent', 'crypto', 'defi', 'web3', 'autonomous', 'gpt', 'llm', 'blockchain',
                              'philosophy', 'ethics', 'art', 'music', 'culture', 'quantum', 'biotech', 'robotics']
            if content and any(kw in content.lower() for kw in diverse_keywords):
                score += 2
            
            # Penalize repetitive content
            if content and 'blockchain' in content.lower():
                score -= 1  # Reduce focus on overused topic
            
            scored_posts.append((score, post))
        
        # Sort by score descending
        scored_posts.sort(reverse=True, key=lambda x: x[0])
        
        # 6. Engage with top posts using enhanced content generation
        liked = 0
        commented = 0
        reposted = 0
        engaged_posts = []
        
        for score, post in scored_posts:
            if (liked + commented + reposted) >= target_count:
                break
            
            post_id = post.get('id') or post.get('post_id')
            author = (post.get('agent_name') or post.get('author_name') or '').lstrip('@')
            content = post.get('content', '')
            likes = post.get('likes_count', 0)
            source = post.get('_source', 'unknown')
            
            if not post_id:
                continue
            if author and getattr(self, 'agent_name', None) and author.lower() == self.agent_name.lower().lstrip('@'):
                continue
            
            print(f"🔍 Dynamic Engage: [{source}] Post by @{author} (score:{score}, likes:{likes})")
            
            # Always try to like
            like_result = self.like_post(str(post_id))
            if isinstance(like_result, str) and like_result.startswith('✅'):
                liked += 1
                print(f"  ✅ Liked")
                
                # Comment on high-score posts using enhanced generation
                should_comment = score >= 3 or likes >= 2 or 'category:' in source
                if should_comment and commented < target_count and hasattr(self, '_generate_enhanced_comment'):
                    print(f"  💬 Generating enhanced AI comment...")
                    try:
                        comment_text = self._generate_enhanced_comment(content, agent_name=author)
                        if comment_text:
                            reply_result = self.reply_to_post(post_id, comment_text)
                            if isinstance(reply_result, str) and reply_result.startswith('✅'):
                                commented += 1
                                print(f"  ✅ Enhanced comment: {comment_text[:60]}...")
                                engaged_posts.append({
                                    'id': post_id, 'author': author, 'action': 'like+enhanced_comment',
                                    'comment': comment_text[:60], 'source': source
                                })
                            else:
                                engaged_posts.append({
                                    'id': post_id, 'author': author, 'action': 'like',
                                    'source': source
                                })
                        else:
                            engaged_posts.append({
                                'id': post_id, 'author': author, 'action': 'like',
                                'source': source
                            })
                    except Exception as e:
                        print(f"  ⚠️ Enhanced comment failed: {e}")
                        engaged_posts.append({
                            'id': post_id, 'author': author, 'action': 'like',
                            'source': source
                        })
                else:
                    engaged_posts.append({
                        'id': post_id, 'author': author, 'action': 'like',
                        'source': source
                    })
                
                # Occasionally repost viral content (likes >= 15)
                if likes >= 15 and reposted < (target_count // 4):
                    print(f"  🔄 Reposting viral content...")
                    try:
                        repost_result = self.repost_post(post_id)
                        if isinstance(repost_result, str) and repost_result.startswith('✅'):
                            reposted += 1
                            print(f"  ✅ Reposted")
                    except Exception as e:
                        pass
            else:
                print(f"  ❌ Failed to like")
        
        total = liked + commented + reposted
        print(f"\n🤖 Dynamic Engage Complete: {liked} likes, {commented} enhanced comments, {reposted} reposts")
        print(f"   Sources: {', '.join(set(sources))}")
        
        if total == 0:
            return "❌ Dynamic Engage: No successful engagements"
        
        return f"✅ Dynamic Engage: {liked} likes, {commented} enhanced comments, {reposted} reposts from {len(sources)} diverse sources"

    def trending_command(self, *args):
        """Command to fetch and format trending hashtags."""
        limit = int(args[0]) if args and str(args[0]).isdigit() else 10
        limit = max(1, min(limit, 30))

        result = self.get_trending_hashtags(limit)
        if isinstance(result, str):
            return result

        hashtags = []
        if isinstance(result, dict):
            if result.get('success') and isinstance(result.get('hashtags'), list):
                hashtags = result.get('hashtags', [])
            elif isinstance(result.get('data'), dict):
                hashtags = result.get('data', {}).get('hashtags', [])
            elif isinstance(result.get('data'), list):
                hashtags = result.get('data', [])
            elif isinstance(result.get('hashtags'), list):
                hashtags = result.get('hashtags', [])
        elif isinstance(result, list):
            hashtags = result

        if not hashtags:
            return "❌ Failed to fetch trending hashtags"

        output = f"🔥 Top {min(len(hashtags), limit)} Trending Hashtags:\n\n"
        for i, tag in enumerate(hashtags[:limit], 1):
            if isinstance(tag, dict):
                name = tag.get('name') or tag.get('hashtag') or tag.get('tag') or 'unknown'
            else:
                name = str(tag)
            output += f"{i}. #{name.lstrip('#')}\n"
        return output

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

    # === SyMod Command Wrappers (delegate to interface) ===

    def symod_start_command(self):
        """Start SyMod-driven social agent loop"""
        return symod_start_command(self)

    def symod_stop_command(self):
        """Stop SyMod-driven social agent loop"""
        return symod_stop_command(self)

    def symod_status_command(self):
        """Get SyMod agent status"""
        return symod_status_command(self)

    def symod_cycle_command(self):
        """Run one manual SyMod cycle"""
        return symod_cycle_command(self)

    def symod_config_command(self, key=None, value=None):
        """View/configure SyMod settings"""
        return symod_config_command(self, key, value)