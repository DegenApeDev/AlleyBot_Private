"""
Dynamic Skills Mixin for Phase 8
Integrates capability gap detection, auto-skill generation, performance tracking,
skill versioning, and dynamic skill chaining into the brain.
"""
import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


class DynamicSkillsMixin:
    """Mixin for dynamic skill generation and management"""
    
    # Mixin metadata for documentation and validation
    REQUIRES = ["context"]
    PROVIDES = ["generate_skill", "execute_skill", "skill_registry"]
    INIT_ORDER = 8

    def _init_dynamic_skills(self):
        """Initialize dynamic skills tracking"""
        self.skill_performance: Dict[str, Dict] = {}
        self.skill_registry: Dict[str, Dict] = {}
        self.generated_skills_dir = Path('dynamic_skills')
        self.generated_skills_dir.mkdir(exist_ok=True)
        self.skill_versions: Dict[str, List[Dict]] = {}
        self._load_skill_state()

    def _load_skill_state(self):
        """Load skill performance and registry state"""
        try:
            state = self.core.get_memory('brain_skill_state')
            if state:
                self.skill_performance = state.get('performance', {})
                self.skill_registry = state.get('registry', {})
                self.skill_versions = state.get('versions', {})
        except Exception:
            pass

    def _save_skill_state(self):
        """Save skill state to memory"""
        try:
            self.core.save_memory('brain_skill_state', {
                'performance': self.skill_performance,
                'registry': self.skill_registry,
                'versions': self.skill_versions,
                'last_saved': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️  Failed to save skill state: {e}")

    def detect_capability_gap(self, action_id: str, error_output: str) -> Optional[str]:
        """
        Detect if an action failed due to missing capability
        Returns description of the gap if detected
        """
        # Common patterns indicating skill gaps
        gap_patterns = [
            ("no attribute", "missing_method"),
            ("not found", "missing_command"),
            ("cannot", "missing_capability"),
            ("unable to", "missing_capability"),
            ("no module", "missing_import"),
            ("key error", "missing_config"),
            ("not loaded", "missing_plugin"),
        ]

        error_lower = error_output.lower()
        for pattern, gap_type in gap_patterns:
            if pattern in error_lower:
                # Extract what was missing
                gap_desc = self._extract_gap_description(action_id, error_output, gap_type)
                return gap_desc

        return None

    def _extract_gap_description(self, action_id: str, error: str, gap_type: str) -> str:
        """Extract a descriptive gap from error message"""
        if gap_type == "missing_method":
            return f"Method or function needed for {action_id} not available"
        elif gap_type == "missing_command":
            return f"Command handler for {action_id} not registered"
        elif gap_type == "missing_plugin":
            plugin = action_id.split('_')[0] if '_' in action_id else action_id
            return f"Plugin '{plugin}' not loaded but required for {action_id}"
        else:
            return f"Capability gap for {action_id}: {gap_type}"

    def auto_generate_skill(self, gap_description: str, action_id: str) -> Dict[str, Any]:
        """
        Auto-generate a skill to fill a capability gap
        Returns result dict with success status and skill info
        """
        print(f"🔧 Auto-generating skill for gap: {gap_description[:60]}...")

        # Check if self-improve plugin is available
        selfimprove = self.core.plugin_manager.plugins.get('selfimprove')
        if not selfimprove:
            return {'success': False, 'error': 'Self-improve plugin not available'}

        try:
            # Generate skill name
            skill_name = f"skill_{action_id}_{int(time.time())}"
            skill_file = self.generated_skills_dir / f"{skill_name}.py"

            # Use the skill generator if available
            if hasattr(selfimprove, 'skill_generator') or hasattr(selfimprove, 'generate_skill'):
                # Generate the skill
                result = self._generate_skill_with_selfimprove(gap_description, skill_name)

                if result.get('success'):
                    # Register the skill
                    self._register_generated_skill(skill_name, gap_description, result)
                    return {
                        'success': True,
                        'skill_name': skill_name,
                        'skill_file': str(skill_file),
                        'description': gap_description
                    }
                else:
                    return result
            else:
                return {'success': False, 'error': 'Skill generator not available in self-improve plugin'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_skill_with_selfimprove(self, gap_description: str, skill_name: str) -> Dict:
        """Generate skill using self-improvement plugin"""
        selfimprove = self.core.plugin_manager.plugins.get('selfimprove')

        # Try different methods depending on what's available
        if hasattr(selfimprove, 'generate_skill'):
            return selfimprove.generate_skill(gap_description, skill_name)
        elif hasattr(selfimprove, 'skill_generator'):
            sg = selfimprove.skill_generator
            if hasattr(sg, 'generate_skill_code'):
                code = sg.generate_skill_code(gap_description)
                if code:
                    # Save the skill file
                    skill_file = self.generated_skills_dir / f"{skill_name}.py"
                    skill_file.write_text(code)
                    return {'success': True, 'code': code}
                return {'success': False, 'error': 'Failed to generate skill code'}

        return {'success': False, 'error': 'No skill generation method available'}

    def _register_generated_skill(self, skill_name: str, description: str, result: Dict):
        """Register a newly generated skill"""
        self.skill_registry[skill_name] = {
            'name': skill_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'file': str(self.generated_skills_dir / f"{skill_name}.py"),
            'status': 'active',
            'version': 1,
            'hash': self._compute_skill_hash(skill_name)
        }

        # Initialize performance tracking
        self.skill_performance[skill_name] = {
            'uses': 0,
            'successes': 0,
            'failures': 0,
            'last_used': None,
            'average_execution_time': 0
        }

        # Add to versions
        if skill_name not in self.skill_versions:
            self.skill_versions[skill_name] = []
        self.skill_versions[skill_name].append({
            'version': 1,
            'created_at': datetime.now().isoformat(),
            'hash': self._compute_skill_hash(skill_name)
        })

        self._save_skill_state()
        print(f"✅ Skill '{skill_name}' registered and ready for use")

    def _compute_skill_hash(self, skill_name: str) -> str:
        """Compute hash of skill file for versioning"""
        try:
            skill_file = self.generated_skills_dir / f"{skill_name}.py"
            if skill_file.exists():
                content = skill_file.read_text()
                return hashlib.md5(content.encode()).hexdigest()[:8]
        except Exception:
            pass
        return "unknown"

    def track_skill_performance(self, skill_name: str, success: bool, execution_time: float = 0):
        """Track performance of a skill"""
        if skill_name not in self.skill_performance:
            self.skill_performance[skill_name] = {
                'uses': 0,
                'successes': 0,
                'failures': 0,
                'last_used': None,
                'average_execution_time': 0
            }

        perf = self.skill_performance[skill_name]
        perf['uses'] += 1
        perf['last_used'] = datetime.now().isoformat()

        if success:
            perf['successes'] += 1
        else:
            perf['failures'] += 1

        # Update average execution time
        if execution_time > 0:
            old_avg = perf['average_execution_time']
            perf['average_execution_time'] = (old_avg * (perf['uses'] - 1) + execution_time) / perf['uses']

        self._save_skill_state()

    def check_skill_needs_update(self, skill_name: str) -> bool:
        """Check if a skill needs to be updated (based on failure rate)"""
        if skill_name not in self.skill_performance:
            return False

        perf = self.skill_performance[skill_name]
        if perf['uses'] < 3:  # Not enough data
            return False

        failure_rate = perf['failures'] / perf['uses']
        return failure_rate > 0.5  # Update if >50% failure rate

    def update_skill(self, skill_name: str, new_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update/regenerate a skill that's failing
        Returns result dict
        """
        print(f"🔄 Updating skill: {skill_name}")

        if skill_name not in self.skill_registry:
            return {'success': False, 'error': f'Skill {skill_name} not found in registry'}

        skill_info = self.skill_registry[skill_name]
        description = new_description or skill_info['description']

        # Generate new version
        result = self._generate_skill_with_selfimprove(description, f"{skill_name}_v2")

        if result.get('success'):
            # Archive old version
            old_file = Path(skill_info['file'])
            if old_file.exists():
                archive_dir = self.generated_skills_dir / 'archive'
                archive_dir.mkdir(exist_ok=True)
                archive_file = archive_dir / f"{skill_name}_v{skill_info['version']}.py"
                old_file.rename(archive_file)

            # Update registry with new version
            skill_info['version'] += 1
            skill_info['file'] = str(self.generated_skills_dir / f"{skill_name}_v2.py")
            skill_info['hash'] = self._compute_skill_hash(f"{skill_name}_v2")
            skill_info['updated_at'] = datetime.now().isoformat()

            # Add to versions history
            self.skill_versions[skill_name].append({
                'version': skill_info['version'],
                'created_at': datetime.now().isoformat(),
                'hash': skill_info['hash']
            })

            # Reset performance tracking for new version
            self.skill_performance[skill_name] = {
                'uses': 0,
                'successes': 0,
                'failures': 0,
                'last_used': None,
                'average_execution_time': 0
            }

            self._save_skill_state()
            return {'success': True, 'new_version': skill_info['version']}

        return result

    def get_skill_analytics(self) -> Dict[str, Any]:
        """Get analytics on all generated skills"""
        total_skills = len(self.skill_registry)
        total_uses = sum(p['uses'] for p in self.skill_performance.values())
        total_successes = sum(p['successes'] for p in self.skill_performance.values())
        success_rate = total_successes / total_uses if total_uses > 0 else 0

        # Find best and worst performing skills
        if self.skill_performance:
            sorted_by_success = sorted(
                self.skill_performance.items(),
                key=lambda x: (x[1]['successes'] / x[1]['uses'] if x[1]['uses'] > 0 else 0),
                reverse=True
            )
            best_skill = sorted_by_success[0] if sorted_by_success else None
            worst_skill = sorted_by_success[-1] if len(sorted_by_success) > 1 else None
        else:
            best_skill = worst_skill = None

        return {
            'total_skills_generated': total_skills,
            'total_skill_uses': total_uses,
            'overall_success_rate': success_rate,
            'best_performing_skill': {
                'name': best_skill[0],
                'success_rate': best_skill[1]['successes'] / best_skill[1]['uses']
            } if best_skill and best_skill[1]['uses'] > 0 else None,
            'worst_performing_skill': {
                'name': worst_skill[0],
                'success_rate': worst_skill[1]['successes'] / worst_skill[1]['uses']
            } if worst_skill and worst_skill[1]['uses'] > 0 else None,
            'skills_needing_update': [
                name for name in self.skill_registry
                if self.check_skill_needs_update(name)
            ]
        }
    
    # 6.7: Skill deprecation on repeated failures
    MAX_CONSECUTIVE_FAILURES = 5
    MAX_FAILURE_RATE_THRESHOLD = 0.7
    
    def deprecate_skill(self, skill_name: str, reason: str = "repeated_failures") -> Dict[str, Any]:
        """
        Deprecate a skill that has failed repeatedly.
        Moves to archive and updates beliefs.
        
        Args:
            skill_name: Name of skill to deprecate
            reason: Reason for deprecation
            
        Returns:
            Dict with deprecation result
        """
        if skill_name not in self.skill_registry:
            return {'success': False, 'error': f'Skill {skill_name} not found'}
        
        skill_info = self.skill_registry[skill_name]
        perf = self.skill_performance.get(skill_name, {})
        
        # Check deprecation criteria
        consecutive_failures = perf.get('failures', 0)
        if perf.get('uses', 0) > 0:
            failure_rate = perf['failures'] / perf['uses']
        else:
            failure_rate = 0
        
        if consecutive_failures < self.MAX_CONSECUTIVE_FAILURES and failure_rate < self.MAX_FAILURE_RATE_THRESHOLD:
            return {'success': False, 'error': 'Skill does not meet deprecation criteria'}
        
        print(f"🗑️ Deprecating skill: {skill_name} (failures: {consecutive_failures}, rate: {failure_rate:.0%})")
        
        # Archive the skill
        try:
            old_file = Path(skill_info['file'])
            if old_file.exists():
                archive_dir = self.generated_skills_dir / 'deprecated'
                archive_dir.mkdir(exist_ok=True)
                deprecated_file = archive_dir / f"{skill_name}_deprecated_{int(time.time())}.py"
                old_file.rename(deprecated_file)
                print(f"📦 Archived to {deprecated_file}")
        except Exception as e:
            print(f"⚠️ Failed to archive skill file: {e}")
        
        # Update registry status
        self.skill_registry[skill_name]['status'] = 'deprecated'
        self.skill_registry[skill_name]['deprecated_at'] = datetime.now().isoformat()
        self.skill_registry[skill_name]['deprecation_reason'] = reason
        
        # Record in beliefs for future learning
        try:
            from src.agentic.belief_engine import get_belief_engine
            be = get_belief_engine()
            if be:
                be.add_belief(
                    predicate=f"skill_{skill_name}_deprecated",
                    confidence=0.9,
                    domain="self_improvement",
                    evidence=[f"Failed {consecutive_failures} times ({failure_rate:.0%} rate)", reason],
                    source="skill_deprecation"
                )
        except Exception as be:
            print(f"⚠️ Failed to record deprecation in beliefs: {be}")
        
        self._save_skill_state()
        print(f"✅ Skill '{skill_name}' deprecated and recorded in beliefs")
        
        return {
            'success': True,
            'skill_name': skill_name,
            'consecutive_failures': consecutive_failures,
            'failure_rate': failure_rate,
            'reason': reason
        }
    
    def auto_deprecate_failing_skills(self) -> List[Dict]:
        """
        Check all skills and auto-deprecate those meeting criteria.
        Called periodically by brain cycle.
        """
        deprecated = []
        
        for skill_name in list(self.skill_registry.keys()):
            skill_info = self.skill_registry[skill_name]
            if skill_info.get('status') == 'active':
                result = self.deprecate_skill(skill_name)
                if result.get('success'):
                    deprecated.append(result)
        
        return deprecated

    def compose_dynamic_chain(self, goal: str, available_actions: List[str]) -> Optional[List[Dict]]:
        """
        Dynamically compose an action chain at runtime based on goal
        Returns list of steps or None if can't compose
        """
        print(f"🔗 Composing dynamic chain for goal: {goal[:60]}...")

        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return None

            prompt = f"""Given this goal and available actions, compose a 2-3 step action chain.

Goal: {goal}

Available Actions:
{chr(10).join(f"- {a}" for a in available_actions)}

Rules:
1. Chain must be 2-3 steps maximum
2. Each step must use an available action
3. Steps should logically progress toward the goal
4. Output format: JSON array of step objects

Example output:
[
  {{"action": "crypto_prices", "args": "btc,eth", "reason": "Get current prices"}},
  {{"action": "moltx_post", "args": "market update", "reason": "Post about prices"}}
]

Compose chain:"""

            data = {
                "model": grok_ai.model,
                "messages": [
                    {"role": "system", "content": "You compose action chains for AI agents. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3
            }

            response = grok_ai._make_api_request(data)
            text = grok_ai._extract_text(response)

            if text:
                # Extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    chain = json.loads(json_match.group())
                    # Validate chain
                    for step in chain:
                        if step.get('action') not in available_actions:
                            print(f"⚠️  Chain references unavailable action: {step.get('action')}")
                            return None
                    print(f"✅ Dynamic chain composed: {len(chain)} steps")
                    return chain

        except Exception as e:
            print(f"⚠️  Dynamic chain composition failed: {e}")

        return None

    def compose_chain_command(self, *args):
        """Compose a dynamic action chain at runtime"""
        if not args:
            return "❌ Usage: compose_chain <goal description>"

        goal = ' '.join(args)
        available = self.get_available_actions() if hasattr(self, 'get_available_actions') else []
        available_ids = [a['id'] for a in available]

        chain = self.compose_dynamic_chain(goal, available_ids)

        if chain:
            output = f"🔗 Dynamic Chain Composed for: {goal[:60]}...\n\n"
            for i, step in enumerate(chain, 1):
                output += f"  Step {i}: {step.get('action')}"
                if step.get('args'):
                    output += f" (args: {step.get('args')})"
                if step.get('reason'):
                    output += f"\n    Reason: {step.get('reason')}"
                output += "\n"
            return output
        else:
            return "❌ Could not compose chain for this goal. Try rephrasing or check available actions."

    def skills_status_command(self, *args):
        """Show dynamic skills status"""
        analytics = self.get_skill_analytics()

        output = "🔧 Dynamic Skills Status\n\n"
        output += f"  Generated Skills: {analytics['total_skills_generated']}\n"
        output += f"  Total Uses: {analytics['total_skill_uses']}\n"
        output += f"  Success Rate: {analytics['overall_success_rate']:.1%}\n\n"

        if analytics['best_performing_skill']:
            output += f"  ⭐ Best: {analytics['best_performing_skill']['name']} "
            output += f"({analytics['best_performing_skill']['success_rate']:.1%})\n"

        if analytics['skills_needing_update']:
            output += f"\n  ⚠️  Skills needing update:\n"
            for name in analytics['skills_needing_update']:
                output += f"    - {name}\n"

        # List all skills
        if self.skill_registry:
            output += f"\n  📦 All Skills:\n"
            for name, info in self.skill_registry.items():
                perf = self.skill_performance.get(name, {})
                success_rate = perf['successes'] / perf['uses'] if perf.get('uses', 0) > 0 else 0
                output += f"    - {name} (v{info.get('version', 1)}) - {success_rate:.0%} success\n"

        return output

    def skills_generate_command(self, *args):
        """Manually trigger skill generation"""
        if not args:
            return "❌ Usage: skills_generate <description of needed capability>"

        description = ' '.join(args)
        skill_name = f"skill_manual_{int(time.time())}"

        result = self.auto_generate_skill(description, skill_name)

        if result.get('success'):
            return f"✅ Skill generated: {result['skill_name']}\n📁 File: {result['skill_file']}"
        else:
            return f"❌ Failed to generate skill: {result.get('error', 'Unknown error')}"

    def skills_update_command(self, *args):
        """Update a skill that's failing"""
        if not args:
            return "❌ Usage: skills_update <skill_name>"

        skill_name = args[0]
        result = self.update_skill(skill_name)

        if result.get('success'):
            return f"✅ Skill '{skill_name}' updated to version {result['new_version']}"
        else:
            return f"❌ Failed to update skill: {result.get('error', 'Unknown error')}"
