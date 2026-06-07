"""
Brain Self-Improve Module - Skill gap detection, code generation, plugin creation

Extracted from autonomous_brain.py for modularity.
Contains: _phase_skill_gap_analysis, _phase_plugin_discovery_and_creation,
          _detect_skill_gaps, _propose_architecture_changes, _is_action_implemented
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BrainSelfImprove:
    """Self-improvement operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    async def skill_gap_analysis(self, observations, agi_kernel) -> None:
        """THINK sub-phase — detect capability gaps and auto-build skills.

        Runs with a cooldown: only every 50 cycles after an initial 10-cycle
        warmup. Prevents skill generation on startup when episodic memory
        may contain stale or malformed entries.
        """
        cycle_count = self.brain.stats.get('cycles_completed', 0)

        # Don't run skill gap analysis in the first 10 cycles (warmup)
        if cycle_count < 10:
            return

        # Only run skill gap analysis every 50 cycles (cooldown)
        if cycle_count % 50 != 0:
            return

        # Phase 1.1: Auto-enable self_improvement domain when 3+ needs_new_skill judgments exist
        if agi_kernel and hasattr(agi_kernel, 'work_item_manager'):
            try:
                wm = agi_kernel.work_item_manager
                # Query work items for repeated needs_new_skill evidence
                all_items = wm.get_all_work_items(limit=100)
                needs_skill_count = 0
                for item in all_items:
                    metadata = item.metadata if hasattr(item, 'metadata') else {}
                    if not metadata:
                        continue
                    judgment = metadata.get('capability_judgment', {})
                    if judgment.get('needs_new_skill'):
                        evidence = metadata.get('upgrade_evidence', {})
                        repeated_count = evidence.get('repeated_need_count', 0)
                        if repeated_count >= 2:
                            needs_skill_count += 1

                # Auto-enable self_improvement domain if threshold met
                if needs_skill_count >= 3:
                    profiles = getattr(agi_kernel, 'domain_autonomy_profiles', {})
                    if not profiles.get('self_improvement', {}).get('enabled', False):
                        profiles['self_improvement']['enabled'] = True
                        logger.info(f"🧠 Self-improvement domain AUTO-ENABLED ({needs_skill_count} work items need new skills)")
            except Exception as e:
                logger.debug(f"Could not check work items for skill gaps: {e}")

        if self.brain.auto_skill_builder:
            try:
                skill_proposals = await self.brain.auto_skill_builder.detect_capability_gaps(observations)
                if skill_proposals:
                    logger.info(f"💡 Detected {len(skill_proposals)} capability gaps")
                built_count = await self.brain.auto_skill_builder.auto_build_simple_skills(max_skills=1)
                if built_count > 0:
                    logger.info(f"🔨 Auto-built {built_count} new skill(s)")
                    # Reload skill executor so new skills are immediately available
                    if agi_kernel and hasattr(agi_kernel, 'skill_executor') and agi_kernel.skill_executor:
                        agi_kernel.skill_executor.reload_skills()
            except Exception as e:
                logger.warning(f"⚠️ Auto skill building error: {e}")

        skill_gaps = await self.detect_skill_gaps(agi_kernel)
        if not skill_gaps:
            return

        # Filter out gaps with unknown/generic action types — they're not actionable
        skill_gaps = [g for g in skill_gaps if g.get('action_type', 'unknown') not in ('unknown', 'none', '')]
        if not skill_gaps:
            return

        logger.info(f"🔍 Detected {len(skill_gaps)} skill gaps")
        selfimprove_plugin = self.brain.plugin_manager.get_plugin('selfimprove') if self.brain.plugin_manager else None

        gap = max(skill_gaps, key=lambda g: g['priority'])
        if gap['priority'] < 4:
            return

        logger.info(f"🤖 Auto-generating skill for gap: {gap['description']}")
        try:
            generated = False

            # Prefer selfimprove plugin's full autonomous coder (has AI generation + sandbox + hot-load)
            if hasattr(selfimprove_plugin, '_generate_code_with_ai'):
                task_desc = f"Create a skill to handle: {gap['description']}. "
                if gap.get('error_patterns'):
                    task_desc += f"Must fix these errors: {', '.join(gap['error_patterns'][:3])}"

                if hasattr(selfimprove_plugin, 'self_update_command'):
                    result = selfimprove_plugin.self_update_command(
                        ['create', gap['action_type'].replace(':', '_'), task_desc]
                    )
                    # Handle both string (confirmation needed) and dict (result) returns
                    if isinstance(result, dict) and result.get('success'):
                        logger.info(f"🚀 Self-update generated and deployed: {result.get('plan_id', 'unknown')}")
                        generated = True
                        if agi_kernel and hasattr(agi_kernel, 'episodic_memory'):
                            agi_kernel.episodic_memory.record_episode(
                                action_type='skill_generation',
                                context={'gap': gap, 'result': result},
                                outcome={'success': True, 'deployed': True}
                            )
                    elif isinstance(result, str) and 'pending confirmation' in result.lower():
                        logger.info(f"⏸️ Self-update requires confirmation: {result[:100]}...")
                    else:
                        logger.warning(f"⚠️ Self-update command returned: {result}")

            # Fallback to skeleton autonomous coder if selfimprove is unavailable
            if not generated:
                from src.agentic.autonomous_coder import SkillSpecification, AutonomousCoder

                spec = SkillSpecification(
                    id=f"fix_{gap['action_type'].replace(':', '_')}_{int(datetime.now().timestamp())}",
                    name=f"Fix {gap['action_type']}",
                    description=gap['description'],
                    category='fix',
                    file_structure={
                        '__init__.py': 'Package initialization',
                        'client.py': 'Main skill client',
                        'actions.py': 'Action handlers'
                    },
                    dependencies=[],
                    evidence=gap.get('error_patterns', [])
                )

                coder = AutonomousCoder()
                skill = coder.generate_skill(spec)

                if skill.status == 'generated' and skill.files_created:
                    logger.info(f"✅ Generated skill: {skill.skill_name}")
                    code_to_test = Path(skill.files_created[0]).read_text()
                    if selfimprove_plugin and hasattr(selfimprove_plugin, 'test_code_in_sandbox'):
                        test_result = selfimprove_plugin.test_code_in_sandbox(
                            code=code_to_test,
                            test_code=None
                        )
                        if test_result['success']:
                            coder.deploy_skill(skill)
                            logger.info(f"🚀 Deployed skill: {skill.skill_name}")
                        else:
                            logger.warning(f"⚠️ Skill failed sandbox test: {test_result.get('error', 'Unknown error')}")
                    else:
                        coder.deploy_skill(skill)
                        logger.info(f"🚀 Deployed skill (no sandbox available): {skill.skill_name}")
                elif skill.status == 'generated' and not skill.files_created:
                    logger.warning("⚠️ Skill generated but no files created")
                else:
                    logger.warning(f"⚠️ Skill generation failed: {skill.errors}")
        except Exception as e:
            logger.warning(f"⚠️ Autonomous coding error: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    async def plugin_discovery_and_creation(self, agi_kernel=None) -> None:
        """Detect capability gaps that could be filled by new plugins and auto-generate them.

        Runs every 50 cycles:
        1. Check knowledge graph for platform entities that lack a local plugin
        2. Check self-model for domains with zero capability data (unknown domains)
        3. Generate a PluginSpecification for each gap
        4. Call AutonomousCoder to generate the plugin
        5. Hot-load it via plugin_manager
        """
        if not self.brain.plugin_manager:
            return

        cycle_count = self.brain.stats.get('cycles_completed', 0)
        if cycle_count <= 0 or cycle_count % 50 != 0:
            return

        logger.info("🔌 === Plugin Discovery & Creation ===")

        try:
            from src.agentic.autonomous_coder import (
                PluginSpecification, get_autonomous_coder
            )
            coder = get_autonomous_coder()

            gaps = []

            # 1. Check knowledge graph for platform entities without plugins
            try:
                if self.brain.knowledge_graph:
                    from src.agentic.knowledge_graph import EntityType
                    platform_entities = self.brain.knowledge_graph.get_entities_by_type(EntityType.PLATFORM)
                    loaded_plugins = set()
                    if self.brain.plugin_manager:
                        loaded_plugins = set(self.brain.plugin_manager.plugins.keys())
                    for entity in platform_entities[:5]:
                        pname = entity.name.lower().replace(' ', '_')
                        if pname not in loaded_plugins:
                            gaps.append(PluginSpecification(
                                name=pname,
                                description=f"Auto-discovered platform: {entity.name}",
                                domain='social',
                                platform_url=getattr(entity, 'url', None),
                                evidence=[f"Discovered via knowledge graph entity: {entity.id}"]
                            ))
            except Exception as e:
                logger.debug(f"KG plugin discovery error: {e}")

            # 2. Check curiosity knowledge gaps for domain-level gaps
            try:
                if hasattr(self.brain, 'capability_weaknesses') and self.brain.capability_weaknesses:
                    unknown_domains = set()
                    for w in self.brain.capability_weaknesses:
                        dom = w.get('domain', '')
                        if dom and dom not in ('general', 'unknown'):
                            unknown_domains.add(dom)
                    for domain in unknown_domains:
                        if not any(g.name == domain for g in gaps):
                            gaps.append(PluginSpecification(
                                name=f"{domain}_agent",
                                description=f"Agent for {domain} domain — generated from capability gap",
                                domain='data',
                                evidence=[f"Capability weakness in domain: {domain}"]
                            ))
            except Exception as e:
                logger.debug(f"Capability gap plugin discovery error: {e}")

            # 3. Generate plugins for each gap
            for gap in gaps[:2]:  # Max 2 per cycle
                result = coder.generate_plugin(gap)
                if result.status == 'generated':
                    logger.info(f"   ✅ Generated plugin: {gap.name}")
                    # Hot-load it
                    try:
                        pm = self.brain.plugin_manager
                        if pm and hasattr(pm, 'load_plugin'):
                            import inspect
                            sig = inspect.signature(pm.load_plugin)
                            if len(sig.parameters) >= 4:
                                pm.load_plugin(gap.name, {'config': {}, 'enabled': True}, None, None)
                            else:
                                pm.load_plugin(gap.name, {'config': {}, 'enabled': True})
                            logger.info(f"   🔌 Hot-loaded plugin: {gap.name}")

                            # Register commands with intent classifier
                            try:
                                from plugins.telegram.intent_classifier import get_intent_classifier
                                classifier = get_intent_classifier()
                                plugin = pm.plugins.get(gap.name)
                                if plugin and classifier:
                                    for cmd_name, func in plugin.get_commands().items():
                                        doc = (func.__doc__ or f"Execute {cmd_name}").split('\\n')[0].strip()
                                        classifier.register_command(cmd_name, doc)
                            except Exception as e:
                                logger.debug("Non-critical error: %s", e)
                            # Tell the self-model a new capability was learned
                            if self.brain.cognitive and hasattr(self.brain.cognitive, 'self_model'):
                                self.brain.cognitive.self_model.record_outcome(
                                    domain=gap.domain,
                                    action_type=f"plugin_{gap.name}",
                                    success=True,
                                    confidence=0.8,
                                )
                    except Exception as e:
                        logger.warning(f"   ⚠️ Hot-load failed for {gap.name}: {e}")
                else:
                    logger.warning(f"   ⚠️ Plugin generation failed for {gap.name}: {result.errors}")

            if not gaps:
                logger.info("   No plugin gaps found")

        except Exception as e:
            logger.debug(f"Plugin discovery error: {e}")

    async def detect_skill_gaps(self, agi_kernel) -> List[Dict]:
        """
        Detect capability gaps that require new skills.

        This is VERTICAL intelligence - identifying what we need to learn.

        Analyzes:
        1. Repeated failures (3+ failures = skill gap)
        2. Missing capabilities (referenced but not implemented)
        3. Performance bottlenecks (slow actions)

        Returns:
            List of skill gap dicts with priority scores
        """
        skill_gaps = []

        try:
            # 1. Analyze recent failures from episodic memory
            if hasattr(agi_kernel, 'episodic_memory'):
                recent_failures = []

                # Get recent failure episodes
                try:
                    recent_failures = agi_kernel.episodic_memory.get_recent_episodes(
                        filters={'outcome': 'failure'},
                        limit=50
                    )
                except Exception as e:
                    logger.warning(f"Episodic memory query failed: {e}")
                    recent_failures = []

                # Group failures by action type
                failure_patterns = {}
                for episode in recent_failures:
                    action_type = episode.action
                    if action_type not in failure_patterns:
                        failure_patterns[action_type] = []
                    failure_patterns[action_type].append(episode)

                # Identify repeated failures (skill gap indicator)
                for action_type, failures in failure_patterns.items():
                    if len(failures) >= 3:  # 3+ failures = skill gap
                        error_patterns = []
                        for f in failures:
                            error = f.outcome
                            if error not in error_patterns:
                                error_patterns.append(error)

                        skill_gaps.append({
                            'type': 'repeated_failure',
                            'action_type': action_type,
                            'failure_count': len(failures),
                            'error_patterns': error_patterns[:5],  # Top 5 unique errors
                            'priority': min(10, len(failures) * 2),  # More failures = higher priority
                            'description': f"Repeated failures in {action_type} - need better implementation"
                        })

            # 2. Analyze missing capabilities from action logger
            if hasattr(agi_kernel, 'action_router'):
                try:
                    from src.agentic.action_logger import get_action_logger
                    action_logger = get_action_logger()

                    # Get recent actions with "not found" errors
                    recent_actions = await action_logger.aget_recent_outcomes(limit=50)

                    for action in recent_actions:
                        error = action.get('error', '')
                        if 'not found' in error.lower() or 'missing' in error.lower():
                            action_type = action.get('action_type', 'unknown')
                            plugin = action.get('plugin', 'unknown')

                            skill_gaps.append({
                                'type': 'missing_capability',
                                'action_type': action_type,
                                'plugin': plugin,
                                'priority': 7,
                                'description': f"Missing capability: {action_type} in {plugin}",
                                'error_patterns': [error]
                            })
                except Exception as e:
                    logger.debug(f"Missing capability detection error: {e}")

            # 3. Analyze performance bottlenecks
            if hasattr(agi_kernel, 'action_router'):
                try:
                    from src.agentic.action_logger import get_action_logger
                    action_logger = get_action_logger()

                    # Get actions with high duration
                    recent_actions = await action_logger.aget_recent_outcomes(limit=50)

                    # Group by action type and calculate avg duration
                    action_durations = {}
                    for action in recent_actions:
                        action_type = action.get('action_type', 'unknown')
                        duration = action.get('duration_ms', 0)

                        if action_type not in action_durations:
                            action_durations[action_type] = []
                        action_durations[action_type].append(duration)

                    # Identify slow actions (avg > 5000ms)
                    for action_type, durations in action_durations.items():
                        if len(durations) >= 3:
                            avg_duration = sum(durations) / len(durations)
                            if avg_duration > 5000:
                                skill_gaps.append({
                                    'type': 'performance_bottleneck',
                                    'action_type': action_type,
                                    'avg_duration_ms': avg_duration,
                                    'priority': 6,
                                    'description': f"Slow action: {action_type} ({avg_duration:.0f}ms avg)",
                                    'error_patterns': []
                                })
                except Exception as e:
                    logger.debug(f"Performance bottleneck detection error: {e}")

            # 6.5: Wire skill gap detection to SelfModel belief data
            try:
                from src.agentic.self_model import get_self_model
                self_model = get_self_model()

                # Get learning priorities from SelfModel
                learning_priorities = self_model.what_should_i_learn()

                for item in learning_priorities:
                    skill_gaps.append({
                        'type': 'belief_driven_learning',
                        'domain': item.get('domain', 'unknown'),
                        'action_type': item.get('action_type', 'unknown'),
                        'reason': item.get('reason', 'unknown'),
                        'sample_size': item.get('sample_size', 0),
                        'success_rate': item.get('success_rate', 0),
                        'priority': 8 if item.get('priority') == 'high' else 5,
                        'description': f"Belief-driven: {item.get('reason')} - {item.get('action_type')}",
                        'error_patterns': [f"Low confidence due to {item.get('reason')}"]
                    })
                logger.debug(f"Added {len(learning_priorities)} belief-driven skill gaps")
            except Exception as e:
                logger.debug(f"SelfModel integration error: {e}")

        except Exception as e:
            logger.debug(f"Skill gap detection error: {e}")

        return skill_gaps

    def propose_architecture_changes(self) -> List[str]:
        """Analyze recent performance and propose configuration adjustments.

        Self-directed architecture modification:
        - If calibration error is high → suggest lowering min_confidence
        - If too many actions blocked → suggest reducing max_actions_per_hour
        - If success rate is low → suggest increasing min_confidence
        - If curiosity gaps found → suggest enabling more observation sources
        Returns a list of human-readable change descriptions.
        """
        changes = []

        try:
            # Check calibration error
            if self.brain.cognitive:
                calibration = self.brain.cognitive.get_belief_calibration()
                mae = calibration.get('mean_absolute_error', 0)
                if mae > 0.25:
                    old = self.brain.config.min_confidence
                    new = max(0.3, old * 0.9)
                    changes.append(f"Raise min_confidence from {old:.2f} to {new:.2f} (high calibration error {mae:.2f})")
                elif mae < 0.05 and self.brain.config.min_confidence < 0.5:
                    old = self.brain.config.min_confidence
                    new = min(0.5, old * 1.1)
                    changes.append(f"Lower min_confidence from {old:.2f} to {new:.2f} (low calibration error {mae:.2f})")

            # Check block rate
            blocked = self.brain.stats.get('actions_blocked', 0)
            total = max(self.brain.stats.get('proposals_generated', 1), 1)
            block_rate = blocked / total
            if block_rate > 0.5:
                changes.append(f"Reduce max_actions_per_hour from {self.brain.config.max_actions_per_hour} "
                               f"to {self.brain.config.max_actions_per_hour // 2} (block rate {block_rate:.0%})")

            # Check self-model weaknesses
            if hasattr(self.brain, 'capability_weaknesses') and self.brain.capability_weaknesses:
                weak_domains = set(w.get('domain', '') for w in self.brain.capability_weaknesses[:3])
                if weak_domains:
                    changes.append(f"Prioritize practice in domains: {', '.join(weak_domains)}")

        except Exception as e:
            logger.debug(f"Architecture proposal error: {e}")

        return changes

    async def _phase_self_code_modification(self, agi_kernel=None) -> None:
        """Detection phase — identify repeated failures and generate bug reports.

        Runs every 50 cycles. Checks error_recovery circuit breaker for patterns
        of repeated failures. If same action failing repeatedly (3+ times),
        generates a bug report and saves it to episodic memory.

        This is the "detection" phase only — no files are written.
        Bug reports are consumed by _phase_review_and_apply_fixes.
        """
        cycle_count = self.brain.stats.get('cycles_completed', 0)

        # Only run every 50 cycles
        if cycle_count <= 0 or cycle_count % 50 != 0:
            return

        logger.info("🔧 === Self Code Modification Phase (Detection) ===")

        try:
            from src.agentic.error_recovery import get_error_recovery

            # Get error recovery system
            plugin_manager = getattr(self.brain, 'plugin_manager', None)
            error_recovery = get_error_recovery(plugin_manager)

            bug_reports = []

            # Check circuit breakers from error recovery system
            if error_recovery:
                error_summary = error_recovery.get_error_summary()
                circuit_breakers = error_summary.get('circuit_breakers', {})

                for component, is_open in circuit_breakers.items():
                    if not is_open:
                        continue

                    failures_count = error_summary.get('component_failures', {}).get(component, 0)
                    if failures_count < 3:
                        continue

                    recent_errors = error_summary.get('recent_errors', [])
                    component_errors = [
                        e for e in recent_errors if e.get('component') == component
                    ]
                    error_patterns = list(set(
                        e.get('error_type', 'unknown') for e in component_errors
                    ))

                    bug_reports.append({
                        'component': component,
                        'failure_count': failures_count,
                        'circuit_breaker_tripped': True,
                        'error_patterns': error_patterns,
                        'detected_at': datetime.now().isoformat(),
                        'severity': 'high' if failures_count >= 5 else 'medium',
                        'description': (
                            f"Repeated failure pattern detected in {component}: "
                            f"{failures_count} failures, "
                            f"patterns: {', '.join(error_patterns[:3])}"
                        ),
                    })

            # Check episodic memory for repeated action failures
            if agi_kernel and hasattr(agi_kernel, 'episodic_memory'):
                try:
                    recent_failures = agi_kernel.episodic_memory.get_recent_episodes(
                        filters={'outcome': 'failure'},
                        limit=50
                    )

                    # Group by action type
                    failure_patterns = {}
                    for episode in recent_failures:
                        action_type = (
                            getattr(episode, 'action', None)
                            or getattr(episode, 'action_type', 'unknown')
                        )
                        if action_type not in failure_patterns:
                            failure_patterns[action_type] = []
                        failure_patterns[action_type].append(episode)

                    # 3+ failures of same action = bug
                    for action_type, episodes in failure_patterns.items():
                        if len(episodes) >= 3:
                            error_messages = []
                            for ep in episodes[:5]:
                                msg = (
                                    getattr(ep, 'outcome', '')
                                    or getattr(ep, 'error', '')
                                    or ''
                                )
                                if msg and msg not in error_messages:
                                    error_messages.append(msg)

                            bug_reports.append({
                                'component': f"action:{action_type}",
                                'failure_count': len(episodes),
                                'circuit_breaker_tripped': False,
                                'error_patterns': error_messages,
                                'detected_at': datetime.now().isoformat(),
                                'severity': 'medium' if len(episodes) < 5 else 'high',
                                'description': (
                                    f"Repeated failure in action '{action_type}': "
                                    f"{len(episodes)} failures, "
                                    f"errors: {', '.join(error_messages[:3])}"
                                ),
                            })
                except Exception as e:
                    logger.debug(f"Episodic memory failure analysis error: {e}")

            if not bug_reports:
                logger.info("   No bug patterns detected")
                return

            logger.info(f"   Detected {len(bug_reports)} bug pattern(s)")

            # Save bug reports to episodic memory
            memory_system = None
            if agi_kernel and hasattr(agi_kernel, 'episodic_memory'):
                memory_system = agi_kernel.episodic_memory
            elif hasattr(self.brain, 'memory') and self.brain.memory:
                memory_system = self.brain.memory

            if memory_system and hasattr(memory_system, 'record_episode'):
                for report in bug_reports:
                    try:
                        memory_system.record_episode(
                            action_type='bug_detection',
                            context={
                                'component': report['component'],
                                'severity': report['severity'],
                            },
                            outcome={
                                'detected': True,
                                'description': report['description'],
                                'failure_count': report['failure_count'],
                                'error_patterns': report['error_patterns'],
                            },
                            success=False,
                            emotional_valence=-0.6,
                            trigger_patterns=[
                                f"bug:{report['component']}",
                                f"failure:{report['component']}",
                            ],
                        )
                        logger.info(f"   📝 Bug report saved to memory: {report['component']}")
                    except Exception as e:
                        logger.debug(f"Failed to save bug report to memory: {e}")
            else:
                logger.info("   No episodic memory system available — bug reports stored on brain only")

            # Store bug reports on brain for review phase to consume
            if not hasattr(self.brain, '_pending_bug_reports'):
                self.brain._pending_bug_reports = []
            self.brain._pending_bug_reports.extend(bug_reports)
            logger.info(f"   Stored {len(bug_reports)} bug report(s) for review phase")

        except Exception as e:
            logger.warning(f"⚠️ Self code modification detection error: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    async def _phase_review_and_apply_fixes(self, agi_kernel=None) -> None:
        """Review phase — generate fix patches for detected bugs (propose, don't apply).

        Runs every 50 cycles, after _phase_self_code_modification.
        Calls autonomous_coder.generate_bugfix_patch() for each detected bug
        and logs the generated patches for owner review.

        This is a safety-first "propose, don't apply" pattern.
        """
        cycle_count = self.brain.stats.get('cycles_completed', 0)

        # Only run every 50 cycles
        if cycle_count <= 0 or cycle_count % 50 != 0:
            return

        # Get pending bug reports from the detection phase
        pending = getattr(self.brain, '_pending_bug_reports', [])
        if not pending:
            return

        logger.info(f"📋 === Review & Apply Fixes Phase ({len(pending)} bug report(s)) ===")

        try:
            from src.agentic.autonomous_coder import AutonomousCoder

            coder = AutonomousCoder()

            # Initialize container on brain for proposed fixes
            if not hasattr(self.brain, '_proposed_fixes'):
                self.brain._proposed_fixes = []

            # Process each bug report
            for report in pending:
                component = report.get('component', 'unknown')
                failure_count = report.get('failure_count', 0)
                error_patterns = report.get('error_patterns', [])
                description = report.get('description', 'Unknown bug')

                logger.info(f"   🔍 Analysing bug: {component} ({failure_count} failure(s))")

                # Map component to a source file path
                source_file = self._map_component_to_source_file(component)
                if not source_file:
                    logger.warning(f"   ⚠️  Cannot map component '{component}' to a source file, skipping")
                    continue

                # Build error log string from patterns
                error_log = '\n'.join([
                    f"Failure #{i + 1}: {pattern}"
                    for i, pattern in enumerate(error_patterns)
                ])

                # Generate fix patch (propose, don't apply)
                fix_result = coder.generate_bugfix_patch(
                    source_file=source_file,
                    error_log=error_log,
                    bug_description=description,
                )

                if fix_result.get('patch'):
                    logger.info(
                        f"   ✅ Generated fix for {component}:\n"
                        f"      File: {fix_result['file']}\n"
                        f"      Confidence: {fix_result['confidence']:.2f}\n"
                        f"      Description: {fix_result['description']}\n"
                        f"      Patch size: {len(fix_result['patch'])} chars"
                    )

                    # Log the full patch for owner review — safety first, never auto-apply
                    logger.info(
                        f"   📝 Proposed patch for {component} (NOT applied — owner review required):\n"
                        f"{'=' * 60}\n"
                        f"{fix_result['patch']}\n"
                        f"{'=' * 60}"
                    )

                    # Store for owner to review later
                    self.brain._proposed_fixes.append(fix_result)
                else:
                    logger.warning(
                        f"   ⚠️  Failed to generate fix for {component}: "
                        f"{fix_result.get('description', 'Unknown error')}"
                    )

            # Clear pending bug reports after processing
            self.brain._pending_bug_reports = []

            total_proposed = len(self.brain._proposed_fixes)
            logger.info(f"   📋 Total proposed fixes stored for owner review: {total_proposed}")

        except Exception as e:
            logger.warning(f"⚠️ Self code modification review phase error: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    def _map_component_to_source_file(self, component: str) -> Optional[str]:
        """Map a component/action name to its source file path.

        Args:
            component: Component name (e.g., 'brain', 'action:process', 'moltx')

        Returns:
            Absolute path to the source file, or None if unknown
        """
        if not component:
            return None

        # Action-based components: action:<action_type>
        if component.startswith('action:'):
            action_name = component.split(':', 1)[1]
            # Try common locations for action handlers
            candidates = [
                f"src/agentic/actions/{action_name}.py",
                f"src/agentic/handlers/{action_name}.py",
                f"plugins/{action_name}/{action_name}.py",
            ]
            for candidate in candidates:
                p = Path(candidate)
                if p.exists():
                    return str(p.resolve())
            # Fallback: return a reasonable guess
            return str(Path(f"src/agentic/actions/{action_name}.py").resolve())

        # Known core components with well-defined source files
        component_map = {
            'brain': 'src/agentic/autonomous_brain.py',
            'moltx': 'plugins/moltx/moltx.py',
            'telegram': 'plugins/telegram/telegram.py',
            'self_improve': 'src/agentic/brain/self_improve.py',
            'cycle_coordinator': 'src/agentic/brain/cycle_coordinator.py',
            'autonomous_coder': 'src/agentic/autonomous_coder.py',
            'error_recovery': 'src/agentic/error_recovery.py',
            'episodic_memory': 'src/agentic/episodic_memory.py',
            'action_logger': 'src/agentic/action_logger.py',
            'cognitive_integration': 'src/agentic/cognitive_integration.py',
            'knowledge_graph': 'src/agentic/knowledge_graph.py',
            'self_model': 'src/agentic/self_model.py',
            'belief_engine': 'src/agentic/belief_engine.py',
            'goal_planner': 'src/agentic/goal_planner.py',
            'curiosity': 'src/agentic/curiosity.py',
        }

        if component in component_map:
            return str(Path(component_map[component]).resolve())

        # Generic fallback: try to find the component as a module path
        generic_path = f"src/agentic/{component.replace(':', '/').replace('.', '/')}.py"
        p = Path(generic_path)
        if p.exists():
            return str(p.resolve())

        # Last resort: return the best guess
        return str(Path(generic_path).resolve())

    @staticmethod
    def is_action_implemented(plugin: str, action: str) -> bool:
        """Check if a plugin/action combo has a real implementation (not None)."""
        try:
            from src.agentic.action_router import ActionRouter
            return ActionRouter.is_action_valid(plugin, action)
        except Exception:
            return False  # fail closed — don't risk unknown actions


def create_brain_self_improve(brain) -> BrainSelfImprove:
    """Factory to create BrainSelfImprove with brain reference."""
    return BrainSelfImprove(brain)
