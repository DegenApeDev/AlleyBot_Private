#!/usr/bin/env python3
"""
Agent Skills Plugin
Lightweight skill framework following agentskills.io specification

Composes:
- SkillDiscoveryMixin: Scan and index SKILL.md files
- SkillLoaderMixin: Progressive disclosure, activate on demand  
- SkillExecutorMixin: Execute instructions and bundled scripts

Skills are stored in skills/<name>/SKILL.md with optional:
- scripts/ - Executable code
- references/ - Documentation
- assets/ - Templates, resources
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


class SkillsPlugin(SkillDiscoveryMixin, SkillLoaderMixin, SkillExecutorMixin, 
                   SkillValidationMixin, SkillTemplatesMixin, SkillGeneratorMixin, 
                   OASFSkillBridgeMixin, SkillPerformanceMixin, SkillMarketplaceMixin, 
                   AlleyBotPlugin):
    """Agent Skills framework for AlleyBot"""

    def __init__(self, config):
        # Set project_root BEFORE super().__init__() so mixins can access it
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        super().__init__(config)
        self.skills_dir = config.get('skills_dir', 'skills')

    def initialize(self, api, core):
        super().initialize(api, core)
        print(f"✅ Agent Skills plugin initialized ({len(self.skill_index)} skills)")

    def get_tasks(self):
        """Return scheduled tasks"""
        return {}

    def get_commands(self):
        """Return CLI commands for skill management"""
        return {
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
            'skill_exec': self.skill_exec_command,
            'skill_find': self.find_skill_command,
            'skill_activate': self.activate_skill_command,
            'skill_lint': self.lint_skill_command,
            'skill_create': self.create_skill_from_template_command,
            'skill_generate': self.generate_skill_command,
            # Marketplace
            'skill_publish': self.marketplace_publish_command,
            'skill_import': self.marketplace_import_command,
            'skill_market_list': self.marketplace_list_command,
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
