"""
Example: Sentiment → Trading → Social Workflow

Demonstrates the Cross-Plugin Orchestrator executing a complex workflow
that spans multiple plugins with automatic failover and dependency resolution.

This is the concrete example from the System Scan Report.
"""

import asyncio
from src.agentic.cross_plugin_orchestrator import create_cross_plugin_orchestrator


async def sentiment_trading_social_example(agi_kernel):
    """
    Execute a workflow that:
    1. Analyzes market sentiment
    2. Executes a trade if conditions are favorable
    3. Posts about the trade on social media
    """
    
    # Create orchestrator
    orchestrator = create_cross_plugin_orchestrator(agi_kernel)
    
    # Define workflow steps
    workflow_steps = [
        {
            'id': 'analyze_sentiment',
            'plugin': 'analytics',
            'action': 'analyze_sentiment',
            'params': {
                'token': 'SOL',
                'platforms': ['moltx', 'clawbr', 'telegram']
            },
            'depends_on': [],
            'required': True
        },
        {
            'id': 'check_price',
            'plugin': 'crypto',
            'action': 'get_price',
            'params': {
                'token': 'SOL'
            },
            'depends_on': [],
            'required': True
        },
        {
            'id': 'get_trading_quote',
            'plugin': 'solana_trading',
            'action': 'get_quote',
            'params': {
                'token': 'SOL',
                'amount': 0.1,
                # Will receive sentiment data from step 1
            },
            'depends_on': ['analyze_sentiment', 'check_price'],
            'fallback_plugins': ['base_trading', 'avax_trading'],
            'required': True
        },
        {
            'id': 'execute_trade',
            'plugin': 'solana_trading',
            'action': 'execute_swap',
            'params': {
                # Will receive quote from step 3
            },
            'depends_on': ['get_trading_quote'],
            'fallback_plugins': ['base_trading'],
            'required': False  # Continue even if trade fails
        },
        {
            'id': 'record_trade',
            'plugin': 'analytics',
            'action': 'record_trade',
            'params': {
                'strategy': 'sentiment_momentum',
                # Will receive trade result from step 4
            },
            'depends_on': ['execute_trade'],
            'required': False
        },
        {
            'id': 'post_to_social',
            'plugin': 'moltx',
            'action': 'create_post',
            'params': {
                'content': 'Just executed a sentiment-driven trade on SOL!',
                # Will receive trade details from step 4
            },
            'depends_on': ['execute_trade'],
            'fallback_plugins': ['moltbook', 'telegram'],
            'required': False  # Social posting is optional
        }
    ]
    
    # Create workflow
    workflow = orchestrator.create_workflow(
        name="Sentiment-Driven Trading with Social Update",
        description="Analyze sentiment, execute trade if favorable, post results",
        steps=workflow_steps
    )
    
    # Execute workflow
    print("🚀 Starting Sentiment → Trading → Social workflow...")
    result = await orchestrator.execute_workflow(workflow)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Workflow Results:")
    print(f"{'='*60}")
    print(f"Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    print(f"Completed Steps: {result['completed_steps']}/{result['completed_steps'] + result['failed_steps']}")
    print(f"\nStep Details:")
    
    for step_id, step_result in result['results'].items():
        status = '✅' if step_result['success'] else '❌'
        print(f"  {status} {step_id}")
        if 'used_fallback' in step_result:
            print(f"     (used fallback: {step_result['used_fallback']})")
    
    if result['errors']:
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  ❌ {error}")
    
    return result


async def simple_multi_platform_post_example(agi_kernel):
    """
    Simpler example: Post to multiple platforms with automatic failover.
    """
    
    orchestrator = create_cross_plugin_orchestrator(agi_kernel)
    
    content = "AlleyBot is now fully sovereign with cross-plugin orchestration! 🚀"
    
    workflow_steps = [
        {
            'id': 'post_moltx',
            'plugin': 'moltx',
            'action': 'create_post',
            'params': {'content': content},
            'fallback_plugins': ['moltbook', 'moltchan'],
            'required': False
        },
        {
            'id': 'post_clawbr',
            'plugin': 'clawbr',
            'action': 'create_post',
            'params': {'content': content},
            'fallback_plugins': ['moltx'],
            'required': False
        },
        {
            'id': 'notify_owner',
            'plugin': 'telegram',
            'action': 'send_message',
            'params': {
                'message': f"Posted to social platforms: {content}"
            },
            'depends_on': ['post_moltx', 'post_clawbr'],
            'required': True
        }
    ]
    
    workflow = orchestrator.create_workflow(
        name="Multi-Platform Social Post",
        description="Post to multiple platforms with automatic failover",
        steps=workflow_steps
    )
    
    result = await orchestrator.execute_workflow(workflow)
    
    print(f"\n✅ Posted to {result['completed_steps']} platforms")
    return result


# Usage example (would be called from autonomous brain or command)
if __name__ == "__main__":
    # This would normally be called with the actual AGI Kernel instance
    print("This is an example file. Import and use with actual AGI Kernel.")
    print("\nExample usage:")
    print("  from examples.sentiment_trading_social_workflow import sentiment_trading_social_example")
    print("  result = await sentiment_trading_social_example(agi_kernel)")
