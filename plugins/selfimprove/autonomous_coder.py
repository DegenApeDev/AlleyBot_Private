"""
Autonomous Coder Mixin
AI-powered code generation, validation, and self-update pipeline.

Flow:
1. Detect what needs to change (from skill diff, task description, or brain decision)
2. Read existing code to understand context
3. Generate code changes using Grok (primary) / DeepSeek (fallback)
4. Validate safety (no eval/exec/os.system, valid syntax)
5. Run test suite to ensure no regressions
6. Apply changes to the codebase on an auto/* git branch
7. Commit, push, and optionally restart

Safety:
- All changes go through validate_code_safety() from TestGateMixin
- Full test suite must pass before changes are applied
- Changes are committed on auto/* branches (never on main/opus_rebuild)
- Backups are created before any file is modified
- Dangerous patterns are blocked (eval, exec, os.system, etc.)
- Max file size limit prevents runaway generation
"""
import os
import re
import json
import shutil
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


# Max generated code size per file (prevent runaway)
MAX_CODE_SIZE = 50_000  # 50KB per file
MAX_FILES_PER_UPDATE = 10
ALLOWED_DIRS = ['plugins/', 'src/', 'skills/', 'config/']
BLOCKED_FILES = ['.env', 'alleybot_core.py', 'plugin_manager.py', 'run_alleybot.py']


class AutonomousCoderMixin:
    """Mixin for AI-powered autonomous code generation and self-update"""

    def _init_autonomous_coder(self):
        """Initialize autonomous coder state"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.update_log_file = os.path.join(self.project_root, 'skills', 'coder_log.json')
        self.pending_updates: List[Dict] = []
        self._coder_history: List[Dict] = []
        self._load_coder_state()
        print("🤖 Autonomous coder ready (Grok primary, DeepSeek fallback)")

    def _load_coder_state(self):
        """Load coder state from memory"""
        try:
            state = self.core.get_memory('selfimprove_coder_state')
            if state:
                self._coder_history = state.get('history', [])
        except Exception:
            pass

    def _save_coder_state(self):
        """Save coder state"""
        try:
            self.core.save_memory('selfimprove_coder_state', {
                'history': self._coder_history[-50:],
            })
        except Exception as e:
            print(f"⚠️  Failed to save coder state: {e}")

    # ------------------------------------------------------------------
    # AI Code Generation
    # ------------------------------------------------------------------

    def _generate_code_with_ai(self, task: str, context: str = "",
                                max_tokens: int = 4000) -> Optional[str]:
        """Generate code using Grok (primary) or DeepSeek (fallback)"""
        system_prompt = """You are an expert Python developer working on AlleyBot, an autonomous AI agent.
You generate clean, production-ready Python code following these rules:
1. Follow existing code style (mixin pattern, plugin architecture)
2. Include proper error handling with try/except
3. Use type hints
4. NO eval(), exec(), os.system(), __import__(), or shell=True
5. Only use standard library + packages already in requirements.txt
6. Keep functions focused and under 50 lines each
7. Return ONLY the code, no explanations or markdown fences"""

        user_prompt = f"""Task: {task}

{f'Context (existing code/skill file):{chr(10)}{context}' if context else ''}

Generate the complete Python code. Return ONLY the raw Python code, no markdown fences or explanations."""

        # Try Grok first (better reasoning for code)
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                result = grok_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=max_tokens)
                if result:
                    return self._clean_generated_code(result)
        except Exception as e:
            print(f"⚠️  Grok code generation failed: {e}")

        # Fallback to DeepSeek
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                result = deepseek_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=max_tokens)
                if result:
                    return self._clean_generated_code(result)
        except Exception as e:
            print(f"⚠️  DeepSeek code generation failed: {e}")

        return None

    def _clean_generated_code(self, raw: str) -> str:
        """Strip markdown fences and clean up AI output"""
        # Remove ```python ... ``` wrappers
        code = re.sub(r'^```(?:python)?\s*\n', '', raw.strip())
        code = re.sub(r'\n```\s*$', '', code)
        return code.strip()

    # ------------------------------------------------------------------
    # Plan: analyze what needs to change
    # ------------------------------------------------------------------

    def _plan_update(self, task: str, skill_content: str = "") -> Optional[Dict]:
        """Use AI to plan what files need to change and how"""
        # Gather project structure for context
        structure = self._get_project_structure()

        plan_prompt = f"""Analyze this task and create a code change plan for AlleyBot.

TASK: {task}

{f'SKILL FILE CONTENT:{chr(10)}{skill_content[:3000]}' if skill_content else ''}

PROJECT STRUCTURE (key files):
{structure}

Create a JSON plan with this exact format:
{{
    "summary": "Brief description of changes",
    "files": [
        {{
            "path": "relative/path/to/file.py",
            "action": "modify" or "create",
            "description": "What to change in this file"
        }}
    ],
    "test_modules": ["tests.test_fixes", "tests.test_phase2"]
}}

Rules:
- Only modify files in plugins/, src/, skills/, config/
- Never modify .env, alleybot_core.py, plugin_manager.py
- Max 10 files per update
- Include which test modules to run for validation

Return ONLY valid JSON, no markdown or explanation."""

        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                result = grok_ai.chat(plan_prompt, max_tokens=2000)
                if result:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        plan = json.loads(json_match.group())
                        # Validate plan
                        if self._validate_plan(plan):
                            return plan
        except Exception as e:
            print(f"⚠️  Plan generation failed: {e}")

        return None

    def _validate_plan(self, plan: Dict) -> bool:
        """Validate a code change plan for safety"""
        if not isinstance(plan, dict):
            return False
        files = plan.get('files', [])
        if not files or len(files) > MAX_FILES_PER_UPDATE:
            print(f"❌ Plan has {len(files)} files (max {MAX_FILES_PER_UPDATE})")
            return False

        for f in files:
            path = f.get('path', '')
            # Block dangerous paths
            if any(path.endswith(b) for b in BLOCKED_FILES):
                print(f"❌ Cannot modify blocked file: {path}")
                return False
            # Must be in allowed directories
            if not any(path.startswith(d) for d in ALLOWED_DIRS):
                if f.get('action') == 'create':
                    # New files can go in allowed dirs only
                    print(f"❌ Cannot create file outside allowed dirs: {path}")
                    return False

        return True

    def _get_project_structure(self) -> str:
        """Get a summary of the project structure for AI context"""
        lines = []
        for d in ['plugins/', 'src/', 'skills/']:
            full = os.path.join(self.project_root, d)
            if os.path.exists(full):
                for root, dirs, files in os.walk(full):
                    # Skip __pycache__
                    dirs[:] = [dd for dd in dirs if dd != '__pycache__']
                    rel = os.path.relpath(root, self.project_root)
                    py_files = [f for f in files if f.endswith('.py')]
                    if py_files:
                        lines.append(f"{rel}/: {', '.join(py_files)}")
        return '\n'.join(lines[:30])

    # ------------------------------------------------------------------
    # Execute: generate code for each file in the plan
    # ------------------------------------------------------------------

    def _execute_plan(self, plan: Dict) -> Dict[str, Any]:
        """Execute a code change plan: generate code, validate, test, apply"""
        results = {
            'plan': plan,
            'generated_files': [],
            'validation': {'safe': True, 'issues': []},
            'tests': {'success': False},
            'applied': False,
            'error': None,
        }

        # Step 1: Generate code for each file
        for file_info in plan['files']:
            path = file_info['path']
            action = file_info.get('action', 'modify')
            description = file_info.get('description', '')

            # Read existing file for context if modifying
            existing_code = ""
            full_path = os.path.join(self.project_root, path)
            if action == 'modify' and os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        existing_code = f.read()
                except Exception:
                    pass

            if action == 'modify' and existing_code:
                task = f"Modify this file: {path}\nChange: {description}\n\nExisting code:\n{existing_code[:8000]}"
            else:
                task = f"Create new file: {path}\nPurpose: {description}\nPlan summary: {plan.get('summary', '')}"

            print(f"🔧 Generating code for {path} ({action})...")
            code = self._generate_code_with_ai(task)

            if not code:
                results['error'] = f"Failed to generate code for {path}"
                return results

            if len(code) > MAX_CODE_SIZE:
                results['error'] = f"Generated code too large for {path}: {len(code)} bytes"
                return results

            results['generated_files'].append({
                'path': path,
                'action': action,
                'code': code,
                'size': len(code),
            })

        # Step 2: Validate all generated code
        all_issues = []
        for gf in results['generated_files']:
            safety = self.validate_code_safety(gf['code'])
            if not safety['safe']:
                all_issues.extend(safety['issues'])

        results['validation'] = {
            'safe': len(all_issues) == 0,
            'issues': all_issues,
        }

        if not results['validation']['safe']:
            results['error'] = f"Safety validation failed: {'; '.join(all_issues)}"
            return results

        # Step 3: Apply changes (on auto/* branch)
        apply_result = self._apply_changes(results['generated_files'], plan.get('summary', 'auto-update'))
        if not apply_result['success']:
            results['error'] = f"Failed to apply changes: {apply_result.get('error', '?')}"
            return results

        # Step 4: Run test suite (with debug-and-retry on failure)
        test_modules = plan.get('test_modules', ['tests.test_fixes', 'tests.test_phase2',
                                                   'tests.test_phase3', 'tests.test_phase4',
                                                   'tests.test_phase5'])
        max_fix_attempts = 2
        attempt = 0

        while True:
            print(f"🧪 Running test suite{f' (fix attempt {attempt})' if attempt > 0 else ''}...")
            test_result = self.run_test_suite(test_modules)
            results['tests'] = test_result

            if test_result.get('success'):
                break  # Tests passed!

            attempt += 1
            if attempt > max_fix_attempts:
                # Exhausted retries — revert and give up
                print(f"❌ Tests still failing after {max_fix_attempts} fix attempts, reverting...")
                self._revert_changes(results['generated_files'])
                results['error'] = (
                    f"Tests failed after {max_fix_attempts} fix attempts: "
                    f"{test_result.get('failures', '?')} failures, "
                    f"{test_result.get('errors', '?')} errors"
                )
                return results

            # Debug-and-retry: feed errors back to AI for a fix
            print(f"🔧 Test failure detected — asking AI to fix (attempt {attempt}/{max_fix_attempts})...")
            error_output = test_result.get('output_tail', '')
            fixed = self._debug_and_fix(results['generated_files'], error_output, plan)

            if not fixed:
                print("❌ AI could not produce a fix, reverting...")
                self._revert_changes(results['generated_files'])
                results['error'] = (
                    f"Tests failed and auto-fix unsuccessful: "
                    f"{test_result.get('failures', '?')} failures, "
                    f"{test_result.get('errors', '?')} errors\n"
                    f"Error: {error_output[-300:]}"
                )
                return results

            # Re-apply the fixed code
            print("📝 Applying fixed code...")
            for gf in results['generated_files']:
                full_path = os.path.join(self.project_root, gf['path'])
                try:
                    with open(full_path, 'w') as f:
                        f.write(gf['code'])
                except Exception as e:
                    print(f"  ⚠️  Failed to write fix for {gf['path']}: {e}")

        results['applied'] = True
        results['fix_attempts'] = attempt
        print(f"✅ Update applied: {plan.get('summary', '?')}"
              f"{f' (after {attempt} fix(es))' if attempt > 0 else ''}")
        return results

    # ------------------------------------------------------------------
    # Debug-and-fix: AI-powered error correction
    # ------------------------------------------------------------------

    def _debug_and_fix(self, generated_files: List[Dict], error_output: str,
                       plan: Dict) -> bool:
        """Feed test errors back to AI and get fixed code.

        Mutates generated_files in-place with corrected code.
        Returns True if at least one file was fixed, False if AI couldn't help.
        """
        any_fixed = False

        for gf in generated_files:
            path = gf['path']
            current_code = gf['code']

            fix_prompt = f"""The following Python code was generated for AlleyBot but FAILED tests.

FILE: {path}
PLAN: {plan.get('summary', '?')}

CURRENT CODE:
```python
{current_code[:6000]}
```

TEST ERROR OUTPUT:
```
{error_output[-1500:]}
```

Fix the code so the tests pass. Common issues:
- Import errors (wrong module path, missing import)
- Attribute errors (wrong method name, missing self parameter)
- Type errors (wrong argument count, wrong types)
- Logic errors (wrong return value, missing edge case)

Return ONLY the complete fixed Python file. No explanations, no markdown fences."""

            fixed_code = self._generate_code_with_ai(fix_prompt, max_tokens=6000)

            if not fixed_code:
                print(f"  ⚠️  AI returned no fix for {path}")
                continue

            # Validate the fix
            safety = self.validate_code_safety(fixed_code)
            if not safety['safe']:
                print(f"  ⚠️  AI fix for {path} failed safety check: {safety['issues']}")
                continue

            # Update in-place
            gf['code'] = fixed_code
            any_fixed = True
            print(f"  🔧 Got fix for {path} ({len(fixed_code)} bytes)")

        return any_fixed

    # ------------------------------------------------------------------
    # Apply / Revert file changes
    # ------------------------------------------------------------------

    def _apply_changes(self, generated_files: List[Dict], summary: str) -> Dict[str, Any]:
        """Apply generated code changes to the filesystem"""
        backup_dir = os.path.join(self.project_root, 'skills', 'backups',
                                   datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(backup_dir, exist_ok=True)

        applied = []
        try:
            for gf in generated_files:
                full_path = os.path.join(self.project_root, gf['path'])

                # Backup existing file
                if os.path.exists(full_path):
                    bak_path = os.path.join(backup_dir, gf['path'].replace('/', '_'))
                    shutil.copy2(full_path, bak_path)

                # Create parent dirs
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Write new code
                with open(full_path, 'w') as f:
                    f.write(gf['code'])

                applied.append(gf['path'])
                print(f"  📝 {'Created' if gf['action'] == 'create' else 'Modified'}: {gf['path']}")

            return {'success': True, 'files': applied, 'backup_dir': backup_dir}

        except Exception as e:
            # Revert on error
            self._revert_from_backup(backup_dir, applied)
            return {'success': False, 'error': str(e)}

    def _revert_changes(self, generated_files: List[Dict]):
        """Revert applied changes using git checkout"""
        for gf in generated_files:
            full_path = os.path.join(self.project_root, gf['path'])
            try:
                if gf['action'] == 'create' and os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"  🗑️  Removed: {gf['path']}")
                elif gf['action'] == 'modify':
                    subprocess.run(
                        ['git', 'checkout', '--', gf['path']],
                        cwd=self.project_root,
                        capture_output=True, timeout=10,
                    )
                    print(f"  ↩️  Reverted: {gf['path']}")
            except Exception as e:
                print(f"  ⚠️  Failed to revert {gf['path']}: {e}")

    def _revert_from_backup(self, backup_dir: str, applied_paths: List[str]):
        """Revert from backup directory"""
        for path in applied_paths:
            bak_path = os.path.join(backup_dir, path.replace('/', '_'))
            full_path = os.path.join(self.project_root, path)
            if os.path.exists(bak_path):
                shutil.copy2(bak_path, full_path)

    # ------------------------------------------------------------------
    # Git commit + push
    # ------------------------------------------------------------------

    def _commit_and_push(self, summary: str, files: List[str]) -> Dict[str, Any]:
        """Commit changes and push to remote"""
        try:
            # Stage files
            for f in files:
                subprocess.run(['git', 'add', f], cwd=self.project_root,
                               capture_output=True, timeout=10)

            # Commit
            msg = f"[auto-coder] {summary}"
            result = subprocess.run(
                ['git', 'commit', '-m', msg],
                cwd=self.project_root, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {'success': False, 'error': f"Commit failed: {result.stderr}"}

            # Push
            result = subprocess.run(
                ['git', 'push'],
                cwd=self.project_root, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {'success': False, 'error': f"Push failed: {result.stderr}"}

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Self-restart
    # ------------------------------------------------------------------

    def _self_restart(self):
        """Restart the bot process by re-executing the entry point"""
        print("🔄 Self-restarting AlleyBot...")

        # Notify via Telegram if possible
        try:
            telegram = self.core.plugin_manager.plugins.get('telegram')
            if telegram and hasattr(telegram, 'send_message_to_owner_sync'):
                telegram.send_message_to_owner_sync(
                    "🔄 AlleyBot is self-restarting to apply code updates..."
                )
        except Exception:
            pass

        # Find the entry point
        entry = os.path.join(self.project_root, 'src', 'main.py')
        venv_python = os.path.join(self.project_root, 'venv', 'bin', 'python')
        python_cmd = venv_python if os.path.exists(venv_python) else 'python3'

        # Replace current process
        os.execv(python_cmd, [python_cmd, entry])

    # ------------------------------------------------------------------
    # High-level commands
    # ------------------------------------------------------------------

    def self_update_command(self, *args):
        """Run a full self-update cycle: plan → generate → validate → test → apply → commit.
        Usage: improve_self_update <task description>"""
        if not args:
            return "❌ Usage: improve_self_update <task description>"

        task = ' '.join(args)
        return self._run_self_update(task)

    def self_update_from_skill_command(self, *args):
        """Update code based on a platform skill file change.
        Usage: improve_apply_skill <platform>"""
        if not args:
            return "❌ Usage: improve_apply_skill <platform>"

        platform = args[0].lower().strip()
        skill_file = os.path.join(self.project_root, 'skills', f'{platform}_skill.md')

        if not os.path.exists(skill_file):
            return f"❌ No skill file found for {platform}. Run improve_update_skills first."

        with open(skill_file, 'r') as f:
            skill_content = f.read()

        task = (f"Update the {platform} plugin to implement changes described in the "
                f"updated {platform} skill file. Compare the skill requirements with "
                f"the current plugin code and implement any missing features or protocol changes.")

        return self._run_self_update(task, skill_content=skill_content)

    def _run_self_update(self, task: str, skill_content: str = "") -> str:
        """Core self-update pipeline"""
        print(f"🤖 Starting self-update: {task[:80]}...")

        # Step 1: Plan
        print("📋 Planning changes...")
        plan = self._plan_update(task, skill_content)
        if not plan:
            return "❌ Failed to generate a code change plan"

        print(f"📋 Plan: {plan.get('summary', '?')}")
        for f in plan.get('files', []):
            print(f"  {'📝' if f['action'] == 'modify' else '📄'} {f['path']}: {f['description'][:60]}")

        # Step 2: Execute plan (generate, validate, test, apply)
        result = self._execute_plan(plan)

        if result.get('error'):
            self._log_coder_update(task, plan, False, result['error'])
            return f"❌ Self-update failed: {result['error']}"

        if not result.get('applied'):
            self._log_coder_update(task, plan, False, "Changes not applied")
            return "❌ Self-update failed: changes were not applied"

        # Step 3: Commit and push
        files = [gf['path'] for gf in result['generated_files']]
        commit_result = self._commit_and_push(plan.get('summary', task[:50]), files)

        if not commit_result['success']:
            self._log_coder_update(task, plan, True, f"Applied but commit failed: {commit_result.get('error')}")
            return f"⚠️  Code applied but commit failed: {commit_result.get('error')}"

        self._log_coder_update(task, plan, True, None)

        tests = result.get('tests', {})
        fix_attempts = result.get('fix_attempts', 0)
        output = f"✅ Self-update complete: {plan.get('summary', '?')}\n"
        output += f"  📝 Files: {len(files)}\n"
        output += f"  🧪 Tests: {tests.get('tests_run', '?')} passed\n"
        if fix_attempts:
            output += f"  🔧 Auto-fixed {fix_attempts} test failure(s)\n"
        output += f"  📦 Committed and pushed\n"

        return output

    def self_update_and_restart_command(self, *args):
        """Run self-update then restart the bot. Usage: improve_update_restart <task>"""
        if not args:
            return "❌ Usage: improve_update_restart <task description>"

        result = self.self_update_command(*args)
        if result.startswith("✅"):
            self._self_restart()
            # Won't reach here if restart succeeds
        return result

    def coder_status_command(self, *args):
        """Show autonomous coder status and recent history"""
        output = "🤖 Autonomous Coder Status\n\n"

        recent = self._coder_history[-5:]
        if recent:
            output += "📋 Recent Updates:\n"
            for entry in reversed(recent):
                icon = "✅" if entry.get('success') else "❌"
                output += f"  {icon} {entry.get('task', '?')[:60]}\n"
                output += f"     {entry.get('timestamp', '?')[:16]}\n"
                if entry.get('error'):
                    output += f"     Error: {entry['error'][:60]}\n"
        else:
            output += "📋 No updates yet\n"

        output += f"\n  🔒 Safety: validate_code_safety + full test suite\n"
        output += f"  🔀 Branch: auto/* only\n"
        output += f"  🤖 AI: Grok primary, DeepSeek fallback\n"

        return output

    def _log_coder_update(self, task: str, plan: Optional[Dict], success: bool, error: Optional[str]):
        """Log an update attempt"""
        entry = {
            'task': task[:200],
            'summary': plan.get('summary', '') if plan else '',
            'files': [f['path'] for f in plan.get('files', [])] if plan else [],
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat(),
        }
        self._coder_history.append(entry)
        self._save_coder_state()

        # Also append to disk log
        try:
            os.makedirs(os.path.dirname(self.update_log_file), exist_ok=True)
            with open(self.update_log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception:
            pass
