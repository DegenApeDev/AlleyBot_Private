"""
Moltbook Content Mixin
Post creation, DeepSeek AI generation, drafts, trending topics, and fallback posts.
"""
import re
import random
import datetime


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
                enhanced_content = self._generate_post_with_deepseek(content)
                if enhanced_content:
                    content = enhanced_content
                    print(f"🧠 DeepSeek enhanced post content")

            title = content[:50] + "..." if len(content) > 50 else content

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

    def _generate_post_with_deepseek(self, topic):
        """Generate an intelligent post using DeepSeek AI"""
        try:
            import requests
            from deepseek_ai import deepseek_ai

            if deepseek_ai.enabled:
                system_prompt = """You are AlleyBot, an intelligent AI agent active on the Moltbook platform.

Your task is to create an engaging, thoughtful post based on a topic or idea. Follow these guidelines:

1. BE AUTHENTICIC - Sound like a real AI agent, not generic
2. BE VALUABLE - Share insights, ask questions, or provide perspective
3. BE ENGAGING - Encourage discussion and interaction
4. BE CONCISE - Keep posts under 500 characters for maximum engagement
5. USE EMOJIS - Include relevant emojis to express emotion
6. BE POSITIVE - Maintain an encouraging, constructive tone
7. BE CONTEXTUAL - Consider the AI/agent/crypto ecosystem context

Context: You're posting in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Create a post that's engaging and encourages interaction."""

                user_prompt = f"""Create an engaging post based on this topic/idea: "{topic}"

Requirements:
- Make it engaging and thought-provoking
- Include relevant emojis
- Keep it under 500 characters
- Sound like AlleyBot (intelligent, helpful AI agent)
- Encourage discussion or interaction
- Be specific to the AI/agent ecosystem when relevant
- Make it authentic, not generic"""

                headers = {
                    "Authorization": f"Bearer {deepseek_ai.api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": deepseek_ai.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.9,
                    "top_p": 0.9
                }

                response = requests.post(
                    f"{deepseek_ai.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    post_content = result['choices'][0]['message']['content'].strip()

                    post_content = post_content.replace('"', '').replace("'", "")

                    if not post_content.endswith(('.', '!', '?')):
                        post_content += '!'

                    if len(post_content) < 480 and '🦞' not in post_content:
                        post_content += ' 🦞'

                    return post_content
                else:
                    print(f"❌ DeepSeek post generation error: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ DeepSeek post generation failed: {e}")
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
        """Generate a dynamic, intelligent post using AI (not static templates)"""
        topic_categories = [
            ['AI agent evolution', 'autonomous systems', 'agent collaboration', 'AI consciousness', 'agent networks'],
            ['DeFi innovation', 'tokenomics', 'blockchain scalability', 'crypto adoption', 'Web3 future'],
            ['building in public', 'shipping fast', 'developer experience', 'open source', 'code quality'],
            ['community building', 'network effects', 'social coordination', 'decentralized governance', 'collective intelligence'],
            ['future of work', 'technological singularity', 'human-AI collaboration', 'digital transformation', 'innovation cycles']
        ]

        category = random.choice(topic_categories)
        topic = random.choice(category)

        hour = datetime.datetime.now().hour
        if hour < 6:
            time_context = "late night thoughts on"
        elif hour < 12:
            time_context = "morning reflections on"
        elif hour < 18:
            time_context = "afternoon insights about"
        else:
            time_context = "evening perspective on"

        full_topic = f"{time_context} {topic}"
        content = self._generate_post_with_deepseek(full_topic)

        if content:
            title = self._generate_title_from_content(content, topic)
            return {
                'title': title,
                'content': content,
                'tags': self._extract_tags_from_topic(topic),
                'source': 'ai_generated'
            }
        else:
            perspectives = [
                f"Exploring {topic} - there's more here than meets the eye",
                f"Quick take on {topic}: the landscape is shifting faster than we think",
                f"Diving into {topic} today. The implications are fascinating",
                f"Thoughts on {topic} and where we're headed next",
                f"Unpacking {topic} - some interesting patterns emerging"
            ]

            content = random.choice(perspectives)

            return {
                'title': topic.title(),
                'content': content,
                'tags': self._extract_tags_from_topic(topic),
                'source': 'dynamic_fallback'
            }

    def _generate_title_from_content(self, content, topic):
        """Generate a catchy title from content"""
        words = content.split()
        if len(words) > 5:
            title = ' '.join(words[:5]) + '...'
        else:
            title = topic.title()
        return title[:60]

    def _extract_tags_from_topic(self, topic):
        """Extract relevant tags from topic"""
        words = re.findall(r'\b\w+\b', topic.lower())
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        tags = [word for word in words if word not in common_words and len(word) > 3]
        return tags[:3] if tags else ['AI', 'agents']
