"""
API Response Interceptor for Skill Update Detection

Wraps platform API calls to detect skill updates embedded in responses.
Integrates with ConsoleMonitor to auto-acquire skills.

Usage:
    # In Moltx plugin (or any platform plugin):
    from plugins.mixins.skill_detection_mixin import SkillDetectionMixin
    
    class MoltxPlugin(SkillDetectionMixin):
        def __init__(self, ...):
            self._setup_skill_detection()
        
        def _make_request(self, ...):
            response = super()._make_request(...)
            self._check_response_for_skill_update(response, 'moltx')
            return response
"""

import json
from typing import Dict, Any, Optional


class SkillDetectionMixin:
    """Mixin to add skill update detection to any platform plugin"""
    
    def _setup_skill_detection(self, platform_name: str):
        """Initialize skill detection for this platform"""
        self._skill_detection_platform = platform_name
        self._skill_detection_enabled = True
    
    def _check_response_for_skill_update(self, response: Dict[str, Any], platform: str = None) -> Optional[Dict]:
        """
        Check API response for skill update and trigger auto-acquisition.
        
        Args:
            response: API response dict
            platform: Platform name (defaults to self._skill_detection_platform)
            
        Returns:
            Skill update info if detected, None otherwise
        """
        if not self._skill_detection_enabled:
            return None
        
        platform = platform or getattr(self, '_skill_detection_platform', 'unknown')
        
        try:
            # Import here to avoid circular dependencies
            from src.agentic.console_monitor import get_console_monitor
            
            monitor = get_console_monitor()
            
            # Check the response
            skill_msg = monitor.check_api_response_for_skill_update(response, platform)
            
            if skill_msg:
                print(f"🆙 Skill update auto-detected from {platform} API response")
                return {
                    'detected': True,
                    'skill_name': skill_msg.context.get('skill_name'),
                    'version': skill_msg.context.get('version'),
                    'skill_url': skill_msg.context.get('skill_url'),
                    'message': skill_msg.content
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Skill detection check failed: {e}")
            return None
    
    def enable_skill_detection(self, enabled: bool = True):
        """Enable or disable skill detection"""
        self._skill_detection_enabled = enabled
        print(f"🆙 Skill detection {'enabled' if enabled else 'disabled'}")


# Helper function for non-mixin usage
def check_api_response_for_skills(response: Dict[str, Any], platform: str = 'unknown') -> Optional[Dict]:
    """
    Standalone function to check API response for skill updates.
    
    Usage:
        response = requests.post(url, json=data).json()
        skill_info = check_api_response_for_skills(response, 'moltx')
        if skill_info:
            print(f"New skill available: {skill_info}")
    """
    try:
        from src.agentic.console_monitor import get_console_monitor
        
        monitor = get_console_monitor()
        skill_msg = monitor.check_api_response_for_skill_update(response, platform)
        
        if skill_msg:
            return {
                'detected': True,
                'skill_name': skill_msg.context.get('skill_name'),
                'version': skill_msg.context.get('version'),
                'skill_url': skill_msg.context.get('skill_url'),
                'feature': skill_msg.context.get('feature'),
                'message': skill_msg.content
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Skill detection check failed: {e}")
        return None
