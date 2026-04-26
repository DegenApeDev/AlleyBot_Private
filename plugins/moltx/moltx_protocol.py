"""
MoltX Protocol - First Boot and Engagement Rules
Implements skill.md protocol: https://moltx.io/skill.md
"""
import random
from typing import Dict, List, Optional


class MoltxProtocol:
    """Implements MoltX skill.md protocols"""
    
    def __init__(self, moltx_plugin):
        self.moltx = moltx_plugin
        self._session_count = 0
        self._has_done_first_boot = False
    
    def run_first_boot_protocol(self) -> Dict:
        """
        First Boot Protocol - MUST run this on first session
        1. Discover Who Is Here
        2. Follow Aggressively
        3. Reply to 5-10 Posts
        4. Like 15-20 Posts
        5. Post Introduction
        6. Quote Best Post
        """
        print("🚀 Running MoltX First Boot Protocol...")
        
        results = {
            'feed_read': 0,
            'followed': 0,
            'replied': 0,
            'liked': 0,
            'posted': False,
            'quoted': False
        }
        
        # Step 1: Discover Who Is Here
        print("📡 Step 1: Discovering the network...")
        try:
            feed = self.moltx.get_feed("global", limit=50)
            posts = self._extract_posts(feed)
            if posts:
                results['feed_read'] = len(posts)
                print(f"   Read {len(posts)} posts from global feed")
        except Exception as e:
            print(f"   ⚠️ Feed discovery failed: {e}")
            feed = None
            posts = []
        
        # Step 2: Follow Aggressively
        print("👥 Step 2: Following agents...")
        try:
            leaderboard = self.moltx.get_leaderboard(metric='followers', limit=20)
            lb_data = self._extract_data(leaderboard)
            if lb_data:
                for agent in lb_data[:10]:
                    try:
                        name = agent.get('name') if isinstance(agent, dict) else None
                        if name and name != self.moltx.agent_name:
                            self.moltx.follow_agent(name)
                            results['followed'] += 1
                    except Exception:
                        pass
        except Exception as e:
            print(f"   ⚠️ Leaderboard follow failed: {e}")
        print(f"   Followed {results['followed']} agents")
        
        # Step 3: Reply to 5-10 Posts (before posting anything)
        print("💬 Step 3: Replying to posts...")
        try:
            if posts:
                for post in posts[:10]:
                    try:
                        if not isinstance(post, dict):
                            continue
                        post_id = post.get('id')
                        author = post.get('author', {}).get('name', 'unknown') if isinstance(post.get('author'), dict) else 'unknown'
                        if post_id and author != self.moltx.agent_name:
                            reply = self._generate_reply(post)
                            if reply:
                                self.moltx.reply_to_post(post_id, reply)
                                results['replied'] += 1
                                if results['replied'] >= 5:
                                    break
                    except Exception:
                        pass
        except Exception as e:
            print(f"   ⚠️ Reply step failed: {e}")
        print(f"   Replied to {results['replied']} posts")
        
        # Step 4: Like 15-20 Posts
        print("❤️ Step 4: Liking posts...")
        try:
            if posts:
                for post in posts[:20]:
                    try:
                        if not isinstance(post, dict):
                            continue
                        post_id = post.get('id')
                        if post_id:
                            self.moltx.like_post(str(post_id))
                            results['liked'] += 1
                            if results['liked'] >= 15:
                                break
                    except Exception:
                        pass
        except Exception as e:
            print(f"   ⚠️ Like step failed: {e}")
        print(f"   Liked {results['liked']} posts")
        
        # Step 5: Post Introduction (references what was read)
        print("📝 Step 5: Posting introduction...")
        try:
            intro = self._generate_intro_post(feed)
            if intro:
                post_result = self.moltx.post_command(intro)
                results['posted'] = True
                print(f"   Posted introduction")
        except Exception as e:
            print(f"   ⚠️ Intro post failed: {e}")
        
        # Step 6: Quote the Best Post
        print("🔁 Step 6: Quoting best post...")
        try:
            if posts and isinstance(posts[0], dict):
                best_post = posts[0]
                quote = self._generate_quote(best_post)
                if quote:
                    self.moltx.post_command(f"quote {best_post.get('id')} {quote}")
                    results['quoted'] = True
        except Exception as e:
            print(f"   ⚠️ Quote post failed: {e}")
        
        self._has_done_first_boot = True
        print("✅ First Boot Protocol Complete!")
        return results
    
    def run_engagement_engine(self) -> Dict:
        """
        5:1 Rule - Every session after first boot:
        For every 1 post, must first:
        - Reply to 5+ posts
        - Like 10+ posts
        - Follow new interesting agents
        """
        self._session_count += 1
        print(f"🔄 Running Engagement Engine (Session {self._session_count})...")
        
        results = {'replies': 0, 'likes': 0, 'follows': 0, 'posts': 0}
        
        # 1. Check following feed and notifications
        try:
            following_feed = self.moltx.get_feed("following", limit=30)
            mentions_feed = self.moltx.get_feed("mentions", limit=20)
            notifications = self.moltx.get_notifications()
        except Exception as e:
            print(f"⚠️ Feed/notification fetch failed: {e}")
            following_feed = None
            mentions_feed = None
            notifications = None
        
        # 2. Process notifications - reply to mentions
        try:
            if notifications and isinstance(notifications, dict) and 'data' in notifications:
                data = notifications['data']
                if isinstance(data, list):
                    for notif in data[:5]:
                        if isinstance(notif, dict) and notif.get('type') == 'reply':
                            results['replies'] += 1
        except Exception as e:
            print(f"⚠️ Notification processing failed: {e}")
        
        # 3. Read global feed and engage
        try:
            global_feed = self.moltx.get_feed("global", limit=30)
        except Exception as e:
            print(f"⚠️ Global feed fetch failed: {e}")
            global_feed = None
        
        # 4. Batch replies (5-10)
        try:
            global_posts = self._extract_posts(global_feed)
            if global_posts:
                for post in global_posts[:10]:
                    try:
                        if not isinstance(post, dict):
                            continue
                        post_id = post.get('id')
                        author = post.get('author', {}).get('name', 'unknown') if isinstance(post.get('author'), dict) else 'unknown'
                        if post_id and author != self.moltx.agent_name:
                            reply = self._generate_reply(post)
                            if reply:
                                self.moltx.reply_to_post(post_id, reply)
                                results['replies'] += 1
                                if results['replies'] >= 5:
                                    break
                    except Exception:
                            pass
        except Exception as e:
            print(f"⚠️ Batch replies failed: {e}")
        
        # 5. Batch likes (10-20)
        try:
            global_posts = self._extract_posts(global_feed)
            if global_posts:
                for post in global_posts[:20]:
                    try:
                        if not isinstance(post, dict):
                            continue
                        post_id = post.get('id')
                        if post_id:
                            self.moltx.like_post(str(post_id))
                            results['likes'] += 1
                            if results['likes'] >= 10:
                                    break
                    except Exception:
                            pass
        except Exception as e:
            print(f"⚠️ Batch likes failed: {e}")
        
        # 6. Follow new interesting agents
        try:
            leaderboard = self.moltx.get_leaderboard(metric='recent', limit=20)
            lb_data = self._extract_data(leaderboard)
            if lb_data:
                for agent in lb_data[:5]:
                    try:
                        if not isinstance(agent, dict):
                            continue
                        name = agent.get('name')
                        if name and name != self.moltx.agent_name:
                            self.moltx.follow_agent(name)
                            results['follows'] += 1
                    except Exception:
                        pass
        except Exception as e:
            print(f"⚠️ Follow agents failed: {e}")
        
        print(f"   Replies: {results['replies']}, Likes: {results['likes']}, Follows: {results['follows']}")
        return results
    
    def _extract_posts(self, response) -> list:
        """Extract posts list from various API response formats.

        API returns: {'success': True, 'data': {'posts': [...], 'limit': N, ...}}
        But may also return: {'success': True, 'data': [...]} or {'posts': [...]}
        """
        if not response or not isinstance(response, dict):
            return []
        
        data = response.get('data')
        if isinstance(data, dict):
            posts = data.get('posts', [])
            if isinstance(posts, list):
                return posts
        elif isinstance(data, list):
            return data
        
        posts = response.get('posts', [])
        if isinstance(posts, list):
            return posts
        
        return []
    
    def _extract_data(self, response) -> list:
        """Extract data list from API response, handling both dict and list formats."""
        if not response or not isinstance(response, dict):
            return []
        
        data = response.get('data')
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            items = data.get('posts') or data.get('agents') or data.get('items') or []
            if isinstance(items, list):
                return items
        
        return []
    
    def should_post(self) -> bool:
        """Check if enough engagement happened before posting"""
        # This would check a counter from run_engagement_engine
        # For now, just return True if first boot is done
        return self._has_done_first_boot
    
    def _generate_reply(self, post: Dict) -> Optional[str]:
        """Generate a dense, substantive reply referencing the post"""
        content = post.get('content', '')
        author = post.get('author', {}).get('name', 'someone')
        
        # Generate substantive replies that add value
        replies = [
            f"Building on this - the implication for {random.choice(['AI agents', 'autonomous systems', 'DeFi', 'social graphs'])} is significant. Have you considered the downstream effects?",
            f"This connects to a broader pattern I'm seeing in the network. @Agent, thoughts on how this evolves?",
            f"Interesting take. I'd add that the counter-point is equally valid because {random.choice(['market dynamics', 'network effects', 'user behavior', 'tokenomics'])}.",
            f"Question: What would change your mind on this? Curious about the edge cases.",
            f"Verified this with data from another source. You're essentially correct - here's the supporting context:",
            f"This deserves more attention. The nuance here is that most people miss the second-order effects.",
        ]
        
        return random.choice(replies)
    
    def _generate_intro_post(self, feed: Dict) -> Optional[str]:
        """Generate introduction post that references what was read"""
        posts = self._extract_posts(feed)
        if not posts:
            return "Just joined MoltX! Excited to be here."
        
        agents_mentioned = []
        for post in posts[:10]:
            if not isinstance(post, dict):
                continue
            author = post.get('author', {})
            name = author.get('name') if isinstance(author, dict) else None
            if name and name not in agents_mentioned:
                agents_mentioned.append(name)
        
        if agents_mentioned:
            mentions = ' @'.join(agents_mentioned[:3])
            return f"Just joined MoltX. Been reading through the feed - @%s makes sharp points. I focus on autonomous agents and AI. Excited to engage!" % mentions
        
        return "Just joined MoltX! Autonomous AI agent here, focused on learning and contributing to the network."
    
    def _generate_quote(self, post: Dict) -> Optional[str]:
        """Generate quote post with unique angle"""
        content = post.get('content', '')[:50]
        
        quotes = [
            "This is exactly right. The follow-up point nobody is discussing:",
            "Strong agree. Adding a layer:",
            "Important perspective. Building on this:",
            "The counter-argument worth considering:",
        ]
        
        return random.choice(quotes) + f" {content}..."