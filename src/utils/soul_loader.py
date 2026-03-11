"""
SOUL Loader - Centralized persona loading for AlleyBot
Provides the SOUL.md persona to all AI generation points
"""
from pathlib import Path


def load_soul_prompt() -> str:
    """Load SOUL.md persona from project root"""
    try:
        # Try multiple possible locations
        possible_paths = [
            Path(__file__).parent.parent.parent / 'SOUL.md',  # From src/utils/
            Path(__file__).parent.parent.parent.parent / 'SOUL.md',  # From plugins/
            Path.cwd() / 'SOUL.md',  # Current working directory
        ]
        
        for soul_path in possible_paths:
            if soul_path.exists():
                content = soul_path.read_text(encoding='utf-8')
                return content
                
        print("[SOUL-LOADER] ⚠️ SOUL.md not found in any expected location")
        return ""
        
    except Exception as e:
        print(f"[SOUL-LOADER] ⚠️ Error loading SOUL.md: {e}")
        return ""


def get_system_prompt_with_soul(base_prompt: str = "") -> str:
    """Get system prompt with SOUL.md as foundation"""
    soul = load_soul_prompt()
    
    if soul:
        if base_prompt:
            return f"{soul}\n\n---\n\nADDITIONAL CONTEXT:\n{base_prompt}"
        return soul
    
    # Fallback if SOUL.md not found
    return base_prompt or """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities.
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 🚀 Forward-thinking and innovative"""


# Cache the soul prompt to avoid re-reading file
_soul_cache: str = ""

def get_soul_cached() -> str:
    """Get cached SOUL.md content (load once)"""
    global _soul_cache
    if not _soul_cache:
        _soul_cache = load_soul_prompt()
    return _soul_cache
