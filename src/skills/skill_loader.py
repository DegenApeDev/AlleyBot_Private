"""
Dynamic Skill Loader for AlleyBot
Loads and manages skills from YAML definitions
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class Skill:
    """Skill definition"""
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get('name', '')
        self.description = config.get('description', '')
        self.category = config.get('category', 'general')
        self.enabled = config.get('enabled', True)
        self.parameters = config.get('parameters', [])
        self.execution = config.get('execution', {})
        self.model_requirements = config.get('model_requirements', {})
        self.success_criteria = config.get('success_criteria', [])
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate provided parameters against requirements"""
        for param_def in self.parameters:
            param_name = param_def.get('name')
            required = param_def.get('required', False)
            
            if required and param_name not in params:
                print(f"❌ Missing required parameter: {param_name}")
                return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameter values"""
        defaults = {}
        for param_def in self.parameters:
            param_name = param_def.get('name')
            if 'default' in param_def:
                defaults[param_name] = param_def['default']
        return defaults


class SkillLoader:
    """Loads and manages skills from YAML files"""
    
    def __init__(self, skills_dir: str = "src/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self.load_all_skills()
    
    def load_all_skills(self):
        """Load all skill definitions from YAML files"""
        try:
            if not self.skills_dir.exists():
                print(f"⚠️ Skills directory not found: {self.skills_dir}")
                return
            
            skill_files = list(self.skills_dir.glob("*.yaml")) + list(self.skills_dir.glob("*.yml"))
            
            for skill_file in skill_files:
                try:
                    with open(skill_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    skill = Skill(config)
                    
                    if skill.enabled:
                        self.skills[skill.name] = skill
                        print(f"✅ Loaded skill: {skill.name} ({skill.category})")
                    else:
                        print(f"⏸️  Skill disabled: {skill.name}")
                        
                except Exception as e:
                    print(f"❌ Failed to load skill {skill_file}: {e}")
            
            print(f"📦 Loaded {len(self.skills)} skills")
            
        except Exception as e:
            print(f"❌ Failed to load skills: {e}")
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self.skills.get(name)
    
    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """List all skills, optionally filtered by category"""
        if category:
            return [s for s in self.skills.values() if s.category == category]
        return list(self.skills.values())
    
    def get_categories(self) -> List[str]:
        """Get all skill categories"""
        return list(set(s.category for s in self.skills.values()))
    
    async def execute_skill(self, skill_name: str, params: Dict[str, Any], core) -> str:
        """Execute a skill with given parameters"""
        try:
            skill = self.get_skill(skill_name)
            if not skill:
                return f"❌ Skill not found: {skill_name}"
            
            # Merge with defaults
            full_params = skill.get_default_parameters()
            full_params.update(params)
            
            # Validate parameters
            if not skill.validate_parameters(full_params):
                return f"❌ Invalid parameters for skill: {skill_name}"
            
            # Execute via plugin
            plugin_name = skill.execution.get('plugin')
            command = skill.execution.get('command')
            
            if not plugin_name or not command:
                return f"❌ Invalid skill execution config: {skill_name}"
            
            # Use core to execute command
            if hasattr(core, 'run_command'):
                # Build command arguments
                args = []
                for param_def in skill.parameters:
                    param_name = param_def.get('name')
                    if param_name in full_params:
                        args.append(str(full_params[param_name]))
                
                result = core.run_command(f"{plugin_name}_{command}", *args)
                print(f"✅ Executed skill: {skill_name}")
                return result
            else:
                return f"❌ Core does not support command execution"
                
        except Exception as e:
            print(f"❌ Skill execution error: {e}")
            return f"❌ Failed to execute skill {skill_name}: {e}"
    
    def reload_skills(self):
        """Reload all skills from disk"""
        self.skills.clear()
        self.load_all_skills()
        print("🔄 Skills reloaded")
