"""
Brain Act Module — Action execution, outcome recording

Extracted from autonomous_brain.py for modularity.
Contains: _phase_execute_proposals, _record_proposal_success,
_record_proposal_failure, _execute_proposal,
_notify_user_of_goal_result, _phase_chess_win_posts,
_check_for_quick_profit_actions
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.agentic.contracts import NotificationPriority

logger = logging.getLogger(__name__)


class BrainAct:
    """Act phase operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    async def _phase_execute_proposals(self, proposals, agi_kernel, next_action) -> int:
        """ACT phase — execute ranked proposals and record outcomes.

        Returns the number of successfully executed actions.
        """
        # Check if chess runner has an active game — if so, deprioritise chess proposals
        chess_has_game = False
        if self.brain.plugin_manager:
            chess = self.brain.plugin_manager.get_plugin('clawchess')
            if chess and hasattr(chess, 'current_game') and chess.current_game is not None:
                chess_has_game = True

        executed = 0
        for proposal in proposals:
            if proposal.confidence < self.brain.config.min_confidence:
                logger.debug(f"⛔ Blocked: confidence {proposal.confidence:.2f} < {self.brain.config.min_confidence}")
                self.brain.stats['actions_blocked'] += 1
                continue

            # Skip chess analysis proposals while a game is active — runner handles it independently
            if chess_has_game:
                plugin = proposal.metadata.get('plugin', '') if proposal.metadata else ''
                is_chess = plugin == 'clawchess' or 'chess' in str(proposal.action_type).lower()
                if is_chess:
                    logger.debug("♟️ Chess game active — skipping chess proposal: %s", proposal.action_type)
                    continue

            if self.brain._actions_this_hour >= self.brain.config.max_actions_per_hour:
                logger.info("⏸️ Hourly budget exhausted")
                break

            result = await self._execute_proposal(proposal)

            # AGI Social: Follow after engagement if appropriate
            if result and proposal.target_name:
                await self.brain._follow_after_engagement_action(
                    proposal.metadata.get('plugin', 'unknown'),
                    self.brain.plugin_manager.get_plugin(proposal.metadata.get('plugin', 'unknown')),
                    proposal.target_name,
                    proposal.action_type
                )

            if result:
                executed += 1
                self.brain._actions_this_hour += 1
                self.brain.stats['actions_taken'] += 1
                self._record_proposal_success(proposal, result, agi_kernel, next_action)
            else:
                self._record_proposal_failure(proposal, agi_kernel)

        return executed

    def _record_proposal_success(self, proposal, result, agi_kernel, next_action):
        """Post-execution bookkeeping for a successful proposal."""
        goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
        if goal_id:
            if self.brain.goal_manager_v2 and hasattr(self.brain.goal_manager_v2, 'record_goal_action_success'):
                self.brain.goal_manager_v2.record_goal_action_success(
                    goal_id,
                    note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} succeeded"
                )
            if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                gm = agi_kernel.goal_manager
                if gm and hasattr(gm, 'complete_action'):
                    gm.complete_action(goal_id, success=True, outcome=f"Successfully executed {proposal.action_type}")

        # Meta-learning with real metrics
        if self.brain.meta_learner and proposal.action_type:
            from src.agentic.meta_learner import LearningOutcome
            from datetime import timedelta

            exec_time_ms = result.get('execution_time_ms', 5000) if isinstance(result, dict) else 5000
            pred_eval = result.get('prediction_evaluation', {}) if isinstance(result, dict) else {}
            mismatch = float(pred_eval.get('mismatch_score', 0.5))
            retention = max(0.0, 1.0 - mismatch)

            outcome = LearningOutcome(
                id=f"outcome_{datetime.now().timestamp()}",
                strategy_id="strategy_active_experimentation",
                domain=proposal.metadata.get('plugin', 'unknown'),
                task=proposal.action_type,
                success=True,
                learning_time=timedelta(milliseconds=exec_time_ms),
                quality_score=proposal.confidence,
                retention_score=retention,
                what_worked=[f"Action: {proposal.action_type}"],
                insights=[f"Confidence {proposal.confidence:.2f}, mismatch {mismatch:.2f}"]
            )
            self.brain.meta_learner.record_outcome(outcome)

        # Transfer learning
        if self.brain.transfer_learner and proposal.action_type:
            applicable_patterns = self.brain.transfer_learner.find_applicable_patterns(
                domain=proposal.metadata.get('plugin', 'unknown'),
                problem=proposal.action_type
            )
            if applicable_patterns:
                logger.info(f"🔄 Found {len(applicable_patterns)} transferable patterns")

        # Knowledge graph
        if self.brain.knowledge_graph:
            from src.agentic.knowledge_graph import Entity, EntityType
            entity = Entity(
                id=f"action_{datetime.now().timestamp()}",
                name=proposal.action_type,
                entity_type=EntityType.ACTION,
                domain=proposal.metadata.get('plugin', 'unknown'),
                attributes={
                    'success': True,
                    'confidence': proposal.confidence,
                    'timestamp': datetime.now().isoformat()
                }
            )
            self.brain.knowledge_graph.add_entity(entity)

        # Goal hierarchy progress
        if self.brain.goal_hierarchy and next_action and next_action.goal_id:
            goal = self.brain.goal_hierarchy.get_goal(next_action.goal_id)
            if goal:
                new_progress = min(goal.progress + 0.05, 1.0)
                self.brain.goal_hierarchy.update_progress(next_action.goal_id, new_progress)
                logger.info(f"📈 Goal progress: {goal.title} → {new_progress:.1%}")

        # Planner completion
        if self.brain.planner and next_action:
            self.brain.planner.complete_action(next_action.id)

    def _record_proposal_failure(self, proposal, agi_kernel):
        """Post-execution bookkeeping for a failed proposal."""
        goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
        if goal_id:
            if self.brain.goal_manager_v2 and hasattr(self.brain.goal_manager_v2, 'record_goal_action_failure'):
                self.brain.goal_manager_v2.record_goal_action_failure(
                    goal_id,
                    note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} failed"
                )
            if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                gm = agi_kernel.goal_manager
                if gm and hasattr(gm, 'complete_action'):
                    gm.complete_action(goal_id, success=False, outcome="Action execution failed")

        if self.brain.outcome_learner:
            self.brain.outcome_learner.record_outcome(
                action_type=proposal.action_type,
                platform=proposal.metadata.get('plugin', 'unknown'),
                success=False,
                data={'reason': 'execution_failed'}
            )

    async def _execute_proposal(self, proposal) -> Optional[Dict]:
        """Execute a single action proposal.

        Route all autonomous proposals through AGIKernel.act()/ActionRouter
        so validation, execution, and learning use one unified pipeline.

        Also notifies owner of high-impact actions via notification service.
        """
        plugin_name = proposal.metadata.get('plugin')

        if not plugin_name or not self.brain.plugin_manager:
            return None

        try:
            agi_kernel = getattr(self.brain.core, 'agi_kernel', None) if self.brain.core else None
            if not agi_kernel:
                logger.warning("⚠️ AGI Kernel unavailable, falling back to direct plugin execution")
                # Fallback: execute directly through plugin
                plugin = self.brain.plugin_manager.get_plugin(plugin_name)
                if not plugin:
                    return None

                # Try to execute the action directly
                action_method = getattr(plugin, proposal.action_type, None)
                if action_method and callable(action_method):
                    try:
                        result = action_method(
                            target_id=proposal.target_id,
                            content=proposal.content,
                            **(proposal.metadata or {})
                        )
                        return {'success': True, 'data': result, 'fallback': True}
                    except Exception as e:
                        logger.error(f"❌ Direct execution error: {e}")
                        return {'success': False, 'error': str(e), 'fallback': True}
                return None
            # Original AGI Kernel route
            action_spec = {
                'plugin': plugin_name,
                'action_type': proposal.action_type,
                'params': {
                    'target_id': proposal.target_id,
                    'target_name': proposal.target_name,
                    'content': proposal.content,
                    'confidence': proposal.confidence,
                    'justification': proposal.justification,
                    'metadata': proposal.metadata or {},
                },
                'context': {
                    'source': 'autonomous_brain_proposal',
                    'trigger': proposal.metadata.get('trigger', 'autonomous_brain') if proposal.metadata else 'autonomous_brain',
                    'impact': 'high' if proposal.confidence >= 0.7 else 'medium',
                    'goal_id': proposal.metadata.get('goal_id') if proposal.metadata else None,
                    'proposal_confidence': proposal.confidence,
                    'spine_context': proposal.metadata.get('spine_context') if proposal.metadata else None,
                }
            }

            result = await agi_kernel.act(action_spec)

            # === NOTIFICATION: Alert owner of meaningful autonomous actions ===
            if result and self.brain.notification_service and self.brain._services_available:
                try:
                    success = result.get('success', False)
                    action_type = proposal.action_type
                    impact = action_spec['context'].get('impact', 'medium')

                    # Routine actions that never warrant notification
                    silent_actions = {'scan', 'check', 'monitor', 'list', 'fetch',
                                      'observe', 'refresh', 'health', 'ping', 'status'}

                    # Determine if this is worth notifying about
                    should_notify = False
                    priority = NotificationPriority.LOW

                    action_root = action_type.split(':')[-1] if ':' in action_type else action_type
                    action_lower = action_type.lower()

                    # Silent routine maintenance — never notify
                    if action_root.lower() in silent_actions:
                        should_notify = False

                    # High-impact successes (but not routine scans)
                    elif success and impact == 'high':
                        should_notify = True
                        priority = NotificationPriority.NORMAL

                    # Failures on high-confidence proposals
                    elif not success and proposal.confidence >= 0.7:
                        should_notify = True
                        priority = NotificationPriority.HIGH

                    # Certain action types are always notable (successes only, or high-confidence failures)
                    else:
                        notable_actions = ['post', 'trade', 'executed', 'placed',
                                           'self_improve', 'auto_fix', 'deploy', 'launch']
                        if any(a in action_lower for a in notable_actions):
                            if success:
                                should_notify = True
                                priority = NotificationPriority.NORMAL
                            elif proposal.confidence >= 0.5:
                                should_notify = True
                                priority = NotificationPriority.HIGH

                    if should_notify:
                        # Build a meaningful message from the result
                        result_summary = result.get('message', result.get('summary', ''))
                        if not result_summary:
                            details = result.get('details', result.get('data', {}))
                            if isinstance(details, dict):
                                result_summary = ', '.join(f"{k}: {v}" for k, v in list(details.items())[:3])
                            elif isinstance(details, str):
                                result_summary = details[:200]

                        title = f"{'✅' if success else '❌'} {action_type}"
                        msg = f"{'✅' if success else '❌'} {action_type} via {plugin_name}"
                        if result_summary:
                            msg += f"\n📊 {result_summary}"
                        msg += f"\n🎯 Confidence: {proposal.confidence:.0%}"

                        await self.brain.notification_service.notify(
                            title=title,
                            message=msg,
                            priority=priority,
                            details={
                                'action_type': action_type,
                                'plugin': plugin_name,
                                'success': success,
                                'confidence': proposal.confidence,
                                'justification': proposal.justification[:100] if proposal.justification else '',
                                'result': result_summary[:200] if result_summary else '',
                            },
                            source_action=f"{plugin_name}:{action_type}",
                        )
                        logger.info(f"🔔 Notification sent: {action_type} {'succeeded' if success else 'failed'}")

                except Exception as e:
                    logger.debug(f"Notification error (non-critical): {e}")

            # === USER FEEDBACK: Tell the owner what happened if they requested this goal ===
            if result and proposal.metadata.get('goal_driven'):
                await self._notify_user_of_goal_result(proposal, result)

            return result

        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _notify_user_of_goal_result(self, proposal: Any, result: Dict[str, Any]) -> None:
        """Send a specialized response back to a user if they originated the goal.

        This bridges the gap between 'On it' and the actual task completion.
        """
        try:
            metadata = proposal.metadata or {}
            origin = metadata.get('origin')
            evidence = metadata.get('evidence', {})

            # We only care about user-originated goals for this channel
            if origin != 'user':
                return

            chat_id = evidence.get('chat_id')
            if not chat_id:
                logger.debug("No chat_id in goal evidence, cannot notify user")
                return

            # Get telegram plugin
            telegram = self.brain.plugin_manager.get_plugin('telegram') if self.brain.plugin_manager else None
            if not telegram:
                return

            success = result.get('success', False)
            action_type = proposal.action_type

            # Extract actual data if possible
            # Result usually contains {'success': True, 'data': ...} or {'success': True, 'output': ...}
            data = result.get('data') or result.get('output') or result.get('details', {})

            # Formulate message
            if success:
                # Clean up data for display
                if isinstance(data, dict):
                    # Special handling for wallet balances
                    if action_type == 'check_wallet' or 'balance' in str(data).lower():
                        display_data = ""
                        for token, bal in data.items():
                            if isinstance(bal, (int, float)):
                                display_data += f"• {token}: {bal:.4f}\n"
                            else:
                                display_data += f"• {token}: {bal}\n"
                    else:
                        display_data = json.dumps(data, indent=2)
                else:
                    display_data = str(data)

                msg = f"🏁 **Task Complete: {proposal.target_name or action_type}**\n\n"
                msg += f"Result:\n{display_data if display_data else 'Success (no details returned)'}"
            else:
                error = result.get('error') or "Unknown error"
                msg = f"❌ **Task Failed: {proposal.target_name or action_type}**\n\n"
                msg += f"Reason: {error}"

            # Send via telegram
            # Use the loop to call the sync method to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, telegram.send_message_to_owner_sync, msg)
            logger.info(f"📤 Sent goal result feedback to user on Telegram (chat: {chat_id})")

        except Exception as e:
            logger.error(f"Error in _notify_user_of_goal_result: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    async def _phase_chess_win_posts(self) -> None:
        """Post queued chess win announcements from the background runner to Moltx.

        The ClawChessRunner's ChessObserver writes win messages to temp files
        to avoid cross-thread plugin calls. This method picks them up on each
        brain cycle and posts them safely from the main thread.
        """
        import tempfile, os, glob
        win_dir = os.path.join(tempfile.gettempdir(), "alleybot_chess_wins")
        if not os.path.isdir(win_dir):
            return

        moltx = self.brain.plugin_manager.get_plugin('moltx') if self.brain.plugin_manager else None
        if not moltx or not hasattr(moltx, 'create_post'):
            return

        posted = 0
        for win_file in sorted(glob.glob(os.path.join(win_dir, "win_*.txt"))):
            try:
                with open(win_file) as f:
                    msg = f.read().strip()
                if msg:
                    moltx.create_post(msg)
                    posted += 1
                    logger.info("♟️ Posted chess win to Moltx: %s", msg[:60])
                os.remove(win_file)
            except Exception as e:
                logger.debug("Chess win post error: %s", e)

        if posted:
            logger.info("♟️ Posted %d chess win announcement(s)", posted)

    async def _check_for_quick_profit_actions(self, checkpoint: str) -> int:
        """Quick mid-cycle profit check — interleaves action between thinking phases.

        Runs fast scans (no heavy LLM) and executes immediately if high-confidence
        opportunities exist. This prevents AlleyBot from overthinking while money
        sits on the table.

        Args:
            checkpoint: Name of the cycle phase this runs after (for logging)

        Returns:
            Number of quick actions executed
        """
        if self.brain._actions_this_hour >= self.brain.config.max_actions_per_hour:
            return 0

        executed = 0

        # Quick Polymarket scan — check for obvious high-confidence trades
        if self.brain.autonomous_trading:
            try:
                proposals = await asyncio.wait_for(
                    self.brain.autonomous_trading.analyze_markets(), timeout=5.0
                )
                if proposals:
                    best = max(proposals, key=lambda t: t.confidence)
                    if best.confidence >= 0.75 and executed == 0:
                        outcome = await asyncio.wait_for(
                            self.brain.autonomous_trading.execute_trade(best), timeout=10.0
                        )
                        if outcome:
                            executed += 1
                            self.brain._actions_this_hour += 1
                            self.brain.stats['actions_taken'] += 1
                            logger.info(f"⚡[{checkpoint}] Quick trade executed: {outcome.trade_id}")
            except asyncio.TimeoutError:
                logger.debug(f"[{checkpoint}] Quick trade scan timed out")
            except Exception as e:
                logger.debug(f"[{checkpoint}] Quick trade check error: {e}")

        # Don't do two heavy scans in one quick-check — avoid slowing the cycle
        return executed


def create_brain_act(brain) -> BrainAct:
    """Factory to create BrainAct with brain reference."""
    return BrainAct(brain)
