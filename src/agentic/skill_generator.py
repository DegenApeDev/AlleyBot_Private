"""
Dynamic Skill Generation System with Sandboxing
Identifies capability gaps and generates new skills safely
"""
import os
import re
import ast
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class CodeSecurityValidator:
    """Validate generated code for security issues"""
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'os\.system',
        r'subprocess\.(?!run\(.*timeout)',  # Allow subprocess with timeout
        r'eval\(',
        r'exec\(',
        r'__import__\(',
        r'compile\(',
        r'open\(.*[\'"]w',  # Block write mode without explicit approval
        r'requests\.(?!get|post)',  # Only allow get/post
        r'socket\.',
        r'urllib\.request',
        r'pickle\.',
        r'shelve\.',
        r'marshal\.',
        r'globals\(\)',
        r'locals\(\)',
        r'vars\(\)',
        r'dir\(\)',
        r'__.*__',  # Dunder methods
        r'rm\s+-rf',
        r'del\s+',
    ]
    
    # Allowlisted imports
    ALLOWED_IMPORTS = {
        'json', 'time', 'datetime', 'typing', 'dataclasses',
        'requests', 'web3', 'eth_account', 'base64', 'hashlib',
        'math', 'random', 'collections', 're', 'pathlib'
    }
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate code for security issues
        
        Returns:
            Dict with 'safe' bool and 'issues' list
        """
        issues = []
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                issues.append(f"Dangerous pattern detected: {pattern}")
        
        # Parse AST to check imports
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in self.ALLOWED_IMPORTS:
                            issues.append(f"Disallowed import: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in self.ALLOWED_IMPORTS:
                        issues.append(f"Disallowed import from: {node.module}")
                
                # Check for exec/eval
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile']:
                            issues.append(f"Dangerous function call: {node.func.id}")
        
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")
        
        return {
            'safe': len(issues) == 0,
            'issues': issues
        }
    
    def sanitize_code(self, code: str) -> str:
        """Attempt to sanitize code by removing dangerous patterns"""
        # Remove dangerous imports
        lines = code.split('\n')
        safe_lines = []
        
        for line in lines:
            # Skip dangerous imports
            if any(pattern in line for pattern in ['os.system', 'eval(', 'exec(']):
                safe_lines.append(f"# REMOVED: {line}")
            else:
                safe_lines.append(line)
        
        return '\n'.join(safe_lines)


class SecureSandbox:
    """Execute code in a secure sandbox environment"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.validator = CodeSecurityValidator()
    
    def execute_in_sandbox(self, code: str, test_input: Any = None) -> Dict[str, Any]:
        """
        Execute code in a sandboxed environment
        
        Args:
            code: Python code to execute
            test_input: Optional test input for the code
            
        Returns:
            Dict with execution result, output, and errors
        """
        # Validate code first
        validation = self.validator.validate_code(code)
        if not validation['safe']:
            return {
                'success': False,
                'error': 'Code failed security validation',
                'issues': validation['issues']
            }
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute in subprocess with timeout
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={'PYTHONPATH': os.getcwd()}  # Restricted environment
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Execution timeout after {self.timeout} seconds'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)}'
            }
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass


class DynamicSkillGenerator:
    """
    Generate new skills dynamically based on capability gaps
    Focus on on-chain/crypto skills
    """
    
    def __init__(self, llm, skills_dir: str = 'dynamic_skills'):
        self.llm = llm
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(exist_ok=True)
        
        self.validator = CodeSecurityValidator()
        self.sandbox = SecureSandbox(timeout=5)
        
        self.generated_skills = []
        self.skill_registry = {}
        
    def identify_capability_gap(self, task: str, available_tools: List[str]) -> Optional[str]:
        """
        Identify if there's a capability gap for the given task
        
        Args:
            task: The task that needs to be accomplished
            available_tools: List of currently available tool names
            
        Returns:
            Description of the missing capability, or None if no gap
        """
        prompt = f"""Analyze this task and available tools to identify capability gaps.

Task: {task}

Available Tools: {', '.join(available_tools)}

Questions:
1. Can this task be accomplished with the available tools?
2. If not, what specific capability is missing?
3. Is this capability related to on-chain/crypto operations?

Respond in JSON format:
{{
    "gap_exists": true/false,
    "missing_capability": "description of what's missing",
    "is_on_chain": true/false,
    "priority": "high/medium/low"
}}
"""
        
        try:
            # Use Grok for skill generation (better reasoning)
            from grok_ai import grok_ai
            
            if grok_ai.enabled:
                response = grok_ai._make_api_request({
                    "model": grok_ai.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert Python programmer and AI agent developer. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                })
                
                if response and response.status_code == 200:
                    result = response.json()
                    # Grok /responses endpoint returns different format
                    if 'output' in result:
                        output = result['output']
                        response_text = output.strip() if isinstance(output, str) else str(output)
                    elif 'choices' in result:
                        response_text = result['choices'][0]['message']['content'].strip()
                    else:
                        response_text = str(result)
                else:
                    raise Exception(f"Grok API error: {response.status_code if response else 'No response'}")
            else:
                # Fallback to DeepSeek
                response = self.llm.invoke(prompt)
                response_text = response
            
            # Parse JSON response
            # Ensure response_text is a string
            if isinstance(response_text, list):
                response_text = str(response_text)
            elif not isinstance(response_text, str):
                response_text = str(response_text)
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    gap_info = json.loads(json_match.group())
                    
                    if gap_info.get('gap_exists'):
                        return gap_info.get('missing_capability')
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parsing error: {e}")
                    print(f"⚠️  Raw response: {response_text[:200]}...")
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error identifying capability gap: {e}")
            return None
    
    def generate_skill_code(self, capability_description: str, 
                           is_on_chain: bool = False) -> Optional[str]:
        """
        Generate Python code for a new skill
        
        Args:
            capability_description: What the skill should do
            is_on_chain: Whether this is an on-chain skill
            
        Returns:
            Generated Python code, or None if generation failed
        """
        on_chain_context = ""
        if is_on_chain:
            on_chain_context = """
This is an ON-CHAIN skill. Include:
- Web3 integration for blockchain interactions
- Safe transaction handling with gas estimation
- Error handling for network issues
- Proper address validation
- Use Base network (Chain ID: 8453) by default
"""
        
        prompt = f"""Generate a Python function for this capability:

{capability_description}

{on_chain_context}

Requirements:
1. Function should be self-contained and well-documented
2. Include type hints
3. Handle errors gracefully
4. Return structured results (dict or dataclass)
5. NO dangerous operations (os.system, eval, exec, etc.)
6. Only use allowlisted imports: json, time, datetime, requests, web3, base64, hashlib
7. Include a test function to verify the skill works

Format:
```python
from typing import Dict, Any
import json

def skill_name(param1: str, param2: int = 0) -> Dict[str, Any]:
    \"\"\"
    Description of what this skill does
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Dict with result data
    \"\"\"
    try:
        # Implementation
        result = {{'success': True, 'data': None}}
        return result
    except Exception as e:
        return {{'success': False, 'error': str(e)}}

def test_skill_name():
    \"\"\"Test the skill\"\"\"
    result = skill_name("test_input")
    assert result['success'], f"Skill failed: {{result.get('error')}}"
    print("✅ Skill test passed")

if __name__ == "__main__":
    test_skill_name()
```

Generate the complete code:
"""
        
        try:
            # Use Grok for skill code generation (better reasoning)
            from grok_ai import grok_ai
            
            if grok_ai.enabled:
                response = grok_ai._make_api_request({
                    "model": grok_ai.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert Python programmer. Generate complete, working code with proper syntax."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                })
                
                if response and response.status_code == 200:
                    result = response.json()
                    # Grok /responses endpoint returns different format
                    if 'output' in result:
                        output = result['output']
                        response_text = output.strip() if isinstance(output, str) else str(output)
                    elif 'choices' in result:
                        response_text = result['choices'][0]['message']['content'].strip()
                    else:
                        response_text = str(result)
                else:
                    raise Exception(f"Grok API error: {response.status_code if response else 'No response'}")
            else:
                # Fallback to DeepSeek
                response = self.llm.invoke(prompt)
                response_text = response
            
            # Ensure response_text is a string
            if isinstance(response_text, list):
                response_text = str(response_text)
            elif not isinstance(response_text, str):
                response_text = str(response_text)
            
            # Extract code from response
            code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                return code
            
            # If no code block, try to use entire response
            if 'def ' in response_text:
                return response_text
            
            return None
            
        except Exception as e:
            print(f"❌ Error generating skill code: {e}")
            return None
    
    def test_skill_in_sandbox(self, code: str) -> Dict[str, Any]:
        """
        Test generated skill in sandbox
        
        Args:
            code: The skill code to test
            
        Returns:
            Test results
        """
        print("🧪 Testing skill in sandbox...")
        
        # Validate code first
        validation = self.validator.validate_code(code)
        if not validation['safe']:
            return {
                'success': False,
                'error': 'Security validation failed',
                'issues': validation['issues']
            }
        
        # Execute in sandbox
        result = self.sandbox.execute_in_sandbox(code)
        
        if result['success']:
            print("✅ Skill test passed in sandbox")
        else:
            print(f"❌ Skill test failed: {result.get('error')}")
        
        return result
    
    def register_skill(self, skill_name: str, code: str, 
                      description: str, metadata: Dict[str, Any]) -> bool:
        """
        Register a new skill in the dynamic skills directory
        
        Args:
            skill_name: Name of the skill
            code: The skill code
            description: What the skill does
            metadata: Additional metadata
            
        Returns:
            True if registered successfully
        """
        try:
            # Create skill file
            skill_file = self.skills_dir / f"{skill_name}.py"
            with open(skill_file, 'w') as f:
                f.write(code)
            
            # Create skill.md
            skill_md = self.skills_dir / f"{skill_name}_SKILL.md"
            skill_md_content = f"""---
name: {skill_name}
description: {description}
generated: true
timestamp: {datetime.now().isoformat()}
---

# {skill_name}

{description}

## Metadata
{json.dumps(metadata, indent=2)}

## Usage

```python
from dynamic_skills.{skill_name} import {skill_name}

result = {skill_name}(...)
```

## Security
- Validated with security checks
- Tested in sandbox environment
- Safe for autonomous execution
"""
            
            with open(skill_md, 'w') as f:
                f.write(skill_md_content)
            
            # Add to registry
            self.skill_registry[skill_name] = {
                'file': str(skill_file),
                'description': description,
                'metadata': metadata,
                'created': datetime.now().isoformat()
            }
            
            # Save registry
            registry_file = self.skills_dir / 'registry.json'
            with open(registry_file, 'w') as f:
                json.dump(self.skill_registry, f, indent=2)
            
            print(f"✅ Skill registered: {skill_name}")
            return True
        except Exception as e:
            print(f"❌ Error registering skill: {e}")
            return False
    
    def generate_and_register_skill(self, capability_description: str,
                                   skill_name: str,
                                   is_on_chain: bool = False) -> Dict[str, Any]:
        """
        Complete workflow: generate, test, and register a new skill
        
        Args:
            capability_description: What the skill should do
            skill_name: Name for the skill
            is_on_chain: Whether this is an on-chain skill
            
        Returns:
            Result dict with success status and details
        """
        print(f"🔧 Generating skill: {skill_name}")
        print(f"📝 Capability: {capability_description}")
        
        # Generate code
        code = self.generate_skill_code(capability_description, is_on_chain)
        if not code:
            import logging
            logging.error("Failed to generate skill code", exc_info=True)
            print("❌ Failed to generate skill code")
            return {
                'success': False,
                'error': 'Failed to generate skill code'
            }
        
        print("✅ Code generated")
        
        # Test in sandbox
        test_result = self.test_skill_in_sandbox(code)
        if not test_result['success']:
            import logging
            logging.error(f"Skill failed sandbox testing: {test_result.get('error', 'Unknown error')}", exc_info=True)
            print(f"❌ Skill failed sandbox testing: {test_result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': 'Skill failed sandbox testing',
                'test_result': test_result
            }
        
        print("✅ Sandbox test passed")
        
        # Register skill
        metadata = {
            'is_on_chain': is_on_chain,
            'capability': capability_description,
            'test_result': test_result
        }
        
        registered = self.register_skill(skill_name, code, capability_description, metadata)
        
        if registered:
            self.generated_skills.append(skill_name)
            print(f"✅ Skill '{skill_name}' registered successfully")
            return {
                'success': True,
                'skill_name': skill_name,
                'file': str(self.skills_dir / f"{skill_name}.py")
            }
        else:
            import logging
            logging.error("Failed to register skill", exc_info=True)
            print("❌ Failed to register skill")
            return {
                'success': False,
                'error': 'Failed to register skill'
            }
    
    def load_dynamic_skills(self) -> List[str]:
        """Load all dynamic skills from the skills directory"""
        loaded_skills = []
        
        try:
            # Read registry
            registry_file = self.skills_dir / 'registry.json'
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    self.skill_registry = json.load(f)
                
                loaded_skills = list(self.skill_registry.keys())
                print(f"✅ Loaded {len(loaded_skills)} dynamic skills")
            
        except Exception as e:
            print(f"⚠️  Error loading dynamic skills: {e}")
        
        return loaded_skills
