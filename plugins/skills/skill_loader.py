"""
Skill Loader and Activation
Progressive disclosure: load full skill only when needed
"""
import re
from datetime import datetime
from typing import Dict, List, Optional, Any


class SkillLoaderMixin:
    """Load and activate skills on demand"""

    def __init__(self, config):
        super().__init__(config)
        self.active_skill: Optional[str] = None
        self.skill_context: Optional[str] = None
        self.skill_history: List[Dict] = []

    def find_skill_for_task(self, task_description: str) -> Optional[str]:
        """Find the most relevant skill for a given task"""
        if not self.skill_index:
            return None

        task_lower = task_description.lower()
        best_match = None
        best_score = 0

        for name, info in self.skill_index.items():
            desc = info.get('description', '').lower()
            score = 0

            # Check for keyword matches
            task_words = set(task_lower.split())
            desc_words = set(desc.split())
            overlap = task_words & desc_words
            score += len(overlap)

            # Bonus for exact phrase matches
            if name.replace('-', ' ') in task_lower:
                score += 5

            # Check category from metadata
            meta = info.get('metadata', {})
            category = meta.get('category', '').lower()
            if category in task_lower:
                score += 3

            if score > best_score:
                best_score = score
                best_match = name

        # Only return if we have a decent match
        if best_score >= 2:
            return best_match
        return None

    def activate_skill(self, skill_name: str) -> Optional[str]:
        """Load full skill and prepare for execution"""
        skill = self._load_full_skill(skill_name)
        if not skill:
            return None

        self.active_skill = skill_name
        self.skill_context = skill['body']

        # Record activation
        self.skill_history.append({
            'skill': skill_name,
            'activated_at': datetime.now().isoformat(),
            'description': skill['description']
        })

        print(f"🔧 Skill activated: {skill_name}")
        return self.skill_context

    def deactivate_skill(self):
        """Clear active skill"""
        if self.active_skill:
            print(f"🔧 Skill deactivated: {self.active_skill}")
        self.active_skill = None
        self.skill_context = None

    def get_skill_prompt(self, skill_name: str) -> Optional[str]:
        """Get the skill body formatted for AI prompt injection"""
        skill = self._load_full_skill(skill_name)
        if not skill:
            return None

        # Format skill context for AI
        fm = skill.get('frontmatter', {})
        prompt = f"""# Skill: {skill['name']}

{skill['description']}

## Instructions
{skill['body']}
"""

        # Add references if available
        if skill.get('references'):
            prompt += "\n## References\n"
            for ref_path in skill['references'][:3]:  # Limit to 3
                try:
                    with open(ref_path, 'r') as f:
                        ref_content = f.read()[:500]  # Limit content
                    prompt += f"\n### {ref_path.split('/')[-1]}\n{ref_content}\n"
                except:
                    pass

        return prompt

    def skill_history_command(self, *args):
        """Show recent skill activations. Usage: skills_history"""
        if not self.skill_history:
            return "📭 No skills activated yet"

        output = "📚 Skill Activation History:\n\n"
        for entry in reversed(self.skill_history[-10:]):
            skill = entry['skill']
            when = entry['activated_at'][:16]  # Trim to datetime
            output += f"  {when} - {skill}\n"
        return output
