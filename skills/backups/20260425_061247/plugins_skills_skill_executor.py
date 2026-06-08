"""
Skill Executor
Execute skill instructions with tool access and script execution.

SKILL COMPOSITION: Skills can call other skills via self.call_skill() during execution.
This enables complex multi-skill workflows and emergent capabilities.
"""
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts with composition support"""

    def __init__(self, config):
        super().__init__(config)
        self.execution_log: List[Dict] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)
        self._composition_stack: List[str] = []  # Track nested skill calls
        self._max_composition_depth = 5  # Prevent infinite recursion
        self._composition_results: Dict[str, Any] = {}  # Store intermediate results

    def execute_skill(self, skill_name: str, task: str, context: str = "") -> Dict[str, Any]:
        """
        Execute a skill with given task and context.
        
        SKILL COMPOSITION: Skills can call other skills via the injected
        `call_skill()` method, enabling complex multi-skill workflows.
        """
        # Check recursion depth
        if len(self._composition_stack) >= self._max_composition_depth:
            return {
                'success': False, 
                'error': f'Max composition depth ({self._max_composition_depth}) exceeded',
                'skill': skill_name,
                'composition_stack': self._composition_stack.copy()
            }
        
        # Check for circular dependencies
        if skill_name in self._composition_stack:
            return {
                'success': False,
                'error': f'Circular skill dependency detected: {skill_name} already in composition stack',
                'skill': skill_name,
                'composition_stack': self._composition_stack.copy()
            }
        
        # Load skill if not already loaded
        skill = self._load_full_skill(skill_name)
        if not skill:
            if skill_name != "unknown_handler":
                print(f"🔄 Unknown skill '{skill_name}', delegating to unknown_handler")
                return self.execute_skill("unknown_handler", f"Handle unknown skill '{skill_name}': {task}", context)
            return {'success': False, 'error': f'Skill not found: {skill_name}'}

        # Activate skill
        self.activate_skill(skill_name)
        
        # Add to composition stack
        self._composition_stack.append(skill_name)

        try:
            # Inject composition capabilities into skill
            skill._call_skill = self._create_skill_caller(skill_name)
            skill._composition_depth = len(self._composition_stack)
            skill._composition_context = self._composition_results.copy()
            
            # Check for scripts to execute
            scripts_result = None
            if skill.get('scripts'):
                scripts_result = self._execute_scripts(skill['scripts'], task)

            # Get AI guidance from skill body
            skill_prompt = self.get_skill_prompt(skill_name)

            # Log execution
            execution_record = {
                'skill': skill_name,
                'task': task,
                'executed_at': datetime.now().isoformat(),
                'scripts_executed': bool(scripts_result),
                'composition_depth': len(self._composition_stack),
                'success': True
            }
            self.execution_log.append(execution_record)
            
            # Store result for composition
            result_key = f"{skill_name}_{len(self._composition_stack)}"
            self._composition_results[result_key] = {
                'skill': skill_name,
                'task': task,
                'result': scripts_result,
                'prompt': skill_prompt
            }

            return {
                'success': True,
                'skill': skill_name,
                'prompt': skill_prompt,
                'scripts_result': scripts_result,
                'execution': execution_record,
                'composition_stack': self._composition_stack.copy(),
                'composition_results': self._composition_results.copy()
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Skill execution failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'skill': skill_name,
                'composition_stack': self._composition_stack.copy()
            }
        finally:
            # Remove from composition stack
            if skill_name in self._composition_stack:
                self._composition_stack.remove(skill_name)
    
    def _create_skill_caller(self, parent_skill_name: str) -> Callable:
        """
        Create a callable that allows a skill to execute other skills.
        
        This enables skill composition - skills can call other skills
        to build complex workflows from simple building blocks.
        """
        def call_skill(skill_name: str, task: str = "", context: str = "") -> Dict[str, Any]:
            """
            Call another skill from within the current skill.
            
            Args:
                skill_name: Name of the skill to call
                task: Task description for the called skill
                context: Additional context for the called skill
                
            Returns:
                Dict with 'success', 'result', and composition info
            """
            print(f"  🔗 Composition: {parent_skill_name} → calling {skill_name}")
            
            # Execute the child skill
            result = self.execute_skill(skill_name, task, context)
            
            if result.get('success'):
                print(f"  ✅ Composition successful: {skill_name}")
            else:
                print(f"  ❌ Composition failed: {skill_name} - {result.get('error', 'Unknown error')}")
            
            return result
        
        return call_skill
    
    def execute_skill_composition(self, skill_chain: List[str], initial_task: str = "") -> Dict[str, Any]:
        """
        Execute a chain of skills in sequence.
        
        Each skill in the chain can access results from previous skills
        via the composition_context.
        
        Args:
            skill_chain: List of skill names to execute in order
            initial_task: Initial task for the first skill
            
        Returns:
            Combined results from all skills in the chain
        """
        if not skill_chain:
            return {'success': False, 'error': 'Empty skill chain'}
        
        print(f"⛓️  Starting skill composition: {' → '.join(skill_chain)}")
        
        results = []
        current_task = initial_task
        
        for i, skill_name in enumerate(skill_chain):
            print(f"  Step {i+1}/{len(skill_chain)}: {skill_name}")
            
            result = self.execute_skill(skill_name, current_task)
            results.append(result)
            
            if not result.get('success'):
                print(f"  ❌ Chain broken at {skill_name}")
                return {
                    'success': False,
                    'error': f'Chain failed at skill {skill_name}',
                    'failed_step': i,
                    'results': results
                }
            
            # Next skill gets summary of previous result as its task
            current_task = f"Previous skill {skill_name} result: {result.get('prompt', 'N/A')[:100]}"
        
        print(f"✅ Composition chain complete: {len(results)} skills executed")
        
        return {
            'success': True,
            'chain': skill_chain,
            'results': results,
            'final_result': results[-1] if results else None
        }

    def _execute_scripts(self, scripts: List[str], task: str) -> Optional[Dict]:
        """Execute bundled scripts in the skill directory"""
        results = {}
        for script_path in scripts:
            if not os.path.exists(script_path):
                print(f"⚠️ Script missing: {script_path}")
                results[script_path] = {'error': 'File not found'}
                continue
            try:
                result = subprocess.run(
                    [sys.executable, script_path],
                    input=task,
                    capture_output=True,
                    text=True,
                    timeout=self.max_script_runtime,
                    cwd=os.path.dirname(script_path) if os.path.dirname(script_path) else None
                )
                output = result.stdout.strip() if result.stdout.strip() else result.stderr.strip()
                results[script_path] = {
                    'success': result.returncode == 0,
                    'output': output,
                    'returncode': result.returncode,
                }
            except subprocess.TimeoutExpired:
                results[script_path] = {'error': f'Timeout after {self.max_script_runtime}s'}
            except Exception as e:
                results[script_path] = {'error': str(e)}
        return results if results else None


class ActionRouter(SkillExecutorMixin):
    """Routes actions to skills or plugins with fallback to unknown_handler"""

    def __init__(self, config):
        super().__init__(config)

    def _execute_via_plugin(self, plugin_name: str, command: str, args: List[str]) -> str:
        """
        Execute a command via a plugin, falling back to unknown_handler skill for errors.
        """
        print(f"🔌 Executing via plugin: {plugin_name}.{command} {args}")
        # In a full implementation, this would access loaded plugins:
        # plugin = self.plugin_loader.get_plugin(plugin_name)
        # if plugin:
        #     func = plugin.get_commands().get(command)
        #     if func:
        #         return func(args)
        task = f"Execute plugin command '{command}' in '{plugin_name}' with args {args}"
        result = self.execute_skill("unknown_handler", task)
        if result.get('success'):
            return result.get('prompt', f"Plugin command executed: {command}")
        return f"Plugin execution failed ({plugin_name}.{command}): {result.get('error', 'Unknown error')}"