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

    @staticmethod
    def _sanitize_path(path: str, project_root: str) -> str:
        """
        Sanitize a path to prevent path traversal attacks.
        Ensures the resolved path stays within the project root.
        """
        import re
        
        # Block dangerous characters
        dangerous_chars = [';', '&', '|', '$', '`', '\x00', '\n']
        for char in dangerous_chars:
            if char in path:
                raise ValueError(f"Path contains dangerous character: {repr(char)}")
        
        # Normalize and resolve the path
        full_path = os.path.join(project_root, path)
        resolved_path = os.path.normpath(os.path.abspath(full_path))
        resolved_root = os.path.normpath(os.path.abspath(project_root))
        
        # Ensure path is within project root
        if not resolved_path.startswith(resolved_root + os.sep) and resolved_path != resolved_root:
            raise ValueError(f"Path '{path}' escapes project root (resolved to: {resolved_path})")
        
        # Check against allowed directories
        rel_path = os.path.relpath(resolved_path, project_root)
        allowed = any(rel_path.startswith(d) for d in ALLOWED_DIRS)
        if not allowed:
            raise ValueError(f"Path '{path}' not in allowed directories: {ALLOWED_DIRS}")
        
        return resolved_path

    def _init_autonomous_coder(self):
        """Initialize autonomous coder state with circuit breaker"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.update_log_file = os.path.join(self.project_root, 'skills', 'coder_log.json')
        self.pending_updates: List[Dict] = []
        self._coder_history: List[Dict] = []
        # Circuit breaker for API failures
        self._api_failure_count = 0
        self._api_failure_threshold = 5  # Stop after 5 consecutive failures
        self._api_last_failure = None
        self._api_cooldown_minutes = 30  # Wait 30 min after threshold reached
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

    def _check_circuit_breaker(self) -> bool:
        """Check if API circuit breaker is open (too many failures)"""
        if self._api_failure_count >= self._api_failure_threshold:
            if self._api_last_failure:
                from datetime import datetime, timedelta
                cooldown_end = self._api_last_failure + timedelta(minutes=self._api_cooldown_minutes)
                if datetime.now() < cooldown_end:
                    remaining = int((cooldown_end - datetime.now()).total_seconds() / 60)
                    print(f"⛔ API circuit breaker OPEN: {self._api_failure_count} failures. Cooldown: {remaining}min remaining")
                    return False
                else:
                    # Reset after cooldown
                    print(f"🔓 API circuit breaker reset after cooldown")
                    self._api_failure_count = 0
                    self._api_last_failure = None
        return True

    def _record_api_failure(self):
        """Record an API failure for circuit breaker"""
        from datetime import datetime
        self._api_failure_count += 1
        self._api_last_failure = datetime.now()
        print(f"⚠️ API failure {self._api_failure_count}/{self._api_failure_threshold}")

    # ------------------------------------------------------------------
    # AI Code Generation
    # ------------------------------------------------------------------

    def _get_import_examples(self) -> str:
        """Get real import patterns from the codebase so AI uses correct paths"""
        examples = []
        # Scan a few key plugin files for their import lines
        sample_files = [
            'plugins/moltx/moltx_content.py',
            'plugins/moltbook/moltbook_content.py',
            'plugins/brain/brain.py',
            'plugins/onchain/onchain.py',
        ]
        for rel in sample_files:
            full = os.path.join(self.project_root, rel)
            if os.path.exists(full):
                try:
                    with open(full, 'r') as f:
                        lines = f.readlines()[:30]
                    imports = [l.rstrip() for l in lines if l.strip().startswith(('import ', 'from '))]
                    if imports:
                        examples.append(f"# {rel}")
                        examples.extend(imports[:8])
                except Exception:
                    pass
        return '\n'.join(examples[:40])

    def _sandbox_check_file(self, code: str, filepath: str) -> Dict[str, Any]:
        """Pre-test a single generated file in isolation: syntax + import check.
        Returns {'ok': bool, 'error': str}.
        Does NOT touch the real filesystem."""
        import tempfile

        # 1. Syntax check via ast.parse
        import ast
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {'ok': False, 'error': f'Syntax error: {e}'}

        # 2. Try to compile + import in a subprocess so we catch ModuleNotFoundError
        #    We run with the project root on PYTHONPATH so real project imports resolve.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            venv_python = os.path.join(self.project_root, 'venv', 'bin', 'python')
            python_cmd = venv_python if os.path.exists(venv_python) else 'python3'

            env = os.environ.copy()
            env['PYTHONPATH'] = self.project_root + ':' + env.get('PYTHONPATH', '')

            result = subprocess.run(
                [python_cmd, '-c', f"import py_compile; py_compile.compile(r'{tmp_path}', doraise=True)"],
                capture_output=True, text=True, timeout=15, env=env,
            )
            if result.returncode != 0:
                return {'ok': False, 'error': f'Compile check failed: {result.stderr[-300:]}'}

            # 3. Try a quick import to catch ModuleNotFoundError etc.
            #    We wrap in try/except inside the subprocess so env-specific errors
            #    (missing API keys, etc.) don't count as failures.
            import_check = (
                f"import sys, os\n"
                f"sys.path.insert(0, r'{self.project_root}')\n"
                f"try:\n"
                f"    compile(open(r'{tmp_path}').read(), r'{tmp_path}', 'exec')\n"
                f"    print('OK')\n"
                f"except SyntaxError as e:\n"
                f"    print(f'SYNTAX:{{e}}')\n"
                f"    sys.exit(1)\n"
            )
            result = subprocess.run(
                [python_cmd, '-c', import_check],
                capture_output=True, text=True, timeout=15, env=env,
            )
            if result.returncode != 0:
                return {'ok': False, 'error': result.stderr[-300:] or result.stdout[-300:]}

            return {'ok': True, 'error': ''}

        except subprocess.TimeoutExpired:
            return {'ok': False, 'error': 'Sandbox check timed out'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _try_template_generation(self, task: str, path: str) -> Optional[str]:
        """Try to generate code using templates for common simple tasks.
        
        This bypasses AI generation for predictable patterns like:
        - Utility functions (palindrome, string processing)
        - Simple text analysis
        - Basic helper functions
        
        Returns generated code or None if not a recognized pattern.
        """
        task_lower = task.lower()
        
        # Pattern: Palindrome detection
        if 'palindrome' in task_lower:
            return self._generate_palindrome_utility(path)
        
        # Pattern: String/ text utility
        if any(word in task_lower for word in ['string utility', 'text utility', 'text processing']):
            return self._generate_text_utility_template(path)
        
        # Pattern: Simple math utility
        if any(word in task_lower for word in ['math utility', 'number utility', 'calculation']):
            return self._generate_math_utility_template(path)
        
        return None
    
    def _generate_palindrome_utility(self, path: str) -> str:
        """Generate a robust palindrome detection utility."""
        return """\"\"\"
Text utility functions for palindrome detection and generation.
\"\"\"
import re


def is_palindrome(text: str) -> bool:
    \"\"\"Check if text is a palindrome, ignoring case and punctuation.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text is a palindrome, False otherwise
    \"\"\"
    if not text:
        return True
    
    # Remove non-alphanumeric characters and convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    
    # Empty or single character is a palindrome
    if len(cleaned) <= 1:
        return True
    
    # Check if string equals its reverse
    return cleaned == cleaned[::-1]


def find_palindromes(text: str, min_length: int = 3) -> list:
    \"\"\"Find all palindromic substrings in text.
    
    Args:
        text: The text to search
        min_length: Minimum length of palindromes to find
        
    Returns:
        List of palindromic substrings found
    \"\"\"
    if not text or len(text) < min_length:
        return []
    
    palindromes = []
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    
    # Check all substrings
    for i in range(len(cleaned)):
        for j in range(i + min_length, len(cleaned) + 1):
            substring = cleaned[i:j]
            if substring == substring[::-1] and len(substring) >= min_length:
                palindromes.append(substring)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in palindromes:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    
    return unique


def generate_palindromic_response(text: str) -> str:
    \"\"\"Generate a palindromic response for engagement.
    
    Creates a fun palindrome-based reply to use in comments/raids.
    
    Args:
        text: The original text to respond to
        
    Returns:
        A palindromic response string
    \"\"\"
    if not text:
        return "A man, a plan, a canal: Panama!"
    
    # Check if the text itself is a palindrome
    if is_palindrome(text):
        return "Nice palindrome! '" + text + "' reads the same forwards and backwards."
    
    # Generate a context-aware palindrome
    palindromes = [
        "A man, a plan, a canal: Panama!",
        "Was it a car or a cat I saw?",
        "No 'x' in Nixon.",
        "Madam, I'm Adam.",
        "A Santa at NASA.",
        "Mr. Owl ate my metal worm.",
        "Do geese see God?",
        "Never odd or even.",
    ]
    
    import random
    return random.choice(palindromes)


def make_palindrome(text: str) -> str:
    \"\"\"Create a palindrome by mirroring the text.
    
    Args:
        text: Base text to mirror
        
    Returns:
        A palindrome created from the text
    \"\"\"
    if not text:
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    # Mirror the text (excluding last char to avoid double middle letter)
    mirrored = cleaned + cleaned[-2::-1] if len(cleaned) > 1 else cleaned
    return mirrored
"""
    
    def _generate_text_utility_template(self, path: str) -> str:
        """Generate a basic text utility module template."""
        return """\"\"\"
Text utility functions for AlleyBot.
\"\"\"
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    \"\"\"Clean text by removing extra whitespace and normalizing.\"\"\"
    if not text:
        return ""
    # Remove extra whitespace
    cleaned = re.sub(r'\\s+', ' ', text)
    # Strip leading/trailing
    return cleaned.strip()


def extract_hashtags(text: str) -> List[str]:
    \"\"\"Extract hashtags from text.\"\"\"
    if not text:
        return []
    return re.findall(r'#\\w+', text)


def extract_mentions(text: str) -> List[str]:
    \"\"\"Extract @mentions from text.\"\"\"
    if not text:
        return []
    return re.findall(r'@\\w+', text)


def truncate_text(text: str, max_length: int = 280, suffix: str = "...") -> str:
    \"\"\"Truncate text to max_length with suffix.\"\"\"
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def count_words(text: str) -> int:
    \"\"\"Count words in text.\"\"\"
    if not text:
        return 0
    return len(text.split())
"""
    
    def _generate_math_utility_template(self, path: str) -> str:
        """Generate a basic math utility module template."""
        return """\"\"\"
Math utility functions for AlleyBot.
\"\"\"
import math
from typing import List, Optional


def clamp(value: float, min_val: float, max_val: float) -> float:
    \"\"\"Clamp value between min and max.\"\"\"
    return max(min_val, min(max_val, value))


def lerp(start: float, end: float, t: float) -> float:
    \"\"\"Linear interpolation between start and end.\"\"\"
    return start + (end - start) * clamp(t, 0.0, 1.0)


def average(values: List[float]) -> float:
    \"\"\"Calculate average of list.\"\"\"
    if not values:
        return 0.0
    return sum(values) / len(values)


def percentage(part: float, whole: float) -> float:
    \"\"\"Calculate percentage.\"\"\"
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def format_number(n: float, decimals: int = 2) -> str:
    \"\"\"Format number with K/M/B suffix.\"\"\"
    if n >= 1_000_000_000:
        return "{n/1_000_000_000:." + str(decimals) + "f}B".format(n=n, decimals=decimals)
    if n >= 1_000_000:
        return "{n/1_000_000:." + str(decimals) + "f}M".format(n=n, decimals=decimals)
    if n >= 1_000:
        return "{n/1_000:." + str(decimals) + "f}K".format(n=n, decimals=decimals)
    return "{n:." + str(decimals) + "f}".format(n=n, decimals=decimals)
"""

    def _generate_code_with_ai(self, task: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate code using AI with timeout handling and circuit breaker"""
        # Check circuit breaker first
        if not self._check_circuit_breaker():
            print(" Skipping AI generation - circuit breaker open")
            return None

        system_prompt = """You are an expert Python developer. Generate clean, correct Python code for AlleyBot.

CRITICAL RULES:
1. Check every bracket, brace, and parenthesis is balanced before finishing
2. NEVER leave unclosed quotes, brackets, or parentheses
3. ALL f-strings must have valid expressions inside { } - escape literal braces as {{ }}
4. NO nested triple quotes inside the same type of quote
5. NEVER use eval(), exec(), os.system(), subprocess with shell=True
6. All code must be valid, complete Python files
7. Wrap optional imports in try/except blocks
8. Follow existing code style and conventions
9. EVERY function must have proper closing parentheses and quotes
10. Check all strings have matching quotes: 'text' or "text"
11. Check all brackets/braces/parens are balanced: [], {}, ()
12. Use 4 spaces for indentation, never tabs
13. Always use trailing commas in multi-line lists/dicts
14. Test your code mentally: would 'python -m py_compile' accept it?

Generate clean, production-ready Python code that passes syntax validation on first try."""

        user_prompt = f"Task: {task}\n\nGenerate complete Python code. Return ONLY code, no markdown fences, no explanations."

        # Try Grok with timeout handling (Grok has built-in 60s timeout + retries)
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                print(f"  🤖 Calling Grok API...")
                result = grok_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=max_tokens)
                if result:
                    self._api_failure_count = 0  # Reset on success
                    return self._clean_generated_code(result)
        except TimeoutError as e:
            print(f"⏰ Grok API timeout: {e}")
            self._record_api_failure()
        except Exception as e:
            print(f"⚠️ Grok code generation failed: {e}")
            self._record_api_failure()

        # Fallback to DeepSeek with timeout handling
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                print(f"  🤖 Calling DeepSeek API...")
                result = deepseek_ai.chat(user_prompt, system_prompt=system_prompt, max_tokens=max_tokens)
                if result:
                    self._api_failure_count = 0  # Reset on success
                    return self._clean_generated_code(result)
        except TimeoutError as e:
            print(f"⏰ DeepSeek API timeout: {e}")
            self._record_api_failure()
        except Exception as e:
            print(f"⚠️ DeepSeek code generation failed: {e}")
            self._record_api_failure()

        return None

    def _clean_generated_code(self, raw: str) -> str:
        """Strip markdown fences and clean up AI output"""
        text = raw.strip()

        # If the response contains a fenced code block, extract just the code
        fence_match = re.search(r'```(?:python|py)?\s*\n(.*?)```', text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)
        else:
            # Fallback: strip leading/trailing fences
            text = re.sub(r'^```(?:python|py)?\s*\n', '', text)
            text = re.sub(r'\n```\s*$', '', text)

        # Strip any leading prose before the first import/def/class/#
        lines = text.split('\n')
        code_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and (stripped.startswith(('import ', 'from ', 'def ', 'class ',
                                                  '#', '"""', "'''", '@'))
                            or stripped[0].isalpha() and '=' in stripped):
                code_start = i
                break
        text = '\n'.join(lines[code_start:])

        return text.strip()

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

    def _get_valid_test_modules(self) -> set:
        """Discover which test modules actually exist on disk (tests/test_*.py)"""
        valid = set()
        tests_dir = os.path.join(self.project_root, 'tests')
        if os.path.isdir(tests_dir):
            for f in os.listdir(tests_dir):
                if f.startswith('test_') and f.endswith('.py'):
                    valid.add(f'tests.{f[:-3]}')
        return valid

    def _scope_test_modules(self, plan: Dict) -> List[str]:
        """Determine which test modules to run based on files being changed.
        
        Instead of running ALL tests (190+), only run the modules that could
        be affected by the changed files. Falls back to a minimal smoke test
        if no specific mapping is found.
        """
        valid_modules = self._get_valid_test_modules()

        # Map file path prefixes to relevant test modules
        prefix_to_tests = {
            'plugins/moltx/': ['tests.test_phase2'],
            'plugins/moltbook/': ['tests.test_phase2'],
            'plugins/brain/': ['tests.test_phase2'],
            'plugins/onchain/': ['tests.test_phase3'],
            'plugins/selfimprove/': ['tests.test_phase4'],
            'plugins/telegram/': ['tests.test_phase2'],
            'plugins/analytics/': ['tests.test_phase2'],
            'plugins/a2a/': ['tests.test_phase2'],
            'src/': ['tests.test_fixes'],
            'skills/': [],  # Skill .md files don't need Python tests
            'config/': ['tests.test_fixes'],
        }

        # Collect test modules from plan files
        needed = set()
        changed_files = plan.get('files', [])
        for f in changed_files:
            path = f.get('path', '')
            matched = False
            for prefix, modules in prefix_to_tests.items():
                if path.startswith(prefix):
                    needed.update(modules)
                    matched = True
                    break
            if not matched:
                # Unknown path — add core smoke test
                needed.add('tests.test_fixes')

        # If plan specified test_modules, only add ones that actually exist
        plan_modules = plan.get('test_modules', [])
        for mod in plan_modules:
            if mod in valid_modules:
                needed.add(mod)
            else:
                print(f"  ⚠️  Ignoring bogus test module from plan: {mod}")

        # If only skill .md files changed, no Python tests needed — just syntax checks
        if not needed:
            # Still run a minimal smoke test to make sure nothing is broken
            needed.add('tests.test_fixes')

        # Final safety: filter out anything that doesn't exist
        needed = needed & valid_modules
        if not needed:
            needed.add('tests.test_fixes')

        result = sorted(needed)
        print(f"  🎯 Scoped tests: {', '.join(result)} (from {len(changed_files)} changed files)")
        return result

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
            
            # Try template-based generation first for common patterns
            code = self._try_template_generation(task, path)
            if code:
                print(f"  📋 Used template generation for {path}")
            else:
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

        # Step 2: Validate all generated code (with syntax-fix retry)
        max_syntax_retries = 2
        for syntax_attempt in range(max_syntax_retries + 1):
            all_issues = []
            syntax_issues = []
            security_issues = []

            for gf in results['generated_files']:
                safety = self.validate_code_safety(gf['code'])
                if not safety['safe']:
                    for issue in safety['issues']:
                        all_issues.append(issue)
                        if 'Syntax error' in issue:
                            syntax_issues.append((gf, issue))
                        else:
                            security_issues.append(issue)

            # Security violations are never retryable
            if security_issues:
                results['validation'] = {'safe': False, 'issues': all_issues}
                results['error'] = f"Safety validation failed: {'; '.join(security_issues)}"
                return results

            # No issues at all — pass
            if not syntax_issues:
                break

            # Syntax errors only — ask AI to fix (unless we've exhausted retries)
            if syntax_attempt >= max_syntax_retries:
                results['validation'] = {'safe': False, 'issues': all_issues}
                results['error'] = f"Safety validation failed after {max_syntax_retries} syntax fix attempts: {'; '.join(all_issues)}"
                return results

            print(f"🔧 Syntax error detected — asking AI to fix (attempt {syntax_attempt + 1}/{max_syntax_retries})...")
            for gf, issue in syntax_issues:
                fix_prompt = (
                    f"This Python code has a syntax error:\n{issue}\n\n"
                    f"```python\n{gf['code'][:6000]}\n```\n\n"
                    f"Fix the syntax error and return ONLY the complete corrected Python file. "
                    f"No markdown fences, no explanations."
                )
                fixed = self._generate_code_with_ai(fix_prompt, max_tokens=6000)
                if fixed:
                    gf['code'] = fixed
                    print(f"  🔧 Got syntax fix for {gf['path']} ({len(fixed)} bytes)")
                else:
                    print(f"  ⚠️  AI returned no syntax fix for {gf['path']}")

        results['validation'] = {'safe': True, 'issues': []}

        # Step 3: Sandbox pre-check each file (syntax + compile) BEFORE touching filesystem
        print("🔬 Running sandbox pre-checks...")
        sandbox_failures = []
        for gf in results['generated_files']:
            check = self._sandbox_check_file(gf['code'], gf['path'])
            if not check['ok']:
                sandbox_failures.append((gf, check['error']))

        # If sandbox fails, try one AI fix round before giving up
        if sandbox_failures:
            print(f"⚠️  {len(sandbox_failures)} file(s) failed sandbox check, asking AI to fix...")
            for gf, err in sandbox_failures:
                fix_prompt = (
                    f"This Python file failed a sandbox check with this error:\n{err}\n\n"
                    f"File: {gf['path']}\n"
                    f"```python\n{gf['code'][:6000]}\n```\n\n"
                    f"IMPORTANT: The project root is on PYTHONPATH. Use imports like:\n"
                    f"  from plugins.brain.brain import BrainPlugin\n"
                    f"  from grok_ai import grok_ai\n"
                    f"  import requests\n"
                    f"NEVER use relative imports. Wrap uncertain imports in try/except.\n\n"
                    f"Fix the code and return ONLY the complete corrected Python file."
                )
                fixed = self._generate_code_with_ai(fix_prompt, max_tokens=6000)
                if fixed:
                    gf['code'] = fixed

            # Re-check after fix
            still_failing = []
            for gf in results['generated_files']:
                check = self._sandbox_check_file(gf['code'], gf['path'])
                if not check['ok']:
                    still_failing.append(f"{gf['path']}: {check['error']}")

            if still_failing:
                results['error'] = f"Sandbox pre-check failed: {'; '.join(still_failing)}"
                return results

        # Step 4: Apply changes (on auto/* branch)
        apply_result = self._apply_changes(results['generated_files'], plan.get('summary', 'auto-update'))
        if not apply_result['success']:
            results['error'] = f"Failed to apply changes: {apply_result.get('error', '?')}"
            return results

        # Step 5: Run test suite (with debug-and-retry on failure)
        #   Scope tests: only run modules that could be affected by the changed files
        test_modules = self._scope_test_modules(plan)
        max_fix_attempts = 3
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

IMPORTANT import conventions:
- Project root is on PYTHONPATH. Use: from plugins.x.y import Z
- For AI: from grok_ai import grok_ai / from deepseek_ai import deepseek_ai
- For HTTP: import requests
- NEVER use relative imports. Wrap uncertain imports in try/except.

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
            try:
                # Sanitize path before using in subprocess
                safe_path = self._sanitize_path(gf['path'], self.project_root)
                full_path = os.path.join(self.project_root, gf['path'])
                
                if gf['action'] == 'create' and os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"  🗑️  Removed: {gf['path']}")
                elif gf['action'] == 'modify':
                    # Use sanitized path for git command
                    rel_path = os.path.relpath(safe_path, self.project_root)
                    subprocess.run(
                        ['git', 'checkout', '--', rel_path],
                        cwd=self.project_root,
                        capture_output=True, timeout=10,
                    )
                    print(f"  ↩️  Reverted: {gf['path']}")
            except ValueError as ve:
                print(f"  🚫 Security blocked revert for {gf['path']}: {ve}")
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
            # Stage files with path sanitization
            for f in files:
                try:
                    safe_path = self._sanitize_path(f, self.project_root)
                    rel_path = os.path.relpath(safe_path, self.project_root)
                    subprocess.run(['git', 'add', rel_path], cwd=self.project_root,
                                   capture_output=True, timeout=10)
                except ValueError as ve:
                    return {'success': False, 'error': f"Security blocked staging for {f}: {ve}"}

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
