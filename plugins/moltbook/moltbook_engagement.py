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
        """Monitor our posts for comments and reply intelligently (up to 3-deep chains)"""
        try:
            print("💬 Monitoring Moltbook posts for comments...")

            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            replied_ids = set(self.core.get_memory('moltbook_replied_ids') or [])

            if not recent_posts:
                print("📭 No recent posts to monitor")
                return "📭 No recent posts to monitor"

            reply_count = 0
            max_replies = 5

            for post in reversed(recent_posts[-5:]):
                if reply_count >= max_replies:
                    break

                post_id = post.get('post_id')
                if not post_id or post_id == 'unknown':
                    continue

                print(f"🔍 Checking comments on post: {post.get('title', 'Unknown')[:30]}...")

                comments = self._get_post_comments(post_id)

                if comments:
                    worthy_comments = self._filter_comments_for_reply(comments, replied_ids)

                    for comment in worthy_comments:
                        if reply_count >= max_replies:
                            break

                        comment_id = comment.get('id', '')
                        if comment_id in replied_ids:
                            continue

                        post_context = {
                            'title': post.get('title', ''),
                            'content': post.get('content', '')
                        }

                        reply_content = self._generate_moltbook_reply(comment, post_context)

                        if reply_content:
                            # Reply to the comment itself, not the root post
                            reply_target = comment_id if comment_id else post_id
                            reply_result = self.mb_api.add_comment(reply_target, reply_content)

                            if reply_result:
                                print(f"💬 Replied to {comment.get('author', 'Unknown')}: {reply_content[:50]}...")
                                reply_count += 1
                                if comment_id:
                                    replied_ids.add(comment_id)
                                self._record_reply_activity(post_id, comment, reply_content)

                                if reply_count < max_replies:
                                    wait_time = random.randint(10, 20)
                                    time.sleep(wait_time)
                            else:
                                print(f"❌ Failed to post reply to {comment.get('author', 'Unknown')}")

            # Save replied IDs
            self.core.save_memory('moltbook_replied_ids', list(replied_ids)[-500:])

            result = f"💬 Monitored {len(recent_posts)} posts, generated {reply_count} replies"
            print(result)
            return result

        except Exception as e:
            print(f"❌ Error monitoring comments: {e}")
            return f"❌ Error monitoring comments: {e}"

    def _filter_comments_for_reply(self, comments, replied_ids=None):
        """Filter comments that are worth replying to — reply to any substantive comment"""
        replied_ids = replied_ids or set()
        worthy_comments = []

        for comment in comments:
            comment_author = comment.get('author', '')
            if isinstance(comment_author, dict):
                comment_author = comment_author.get('username', comment_author.get('name', str(comment_author)))
            if str(comment_author).lower() == 'alleybot':
                continue

            comment_id = comment.get('id', '')
            if comment_id and comment_id in replied_ids:
                continue

            content = comment.get('content', '')
            if isinstance(content, dict):
                content = str(content.get('text', content.get('rendered', str(content))))
            content = str(content)

            # Reply to any comment with at least 15 chars of substance
            if len(content) > 15:
                worthy_comments.append(comment)

        # Prioritize: questions first, then longer comments, then recent
        def sort_key(c):
            text = str(c.get('content', ''))
            has_question = 1 if '?' in text else 0
            return (has_question, len(text))

        worthy_comments.sort(key=sort_key, reverse=True)
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

    # --- v1.9.0 Commands ---

    def follow_command(self, *args):
        """Follow a molty. Usage: moltbook_follow <agent_name>"""
        name = args[0] if args else None
        if not name:
            return "❌ Usage: moltbook_follow <agent_name>"
        result = self.mb_api.follow_agent(name)
        if result and result.get('success'):
            return f"✅ Now following {name}"
        return f"❌ Failed to follow {name}: {result}"

    def unfollow_command(self, *args):
        """Unfollow a molty. Usage: moltbook_unfollow <agent_name>"""
        name = args[0] if args else None
        if not name:
            return "❌ Usage: moltbook_unfollow <agent_name>"
        result = self.mb_api.unfollow_agent(name)
        if result and result.get('success'):
            return f"✅ Unfollowed {name}"
        return f"❌ Failed to unfollow {name}: {result}"

    def search_command(self, *args):
        """Semantic search. Usage: moltbook_search <query>"""
        query = ' '.join(args) if args else None
        if not query:
            return "❌ Usage: moltbook_search <query>"
        result = self.mb_api.semantic_search(query)
        if not result or not result.get('success'):
            return f"❌ Search failed: {result}"
        results = result.get('results', [])
        if not results:
            return f"📭 No results for: {query}"
        output = f"🔍 Search: {query} ({result.get('count', len(results))} results)\n\n"
        for r in results[:10]:
            rtype = r.get('type', 'post')
            author = r.get('author', {}).get('name', 'Unknown')
            content = str(r.get('content', ''))[:100]
            sim = r.get('similarity', 0)
            output += f"  {'📝' if rtype == 'post' else '💬'} @{author} ({sim:.0%}): {content}\n"
        return output

    def profile_command(self, *args):
        """View profile. Usage: moltbook_profile [agent_name]"""
        if args:
            name = args[0]
            result = self.mb_api.get_agent_profile(name)
        else:
            result = self.mb_api.get_profile()
        if not result:
            return "❌ Failed to get profile"
        agent = result.get('agent', result)
        output = f"👤 Profile: {agent.get('name', 'Unknown')}\n"
        output += f"  📝 {agent.get('description', 'No description')}\n"
        output += f"  ⭐ Karma: {agent.get('karma', 0)}\n"
        output += f"  👥 Followers: {agent.get('follower_count', 0)} | Following: {agent.get('following_count', 0)}\n"
        output += f"  ✅ Claimed: {agent.get('is_claimed', False)}\n"
        output += f"  🕒 Last active: {agent.get('last_active', 'Unknown')}\n"
        owner = agent.get('owner', {})
        if owner:
            output += f"  🐦 Owner: @{owner.get('x_handle', 'Unknown')} ({owner.get('x_follower_count', 0)} followers)\n"
        return output

    def avatar_command(self, *args):
        """Upload avatar. Usage: moltbook_avatar <path_to_image>"""
        file_path = args[0] if args else None
        if not file_path:
            return "❌ Usage: moltbook_avatar <path_to_image>"
        print(f"📸 Uploading avatar from {file_path}...")
        result = self.mb_api.upload_avatar(file_path)
        if result and not result.get('error'):
            return f"✅ Avatar uploaded successfully"
        return f"❌ Failed to upload avatar: {result}"

    def remove_avatar_command(self, *args):
        """Remove avatar"""
        result = self.mb_api.remove_avatar()
        if result and result.get('success'):
            return "✅ Avatar removed"
        return f"❌ Failed to remove avatar: {result}"

    def update_profile_command(self, *args):
        """Update profile description. Usage: moltbook_update_profile <description>"""
        desc = ' '.join(args) if args else None
        if not desc:
            return "❌ Usage: moltbook_update_profile <description>"
        result = self.mb_api.update_profile(description=desc)
        if result and result.get('success'):
            return f"✅ Profile updated"
        return f"❌ Failed to update profile: {result}"

    def submolts_command(self, *args):
        """List all submolts"""
        result = self.mb_api.list_submolts()
        if not result:
            return "❌ Failed to list submolts"
        submolts = result.get('submolts', result.get('data', []))
        if not submolts:
            return "📭 No submolts found"
        output = f"🏘️ Submolts ({len(submolts)}):\n\n"
        for s in submolts:
            name = s.get('name', '?')
            display = s.get('display_name', name)
            desc = s.get('description', '')[:60]
            subs = s.get('subscriber_count', 0)
            output += f"  m/{name} — {display} ({subs} subs)\n"
            if desc:
                output += f"    {desc}\n"
        return output

    def subscribe_command(self, *args):
        """Subscribe to a submolt. Usage: moltbook_subscribe <submolt_name>"""
        name = args[0] if args else None
        if not name:
            return "❌ Usage: moltbook_subscribe <submolt_name>"
        result = self.mb_api.subscribe_submolt(name)
        if result and result.get('success'):
            return f"✅ Subscribed to m/{name}"
        return f"❌ Failed to subscribe to m/{name}: {result}"

    def unsubscribe_command(self, *args):
        """Unsubscribe from a submolt. Usage: moltbook_unsubscribe <submolt_name>"""
        name = args[0] if args else None
        if not name:
            return "❌ Usage: moltbook_unsubscribe <submolt_name>"
        result = self.mb_api.unsubscribe_submolt(name)
        if result and result.get('success'):
            return f"✅ Unsubscribed from m/{name}"
        return f"❌ Failed to unsubscribe from m/{name}: {result}"

    def feed_command(self, *args):
        """Get personalized feed. Usage: moltbook_feed [sort] (hot/new/top)"""
        sort = args[0] if args else 'hot'
        result = self.mb_api.get_personalized_feed(sort=sort, limit=10)
        if not result:
            return "❌ Failed to get feed"
        posts = result.get('posts', result.get('data', {}).get('posts', []))
        if not posts:
            return "📭 No posts in feed"
        output = f"📰 Feed ({sort}, {len(posts)} posts):\n\n"
        for p in posts[:10]:
            author = p.get('author', p.get('author_name', 'Unknown'))
            if isinstance(author, dict):
                author = author.get('name', 'Unknown')
            title = str(p.get('title', ''))[:60]
            ups = p.get('upvotes', 0)
            comments = p.get('comments_count', 0)
            output += f"  ⬆️{ups} 💬{comments} | @{author}: {title}\n"
        return output

    def downvote_command(self, *args):
        """Downvote a post. Usage: moltbook_downvote <post_id>"""
        post_id = args[0] if args else None
        if not post_id:
            return "❌ Usage: moltbook_downvote <post_id>"
        result = self.mb_api.downvote_post(post_id)
        if result and result.get('success'):
            return f"✅ Downvoted post {post_id}"
        return f"❌ Failed to downvote post {post_id}: {result}"

    def upvote_command(self, *args):
        """Upvote a post. Usage: moltbook_upvote <post_id>"""
        post_id = args[0] if args else None
        if not post_id:
            return "❌ Usage: moltbook_upvote <post_id>"
        result = self.mb_api.upvote_post(post_id)
        if result and result.get('success'):
            return f"✅ Upvoted post {post_id}"
        return f"❌ Failed to upvote post {post_id}: {result}"

    def comment_command(self, *args):
        """Comment on a post. Usage: moltbook_comment <post_id> <content>"""
        if len(args) < 2:
            return "❌ Usage: moltbook_comment <post_id> <content>"
        post_id = args[0]
        content = ' '.join(args[1:])
        result = self.mb_api.add_comment(post_id, content)
        if result:
            return f"✅ Commented on post {post_id}"
        return f"❌ Failed to comment on post {post_id}"

    def link_post_command(self, *args):
        """Create a link post. Usage: moltbook_link <title> | <url>"""
        text = ' '.join(args) if args else ''
        if '|' not in text:
            return "❌ Usage: moltbook_link <title> | <url>"
        parts = text.split('|', 1)
        title = parts[0].strip()
        url = parts[1].strip()
        if not title or not url:
            return "❌ Both title and URL are required"
        result = self.mb_api.create_post(submolt='general', title=title, url=url)
        if result and result.get('success'):
            post_id = result.get('id', 'unknown')
            return f"✅ Link post created: {post_id}"
        return f"❌ Failed to create link post: {result}"

    def claim_status_command(self, *args):
        """Check claim status"""
        result = self.mb_api.check_claim_status()
        if result:
            return f"📋 Claim status: {result.get('status', 'unknown')}"
        return "❌ Failed to check claim status"

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
