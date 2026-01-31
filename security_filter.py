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
        
        # API Keys
        moltbook_key = os.getenv('MOLTBOOK_API_KEY')
        xai_key = os.getenv('XAI_API_KEY')
        base_private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        moltcities_key = os.getenv('MOLTCITIES_API_KEY')
        
        # Add to sensitive set (only if they exist)
        if moltbook_key:
            self.sensitive_values.add(moltbook_key)
        if xai_key:
            self.sensitive_values.add(xai_key)
        if base_private_key:
            self.sensitive_values.add(base_private_key)
        if moltcities_key:
            self.sensitive_values.add(moltcities_key)
        
        # Patterns to detect and block
        self.sensitive_patterns = [
            # API key patterns
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI/XAI style keys
            r'xai-[a-zA-Z0-9]{32,}',  # XAI keys
            r'[a-f0-9]{64}',  # Generic API keys (64 hex chars)
            
            # Private key patterns
            r'0x[a-f0-9]{64}',  # Ethereum private keys
            r'-----BEGIN.*PRIVATE KEY-----',  # PEM private keys
            
            # Environment variable references
            r'\.env',
            r'MOLTBOOK_API_KEY',
            r'XAI_API_KEY',
            r'BASE_WALLET_PRIVATE_KEY',
            r'MOLTCITIES_API_KEY',
        ]
        
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
