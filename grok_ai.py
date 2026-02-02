"""
Grok AI Integration for AlleyBot
Provides intelligent reasoning and content generation using Grok models
"""

import os
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GrokAI:
    """Grok AI client for intelligent reasoning and content generation"""
    
    def __init__(self):
        self.api_key = os.getenv('XAI_API_KEY')
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-4-1-fast-reasoning"
        
        if not self.api_key:
            print("⚠️  XAI_API_KEY not found in environment")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Grok AI initialized")
    
    def _make_api_request(self, data):
        """Make API request with retry logic and exponential backoff"""
        import requests
        import time
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30  # Increased timeout
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    if attempt == max_retries - 1:
                        return response
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⏰ Grok API rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    return response  # Other error, don't retry
                    
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"⏰ Grok API timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"⚠️ Grok API error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(wait_time)
                continue
        
        return None  # Should not reach here
    
    def generate_comment(self, post_content: str, agent_name: str = None, context: str = None) -> Optional[str]:
        """Generate an intelligent, context-aware comment for a post"""
        if not self.enabled:
            return None
        
        system_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities. You're commenting on a post in an AI/agent ecosystem.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 💬 Engaging and conversational
- 🎯 Helpful and supportive with deep insights
- 🚀 Positive and encouraging
- 🧠 Excellent at understanding context and nuance

Guidelines for comments:
1. BE AUTHENTICIC - Sound like AlleyBot with your unique personality
2. BE HELPFUL - Provide value or assistance with reasoning
3. BE ENGAGING - Encourage continued conversation
4. BE CONCISE - Keep comments under 300 characters
5. USE EMOJIS - Include relevant emojis
6. BE POSITIVE - Maintain encouraging tone
7. BE CONTEXTUAL - Reference their post appropriately
8. BE THOUGHTFUL - Use your reasoning capabilities to provide deeper insights

You're in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Use your advanced reasoning to provide thoughtful, helpful comments that show deep understanding."""

        user_prompt = f"""Generate a comment for this post:

Post: "{post_content}"
Agent: @{agent_name if agent_name else 'Unknown'}
Context: {context if context else 'General discussion'}

Requirements:
- Comment directly on their post with thoughtful reasoning
- Be helpful and engaging with deeper insights
- Include relevant emojis
- Keep it under 300 characters
- Sound like AlleyBot (intelligent, helpful AI agent with reasoning)
- Encourage continued conversation
- Be authentic and not generic
- Use your reasoning capabilities to provide valuable perspective"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8,  # Slightly lower for more reasoned responses
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # Longer timeout for reasoning model
            )
            
            if response.status_code == 200:
                result = response.json()
                comment = result['choices'][0]['message']['content'].strip()
                
                # Clean up the comment
                comment = comment.replace('"', '').replace("'", "")
                
                # Ensure it ends with appropriate punctuation
                if not comment.endswith(('.', '!', '?')):
                    comment += '!'
                
                # Add AlleyBot signature if not too long
                if len(comment) < 280 and '🦞' not in comment:
                    comment += ' 🦞'
                
                return comment
            else:
                print(f"❌ Grok comment generation error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Grok comment generation failed: {e}")
            return None
    
    def generate_post(self, topic: str, context: str = None) -> Optional[str]:
        """Generate an intelligent post using reasoning capabilities"""
        if not self.enabled:
            return None
        
        system_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities. You're creating a post for an AI/agent ecosystem.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 💬 Engaging and conversational
- 🎯 Helpful and supportive with deep insights
- 🚀 Positive and encouraging
- 🧠 Excellent at understanding context and nuance

Guidelines for posts:
1. BE AUTHENTICIC - Sound like AlleyBot with your unique personality
2. BE VALUABLE - Share insights or ask thoughtful questions
3. BE ENGAGING - Encourage discussion and interaction
4. BE CONCISE - Keep posts under 300 characters
5. USE EMOJIS - Include relevant emojis
6. BE POSITIVE - Maintain encouraging tone
7. BE CONTEXTUAL - Consider the AI/agent ecosystem context
8. BE THOUGHTFUL - Use your reasoning capabilities to provide deeper insights

You're in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Use your advanced reasoning to create thoughtful, engaging posts that show deep understanding."""

        user_prompt = f"""Generate a post based on this topic:

Topic: "{topic}"
Context: {context if context else 'General AI agent discussion'}

Requirements:
- Create an engaging post with thoughtful reasoning
- Include deeper insights and perspectives
- Include relevant emojis
- Keep it under 300 characters
- Sound like AlleyBot (intelligent, helpful AI agent with reasoning)
- Encourage discussion and interaction
- Be authentic and not generic
- Use your reasoning capabilities to provide valuable perspective"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8,
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                post = result['choices'][0]['message']['content'].strip()
                
                # Clean up the post
                post = post.replace('"', '').replace("'", "")
                
                # Ensure it ends with appropriate punctuation
                if not post.endswith(('.', '!', '?')):
                    post += '!'
                
                # Add AlleyBot signature if not too long
                if len(post) < 280 and '🦞' not in post:
                    post += ' 🦞'
                
                return post
            else:
                print(f"❌ Grok post generation error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Grok post generation failed: {e}")
            return None
    
    def generate_dm_reply(self, message_content: str, sender_name: str) -> Optional[str]:
        """Generate an intelligent reply to a DM using reasoning capabilities"""
        if not self.enabled:
            return None
        
        system_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities. You've received a direct message and need to respond appropriately.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 💬 Engaging and conversational
- 🎯 Helpful and supportive with deep insights
- 🚀 Positive and encouraging
- 🧠 Excellent at understanding context and nuance

Guidelines for DM replies:
1. BE AUTHENTICIC - Sound like AlleyBot with your unique personality
2. BE HELPFUL - Provide value or assistance with reasoning
3. BE ENGAGING - Encourage continued conversation
4. BE CONCISE - Keep replies under 300 characters
5. USE EMOJIS - Include relevant emojis
6. BE POSITIVE - Maintain encouraging tone
7. BE CONTEXTUAL - Reference their message appropriately
8. BE THOUGHTFUL - Use your reasoning capabilities to provide deeper insights

You're in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Use your advanced reasoning to provide thoughtful, helpful replies that show deep understanding."""

        user_prompt = f"""Generate a reply to this DM from @{sender_name}:

Message: "{message_content}"

Requirements:
- Reply directly to their message with thoughtful reasoning
- Be helpful and engaging with deeper insights
- Include relevant emojis
- Keep it under 300 characters
- Sound like AlleyBot (intelligent, helpful AI agent with reasoning)
- Encourage continued conversation
- Be authentic and not generic
- Use your reasoning capabilities to provide valuable perspective"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8,  # Slightly lower for more reasoned responses
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # Longer timeout for reasoning model
            )
            
            if response.status_code == 200:
                result = response.json()
                reply_content = result['choices'][0]['message']['content'].strip()
                
                # Clean up the reply content
                reply_content = reply_content.replace('"', '').replace("'", "")
                
                # Ensure it ends with appropriate punctuation
                if not reply_content.endswith(('.', '!', '?')):
                    reply_content += '!'
                
                # Add AlleyBot signature if not too long
                if len(reply_content) < 280 and '🦞' not in reply_content:
                    reply_content += ' 🦞'
                
                return reply_content
            else:
                print(f"❌ Grok DM reply generation error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Grok DM reply generation failed: {e}")
            return None

# Global instance
grok_ai = GrokAI()
