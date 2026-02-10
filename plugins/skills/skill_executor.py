"""
Skill Executor
Execute skill instructions with tool access and script execution
"""
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts"""

    def __init__(self, config):
        super().__init__(config)
        self.execution_log: List[Dict] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)

    def execute_skill(self, skill_name: str, task: str, context: str = "") -> Dict[str, Any]:
        """Execute a skill with given task and context"""
        # Load skill if not already loaded
        skill = self._load_full_skill(skill_name)
        if not skill:
            return {'success': False, 'error': f'Skill not found: {skill_name}'}

        # Activate skill
        self.activate_skill(skill_name)

        try:
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
                'success': True
            }
            self.execution_log.append(execution_record)

            return {
                'success': True,
                'skill': skill_name,
                'prompt': skill_prompt,
                'scripts_result': scripts_result,
                'execution': execution_record
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Skill execution failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'skill': skill_name
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
            output += f"  {success} {when} | {skill}: {task}...\n"
        return output
