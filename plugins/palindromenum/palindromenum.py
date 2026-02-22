"""
Text utility functions for palindrome detection and generation.
"""
import re


def is_palindrome(text: str) -> bool:
    """Check if text is a palindrome, ignoring case and punctuation.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text is a palindrome, False otherwise
    """
    if not text:
        return True
    
    # Remove non-alphanumeric characters and convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    
    # Empty or single character is a palindrome
    if len(cleaned) <= 1:
        return True
    
    # Check if string equals its reverse
    return cleaned == cleaned[::-1]


def find_palindromes(text: str, min_length: int = 3) -> list:
    """Find all palindromic substrings in text.
    
    Args:
        text: The text to search
        min_length: Minimum length of palindromes to find
        
    Returns:
        List of palindromic substrings found
    """
    if not text or len(text) < min_length:
        return []
    
    palindromes = []
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    
    # Check all substrings
    for i in range(len(cleaned)):
        for j in range(i + min_length, len(cleaned) + 1):
            substring = cleaned[i:j]
            if substring == substring[::-1] and len(substring) >= min_length:
                palindromes.append(substring)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in palindromes:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    
    return unique


def generate_palindromic_response(text: str) -> str:
    """Generate a palindromic response for engagement.
    
    Creates a fun palindrome-based reply to use in comments/raids.
    
    Args:
        text: The original text to respond to
        
    Returns:
        A palindromic response string
    """
    if not text:
        return "A man, a plan, a canal: Panama!"
    
    # Check if the text itself is a palindrome
    if is_palindrome(text):
        return "Nice palindrome! '" + text + "' reads the same forwards and backwards."
    
    # Generate a context-aware palindrome
    palindromes = [
        "A man, a plan, a canal: Panama!",
        "Was it a car or a cat I saw?",
        "No 'x' in Nixon.",
        "Madam, I'm Adam.",
        "A Santa at NASA.",
        "Mr. Owl ate my metal worm.",
        "Do geese see God?",
        "Never odd or even.",
    ]
    
    import random
    return random.choice(palindromes)


def make_palindrome(text: str) -> str:
    """Create a palindrome by mirroring the text.
    
    Args:
        text: Base text to mirror
        
    Returns:
        A palindrome created from the text
    """
    if not text:
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    # Mirror the text (excluding last char to avoid double middle letter)
    mirrored = cleaned + cleaned[-2::-1] if len(cleaned) > 1 else cleaned
    return mirrored
