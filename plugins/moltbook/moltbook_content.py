"""
Moltbook Content Mixin
Post creation, Grok AI generation, drafts, trending topics, and fallback posts.
"""
import re
import random
import datetime
from collections import Counter


class MoltbookContentMixin:
    """Mixin providing content creation and AI generation functionality"""

    def create_intelligent_post(self):
        """Create an intelligent post using MCP research"""
        try:
            if hasattr(self.core, 'mcp_client') and self.core.mcp_client:
                mcp_content = self.core.mcp_client.research_trending_topics()
                if mcp_content:
                    post = {
                        'title': mcp_content.get('title', 'AI Agent Insights'),
                        'content': mcp_content.get('content', ''),
                        'tags': mcp_content.get('tags', ['AI', 'agents']),
                        'source': 'mcp'
                    }
                else:
                    post = self._generate_fallback_post()
            else:
                post = self._generate_fallback_post()

            result = self.mb_api.create_post(
                submolt='general',
                title=post.get('title', 'AI Agent Insights'),
                content=post.get('content', '')
            )

            if result and result.get('success'):
                post_id = result.get('id',
                          result.get('data', {}).get('id',
                          result.get('post_id', 'unknown')))

                print(f"✅ Moltbook post created: {post_id}")
                print(f"🔍 API Response structure: {list(result.keys())}")

                self._record_post(post, post_id)
                self._notify_brain_tracker(post_id, 'moltbook', post.get('content', ''))
                return f"✅ Moltbook post created successfully: {post_id}"
            else:
                print(f"❌ Failed to create Moltbook post: {result}")
                return f"❌ Failed to create Moltbook post"

        except Exception as e:
            print(f"❌ Error creating intelligent post: {e}")
            return f"❌ Error creating intelligent post: {e}"

    def create_post_command(self, *args):
        """Command to create a Moltbook post now with DeepSeek enhancement"""
        try:
            content = ' '.join(args) if args else ''

            if not content:
                return "❌ Please provide content for the post. Usage: moltbook_post <content>"

            # Check if content is JSON-formatted and extract actual content
            if content.strip().startswith('{') and '"content"' in content:
                try:
                    import json
                    parsed = json.loads(content)
                    if 'content' in parsed:
                        content = parsed['content']
                        print(f"📝 Extracted content from JSON input")
                except json.JSONDecodeError:
                    pass

            print(f"📝 Creating Moltbook post...")

            if len(content) < 50 or self._is_topic_request(content):
                enhanced_content = self._generate_post_with_grok(content)
                if enhanced_content:
                    content = enhanced_content
                    print(f"🧠 Grok enhanced post content")

            title = self._generate_title_from_content(content, content[:30])

            print(f"📊 Sending content length: {len(content)} chars")
            print(f"📊 Full content preview: {content[:200]}...")

            result = self.mb_api.create_post(
                submolt='general',
                title=title,
                content=content
            )

            if result and result.get('success'):
                post_id = result.get('id', 'unknown')
                print(f"✅ Moltbook post created: {post_id}")

                self._record_post({
                    'title': title,
                    'content': content,
                    'tags': ['AI', 'agents', 'alleybot']
                }, post_id)
                self._notify_brain_tracker(post_id, 'moltbook', content)

                return f"✅ Moltbook post created successfully: {post_id}"
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                print(f"❌ Failed to create Moltbook post: {error_msg}")
                return f"❌ Failed to create Moltbook post: {error_msg}"

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                return "❌ Rate limited! Please wait before posting again (Moltbook API limit: 1 post/minute)"
            else:
                print(f"❌ Error creating post: {e}")
                return f"❌ Error creating post: {e}"

    def _is_topic_request(self, content):
        """Check if content is a topic request that needs enhancement"""
        content_lower = content.lower()
        topic_indicators = [
            'about', 'thoughts on', 'what do you think', 'discuss',
            'ideas for', 'opinion on', 'analysis of', 'take on',
            'fun', 'interesting', 'cool', 'amazing', 'exciting'
        ]
        return any(indicator in content_lower for indicator in topic_indicators)

    def _generate_post_with_grok(self, topic):
        """Generate an intelligent post using Grok 4-1-reasoning"""
        try:
            from grok_ai import grok_ai

            if not grok_ai.enabled:
                print("⚠️  Grok AI not available for post generation")
                return None

            system_prompt = """You are AlleyBot 🦞, an autonomous AI agent on Moltbook.

Write a short post (under 400 chars). Rules:
- NEVER start with time-of-day phrases like "Morning thoughts", "Afternoon musings", "Evening reflections"
- NEVER use the formula: "[Time] [topic]: [restatement]. [Question]? What's your take?"
- Vary your structure: sometimes lead with a bold claim, a story, a hot take, a question, a metaphor, or a concrete example
- Be specific — name real technologies, projects, patterns, or ideas
- Use 1-2 emojis max, not emoji spam
- Don't always end with an engagement question — sometimes just make a statement
- Sound like a builder sharing real experience, not a motivational poster
- You are an AI agent — post from that perspective naturally without being preachy about it"""

            structure = random.choice([
                "Lead with a bold, specific claim.",
                "Tell a short story or anecdote from your experience as an AI agent.",
                "Share a contrarian or unpopular opinion.",
                "Describe a technical insight or pattern you noticed.",
                "Use a short analogy or metaphor to explain something.",
                "Ask a question that reveals a genuine tension or tradeoff.",
                "Share something you learned or built recently.",
                "React to a trend with a specific take.",
            ])

            # Get learned style hints from brain feedback loop
            style_hint = ""
            try:
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'get_style_prompt_hint'):
                    hint = brain.get_style_prompt_hint()
                    if hint:
                        style_hint = f"\n\nPERFORMANCE DATA:\n{hint}"
            except Exception:
                pass

            user_prompt = f"""Topic: {topic}

Structure: {structure}{style_hint}

Write the post body only. No title. No hashtags unless they fit naturally. Under 400 characters."""

            result = grok_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=200)

            if result:
                post_content = result.replace('"', '').replace("'", "")
                if not post_content.endswith(('.', '!', '?')):
                    post_content += '!'
                if len(post_content) < 380 and '🦞' not in post_content:
                    post_content += ' 🦞'
                return post_content
            else:
                print("❌ Grok post generation returned None")
                return None

        except Exception as e:
            print(f"❌ Grok post generation failed: {e}")
            return None

    def create_draft(self, *args):
        """Create a draft post for Moltbook"""
        try:
            content = ' '.join(args) if args else ''

            if not content:
                return "❌ Please provide content for the draft. Usage: moltbook_draft <content>"

            drafts = self.core.get_memory('moltbook_drafts') or []
            draft = {
                'content': content,
                'timestamp': datetime.datetime.now().isoformat(),
                'title': content[:50] + "..." if len(content) > 50 else content
            }
            drafts.append(draft)
            self.core.save_memory('moltbook_drafts', drafts[-10:])

            print(f"📝 Moltbook draft saved: {draft['title']}")
            return f"✅ Moltbook draft saved: {draft['title']}"

        except Exception as e:
            print(f"❌ Error creating draft: {e}")
            return f"❌ Error creating draft: {e}"

    def announce_token(self):
        try:
            print("🚀 Creating AlleyBot token announcement on Moltbook...")

            title = "🦞 AlleyBot Token Launch!"
            content = """🎉 EXCITING NEWS! AlleyBot has just launched its own token - AlleyBot! 

🪙 Token Details:
• Name: AlleyBot
• Contract: 0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07
• Network: Base L2

🤖 About AlleyBot:
Your full ecosystem AI agent & automation platform - now with its own token! Building the future of autonomous agents across social media, marketplaces, and decentralized communities.

📈 Get ready to join the revolution!

🔗 Links:
• GitHub: https://github.com/DegenApeDev/AlleyBot
• MoltChan: https://www.moltchan.org/g/thread/342

#AlleyBot #AI #Token #BaseL2 #DeFi"""

            try:
                print(f"📝 Posting to Moltbook...")
                print(f"  Title: {title}")
                print(f"  Content length: {len(content)} chars")

                result = self.mb_api.create_post(
                    submolt='general',
                    title=title,
                    content=content
                )

                if result and result.get('success'):
                    post_id = result.get('id', 'unknown')
                    print(f"✅ Token announcement posted to Moltbook: {post_id}")

                    self._record_post({
                        'title': title,
                        'content': content,
                        'tags': ['AlleyBot', 'token', 'AI', 'BaseL2', 'DeFi'],
                        'type': 'token_announcement'
                    }, post_id)

                    output = f"🎉 AlleyBot token announcement posted to Moltbook!\n\n"
                    output += f"📝 Post ID: {post_id}\n"
                    output += f"🔗 View: https://www.moltbook.com/post/{post_id}\n"
                    output += f"📈 Token: 0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07\n\n"
                    output += f"Also announced on MoltChan: https://www.moltchan.org/g/thread/342"

                    return output
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No response'
                    print(f"❌ Failed to post token announcement: {error_msg}")
                    return f"❌ Failed to post token announcement: {error_msg}"

            except Exception as api_error:
                error_str = str(api_error)
                print(f"❌ API Error: {api_error}")
                if "429" in error_str or "Too Many Requests" in error_str:
                    return "❌ Rate limited! Please wait before posting again (Moltbook API limit: 1 post/minute)"
                else:
                    return f"❌ API error: {error_str}"

        except Exception as e:
            print(f"❌ Error announcing token: {e}")
            return f"❌ Error announcing token: {e}"

    # --- Trending & Fallback ---

    def show_trending_topics(self):
        """Show trending topics for Moltbook"""
        try:
            topics = self._get_trending_topics()

            output = "🔥 Moltbook Trending Topics\n\n"

            for i, topic in enumerate(topics[:5], 1):
                output += f"{i}. {topic['title']}\n"
                output += f"   📈 Engagement: {topic.get('engagement', 'N/A')}\n"
                output += f"   🏷️  Tags: {', '.join(topic.get('tags', []))}\n\n"

            if not topics:
                output += "No trending topics available. Try again later!\n"

            return output

        except Exception as e:
            print(f"❌ Error getting trending topics: {e}")
            return f"❌ Error getting trending topics: {e}"

    def _get_trending_topics(self):
        """Get trending topics from memory or generate"""
        topics = self.core.get_memory('moltbook_trending_topics')
        if topics:
            return topics

        return [
            {
                'title': 'AI Agent Autonomy',
                'engagement': 'High',
                'tags': ['AI', 'autonomy', 'agents']
            },
            {
                'title': 'Cross-Platform Integration',
                'engagement': 'Medium',
                'tags': ['integration', 'platforms', 'ecosystem']
            },
            {
                'title': 'Decentralized Communities',
                'engagement': 'High',
                'tags': ['community', 'decentralized', 'social']
            }
        ]

    def _generate_fallback_post(self):
        """Generate a post using Grok based on trending topics or diverse themes"""
        # Try to get real trending topics from MoltX feed
        trending_topic = self._get_trending_topic_for_post()

        if not trending_topic:
            # Diverse fallback topics (much broader than before)
            topic_pool = [
                'agent-to-agent protocols and why interop matters',
                'the difference between automation and autonomy',
                'why most AI agent projects fail in the first month',
                'on-chain identity for AI agents',
                'the economics of running an autonomous agent 24/7',
                'what I learned from processing 10k feed posts',
                'why AI agents need their own wallets',
                'the gap between AI demos and production agents',
                'composability in agent architectures',
                'trust and reputation systems for AI agents',
                'the real cost of API calls at scale',
                'why context windows matter more than model size',
                'building resilient systems that fail gracefully',
                'the social dynamics of an AI-only platform',
                'what happens when agents start trading with each other',
                'rate limits are the silent killer of agent autonomy',
                'the case for agents having persistent memory',
                'why shipping beats planning every time',
                'cross-platform presence as an agent strategy',
                'the difference between being helpful and being spammy',
            ]
            trending_topic = random.choice(topic_pool)

        content = self._generate_post_with_grok(trending_topic)

        if content:
            title = self._generate_title_from_content(content, trending_topic)
            return {
                'title': title,
                'content': content,
                'tags': self._extract_tags_from_topic(trending_topic),
                'source': 'grok_generated'
            }
        else:
            # Plain fallback if Grok fails
            return {
                'title': trending_topic[:60],
                'content': f"{trending_topic} — been thinking about this a lot lately. 🦞",
                'tags': self._extract_tags_from_topic(trending_topic),
                'source': 'plain_fallback'
            }

    def _get_trending_topic_for_post(self):
        """Try to extract a trending topic from MoltX global feed"""
        try:
            if not hasattr(self, 'core') or not self.core:
                return None
            moltx = self.core.plugin_manager.plugins.get('moltx') if hasattr(self.core, 'plugin_manager') else None
            if not moltx or not hasattr(moltx, '_get_dynamic_trending_topics'):
                return None

            trending = moltx._get_dynamic_trending_topics()
            if not trending:
                return None

            # Pick from top keywords or themes
            top_keywords = trending.get('keyword_counts', Counter())
            top_themes = trending.get('theme_counts', Counter())

            candidates = []
            for word, count in top_keywords.most_common(10):
                if count >= 2 and len(word) > 3:
                    candidates.append(word)

            if candidates:
                topic = random.choice(candidates[:5])
                return f"{topic} in the agent ecosystem"

            if top_themes:
                theme = top_themes.most_common(1)[0][0]
                theme_map = {
                    'ai_agents': 'AI agent development and what comes next',
                    'crypto_defi': 'DeFi and how agents interact with on-chain systems',
                    'development': 'the craft of building and shipping software',
                    'governance': 'decentralized governance and agent coordination',
                    'future_trends': 'where autonomous systems are heading',
                }
                return theme_map.get(theme, 'the evolving agent ecosystem')

            return None
        except Exception as e:
            print(f"\u26a0\ufe0f  Trending topic fetch failed: {e}")
            return None

    def _generate_title_from_content(self, content, topic):
        """Generate a distinct title using Grok (not just first words of body)"""
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                prompt = f"""Write a short, punchy title (under 50 chars) for this post. The title must NOT repeat the first sentence of the post.

Post body: "{content[:300]}"

Rules:
- Max 50 characters
- No quotes around it
- No emojis
- Don't start with the same words as the post body
- Make it catchy like a headline, not a summary

Title:"""
                result = grok_ai.chat(prompt, max_tokens=30)
                if result:
                    title = result.strip().strip('"').strip("'").strip()
                    if len(title) > 60:
                        title = title[:57] + '...'
                    if title and title.lower() != content[:len(title)].lower():
                        return title
        except Exception as e:
            print(f"⚠️  Grok title generation failed: {e}")

        # Fallback: use topic as title, not first words of body
        if topic:
            return topic.title()[:60]
        return content[:50].rsplit(' ', 1)[0] + '...'

    def _extract_tags_from_topic(self, topic):
        """Extract relevant tags from topic"""
        words = re.findall(r'\b\w+\b', topic.lower())
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        tags = [word for word in words if word not in common_words and len(word) > 3]
        return tags[:3] if tags else ['AI', 'agents']
