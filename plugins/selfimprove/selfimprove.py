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
from plugins.selfimprove.skill_builder import SkillBuilderMixin
from plugins.selfimprove.skill_updater import SkillUpdaterMixin


class SelfImprovePlugin(GitWorkflowMixin, TestGateMixin, SkillMarketplaceMixin, SkillBuilderMixin, SkillUpdaterMixin, AlleyBotPlugin):
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

        # Initialize skill builder (SKILL.md discovery + AI generation)
        self._init_skill_builder()
        print(f"🧩 Skill builder ready ({len(self.loaded_skills)} skills discovered)")

        # Initialize skill updater (auto-download platform skill files)
        self._init_skill_updater()

        print("✅ Self-improvement plugin ready")

    def improve_command(self, *args):
        """Run a self-improvement cycle: identify gaps, generate a new skill"""
        return self.build_skill_command(*args)

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

        # Skill builder
        output += f"  🧩 Skills discovered: {len(self.loaded_skills)}\n"
        if self.loaded_skills:
            for name in list(self.loaded_skills.keys())[:5]:
                output += f"      📄 {name}\n"

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

        # Skill updater
        if hasattr(self, 'skill_versions') and self.skill_versions:
            output += f"\n  🔄 Tracked platform skills: {len(self.skill_versions)}\n"
            for plat, ver in sorted(self.skill_versions.items()):
                output += f"      {plat}: v{ver}\n"

        return output

    def get_tasks(self):
        """Return scheduled tasks"""
        tasks = {}

        if self.config.get('auto_improve', False):
            tasks['self_improvement_cycle'] = {
                'function': lambda: self.improve_command(),
                'schedule': '0 */6 * * *',
                'description': 'Run autonomous self-improvement cycle every 6 hours'
            }

        # Always check for skill updates every 12 hours
        tasks['skill_update_check'] = {
            'function': lambda: self.update_skills_command(),
            'schedule': '0 */12 * * *',
            'description': 'Check all platforms for skill file updates'
        }

        return tasks

    def get_commands(self):
        """Return CLI commands"""
        return {
            # Core
            'improve': self.improve_command,
            'improve_status': self.status_command,
            'improve_skills': self.list_skills_command,
            'improve_build': self.build_skill_command,
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
            # Skill updater
            'improve_update_skills': self.update_skills_command,
            'improve_update_skill': self.update_single_skill_command,
            'improve_skill_versions': self.skill_versions_command,
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
