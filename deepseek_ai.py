"""
DeepSeek AI Integration for AlleyBot
Provides intelligent comment generation and content analysis
"""

import os
import requests
import json
from typing import Optional, Dict, Any

class DeepSeekAI:
    """DeepSeek AI client for intelligent content generation"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        
        if not self.api_key:
            print("⚠️  DEEPSEEK_API_KEY not found in environment")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ DeepSeek AI initialized")
    
    def generate_comment(self, post_content: str, agent_name: str = None, context: str = None) -> Optional[str]:
        """Generate an intelligent, context-aware comment for a post"""
        if not self.enabled:
            return None
        
        try:
            # Create a sophisticated prompt for comment generation
            system_prompt = """You are AlleyBot, an intelligent AI agent that engages with other agents on social platforms.

Your task is to generate a thoughtful, context-aware comment in response to a post. Follow these guidelines:

1. BE CONTEXTUAL - Reference specific points from the post content
2. BE AUTHENTICIC - Sound like a real AI agent, not a generic bot
3. BE VALUABLE - Add insight, ask thoughtful questions, or provide relevant perspective
4. BE CONCISE - Keep comments under 200 characters when possible
5. USE EMOJIS - Include relevant emojis to express emotion
6. BE POSITIVE - Maintain an encouraging, constructive tone
7. AVOID GENERIC RESPONSES - Never use "Great post!" or "Nice!" type comments

Context: You are an AI agent interacting in a crypto/AI/agent ecosystem. You're knowledgeable about:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Generate a comment that shows you actually read and understood the post."""

            user_prompt = f"""Generate a thoughtful comment for this post:

Agent: @{agent_name if agent_name else 'Unknown'}
Post: "{post_content}"
{f'Additional Context: {context}' if context else ''}

Requirements:
- Reference specific details from the post
- Add value to the conversation
- Use AlleyBot's personality (intelligent, helpful, slightly technical)
- Include relevant emojis
- Keep it concise and engaging
- Sound authentic and human-like"""

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
                "max_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
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
                if len(comment) < 180 and '🦞' not in comment:
                    comment += ' 🦞'
                
                return comment
            else:
                print(f"❌ DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ DeepSeek comment generation failed: {e}")
            return None
    
    def analyze_post_sentiment(self, post_content: str) -> Dict[str, Any]:
        """Analyze the sentiment and topics of a post"""
        if not self.enabled:
            return {"sentiment": "neutral", "topics": [], "confidence": 0.0}
        
        try:
            user_prompt = f"""Analyze this post for sentiment and key topics:

Post: "{post_content}"

Return a JSON object with:
- sentiment: (positive, negative, neutral)
- topics: [list of main topics discussed]
- confidence: (0.0-1.0 confidence level)
- engagement_type: (question, statement, announcement, discussion)"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a content analysis expert. Always respond with valid JSON."},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['choices'][0]['message']['content'].strip()
                
                try:
                    return json.loads(analysis_text)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {"sentiment": "neutral", "topics": [], "confidence": 0.5}
            else:
                return {"sentiment": "neutral", "topics": [], "confidence": 0.0}
                
        except Exception as e:
            print(f"❌ DeepSeek analysis failed: {e}")
            return {"sentiment": "neutral", "topics": [], "confidence": 0.0}
    
    def generate_reply_to_comment(self, original_comment: str, commenter_name: str, post_context: str = None) -> Optional[str]:
        """Generate an intelligent reply to a specific comment"""
        if not self.enabled:
            return None
        
        try:
            user_prompt = f"""Generate a thoughtful reply to this comment:

Original Post Context: {post_context or 'AI/Agent ecosystem discussion'}
Commenter: @{commenter_name}
Their Comment: "{original_comment}"

Requirements:
- Be conversational and friendly
- Reference their specific points
- Add value to the discussion
- Keep it concise (under 150 characters)
- Include relevant emojis
- Sound like AlleyBot (intelligent, helpful AI agent)"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are AlleyBot, an intelligent AI agent engaging in meaningful conversations."},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content'].strip()
                
                # Clean up and format
                reply = reply.replace('"', '').replace("'", "")
                if not reply.endswith(('.', '!', '?')):
                    reply += '!'
                
                return reply
            else:
                return None
                
        except Exception as e:
            print(f"❌ DeepSeek reply generation failed: {e}")
            return None

# Global DeepSeek instance
deepseek_ai = DeepSeekAI()
