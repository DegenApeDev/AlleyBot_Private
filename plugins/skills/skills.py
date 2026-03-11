#!/usr/bin/env python3
"""
Agent Skills Plugin
Enhanced skill framework with OpenClaw/ElizaOS compatibility

Features:
- SkillDiscoveryMixin: Scan and index SKILL.md files
- SkillLoaderMixin: Progressive disclosure, activate on demand  
- SkillExecutorMixin: Execute instructions and bundled scripts
- SkillAutonomousExecutorMixin: OpenClaw-style heartbeat & triggers
- SkillFormatAdapterMixin: Import/export OpenClaw/ElizaOS skills
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.skills.skill_discovery import SkillDiscoveryMixin
from plugins.skills.skill_loader import SkillLoaderMixin
from plugins.skills.skill_executor import SkillExecutorMixin
from plugins.skills.skill_validation import SkillValidationMixin
from plugins.skills.skill_templates import SkillTemplatesMixin
from plugins.skills.skill_generator import SkillGeneratorMixin
from plugins.skills.skill_oasf_bridge import OASFSkillBridgeMixin
from plugins.skills.skill_performance import SkillPerformanceMixin
from plugins.skills.skill_marketplace import SkillMarketplaceMixin
from plugins.skills.skill_autonomous import SkillAutonomousExecutorMixin
from plugins.skills.skill_format_adapter import SkillFormatAdapterMixin
from plugins.skills.skill_swarm import SwarmManagerMixin


class SkillsPlugin(
    SwarmManagerMixin,              # NEW: Multi-agent swarm control
    SkillAutonomousExecutorMixin,  # Autonomous execution & tools
    SkillFormatAdapterMixin,     # OpenClaw/ElizaOS compatibility
    SkillDiscoveryMixin,
    SkillLoaderMixin,
    SkillExecutorMixin,
    SkillValidationMixin,
    SkillTemplatesMixin,
    SkillGeneratorMixin,
    OASFSkillBridgeMixin,
    SkillPerformanceMixin,
    SkillMarketplaceMixin,
    AlleyBotPlugin
):
    """Agent Skills framework for AlleyBot - With Swarm Control!"""

    def __init__(self, config):
        # Set project_root BEFORE super().__init__() so mixins can access it
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        super().__init__(config)
        self.skills_dir = config.get('skills_dir', 'skills')

    def initialize(self, api, core):
        super().initialize(api, core)
        self.initialize_swarm()
        print(f"✅ Agent Skills plugin initialized ({len(self.skill_index)} skills)")
        print(f"   🔧 Tools available: {len(self.tool_registry)}")
        print(f"   🤖 Autonomous mode: Ready (use /autonomous_start)")
        print(f"   🔄 OpenClaw/ElizaOS: Import ready")
        print(f"   🐝 Swarm control: {len(self.swarm_nodes)} nodes active")

    def get_tasks(self):
        """Return scheduled tasks"""
        return {}

    def get_commands(self):
        """Return CLI commands for skill management"""
        return {
            # Core skill management
            'skills_list': self.list_skills_command,
            'skills_info': self.skill_info_command,
            'skills_history': self.skill_history_command,
            'skills_log': self.execution_log_command,
            'skills_validate': self.validate_all_skills_command,
            'skills_templates': self.list_templates_command,
            'skills_generate_all': self.generate_all_platform_skills_command,
            'skills_oasf_bridge': self.oasf_bridge_command,
            'skills_suggest': self.suggest_skills_command,
            'skills_stats': self.skills_stats_command,
            'skills_recommend': self.skills_recommend_command,
            # Skill execution
            'skill_exec': self.skill_exec_command,
            'skill_chain': self.skill_chain_command,
            'skill_find': self.find_skill_command,
            'skill_activate': self.activate_skill_command,
            'skill_lint': self.lint_skill_command,
            'skill_create': self.create_skill_from_template_command,
            'skill_generate': self.generate_skill_command,
            'skill_autocode': self.skill_autocode_command,
            # Marketplace
            'skill_publish': self.marketplace_publish_command,
            'skill_import': self.marketplace_import_command,
            'skill_market_list': self.marketplace_list_command,
            # NEW: Autonomous execution
            'autonomous_start': self.autonomous_start_command,
            'autonomous_stop': self.autonomous_stop_command,
            'autonomous_status': self.autonomous_status_command,
            # NEW: Tool registry
            'tool_list': self.tool_list_command,
            'tool_exec': self.tool_exec_command,
            # NEW: Format adapters
            'skill_import_openclaw': self.skill_import_openclaw_command,
            'skill_import_elizaos': self.skill_import_elizaos_command,
            'skill_export_openclaw': self.skill_export_openclaw_command,
            # NEW: Swarm control
            'swarm_spawn': self.swarm_spawn_command,
            'swarm_kill': self.swarm_kill_command,
            'swarm_list': self.swarm_list_command,
            'swarm_delegate': self.swarm_delegate_command,
            'swarm_result': self.swarm_result_command,
            'swarm_status': self.swarm_status_command,
            'swarm_parallel': self.swarm_parallel_command,
        }

    def get_endpoints(self):
        """Return web endpoints"""
        return {}

    # --- Additional Commands ---

    def find_skill_command(self, *args):
        """Find best skill for a task. Usage: skill_find <task_description>"""
        if not args:
            return "❌ Usage: skill_find <task_description>"

        task = ' '.join(args)
        best_skill = self.find_skill_for_task(task)

        if best_skill:
            info = self.skill_index.get(best_skill, {})
            return (
                f"🔧 Best match: {best_skill}\n"
                f"📝 {info.get('description', '')}\n"
                f"💡 Use: skill_activate {best_skill}"
            )
        else:
            available = ', '.join(sorted(self.skill_index.keys()))
            return f"📭 No matching skill found. Available: {available}"

    def activate_skill_command(self, *args):
        """Activate a skill for immediate use. Usage: skill_activate <name>"""
        if not args:
            return "❌ Usage: skill_activate <skill_name>"

        skill_name = args[0]
        prompt = self.activate_skill(skill_name)

        if prompt:
            return (
                f"✅ Skill activated: {skill_name}\n"
                f"📝 Loaded into context\n"
                f"💡 The skill instructions are now available for AI use"
            )
        else:
            return f"❌ Failed to activate skill: {skill_name}"


# Plugin is automatically registered through the plugin manager system
