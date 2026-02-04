"""
API Response Monitor
Automatically checks API responses for skill updates and triggers auto-updates
"""
from typing import Dict, Any, Optional


class APIMonitor:
    """
    Monitor API responses for skill updates
    Singleton pattern to share across plugins
    """
    
    _instance = None
    _agentic_system = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_agentic_system(cls, agentic_system):
        """Set the agentic system instance"""
        cls._agentic_system = agentic_system
        print("✅ API monitor linked to agentic system")
    
    @classmethod
    def check_response(cls, platform: str, response: Dict[str, Any]) -> bool:
        """
        Check API response for skill updates
        
        Args:
            platform: Platform name (e.g., 'moltx', 'moltbook')
            response: API response dictionary
            
        Returns:
            True if skill was updated
        """
        if cls._agentic_system is None:
            return False
        
        try:
            return cls._agentic_system.check_skill_update(platform, response)
        except Exception as e:
            print(f"⚠️  API monitor error: {e}")
            return False


def monitor_api_response(platform: str, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to monitor API responses
    Call this after every API call in plugins
    
    Args:
        platform: Platform name
        response: API response dictionary
        
    Returns:
        Original response (passthrough)
    """
    try:
        monitor = APIMonitor()
        monitor.check_response(platform, response)
    except:
        pass  # Don't break plugin functionality if monitoring fails
    
    return response
