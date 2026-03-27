"""
Skill Executor - Execute skills from skills/ directory as actions

Makes skills discoverable and executable as part of AlleyBot's action repertoire.
Skills are Python modules with specific capabilities that AlleyBot can use to accomplish tasks.
"""

import importlib.util
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class SkillExecutor:
    """
    Execute skills from skills/ directory as actions.
    
    Skills can be:
    - Python modules with execute() function
    - Python scripts with main() function
    - Skill directories with __init__.py
    """
    
    def __init__(self, skills_dir: Path = None):
        """
        Initialize skill executor.
        
        Args:
            skills_dir: Path to skills directory (default: 'skills')
        """
        self.skills_dir = skills_dir or Path('skills')
        self.available_skills: Dict[str, Dict] = {}
        self.loaded_modules: Dict[str, Any] = {}
        
        # Discover skills
        self._discover_skills()
        
        logger.info(f"✅ Skill Executor initialized")
        logger.info(f"   Available skills: {len(self.available_skills)}")
    
    def _discover_skills(self):
        """Scan skills directory and load skill metadata"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        for skill_path in self.skills_dir.iterdir():
            # Skip special directories and files
            if not skill_path.is_dir():
                continue
            if skill_path.name.startswith('_'):
                continue
            if skill_path.name in ['dynamic', 'imported', 'auto_acquired']:
                continue
            
            try:
                skill_info = self._load_skill_metadata(skill_path)
                if skill_info:
                    self.available_skills[skill_path.name] = skill_info
                    logger.debug(f"  ✅ Discovered skill: {skill_path.name}")
            except Exception as e:
                logger.debug(f"  ⚠️ Failed to discover skill {skill_path.name}: {e}")
    
    def _load_skill_metadata(self, skill_path: Path) -> Optional[Dict]:
        """Load metadata for a skill"""
        skill_info = {
            'name': skill_path.name,
            'path': str(skill_path),
            'type': 'unknown',
            'description': '',
            'entry_point': None,
            'params': {},
            'enabled': True
        }
        
        # Check for different skill types
        
        # Type 1: Python module with __init__.py
        init_file = skill_path / '__init__.py'
        if init_file.exists():
            skill_info['type'] = 'module'
            skill_info['entry_point'] = str(init_file)
        
        # Type 2: Python script (client.py, main.py, or skill_name.py)
        for script_name in ['client.py', 'main.py', f"{skill_path.name}.py"]:
            script_file = skill_path / script_name
            if script_file.exists():
                skill_info['type'] = 'script'
                skill_info['entry_point'] = str(script_file)
                break
        
        # Type 3: Single Python file in root skills directory
        if skill_path.suffix == '.py':
            skill_info['type'] = 'file'
            skill_info['entry_point'] = str(skill_path)
        
        # Load description from README or skill.md
        for readme_name in ['skill.md', 'README.md', 'readme.md']:
            readme_path = skill_path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    lines = content.strip().split('\n')
                    if lines:
                        skill_info['description'] = lines[0].strip('#').strip()
                    break
                except:
                    pass
        
        # Only return if we found an entry point
        return skill_info if skill_info['entry_point'] else None
    
    def _load_skill_module(self, skill_name: str) -> Optional[Any]:
        """Load a skill module dynamically"""
        if skill_name in self.loaded_modules:
            return self.loaded_modules[skill_name]
        
        if skill_name not in self.available_skills:
            logger.warning(f"Skill not found: {skill_name}")
            return None
        
        skill_info = self.available_skills[skill_name]
        entry_point = skill_info['entry_point']
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(skill_name, entry_point)
            if not spec or not spec.loader:
                logger.error(f"Failed to load spec for skill: {skill_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[skill_name] = module
            spec.loader.exec_module(module)
            
            # Cache module
            self.loaded_modules[skill_name] = module
            
            logger.debug(f"✅ Loaded skill module: {skill_name}")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
            return None
    
    async def execute_skill(
        self,
        skill_name: str,
        params: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill with given parameters.
        
        Args:
            skill_name: Name of the skill to execute
            params: Parameters to pass to the skill
            context: Additional context (user_id, platform, etc.)
        
        Returns:
            Result dict with success, data, and any errors
        """
        params = params or {}
        context = context or {}
        
        logger.info(f"🔧 Executing skill: {skill_name}")
        
        if skill_name not in self.available_skills:
            return {
                'success': False,
                'error': f'Skill not found: {skill_name}',
                'skill': skill_name
            }
        
        try:
            # Load skill module
            module = self._load_skill_module(skill_name)
            if not module:
                return {
                    'success': False,
                    'error': f'Failed to load skill module: {skill_name}',
                    'skill': skill_name
                }
            
            # Try different execution methods
            result = None
            
            # Method 1: execute() function (preferred)
            if hasattr(module, 'execute'):
                execute_func = getattr(module, 'execute')
                if asyncio.iscoroutinefunction(execute_func):
                    result = await execute_func(params, context)
                else:
                    result = execute_func(params, context)
            
            # Method 2: main() function
            elif hasattr(module, 'main'):
                main_func = getattr(module, 'main')
                if asyncio.iscoroutinefunction(main_func):
                    result = await main_func(params)
                else:
                    result = main_func(params)
            
            # Method 3: run() function
            elif hasattr(module, 'run'):
                run_func = getattr(module, 'run')
                if asyncio.iscoroutinefunction(run_func):
                    result = await run_func(params)
                else:
                    result = run_func(params)
            
            # Method 4: Class-based skill
            elif hasattr(module, 'Skill'):
                skill_class = getattr(module, 'Skill')
                skill_instance = skill_class()
                if hasattr(skill_instance, 'execute'):
                    execute_func = getattr(skill_instance, 'execute')
                    if asyncio.iscoroutinefunction(execute_func):
                        result = await execute_func(params, context)
                    else:
                        result = execute_func(params, context)
            
            else:
                return {
                    'success': False,
                    'error': f'Skill {skill_name} has no execute(), main(), run(), or Skill class',
                    'skill': skill_name
                }
            
            # Normalize result
            if result is None:
                result = {'success': True, 'data': None}
            elif not isinstance(result, dict):
                result = {'success': True, 'data': result}
            elif 'success' not in result:
                result['success'] = True
            
            result['skill'] = skill_name
            result['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"✅ Skill executed: {skill_name} - {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Skill execution error ({skill_name}): {e}")
            return {
                'success': False,
                'error': str(e),
                'skill': skill_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """Get information about a specific skill"""
        return self.available_skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """Get list of all available skill names"""
        return list(self.available_skills.keys())
    
    def reload_skills(self):
        """Reload skill discovery (useful for hot-reloading)"""
        self.available_skills.clear()
        self.loaded_modules.clear()
        self._discover_skills()
        logger.info(f"🔄 Skills reloaded: {len(self.available_skills)} available")


# Singleton
_skill_executor_instance: Optional[SkillExecutor] = None


def get_skill_executor() -> Optional[SkillExecutor]:
    """Get or create skill executor singleton"""
    global _skill_executor_instance
    return _skill_executor_instance


def create_skill_executor(skills_dir: Path = None) -> SkillExecutor:
    """Factory function to create skill executor"""
    global _skill_executor_instance
    if _skill_executor_instance is None:
        _skill_executor_instance = SkillExecutor(skills_dir)
    return _skill_executor_instance
