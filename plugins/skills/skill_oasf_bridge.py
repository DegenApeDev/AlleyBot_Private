"""
OASF to Agent Skills Bridge
Maps OASF skill categories to Agent Skills discovery
"""
from typing import Dict, List, Optional


class OASFSkillBridgeMixin:
    """Bridge between OASF skill categories and Agent Skills framework"""

    # OASF category to skill name mapping
    OASF_TO_SKILL_MAP = {
        # Content creation
        'content_creation': ['content-generation', 'social-engagement'],
        'natural_language_processing/natural_language_generation': ['content-generation'],
        'natural_language_processing/creative_content': ['content-generation'],
        'natural_language_processing/sentiment_analysis': ['content-analysis'],
        
        # Blockchain
        'blockchain': ['blockchain-analysis', 'blockchain-query'],
        'analytical_skills/data_analysis/blockchain_analysis': ['blockchain-analysis'],
        
        # Analytics
        'analytics': ['data-analysis', 'trend-analysis'],
        'analytical_skills/data_analysis': ['data-analysis'],
        'evaluation_monitoring/performance_monitoring': ['analytics-monitoring'],
        
        # Software engineering
        'software_engineering': ['code-generation', 'code-review'],
        'analytical_skills/coding_skills/text_to_code': ['code-generation'],
        'analytical_skills/coding_skills/code_optimization': ['code-optimization'],
        
        # Agent orchestration
        'agent_orchestration': ['multi-agent-coordination', 'task-delegation'],
        'agent_orchestration/agent_coordination': ['multi-agent-coordination'],
        'agent_orchestration/task_decomposition': ['task-planning'],
        
        # Reasoning
        'reasoning': ['strategic-planning', 'decision-making'],
        'advanced_reasoning_planning/strategic_planning': ['strategic-planning'],
        'advanced_reasoning_planning/long_horizon_reasoning': ['long-term-planning'],
        
        # Communication
        'communication': ['messaging', 'notifications'],
        'interaction/user_engagement': ['user-engagement'],
        
        # Information gathering
        'information_gathering': ['web-search', 'research'],
        'natural_language_processing/information_retrieval_synthesis/search': ['web-search'],
    }

    def __init__(self, config):
        super().__init__(config)

    def get_skills_for_oasf_category(self, oasf_category: str) -> List[str]:
        """Get Agent Skills that map to an OASF category"""
        # Direct match
        if oasf_category in self.OASF_TO_SKILL_MAP:
            return self.OASF_TO_SKILL_MAP[oasf_category]
        
        # Partial match (check if category starts with any key)
        for key, skills in self.OASF_TO_SKILL_MAP.items():
            if oasf_category.startswith(key) or key.startswith(oasf_category):
                return skills
        
        return []

    def find_skills_by_oasf_category(self, category: str) -> List[Dict]:
        """Find discovered skills that match an OASF category"""
        skill_names = self.get_skills_for_oasf_category(category)
        
        found_skills = []
        for name in skill_names:
            if name in self.skill_index:
                found_skills.append(self.skill_index[name])
        
        return found_skills

    def suggest_skills_from_capabilities(self, capabilities: List[str]) -> List[str]:
        """Suggest skills based on OASF capability list"""
        suggested = []
        
        for cap in capabilities:
            skills = self.get_skills_for_oasf_category(cap)
            for skill in skills:
                if skill in self.skill_index and skill not in suggested:
                    suggested.append(skill)
        
        return suggested

    def oasf_bridge_command(self, *args):
        """Show OASF to Skills bridge mapping. Usage: skills_oasf_bridge [category]"""
        if not args:
            output = "🔗 OASF to Agent Skills Bridge\n\n"
            output += "Available mappings:\n\n"
            
            for oasf_cat, skills in sorted(self.OASF_TO_SKILL_MAP.items())[:15]:
                skill_list = ', '.join(skills)
                status = "✅" if any(s in self.skill_index for s in skills) else "⏳"
                output += f"  {status} {oasf_cat} → {skill_list}\n"
            
            output += f"\n💡 Use: skills_oasf_bridge <category> for details"
            return output
        
        category = args[0]
        skills = self.get_skills_for_oasf_category(category)
        
        if not skills:
            return f"📭 No skill mapping found for: {category}"
        
        output = f"🔗 {category}\n\n"
        output += "Mapped skills:\n"
        
        for skill_name in skills:
            if skill_name in self.skill_index:
                info = self.skill_index[skill_name]
                output += f"  ✅ {skill_name}: {info.get('description', '')[:60]}\n"
            else:
                output += f"  ⏳ {skill_name}: Not yet created\n"
        
        return output

    def suggest_skills_command(self, *args):
        """Suggest skills based on current capabilities. Usage: skills_suggest"""
        # Get capabilities from agent card if available
        try:
            from plugins.analytics.agent_card import PLUGIN_SKILL_MAP
            
            # Collect all OASF skills from loaded plugins
            loaded_plugins = self.core.plugin_manager.plugins.keys() if self.core else []
            all_oasf_skills = []
            
            for plugin_name, skill_info in PLUGIN_SKILL_MAP.items():
                if plugin_name in loaded_plugins:
                    all_oasf_skills.extend(skill_info.get('skills', []))
            
            suggested = self.suggest_skills_from_capabilities(all_oasf_skills)
            
            if not suggested:
                return "📭 No skill suggestions based on current capabilities"
            
            output = "💡 Suggested Skills for Current Capabilities:\n\n"
            for skill_name in suggested[:10]:
                info = self.skill_index.get(skill_name, {})
                desc = info.get('description', '')[:50]
                output += f"  📄 {skill_name}\n"
                if desc:
                    output += f"     {desc}...\n"
            
            output += f"\n🔧 Total suggestions: {len(suggested)}"
            return output
            
        except Exception as e:
            return f"⚠️ Could not generate suggestions: {e}"
