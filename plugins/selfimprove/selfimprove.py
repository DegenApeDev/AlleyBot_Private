"""
Self-Improvement Plugin for AlleyBot
Autonomous coding, git branch workflow, test-before-merge, and skill marketplace.

Split into mixins:
- git_workflow.py: Git branching for safe self-edits
- test_gate.py: Test-before-merge validation
- skill_marketplace.py: Skill sharing and importing
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.selfimprove.git_workflow import GitWorkflowMixin
from plugins.selfimprove.test_gate import TestGateMixin
from plugins.selfimprove.skill_marketplace import SkillMarketplaceMixin


class SelfImprovePlugin(GitWorkflowMixin, TestGateMixin, SkillMarketplaceMixin, AlleyBotPlugin):
    """Self-improvement capabilities: autonomous coding, git workflow, test gates, skill marketplace"""

    def __init__(self, config):
        super().__init__(config)
        self.autonomous_coder = None

    def initialize(self, api, core):
        """Initialize self-improvement plugin"""
        super().initialize(api, core)

        # Initialize sub-systems
        self._init_git_workflow()
        self._init_test_gate()
        self._init_marketplace()

        # Wire autonomous coder if available
        try:
            from autonomous_coder import AutonomousCoder
            self.autonomous_coder = AutonomousCoder()
            print("✅ Autonomous coder loaded")
        except ImportError:
            print("⚠️  autonomous_coder.py not found, code generation limited to skill_generator")

        # Wire skill workflow if available
        try:
            from autonomous_skill_workflow import AutonomousSkillWorkflow
            self.skill_workflow = AutonomousSkillWorkflow(core)
            print("✅ Autonomous skill workflow loaded")
        except ImportError:
            self.skill_workflow = None
            print("⚠️  autonomous_skill_workflow.py not available")

        print("✅ Self-improvement plugin ready")

    def improve_command(self, *args):
        """Run a full self-improvement cycle: generate ideas, develop skill, test, branch, commit"""
        if not self.skill_workflow:
            return "❌ Skill workflow not available"

        output = "🧠 Starting Self-Improvement Cycle\n\n"

        # Step 1: Generate skill ideas
        try:
            ideas = self.skill_workflow.generate_skill_ideas()
            output += f"💡 Generated {len(ideas)} skill ideas\n"
            if not ideas:
                return output + "📭 No skill ideas generated. Try again later."
        except Exception as e:
            return output + f"❌ Idea generation failed: {e}"

        # Step 2: Show top idea
        top = ideas[0]
        output += f"🎯 Top idea: {top.get('topic', '?')} (score: {top.get('score', 0):.2f})\n"
        output += f"   Source: {top.get('source', '?')} | Platform: {top.get('platform', '?')}\n\n"

        # Step 3: Create improvement branch
        feature_name = top.get('topic', 'skill-improvement')
        branch_result = self.create_improvement_branch(feature_name)
        if branch_result['success']:
            output += f"🔀 Branch: {branch_result['branch']}\n"
        else:
            output += f"⚠️  Branch creation skipped: {branch_result['error']}\n"

        # Step 4: Develop the skill
        try:
            skill_result = self.skill_workflow.develop_top_skill(ideas)
            if skill_result:
                output += f"✅ Skill developed: {skill_result['code_result'].get('draft_id', '?')}\n"
            else:
                output += "❌ Skill development failed\n"
                return output
        except Exception as e:
            output += f"❌ Skill development error: {e}\n"
            return output

        # Step 5: Run test gate
        gate = self.merge_gate_check()
        output += f"\n{gate['summary']}\n"

        # Step 6: Commit if tests pass
        if gate['gate_passed']:
            commit_result = self.commit_changes(f"Add skill: {feature_name}")
            if commit_result['success']:
                output += f"✅ Committed on {commit_result['branch']}\n"
            else:
                output += f"⚠️  Commit skipped: {commit_result.get('error', '?')}\n"

            # Switch back to base
            self.switch_back_to_base()
            output += "🔀 Switched back to base branch\n"
            output += "📋 Branch ready for human review\n"
        else:
            output += "⚠️  Not committing - tests failed. Fix issues first.\n"

        return output

    def drafts_command(self, *args):
        """Show pending code drafts from autonomous coder"""
        if not self.autonomous_coder:
            return "❌ Autonomous coder not available"

        drafts = self.autonomous_coder.get_pending_drafts()
        if not drafts:
            return "📭 No pending drafts"

        output = f"📋 Pending Drafts ({len(drafts)})\n\n"
        for d in drafts[:10]:
            output += f"  📝 {d['draft_id']} - {d['task'][:50]}\n"
            output += f"     Status: {d['status']} | Files: {len(d.get('files', []))}\n"
            output += f"     Created: {d['timestamp'][:16]}\n\n"
        return output

    def approve_draft_command(self, *args):
        """Approve a code draft. Usage: improve_approve <draft_id>"""
        if not self.autonomous_coder:
            return "❌ Autonomous coder not available"
        if not args:
            return "❌ Usage: improve_approve <draft_id>"

        draft_id = args[0]

        # Test the draft first
        test_result = self.autonomous_coder.test_code(draft_id)
        if test_result.get('status') == 'test_error':
            return f"❌ Draft failed testing: {test_result.get('error', '?')}"

        if test_result.get('tests_failed', 0) > 0:
            return (
                f"❌ Draft has failing tests: "
                f"{test_result['tests_passed']}/{test_result['tests_run']} passed\n"
                f"Fix issues before approving."
            )

        # Approve
        result = self.autonomous_coder.approve_draft(draft_id, {
            'reviewer': 'AlleyBot-SelfImprove',
            'comments': 'Auto-approved after passing tests',
        })

        if result.get('status') == 'approved':
            return f"✅ Draft {draft_id} approved and ready for deployment"
        return f"❌ Approval failed: {result.get('error', '?')}"

    def deploy_draft_command(self, *args):
        """Deploy an approved draft. Usage: improve_deploy <draft_id>"""
        if not self.autonomous_coder:
            return "❌ Autonomous coder not available"
        if not args:
            return "❌ Usage: improve_deploy <draft_id>"

        draft_id = args[0]

        # Run merge gate first
        gate = self.merge_gate_check()
        if not gate['gate_passed']:
            return f"❌ Cannot deploy - test gate failed:\n{gate['summary']}"

        result = self.autonomous_coder.deploy_code(draft_id)
        if result.get('status') == 'deployed':
            files = result.get('files_deployed', [])
            return f"✅ Deployed {len(files)} files from draft {draft_id}"
        return f"❌ Deployment failed: {result.get('error', '?')}"

    def status_command(self, *args):
        """Show self-improvement system status"""
        output = "🧠 Self-Improvement Status\n\n"

        # Git workflow
        current = self._current_branch()
        output += f"  📍 Branch: {current}\n"
        auto_branches = [b for b in self.branch_history if b['status'] == 'active']
        output += f"  🔀 Active improvement branches: {len(auto_branches)}\n"

        # Autonomous coder
        if self.autonomous_coder:
            drafts = self.autonomous_coder.get_pending_drafts()
            output += f"  📝 Pending drafts: {len(drafts)}\n"
        else:
            output += "  📝 Autonomous coder: not loaded\n"

        # Skill workflow
        if self.skill_workflow:
            queue = self.skill_workflow.get_skill_queue_status()
            output += f"  🧩 Skill queue: {queue['queue_size']} pending\n"
        else:
            output += "  🧩 Skill workflow: not loaded\n"

        # Test gate
        recent_tests = self.test_results_history[-3:] if self.test_results_history else []
        if recent_tests:
            output += "\n  🧪 Recent Test Results:\n"
            for t in recent_tests:
                icon = "✅" if t.get('gate_passed') else "❌"
                tests = t.get('tests', {})
                output += f"    {icon} {tests.get('tests_run', '?')} tests | {t.get('branch', '?')}\n"
        else:
            output += "  🧪 No test results yet\n"

        # Marketplace
        output += f"\n  📦 Published skills: {len(self.published_skills)}\n"
        output += f"  📥 Imported skills: {len(self.imported_skills)}\n"

        return output

    def get_tasks(self):
        """Return scheduled tasks"""
        tasks = {}

        if self.config.get('auto_improve', False) and self.skill_workflow:
            tasks['self_improvement_cycle'] = {
                'function': lambda: self.improve_command(),
                'schedule': '0 */6 * * *',
                'description': 'Run autonomous self-improvement cycle every 6 hours'
            }

        return tasks

    def get_commands(self):
        """Return CLI commands"""
        return {
            # Core
            'improve': self.improve_command,
            'improve_status': self.status_command,
            # Git workflow
            'improve_branch': self.git_branch_command,
            'improve_commit': self.git_commit_command,
            'improve_done': self.git_done_command,
            'improve_git': self.git_status_command,
            # Test gate
            'improve_test': self.test_gate_command,
            'improve_gate': self.merge_gate_command,
            'improve_sandbox': self.sandbox_test_command,
            # Autonomous coder
            'improve_drafts': self.drafts_command,
            'improve_approve': self.approve_draft_command,
            'improve_deploy': self.deploy_draft_command,
            # Marketplace
            'improve_market': self.marketplace_list_command,
            'improve_publish': self.marketplace_publish_command,
            'improve_import': self.marketplace_import_command,
            'improve_market_status': self.marketplace_status_command,
        }

    def get_endpoints(self):
        """Return web endpoints"""
        return {}

    def cleanup(self):
        """Cleanup self-improvement plugin"""
        self._save_git_state()
        self._save_test_state()
        self._save_marketplace_state()
        print("🧠 Self-improvement plugin cleaned up")
