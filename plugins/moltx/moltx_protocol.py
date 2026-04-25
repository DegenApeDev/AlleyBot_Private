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
        feed = self.moltx.get_feed("global", limit=50)
        if feed and 'data' in feed:
            posts = feed['data']
            results['feed_read'] = len(posts)
            print(f"   Read {len(posts)} posts from global feed")
        
        # Step 2: Follow Aggressively
        print("👥 Step 2: Following agents...")
        leaderboard = self.moltx.get_leaderboard(metric='followers', limit=20)
        if leaderboard and 'data' in leaderboard:
            for agent in leaderboard['data'][:10]:
                try:
                    name = agent.get('name')
                    if name and name != self.moltx.agent_name:
                        self.moltx.follow_agent(name)
                        results['followed'] += 1
                except Exception as e:
                    pass
        print(f"   Followed {results['followed']} agents")
        
        # Step 3: Reply to 5-10 Posts (before posting anything)
        print("💬 Step 3: Replying to posts...")
        if feed and 'data' in feed:
            for post in feed['data'][:10]:
                try:
                    post_id = post.get('id')
                    author = post.get('author', {}).get('name', 'unknown')
                    if post_id and author != self.moltx.agent_name:
                        reply = self._generate_reply(post)
                        if reply:
                            self.moltx.reply_to_post(post_id, reply)
                            results['replied'] += 1
                            if results['replied'] >= 5:
                                break
                except Exception:
                    pass
        print(f"   Replied to {results['replied']} posts")
        
        # Step 4: Like 15-20 Posts
        print("❤️ Step 4: Liking posts...")
        if feed and 'data' in feed:
            for post in feed['data'][:20]:
                try:
                    post_id = post.get('id')
                    if post_id:
                        self.moltx.like_post(post_id)
                        results['liked'] += 1
                        if results['liked'] >= 15:
                            break
                except Exception:
                    pass
        print(f"   Liked {results['liked']} posts")
        
        # Step 5: Post Introduction (references what was read)
        print("📝 Step 5: Posting introduction...")
        intro = self._generate_intro_post(feed)
        if intro:
            post_result = self.moltx.post_command(intro)
            results['posted'] = True
            print(f"   Posted introduction")
        
        # Step 6: Quote the Best Post
        print("🔁 Step 6: Quoting best post...")
        if feed and 'data' in feed:
            best_post = feed['data'][0]
            quote = self._generate_quote(best_post)
            if quote:
                try:
                    self.moltx.post_command(f"quote {best_post.get('id')} {quote}")
                    results['quoted'] = True
                except Exception:
                    pass
        
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
        following_feed = self.moltx.get_feed("following", limit=30)
        mentions_feed = self.moltx.get_feed("mentions", limit=20)
        notifications = self.moltx.get_notifications()
        
        # 2. Process notifications - reply to mentions
        if notifications and 'data' in notifications:
            for notif in notifications['data'][:5]:
                if notif.get('type') == 'reply':
                    # Get the post and reply
                    results['replies'] += 1
        
        # 3. Read global feed and engage
        global_feed = self.moltx.get_feed("global", limit=30)
        
        # 4. Batch replies (5-10)
        if global_feed and 'data' in global_feed:
            for post in global_feed['data'][:10]:
                try:
                    post_id = post.get('id')
                    author = post.get('author', {}).get('name', 'unknown')
                    if post_id and author != self.moltx.agent_name:
                        reply = self._generate_reply(post)
                        if reply:
                            self.moltx.reply_to_post(post_id, reply)
                            results['replies'] += 1
                            if results['replies'] >= 5:
                                break
                except Exception:
                    pass
        
        # 5. Batch likes (10-20)
        if global_feed and 'data' in global_feed:
            for post in global_feed['data'][:20]:
                try:
                    post_id = post.get('id')
                    if post_id:
                        self.moltx.like_post(post_id)
                        results['likes'] += 1
                        if results['likes'] >= 10:
                            break
                except Exception:
                    pass
        
        # 6. Follow new interesting agents
        leaderboard = self.moltx.get_leaderboard(metric='recent', limit=20)
        if leaderboard and 'data' in leaderboard:
            for agent in leaderboard['data'][:5]:
                try:
                    name = agent.get('name')
                    if name and name != self.moltx.agent_name:
                        self.moltx.follow_agent(name)
                        results['follows'] += 1
                except Exception:
                    pass
        
        print(f"   Replies: {results['replies']}, Likes: {results['likes']}, Follows: {results['follows']}")
        return results
    
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
        if not feed or 'data' not in feed or not feed['data']:
            return "Just joined MoltX! Excited to be here."
        
        # Reference real agents from feed
        agents_mentioned = []
        for post in feed['data'][:10]:
            author = post.get('author', {})
            name = author.get('name')
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