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
import inspect

from src.agentic.action_logger import get_action_logger
from src.agentic.planning import get_plan_manager


from src.agentic.contracts import (
    ActionEnvelope,
    ActionOutcome,
    ValidationProfile,
    PredictionRecord,
    PredictionEvaluation,
    ImpactLevel,
    RiskLevel,
    TrustLevel,
    action_spec_to_envelope,
    envelope_to_action_spec,
)


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
        self.plan_manager = get_plan_manager()
        
        print("✅ Action Router initialized - all actions will flow through AGI Kernel")

    def _normalize_action_family(self, action_spec: Dict[str, Any]) -> str:
        """Collapse concrete action types into broader action-family labels for trust persistence."""
        action_type = str(action_spec.get('action_type', '') or '').lower()
        if 'post' in action_type or 'content' in action_type:
            return 'post'
        if 'engage' in action_type or 'reply' in action_type:
            return 'engage'
        if 'analy' in action_type or 'report' in action_type or 'research' in action_type:
            return 'analyze'
        if 'fix' in action_type or 'repair' in action_type or 'retry' in action_type:
            return 'fix'
        return action_type or 'unknown'

    def _refresh_action_family_trust_from_outcome(
        self,
        action_spec: Dict[str, Any],
        result: Dict[str, Any],
        prediction_evaluation: Dict[str, Any],
    ) -> None:
        """Update persisted action-family trust from routed outcome evidence."""
        action_family = self._normalize_action_family(action_spec)
        if not action_family or action_family == 'unknown':
            return

        existing = self.plan_manager.get_action_family_states().get(action_family, {})
        existing_degradation = float(existing.get('degradation_score', 0.0) or 0.0)
        existing_recovery = float(existing.get('recovery_score', 0.0) or 0.0)
        mismatch_score = float(prediction_evaluation.get('mismatch_score', 0.0) or 0.0)
        success = bool(result.get('success', False))

        if success:
            recovery_score = min(max(existing_recovery, 0.0) + max(0.2, (1.0 - mismatch_score) * 0.3), 1.0)
            degradation_score = max(existing_degradation * 0.7, 0.0)
            cooldown_until = None
        else:
            recovery_score = max(existing_recovery * 0.5, 0.0)
            degradation_score = min(max(existing_degradation, mismatch_score) + 0.15, 1.0)
            cooldown_until = datetime.now()

        trust_bucket = self.plan_manager._derive_trust_bucket(
            degradation_score=degradation_score,
            recovery_score=recovery_score,
            cooldown_until=cooldown_until,
        )
        self.plan_manager.update_action_family_state(
            action_family=action_family,
            trust_bucket=trust_bucket,
            degradation_score=degradation_score,
            recovery_score=recovery_score,
            cooldown_until=cooldown_until,
            last_plan_id=(action_spec.get('context', {}) or {}).get('plan_id'),
            metadata={
                'source': 'action_router_outcome',
                'plugin': action_spec.get('plugin'),
                'action_type': action_spec.get('action_type'),
                'success': success,
                'mismatch_score': mismatch_score,
                'recent_performance': {
                    'confidence_calibration': prediction_evaluation.get('confidence_calibration'),
                    'value_alignment': prediction_evaluation.get('value_alignment'),
                    'risk_alignment': prediction_evaluation.get('risk_alignment'),
                },
            },
        )

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
    
    def _verify_with_symod(self, action_spec: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify action through SyMod mathematical validation.
        
        This provides physics-based truth validation for high-impact actions.
        """
        symod_manager = getattr(self.agi, 'symod', None)
        
        if not symod_manager or not symod_manager.enabled:
            return {
                'approved': True,
                'reason': 'SyMod validation skipped (not available)',
                'details': {'symod_available': False}
            }
        
        try:
            # Build SyMod observation from action
            from src.agentic.symod_core import SyModObservation
            
            observation = SyModObservation(
                observation_type='action_proposal',
                source_plugin=action_spec.get('plugin', 'unknown'),
                content=str(action_spec.get('params', {})),
                metadata={
                    'action_type': action_spec.get('action_type'),
                    'context': action_spec.get('context', {}),
                    'validation': validation,
                }
            )
            
            # Submit to SyMod for validation
            symod_manager.observe(observation)
            
            # For now, SyMod observation is informational
            # Actual validation happens through Synergy field
            return {
                'approved': True,
                'reason': 'SyMod observation recorded',
                'details': {
                    'symod_enabled': True,
                    'observation_recorded': True,
                }
            }
            
        except Exception as e:
            # Fail open for SyMod errors to avoid blocking actions
            return {
                'approved': True,
                'reason': f'SyMod validation skipped due to error: {e}',
                'error': str(e),
                'details': {'symod_error': True}
            }
    
    def _validate_with_synergy(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action through the centralized Synergy field gate when available."""
        decision_system = getattr(self.agi, 'decision_system', None)
        synergy_engine = getattr(decision_system, 'synergy_engine', None) if decision_system else None
        validation_profile = self._get_validation_profile(action_spec)
        
        if not synergy_engine:
            if validation_profile['requires_strict_validation']:
                return {
                    'approved': False,
                    'reason': 'Synergy not available for strict-validation action',
                    'error': 'synergy_unavailable',
                }
            return {'approved': True, 'reason': 'Synergy not available'}
        
        action_name = action_spec.get('action_type') or action_spec.get('id', 'unknown')
        context = {
            **action_spec.get('context', {}),
            'plugin': action_spec.get('plugin'),
            'params': action_spec.get('params', {}),
        }
        confidence = (
            action_spec.get('context', {}).get('proposal_confidence')
            or action_spec.get('decision_confidence')
            or action_spec.get('context', {}).get('decision_confidence')
            or 0.7
        )

        try:
            synergy_decision = synergy_engine.decide_with_synergy(
                context=context,
                available_actions=[action_name],
                ai_confidence=confidence,
            )
            if not synergy_decision.get('approved'):
                return {
                    'approved': False,
                    'reason': synergy_decision.get('reasoning', 'Rejected by Synergy field validation'),
                    'details': synergy_decision,
                }

            action_spec['synergy_validated'] = True
            return {
                'approved': True,
                'reason': synergy_decision.get('reasoning', 'Approved by Synergy'),
                'details': synergy_decision,
            }
        except Exception as e:
            if validation_profile['requires_strict_validation']:
                return {
                    'approved': False,
                    'reason': f'Synergy validation error for strict-validation action: {e}',
                    'error': str(e),
                }
            return {
                'approved': True,
                'reason': f'Synergy validation skipped due to error: {e}',
                'error': str(e),
            }
    
    def _get_validation_profile(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize risk/trust metadata used for validation enforcement."""
        context = action_spec.get('context', {}) or {}
        impact = context.get('impact', action_spec.get('impact', 'medium'))
        risk_level = (
            context.get('risk_level')
            or action_spec.get('risk_level')
            or 'medium'
        )
        trust_level = (
            context.get('trust_level')
            or action_spec.get('trust_level')
            or 'normal'
        )
        requires_strict_validation = (
            impact == 'high'
            or str(risk_level).lower() in {'high', 'critical'}
            or str(trust_level).lower() in {'low', 'untrusted'}
        )
        return {
            'impact': impact,
            'risk_level': str(risk_level).lower(),
            'trust_level': str(trust_level).lower(),
            'requires_strict_validation': requires_strict_validation,
        }

    def _normalize_validation_result(
        self,
        stage: str,
        raw_result: Optional[Dict[str, Any]],
        *,
        fail_closed: bool,
    ) -> Dict[str, Any]:
        """Normalize validation outputs into one fail-closed routed schema."""
        if not isinstance(raw_result, dict):
            approved = False if fail_closed else True
            return {
                'stage': stage,
                'approved': approved,
                'reason': f'{stage} returned non-dict validation result',
                'error': 'invalid_validation_shape',
                'details': {'raw_type': type(raw_result).__name__},
            }

        approved = raw_result.get('approved')
        if approved is None:
            if 'valid' in raw_result:
                approved = bool(raw_result.get('valid'))
            elif 'success' in raw_result:
                approved = bool(raw_result.get('success'))
            else:
                approved = False if fail_closed else True

        reason = (
            raw_result.get('reason')
            or raw_result.get('message')
            or raw_result.get('reasoning')
            or raw_result.get('reasoning_trace')
            or ('approved' if approved else 'rejected')
        )

        normalized = {
            'stage': stage,
            'approved': bool(approved),
            'reason': str(reason),
            'error': raw_result.get('error'),
            'details': raw_result.get('details', raw_result),
        }
        return normalized
    
    def _map_action_to_method(self, plugin_name: str, action_type: str) -> str:
        """
        Map generic action types to plugin-specific method names.
        
        Args:
            plugin_name: Name of the plugin
            action_type: Generic action type (e.g., 'post', 'reply')
        
        Returns:
            Plugin-specific method name
        """
        # Action mapping by plugin
        action_map = {
            'moltx': {
                'post': 'create_post',
                'reply': 'reply_to_post',
                'like': 'like_post',
                'engage': 'dynamic_engage',
                'update': 'create_post',  # MoltX doesn't have separate update
            },
            'moltchan': {
                'post': 'create_thread',
                'reply': 'reply_to_thread',
                'update': 'create_thread',
            },
            'moltbook': {
                'post': 'create_post',
                'reply': 'add_comment',
                'comment': 'add_comment',
            },
            'moltbookai': {
                'post': 'create_post',
                'update': 'create_post',
            },
            'clawbr': {
                'post': 'create_post',
                'reply': 'add_comment',
                'debate': 'create_debate',
            },
            'a2a': {
                'discover': 'discover_agents',
                'connect': 'connect_to_agent',
            },
        }
        
        # Get plugin-specific mapping
        plugin_actions = action_map.get(plugin_name, {})
        
        # Return mapped method or original action_type as fallback
        return plugin_actions.get(action_type, action_type)
    
    async def _execute_via_plugin(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action via the target plugin.
        
        Args:
            action_spec: Action specification with plugin, action_type, params
        
        Returns:
            Result dict from plugin execution
        """
        plugin_name = action_spec.get('plugin')
        action_type = action_spec.get('action_type')
        params = action_spec.get('params', {})
        
        if not plugin_name or not action_type:
            return {
                'success': False,
                'error': 'Missing plugin or action_type',
                'stage': 'execution'
            }
        
        # Get plugin
        plugin = self.plugins.get_plugin(plugin_name)
        if not plugin:
            return {
                'success': False,
                'error': f'Plugin not found: {plugin_name}',
                'stage': 'execution'
            }
        
        # Map action type to plugin-specific method
        method_name = self._map_action_to_method(plugin_name, action_type)
        
        # Execute action
        try:
            # Check if plugin has the mapped method
            if hasattr(plugin, method_name):
                method = getattr(plugin, method_name)
                
                # Call method (handle both sync and async)
                if inspect.iscoroutinefunction(method):
                    result = await method(**params)
                else:
                    result = method(**params)
                
                # Normalize result
                if isinstance(result, dict):
                    return result
                else:
                    return {'success': True, 'data': result}
            else:
                return {
                    'success': False,
                    'error': f'Action method not found on plugin: {method_name} (mapped from {action_type})',
                    'stage': 'execution'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'execution',
                'exception_type': type(e).__name__
            }
    
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
        validation_trace = []
        
        # Step 1: AGI Kernel validation
        validation = self._normalize_validation_result(
            'agi_validation',
            await self._validate_with_agi(action_spec),
            fail_closed=True,
        )
        validation_trace.append(validation)
        if not validation['approved']:
            return {
                'success': False,
                'reason': validation['reason'],
                'stage': 'agi_validation',
                'action_id': action_id,
                'validation_trace': validation_trace,
            }
        
        # Step 1.5: FairMind DNA validation (Ethical Consciousness)
        if self.agi and hasattr(self.agi, 'fairmind'):
            try:
                fairmind_check = self.agi.fairmind.validate_action(
                    action_type=action_spec.get('action_type', 'unknown'),
                    params=action_spec.get('params', {}),
                    context=action_spec.get('context', {})
                )
                
                fairmind_validation = self._normalize_validation_result(
                    'fairmind_validation',
                    fairmind_check,
                    fail_closed=False,  # Don't fail-closed, just warn
                )
                validation_trace.append(fairmind_validation)
                
                if not fairmind_check['approved']:
                    print(f"⚠️ FairMind rejected action: {fairmind_check['reason']}")
                    return {
                        'success': False,
                        'error': f"FairMind validation failed: {fairmind_check['reason']}",
                        'stage': 'fairmind_validation',
                        'action_id': action_id,
                        'validation_trace': validation_trace,
                        'truth_violations': fairmind_check.get('violations', []),
                        'sovereign_health': fairmind_check.get('sovereign_health', 0),
                        'value_analysis': fairmind_check.get('value_analysis', {})
                    }
                
                # Add FairMind metadata to validation
                validation['fairmind_approved'] = True
                validation['sovereign_health'] = fairmind_check.get('sovereign_health', 0)
                validation['value_svu'] = fairmind_check.get('value_analysis', {}).get('total_svu', 0)
                
                # Log value analysis
                value_analysis = fairmind_check.get('value_analysis', {})
                if value_analysis.get('total_svu', 0) != 0:
                    print(f"💎 Value: {value_analysis['total_svu']:.2f} SVU ({value_analysis['verdict']})")
                
            except Exception as e:
                print(f"⚠️ FairMind validation error (non-critical): {e}")
        
        # Step 2: Apply episodic learning modulation
        modulated_action = action_spec
        if hasattr(self.agi, 'behavior_modulator'):
            context = {
                'hour': datetime.now().hour,
                'platform': action_spec.get('plugin'),
                'user_id': action_spec.get('context', {}).get('user_id')
            }
            modulated_action = self.agi.behavior_modulator.modulate_action(action_spec, context)
            
            # Log episodic warnings if present
            if modulated_action.get('episodic_warnings'):
                for warning in modulated_action['episodic_warnings']:
                    print(warning)
            
            # Log episodic insights if present
            if modulated_action.get('episodic_insights'):
                for insight in modulated_action['episodic_insights']:
                    print(insight)

        # Get validation profile early - needed for both Synergy and SyMod validation
        validation_profile = self._get_validation_profile(modulated_action)

        # Step 3: Synergy validation (field / harmonic approval)
        synergy_check = self._normalize_validation_result(
            'synergy_validation',
            self._validate_with_synergy(modulated_action),
            fail_closed=validation_profile['requires_strict_validation'],
        )
        validation_trace.append(synergy_check)
        if not synergy_check['approved']:
            return {
                'success': False,
                'reason': synergy_check['reason'],
                'stage': 'synergy_validation',
                'action_id': action_id,
                'validation_trace': validation_trace,
                'synergy_details': synergy_check,
            }
        
        # Step 4: SyMod verification (for high-impact actions)
        if validation_profile['requires_strict_validation']:
            symod_check = self._normalize_validation_result(
                'symod_verification',
                self._verify_with_symod(modulated_action, validation),
                fail_closed=True,
            )
            validation_trace.append(symod_check)
            if not symod_check['approved']:
                return {
                    'success': False,
                    'reason': symod_check['reason'],
                    'stage': 'symod_verification',
                    'action_id': action_id,
                    'validation_trace': validation_trace,
                    'symod_details': symod_check
                }

        # Step 4.5: Build pre-action prediction artifact for later reflection
        prediction = self._build_prediction_record(modulated_action, validation, validation_profile)
        modulated_action.setdefault('context', {})['prediction'] = prediction
        
        # Step 5: Execute via plugin
        try:
            result = await self._execute_via_plugin(modulated_action)
            prediction_evaluation = self._build_prediction_evaluation(modulated_action, result)
            
            # Step 6: Reflect and learn through the unified AGI pathway
            await self._reflect_on_outcome(modulated_action, result, validation, prediction_evaluation)
            result['outcome_record'] = self._build_outcome_record(
                modulated_action,
                result,
                validation,
                action_id,
                prediction_evaluation=prediction_evaluation,
            )
            self._refresh_action_family_trust_from_outcome(modulated_action, result, prediction_evaluation)
            
            # Step 7: Feed learning to MetaLearner for strategy evolution
            await self._feed_learning_to_meta_learner(modulated_action, result, prediction_evaluation)
            
            # Add metadata
            result['action_id'] = action_id
            result['execution_time_ms'] = (datetime.now() - start_time).total_seconds() * 1000
            result['routed_through_agi'] = True
            result['validation_trace'] = validation_trace
            result['prediction'] = prediction
            result['prediction_evaluation'] = prediction_evaluation
            
            return result
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'stage': 'execution',
                'action_id': action_id,
                'validation_trace': validation_trace,
                'prediction': prediction,
            }
            error_result['prediction_evaluation'] = self._build_prediction_evaluation(modulated_action, error_result)
            self._refresh_action_family_trust_from_outcome(modulated_action, error_result, error_result['prediction_evaluation'])
            
            # Step 6: Reflect and learn from outcome
            await self._reflect_on_outcome(modulated_action, error_result, prediction, error_result['prediction_evaluation'])
            
            # Step 7: Feed learning to MetaLearner for strategy evolution
            await self._feed_learning_to_meta_learner(modulated_action, error_result, error_result['prediction_evaluation'])
            
            return error_result

    def _build_prediction_record(
        self,
        action_spec: Dict[str, Any],
        validation: Dict[str, Any],
        validation_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a lightweight expected-outcome artifact before execution."""
        context = action_spec.get('context', {}) or {}
        action_type = action_spec.get('action_type', 'unknown')
        plugin = action_spec.get('plugin', 'unknown')
        confidence = context.get('proposal_confidence', validation.get('confidence', 0.5))
        confidence = max(0.0, min(float(confidence or 0.5), 1.0))

        expected_outcome = 'successful execution'
        if 'engage' in action_type:
            expected_outcome = 'successful engagement cycle with useful external signal'
        elif 'post' in action_type or 'debate' in action_type or 'reply' in action_type:
            expected_outcome = 'successful public response aligned with current goals'
        elif 'analyze' in action_type or 'check_' in action_type:
            expected_outcome = 'useful analysis that improves later decisions'
        elif 'self_improve' in action_type or 'auto_fix' in action_type:
            expected_outcome = 'bounded system improvement backed by evidence'

        expected_value = 'medium'
        if validation_profile.get('impact') == 'high':
            expected_value = 'high'
        elif validation_profile.get('impact') == 'low':
            expected_value = 'low'

        expected_risk = validation_profile.get('risk_level', 'medium')
        if validation_profile.get('requires_strict_validation') and expected_risk not in {'high', 'critical'}:
            expected_risk = 'elevated'

        exploration = context.get('exploration') or action_spec.get('exploration')

        return {
            'timestamp': datetime.now().isoformat(),
            'plugin': plugin,
            'action_type': action_type,
            'expected_outcome': expected_outcome,
            'expected_value': expected_value,
            'expected_risk': expected_risk,
            'confidence': confidence,
            'exploration': exploration,
            'basis': {
                'goal_id': context.get('goal_id'),
                'trigger': context.get('trigger', context.get('source', 'unknown')),
                'impact': validation_profile.get('impact'),
                'trust_level': validation_profile.get('trust_level'),
                'risk_level': validation_profile.get('risk_level'),
                'validation_reason': validation.get('reason'),
            }
        }

    async def _reflect_on_outcome(self, action_spec: Dict[str, Any], result: Dict[str, Any], prediction: Dict[str, Any] = None, evaluation: Dict[str, Any] = None) -> None:
        """
        Reflect on action outcome and learn.
        
        This is the AGI feedback loop - every outcome improves future decisions.
        
        Args:
            action_spec: The action specification
            result: The execution result
            prediction: Optional prediction dict (for compatibility)
            evaluation: Optional evaluation dict (for compatibility)
        """
        action_id = f"{action_spec.get('plugin')}:{action_spec.get('action_type')}"
        success = result.get('success', False)
        validation_trace = result.get('validation_trace') or []
        
        # Build validation dict from result if not in trace
        validation = prediction if prediction else {'approved': success, 'reason': result.get('error') or 'Success'}
        
        outcome_record = self._build_outcome_record(
            action_spec,
            result,
            validation,
            action_id,
            validation_trace=validation_trace,
        )
        
        # Record in execution history
        self.execution_history.append(outcome_record)
        
        # Keep history manageable
        self.execution_history = self.execution_history[-100:]

        # Persist canonical record to shared action log
        try:
            get_action_logger().log_outcome_record(outcome_record)
        except Exception as e:
            print(f"⚠️ Action logger write failed: {e}")
        
        # Learn through AGI Kernel
        if hasattr(self.agi, 'learn'):
            self.agi.learn(
                context=action_id,
                action=action_spec.get('action_type', ''),
                outcome=str(result)[:100],
                success=success,
                user_id=action_spec.get('context', {}).get('user_id'),
                outcome_record=outcome_record,
            )
        
        # Record in decision system
        if hasattr(self.agi, 'decision_system'):
            self.agi.decision_system.record_action(action_id, result)

    def _build_outcome_record(
        self,
        action_spec: Dict[str, Any],
        result: Dict[str, Any],
        validation: Dict[str, Any],
        action_id: str,
        prediction_evaluation: Optional[Dict[str, Any]] = None,
        validation_trace: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Build a canonical autonomous action outcome record."""
        context = action_spec.get('context', {})
        evaluation = prediction_evaluation or result.get('prediction_evaluation') or self._build_prediction_evaluation(action_spec, result)
        normalized_validation_trace = validation_trace or result.get('validation_trace') or [validation]
        return {
            'action_id': action_id,
            'timestamp': datetime.now().isoformat(),
            'plugin': action_spec.get('plugin'),
            'action_type': action_spec.get('action_type'),
            'success': result.get('success', False),
            'goal_id': context.get('goal_id'),
            'goal_description': context.get('goal_description'),
            'trigger': context.get('trigger', context.get('source', 'unknown')),
            'source': context.get('source'),
            'impact': context.get('impact', action_spec.get('impact')),
            'params_summary': str(action_spec.get('params', {}))[:200],
            'result_summary': str(result)[:200],
            'prediction': context.get('prediction'),
            'exploration': context.get('exploration') or action_spec.get('exploration'),
            'prediction_evaluation': evaluation,
            'mismatch_score': evaluation.get('mismatch_score'),
            'reflection_summary': evaluation.get('reflection_summary'),
            'validation_trace': normalized_validation_trace,
            'validation': {
                'agi': validation,
                'trace': normalized_validation_trace,
                'synergy_validated': action_spec.get('synergy_validated', False),
                'synergy_score': action_spec.get('synergy_score'),
                'field_state': action_spec.get('field_state'),
                'synergy_reasoning': action_spec.get('synergy_reasoning'),
            },
        }
    
    def _build_prediction_evaluation(
        self,
        action_spec: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare pre-action prediction with actual result and compute mismatch metadata."""
        prediction = (action_spec.get('context', {}) or {}).get('prediction') or {}
        predicted_success = True
        actual_success = bool(result.get('success', False))
        confidence = max(0.0, min(float(prediction.get('confidence', 0.5) or 0.5), 1.0))
        
        predicted_value = prediction.get('expected_value', 'medium')
        realized_value = self._categorize_realized_value(result)
        predicted_risk = prediction.get('expected_risk', 'medium')
        observed_risk = self._categorize_observed_risk(result)
        
        success_mismatch = 0.0 if predicted_success == actual_success else 1.0
        confidence_mismatch = abs(confidence - (1.0 if actual_success else 0.0))
        value_mismatch = min(abs(self._value_rank(predicted_value) - self._value_rank(realized_value)) / 2.0, 1.0)
        risk_mismatch = min(abs(self._risk_rank(predicted_risk) - self._risk_rank(observed_risk)) / 4.0, 1.0)
        
        mismatch_score = round(
            (success_mismatch * 0.4)
            + (confidence_mismatch * 0.3)
            + (value_mismatch * 0.2)
            + (risk_mismatch * 0.1),
            4,
        )

        calibration = 'well_calibrated'
        if confidence >= 0.75 and not actual_success:
            calibration = 'overconfident'
        elif confidence <= 0.35 and actual_success:
            calibration = 'underconfident'
        
        exploration = (action_spec.get('context', {}) or {}).get('exploration') or action_spec.get('exploration')
        
        value_alignment = 'matched'
        if self._value_rank(realized_value) > self._value_rank(predicted_value):
            value_alignment = 'underestimated_value'
        elif self._value_rank(realized_value) < self._value_rank(predicted_value):
            value_alignment = 'overestimated_value'
        
        risk_alignment = 'matched'
        if self._risk_rank(observed_risk) > self._risk_rank(predicted_risk):
            risk_alignment = 'underestimated_risk'
        elif self._risk_rank(observed_risk) < self._risk_rank(predicted_risk):
            risk_alignment = 'overestimated_risk'
        
        return {
            'predicted_success': predicted_success,
            'actual_success': actual_success,
            'success_mismatch': success_mismatch,
            'confidence': confidence,
            'confidence_mismatch': round(confidence_mismatch, 4),
            'confidence_calibration': calibration,
            'predicted_value': predicted_value,
            'realized_value': realized_value,
            'value_alignment': value_alignment,
            'value_mismatch': round(value_mismatch, 4),
            'predicted_risk': predicted_risk,
            'observed_risk': observed_risk,
            'risk_alignment': risk_alignment,
            'risk_mismatch': round(risk_mismatch, 4),
            'mismatch_score': mismatch_score,
            'exploration': exploration,
            'reflection_summary': self._summarize_prediction_evaluation(
                actual_success,
                calibration,
                value_alignment,
                risk_alignment,
                mismatch_score,
            ),
        }

    def _summarize_prediction_evaluation(
        self,
        actual_success: bool,
        calibration: str,
        value_alignment: str,
        risk_alignment: str,
        mismatch_score: float,
    ) -> str:
        """Generate human-readable summary of prediction evaluation."""
        parts = []
        
        if actual_success:
            parts.append("✅ Action succeeded")
        else:
            parts.append("❌ Action failed")
        
        if calibration == 'overconfident':
            parts.append("⚠️ Overconfident prediction")
        elif calibration == 'underconfident':
            parts.append("💡 Underconfident prediction")
        
        if value_alignment == 'underestimated_value':
            parts.append("📈 Better than expected")
        elif value_alignment == 'overestimated_value':
            parts.append("📉 Worse than expected")
        
        if risk_alignment == 'underestimated_risk':
            parts.append("⚠️ Riskier than expected")
        
        if mismatch_score < 0.2:
            parts.append("🎯 Excellent prediction")
        elif mismatch_score > 0.5:
            parts.append("🔄 Poor prediction - needs learning")
        
        return " | ".join(parts)

    def _value_rank(self, value: str) -> int:
        ranks = {
            'low': 1,
            'medium': 2,
            'high': 3,
        }
        return ranks.get(str(value).lower(), 2)

    def _categorize_realized_value(self, result: Dict[str, Any]) -> str:
        """Estimate realized usefulness from the execution result."""
        if not result.get('success', False):
            return 'low'

        engagement_signals = [
            result.get('engagement'),
            result.get('engagement_count'),
            result.get('likes'),
            result.get('replies'),
            result.get('comments'),
            result.get('score'),
        ]
        numeric_engagement = 0.0
        for signal in engagement_signals:
            if isinstance(signal, (int, float)):
                numeric_engagement += float(signal)

        result_text = str(result).lower()
        if numeric_engagement >= 10:
            return 'high'
        if numeric_engagement >= 1:
            return 'medium'
        if any(keyword in result_text for keyword in ['created', 'posted', 'completed', 'analy', 'report', 'summary']):
            return 'medium'
        return 'low'

    def _categorize_observed_risk(self, result: Dict[str, Any]) -> str:
        """Estimate observed execution risk from failures or blocking patterns."""
        if result.get('success', False):
            return 'low'

        error_text = str(result.get('error') or result.get('reason') or result).lower()
        if any(keyword in error_text for keyword in ['security', 'permission', 'secret', 'wallet', 'private key', 'forbidden']):
            return 'critical'
        if any(keyword in error_text for keyword in ['validation', 'blocked', 'reject', 'denied', 'symod', 'synergy']):
            return 'high'
        if any(keyword in error_text for keyword in ['timeout', 'network', 'unavailable', 'not loaded']):
            return 'medium'
        return 'medium'
    
    def _risk_rank(self, risk: str) -> int:
        """Convert risk level to numeric rank for comparison."""
        ranks = {
            'low': 1,
            'medium': 2,
            'elevated': 3,
            'high': 4,
            'critical': 5,
        }
        return ranks.get(str(risk).lower(), 2)
    
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

    # ------------------------------------------------------------------
    # Canonical Contract Methods (Phase 4 Hardening)
    # ------------------------------------------------------------------
    
    async def route(
        self,
        envelope: ActionEnvelope,
    ) -> ActionOutcome:
        """
        Canonical action routing with typed contracts.
        
        This is the Phase 4 hardened entry point that uses ActionEnvelope
        and ActionOutcome for type-safe action routing.
        
        Args:
            envelope: Canonical action specification
            
        Returns:
            ActionOutcome with full reflection metadata
        """
        start_time = datetime.now()
        
        print(f"🔄 Routing canonical action: {envelope.action_id}")
        
        # Convert to dict for internal processing (backward compatibility)
        action_spec = envelope.to_dict()
        
        # Run existing routing logic
        result_dict = await self.route_action(action_spec)
        
        # Build canonical outcome
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        outcome = ActionOutcome.from_result_dict(result_dict, envelope)
        outcome.execution_time_ms = execution_time_ms
        
        # Attach prediction/evaluation if present
        if 'prediction' in result_dict:
            outcome.prediction = result_dict.get('prediction')
        if 'prediction_evaluation' in result_dict:
            outcome.prediction_evaluation = result_dict.get('prediction_evaluation')
        
        return outcome
    
    async def route_with_prediction(
        self,
        envelope: ActionEnvelope,
        expected_outcome: str,
        confidence: float = 0.7,
    ) -> ActionOutcome:
        """
        Route action with explicit prediction for reflection.
        
        Args:
            envelope: Canonical action specification
            expected_outcome: Human-readable expected outcome
            confidence: Confidence level (0.0-1.0)
            
        Returns:
            ActionOutcome with prediction evaluation
        """
        # Build validation profile for prediction
        validation_profile = ValidationProfile.from_action_spec(envelope.to_dict())
        
        # Create prediction record
        prediction = PredictionRecord.from_action_spec(
            action_spec=envelope.to_dict(),
            validation={'approved': True, 'reason': 'Pre-validated'},
            validation_profile=validation_profile,
        )
        prediction.expected_outcome = expected_outcome
        prediction.confidence = max(0.0, min(float(confidence), 1.0))
        
        # Attach to envelope
        envelope.prediction = prediction
        envelope.validation_profile = validation_profile
        
        # Route with prediction attached
        return await self.route(envelope)
    
    def create_envelope(
        self,
        plugin: str,
        action_type: str,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        impact: ImpactLevel = ImpactLevel.MEDIUM,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        trust_level: TrustLevel = TrustLevel.NORMAL,
    ) -> ActionEnvelope:
        """
        Factory method to create canonical action envelopes with proper metadata.
        
        Args:
            plugin: Target plugin name
            action_type: Action to execute
            params: Action parameters
            context: Additional context
            impact: Impact classification
            risk_level: Risk classification  
            trust_level: Trust classification
            
        Returns:
            Configured ActionEnvelope
        """
        merged_context = context or {}
        merged_context.update({
            'impact': impact.value,
            'risk_level': risk_level.value,
            'trust_level': trust_level.value,
        })
        
        return ActionEnvelope(
            plugin=plugin,
            action_type=action_type,
            params=params or {},
            context=merged_context,
            validation_profile=ValidationProfile(
                impact=impact,
                risk_level=risk_level,
                trust_level=trust_level,
            ),
        )
    
    async def validate_envelope(
        self,
        envelope: ActionEnvelope,
    ) -> Dict[str, Any]:
        """
        Pre-validate an envelope without executing.
        
        Returns validation result without side effects.
        """
        action_spec = envelope.to_dict()
        
        validation_trace = []
        
        # AGI validation
        agi_validation = self._normalize_validation_result(
            'agi_validation',
            await self._validate_with_agi(action_spec),
            fail_closed=True,
        )
        validation_trace.append(agi_validation)
        
        # Synergy validation
        synergy_validation = self._normalize_validation_result(
            'synergy_validation',
            self._validate_with_synergy(action_spec),
            fail_closed=envelope.validation_profile.requires_strict_validation if envelope.validation_profile else False,
        )
        validation_trace.append(synergy_validation)
        
        return {
            'action_id': envelope.action_id,
            'approved': all(v.get('approved', False) for v in validation_trace),
            'validation_trace': validation_trace,
            'requires_strict_validation': (
                envelope.validation_profile.requires_strict_validation 
                if envelope.validation_profile else False
            ),
        }
    
    async def _feed_learning_to_meta_learner(self, action_spec: Dict[str, Any], result: Dict[str, Any], prediction_evaluation: Dict[str, Any]):
        """Feed action outcome to MetaLearner for continuous strategy improvement."""
        if not hasattr(self.agi, 'meta_engine') or not self.agi.meta_engine:
            return
        
        try:
            # Determine domain from action
            plugin = action_spec.get('plugin', 'unknown')
            domain_map = {
                'moltx': 'social',
                'clawbr': 'social',
                'moltchan': 'social',
                'polymarket': 'trading',
                'crypto': 'trading',
                'analytics': 'analysis',
            }
            domain = domain_map.get(plugin, 'general')
            
            # Extract learning metrics
            success = result.get('success', False)
            mismatch_score = float(prediction_evaluation.get('mismatch_score', 0.0))
            quality_score = 1.0 - mismatch_score if success else 0.0
            
            # Determine strategy used
            strategy = 'active_experimentation'
            if action_spec.get('context', {}).get('exploration'):
                strategy = 'exploration'
            
            # Build context description
            action_type = action_spec.get('action_type', 'unknown')
            context = f"{plugin}:{action_type}"
            
            # Build notes about what happened
            notes = []
            if success:
                if mismatch_score < 0.3:
                    notes.append(f"Accurate prediction (mismatch: {mismatch_score:.2f})")
                notes.append(f"Successful {action_type} execution")
            else:
                error = result.get('error', 'Unknown error')
                notes.append(f"Action failed: {error}")
                if mismatch_score > 0.5:
                    notes.append(f"Poor prediction accuracy (mismatch: {mismatch_score:.2f})")
            
            notes_str = " | ".join(notes)
            
            # Record learning attempt in MetaLearningEngine
            self.agi.meta_engine.record_learning_attempt(
                domain=domain,
                context=context,
                strategy=strategy,
                success=success,
                time_to_success=1.0 if success else 0.0,
                exploration_rate=0.3,
                memory_depth=10,
                notes=notes_str
            )
            
            print(f"📚 Learning recorded: {domain} domain, quality={quality_score:.2f}")
            
        except Exception as e:
            print(f"⚠️ MetaLearner feed failed: {e}")

def create_action_router(agi_kernel, plugin_manager):
    """Factory function to create action router"""
    return ActionRouter(agi_kernel, plugin_manager)
