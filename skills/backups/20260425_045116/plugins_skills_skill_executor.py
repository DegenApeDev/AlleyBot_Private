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
                continue

            # Determine script type by extension
            if script_path.endswith('.py'):
                result = self._run_python_script(script_path, task)
            elif script_path.endswith('.sh'):
                result = self._run_shell_script(script_path, task)
            else:
                # Skip unknown script types
                continue

            results[script_path.split('/')[-1]] = result

        return results if results else None

    def _run_python_script(self, script_path: str, task: str) -> Dict:
        """Execute a Python script with task as argument"""
        try:
            result = subprocess.run(
                ['python3', script_path, task],
                capture_output=True,
                text=True,
                timeout=self.max_script_runtime,
                cwd=os.path.dirname(script_path)
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Script timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_shell_script(self, script_path: str, task: str) -> Dict:
        """Execute a shell script with task as argument"""
        try:
            result = subprocess.run(
                [script_path, task],
                capture_output=True,
                text=True,
                timeout=self.max_script_runtime,
                cwd=os.path.dirname(script_path)
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Script timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def skill_exec_command(self, *args):
        """Execute a skill directly. Usage: skill_exec <name> <task>"""
        if len(args) < 2:
            return "❌ Usage: skill_exec <skill_name> <task_description>"

        skill_name = args[0]
        task = ' '.join(args[1:])

        result = self.execute_skill(skill_name, task)

        if result['success']:
            output = f"✅ Skill executed: {skill_name}\n"
            output += f"📝 Task: {task}\n"

            if result.get('scripts_result'):
                output += f"📜 Scripts: {len(result['scripts_result'])} executed\n"

            return output
        else:
            return f"❌ Skill execution failed: {result.get('error', 'Unknown error')}"

    def execution_log_command(self, *args):
        """Show skill execution log. Usage: skills_log"""
        if not self.execution_log:
            return "📭 No skill executions yet"

        output = "📚 Skill Execution Log:\n\n"
        for entry in reversed(self.execution_log[-10:]):
            skill = entry['skill']
            task = entry.get('task', '')[:40]
            when = entry['executed_at'][:16]
            success = "✅" if entry.get('success') else "❌"
            depth = entry.get('composition_depth', 0)
            depth_indicator = f"[depth:{depth}]" if depth > 1 else ""
            output += f"  {success} {when} | {skill}{depth_indicator}: {task}...\n"
        return output
    
    def skill_chain_command(self, *args):
        """
        Execute a chain of skills in sequence.
        Usage: skill_chain <skill1> <skill2> ... <skillN>
        
        Example: skill_chain crypto_prices sentiment_analysis moltx_post
        """
        if len(args) < 2:
            return "❌ Usage: skill_chain <skill1> <skill2> ... <skillN>\nExample: skill_chain crypto_prices sentiment_analysis post"
        
        skill_chain = list(args)
        
        result = self.execute_skill_composition(skill_chain)
        
        if result['success']:
            output = f"⛓️ Skill Chain Complete ({len(skill_chain)} skills)\n"
            output += f"Chain: {' → '.join(skill_chain)}\n\n"
            
            for i, step_result in enumerate(result['results'], 1):
                skill = step_result['skill']
                success = "✅" if step_result['success'] else "❌"
                depth = step_result.get('composition_depth', 1)
                output += f"  Step {i}: {success} {skill} (depth: {depth})\n"
                
                # Show composition info if present
                if step_result.get('composition_results'):
                    comp_count = len(step_result['composition_results'])
                    if comp_count > 1:
                        output += f"    └─ Composed {comp_count} intermediate results\n"
            
            final = result.get('final_result', {})
            if final:
                output += f"\n📊 Final Result: {final.get('prompt', 'N/A')[:100]}...\n"
            
            return output
        else:
            failed_step = result.get('failed_step', '?')
            error = result.get('error', 'Unknown error')
            return f"❌ Chain failed at step {failed_step}: {error}"
