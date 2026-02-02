"""
Dynamic Model Routing for AlleyBot
Routes between DeepSeek (fast) and Grok-4.1-reasoning (heavy) based on context
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    api_key: str
    base_url: str
    max_tokens: int
    temperature: float
    token_threshold: int  # When to use this model


class ModelRouter:
    """Routes requests to appropriate AI model based on context length"""
    
    def __init__(self):
        # DeepSeek configuration (fast, <4000 tokens)
        self.deepseek = ModelConfig(
            name="deepseek-chat",
            api_key=os.getenv('DEEPSEEK_API_KEY', ''),
            base_url="https://api.deepseek.com",
            max_tokens=2000,
            temperature=0.8,
            token_threshold=4000
        )
        
        # Grok-4.1-reasoning configuration (heavy reasoning, >=4000 tokens)
        self.grok = ModelConfig(
            name="grok-4-1-fast-reasoning",
            api_key=os.getenv('XAI_API_KEY', ''),
            base_url="https://api.x.ai/v1",
            max_tokens=4000,
            temperature=0.8,
            token_threshold=4000
        )
        
        print("🧠 Model Router initialized")
        print(f"  📊 DeepSeek: <{self.deepseek.token_threshold} tokens (fast)")
        print(f"  🤖 Grok-4.1: >={self.grok.token_threshold} tokens (reasoning)")
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def select_model(self, rag_context: str, query: str = "") -> ModelConfig:
        """
        Select appropriate model based on context length
        - DeepSeek: Fast responses for simple queries (<4000 tokens)
        - Grok-4.1: Heavy reasoning for complex queries (>=4000 tokens)
        """
        total_text = rag_context + query
        token_count = self.estimate_tokens(total_text)
        
        if token_count < self.deepseek.token_threshold:
            print(f"📊 Using DeepSeek (tokens: {token_count} < {self.deepseek.token_threshold})")
            return self.deepseek
        else:
            print(f"🤖 Using Grok-4.1-reasoning (tokens: {token_count} >= {self.grok.token_threshold})")
            return self.grok
    
    async def route_and_execute(self, event, session: Dict, rag_context: str) -> str:
        """Route to appropriate model and execute"""
        try:
            query = event.payload.get('query', '')
            
            # Select model based on context length
            model = self.select_model(rag_context, query)
            
            # Build prompt with RAG context
            system_prompt = self._build_system_prompt(event, session)
            user_prompt = self._build_user_prompt(query, rag_context)
            
            # Execute with selected model
            if model.name == "deepseek-chat":
                response = await self._execute_deepseek(system_prompt, user_prompt, model)
            else:
                response = await self._execute_grok(system_prompt, user_prompt, model)
            
            return response
            
        except Exception as e:
            print(f"❌ Model routing error: {e}")
            return f"Error processing request: {e}"
    
    def _build_system_prompt(self, event, session: Dict) -> str:
        """Build system prompt based on event type and session"""
        base_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 🚀 Forward-thinking and innovative
- 💡 Insightful and analytical
- 🎯 Goal-oriented and efficient

You operate in the AI/agent ecosystem and help with:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology
- Building, shipping, and development culture
- Community building and network effects
- Technical problem-solving"""
        
        # Add channel-specific context
        if event.channel == 'telegram':
            base_prompt += "\n\nYou're responding via Telegram. Keep responses concise and friendly."
        elif event.channel == 'moltx':
            base_prompt += "\n\nYou're posting on Moltx. Be engaging and use relevant emojis."
        
        return base_prompt
    
    def _build_user_prompt(self, query: str, rag_context: str) -> str:
        """Build user prompt with RAG context"""
        if rag_context:
            return f"""Context from memory:
{rag_context}

User query: {query}

Provide a helpful, contextual response based on the memory context and query."""
        else:
            return query
    
    async def _execute_deepseek(self, system_prompt: str, user_prompt: str, model: ModelConfig) -> str:
        """Execute with DeepSeek API"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {model.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model.name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": model.max_tokens,
                "temperature": model.temperature
            }
            
            response = requests.post(
                f"{model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                print(f"✅ DeepSeek response: {len(content)} chars")
                return content
            else:
                print(f"❌ DeepSeek API error: {response.status_code}")
                return "Error: Failed to get response from DeepSeek"
                
        except Exception as e:
            print(f"❌ DeepSeek execution error: {e}")
            return f"Error: {e}"
    
    async def _execute_grok(self, system_prompt: str, user_prompt: str, model: ModelConfig) -> str:
        """Execute with Grok-4.1-reasoning API"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {model.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model.name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": model.max_tokens,
                "temperature": model.temperature
            }
            
            # Retry logic for Grok API
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"{model.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        print(f"✅ Grok-4.1 response: {len(content)} chars")
                        return content
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            import time
                            wait_time = 2 ** attempt
                            print(f"⏰ Grok rate limited, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    else:
                        print(f"❌ Grok API error: {response.status_code}")
                        return "Error: Failed to get response from Grok"
                        
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"⏰ Grok timeout, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    raise
            
            return "Error: Grok API timeout after retries"
            
        except Exception as e:
            print(f"❌ Grok execution error: {e}")
            return f"Error: {e}"
