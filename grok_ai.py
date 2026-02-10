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
        
        # Convert messages format to input format for Grok API
        if 'messages' in data:
            converted = {
                'input': data['messages'],
                'model': data.get('model', self.model)
            }
            # Copy other params if present
            if 'max_tokens' in data:
                converted['max_tokens'] = data['max_tokens']
            if 'temperature' in data:
                converted['temperature'] = data['temperature']
            if 'top_p' in data:
                converted['top_p'] = data['top_p']
            data = converted
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/responses",  # Correct Grok endpoint
                    headers=headers,
                    json=data,
                    timeout=60  # Increased timeout for reasoning model
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
    
    def _extract_text(self, response) -> Optional[str]:
        """Extract text content from Grok /responses API response"""
        if response is None or response.status_code != 200:
            status = response.status_code if response else 'None'
            print(f"❌ Grok API error: status {status}")
            if response is not None:
                print(f"   Response: {response.text[:200]}")
            return None
        
        try:
            result = response.json()
            
            # Grok /responses format: output_text field
            if 'output_text' in result:
                return result['output_text'].strip()
            
            # Fallback: check output array for message content
            if 'output' in result:
                for item in result['output']:
                    if item.get('type') == 'message' and 'content' in item:
                        for content_block in item['content']:
                            if content_block.get('type') == 'output_text':
                                return content_block.get('text', '').strip()
                            if 'text' in content_block:
                                return content_block['text'].strip()
            
            # Legacy fallback: OpenAI chat completions format
            if 'choices' in result:
                return result['choices'][0]['message']['content'].strip()
            
            print(f"⚠️  Grok: unexpected response format, keys: {list(result.keys())}")
            return None
            
        except Exception as e:
            print(f"❌ Grok response parsing failed: {e}")
            return None
    
    def _clean_output(self, text: str, max_len: int = 300) -> str:
        """Clean and format generated text"""
        text = text.replace('"', '').replace("'", "")
        
        # Ensure it ends with appropriate punctuation
        if not text.endswith(('.', '!', '?')):
            text += '!'
        
        # Add AlleyBot signature if not too long
        if len(text) < (max_len - 20) and '🦞' not in text:
            text += ' 🦞'
        
        return text
    
    def chat(self, prompt: str, system_prompt: str = None, max_tokens: int = 500) -> Optional[str]:
        """General-purpose chat method for simple prompts"""
        if not self.enabled:
            return None
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            response = self._make_api_request(data)
            return self._extract_text(response)
        except Exception as e:
            print(f"❌ Grok chat failed: {e}")
            return None

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
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.8,
                "top_p": 0.9
            }
            
            response = self._make_api_request(data)
            text = self._extract_text(response)
            
            if text:
                return self._clean_output(text)
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
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.8,
                "top_p": 0.9
            }
            
            response = self._make_api_request(data)
            text = self._extract_text(response)
            
            if text:
                return self._clean_output(text)
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
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.8,
                "top_p": 0.9
            }
            
            response = self._make_api_request(data)
            text = self._extract_text(response)
            
            if text:
                return self._clean_output(text)
            return None
                
        except Exception as e:
            print(f"❌ Grok DM reply generation failed: {e}")
            return None

    def generate_image(self, prompt: str, model: str = "grok-imagine-image") -> Optional[Dict]:
        """Generate an image using Grok's image model
        
        Args:
            prompt: Text description of the image to generate
            model: Image model to use (default "grok-imagine-image")
        
        Returns:
            Dict with 'image_url', 'moderation_passed', 'model'
            Cost: ~$0.02 per image (2 cents)
        """
        if not self.enabled:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Use simpler API call matching x.ai SDK pattern
            data = {
                "model": model,
                "prompt": prompt,
            }
            
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if we got valid image data
                if 'data' in result and len(result['data']) > 0:
                    image_data = result['data'][0]
                    
                    output = {
                        'moderation_passed': image_data.get('respect_moderation', True),
                        'model': result.get('model', 'grok-imagine-image'),
                    }
                    
                    # Return URL directly (simpler, matches SDK example)
                    if 'url' in image_data:
                        output['image_url'] = image_data['url']
                        output['image_data'] = image_data['url']  # Backward compat
                        output['format'] = 'url'
                    elif 'b64_json' in image_data:
                        import base64
                        output['image_data'] = base64.b64decode(image_data['b64_json'])
                        output['format'] = 'base64_bytes'
                    else:
                        print(f"⚠️ Grok image: unexpected data format, keys: {list(image_data.keys())}")
                        return None
                    
                    return output
                    
                print(f"⚠️ Grok image: no data in response, keys: {list(result.keys())}")
                return None
            else:
                print(f"❌ Grok image generation failed: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Grok image generation error: {e}")
            return None

# Global instance
grok_ai = GrokAI()
