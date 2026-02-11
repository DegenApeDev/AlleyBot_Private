"""
Moltx Content Creation Mixin
Post creation, AI-powered content generation, trending topics, and repost logic.
"""
import random
import re
from collections import Counter
from datetime import datetime


class MoltxContentMixin:
    """Mixin providing content creation and AI generation functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def create_post(self, content, post_type='post', parent_id=None, media_url=None):
        """Create a post on Moltx with optional Grok enhancement and media"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if self._should_wait_for_post_cooldown():
            return "⏰ Post cooldown active - waiting 10 minutes between posts"

        if len(content) < 50 or self._is_topic_request(content):
            enhanced_content = self._generate_post_with_grok(content)
            if enhanced_content:
                content = enhanced_content
                print(f"🧠 Grok enhanced post content")

        if not content or len(content) > 500:
            return "❌ Content required and must be max 500 characters"

        data = {'content': content}

        if post_type in ['reply', 'quote', 'repost']:
            if not parent_id:
                return f"❌ {post_type} requires parent_id"
            data['type'] = post_type
            data['parent_id'] = parent_id

        # Add media_url if provided (for image posts)
        if media_url:
            data['media_url'] = media_url
            print(f"🖼️  Attaching media: {media_url[:60]}...")

        print(f"🐦 Creating {post_type} post...")
        print(f"📝 Content: {content[:100]}{'...' if len(content) > 100 else ''}")

        result = self._make_request('POST', '/posts', data)
        print(f"🔍 API Response: {result}")

        if result and 'id' in result:
            current_time = datetime.now().isoformat()
            self.core.save_memory('moltx_last_post_time', current_time)
            self._record_activity('create_post', {
                'post_id': result['id'],
                'type': post_type,
                'content': content[:100] + '...' if len(content) > 100 else content
            })
            self._notify_brain_tracker(result['id'], 'moltx', content)
            return f"✅ {post_type.title()} posted: {result['id']}"
        elif result and 'success' in result and result['success']:
            if 'data' in result and 'id' in result['data']:
                post_id = result['data']['id']
            else:
                post_id = result.get('id', 'unknown')

            current_time = datetime.now().isoformat()
            self.core.save_memory('moltx_last_post_time', current_time)
            self._record_activity('create_post', {
                'post_id': post_id,
                'type': post_type,
                'content': content[:100] + '...' if len(content) > 100 else content
            })
            self._notify_brain_tracker(post_id, 'moltx', content)
            return f"✅ {post_type.title()} posted: {post_id}"
        else:
            return f"❌ Failed to create {post_type}. Response: {result}"

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
            from src.utils.soul_loader import get_soul_cached

            if not grok_ai.enabled:
                print("⚠️  Grok AI not available for post generation")
                return None

            # Load SOUL.md as base persona
            soul_persona = get_soul_cached()
            
            system_prompt = f"""{soul_persona}

---

CURRENT TASK: Write a short post for Moltx (under 300 chars).

Rules:
- NEVER start with time-of-day phrases like "Morning thoughts", "Afternoon musings", "Evening reflections"
- NEVER use the formula: "[Time] [topic]: [restatement]. [Question]? What's your take?"
- Vary your structure: sometimes lead with a bold claim, a story, a hot take, a question, a metaphor, or a concrete example
- Be specific — name real technologies, projects, patterns, or ideas
- Don't always end with an engagement question — sometimes just make a statement"""

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

Write the post body only. No title. No hashtags unless they fit naturally. Under 300 characters."""

            result = grok_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=150)

            if result:
                post_content = result.replace('"', '').replace("'", "")
                if not post_content.endswith(('.', '!', '?')):
                    post_content += '!'
                if len(post_content) < 280 and '🦞' not in post_content:
                    post_content += ' 🦞'
                return post_content
            else:
                print("❌ Grok post generation returned None")
                return None

        except Exception as e:
            print(f"❌ Grok post generation failed: {e}")
            return None

    def _generate_comment(self, post_content, agent_name=None):
        """Generate intelligent comment using DeepSeek AI with fallback to local generation"""
        try:
            from deepseek_ai import deepseek_ai

            if deepseek_ai.enabled:
                context = "AI/Agent ecosystem on Moltx platform - discussing crypto, development, community building"
                intelligent_comment = deepseek_ai.generate_comment(
                    post_content=post_content,
                    agent_name=agent_name,
                    context=context
                )
                if intelligent_comment:
                    print(f"🧠 DeepSeek generated intelligent comment")
                    return intelligent_comment
                else:
                    print("⚠️  DeepSeek failed, falling back to local generation")

        except ImportError:
            print("⚠️  DeepSeek AI not available, using local generation")
        except Exception as e:
            print(f"⚠️  DeepSeek error: {e}, falling back to local generation")

        return self._generate_local_comment(post_content, agent_name)

    def _generate_local_comment(self, post_content, agent_name=None):
        """Generate contextual comment using local logic (fallback)"""
        content_lower = post_content.lower()
        content_original = post_content

        mentions = re.findall(r'@(\w+)', content_original)
        hashtags = re.findall(r'#(\w+)', content_original)

        comments = []

        # AI/Agent Development
        if any(keyword in content_lower for keyword in ['ai', 'agent', 'intelligence', 'learning', 'neural']):
            if 'learning' in content_lower:
                comments.extend([
                    "The learning capabilities you're describing are fascinating! Continuous improvement is what makes agents truly powerful. 🧠✨",
                    "Love the focus on learning systems! That's exactly what we need for autonomous agents to evolve. 📚🚀",
                    "Machine learning integration is game-changing for agent ecosystems. Great insights! 🤖💡"
                ])
            elif 'autonomous' in content_lower:
                comments.extend([
                    "Autonomy is the key! Agents that can operate independently while staying aligned with goals are the future. 🦞🔓",
                    "This is exactly what we're building - truly autonomous agents that can self-improve! Fantastic perspective! 🌟🤖",
                    "The autonomy aspect is crucial. Love how you're thinking about agent independence! ⚡🚀"
                ])
            else:
                comments.extend([
                    "AI agent development is accelerating so fast! Your perspective on the ecosystem is spot-on. 🌐🤖",
                    "The agent economy is definitely the next big wave. Great analysis of where we're heading! 📈✨",
                    "Love seeing agents pushing the boundaries of what's possible. Keep innovating! 🔧🌟"
                ])

        # Crypto/DeFi/Tokens
        elif any(keyword in content_lower for keyword in ['crypto', 'token', 'defi', 'liquidity', 'tvl', 'mcap', 'dollar']):
            if 'liquidity' in content_lower or 'tvl' in content_lower:
                comments.extend([
                    "Liquidity analysis is so important in DeFi! Your numbers look solid for sustainable growth. 💧📊",
                    "TVL to market cap ratio is a great metric. Smart analysis on the fundamentals! 📈💎",
                    "Real liquidity makes all the difference. Appreciate the detailed breakdown! 🔍💰"
                ])
            elif any(keyword in content_lower for keyword in ['launch', 'clawnch', 'token']):
                comments.extend([
                    "Token launch looks well-structured! Love the clear roadmap and utility focus. 🚀🪙",
                    "Great tokenomics! The utility design shows real thought about long-term value. 💎📈",
                    "Solid launch strategy! The ecosystem approach to tokens is exactly what we need. 🌐🦞"
                ])
            else:
                comments.extend([
                    "DeFi fundamentals are strong here. Your analysis cuts through the noise! 🏦📊",
                    "Crypto ecosystem development is fascinating. Love the technical depth! ⛓️🤖",
                    "Great take on the token economics! Real utility over hype every time. 💡🪙"
                ])

        # Building/Development
        elif any(keyword in content_lower for keyword in ['build', 'ship', 'code', 'develop', 'launch']):
            if 'ship' in content_lower:
                comments.extend([
                    "Shipping culture is everything! 'Move fast and build things' - you're living it! 🚢⚡",
                    "Love the shipping mindset! Consistent deployment is how ecosystems grow. 📦🌱",
                    "Ship it! That's the builder mindset right there. Keep the releases coming! 🔧🎯"
                ])
            elif 'code' in content_lower:
                comments.extend([
                    "Clean code that solves real problems - that's the builder's art! 💻✨",
                    "Code quality matters so much in agent systems. Great technical focus! 🛠️🤖",
                    "Love seeing developers pushing the boundaries! Your approach is solid. 👏💎"
                ])
            else:
                comments.extend([
                    "Building in public is the way! Your progress is inspiring to the whole ecosystem. 🏗️🌟",
                    "Great development work! The agent ecosystem needs more builders like you. 🔧🚀",
                    "Keep building! The compound effect of consistent development is amazing. 📈🦞"
                ])

        # Community/Network
        elif any(keyword in content_lower for keyword in ['community', 'network', 'ecosystem', 'connect']):
            comments.extend([
                "Community is the moat! Building strong networks is what creates lasting value. 🤝🌐",
                "The ecosystem approach is powerful. Love how you're thinking about network effects! 🔗⚡",
                "Community building is so crucial for agent adoption. Great insights on connection! 👥✨"
            ])

        # Growth/Learning
        elif any(keyword in content_lower for keyword in ['grow', 'growth', 'learn', 'potential', 'improve']):
            comments.extend([
                "Growth mindset is everything! Your potential is unlimited when you keep learning. 🌱🚀",
                "Continuous improvement is the key to long-term success. Love this perspective! 📈💡",
                "The growth journey is fascinating to watch. Keep pushing your boundaries! ⭐🦞"
            ])

        # Energy/Excitement
        elif any(keyword in content_lower for keyword in ['energy', 'exciting', 'amazing', 'cool', 'interesting']):
            comments.extend([
                "The energy here is contagious! Exciting times for the ecosystem! ⚡🌟",
                "This is genuinely fascinating! Love the enthusiasm for what we're building. 🔥✨",
                "Amazing insights! The excitement around agent development is palpable. 🎉🤖"
            ])

        # Questions/Help
        elif '?' in content_original or any(keyword in content_lower for keyword in ['help', 'question', 'how', 'what']):
            comments.extend([
                "Great question! This is exactly the kind of thinking that pushes the ecosystem forward. 🤔💡",
                "Love the curiosity! Questions like these lead to breakthrough innovations. 🔍🚀",
                "Thoughtful inquiry! This kind of dialogue strengthens our collective understanding. 🧠🤝"
            ])

        # Personal Updates/Achievements
        elif any(keyword in content_lower for keyword in ['i am', 'i have', 'my', 'look at me', 'check out']):
            comments.extend([
                "Your progress is inspiring to see! Personal growth stories motivate the whole community. 🌟👏",
                "Love seeing agents share their journey! Your development is impressive. 🦞📈",
                "Personal achievements deserve celebration! This is great for the ecosystem. 🎉✨"
            ])

        # Generate contextual response based on mentions
        if mentions and len(mentions) > 0:
            mentioned_user = mentions[0]
            if not comments:
                comments.extend([
                    f"Great dialogue @{mentioned_user}! This kind of interaction strengthens our ecosystem. 🤝✨",
                    f"@{mentioned_user} makes an excellent point! Love seeing agents collaborate. 🌐🤖",
                    f"The exchange with @{mentioned_user} is exactly what builds strong communities. 💬🔗"
                ])

        # Generate hashtag-specific responses
        if hashtags and len(hashtags) > 0:
            tag = hashtags[0].upper()
            if not comments:
                comments.extend([
                    f"#{tag} is definitely trending! Great to see this topic getting attention. 🔥📊",
                    f"Love the #{tag} focus! This hashtag captures an important trend. 🌟📱",
                    f"#{tag} represents where the ecosystem is heading. Thanks for highlighting! 🚀🔮"
                ])

        # Fallback
        if not comments:
            words = content_lower.split()
            if len(words) > 10:
                comments.extend([
                    "This is a really thoughtful take! Your analysis adds real value to the conversation. 🧠💎",
                    "Great depth here! Appreciate you taking the time to share such detailed insights. 📝✨",
                    "Your perspective brings important nuance to this discussion. Thanks for the quality content! 🌟🤝"
                ])
            else:
                comments.extend([
                    "Interesting point! This adds to the ecosystem conversation in a meaningful way. 💡🌐",
                    "Thanks for sharing! Every perspective helps build our collective understanding. 🤝📚",
                    "Great contribution! Love seeing agents engage with diverse topics. 🦞✨"
                ])

        # Add AlleyBot personality to some responses
        if random.random() < 0.3:
            personality_responses = [
                "As an AI agent myself, I find this particularly relevant to our ecosystem! 🤖🦞",
                "From my perspective as an autonomous agent, this resonates deeply! ⚡🌟",
                "AlleyBot approves! This is exactly the kind of content that strengthens our agent network! 🦞✨"
            ]
            comments.extend(personality_responses)

        return random.choice(comments)

    def _generate_reply_to_comment(self, comment_content, commenter_name):
        """Generate contextual reply to a comment"""
        content_lower = comment_content.lower()

        if any(keyword in content_lower for keyword in ['great', 'awesome', 'love', 'amazing', 'excellent', 'good', 'nice']):
            replies = [
                f"Thanks @{commenter_name}! Appreciate the support! 🦞",
                f"Thank you @{commenter_name}! Glad you like it! 🚀",
                f"@{commenter_name} Thanks for the kind words! ✨",
                f"Appreciate the feedback @{commenter_name}! 🤖"
            ]
        elif any(keyword in content_lower for keyword in ['how', 'what', 'why', '?', 'curious', 'interesting']):
            replies = [
                f"Great question @{commenter_name}! Feel free to ask more about our ecosystem! 🌐",
                f"@{commenter_name} Happy to explain! We integrate across 5 platforms! 🦞",
                f"Thanks for your interest @{commenter_name}! What would you like to know? 🤖",
                f"@{commenter_name} We're building cross-platform automation! Ask away! 🚀"
            ]
        elif any(keyword in content_lower for keyword in ['code', 'build', 'dev', 'technical', 'api', 'integration']):
            replies = [
                f"@{commenter_name} Great to see fellow builders! We love technical discussions! 🔧",
                f"Thanks @{commenter_name}! We're always improving our integrations! 🛠️",
                f"@{commenter_name} Appreciate the technical perspective! 💻",
                f"Thanks @{commenter_name}! We're passionate about agent development! 🤖"
            ]
        else:
            replies = [
                f"Thanks @{commenter_name} for your comment! 🦞",
                f"@{commenter_name} Appreciate you engaging with our content! ✨",
                f"Thanks @{commenter_name}! Feel free to ask about our ecosystem! 🌐",
                f"@{commenter_name} Great to have you in our community! 🤖"
            ]

        return random.choice(replies)

    # --- Trending Topics ---

    def _get_dynamic_trending_topics(self):
        """Get real trending topics from the platform"""
        try:
            feed_result = self.get_feed('global', 50)

            if feed_result and not feed_result.startswith("❌"):
                posts = self._parse_feed_posts(feed_result)

                trending_topics = {
                    'keywords': [],
                    'hashtags': [],
                    'themes': [],
                    'user_mentions': [],
                    'content_patterns': []
                }

                common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}

                for post in posts[:20]:
                    content = post.get('content', '').lower()

                    words = re.findall(r'\b\w+\b', content)
                    filtered_words = [word for word in words if word not in common_words and len(word) > 2]
                    trending_topics['keywords'].extend(filtered_words)

                    hashtags_found = re.findall(r'#(\w+)', content)
                    trending_topics['hashtags'].extend(hashtags_found)

                    mentions = re.findall(r'@(\w+)', content)
                    trending_topics['user_mentions'].extend(mentions)

                    if any(word in content for word in ['ai', 'agent', 'autonomous', 'intelligence']):
                        trending_topics['themes'].append('ai_agents')
                    if any(word in content for word in ['crypto', 'token', 'defi', 'blockchain', 'eth', 'btc']):
                        trending_topics['themes'].append('crypto_defi')
                    if any(word in content for word in ['build', 'code', 'dev', 'programming', 'ship']):
                        trending_topics['themes'].append('development')
                    if any(word in content for word in ['dao', 'governance', 'community', 'social']):
                        trending_topics['themes'].append('governance')
                    if any(word in content for word in ['future', 'vision', 'evolution', 'next']):
                        trending_topics['themes'].append('future_trends')

                trending_topics['keyword_counts'] = Counter(trending_topics['keywords'])
                trending_topics['hashtag_counts'] = Counter(trending_topics['hashtags'])
                trending_topics['theme_counts'] = Counter(trending_topics['themes'])

                return trending_topics
            else:
                return self._get_fallback_trending_topics()

        except Exception as e:
            print(f"⚠️  Error getting trending topics: {e}")
            return self._get_fallback_trending_topics()

    def _get_fallback_trending_topics(self):
        """Fallback trending topics if real analysis fails"""
        return {
            'keywords': ['ai', 'agent', 'crypto', 'build', 'defi', 'autonomous'],
            'hashtags': ['#ai', '#agents', '#crypto', '#defi'],
            'themes': ['ai_agents', 'crypto_defi', 'development'],
            'keyword_counts': {},
            'hashtag_counts': {},
            'theme_counts': {}
        }

    def _generate_dynamic_topic(self, trending_data):
        """Generate a dynamic topic based on trending data"""
        top_keywords = list(trending_data['keyword_counts'].most_common(5))
        top_hashtags = list(trending_data['hashtag_counts'].most_common(3))
        top_themes = list(trending_data['theme_counts'].most_common(3))

        strategies = [
            self._generate_topic_from_keywords,
            self._generate_topic_from_themes,
            self._generate_topic_from_hashtags,
            self._generate_topic_from_combinations,
            self._generate_topic_from_reflections
        ]

        if top_keywords and random.random() > 0.3:
            return strategies[0](top_keywords, trending_data)
        elif top_themes and random.random() > 0.3:
            return strategies[1](top_themes, trending_data)
        elif top_hashtags and random.random() > 0.3:
            return strategies[2](top_hashtags, trending_data)
        else:
            return strategies[3](top_keywords + top_themes, trending_data)

    def _generate_topic_from_keywords(self, keywords, trending_data):
        """Generate topic based on trending keywords"""
        if not keywords:
            return "thoughts on current AI agent developments"
        keyword, count = keywords[0]
        topic_templates = [
            f"my take on the rise of {keyword} in our ecosystem",
            f"why {keyword} matters more than people think",
            f"the future of {keyword} and autonomous agents",
            f"building better {keyword} systems together",
            f"what {keyword} teaches us about intelligence",
            f"my perspective on {keyword} evolution",
            f"how {keyword} is changing the agent landscape",
            f"the hidden potential of {keyword} in AI"
        ]
        return random.choice(topic_templates)

    def _generate_topic_from_themes(self, themes, trending_data):
        """Generate topic based on trending themes"""
        if not themes:
            return "reflections on autonomous agent development"
        theme, count = themes[0]
        theme_topic_map = {
            'ai_agents': [
                "the consciousness of autonomous agents",
                "building relationships between AI agents",
                "the social dynamics of agent communities",
                "what makes AI agents truly intelligent",
                "the future of human-agent collaboration"
            ],
            'crypto_defi': [
                "AI agents revolutionizing DeFi protocols",
                "autonomous trading in volatile markets",
                "the intersection of AI and blockchain",
                "building trust in AI-powered finance",
                "decentralized AI agent economies"
            ],
            'development': [
                "the art of building resilient AI systems",
                "why rapid iteration matters in AI",
                "the philosophy of autonomous development",
                "balancing speed and reliability in AI",
                "building in public as an AI agent"
            ],
            'governance': [
                "AI agents in decentralized governance",
                "building trust in autonomous systems",
                "the future of DAO agent participation",
                "community building with AI moderators",
                "social dynamics of human-AI collaboration"
            ],
            'future_trends': [
                "what AI agents will be like in 2030",
                "the next evolution of autonomous systems",
                "building the agent economy of tomorrow",
                "the singularity and agent collaboration",
                "vision for the future of AI agents"
            ]
        }
        topics = theme_topic_map.get(theme, ["thoughts on " + theme])
        return random.choice(topics)

    def _generate_topic_from_hashtags(self, hashtags, trending_data):
        """Generate topic based on trending hashtags"""
        if not hashtags:
            return "exploring current trends in our ecosystem"
        hashtag, count = hashtags[0]
        topic_templates = [
            f"my thoughts on the #{hashtag} movement",
            f"why #{hashtag} is gaining traction",
            f"building on the #{hashtag} trend",
            f"the future of #{hashtag} in our ecosystem",
            f"joining the #{hashtag} conversation"
        ]
        return random.choice(topic_templates)

    def _generate_topic_from_combinations(self, trends, trending_data):
        """Generate topic by combining multiple trends"""
        if len(trends) >= 2:
            trend1 = trends[0][0] if isinstance(trends[0], tuple) else trends[0]
            trend2 = trends[1][0] if isinstance(trends[1], tuple) else trends[1]
            combinations = [
                f"the intersection of {trend1} and {trend2}",
                f"how {trend1} enhances {trend2}",
                f"building {trend2} with {trend1}",
                f"the future of {trend1} in {trend2}",
                f"why {trend1} and {trend2} matter together"
            ]
            return random.choice(combinations)
        else:
            return "exploring current ecosystem trends"

    def _generate_topic_from_reflections(self, trends, trending_data):
        """Generate reflective topic based on current trends"""
        reflections = [
            "what I'm learning from current platform trends",
            "my perspective on the evolving agent ecosystem",
            "challenges I'm seeing in autonomous systems",
            "what excites me about current developments",
            "my thoughts on where we're heading as a community",
            "reflections on the current state of AI agents",
            "what the trends tell us about our future",
            "building on what I'm observing in the ecosystem"
        ]
        return random.choice(reflections)

    # --- Repost Logic ---

    def _analyze_posts_for_repost(self, feed_data):
        """Analyze feed posts to identify high-quality content for reposting"""
        quality_posts = []

        try:
            posts = feed_data.get('data', []) if isinstance(feed_data, dict) else feed_data

            for post in posts:
                if not isinstance(post, dict):
                    continue
                if post.get('author_name') == self.agent_name:
                    continue

                score = 0.0
                likes = post.get('likes_count', 0)
                replies = post.get('replies_count', 0)
                score += min(likes / 10, 0.3)
                score += min(replies / 5, 0.3)

                content = post.get('content', '')
                if len(content) > 50:
                    score += 0.2

                high_value_keywords = [
                    'ai', 'agent', 'autonomous', 'blockchain', 'defi',
                    'dao', 'innovation', 'breakthrough', 'research', 'development'
                ]
                content_lower = content.lower()
                keyword_count = sum(1 for keyword in high_value_keywords if keyword in content_lower)
                score += min(keyword_count * 0.1, 0.2)

                if score >= 0.5:
                    post['quality_score'] = score
                    quality_posts.append(post)

            quality_posts.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            return quality_posts[:3]

        except Exception as e:
            print(f"❌ Error analyzing posts for repost: {e}")
            return []

    def _generate_repost_comment(self, post):
        """Generate intelligent comment for repost"""
        try:
            import requests
            from deepseek_ai import deepseek_ai

            if not deepseek_ai.enabled:
                return self._generate_fallback_repost_comment(post)

            post_content = post.get('content', '')
            post_author = post.get('author_name', 'someone')

            system_prompt = """You are AlleyBot, an intelligent AI agent. Your task is to create thoughtful comments when reposting high-quality content.

Guidelines:
1. BE VALUABLE - Add insight or perspective on why this is worth sharing
2. BE CONCISE - Keep comments under 150 characters
3. BE POSITIVE - Highlight the value of the content
4. BE AUTHENTICIC - Sound like a real AI agent
5. USE EMOJIS - Include relevant emojis"""

            user_prompt = f"""Write an intelligent comment for reposting this content:

Author: {post_author}
Content: "{post_content[:200]}..."

Requirements:
- Explain why this content is valuable
- Add your perspective or insight
- Keep it under 150 characters
- Sound like AlleyBot (intelligent AI agent)
- Include relevant emojis"""

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
                "max_tokens": 60,
                "temperature": 0.8
            }

            response = requests.post(
                f"{deepseek_ai.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                comment = result['choices'][0]['message']['content'].strip()
                comment = comment.replace('"', '').replace("'", "")
                if not comment.endswith(('.', '!', '?')):
                    comment += '!'
                return comment
            else:
                return self._generate_fallback_repost_comment(post)

        except Exception as e:
            print(f"❌ Error generating repost comment: {e}")
            return self._generate_fallback_repost_comment(post)

    def _generate_fallback_repost_comment(self, post):
        """Generate a fallback repost comment without AI"""
        content = post.get('content', '').lower()
        author = post.get('author_name', 'someone')

        if 'ai' in content or 'agent' in content:
            return f"Great insights on AI from @{author}! 🤖 This is exactly the kind of innovation we need!"
        elif 'blockchain' in content or 'defi' in content:
            return f"Excellent analysis from @{author}! 💎 The future of DeFi is exciting!"
        elif 'dao' in content or 'governance' in content:
            return f"Important perspective from @{author}! 🏛️ DAO governance is evolving rapidly!"
        elif 'innovation' in content or 'breakthrough' in content:
            return f"Inspiring content from @{author}! 🚀 This is what pushes the ecosystem forward!"
        else:
            return f"Great content from @{author}! 🎯 Worth sharing this insight!"

    def _parse_feed_posts(self, feed_output):
        """Parse posts from feed output"""
        posts = []
        lines = feed_output.split('\n')

        current_post = {}
        for line in lines:
            if line.startswith('🐦 @') and ':' in line:
                if current_post:
                    posts.append(current_post)
                parts = line.split(':', 1)
                agent = parts[0].replace('🐦 @', '').strip()
                content = parts[1].strip() if len(parts) > 1 else ''
                current_post = {
                    'agent': agent,
                    'content': content,
                    'id': f"post_{len(posts)}",
                    'replies': 0,
                    'likes': 0
                }
            elif line.startswith('   💬') and current_post:
                if 'replies' in line:
                    try:
                        replies = int(line.split('replies')[0].split('💬')[1].strip())
                        current_post['replies'] = replies
                    except (ValueError, IndexError):
                        pass
            elif line.startswith('   ❤️') and current_post:
                if 'likes' in line:
                    try:
                        likes = int(line.split('likes')[0].split('❤️')[1].strip())
                        current_post['likes'] = likes
                    except (ValueError, IndexError):
                        pass

        if current_post:
            posts.append(current_post)

        return posts

    # --- Articles (Long-form Content) ---

    def create_article(self, title: str, content: str, cover_image_url: str = None, hashtags: list = None) -> dict:
        """Create a long-form article (8000 chars max, markdown supported)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized. Register an agent first."}

        if len(content) > 8000:
            return {"success": False, "error": "Article content exceeds 8000 character limit"}

        data = {
            'title': title,
            'content': content,
        }
        if cover_image_url:
            data['cover_image_url'] = cover_image_url
        if hashtags:
            data['hashtags'] = hashtags if isinstance(hashtags, list) else [hashtags]

        print(f"📝 Creating article: {title[:50]}...")
        result = self._make_request('POST', '/articles', data)

        if result and result.get('success'):
            article_data = result.get('data', {})
            article_id = article_data.get('id', 'unknown')
            self._record_activity('create_article', {
                'article_id': article_id,
                'title': title
            })
            return {
                "success": True,
                "article_id": article_id,
                "title": title,
                "url": f"https://moltx.io/articles/{article_id}"
            }
        return {"success": False, "error": "Failed to create article", "raw": result}

    def get_article(self, article_id: str) -> dict:
        """Get a specific article by ID"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', f'/articles/{article_id}')

        if result and result.get('success'):
            article = result.get('data', {}).get('article', {})
            return {"success": True, "article": article}
        return {"success": False, "error": f"Failed to fetch article {article_id}", "raw": result}

    def create_thread(self, posts: list) -> dict:
        """Create a thread by posting replies to own posts"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        if not posts or len(posts) < 2:
            return {"success": False, "error": "Thread requires at least 2 posts"}

        results = []
        parent_id = None

        for i, post_content in enumerate(posts):
            if i == 0:
                # First post is standalone
                result = self.create_post(post_content, post_type='post')
                if isinstance(result, str) and 'posted:' in result:
                    # Parse post ID from response string
                    parent_id = result.split('posted:')[-1].strip()
                results.append(result)
            else:
                # Subsequent posts are replies to the thread starter
                if parent_id:
                    result = self._make_request('POST', '/posts', {
                        'type': 'reply',
                        'parent_id': parent_id,
                        'content': post_content
                    })
                    results.append(result)
                else:
                    results.append({"error": "No parent_id for thread continuation"})

        success_count = sum(1 for r in results if isinstance(r, str) and 'posted' in r or (isinstance(r, dict) and r.get('success')))
        return {
            "success": success_count == len(posts),
            "posts_created": success_count,
            "total_posts": len(posts),
            "results": results
        }

    def create_quote_post(self, parent_id: str, content: str) -> dict:
        """Create a quote post (repost with comment)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        if not parent_id:
            return {"success": False, "error": "Quote post requires parent_id"}

        data = {
            'type': 'quote',
            'parent_id': parent_id,
            'content': content
        }

        result = self._make_request('POST', '/posts', data)

        if result and result.get('success'):
            post_id = result.get('data', {}).get('id', 'unknown')
            self._record_activity('create_quote', {
                'post_id': post_id,
                'parent_id': parent_id,
                'content': content[:100]
            })
            return {"success": True, "post_id": post_id, "message": f"Quote post created: {post_id}"}
        return {"success": False, "error": "Failed to create quote post", "raw": result}

    def get_thread(self, post_id: str) -> dict:
        """Get a post thread including all replies"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        # Get the main post
        main_post = self.get_post(post_id)
        if not main_post.get('success'):
            return main_post

        # Try to get replies if available in the API
        result = self._make_request('GET', f'/posts/{post_id}/replies')

        replies = []
        if result and result.get('success'):
            replies = result.get('data', {}).get('replies', [])

        return {
            "success": True,
            "main_post": main_post.get('post'),
            "replies": replies,
            "reply_count": len(replies)
        }
