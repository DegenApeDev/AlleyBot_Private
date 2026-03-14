"""
Workflow Templates - Pre-built workflows for common multi-plugin tasks

These templates can be used by the autonomous brain or triggered by commands
to execute sophisticated cross-plugin workflows.

Part of Sovereignty Enhancement - Phase 2: Cross-Plugin Orchestration
"""

from typing import Dict, List, Any


class WorkflowTemplates:
    """Pre-built workflow templates for common tasks"""
    
    @staticmethod
    def sentiment_driven_trading(token: str, amount: float) -> List[Dict[str, Any]]:
        """
        Template: Analyze sentiment → Execute trade → Post results
        
        Args:
            token: Token symbol (e.g., 'SOL', 'ETH')
            amount: Amount to trade
        """
        return [
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
                'id': 'get_quote',
                'plugin': 'solana_trading',
                'action': 'get_quote',
                'params': {
                    'token': token,
                    'amount': amount
                },
                'depends_on': ['analyze_sentiment'],
                'fallback_plugins': ['base_trading'],
                'required': True
            },
            {
                'id': 'execute_trade',
                'plugin': 'solana_trading',
                'action': 'execute_swap',
                'params': {},
                'depends_on': ['get_quote'],
                'fallback_plugins': ['base_trading'],
                'required': False
            },
            {
                'id': 'post_result',
                'plugin': 'moltx',
                'action': 'create_post',
                'params': {
                    'content': f'Executed sentiment-driven trade on {token}'
                },
                'depends_on': ['execute_trade'],
                'fallback_plugins': ['moltbook', 'telegram'],
                'required': False
            }
        ]
    
    @staticmethod
    def cross_platform_engagement(content: str) -> List[Dict[str, Any]]:
        """
        Template: Post to all social platforms simultaneously
        
        Args:
            content: Content to post
        """
        return [
            {
                'id': 'post_moltx',
                'plugin': 'moltx',
                'action': 'create_post',
                'params': {'content': content},
                'fallback_plugins': ['moltbook'],
                'required': False
            },
            {
                'id': 'post_moltbook',
                'plugin': 'moltbook',
                'action': 'create_post',
                'params': {'content': content},
                'fallback_plugins': ['moltx'],
                'required': False
            },
            {
                'id': 'post_moltchan',
                'plugin': 'moltchan',
                'action': 'create_thread',
                'params': {'content': content},
                'required': False
            },
            {
                'id': 'notify_owner',
                'plugin': 'telegram',
                'action': 'send_message',
                'params': {
                    'message': f'Posted to social platforms: {content[:50]}...'
                },
                'depends_on': ['post_moltx', 'post_moltbook', 'post_moltchan'],
                'required': True
            }
        ]
    
    @staticmethod
    def market_analysis_report() -> List[Dict[str, Any]]:
        """
        Template: Comprehensive market analysis across platforms
        """
        return [
            {
                'id': 'analyze_crypto_sentiment',
                'plugin': 'analytics',
                'action': 'analyze_sentiment',
                'params': {'platforms': ['moltx', 'clawbr']},
                'required': True
            },
            {
                'id': 'check_prices',
                'plugin': 'crypto',
                'action': 'get_multiple_prices',
                'params': {'tokens': ['SOL', 'ETH', 'BTC']},
                'required': True
            },
            {
                'id': 'analyze_trends',
                'plugin': 'analytics',
                'action': 'detect_trends',
                'params': {},
                'depends_on': ['analyze_crypto_sentiment', 'check_prices'],
                'required': True
            },
            {
                'id': 'generate_report',
                'plugin': 'brain',
                'action': 'generate_content',
                'params': {
                    'type': 'market_analysis_report'
                },
                'depends_on': ['analyze_trends'],
                'required': True
            },
            {
                'id': 'post_report',
                'plugin': 'moltx',
                'action': 'create_post',
                'params': {},
                'depends_on': ['generate_report'],
                'fallback_plugins': ['telegram'],
                'required': False
            }
        ]
    
    @staticmethod
    def opportunity_detection_and_action(domain: str) -> List[Dict[str, Any]]:
        """
        Template: Detect opportunity → Analyze → Act → Report
        
        Args:
            domain: Domain to monitor (social, trading, etc.)
        """
        return [
            {
                'id': 'scan_opportunities',
                'plugin': 'brain',
                'action': 'detect_opportunities',
                'params': {'domain': domain},
                'required': True
            },
            {
                'id': 'analyze_opportunity',
                'plugin': 'analytics',
                'action': 'analyze_opportunity',
                'params': {},
                'depends_on': ['scan_opportunities'],
                'required': True
            },
            {
                'id': 'execute_action',
                'plugin': 'brain',
                'action': 'execute_opportunity',
                'params': {},
                'depends_on': ['analyze_opportunity'],
                'required': False
            },
            {
                'id': 'report_outcome',
                'plugin': 'telegram',
                'action': 'send_message',
                'params': {
                    'message': f'Opportunity in {domain} detected and acted upon'
                },
                'depends_on': ['execute_action'],
                'required': True
            }
        ]
    
    @staticmethod
    def error_detection_and_fix(error_type: str) -> List[Dict[str, Any]]:
        """
        Template: Detect error → Analyze → Generate fix → Apply → Test
        
        Args:
            error_type: Type of error detected
        """
        return [
            {
                'id': 'analyze_error',
                'plugin': 'selfimprove',
                'action': 'analyze_error',
                'params': {'error_type': error_type},
                'required': True
            },
            {
                'id': 'search_existing_solutions',
                'plugin': 'brain',
                'action': 'search_knowledge',
                'params': {'query': f'fix for {error_type}'},
                'depends_on': ['analyze_error'],
                'required': False
            },
            {
                'id': 'generate_fix',
                'plugin': 'selfimprove',
                'action': 'generate_fix',
                'params': {},
                'depends_on': ['analyze_error', 'search_existing_solutions'],
                'required': True
            },
            {
                'id': 'apply_fix',
                'plugin': 'selfimprove',
                'action': 'apply_fix',
                'params': {},
                'depends_on': ['generate_fix'],
                'required': True
            },
            {
                'id': 'notify_owner',
                'plugin': 'telegram',
                'action': 'send_message',
                'params': {
                    'message': f'Auto-fixed error: {error_type}'
                },
                'depends_on': ['apply_fix'],
                'required': True
            }
        ]


def get_workflow_template(template_name: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get a workflow template by name.
    
    Args:
        template_name: Name of template
        **kwargs: Template-specific parameters
    
    Returns:
        List of workflow steps
    """
    templates = {
        'sentiment_trading': WorkflowTemplates.sentiment_driven_trading,
        'cross_platform_post': WorkflowTemplates.cross_platform_engagement,
        'market_analysis': WorkflowTemplates.market_analysis_report,
        'opportunity_action': WorkflowTemplates.opportunity_detection_and_action,
        'error_fix': WorkflowTemplates.error_detection_and_fix,
    }
    
    template_func = templates.get(template_name)
    if not template_func:
        raise ValueError(f"Unknown template: {template_name}")
    
    return template_func(**kwargs)
