"""
Skill Performance Tracking
Track which skills are used most and optimize descriptions
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class SkillPerformanceMixin:
    """Track skill usage and performance metrics"""

    def __init__(self, config):
        super().__init__(config)
        self.performance_file = os.path.join(
            self.project_root, 'skills', 'performance.json'
        )
        self.usage_stats: Dict[str, Dict] = {}
        self._load_performance_data()

    def _load_performance_data(self):
        """Load historical performance data"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    self.usage_stats = json.load(f)
            except Exception:
                self.usage_stats = {}

    def _save_performance_data(self):
        """Save performance data to disk"""
        try:
            os.makedirs(os.path.dirname(self.performance_file), exist_ok=True)
            with open(self.performance_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save performance data: {e}")

    def record_skill_activation(self, skill_name: str):
        """Record when a skill is activated"""
        if skill_name not in self.usage_stats:
            self.usage_stats[skill_name] = {
                'activations': 0,
                'executions': 0,
                'first_used': datetime.now().isoformat(),
                'last_used': None,
                'daily_uses': {},
                'success_count': 0,
                'fail_count': 0,
            }
        
        stats = self.usage_stats[skill_name]
        stats['activations'] += 1
        stats['last_used'] = datetime.now().isoformat()
        
        # Track daily usage
        today = datetime.now().strftime('%Y-%m-%d')
        stats['daily_uses'][today] = stats['daily_uses'].get(today, 0) + 1
        
        self._save_performance_data()

    def record_skill_execution(self, skill_name: str, success: bool):
        """Record skill execution result"""
        if skill_name in self.usage_stats:
            self.usage_stats[skill_name]['executions'] += 1
            if success:
                self.usage_stats[skill_name]['success_count'] += 1
            else:
                self.usage_stats[skill_name]['fail_count'] += 1
            self._save_performance_data()

    def get_top_skills(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get most frequently used skills"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        scored_skills = []
        for name, stats in self.usage_stats.items():
            # Calculate score based on recent usage
            recent_uses = sum(
                count for date, count in stats.get('daily_uses', {}).items()
                if date >= cutoff
            )
            
            total_execs = stats.get('executions', 0)
            success_rate = (
                stats['success_count'] / total_execs * 100
                if total_execs > 0 else 0
            )
            
            scored_skills.append({
                'name': name,
                'recent_uses': recent_uses,
                'total_activations': stats.get('activations', 0),
                'success_rate': success_rate,
                'score': recent_uses * (success_rate / 100 + 0.5),
            })
        
        # Sort by score
        scored_skills.sort(key=lambda x: x['score'], reverse=True)
        return scored_skills[:limit]

    def get_unused_skills(self, days: int = 30) -> List[str]:
        """Get skills that haven't been used recently"""
        cutoff = (datetime.now() - timedelta(days=days))
        unused = []
        
        for name, info in self.skill_index.items():
            if name not in self.usage_stats:
                unused.append(name)
            else:
                last_used_str = self.usage_stats[name].get('last_used')
                if last_used_str:
                    last_used = datetime.fromisoformat(last_used_str)
                    if last_used < cutoff:
                        unused.append(name)
        
        return unused

    def skills_stats_command(self, *args):
        """Show skill usage statistics. Usage: skills_stats [days]"""
        days = int(args[0]) if args else 7
        
        top_skills = self.get_top_skills(days=days)
        unused = self.get_unused_skills(days=days)
        
        output = f"📊 Skill Performance (last {days} days)\n\n"
        
        # Top used skills
        output += "🔥 Most Used Skills:\n"
        for i, skill in enumerate(top_skills[:5], 1):
            name = skill['name']
            uses = skill['recent_uses']
            rate = skill['success_rate']
            output += f"  {i}. {name}: {uses} uses, {rate:.0f}% success\n"
        
        # Unused skills
        if unused:
            output += f"\n📭 Unused Skills ({len(unused)}):\n"
            for name in unused[:5]:
                output += f"  - {name}\n"
        
        # Totals
        total_activations = sum(s.get('activations', 0) for s in self.usage_stats.values())
        output += f"\n📈 Total: {len(self.skill_index)} skills, {total_activations} activations"
        
        return output

    def skills_recommend_command(self, *args):
        """Get recommendations for skill improvements. Usage: skills_recommend"""
        unused = self.get_unused_skills(days=14)
        
        output = "💡 Skill Recommendations:\n\n"
        
        if unused:
            output += "Skills not used in 14 days (consider improving descriptions):\n"
            for name in unused:
                info = self.skill_index.get(name, {})
                desc = info.get('description', '')
                output += f"  - {name}: {desc[:50]}...\n"
        else:
            output += "✅ All skills have been used recently!\n"
        
        # Suggest missing skills based on OASF
        try:
            from plugins.analytics.agent_card import PLUGIN_SKILL_MAP
            
            loaded_plugins = self.core.plugin_manager.plugins.keys() if self.core else []
            all_oasf = []
            for plugin_name, skill_info in PLUGIN_SKILL_MAP.items():
                if plugin_name in loaded_plugins:
                    all_oasf.extend(skill_info.get('skills', []))
            
            suggested = self.suggest_skills_from_capabilities(all_oasf)
            missing = [s for s in suggested if s not in self.skill_index]
            
            if missing:
                output += f"\n💭 Suggested skills to create:\n"
                for name in missing[:5]:
                    output += f"  - {name}\n"
        except Exception:
            pass
        
        return output
