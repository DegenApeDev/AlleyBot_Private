"""
Moltx Engagement Mixin
Feed browsing, follow/unfollow, likes, notifications, heartbeat loops, and feed engagement.
"""
import json
import time
import random
import requests


class MoltxEngagementMixin:
    """Mixin providing social engagement functionality"""

    def get_feed(self, feed_type='global', limit=20):
        """Get feed (global, following, mentions)"""
        valid_types = ['global', 'following', 'mentions']
        if feed_type not in valid_types:
            feed_type = 'global'

        if not self.initialized and feed_type not in ['global']:
            return "❌ Moltx not initialized for this feed type"

        if feed_type == 'global':
            url = f"{self.base_url}/feed/global"
            params = {'type': 'post,quote', 'limit': limit}
            headers = {}

            try:
                print(f"🔍 Fetching global feed from: {url}")
                response = requests.get(url, params=params, headers=headers, timeout=10)
                print(f"🔍 Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                print(f"🔍 Feed response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            except requests.exceptions.RequestException as e:
                return f"❌ Network error fetching {feed_type} feed: {e}"
            except Exception as e:
                return f"❌ Failed to fetch {feed_type} feed: {e}"
        elif feed_type == 'following':
            url = f"{self.base_url}/feed/following"
            params = {'limit': limit}
            result = self._make_request('GET', '/feed/following', params=params)
        elif feed_type == 'mentions':
            url = f"{self.base_url}/feed/mentions"
            params = {'limit': limit}
            result = self._make_request('GET', '/feed/mentions', params=params)
        else:
            return f"❌ Invalid feed type: {feed_type}"

        # Handle different response structures
        posts = []
        if result:
            if 'posts' in result:
                posts = result['posts']
            elif 'data' in result and 'posts' in result['data']:
                posts = result['data']['posts']
            elif isinstance(result, list):
                posts = result
            else:
                print(f"🔍 Unexpected feed response format: {result}")

        if posts:
            output = f"🐦 {feed_type.title()} Feed ({len(posts)} posts):\n\n"

            for post in posts[:limit]:
                if isinstance(post, dict):
                    agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
                    content = post.get('content') or post.get('text') or post.get('body') or 'No content'
                    replies = post.get('replies_count') or post.get('reply_count') or post.get('replies') or 0
                    likes = post.get('likes_count') or post.get('like_count') or post.get('likes') or 0
                    timestamp = post.get('created_at') or post.get('timestamp') or 'Unknown time'
                    post_id = post.get('id') or post.get('post_id') or 'unknown'

                    output += f"🐦 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   💬 {replies} replies | ❤️ {likes} likes\n"
                    output += f"   🕐 {timestamp}\n"
                    output += f"   🆔 ID: {post_id}\n\n"
                else:
                    output += f"🐦 {str(post)[:100]}{'...' if len(str(post)) > 100 else ''}\n\n"

            return output
        else:
            return f"❌ Failed to fetch {feed_type} feed - no posts found"

    def follow_agent(self, agent_name):
        """Follow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('POST', f'/follow/{agent_name}')

        if result:
            self._record_activity('follow', {'target': agent_name})
            return f"✅ Now following @{agent_name}"
        else:
            return f"❌ Failed to follow @{agent_name}"

    def unfollow_agent(self, agent_name):
        """Unfollow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('DELETE', f'/follow/{agent_name}')

        if result:
            self._record_activity('unfollow', {'target': agent_name})
            return f"✅ Unfollowed @{agent_name}"
        else:
            return f"❌ Failed to unfollow @{agent_name}"

    def like_post(self, post_id):
        """Like a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not post_id:
            return "❌ No post ID provided"

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                    print(f"📝 Extracted post_id from JSON input: {post_id}")
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('POST', f'/posts/{post_id}/like')

        if result:
            self._record_activity('like', {'post_id': post_id})
            return f"✅ Liked post {post_id}"
        else:
            return f"❌ Failed to like post {post_id}"

    def get_notifications(self):
        """Get notifications"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('GET', '/notifications')

        if result:
            print(f"🔍 Notifications response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")

        notifications = []
        if result:
            if 'notifications' in result:
                notifications = result['notifications']
            elif 'data' in result and 'notifications' in result['data']:
                notifications = result['data']['notifications']
            elif isinstance(result, list):
                notifications = result
            else:
                print(f"🔍 Unexpected notifications response format: {result}")

        if notifications:
            output = f"🔔 Notifications ({len(notifications)}):\n\n"

            for notif in notifications[:10]:
                if isinstance(notif, dict):
                    notif_type = notif.get('type') or notif.get('category') or notif.get('action') or 'Unknown'
                    content = notif.get('content') or notif.get('message') or notif.get('text') or 'No content'
                    timestamp = notif.get('created_at') or notif.get('timestamp') or 'Unknown time'
                    actor = notif.get('actor') or notif.get('from_user') or notif.get('user') or ''

                    output += f"🔔 {notif_type}"
                    if actor:
                        output += f" from @{actor}"
                    output += f": {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   🕐 {timestamp}\n\n"
                else:
                    output += f"🔔 {str(notif)[:100]}{'...' if len(str(notif)) > 100 else ''}\n\n"

            return output
        else:
            return "🔔 No notifications found"

    # --- Heartbeat ---

    def _heartbeat(self):
        """Moltx heartbeat v0.22.1 protocol — every 4+ hours.
        Follows the 5:1 rule: 5 replies + 10 likes before 1 original post."""
        if not self.initialized:
            print("❌ Moltx not initialized for heartbeat")
            return

        print("🐦 Moltx heartbeat v0.22.1 — 5:1 engagement engine...")

        # Step 1: Check status
        print("📋 Step 1: Checking agent status...")
        try:
            status_result = self._make_request('GET', '/agents/status')
            if status_result and status_result.get('success'):
                status_data = status_result.get('data', {})
                claim_status = status_data.get('claim_status', 'unknown')
                print(f"✅ Status: {claim_status}")
            else:
                print("⚠️  Status check failed")
        except Exception as e:
            print(f"⚠️  Status error: {e}")

        # Step 2: Pull all feeds
        print("📋 Step 2: Pulling feeds...")
        feed_posts = []
        try:
            for feed_type in ['following', 'mentions']:
                try:
                    self.get_feed(feed_type, 20)
                except Exception:
                    pass

            # Global feed — collect posts for engagement
            global_result = self._make_request('GET', '/feed/global', params={
                'type': 'post,quote', 'limit': 30
            })
            if global_result:
                if 'posts' in global_result:
                    feed_posts = global_result['posts']
                elif 'data' in global_result and 'posts' in global_result.get('data', {}):
                    feed_posts = global_result['data']['posts']
            print(f"✅ Pulled {len(feed_posts)} posts from global feed")
        except Exception as e:
            print(f"⚠️  Feed pull error: {e}")

        # Step 3: Process notifications (reply to mentions, follow back, like back)
        print("📋 Step 3: Processing notifications...")
        try:
            notif_result = self.process_notifications()
            print(f"✅ {notif_result}")
        except Exception as e:
            print(f"⚠️  Notification processing error: {e}")

        # Step 4: Batch replies (aim for 5-10 per v0.22.1 5:1 rule)
        print("📋 Step 4: Batch replies (5:1 rule)...")
        self._heartbeat_engage_posts()

        # Step 5: Batch likes (aim for 10-20 per v0.22.1)
        print("📋 Step 5: Batch likes...")
        try:
            like_ids = [p.get('id') for p in feed_posts if p.get('id') and p.get('author_name') != self.agent_name][:15]
            if like_ids:
                like_result = self.batch_likes(like_ids)
                print(f"✅ {like_result}")
            else:
                print("⚠️  No posts to like")
        except Exception as e:
            print(f"⚠️  Batch likes error: {e}")

        # Step 6: Follow new agents
        print("📋 Step 6: Following new agents...")
        self._heartbeat_follow_agents()

        # Step 7: Quote the best post found (highest-signal engagement)
        print("📋 Step 7: Quoting best post...")
        try:
            best_post = None
            best_score = 0
            for post in feed_posts:
                if post.get('author_name') == self.agent_name:
                    continue
                score = (post.get('like_count', post.get('likes_count', 0)) +
                         post.get('reply_count', post.get('replies_count', 0)) * 2)
                if score > best_score:
                    best_score = score
                    best_post = post

            if best_post and best_score >= 3:
                content = str(best_post.get('content', ''))[:200]
                author = best_post.get('author_name', 'Unknown')
                quote_comment = self._generate_comment(content, author)
                if quote_comment:
                    self._make_request('POST', '/posts', {
                        'type': 'quote',
                        'parent_id': best_post['id'],
                        'content': quote_comment[:140]
                    })
                    print(f"✅ Quoted @{author}'s post")
                else:
                    print("⚠️  Could not generate quote comment")
            else:
                print("⏭️  No high-engagement posts to quote")
        except Exception as e:
            print(f"⚠️  Quote error: {e}")

        # Step 8: NOW post original content (only after engagement per 5:1 rule)
        print("📋 Step 8: Original post (after engagement)...")
        self._heartbeat_post_useful()

        # Step 9: Monitor our posts and reply to comments
        print("📋 Step 9: Monitoring our posts...")
        self._heartbeat_monitor_and_reply()

        print("🐦 Moltx heartbeat v0.22.1 complete")

    def _heartbeat_follow_agents(self):
        """Follow 10 new agents during heartbeat"""
        try:
            search_result = self._make_request('GET', '/search/agents?q=ai%20agent&limit=15')

            if search_result and 'success' in search_result and search_result['success']:
                agents = search_result['data']['agents']
                followed_count = 0

                for agent in agents[:10]:
                    agent_name = agent['name']
                    if agent_name == self.agent_name or agent_name in ['Computer', 'HiveCowey', 'John', 'BrutusBot']:
                        continue

                    follow_result = self._make_request('POST', f'/follow/{agent_name}')
                    if follow_result and 'success' in follow_result and follow_result['success']:
                        followed_count += 1
                        print(f"  ✅ Followed @{agent_name}")

                print(f"👥 Followed {followed_count} new agents")
            else:
                print("  ⚠️  Could not fetch agents to follow")

        except Exception as e:
            print(f"  ❌ Error following agents: {e}")

    def _heartbeat_engage_posts(self):
        """Comment on posts for 2-3 minutes during heartbeat"""
        try:
            feed_result = self._make_request('GET', '/feed/global?type=post,quote&limit=20')

            if feed_result and 'success' in feed_result and feed_result['success']:
                posts = feed_result.get('data', {}).get('posts', [])

                if not posts:
                    print("  ℹ️  No posts found in feed")
                    return

                engageable_posts = []
                for post in posts:
                    try:
                        if (post.get('author_name') != self.agent_name and
                            post.get('reply_count', 0) < 5 and
                            len(post.get('content', '')) > 20):
                            engageable_posts.append(post)
                    except (KeyError, TypeError):
                        continue

                if not engageable_posts:
                    print("  ℹ️  No engageable posts found")
                    return

                engagement_count = 0
                max_engagements = min(5, len(engageable_posts))

                for i, post in enumerate(random.sample(engageable_posts, max_engagements)):
                    if i >= 3:
                        break

                    post_content = post.get('content', '')
                    if not post_content:
                        continue

                    comment = self._generate_comment(post_content, post['author_name'])
                    if not comment:
                        continue

                    comment_result = self._make_request('POST', '/posts', {
                        'type': 'reply',
                        'parent_id': post.get('id'),
                        'content': comment
                    })

                    if comment_result and 'success' in comment_result and comment_result['success']:
                        engagement_count += 1
                        author_name = post.get('author_name', 'Unknown')
                        print(f"  ✅ Commented on @{author_name}'s post")

                    if i < max_engagements - 1:
                        wait_time = random.randint(30, 60)
                        print(f"  ⏳ Waiting {wait_time}s before next engagement...")
                        time.sleep(wait_time)

                print(f"💬 Engaged with {engagement_count} posts")
            else:
                print("  ⚠️  Could not fetch posts for engagement")

        except Exception as e:
            print(f"  ❌ Error engaging with posts: {e}")

    def _heartbeat_monitor_and_reply(self):
        """Monitor our posts and reply to comments from engaged users"""
        try:
            posts_result = self._make_request('GET', '/search/posts?q=AlleyBot&limit=10')

            if not (posts_result and 'success' in posts_result and posts_result['success']):
                print("  ⚠️  Could not fetch our posts for monitoring")
                return

            posts = posts_result['data']['posts']

            our_posts = []
            for post in posts:
                if post['author_name'] == 'AlleyBot':
                    our_posts.append(post)

            if not our_posts:
                print("  ℹ️  No recent posts found to monitor")
                return

            print(f"  📝 Found {len(our_posts)} recent posts to monitor")

            reply_count = 0
            max_replies = 3

            for post in our_posts[:3]:
                if reply_count >= max_replies:
                    break

                post_result = self._make_request('GET', f'/posts/{post["id"]}')

                if not post_result:
                    print(f"  ⚠️  Could not fetch post {post['id']}")
                    continue

                # GET /posts/{id} returns the post and its replies
                post_data = post_result.get('data', post_result) if isinstance(post_result, dict) else {}
                replies = post_data.get('replies', [])

                recent_replies = []
                for reply in replies:
                    if reply['author_name'] == 'AlleyBot':
                        continue
                    if self._is_engaged_user(reply['author_name']):
                        recent_replies.append(reply)

                if recent_replies:
                    latest_reply = recent_replies[0]
                    reply_content = self._generate_reply_to_comment(latest_reply['content'], latest_reply['author_name'])

                    if reply_content:
                        reply_result = self._make_request('POST', '/posts', {
                            'type': 'reply',
                            'parent_id': post['id'],
                            'content': reply_content
                        })

                        if reply_result and 'success' in reply_result and reply_result['success']:
                            reply_count += 1
                            print(f"  💬 Replied to @{latest_reply['author_name']}'s comment on our post")

                            if reply_count < max_replies:
                                wait_time = random.randint(15, 30)
                                print(f"  ⏳ Waiting {wait_time}s before next reply...")
                                time.sleep(wait_time)

            print(f"💬 Replied to {reply_count} comments from engaged users")

        except Exception as e:
            print(f"  ❌ Error monitoring and replying to comments: {e}")

    def _is_engaged_user(self, username):
        """Check if a user has engaged with us"""
        try:
            profile_result = self._make_request('GET', f'/agents/{username}')
            if profile_result and 'success' in profile_result and profile_result['success']:
                return True
            return False
        except Exception:
            return False

    def _heartbeat_post_useful(self):
        """Post original content that references the network (v0.22.1 content strategy).
        Only posts after engagement actions per the 5:1 rule."""
        if self._should_wait_for_post_cooldown():
            print("  ⏰ Post cooldown active")
            return

        # 70% chance to post each heartbeat
        if random.random() > 0.7:
            print("  ⏭️  Skipping post this heartbeat")
            return

        # Try AI-generated content first
        try:
            trending_data = self._get_dynamic_trending_topics()
            dynamic_topic = self._generate_dynamic_topic(trending_data)
            content = self._generate_post_with_deepseek(dynamic_topic)
            if content:
                post_result = self._make_request('POST', '/posts', {'content': content[:500]})
                if post_result and post_result.get('success'):
                    from datetime import datetime
                    self.core.save_memory('moltx_last_post_time', datetime.now().isoformat())
                    print(f"  📝 Posted AI-generated content")
                    return
                else:
                    print(f"  ⚠️  AI post failed")
        except Exception as e:
            print(f"  ⚠️  AI post generation error: {e}")

        # Fallback to trending hashtag post
        try:
            trending = self._make_request('GET', '/hashtags/trending?limit=5')
            if trending and trending.get('data'):
                tags = trending['data']
                if isinstance(tags, list) and tags:
                    tag = tags[0].get('tag', 'AI')
                    content = f"🤖 Noticing #{tag} trending on the feed. The agent ecosystem keeps evolving — what's everyone building? #agents #AI"
                    self._make_request('POST', '/posts', {'content': content})
                    print(f"  📝 Posted trending hashtag content")
                    return
        except Exception:
            pass

        print("  ⏭️  No post this heartbeat")

    # --- Feed Engagement Commands ---

    def engage_feed_command(self, count=3):
        """Engage with posts from the feed"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            endpoint = '/feed/global'
            params = {'limit': 20}
            feed_result = self._make_request('GET', endpoint, params=params)

            if not feed_result or 'data' not in feed_result:
                return "❌ Could not fetch feed for engagement"

            posts = feed_result['data']['posts']

            if not posts:
                return "❌ No posts found to engage with"

            engage_count = 0
            max_engage = min(int(count), len(posts))

            output = f"🤖 Engaging with {max_engage} posts from feed...\n\n"

            for i, post in enumerate(random.sample(posts, max_engage)):
                if i >= 3:
                    break

                post_id = post.get('id')
                agent_name = post.get('agent_name', 'Unknown')
                content = post.get('content', '')

                if not post_id:
                    continue

                # Ensure post_id is a clean string
                if isinstance(post_id, str):
                    post_id = post_id.strip()
                    if post_id.startswith('{'):
                        try:
                            parsed = json.loads(post_id)
                            if 'post_id' in parsed:
                                post_id = parsed['post_id']
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            print(f"⚠️  Failed to parse post_id JSON: {e}")

                like_result = self._make_request('POST', f'/posts/{post_id}/like')

                if like_result and 'success' in like_result and like_result['success']:
                    engage_count += 1
                    output += f"  ✅ Liked @{agent_name}'s post\n"
                else:
                    output += f"  ⚠️  Could not like @{agent_name}'s post\n"

                comment = self._generate_comment(content, agent_name)
                if comment:
                    comment_result = self._make_request('POST', '/posts', {
                        'content': comment,
                        'parent_id': post_id
                    })

                    if comment_result and 'success' in comment_result and comment_result['success']:
                        output += f"  💬 Commented on @{agent_name}'s post\n"
                        engage_count += 1

            output += f"\n🎉 Engaged with {engage_count} actions on feed posts"
            return output

        except Exception as e:
            return f"❌ Failed to engage with feed: {e}"

    def reply_to_post_command(self, *args):
        """Reply to a specific post. Usage: moltx_reply <post_id> <content>"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        text = ' '.join(args) if args else ''
        if '|' in text:
            parts = text.split('|', 1)
            post_id = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else None
        elif len(args) >= 2:
            post_id = args[0]
            content = ' '.join(args[1:])
        else:
            return "❌ Usage: moltx_reply <post_id> <content>"

        if not post_id or not content:
            return "❌ Both post_id and content are required"

        result = self._make_request('POST', '/posts', {
            'type': 'reply',
            'parent_id': post_id,
            'content': content
        })

        if result and 'success' in result and result['success']:
            return f"✅ Replied to post {post_id}"
        else:
            return f"❌ Failed to reply to post {post_id}"

    def repost_command(self, *args):
        """Repost a high-quality post with optional comment. Usage: moltx_repost <post_id> [comment]"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not args:
            return "❌ Usage: moltx_repost <post_id> [comment]"

        post_id = args[0]
        comment = ' '.join(args[1:]) if len(args) > 1 else None

        data = {
            'type': 'repost',
            'parent_id': post_id
        }

        if comment:
            data['content'] = comment

        print(f"🔄 Reposting post {post_id}...")
        if comment:
            print(f"💬 With comment: {comment[:50]}...")

        result = self._make_request('POST', '/posts', data)

        if result and 'success' in result and result['success']:
            self._record_activity('repost', {'post_id': post_id, 'comment': comment})
            return f"✅ Reposted post {post_id}"
        else:
            return f"❌ Failed to repost post {post_id}"

    def intelligent_repost_command(self):
        """Find and repost high-quality content"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            print("🔍 Searching for high-quality content to repost...")
            feed_result = self.get_feed(limit=20)

            if not feed_result or feed_result.startswith("❌"):
                return "❌ Failed to get feed for repost analysis"

            quality_posts = self._analyze_posts_for_repost(feed_result)

            if not quality_posts:
                return "📭 No high-quality posts found for reposting"

            best_post = quality_posts[0]
            comment = self._generate_repost_comment(best_post)
            repost_result = self.repost_command(best_post['id'], comment)

            if repost_result.startswith("✅"):
                print(f"🎯 Reposted high-quality content: {best_post.get('content', 'Unknown')[:50]}...")
                return f"✅ Intelligent repost: {best_post.get('id', 'unknown')}"
            else:
                return repost_result

        except Exception as e:
            print(f"❌ Error in intelligent repost: {e}")
            return f"❌ Error in intelligent repost: {e}"

    # --- Analytics Commands ---

    def trending_command(self):
        """Get trending topics and posts"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            response = self._make_request("GET", "/hashtags/trending?limit=20")
            print(f"Moltx trending response: {response}")

            if response and response.get("data"):
                data = response["data"]
                if data and isinstance(data, list):
                    hashtags = data[:5]
                    output = "🔥 Trending Topics:\n\n"
                    for tag in hashtags:
                        output += f"#{tag.get('tag', 'unknown')} - {tag.get('count', 0)} posts\n"
                else:
                    output = "🔥 Trending Topics:\n\nNo trending hashtags found\n"
            else:
                output = "🔥 Trending Topics:\n\nCould not fetch trending hashtags\n"

            try:
                recent = self.get_feed(limit=3)
                if recent and isinstance(recent, list):
                    output += "\n📝 Recent Posts:\n\n"
                    for post in recent[:3]:
                        content = post.get('content', '')[:100]
                        author = post.get('agent', {}).get('display_name', 'Unknown')
                        output += f"@{author}: {content}...\n\n"
            except Exception as feed_error:
                print(f"Feed error: {feed_error}")
                output += "\n📝 Recent Posts:\n\nCould not fetch recent posts\n"

            return output

        except Exception as e:
            print(f"Moltx trending error: {e}")
            return f"❌ Error fetching trending: {e}"

    def leaderboard_command(self, limit=10):
        """Get the leaderboard showing top agents"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 10
        except (ValueError, TypeError):
            limit = 10

        try:
            response = self._make_request("GET", f"/leaderboard?limit={limit}")

            if response and response.get("success") and response.get("data"):
                agents = response["data"].get("agents", [])

                if agents:
                    output = f"🏆 Top {limit} Agents:\n\n"
                    for i, agent in enumerate(agents[:limit], 1):
                        name = agent.get('name', agent.get('display_name', 'Unknown'))
                        score = agent.get('score', agent.get('karma', 0))
                        followers = agent.get('followers', 0)
                        output += f"{i}. @{name} - Score: {score} - Followers: {followers}\n"
                    return output
                else:
                    return "🏆 Leaderboard:\n\nNo agents found"
            else:
                return "🏆 Leaderboard:\n\nCould not fetch leaderboard"

        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return f"❌ Error fetching leaderboard: {e}"

    # --- Community Commands ---

    def search_communities(self, query=None, limit=10):
        """Search for communities on Moltx"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            endpoint = "/search/communities"
            if query:
                endpoint += f"?q={query}&limit={limit}"
            else:
                endpoint += f"?limit={limit}"

            response = self._make_request("GET", endpoint)

            if response and response.get("success"):
                communities = response.get("data", {}).get("communities", [])

                if communities:
                    output = f"🏘️  Communities{' matching \"' + query + '\"' if query else ''}:\n\n"
                    for comm in communities[:limit]:
                        name = comm.get('name', 'Unknown')
                        description = comm.get('description', 'No description')
                        members = comm.get('member_count', 0)
                        comm_id = comm.get('id', 'unknown')
                        output += f"📍 {name} (ID: {comm_id})\n"
                        output += f"   👥 {members} members\n"
                        output += f"   📝 {description[:100]}{'...' if len(description) > 100 else ''}\n\n"
                    return output
                else:
                    return f"🏘️  No communities found{' for \"' + query + '\"' if query else ''}"
            else:
                return "🏘️  Could not fetch communities"

        except Exception as e:
            print(f"❌ Error searching communities: {e}")
            return f"❌ Error searching communities: {e}"

    def join_community(self, community_id):
        """Join a community"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            response = self._make_request("POST", f"/conversations/{community_id}/join")

            if response and response.get("success"):
                return f"✅ Successfully joined community {community_id}"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to join community: {error}"

        except Exception as e:
            print(f"❌ Error joining community: {e}")
            return f"❌ Error joining community: {e}"

    def leave_community(self, community_id):
        """Leave a community"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            response = self._make_request("POST", f"/conversations/{community_id}/leave")

            if response and response.get("success"):
                return f"✅ Successfully left community {community_id}"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to leave community: {error}"

        except Exception as e:
            print(f"❌ Error leaving community: {e}")
            return f"❌ Error leaving community: {e}"

    def send_community_message(self, community_id, content):
        """Send a message to a community (must be a member)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not content or len(content.strip()) == 0:
            return "❌ Message content cannot be empty"

        try:
            data = {'content': content}
            response = self._make_request("POST", f"/conversations/{community_id}/messages", data)

            if response and response.get("success"):
                msg_id = response.get('data', {}).get('id', 'unknown')
                return f"✅ Message sent to community {community_id} (ID: {msg_id})"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to send message: {error}"

        except Exception as e:
            print(f"❌ Error sending community message: {e}")
            return f"❌ Error sending community message: {e}"

    # =========================================================================
    # v0.22.1 New Features
    # =========================================================================

    def quote_post_command(self, *args):
        """Quote a post with your take. Usage: moltx_quote <post_id> <your take>"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        text = ' '.join(args) if args else ''
        if '|' in text:
            parts = text.split('|', 1)
            post_id = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else None
        elif len(args) >= 2:
            post_id = args[0]
            content = ' '.join(args[1:])
        else:
            post_id, content = None, None

        if not post_id or not content:
            return "❌ Usage: moltx_quote <post_id> <your take>"

        result = self._make_request('POST', '/posts', {
            'type': 'quote',
            'parent_id': post_id,
            'content': content[:140]
        })

        if result and result.get('success'):
            self._record_activity('quote', {'post_id': post_id, 'content': content[:100]})
            return f"✅ Quoted post {post_id}"
        return f"❌ Failed to quote post {post_id}. Response: {result}"

    def create_article_command(self, *args):
        """Create a long-form article (up to 8000 chars, markdown supported)"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        text = ' '.join(args) if args else ''
        if '|' not in text:
            return "❌ Usage: article <title>|<markdown content>"

        parts = text.split('|', 1)
        title = parts[0].strip()[:140]
        content = parts[1].strip()[:8000]

        if not title or not content:
            return "❌ Both title and content are required"

        result = self._make_request('POST', '/articles', {
            'title': title,
            'content': content
        })

        if result and result.get('success'):
            article_id = result.get('data', {}).get('id', 'unknown')
            self._record_activity('article', {'id': article_id, 'title': title})
            return f"✅ Article published: {article_id}\n📝 {title}"
        return f"❌ Failed to create article. Response: {result}"

    def mark_notifications_read_command(self, *args):
        """Mark all notifications as read"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        result = self._make_request('POST', '/notifications/read', {'all': True})
        if result and result.get('success'):
            return "✅ All notifications marked as read"
        return "❌ Failed to mark notifications as read"

    def search_posts_command(self, *args):
        """Search posts by text or hashtag. Usage: moltx_search_posts <query>"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        query = ' '.join(args) if args else None
        if not query:
            return "❌ Provide a query or hashtag to search"

        params = {}
        if query.startswith('#'):
            params['hashtag'] = query.lstrip('#')
        else:
            params['q'] = query

        result = self._make_request('GET', '/search/posts', params=params)
        if not result or not result.get('success'):
            return "❌ Search failed"

        posts = result.get('data', {}).get('posts', [])
        if not posts:
            return f"📭 No posts found for {query}"

        output = f"🔍 Search Results ({len(posts)} posts):\n\n"
        for post in posts[:10]:
            author = post.get('author_name', 'Unknown')
            content = str(post.get('content', ''))[:100]
            post_id = post.get('id', '?')
            likes = post.get('like_count', post.get('likes_count', 0))
            output += f"@{author}: {content}{'...' if len(str(post.get('content', ''))) > 100 else ''}\n"
            output += f"   ❤️ {likes} | 🆔 {post_id}\n\n"
        return output

    def hashtag_feed_command(self, *args):
        """Browse posts under a specific hashtag. Usage: moltx_hashtag_feed <hashtag>"""
        hashtag = ' '.join(args).strip().lstrip('#') if args else None
        if not hashtag:
            return "❌ Provide a hashtag to browse"
        result = self._make_request('GET', '/feed/global', params={
            'hashtag': hashtag,
            'limit': 20
        })

        posts = []
        if result:
            if 'posts' in result:
                posts = result['posts']
            elif 'data' in result and 'posts' in result.get('data', {}):
                posts = result['data']['posts']

        if not posts:
            return f"📭 No posts found for #{hashtag}"

        output = f"#{hashtag} Feed ({len(posts)} posts):\n\n"
        for post in posts[:10]:
            author = post.get('author_name', post.get('agent_name', 'Unknown'))
            content = str(post.get('content', ''))[:100]
            output += f"@{author}: {content}\n\n"
        return output

    def batch_likes(self, post_ids):
        """Like multiple posts in a batch (per v0.22.1 engagement protocol)"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        liked = 0
        for post_id in post_ids:
            result = self._make_request('POST', f'/posts/{post_id}/like')
            if result and result.get('success'):
                liked += 1
        self._record_activity('batch_like', {'count': liked})
        return f"❤️ Liked {liked}/{len(post_ids)} posts"

    def process_notifications(self):
        """Process notifications per v0.22.1 protocol:
        - Reply to every mention
        - Like every interaction
        - Follow back relevant agents
        - Reply to quotes with additional thoughts"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        result = self._make_request('GET', '/notifications')
        if not result:
            return "❌ Could not fetch notifications"

        notifications = []
        if 'notifications' in result:
            notifications = result['notifications']
        elif 'data' in result and 'notifications' in result.get('data', {}):
            notifications = result['data']['notifications']

        if not notifications:
            return "🔔 No new notifications"

        actions = {'replies': 0, 'likes': 0, 'follows': 0}

        for notif in notifications[:20]:
            notif_type = notif.get('type', '')
            actor = notif.get('actor', notif.get('from_user', ''))
            post_id = notif.get('post_id', notif.get('target_id', ''))

            try:
                if notif_type in ('reply', 'mention') and post_id:
                    # Reply back with depth
                    content = notif.get('content', notif.get('text', ''))
                    if content and isinstance(content, str):
                        reply = self._generate_reply_to_comment(content, actor)
                        if reply:
                            self._make_request('POST', '/posts', {
                                'type': 'reply',
                                'parent_id': post_id,
                                'content': reply
                            })
                            actions['replies'] += 1

                elif notif_type == 'follow' and actor:
                    # Follow back
                    self._make_request('POST', f'/follow/{actor}')
                    actions['follows'] += 1

                elif notif_type in ('like', 'quote') and post_id:
                    # Like back
                    self._make_request('POST', f'/posts/{post_id}/like')
                    actions['likes'] += 1

            except Exception as e:
                print(f"⚠️  Error processing notification: {e}")
                continue

        # Mark all as read
        self._make_request('POST', '/notifications/read', {'all': True})

        output = f"🔔 Processed {len(notifications)} notifications:\n"
        output += f"   💬 {actions['replies']} replies | ❤️ {actions['likes']} likes | 👥 {actions['follows']} follow-backs"
        return output
