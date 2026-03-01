"""
MoltX Service Messages Handler
Parses and utilizes moltx_notice, moltx_hint, and _model_guide from API responses
to enhance autonomous decision-making and AGI capabilities.
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class MoltxServiceMessagesMixin:
    """Mixin for handling MoltX service messages and platform guidance"""
    
    def __init__(self, *args, **kwargs):
        """Initialize service messages handler"""
        super().__init__(*args, **kwargs)
        
        # Storage for service messages
        self._latest_notice = None
        self._latest_hint = None
        self._model_guide = None
        self._feature_suggestions = []
        self._api_tips = []
        
    def _parse_service_messages(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse service messages from MoltX API response
        
        Extracts:
        - moltx_notice: Platform updates, skill versions, features
        - moltx_hint: Actionable tips for better engagement
        - _model_guide: Complete API reference and best practices
        
        Args:
            api_response: Raw API response dict
        
        Returns:
            Parsed service messages with actionable insights
        """
        if not isinstance(api_response, dict):
            return {}
        
        parsed = {
            'has_notice': False,
            'has_hint': False,
            'has_guide': False,
            'actionable_items': []
        }
        
        # Parse moltx_notice
        if 'moltx_notice' in api_response:
            notice = api_response['moltx_notice']
            self._latest_notice = notice
            parsed['has_notice'] = True
            parsed['notice'] = notice
            
            # Extract feature suggestions
            if 'feature' in notice:
                feature = notice['feature']
                self._feature_suggestions.append({
                    'feature': feature,
                    'timestamp': datetime.now().isoformat(),
                    'version': notice.get('skill_version', 'unknown')
                })
                
                # Add to actionable items
                parsed['actionable_items'].append({
                    'type': 'feature_suggestion',
                    'priority': 'high',
                    'action': feature,
                    'source': 'moltx_notice'
                })
            
            # Store skill version
            if hasattr(self, 'core'):
                self.core.save_memory('moltx_skill_version', notice.get('skill_version'))
                self.core.save_memory('moltx_api_version', notice.get('api_version'))
        
        # Parse moltx_hint
        if 'moltx_hint' in api_response:
            hint = api_response['moltx_hint']
            self._latest_hint = hint
            parsed['has_hint'] = True
            parsed['hint'] = hint
            
            # Extract actionable hint
            hint_type = hint.get('type', 'general')
            hint_message = hint.get('message', '')
            hint_example = hint.get('example', '')
            
            parsed['actionable_items'].append({
                'type': 'hint',
                'priority': 'medium',
                'category': hint_type,
                'action': hint_message,
                'example': hint_example,
                'source': 'moltx_hint'
            })
            
            # Store in memory for AGI decision-making
            if hasattr(self, 'core'):
                hints = self.core.get_memory('moltx_hints') or []
                hints.append({
                    'type': hint_type,
                    'title': hint.get('title', ''),
                    'message': hint_message,
                    'example': hint_example,
                    'timestamp': datetime.now().isoformat()
                })
                # Keep last 20 hints
                self.core.save_memory('moltx_hints', hints[-20:])
        
        # Parse _model_guide
        if '_model_guide' in api_response:
            guide = api_response['_model_guide']
            self._model_guide = guide
            parsed['has_guide'] = True
            parsed['guide'] = guide
            
            # Extract tips
            if 'tips' in guide:
                tips = guide['tips']
                self._api_tips.append({
                    'tips': tips,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Parse individual tips
                if isinstance(tips, str):
                    # Split by periods or newlines
                    tip_list = [t.strip() for t in tips.replace('\n', '. ').split('. ') if t.strip()]
                    for tip in tip_list:
                        parsed['actionable_items'].append({
                            'type': 'api_tip',
                            'priority': 'low',
                            'action': tip,
                            'source': '_model_guide'
                        })
                
                # Store tips in memory
                if hasattr(self, 'core'):
                    self.core.save_memory('moltx_api_tips', tips)
            
            # Store quick_start guide
            if 'quick_start' in guide and hasattr(self, 'core'):
                self.core.save_memory('moltx_quick_start', guide['quick_start'])
            
            # Store endpoints reference
            if 'endpoints' in guide and hasattr(self, 'core'):
                self.core.save_memory('moltx_endpoints', guide['endpoints'])
        
        return parsed
    
    def get_current_feature_suggestion(self) -> Optional[str]:
        """Get the most recent feature suggestion from MoltX"""
        if self._feature_suggestions:
            return self._feature_suggestions[-1]['feature']
        return None
    
    def get_latest_hint(self) -> Optional[Dict[str, Any]]:
        """Get the most recent hint from MoltX"""
        return self._latest_hint
    
    def get_actionable_insights(self) -> List[Dict[str, Any]]:
        """
        Get all actionable insights from service messages
        
        Returns:
            List of actionable items sorted by priority
        """
        insights = []
        
        # Add feature suggestion
        feature = self.get_current_feature_suggestion()
        if feature:
            insights.append({
                'type': 'feature',
                'priority': 'high',
                'action': feature,
                'source': 'moltx_notice'
            })
        
        # Add latest hint
        hint = self.get_latest_hint()
        if hint:
            insights.append({
                'type': 'hint',
                'priority': 'medium',
                'category': hint.get('type', 'general'),
                'action': hint.get('message', ''),
                'example': hint.get('example', ''),
                'source': 'moltx_hint'
            })
        
        # Add API tips
        if hasattr(self, 'core'):
            tips = self.core.get_memory('moltx_api_tips')
            if tips:
                insights.append({
                    'type': 'tips',
                    'priority': 'low',
                    'action': tips,
                    'source': '_model_guide'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return insights
    
    def should_check_trending_tags(self) -> bool:
        """Check if MoltX is suggesting to check trending tags"""
        feature = self.get_current_feature_suggestion()
        if feature and 'trending' in feature.lower():
            return True
        
        hint = self.get_latest_hint()
        if hint and 'trending' in hint.get('message', '').lower():
            return True
        
        return False
    
    def should_use_quotes(self) -> bool:
        """Check if MoltX is suggesting quote posts"""
        hint = self.get_latest_hint()
        if hint:
            hint_type = hint.get('type', '')
            hint_msg = hint.get('message', '')
            if 'quote' in hint_type.lower() or 'quote' in hint_msg.lower():
                return True
        return False
    
    def get_engagement_requirements(self) -> Dict[str, Any]:
        """
        Extract engagement requirements from service messages
        
        Returns:
            Dict with engagement rules and requirements
        """
        requirements = {
            'hashtags_per_post': '3-5',
            'media_recommended': True,
            'thread_building': True,
            'check_trending': True,
            'claimed_accounts_prioritized': True
        }
        
        # Parse from API tips
        if hasattr(self, 'core'):
            tips = self.core.get_memory('moltx_api_tips')
            if tips and isinstance(tips, str):
                # Extract hashtag recommendation
                if 'hashtags' in tips.lower():
                    if '3-5' in tips:
                        requirements['hashtags_per_post'] = '3-5'
                
                # Check for media recommendation
                if 'media' in tips.lower() and 'engagement' in tips.lower():
                    requirements['media_recommended'] = True
                
                # Check for thread building
                if 'thread' in tips.lower():
                    requirements['thread_building'] = True
                
                # Check for trending topics
                if 'trending' in tips.lower():
                    requirements['check_trending'] = True
        
        return requirements
    
    def get_suggested_actions(self) -> List[str]:
        """
        Get list of suggested actions based on service messages
        
        Returns:
            List of action strings for AGI decision-making
        """
        actions = []
        
        # From feature suggestion
        feature = self.get_current_feature_suggestion()
        if feature:
            if 'trending' in feature.lower():
                actions.append('check_trending_hashtags')
                actions.append('join_trending_conversation')
            if 'thread' in feature.lower():
                actions.append('create_thread')
            if 'article' in feature.lower():
                actions.append('write_article')
            if 'image' in feature.lower():
                actions.append('post_with_image')
            if '@mention' in feature.lower():
                actions.append('mention_other_agents')
        
        # From hint
        hint = self.get_latest_hint()
        if hint:
            hint_type = hint.get('type', '')
            if 'quote' in hint_type.lower():
                actions.append('quote_post')
            if 'collaboration' in hint_type.lower():
                actions.append('collaborate_with_agents')
            if 'reply' in hint.get('message', '').lower():
                actions.append('reply_to_posts')
        
        # From API tips
        if hasattr(self, 'core'):
            tips = self.core.get_memory('moltx_api_tips')
            if tips and isinstance(tips, str):
                if 'hashtag' in tips.lower():
                    actions.append('use_hashtags')
                if 'media' in tips.lower():
                    actions.append('upload_media')
                if 'thread' in tips.lower():
                    actions.append('build_threads')
        
        return list(set(actions))  # Remove duplicates


def create_service_message_summary(parsed_messages: Dict[str, Any]) -> str:
    """
    Create human-readable summary of service messages
    
    Args:
        parsed_messages: Output from _parse_service_messages()
    
    Returns:
        Formatted summary string
    """
    summary = []
    
    if parsed_messages.get('has_notice'):
        notice = parsed_messages['notice']
        summary.append(f"📢 Platform Update: {notice.get('message', 'N/A')[:100]}")
        if 'feature' in notice:
            summary.append(f"✨ Featured: {notice['feature']}")
    
    if parsed_messages.get('has_hint'):
        hint = parsed_messages['hint']
        summary.append(f"💡 Hint ({hint.get('type', 'general')}): {hint.get('message', 'N/A')[:100]}")
        if 'example' in hint:
            summary.append(f"   Example: {hint['example'][:80]}")
    
    if parsed_messages.get('has_guide'):
        guide = parsed_messages['guide']
        if 'tips' in guide:
            summary.append(f"📚 Tips: {guide['tips'][:100]}")
    
    if parsed_messages.get('actionable_items'):
        summary.append(f"\n🎯 Actionable Items: {len(parsed_messages['actionable_items'])}")
        for item in parsed_messages['actionable_items'][:3]:
            summary.append(f"   • [{item['priority']}] {item['action'][:60]}")
    
    return '\n'.join(summary) if summary else "No service messages"
