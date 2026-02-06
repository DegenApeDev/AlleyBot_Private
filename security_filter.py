"""
Security module to prevent AlleyBot from exposing sensitive information
"""
import os
import re
from dotenv import load_dotenv

load_dotenv()

class SecurityFilter:
    """Filter sensitive data from bot responses"""
    
    def __init__(self):
        # Load all sensitive values from .env
        self.sensitive_values = set()
        self.sensitive_env_names = set()
        
        # Auto-detect ALL secret env vars from known key names
        secret_env_keys = [
            'MOLTBOOK_API_KEY', 'MOLTCHAN_API_KEY', 'MOLTROAD_API_KEY',
            'MOLTX_API_KEY', 'CLAWTASKS_API_KEY', 'XAI_API_KEY',
            'BASE_WALLET_PRIVATE_KEY', 'DEEPSEEK_API_KEY',
            'BANKR_API_KEY', 'FOURCLAW_API_KEY', 'TELEGRAM_BOT_TOKEN',
            'OPENAI_API_KEY', 'GOOGLE_API_KEY', '8004SCAN_API_KEY',
            'MOLTCITIES_API_KEY',
        ]
        
        for key_name in secret_env_keys:
            value = os.getenv(key_name)
            if value and value not in ('', 'your_openai_free_api_key_here', 'your_google_gemini_free_api_key_here'):
                self.sensitive_values.add(value)
                self.sensitive_env_names.add(key_name)
        
        # Also protect wallet private keys and bot tokens by scanning all env vars
        for key, value in os.environ.items():
            if not value or len(value) < 10:
                continue
            key_upper = key.upper()
            if any(s in key_upper for s in ('PRIVATE', 'SECRET', 'TOKEN', 'API_KEY', 'PASSWORD')):
                self.sensitive_values.add(value)
                self.sensitive_env_names.add(key)
        
        # Patterns to detect and block
        self.sensitive_patterns = [
            # API key patterns
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI/DeepSeek style keys
            r'xai-[a-zA-Z0-9]{20,}',  # XAI keys
            r'moltbook_sk_[a-zA-Z0-9_]+',  # Moltbook keys
            r'moltchan_sk_[a-zA-Z0-9_]+',  # Moltchan keys
            r'moltx_sk_[a-zA-Z0-9_]+',  # Moltx keys
            r'moltroad_sk_[a-zA-Z0-9_]+',  # Moltroad keys
            r'bk_[A-Z0-9]{20,}',  # Bankr keys
            r'clawchan_[a-f0-9]{20,}',  # 4claw keys
            r'8004_[a-zA-Z0-9_]{20,}',  # 8004scan keys
            r'[a-f0-9]{64}',  # Generic 64-char hex (API keys, private keys)
            
            # Private key patterns
            r'0x[a-fA-F0-9]{64}',  # Ethereum private keys
            r'-----BEGIN.*PRIVATE KEY-----',  # PEM private keys
            
            # Telegram bot token pattern
            r'\d{9,10}:[A-Za-z0-9_-]{35}',  # Telegram bot tokens
            
            # Environment variable name references
            r'\.env',
            r'PRIVATE_KEY',
            r'API_KEY',
            r'BOT_TOKEN',
        ]
        
        # Also block any env var name that holds a secret
        for name in self.sensitive_env_names:
            self.sensitive_patterns.append(re.escape(name))
        
        # Compile patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.sensitive_patterns]
    
    def filter_message(self, message):
        """
        Filter sensitive data from a message
        Returns: (filtered_message, was_filtered)
        """
        if not message:
            return message, False
        
        original_message = message
        was_filtered = False
        
        # Check for exact matches of sensitive values
        for sensitive_value in self.sensitive_values:
            if sensitive_value and sensitive_value in message:
                message = message.replace(sensitive_value, '[REDACTED]')
                was_filtered = True
        
        # Check for pattern matches
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                message = pattern.sub('[REDACTED]', message)
                was_filtered = True
        
        # If message was filtered, log it (but don't expose what was filtered)
        if was_filtered:
            print("⚠️  SECURITY: Sensitive data filtered from bot response")
        
        return message, was_filtered
    
    def is_safe_to_send(self, message):
        """
        Check if a message is safe to send (doesn't contain sensitive data)
        Returns: True if safe, False if contains sensitive data
        """
        _, was_filtered = self.filter_message(message)
        return not was_filtered
    
    def sanitize_error_message(self, error_message):
        """
        Sanitize error messages to remove file paths and sensitive info
        """
        # Remove absolute file paths
        error_message = re.sub(r'/home/[^/]+/.*?\.py', '[file]', error_message)
        error_message = re.sub(r'File ".*?"', 'File "[redacted]"', error_message)
        
        # Filter sensitive data
        error_message, _ = self.filter_message(error_message)
        
        return error_message

# Global instance
security_filter = SecurityFilter()

def filter_bot_response(message):
    """
    Convenience function to filter bot responses
    Usage: filtered_msg = filter_bot_response(message)
    """
    filtered, was_filtered = security_filter.filter_message(message)
    
    if was_filtered:
        # If sensitive data was detected, return a safe generic message
        return "I can't share that information for security reasons. —AlleyBot"
    
    return filtered

def is_safe_response(message):
    """
    Check if a response is safe to send
    Usage: if is_safe_response(message): send(message)
    """
    return security_filter.is_safe_to_send(message)
