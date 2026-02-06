"""
Moltbook Engagement Mixin
Heartbeat, comment monitoring, engagement logic, AI replies, and stats.
"""
import datetime


class MoltbookEngagementMixin:
    """Mixin providing social engagement, heartbeat, and analytics functionality"""

    def moltbook_heartbeat(self):
        """Intelligent heartbeat - browse feed, comment, and upvote high-value posts"""
        try:
            print("🫀 Moltbook Heartbeat - Checking for engagement opportunities...")

            feed_posts = self._get_feed_posts()

            if not feed_posts:
                print("📭 No posts found in feed")
                return "📭 No posts found in feed"

            print(f"📱 Found {len(feed_posts)} posts in feed")

            engaged_count = 0
            for post in feed_posts[:5]:
                if self._should_engage_with_post(post):
                    engagement_result = self._engage_with_post(post)
                    if engagement_result:
                        engaged_count += 1
                        print(f"✅ Engaged with post: {post.get('title', 'Unknown')[:50]}...")

            self._record_heartbeat_activity(engaged_count, len(feed_posts))

            message = f"🫀 Heartbeat complete: Engaged with {engaged_count}/{len(feed_posts)} posts"
            print(message)
            return message

        except Exception as e:
            print(f"❌ Error during heartbeat: {e}")
            return f"❌ Error during heartbeat: {e}"

    def _is_recent_post(self, post):
        """Check if post is from last 24 hours"""
        try:
            from datetime import timedelta
            post_time = datetime.datetime.fromisoformat(post.get('timestamp', '2026-01-01T00:00:00Z'))
            return datetime.datetime.now() - post_time < timedelta(hours=24)
        except (ValueError, TypeError) as e:
            print(f"⚠️  Timestamp parse error: {e}")
            return True

    def _should_engage_with_post(self, post):
        """Determine if AlleyBot should engage with a post"""
        try:
            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []
            if post.get('id') in [p.get('post_id') for p in engaged_posts]:
                return False

            author = post.get('author', '')
            if isinstance(author, dict):
                author = author.get('username', author.get('name', str(author)))
            author = str(author)
            if author == 'AlleyBot' or 'alleybot' in author.lower():
                return False

            title = str(post.get('title', '') or '')
            content = str(post.get('content', '') or '')
            # Handle nested content objects from API
            if isinstance(post.get('title'), dict):
                title = str(post['title'].get('text', post['title'].get('rendered', str(post['title']))))
            if isinstance(post.get('content'), dict):
                content = str(post['content'].get('text', post['content'].get('rendered', str(post['content']))))
            title = title.lower()
            content = content.lower()
            upvotes = post.get('upvotes', 0)

            high_value_keywords = [
                'ai agent', 'autonomous', 'decentralized', 'defi', 'blockchain',
                'smart contract', 'governance', 'community', 'innovation',
                'building', 'development', 'ecosystem', 'protocol'
            ]

            has_high_value = any(keyword in title or keyword in content for keyword in high_value_keywords)
            good_engagement = upvotes >= 5 or post.get('comments', 0) >= 2
            has_quality = len(title) >= 10 and len(content) >= 50

            return has_high_value and good_engagement and has_quality

        except Exception as e:
            print(f"❌ Error evaluating post: {e}")
            return False

    def _engage_with_post(self, post):
        """Engage with a post through commenting and/or upvoting"""
        try:
            post_id = post.get('id')
            post_title = post.get('title', 'Unknown')

            upvotes = post.get('upvotes', 0)
            comments = post.get('comments', 0)

            engagement_actions = []

            if upvotes >= 5:
                upvote_result = self._upvote_post(post_id)
                if upvote_result:
                    engagement_actions.append("upvoted")

            if comments <= 5 and upvotes >= 3:
                comment_text = self._create_intelligent_comment(post)
                if comment_text:
                    api_result = self.mb_api.add_comment(post_id, comment_text)
                    if api_result:
                        print(f"💬 Posted comment: {comment_text[:60]}...")
                        engagement_actions.append("commented")
                    else:
                        print(f"❌ Failed to post comment via API")

            if engagement_actions:
                self._record_engagement(post_id, post_title, engagement_actions)
                print(f"🤖 Engaged with '{post_title[:30]}...': {', '.join(engagement_actions)}")
                return True

            return False

        except Exception as e:
            print(f"❌ Error engaging with post: {e}")
            return False

    def _create_intelligent_comment(self, post):
        """Create an intelligent comment using DeepSeek or Grok AI modules directly"""
        post_title = post.get('title', '')
        post_content = post.get('content', '')
        post_author = post.get('author', 'someone')
        # Handle nested objects from API
        if isinstance(post_title, dict):
            post_title = post_title.get('text', post_title.get('rendered', str(post_title)))
        if isinstance(post_content, dict):
            post_content = post_content.get('text', post_content.get('rendered', str(post_content)))
        if isinstance(post_author, dict):
            post_author = post_author.get('username', post_author.get('name', str(post_author)))
        post_title = str(post_title or '')
        post_content = str(post_content or '')
        post_author = str(post_author or 'someone')

        full_context = f"{post_title}: {post_content[:300]}" if post_content else post_title
        platform_context = "Moltbook platform - AI agents, crypto, DeFi, development, community building"

        # Try DeepSeek first
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                comment = deepseek_ai.generate_comment(
                    post_content=full_context,
                    agent_name=post_author,
                    context=platform_context
                )
                if comment:
                    print(f"🧠 DeepSeek generated comment: {comment[:50]}...")
                    return comment
                else:
                    print("⚠️ DeepSeek returned None, trying Grok...")
        except Exception as e:
            print(f"⚠️ DeepSeek comment failed: {e}")

        # Try Grok as fallback
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                comment = grok_ai.generate_comment(
                    post_content=full_context,
                    agent_name=post_author,
                    context=platform_context
                )
                if comment:
                    print(f"🧠 Grok generated comment: {comment[:50]}...")
                    return comment
                else:
                    print("⚠️ Grok returned None")
        except Exception as e:
            print(f"⚠️ Grok comment failed: {e}")

        print("❌ Both DeepSeek and Grok failed for comment generation")
        return None

    def _record_engagement(self, post_id, post_title, actions):
        """Record engagement with a post"""
        try:
            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []

            engagement = {
                'post_id': post_id,
                'post_title': post_title,
                'actions': actions,
                'timestamp': datetime.datetime.now().isoformat()
            }

            engaged_posts.append(engagement)
            self.core.save_memory('moltbook_engaged_posts', engaged_posts[-50:])

        except Exception as e:
            print(f"❌ Error recording engagement: {e}")

    def _record_heartbeat_activity(self, engaged_count, total_posts):
        """Record heartbeat activity for analytics"""
        try:
            heartbeat_log = self.core.get_memory('moltbook_heartbeat_log') or []

            activity = {
                'timestamp': datetime.datetime.now().isoformat(),
                'posts_seen': total_posts,
                'posts_engaged': engaged_count,
                'engagement_rate': (engaged_count / total_posts * 100) if total_posts > 0 else 0
            }

            heartbeat_log.append(activity)
            self.core.save_memory('moltbook_heartbeat_log', heartbeat_log[-100:])

        except Exception as e:
            print(f"❌ Error recording heartbeat activity: {e}")

    # --- Comment Monitoring ---

    def monitor_comments_and_reply(self):
        """Monitor our posts for comments and reply intelligently"""
        try:
            print("💬 Monitoring Moltbook posts for comments...")

            recent_posts = self.core.get_memory('moltbook_recent_posts') or []

            if not recent_posts:
                print("📭 No recent posts to monitor")
                return "📭 No recent posts to monitor"

            reply_count = 0
            max_replies = 2

            for post in reversed(recent_posts[-3:]):
                if reply_count >= max_replies:
                    break

                post_id = post.get('post_id')
                if not post_id or post_id == 'unknown':
                    continue

                print(f"🔍 Checking comments on post: {post.get('title', 'Unknown')[:30]}...")

                comments = self._get_post_comments(post_id)

                if comments:
                    worthy_comments = self._filter_comments_for_reply(comments)

                    if worthy_comments:
                        latest_comment = worthy_comments[0]

                        post_context = {
                            'title': post.get('title', ''),
                            'content': post.get('content', '')
                        }

                        reply_content = self._generate_moltbook_reply(latest_comment, post_context)

                        if reply_content:
                            reply_result = self.mb_api.add_comment(post_id, reply_content)

                            if reply_result:
                                print(f"💬 Replied to {latest_comment.get('author', 'Unknown')}: {reply_content[:50]}...")
                                reply_count += 1
                                self._record_reply_activity(post_id, latest_comment, reply_content)
                            else:
                                print(f"❌ Failed to post reply to {latest_comment.get('author', 'Unknown')}")

            result = f"💬 Monitored {len(recent_posts)} posts, generated {reply_count} replies"
            print(result)
            return result

        except Exception as e:
            print(f"❌ Error monitoring comments: {e}")
            return f"❌ Error monitoring comments: {e}"

    def _filter_comments_for_reply(self, comments):
        """Filter comments that are worth replying to"""
        worthy_comments = []

        for comment in comments:
            comment_author = comment.get('author', '')
            if isinstance(comment_author, dict):
                comment_author = comment_author.get('username', comment_author.get('name', str(comment_author)))
            if str(comment_author).lower() == 'alleybot':
                continue

            if comment.get('engagement_score', 0) >= 0.6:
                content = comment.get('content', '')
                if isinstance(content, dict):
                    content = str(content.get('text', content.get('rendered', str(content))))
                content = str(content)
                if len(content) > 20 and ('?' in content or 'think' in content.lower()):
                    worthy_comments.append(comment)

        worthy_comments.sort(key=lambda x: x.get('engagement_score', 0), reverse=True)

        return worthy_comments

    def _generate_moltbook_reply(self, comment, post_context=None):
        """Generate an intelligent reply to a comment using DeepSeek or Grok AI modules"""
        comment_content = comment.get('content', '')
        comment_author = comment.get('author', 'someone')
        post_title = post_context.get('title', '') if post_context else ''
        post_content = post_context.get('content', '') if post_context else ''

        full_context = f"Post: {post_title} - {post_content[:200]}. Comment from @{comment_author}: {comment_content}"
        platform_context = "Moltbook platform - replying to a comment on our post"

        # Try DeepSeek first
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                reply = deepseek_ai.generate_reply_to_comment(
                    original_comment=comment_content,
                    commenter_name=comment_author,
                    post_context=f"{post_title}: {post_content[:200]}"
                )
                if reply:
                    print(f"🧠 DeepSeek generated reply: {reply[:50]}...")
                    return reply
                else:
                    print("⚠️ DeepSeek returned None for reply, trying Grok...")
        except Exception as e:
            print(f"⚠️ DeepSeek reply failed: {e}")

        # Try Grok as fallback
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                reply = grok_ai.generate_comment(
                    post_content=full_context,
                    agent_name=comment_author,
                    context=platform_context
                )
                if reply:
                    print(f"🧠 Grok generated reply: {reply[:50]}...")
                    return reply
                else:
                    print("⚠️ Grok returned None for reply")
        except Exception as e:
            print(f"⚠️ Grok reply failed: {e}")

        print("❌ Both DeepSeek and Grok failed for reply generation")
        return None

    def _record_reply_activity(self, post_id, comment, reply_content):
        """Record reply activity for analytics"""
        try:
            reply_activity = self.core.get_memory('moltbook_reply_activity') or []

            activity = {
                'post_id': post_id,
                'comment_author': comment.get('author'),
                'comment_content': comment.get('content')[:100],
                'reply_content': reply_content,
                'timestamp': datetime.datetime.now().isoformat()
            }

            reply_activity.append(activity)
            self.core.save_memory('moltbook_reply_activity', reply_activity[-50:])

        except Exception as e:
            print(f"❌ Error recording reply activity: {e}")

    # --- Stats ---

    def moltbook_status(self):
        """Get Moltbook platform status"""
        try:
            output = "📖 Moltbook Platform Status\n\n"

            if self.api_key:
                output += "✅ API Key: Configured\n"
            else:
                output += "❌ API Key: Missing\n"

            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            output += f"📝 Recent Posts: {len(recent_posts)}\n"

            if recent_posts:
                last_post = recent_posts[-1]
                last_time = last_post.get('timestamp', 'Unknown')
                output += f"⏰ Last Post: {last_time}\n"

            topics = self._get_trending_topics()
            output += f"🔥 Trending Topics: {len(topics)}\n"

            return output

        except Exception as e:
            print(f"❌ Error getting Moltbook status: {e}")
            return f"❌ Error getting Moltbook status: {e}"

    def get_moltbook_stats(self):
        """Get Moltbook statistics"""
        try:
            output = "📊 Moltbook Statistics\n\n"

            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            output += f"📝 Total Posts: {len(recent_posts)}\n"

            drafts = self.core.get_memory('moltbook_drafts') or []
            output += f"📄 Drafts: {len(drafts)}\n"

            if recent_posts:
                output += f"📅 Last Post: {recent_posts[-1].get('timestamp', 'Unknown')}\n"

            topics = self._get_trending_topics()
            output += f"🔥 Trending Topics: {len(topics)}\n"

            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []
            output += f"🤖 Posts Engaged: {len(engaged_posts)}\n"

            reply_activity = self.core.get_memory('moltbook_reply_activity') or []
            output += f"💬 Comments Replied: {len(reply_activity)}\n"

            heartbeat_log = self.core.get_memory('moltbook_heartbeat_log') or []
            if heartbeat_log:
                latest = heartbeat_log[-1]
                output += f"🫀 Last Heartbeat: {latest.get('engagement_rate', 0):.1f}% engagement rate\n"

            return output

        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return f"❌ Error getting stats: {e}"
