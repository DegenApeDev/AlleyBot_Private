#!/usr/bin/env python3
"""
Strip duplicated phase methods from autonomous_brain.py and replace with
thin delegations to the CycleCoordinator brain modules.

Safe: all phase methods have been extracted to brain/{sense,think,act,learn,trading,self_improve}.py
and _execute_cycle now routes through self.coordinator.
"""
import re
import ast
import sys
from pathlib import Path

FILE = Path("/home/degendev/Dev/Agents/AlleyBot_Private/src/agentic/autonomous_brain.py")
content = FILE.read_text()

# Methods to strip — grouped by target coordinator attribute
DELEGATIONS = {
    # SENSE
    "_gather_observations": "coordinator.gather_observations()",
    "_gather_observations_sync": None,  # only called by _gather_observations which is stripped
    "_feed_observations_to_world_state": "coordinator.feed_observations_to_world_state(observations)",
    "_phase_detect_opportunities": "coordinator.detect_opportunities()",
    "_build_runtime_spine_context": "coordinator.build_spine_context(observations=observations, active_work_items=active_work_items, opportunities=opportunities)",
    
    # THINK
    "_get_proposals": "coordinator.think.get_proposals()",
    "_apply_meta_learning_bias": "coordinator.think.apply_meta_learning_bias(proposals)",
    "_apply_transfer_learning_bias": "coordinator.think.apply_transfer_learning_bias(proposals)",
    "_apply_active_goal_bias": "coordinator.think.apply_active_goal_bias(proposals)",
    "_apply_active_work_item_bias": "coordinator.think.apply_active_work_item_bias(proposals, active_work_items)",
    "_apply_runtime_spine_bias": "coordinator.think.apply_runtime_spine_bias(proposals, spine_context)",
    "_apply_cognitive_bias": "coordinator.think.apply_cognitive_bias(proposals)",
    "_prioritize_runtime_spine_proposals": "coordinator.think.prioritize_runtime_spine_proposals(proposals, spine_context)",
    "_get_recent_routed_outcomes": "coordinator.think.get_recent_routed_outcomes(limit)",
    "_estimate_predicted_value": "coordinator.think.estimate_predicted_value(proposal)",
    "_recall_memory_signals": "coordinator.think.recall_memory_signals(proposal)",
    "_apply_memory_shaped_ranking": "coordinator.think.apply_memory_shaped_ranking(proposals)",
    "_run_agi_orchestration_cycle": "coordinator.run_agi_orchestration()",
    "_convert_agi_action_to_proposal": "coordinator.think.convert_agi_action_to_proposal(agi_action, phases_executed)",
    "_extract_creative_proposals": "coordinator.think.extract_creative_proposals(creative_output, phases_executed)",
    "_phase_memory_driven_thinking": "coordinator.memory_driven_thinking(observations, agi_kernel)",
    "_phase_assemble_proposals": "coordinator.assemble_proposals(agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals, revenue_proposals, curiosity_proposals, intent_proposals)",
    "_phase_curiosity_goals": "coordinator.curiosity_goals(agi_kernel)",
    "_phase_maintain_persistent_intents": "coordinator.maintain_persistent_intents(agi_kernel)",
    "_phase_goal_management": "coordinator.goal_management(agi_kernel, observations)",
    "_phase_cross_domain_synthesis_and_planning": "coordinator.cross_domain_synthesis(agi_kernel, observations, proposals)",
    "_handle_idle_state": "coordinator.handle_idle_state(active_work_items, proposals, spine_context)",
    "_advance_active_plans": "coordinator.advance_active_plans(agi_kernel)",
    "_generate_default_goals": "coordinator.generate_default_goals()",
    "_generate_proactive_goals": "coordinator.think.generate_proactive_goals(observations)",
    "_generate_curiosity_goals": "coordinator.think.generate_curiosity_goals()",
    "_adversarial_self_critique": "coordinator.think.adversarial_self_critique(agi_kernel)",
    "_map_intent_action_to_plugin": None,  # static-like utility, not worth delegating
    
    # ACT
    "_phase_execute_proposals": "coordinator.execute_proposals(proposals, agi_kernel, next_action)",
    "_record_proposal_success": "coordinator.act._record_proposal_success(proposal, result, agi_kernel, next_action)",
    "_record_proposal_failure": "coordinator.act._record_proposal_failure(proposal, agi_kernel)",
    "_execute_proposal": "coordinator.act._execute_proposal(proposal)",  # already done
    "_notify_user_of_goal_result": "coordinator.act._notify_user_of_goal_result(proposal, result)",
    "_phase_chess_win_posts": "coordinator.post_chess_wins()",
    "_check_for_quick_profit_actions": "coordinator.quick_profit_actions(checkpoint)",
    
    # LEARN
    "_phase_periodic_reflection": "coordinator.periodic_reflection(agi_kernel)",
    "_phase_consolidate_learning": "coordinator.consolidate_learning(agi_kernel)",
    "_phase_meta_adaptation": "coordinator.meta_adaptation(agi_kernel)",
    "_phase_causal_reasoning": "coordinator.causal_reasoning(observations, agi_kernel)",
    "_phase_theory_of_mind": "coordinator.theory_of_mind(observations)",
    "_phase_learning_goal_acquisition": "coordinator.learning_acquisition(agi_kernel)",
    
    # TRADING
    "_phase_revenue_intelligence": "coordinator.revenue_intelligence(agi_kernel)",
    
    # SELF-IMPROVE
    "_phase_skill_gap_analysis": "coordinator.skill_gap_analysis(observations, agi_kernel)",
    "_phase_plugin_discovery_and_creation": "coordinator.plugin_discovery(agi_kernel)",
    "_detect_skill_gaps": "coordinator.self_improve.detect_skill_gaps(agi_kernel)",
    "_propose_architecture_changes": "coordinator.self_improve.propose_architecture_changes()",
    "_is_action_implemented": "coordinator.self_improve.is_action_implemented(plugin, action)",
    
    # SOCIAL (kept on AutonomousBrain, not extracted)
    # "_run_agi_social_cycle" — stays
    # "_run_agi_social_cycle_sync" — stays
    # "_generate_post_from_concept" — stays
    # "_extract_market_state" — stays
    # "_extract_social_state" — stays
}

def make_delegation_body(method_name, delegation_expr):
    """Create the new method body with proper indentation."""
    if delegation_expr is None:
        # Remove entirely — not referenced externally
        return None
    
    # Determine if async
    pattern = re.compile(rf'^(?P<indent>(?:    )+?)(?P<async>async )?def {re.escape(method_name)}\(', re.MULTILINE)
    match = pattern.search(content)
    if not match:
        print(f"⚠️  Could not find method: {method_name}")
        return None
    
    is_async = bool(match.group('async'))
    indent = match.group('indent')
    
    if is_async:
        body = f'{indent}"""Delegate to brain module."""\n'
        body += f'{indent}return await self.{delegation_expr}\n'
    elif method_name == '_build_runtime_spine_context':
        # Special case — building a dict
        body = f'{indent}"""Delegate to brain module."""\n'
        body += f'{indent}return self.{delegation_expr}\n'
    elif method_name == '_handle_idle_state':
        body = f'{indent}"""Delegate to brain module."""\n'
        body += f'{indent}return self.{delegation_expr}\n'
    elif method_name == '_is_action_implemented':
        body = f'{indent}"""Delegate to brain module."""\n'
        body += f'{indent}return self.{delegation_expr}\n'
    else:
        body = f'{indent}"""Delegate to brain module."""\n'
        body += f'{indent}return self.{delegation_expr}\n'
    
    return body

# Process each method
for method_name, delegation in DELEGATIONS.items():
    if delegation is None:
        # Remove method entirely — strip from def to next def or class end
        pattern = re.compile(
            rf'^(?P<indent>(?:    )+?)(?:async )?def {re.escape(method_name)}\(.*?(\n(?!\1(?:async )?def |\1class |\Z|$))+\Z',
            re.MULTILINE | re.DOTALL
        )
        new_content, count = pattern.subn('', content, count=1)
        if count > 0:
            content = new_content
            print(f"🗑️  Removed {method_name} (no delegation)")
        continue
    
    body = make_delegation_body(method_name, delegation)
    if body is None:
        continue
    
    # Find the method definition and replace everything after the signature line
    # until the next method at the same indentation level
    pattern = re.compile(
        rf'^(?P<indent>(?:    )+?)(?:async )?def {re.escape(method_name)}\(.*?(\n(?!(?P=indent)(?:async )?def |(?P=indent)class |\Z))+\Z',
        re.MULTILINE | re.DOTALL
    )
    
    # Get original method to extract its signature line
    sig_match = re.search(
        rf'^(?P<indent>(?:    )+?)(?P<async>async )?def {re.escape(method_name)}\(',
        content, re.MULTILINE
    )
    if not sig_match:
        print(f"⚠️  Signature not found: {method_name}")
        continue
    
    # Find end of signature (the line with :) 
    start = sig_match.start()
    # Find the end of the signature line (first : that's not in a type hint)
    sig_end_match = re.search(r':\s*$', content[sig_match.start():sig_match.end() + 200], re.MULTILINE)
    if not sig_end_match:
        print(f"⚠️  Could not find end of signature for {method_name}")
        continue
    
    # Now find where the body ends — next def at same indent or end of file
    indent = sig_match.group('indent')
    body_start = sig_match.start() + sig_end_match.end() + 1  # +1 for the newline after :
    
    rest = content[body_start:]
    next_method = re.search(rf'\n{indent}(?:async )?def ', rest)
    if next_method:
        body_end = body_start + next_method.start()
    else:
        body_end = len(content)
    
    # Replace everything between the signature and the next method
    new_block = content[start:body_start] + body
    
    # Remove trailing blank lines from old body
    old_body = content[body_start:body_end]
    # Strip trailing whitespace/newlines from old body
    stripped_old = old_body.rstrip('\n')
    
    content = content[:body_start] + body.rstrip('\n') + '\n\n' + content[body_end:]
    print(f"✅ {method_name} → delegated")

FILE.write_text(content)
print(f"\n📏 New file size: {len(content.splitlines())} lines")
