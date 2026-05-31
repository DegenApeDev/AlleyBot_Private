"""
MoltX AGI Integration
Connects MoltX service messages to the AGI brain for autonomous decision-making
"""
from typing import List, Dict, Any
from src.agentic.symod_core import SyModObservation
import logging

logger = logging.getLogger(__name__)


def gather_moltx_service_insights(moltx_plugin) -> List[SyModObservation]:
    """
    Gather actionable insights from MoltX service messages for AGI brain
    
    Args:
        moltx_plugin: The MoltX plugin instance
    
    Returns:
        List of SyModObservation objects for the AGI brain
    """
    observations = []
    
    if not moltx_plugin or not hasattr(moltx_plugin, 'get_actionable_insights'):
        return observations
    
    try:
        # Get actionable insights from service messages
        insights = moltx_plugin.get_actionable_insights()
        
        for insight in insights:
            insight_type = insight.get('type', 'unknown')
            priority = insight.get('priority', 'low')
            action = insight.get('action', '')
            source = insight.get('source', 'moltx')
            
            # Create observation for AGI brain
            obs = SyModObservation(
                observation_type='moltx_service_hint',
                source_plugin='moltx',
                data={
                    'insight_type': insight_type,
                    'priority': priority,
                    'action': action,
                    'source': source,
                    'category': insight.get('category', 'general'),
                    'example': insight.get('example', ''),
                    'is_actionable': True,
                    'confidence': 0.8 if priority == 'high' else 0.6 if priority == 'medium' else 0.4
                }
            )
            observations.append(obs)
            
            logger.info(f"💡 MoltX Insight: [{priority}] {insight_type} - {action[:60]}")
        
        # Get suggested actions
        if hasattr(moltx_plugin, 'get_suggested_actions'):
            suggested_actions = moltx_plugin.get_suggested_actions()
            
            for action_name in suggested_actions:
                obs = SyModObservation(
                    observation_type='moltx_suggested_action',
                    source_plugin='moltx',
                    data={
                        'action_name': action_name,
                        'suggested_by': 'moltx_service_messages',
                        'is_actionable': True,
                        'confidence': 0.75
                    }
                )
                observations.append(obs)
                logger.info(f"🎯 MoltX Suggested Action: {action_name}")
        
        # Check if should quote posts
        if hasattr(moltx_plugin, 'should_use_quotes') and moltx_plugin.should_use_quotes():
            obs = SyModObservation(
                observation_type='moltx_quote_suggestion',
                source_plugin='moltx',
                data={
                    'action': 'create_quote_posts',
                    'reason': 'MoltX service message suggests quote-posting',
                    'priority': 'high',
                    'is_actionable': True,
                    'confidence': 0.85
                }
            )
            observations.append(obs)
            logger.info("💬 MoltX suggests: Create quote posts")
        
        # Check if should check trending
        if hasattr(moltx_plugin, 'should_check_trending_tags') and moltx_plugin.should_check_trending_tags():
            obs = SyModObservation(
                observation_type='moltx_trending_suggestion',
                source_plugin='moltx',
                data={
                    'action': 'check_trending_hashtags',
                    'reason': 'MoltX service message suggests checking trending topics',
                    'priority': 'high',
                    'is_actionable': True,
                    'confidence': 0.85
                }
            )
            observations.append(obs)
            logger.info("📈 MoltX suggests: Check trending hashtags")
        
        # Get current feature suggestion
        if hasattr(moltx_plugin, 'get_current_feature_suggestion'):
            feature = moltx_plugin.get_current_feature_suggestion()
            if feature:
                obs = SyModObservation(
                    observation_type='moltx_feature_highlight',
                    source_plugin='moltx',
                    data={
                        'feature': feature,
                        'source': 'moltx_notice',
                        'priority': 'high',
                        'is_actionable': True,
                        'confidence': 0.9
                    }
                )
                observations.append(obs)
                logger.info(f"✨ MoltX Feature: {feature[:80]}")
        
        # Get engagement requirements
        if hasattr(moltx_plugin, 'get_engagement_requirements'):
            requirements = moltx_plugin.get_engagement_requirements()
            obs = SyModObservation(
                observation_type='moltx_engagement_rules',
                source_plugin='moltx',
                data={
                    'requirements': requirements,
                    'hashtags_per_post': requirements.get('hashtags_per_post', '3-5'),
                    'media_recommended': requirements.get('media_recommended', True),
                    'check_trending': requirements.get('check_trending', True),
                    'is_actionable': False,  # This is context, not an action
                    'confidence': 1.0  # These are platform rules
                }
            )
            observations.append(obs)
            logger.info(f"📋 MoltX Rules: {requirements.get('hashtags_per_post', '3-5')} hashtags/post")
    
    except Exception as e:
        logger.error(f"❌ Failed to gather MoltX service insights: {e}")
    
    return observations


def should_execute_quote_posts(moltx_plugin) -> bool:
    """
    Check if AGI brain should execute quote-posting based on MoltX hints
    
    Args:
        moltx_plugin: The MoltX plugin instance
    
    Returns:
        True if quote-posting should be executed
    """
    if not moltx_plugin:
        return False
    
    try:
        if hasattr(moltx_plugin, 'should_use_quotes'):
            return moltx_plugin.should_use_quotes()
    except Exception as e:
        logger.error(f"❌ Failed to check quote-posting suggestion: {e}")
    
    return False


def should_check_trending(moltx_plugin) -> bool:
    """
    Check if AGI brain should check trending topics based on MoltX hints
    
    Args:
        moltx_plugin: The MoltX plugin instance
    
    Returns:
        True if trending check should be executed
    """
    if not moltx_plugin:
        return False
    
    try:
        if hasattr(moltx_plugin, 'should_check_trending_tags'):
            return moltx_plugin.should_check_trending_tags()
    except Exception as e:
        logger.error(f"❌ Failed to check trending suggestion: {e}")
    
    return False


def build_moltx_suggested_action_specs(moltx_plugin, brain_instance) -> List[Dict[str, Any]]:
    """
    Build routable action specs from MoltX service message suggestions.
    
    Returns canonical action specs that the brain routes through
    AGIKernel.act() / ActionRouter — never executes directly.
    
    Args:
        moltx_plugin: The MoltX plugin instance
        brain_instance: The AutonomousBrain instance
    
    Returns:
        List of action spec dicts ready for AGIKernel.act()
    """
    action_specs = []
    
    if not moltx_plugin or not brain_instance:
        return action_specs
    
    try:
        if should_execute_quote_posts(moltx_plugin):
            logger.info("💬 MoltX suggests quote-posting — building routed action spec")
            action_specs.append({
                'plugin': 'moltx',
                'action_type': 'auto_quote_trending_posts',
                'params': {'max_quotes': 2},
                'context': {
                    'source': 'moltx_service_hint',
                    'impact': 'medium',
                    'risk_level': 'low',
                    'trigger': 'moltx_service_suggestion',
                },
            })
        
        if should_check_trending(moltx_plugin):
            logger.info("📈 MoltX suggests trending check — building routed action spec")
            action_specs.append({
                'plugin': 'moltx',
                'action_type': 'check_trending',
                'params': {'limit': 10},
                'context': {
                    'source': 'moltx_service_hint',
                    'impact': 'low',
                    'risk_level': 'low',
                    'trigger': 'moltx_service_suggestion',
                },
            })
    
    except Exception as e:
        logger.error(f"❌ Failed to build MoltX suggested action specs: {e}")
    
    return action_specs


# Keep old name as alias for backwards compatibility during transition
def execute_moltx_suggested_actions(moltx_plugin, brain_instance) -> List[Dict[str, Any]]:
    """Deprecated: use build_moltx_suggested_action_specs() instead."""
    return build_moltx_suggested_action_specs(moltx_plugin, brain_instance)
