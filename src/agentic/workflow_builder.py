"""
Workflow Builder - Converts goal patterns into executable workflows

Bridges the gap between Decision System's workflow detection and
Cross-Plugin Orchestrator's execution engine.

Part of Sovereignty Enhancement - Autonomous Multi-Step Execution
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """
    Builds executable workflows from goal patterns and context.
    
    Takes high-level workflow specifications from Decision System and
    converts them into concrete step sequences for the Orchestrator.
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.command_registry = None
        if agi_kernel and hasattr(agi_kernel, 'command_registry'):
            self.command_registry = agi_kernel.command_registry
    
    def build_workflow_from_spec(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build executable workflow from specification.
        
        Args:
            workflow_spec: Workflow specification from Decision System
        
        Returns:
            Workflow dict ready for orchestrator execution
        """
        workflow_type = workflow_spec.get('workflow_type')
        goal = workflow_spec.get('goal', {})
        pattern = workflow_spec.get('pattern', {})
        
        # Route to appropriate builder
        if workflow_type == 'image_post':
            return self._build_image_post_workflow(goal, pattern)
        elif workflow_type == 'sentiment_trading':
            return self._build_sentiment_trading_workflow(goal, pattern)
        elif workflow_type == 'market_analysis_post':
            return self._build_market_analysis_workflow(goal, pattern)
        elif workflow_type == 'cross_platform_engagement':
            return self._build_cross_platform_engagement_workflow(goal, pattern)
        elif workflow_type == 'custom_multi_step':
            return self._build_custom_workflow(goal, pattern)
        else:
            logger.warning(f"Unknown workflow type: {workflow_type}")
            return self._build_fallback_workflow(goal)
    
    def _build_image_post_workflow(self, goal: Dict, pattern: Dict) -> Dict[str, Any]:
        """Build workflow for image generation + posting"""
        goal_desc = goal.get('description', '')
        
        # Extract topic from goal
        topic = goal_desc.replace('image', '').replace('post', '').strip()
        if not topic:
            topic = "AlleyBot's autonomous capabilities"
        
        # Determine target platform
        platform = 'moltx'  # Default
        for plat in ['moltbook', 'clawbr', 'telegram']:
            if plat in goal_desc.lower():
                platform = plat
                break
        
        steps = [
            {
                'id': 'generate_image',
                'plugin': 'grok_ai',
                'action': 'generate_image',
                'params': {'prompt': topic},
                'required': True
            },
            {
                'id': 'post_with_image',
                'plugin': platform,
                'action': 'create_post',
                'params': {
                    'content': f"Check out this visualization: {topic}",
                    # Image URL will be injected from previous step
                },
                'depends_on': ['generate_image'],
                'fallback_plugins': ['moltbook', 'telegram'] if platform == 'moltx' else [],
                'required': True
            }
        ]
        
        return {
            'name': f"Image Post to {platform.upper()}",
            'description': f"Generate image and post to {platform}",
            'steps': steps,
            'workflow_type': 'image_post'
        }
    
    def _build_sentiment_trading_workflow(self, goal: Dict, pattern: Dict) -> Dict[str, Any]:
        """Build workflow for sentiment analysis → trading → posting"""
        goal_desc = goal.get('description', '')
        
        # Extract token from goal
        token = 'SOL'  # Default
        for t in ['BTC', 'ETH', 'SOL', 'BASE']:
            if t.lower() in goal_desc.lower():
                token = t
                break
        
        steps = [
            {
                'id': 'analyze_sentiment',
                'plugin': 'analytics',
                'action': 'analyze_sentiment',
                'params': {
                    'token': token,
                    'platforms': ['moltx', 'clawbr']
                },
                'required': True
            },
            {
                'id': 'check_price',
                'plugin': 'crypto',
                'action': 'get_price',
                'params': {'token': token},
                'required': True
            },
            {
                'id': 'get_quote',
                'plugin': 'solana_trading',
                'action': 'get_quote',
                'params': {
                    'token': token,
                    'amount': 0.1
                },
                'depends_on': ['analyze_sentiment', 'check_price'],
                'fallback_plugins': ['base_trading'],
                'required': False  # Trading is optional
            },
            {
                'id': 'post_analysis',
                'plugin': 'moltx',
                'action': 'create_post',
                'params': {
                    'content': f"Market analysis for {token}"
                },
                'depends_on': ['analyze_sentiment', 'check_price'],
                'fallback_plugins': ['telegram'],
                'required': True
            }
        ]
        
        return {
            'name': f"Sentiment Trading: {token}",
            'description': f"Analyze sentiment and trade {token}",
            'steps': steps,
            'workflow_type': 'sentiment_trading'
        }
    
    def _build_market_analysis_workflow(self, goal: Dict, pattern: Dict) -> Dict[str, Any]:
        """Build workflow for market analysis + reporting"""
        steps = [
            {
                'id': 'check_prices',
                'plugin': 'crypto',
                'action': 'get_multiple_prices',
                'params': {'tokens': ['BTC', 'ETH', 'SOL']},
                'required': True
            },
            {
                'id': 'analyze_trends',
                'plugin': 'analytics',
                'action': 'detect_trends',
                'params': {},
                'depends_on': ['check_prices'],
                'required': True
            },
            {
                'id': 'generate_report',
                'plugin': 'brain',
                'action': 'generate_content',
                'params': {'type': 'market_analysis'},
                'depends_on': ['analyze_trends'],
                'required': True
            },
            {
                'id': 'post_report',
                'plugin': 'moltx',
                'action': 'create_post',
                'params': {},
                'depends_on': ['generate_report'],
                'fallback_plugins': ['moltbook', 'telegram'],
                'required': True
            }
        ]
        
        return {
            'name': "Market Analysis Report",
            'description': "Comprehensive market analysis and reporting",
            'steps': steps,
            'workflow_type': 'market_analysis_post'
        }
    
    def _build_cross_platform_engagement_workflow(self, goal: Dict, pattern: Dict) -> Dict[str, Any]:
        """Build workflow for engaging across multiple platforms"""
        platforms = ['moltx', 'moltbook', 'moltchan']
        
        steps = []
        for i, platform in enumerate(platforms):
            steps.append({
                'id': f'engage_{platform}',
                'plugin': platform,
                'action': 'engage_with_feed',
                'params': {'count': 5},
                'required': False  # Each platform is optional
            })
        
        # Add notification step
        steps.append({
            'id': 'notify_completion',
            'plugin': 'telegram',
            'action': 'send_message',
            'params': {
                'message': f"Engaged across {len(platforms)} platforms"
            },
            'depends_on': [f'engage_{p}' for p in platforms],
            'required': True
        })
        
        return {
            'name': "Cross-Platform Engagement",
            'description': "Engage with feeds across multiple platforms",
            'steps': steps,
            'workflow_type': 'cross_platform_engagement'
        }
    
    def _build_custom_workflow(self, goal: Dict, pattern: Dict) -> Dict[str, Any]:
        """Build custom workflow from goal description using command registry"""
        goal_desc = goal.get('description', '')
        
        # Use command registry to find relevant commands
        if self.command_registry:
            commands = self.command_registry.search_semantic(goal_desc, top_k=5)
            
            steps = []
            for i, cmd in enumerate(commands):
                steps.append({
                    'id': f'step_{i}',
                    'plugin': cmd.plugin,
                    'action': cmd.function_name,
                    'params': {},
                    'required': i == 0  # First step required, rest optional
                })
            
            return {
                'name': "Custom Workflow",
                'description': goal_desc,
                'steps': steps,
                'workflow_type': 'custom_multi_step'
            }
        
        return self._build_fallback_workflow(goal)
    
    def _build_fallback_workflow(self, goal: Dict) -> Dict[str, Any]:
        """Fallback workflow when pattern detection fails"""
        return {
            'name': "Single Action Workflow",
            'description': goal.get('description', 'Execute goal'),
            'steps': [
                {
                    'id': 'execute_goal',
                    'plugin': 'brain',
                    'action': 'execute_goal',
                    'params': {'goal': goal},
                    'required': True
                }
            ],
            'workflow_type': 'fallback'
        }


def create_workflow_builder(agi_kernel) -> WorkflowBuilder:
    """Create workflow builder instance"""
    return WorkflowBuilder(agi_kernel)
