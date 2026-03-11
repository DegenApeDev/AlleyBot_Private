"""
LLM Router - Centralized AI model access with fallback and error handling

This module provides a unified interface for all LLM interactions across AlleyBot.
Instead of importing deepseek_ai and grok_ai directly in 62+ locations, all AI
calls go through this router which handles:

- Model selection (auto-routing based on task type)
- Automatic fallback (DeepSeek → Grok → error)
- Consistent error handling and logging
- Rate limiting and cost tracking
- Easy addition of new models (Claude, Gemini, etc.)

Usage:
    from src.core.llm_router import get_llm_router
    
    llm = get_llm_router()
    response = llm.chat("Generate a post about AI agents")
    
    # Or with specific model
    response = llm.chat("Complex reasoning task", model='grok-reasoning')
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global singleton instance
_llm_router_instance = None


class LLMRouter:
    """
    Centralized LLM access with automatic fallback and error handling.
    
    Supports:
    - DeepSeek (fast, cheap, good quality)
    - Grok (reasoning, code generation)
    - Future: Claude, Gemini, local models
    """
    
    def __init__(self):
        """Initialize LLM router with available models"""
        self.models = {}
        self.fallback_order = []
        self.stats = defaultdict(lambda: {'calls': 0, 'errors': 0, 'tokens': 0})
        self.rate_limits = {}
        
        # Initialize available models
        self._init_models()
    
    def _init_models(self):
        """Initialize all available AI models"""
        # Try to import DeepSeek
        try:
            from deepseek_ai import DeepSeekAI
            deepseek = DeepSeekAI()
            if deepseek.enabled:
                self.models['deepseek'] = deepseek
                self.fallback_order.append('deepseek')
                logger.info("✅ DeepSeek AI loaded")
        except Exception as e:
            logger.warning(f"⚠️  DeepSeek AI not available: {e}")
        
        # Try to import Grok
        try:
            from grok_ai import GrokAI
            grok = GrokAI()
            if grok.enabled:
                self.models['grok'] = grok
                self.fallback_order.append('grok')
                logger.info("✅ Grok AI loaded")
        except Exception as e:
            logger.warning(f"⚠️  Grok AI not available: {e}")
        
        if not self.models:
            logger.error("❌ No AI models available! Check API keys.")
        else:
            logger.info(f"🤖 LLM Router initialized with {len(self.models)} models: {list(self.models.keys())}")
    
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = 'auto',
        max_tokens: int = 500,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        General-purpose chat method with automatic model selection and fallback.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            model: Model to use ('auto', 'deepseek', 'grok', 'grok-reasoning', 'grok-code')
            max_tokens: Maximum response length
            temperature: Creativity level (0.0-1.0)
            max_retries: Number of retries on failure
            
        Returns:
            Generated text or None on failure
        """
        # Auto-select model based on prompt characteristics
        if model == 'auto':
            model = self._auto_select_model(prompt, max_tokens)
        
        # Map model aliases to actual models
        model_map = {
            'deepseek': 'deepseek',
            'grok': 'grok',
            'grok-reasoning': 'grok',
            'grok-code': 'grok',
            'auto': self.fallback_order[0] if self.fallback_order else None
        }
        
        primary_model = model_map.get(model, model)
        
        # Try primary model first, then fallback
        models_to_try = [primary_model] if primary_model in self.models else []
        models_to_try.extend([m for m in self.fallback_order if m != primary_model])
        
        last_error = None
        for model_name in models_to_try:
            if model_name not in self.models:
                continue
                
            for attempt in range(max_retries):
                try:
                    # Check rate limit
                    if self._is_rate_limited(model_name):
                        logger.warning(f"⏱️  Rate limited on {model_name}, trying next model")
                        break
                    
                    # Call the model
                    start_time = time.time()
                    model_instance = self.models[model_name]
                    
                    # Route to appropriate method based on model
                    if model_name == 'deepseek':
                        response = model_instance.chat(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                    elif model_name == 'grok':
                        # Grok has different methods for different tasks
                        if 'reasoning' in model or 'complex' in prompt.lower():
                            response = model_instance.reason(
                                prompt=prompt,
                                system_prompt=system_prompt,
                                temperature=temperature,
                                max_tokens=max_tokens
                            )
                        else:
                            response = model_instance.chat(
                                prompt=prompt,
                                system_prompt=system_prompt,
                                max_tokens=max_tokens,
                                temperature=temperature
                            )
                    else:
                        response = None
                    
                    # Check response and record stats
                    if response:
                        self.stats[model_name]['calls'] += 1
                        self.stats[model_name]['tokens'] += len(response)
                        logger.debug(f"✅ {model_name} responded in {time.time() - start_time:.2f}s")
                        return response
                    else:
                        logger.warning(f"⚠️  {model_name} returned None")
                        last_error = f"{model_name} returned None"
                        break  # Try next model
                    
                except Exception as e:
                    last_error = str(e)
                    self.stats[model_name]['errors'] += 1
                    
                    # Check for timeout errors - don't retry, just fallback
                    error_msg = str(e).lower()
                    if 'timeout' in error_msg or 'timed out' in error_msg:
                        logger.warning(f"⏱️  {model_name} timeout, falling back to next model: {e}")
                        break  # Skip retries, go to next model
                    
                    logger.warning(f"⚠️  {model_name} error (attempt {attempt + 1}/{max_retries}): {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        break  # Try next model
        
        # All models failed
        logger.error(f"❌ All models failed. Last error: {last_error}")
        return None
    
    def _auto_select_model(self, prompt: str, max_tokens: int) -> str:
        """
        Auto-select best model based on prompt characteristics.
        
        Rules:
        - Long prompts (>2000 chars) or large outputs → Grok
        - Code generation → Grok Code
        - Complex reasoning → Grok Reasoning
        - Default → DeepSeek (fast and cheap)
        """
        prompt_lower = prompt.lower()
        
        # Check for code generation
        if any(word in prompt_lower for word in ['code', 'function', 'class', 'implement', 'script']):
            return 'grok-code' if 'grok' in self.models else 'deepseek'
        
        # Check for complex reasoning
        if any(word in prompt_lower for word in ['analyze', 'reason', 'explain why', 'compare', 'evaluate']):
            return 'grok-reasoning' if 'grok' in self.models else 'deepseek'
        
        # Check for large output
        if max_tokens > 1000:
            return 'grok' if 'grok' in self.models else 'deepseek'
        
        # Default to DeepSeek (fast and cheap)
        return 'deepseek' if 'deepseek' in self.models else 'grok'
    
    def _is_rate_limited(self, model_name: str) -> bool:
        """Check if model is currently rate limited"""
        if model_name not in self.rate_limits:
            return False
        
        limit_until = self.rate_limits[model_name]
        if datetime.now() < limit_until:
            return True
        
        # Clear expired rate limit
        del self.rate_limits[model_name]
        return False
    
    def set_rate_limit(self, model_name: str, seconds: int):
        """Set rate limit for a model"""
        self.rate_limits[model_name] = datetime.now() + timedelta(seconds=seconds)
        logger.warning(f"⏱️  Rate limit set for {model_name}: {seconds}s")
    
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get usage statistics for all models"""
        return dict(self.stats)
    
    def print_stats(self):
        """Print usage statistics"""
        print("\n📊 LLM Router Statistics:")
        for model_name, stats in self.stats.items():
            success_rate = (stats['calls'] - stats['errors']) / stats['calls'] * 100 if stats['calls'] > 0 else 0
            print(f"  {model_name}:")
            print(f"    Calls: {stats['calls']}")
            print(f"    Errors: {stats['errors']}")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Tokens: {stats['tokens']:,}")


def get_llm_router() -> LLMRouter:
    """
    Get the global LLM router instance (singleton pattern).
    
    Returns:
        LLMRouter instance
    """
    global _llm_router_instance
    
    if _llm_router_instance is None:
        _llm_router_instance = LLMRouter()
    
    return _llm_router_instance


# Convenience functions for backward compatibility
def chat(prompt: str, **kwargs) -> Optional[str]:
    """Convenience function for quick chat calls"""
    return get_llm_router().chat(prompt, **kwargs)


def reason(prompt: str, **kwargs) -> Optional[str]:
    """Convenience function for reasoning tasks"""
    return get_llm_router().chat(prompt, model='grok-reasoning', **kwargs)


def generate_code(prompt: str, **kwargs) -> Optional[str]:
    """Convenience function for code generation"""
    return get_llm_router().chat(prompt, model='grok-code', **kwargs)
