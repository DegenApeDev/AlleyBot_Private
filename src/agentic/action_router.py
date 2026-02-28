"""
Action Router - Unified action execution pipeline for AGI Kernel

This is the SINGLE entry point for all actions in AlleyBot.
Every action flows through here to ensure:
- AGI Kernel validation
- SyMod mathematical verification
- Episodic memory recording
- Learning from outcomes
- Goal progress tracking

This replaces scattered action execution across plugins.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime


class ActionRouter:
    """
    Single entry point for all actions.
    
    Ensures every action goes through:
    1. AGI Kernel validation (goals, timing, strategy)
    2. SyMod verification (mathematical truth)
    3. Plugin execution (actual work)
    4. Outcome reflection (learning)
    """
    
    def __init__(self, agi_kernel, plugin_manager):
        """
        Initialize action router.
        
        Args:
            agi_kernel: AGI Kernel instance for validation/learning
            plugin_manager: Plugin manager for execution
        """
        self.agi = agi_kernel
        self.plugins = plugin_manager
        self.execution_history = []
        
        print("✅ Action Router initialized - all actions will flow through AGI Kernel")
    
    async def route_action(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route action through complete AGI pipeline.
        
        Flow:
        1. Validate with AGI Kernel (strategy, timing, goals)
        2. Verify with SyMod (mathematical truth for high-impact)
        3. Execute via plugin
        4. Reflect and learn from outcome
        
        Args:
            action_spec: Action specification with:
                - plugin: Plugin name (e.g., 'moltx')
                - action_type: Action to execute (e.g., 'create_post')
                - params: Parameters for action
                - context: Additional context (user_requested, etc.)
        
        Returns:
            Result dict with success, data, and learning metadata
        """
        start_time = datetime.now()
        action_id = f"{action_spec.get('plugin', 'unknown')}:{action_spec.get('action_type', 'unknown')}"
        
        print(f"🔄 Routing action: {action_id}")
        
        # Step 1: AGI Kernel validation
        validation = await self._validate_with_agi(action_spec)
        if not validation['approved']:
            return {
                'success': False,
                'reason': validation['reason'],
                'stage': 'agi_validation',
                'action_id': action_id
            }
        
        # Step 2: SyMod verification (for high-impact actions)
        if action_spec.get('context', {}).get('impact') == 'high':
            symod_check = self._verify_with_symod(action_spec, validation)
            if not symod_check['approved']:
                return {
                    'success': False,
                    'reason': symod_check['reason'],
                    'stage': 'symod_verification',
                    'action_id': action_id,
                    'symod_details': symod_check
                }
        
        # Step 3: Execute via plugin
        try:
            result = await self._execute_via_plugin(action_spec)
            
            # Step 4: Reflect and learn
            await self._reflect_on_outcome(action_spec, result, validation)
            
            # Add metadata
            result['action_id'] = action_id
            result['execution_time_ms'] = (datetime.now() - start_time).total_seconds() * 1000
            result['routed_through_agi'] = True
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'stage': 'execution',
                'action_id': action_id
            }
            
            # Learn from failure
            await self._reflect_on_outcome(action_spec, error_result, validation)
            
            return error_result
    
    async def _validate_with_agi(self, action_spec: Dict) -> Dict:
        """
        Validate action with AGI Kernel.
        
        Checks:
        - Alignment with active goals
        - Timing appropriateness
        - Strategic value
        - Behavior modulation from episodic memory
        """
        context = action_spec.get('context', {})
        
        # Check if user requested (always approve user requests)
        if context.get('user_requested'):
            return {
                'approved': True,
                'reason': 'User requested action',
                'modulations': {}
            }
        
        # Check with decision system if available
        if hasattr(self.agi, 'decision_system'):
            # Get behavior modulation from episodic memory
            modulations = {}
            if hasattr(self.agi, 'behavior_modulator'):
                modulations = self.agi.behavior_modulator.get_effective_params(
                    action_spec.get('action_type', '')
                )
            
            # Check timing and strategy
            action_type = action_spec.get('action_type', '')
            platform = action_spec.get('plugin', '')
            
            # For content posts, check content strategy
            if action_type in ['create_post', 'post_text', 'post_article']:
                if hasattr(self.agi, 'content_intelligence'):
                    content_check = self.agi.content_intelligence.should_post_now(
                        platform=platform,
                        action_type=action_type
                    )
                    if not content_check.get('should_post'):
                        return {
                            'approved': False,
                            'reason': content_check.get('reason', 'Content strategy blocked'),
                            'modulations': modulations
                        }
            
            return {
                'approved': True,
                'reason': 'AGI validation passed',
                'modulations': modulations
            }
        
        # No decision system - approve by default
        return {
            'approved': True,
            'reason': 'No decision system available',
            'modulations': {}
        }
    
    def _verify_with_symod(self, action_spec: Dict, validation: Dict) -> Dict:
        """
        Verify action with SyMod mathematical framework.
        
        High-impact actions must pass mathematical validation.
        """
        if hasattr(self.agi, 'decision_system'):
            return self.agi.decision_system.validate_with_symod(
                action=action_spec,
                context=action_spec.get('context', {})
            )
        
        return {'approved': True, 'reason': 'SyMod not available'}
    
    async def _execute_via_plugin(self, action_spec: Dict) -> Dict:
        """
        Execute action via appropriate plugin.
        
        This is where the actual work happens.
        """
        plugin_name = action_spec.get('plugin')
        action_type = action_spec.get('action_type')
        params = action_spec.get('params', {})
        
        # Get plugin
        plugin = self.plugins.plugins.get(plugin_name)
        if not plugin:
            return {
                'success': False,
                'error': f'Plugin {plugin_name} not loaded'
            }
        
        # Execute action
        if hasattr(plugin, 'execute_action'):
            # New-style plugin with execute_action method
            result = await plugin.execute_action(action_type, params)
        else:
            # Old-style plugin - call method directly
            method = getattr(plugin, action_type, None)
            if not method:
                return {
                    'success': False,
                    'error': f'Action {action_type} not found in plugin {plugin_name}'
                }
            
            # Call method
            if asyncio.iscoroutinefunction(method):
                result = await method(**params)
            else:
                result = method(**params)
            
            # Normalize result to dict
            if not isinstance(result, dict):
                result = {'success': True, 'data': result}
        
        return result
    
    async def _reflect_on_outcome(self, action_spec: Dict, result: Dict, validation: Dict):
        """
        Reflect on action outcome and learn.
        
        This is the AGI feedback loop - every outcome improves future decisions.
        """
        action_id = f"{action_spec.get('plugin')}:{action_spec.get('action_type')}"
        success = result.get('success', False)
        
        # Record in execution history
        self.execution_history.append({
            'action_id': action_id,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'result_summary': str(result)[:200]
        })
        
        # Keep history manageable
        self.execution_history = self.execution_history[-100:]
        
        # Learn through AGI Kernel
        if hasattr(self.agi, 'learn'):
            self.agi.learn(
                context=action_id,
                action=action_spec.get('action_type', ''),
                outcome=str(result)[:100],
                success=success,
                user_id=action_spec.get('context', {}).get('user_id')
            )
        
        # Update goal progress if action was goal-driven
        goal_id = action_spec.get('context', {}).get('goal_id')
        if goal_id and hasattr(self.agi, 'goal_manager'):
            self.agi.goal_manager.complete_action(
                goal_id=goal_id,
                success=success,
                outcome=str(result)[:100]
            )
        
        # Record in decision system
        if hasattr(self.agi, 'decision_system'):
            self.agi.decision_system.record_action(action_id, result)
    
    def get_execution_stats(self) -> Dict:
        """Get statistics about action execution"""
        if not self.execution_history:
            return {'total': 0, 'success_rate': 0.0}
        
        total = len(self.execution_history)
        successes = sum(1 for e in self.execution_history if e.get('success'))
        
        return {
            'total': total,
            'successes': successes,
            'failures': total - successes,
            'success_rate': successes / total if total > 0 else 0.0,
            'recent_actions': self.execution_history[-5:]
        }


def create_action_router(agi_kernel, plugin_manager):
    """Factory function to create action router"""
    return ActionRouter(agi_kernel, plugin_manager)
