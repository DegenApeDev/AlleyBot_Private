"""
Test-Before-Merge Gate Mixin
Generated code must pass tests before it can be merged.
"""
import os
import subprocess
import tempfile
import ast
from typing import Dict, List, Any, Optional


class TestGateMixin:
    """Mixin for test-before-merge workflow"""

    def _init_test_gate(self):
        """Initialize test gate state"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.test_results_history: List[Dict] = []
        self._load_test_state()

    def _load_test_state(self):
        """Load test gate state from memory"""
        try:
            state = self.core.get_memory('selfimprove_test_state')
            if state:
                self.test_results_history = state.get('test_results_history', [])
        except Exception:
            pass

    def _save_test_state(self):
        """Save test gate state"""
        try:
            self.core.save_memory('selfimprove_test_state', {
                'test_results_history': self.test_results_history[-30:],
            })
        except Exception as e:
            print(f"⚠️  Failed to save test state: {e}")

    def run_test_suite(self, test_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the project test suite and return results"""
        if not test_modules:
            test_modules = ['tests.test_fixes', 'tests.test_phase2', 'tests.test_phase3']

        try:
            # Find python executable
            venv_python = os.path.join(self.project_root, 'venv', 'bin', 'python')
            python_cmd = venv_python if os.path.exists(venv_python) else 'python3'

            # First ensure pytest is available
            check_cmd = [python_cmd, '-c', 'import pytest']
            check_result = subprocess.run(check_cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if check_result.returncode != 0:
                # Install pytest if missing
                install_cmd = [python_cmd, '-m', 'pip', 'install', 'pytest']
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, cwd=self.project_root)
                if install_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Failed to install pytest: {install_result.stderr}',
                        'failures': 0,
                        'errors': 1,
                        'total': 0
                    }

            cmd = [python_cmd, '-m', 'pytest'] + test_modules + ['-v', '--tb=short']
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            tests_run = 0
            failures = 0
            errors = 0

            for line in output.split('\n'):
                if ' passed' in line and ' failed' in line and ' error' in line:
                    # Parse pytest summary line like "31 passed, 1 failed, 2 errors"
                    try:
                        parts = line.split()
                        for part in parts:
                            if 'passed' in part:
                                tests_run += int(part.split()[0])
                            elif 'failed' in part:
                                failures += int(part.split()[0])
                            elif 'error' in part:
                                errors += int(part.split()[0])
                    except (ValueError, IndexError):
                        pass

            passed = result.returncode == 0

            test_result = {
                'success': passed,
                'tests_run': tests_run,
                'failures': failures,
                'errors': errors,
                'returncode': result.returncode,
                'output_tail': output[-500:] if output else '',
                'modules': test_modules,
            }

            return test_result

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Test suite timed out (120s)', 'tests_run': 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'tests_run': 0}

    def validate_code_safety(self, code: str) -> Dict[str, Any]:
        """Validate generated code for security issues before allowing merge"""
        issues = []

        # Dangerous patterns
        dangerous = [
            ('os.system(', 'Unsafe os.system() call'),
            ('eval(', 'Unsafe eval() call'),
            ('exec(', 'Unsafe exec() call'),
            ('__import__(', 'Dynamic import'),
            ('subprocess.call(', 'Unsafe subprocess.call'),
            ('shell=True', 'Shell injection risk'),
            ('pickle.loads', 'Unsafe deserialization'),
            ('rm -rf', 'Dangerous file deletion'),
        ]

        for pattern, description in dangerous:
            if pattern in code:
                issues.append(f"⚠️  {description}: found '{pattern}'")

        # Try to parse as valid Python
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"❌ Syntax error: {e}")

        return {
            'safe': len(issues) == 0,
            'issues': issues,
        }

    def test_code_in_sandbox(self, code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        """Test generated code in an isolated temp directory"""
        safety = self.validate_code_safety(code)
        if not safety['safe']:
            return {
                'success': False,
                'error': 'Code failed safety validation',
                'issues': safety['issues'],
            }

        with tempfile.TemporaryDirectory(prefix='alleybot_sandbox_') as sandbox:
            try:
                # Write the code
                code_file = os.path.join(sandbox, 'generated_code.py')
                with open(code_file, 'w') as f:
                    f.write(code)

                # Write test if provided
                if test_code:
                    test_file = os.path.join(sandbox, 'test_generated.py')
                    with open(test_file, 'w') as f:
                        f.write(test_code)

                # Find python executable
                venv_python = os.path.join(self.project_root, 'venv', 'bin', 'python')
                python_cmd = venv_python if os.path.exists(venv_python) else 'python3'

                # Syntax check
                result = subprocess.run(
                    [python_cmd, '-c', f"import ast; ast.parse(open('{code_file}').read()); print('OK')"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    return {'success': False, 'error': f'Syntax check failed: {result.stderr}'}

                # Run test if provided
                if test_code:
                    result = subprocess.run(
                        [python_cmd, test_file],
                        capture_output=True, text=True, timeout=30,
                        cwd=sandbox,
                    )
                    return {
                        'success': result.returncode == 0,
                        'stdout': result.stdout[-500:],
                        'stderr': result.stderr[-500:],
                    }

                return {'success': True, 'message': 'Code passed syntax and safety checks'}

            except subprocess.TimeoutExpired:
                return {'success': False, 'error': 'Sandbox execution timed out'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def merge_gate_check(self, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """Full merge gate: run test suite and report pass/fail"""
        print("🧪 Running merge gate checks...")

        # Run full test suite
        test_result = self.run_test_suite()

        gate_result = {
            'branch': branch_name or self._current_branch(),
            'tests': test_result,
            'gate_passed': test_result.get('success', False),
            'summary': '',
        }

        if test_result.get('success'):
            gate_result['summary'] = (
                f"✅ GATE PASSED: {test_result['tests_run']} tests, "
                f"0 failures, 0 errors"
            )
        else:
            gate_result['summary'] = (
                f"❌ GATE FAILED: {test_result.get('tests_run', 0)} tests, "
                f"{test_result.get('failures', '?')} failures, "
                f"{test_result.get('errors', '?')} errors"
            )

        # Record result
        self.test_results_history.append(gate_result)
        self._save_test_state()

        print(gate_result['summary'])
        return gate_result

    def test_gate_command(self, *args):
        """Run test gate checks. Usage: improve_test [module...]"""
        modules = list(args) if args else None
        if modules:
            result = self.run_test_suite(modules)
        else:
            result = self.run_test_suite()

        if result.get('success'):
            return f"✅ Tests passed: {result['tests_run']} tests, 0 failures"
        elif result.get('error'):
            return f"❌ Test error: {result['error']}"
        else:
            return (
                f"❌ Tests failed: {result.get('tests_run', 0)} tests, "
                f"{result.get('failures', '?')} failures, "
                f"{result.get('errors', '?')} errors\n"
                f"{result.get('output_tail', '')[-200:]}"
            )

    def merge_gate_command(self, *args):
        """Run full merge gate check"""
        result = self.merge_gate_check()
        return result['summary']

    def sandbox_test_command(self, *args):
        """Test code snippet in sandbox. Usage: improve_sandbox <code>"""
        if not args:
            return "❌ Usage: improve_sandbox <python_code>"
        code = ' '.join(args)
        result = self.test_code_in_sandbox(code)
        if result.get('success'):
            return f"✅ Code passed sandbox checks\n{result.get('message', '')}"
        return f"❌ Sandbox failed: {result.get('error', 'Unknown')}\n{result.get('issues', '')}"
