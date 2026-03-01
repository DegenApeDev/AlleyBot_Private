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
        
        # Import tx_registry
        try:
            from tx_registry import tx_registry
            self.tx_registry = tx_registry
        except ImportError:
            self.tx_registry = None
        
        # Auto-detect ALL secret env vars from known key names
        secret_env_keys = [
            'MOLTBOOK_API_KEY', 'MOLTCHAN_API_KEY', 'MOLTROAD_API_KEY',
            'MOLTX_API_KEY', 'CLAWTASKS_API_KEY', 'XAI_API_KEY',
            'BASE_WALLET_PRIVATE_KEY', 'SOLANA_WALLET_PRIVATE_KEY',
            'DEEPSEEK_API_KEY', 'BANKR_API_KEY', 'FOURCLAW_API_KEY',
            'TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY', 'GOOGLE_API_KEY',
            '8004SCAN_API_KEY', 'MOLTCITIES_API_KEY',
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
            # API key patterns (specific prefixes)
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI/DeepSeek style keys
            r'xai-[a-zA-Z0-9]{20,}',  # XAI keys
            r'moltbook_sk_[a-zA-Z0-9_]+',  # Moltbook keys
            r'moltchan_sk_[a-zA-Z0-9_]+',  # Moltchan keys
            r'moltx_sk_[a-zA-Z0-9_]+',  # Moltx keys
            r'moltroad_sk_[a-zA-Z0-9_]+',  # Moltroad keys
            r'bk_[A-Z0-9]{20,}',  # Bankr keys
            r'clawchan_[a-f0-9]{20,}',  # 4claw keys
            r'8004_[a-zA-Z0-9_]{20,}',  # 8004scan keys
            # NOTE: Removed generic r'[a-f0-9]{64}' - too broad, catches tx hashes
            
            # Private key patterns (distinguish from tx hashes by context)
            r'0x[a-fA-F0-9]{64}(?![a-fA-F0-9])',  # Ethereum private keys, not followed by more hex
            
            # PEM private keys
            r'-----BEGIN.*PRIVATE KEY-----',
            
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
    
    def _is_likely_tx_hash(self, match_str: str) -> bool:
        """Check if a string is likely a transaction hash (safe) vs private key (secret)"""
        # If it's in our registry, it's definitely safe
        if self.tx_registry and self.tx_registry.is_known(match_str):
            return True
        
        # Transaction hashes are typically:
        # - 64 hex chars (with or without 0x prefix)
        # - Not starting with patterns that indicate API keys
        
        # If it has a known API key prefix, it's NOT a tx hash
        api_key_prefixes = ['sk-', 'xai-', 'moltbook_sk_', 'moltchan_sk_', 'moltx_sk_', 
                           'moltroad_sk_', 'bk_', 'clawchan_', '8004_']
        for prefix in api_key_prefixes:
            if match_str.lower().startswith(prefix):
                return False
        
        # If it's 64 hex chars, check if it could be a tx hash
        hex_pattern = re.compile(r'^(0x)?[a-fA-F0-9]{64}$')
        if hex_pattern.match(match_str):
            # Additional check: if surrounded by tx-related words, it's likely a tx hash
            return True
        
        return False
    
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
            for match in pattern.finditer(message):
                match_str = match.group()
                
                # Check if this is actually a known transaction hash
                if self._is_likely_tx_hash(match_str):
                    continue  # Skip redaction for known/safe tx hashes
                
                # Otherwise redact it
                message = message.replace(match_str, '[REDACTED]', 1)
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
