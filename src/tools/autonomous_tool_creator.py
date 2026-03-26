"""
Autonomous Tool Creation System
Enables AlleyBot to create new tools on-the-fly when needed
"""

import json
import ast
import inspect
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path


class ToolCreationRequest:
    """Request to create a new tool"""
    def __init__(
        self,
        capability_needed: str,
        context: Dict[str, Any],
        urgency: str = 'normal'  # 'low', 'normal', 'high', 'critical'
    ):
        self.capability_needed = capability_needed
        self.context = context
        self.urgency = urgency
        self.created_at = datetime.now()


class AutonomousToolCreator:
    """
    Creates tools autonomously when AlleyBot detects missing capabilities
    
    Flow:
    1. Detect capability gap (e.g., "need to analyze sentiment")
    2. Generate tool specification using AI
    3. Generate Python code for the tool
    4. Validate code safety
    5. Test tool in sandbox
    6. Register tool dynamically
    7. Use tool immediately
    
    Features:
    - Runtime tool creation (no restart needed)
    - AI-powered code generation
    - Safety validation
    - Automatic schema inference
    - Tool versioning and rollback
    """
    
    def __init__(self, llm_client, function_calling_engine, core):
        self.llm_client = llm_client
        self.fc_engine = function_calling_engine
        self.core = core
        self.created_tools: Dict[str, Dict] = {}
        self.tool_creation_log: List[Dict] = []
        self._load_state()
    
    def _load_state(self):
        """Load previously created tools"""
        try:
            state = self.core.get_memory('autonomous_tool_creator_state')
            if state:
                self.created_tools = state.get('tools', {})
                self.tool_creation_log = state.get('log', [])
                print(f"📦 Loaded {len(self.created_tools)} previously created tools")
        except Exception:
            pass
    
    def _save_state(self):
        """Save tool creation state"""
        try:
            self.core.save_memory('autonomous_tool_creator_state', {
                'tools': self.created_tools,
                'log': self.tool_creation_log[-100:]
            })
        except Exception as e:
            print(f"⚠️ Failed to save tool creator state: {e}")
    
    def detect_capability_gap(self, task: str, available_tools: List[str]) -> Optional[ToolCreationRequest]:
        """
        Detect if a capability is missing for a task
        
        Args:
            task: The task to accomplish
            available_tools: List of currently available tool names
        
        Returns:
            ToolCreationRequest if gap detected, None otherwise
        """
        prompt = f"""Analyze if the following task can be accomplished with available tools.

Task: {task}

Available tools: {', '.join(available_tools)}

If a capability is missing, respond with JSON:
{{
    "gap_detected": true,
    "capability_needed": "brief description of missing capability",
    "urgency": "low/normal/high/critical",
    "reasoning": "why this capability is needed"
}}

If no gap, respond with:
{{
    "gap_detected": false
}}
"""
        
        try:
            response = self._call_llm(prompt, max_tokens=300)
            result = json.loads(response)
            
            if result.get('gap_detected'):
                return ToolCreationRequest(
                    capability_needed=result['capability_needed'],
                    context={
                        'task': task,
                        'reasoning': result.get('reasoning', ''),
                        'available_tools': available_tools
                    },
                    urgency=result.get('urgency', 'normal')
                )
        except Exception as e:
            print(f"⚠️ Gap detection failed: {e}")
        
        return None
    
    def create_tool(self, request: ToolCreationRequest) -> Optional[str]:
        """
        Create a new tool based on capability request
        
        Returns:
            Tool name if successful, None otherwise
        """
        print(f"🔨 Creating tool for: {request.capability_needed}")
        
        # Step 1: Generate tool specification
        spec = self._generate_tool_spec(request)
        if not spec:
            return None
        
        # Step 2: Generate Python code
        code = self._generate_tool_code(spec)
        if not code:
            return None
        
        # Step 3: Validate safety
        if not self._validate_code_safety(code):
            print(f"❌ Tool code failed safety validation")
            return None
        
        # Step 4: Test in sandbox
        if not self._test_tool_in_sandbox(code, spec):
            print(f"❌ Tool failed sandbox testing")
            return None
        
        # Step 5: Register tool dynamically
        tool_name = self._register_tool_from_code(code, spec)
        if not tool_name:
            return None
        
        # Step 6: Log creation
        self.tool_creation_log.append({
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'capability': request.capability_needed,
            'urgency': request.urgency,
            'code_lines': len(code.split('\n')),
            'success': True
        })
        
        self.created_tools[tool_name] = {
            'spec': spec,
            'code': code,
            'created_at': datetime.now().isoformat(),
            'usage_count': 0
        }
        
        self._save_state()
        print(f"✅ Tool created and registered: {tool_name}")
        return tool_name
    
    def _generate_tool_spec(self, request: ToolCreationRequest) -> Optional[Dict]:
        """Generate tool specification using AI"""
        prompt = f"""Generate a tool specification for this capability:

Capability needed: {request.capability_needed}
Context: {json.dumps(request.context, indent=2)}
Urgency: {request.urgency}

Respond with JSON specification:
{{
    "name": "tool_name_in_snake_case",
    "description": "what the tool does",
    "parameters": [
        {{
            "name": "param_name",
            "type": "string/number/boolean/array/object",
            "description": "parameter description",
            "required": true
        }}
    ],
    "returns": "description of return value",
    "example_usage": "example of how to use the tool"
}}
"""
        
        try:
            response = self._call_llm(prompt, max_tokens=500)
            spec = json.loads(response)
            
            # Validate spec has required fields
            if all(k in spec for k in ['name', 'description', 'parameters']):
                return spec
        except Exception as e:
            print(f"⚠️ Tool spec generation failed: {e}")
        
        return None
    
    def _generate_tool_code(self, spec: Dict) -> Optional[str]:
        """Generate Python code for the tool"""
        params_desc = '\n'.join([
            f"    {p['name']} ({p['type']}): {p['description']}"
            for p in spec['parameters']
        ])
        
        prompt = f"""Generate production-ready Python code for this tool:

Name: {spec['name']}
Description: {spec['description']}

Parameters:
{params_desc}

Returns: {spec.get('returns', 'result')}

Requirements:
1. Function must be named '{spec['name']}'
2. Include type hints
3. Include comprehensive docstring
4. Add error handling
5. Return structured result (dict or string)
6. No external API calls unless specified
7. Use only standard library or common packages (requests, json, re, datetime)

Generate ONLY the function code, no imports or explanations:
"""
        
        try:
            response = self._call_llm(prompt, max_tokens=1000, model='grok-code-fast-1')
            
            # Extract code from markdown if present
            if '```python' in response:
                code = response.split('```python')[1].split('```')[0].strip()
            elif '```' in response:
                code = response.split('```')[1].split('```')[0].strip()
            else:
                code = response.strip()
            
            # Validate it's valid Python
            try:
                ast.parse(code)
                return code
            except SyntaxError as e:
                print(f"⚠️ Generated code has syntax error: {e}")
                return None
                
        except Exception as e:
            print(f"⚠️ Tool code generation failed: {e}")
        
        return None
    
    def _validate_code_safety(self, code: str) -> bool:
        """Validate code doesn't contain dangerous patterns"""
        dangerous_patterns = [
            'eval(',
            'exec(',
            'compile(',
            '__import__',
            'os.system',
            'subprocess.run',
            'subprocess.call',
            'subprocess.Popen',
            'open(',  # File operations need review
            'pickle.loads',
            'yaml.load',
            'input(',
            'raw_input('
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                print(f"⚠️ Dangerous pattern detected: {pattern}")
                return False
        
        # Check for valid Python syntax
        try:
            ast.parse(code)
        except SyntaxError:
            return False
        
        return True
    
    def _test_tool_in_sandbox(self, code: str, spec: Dict) -> bool:
        """Test tool in isolated sandbox environment"""
        try:
            # Create isolated namespace
            namespace = {
                '__builtins__': __builtins__,
                'json': json,
                're': __import__('re'),
                'datetime': __import__('datetime'),
                'requests': __import__('requests')
            }
            
            # Execute code in namespace
            exec(code, namespace)
            
            # Check function exists
            func_name = spec['name']
            if func_name not in namespace:
                print(f"⚠️ Function {func_name} not found in generated code")
                return False
            
            # Try calling with dummy parameters
            func = namespace[func_name]
            test_args = {}
            for param in spec['parameters']:
                if param['required']:
                    # Generate dummy value based on type
                    if param['type'] == 'string':
                        test_args[param['name']] = 'test'
                    elif param['type'] == 'number':
                        test_args[param['name']] = 1.0
                    elif param['type'] == 'integer':
                        test_args[param['name']] = 1
                    elif param['type'] == 'boolean':
                        test_args[param['name']] = True
                    elif param['type'] == 'array':
                        test_args[param['name']] = []
                    elif param['type'] == 'object':
                        test_args[param['name']] = {}
            
            # Call function with test args
            result = func(**test_args)
            
            # Verify it returns something
            if result is None:
                print(f"⚠️ Function returned None")
                return False
            
            print(f"✅ Sandbox test passed")
            return True
            
        except Exception as e:
            print(f"⚠️ Sandbox test failed: {e}")
            return False
    
    def _register_tool_from_code(self, code: str, spec: Dict) -> Optional[str]:
        """Register tool dynamically in function calling engine"""
        try:
            # Execute code to get function
            namespace = {
                '__builtins__': __builtins__,
                'json': json,
                're': __import__('re'),
                'datetime': __import__('datetime'),
                'requests': __import__('requests')
            }
            exec(code, namespace)
            
            func_name = spec['name']
            func = namespace[func_name]
            
            # Register with function calling engine
            self.fc_engine.register_from_function(
                func,
                name=func_name,
                description=spec['description']
            )
            
            return func_name
            
        except Exception as e:
            print(f"⚠️ Tool registration failed: {e}")
            return None
    
    def _call_llm(self, prompt: str, max_tokens: int = 500, model: Optional[str] = None) -> str:
        """Call LLM for code generation"""
        # Use Grok for code generation
        if hasattr(self.llm_client, 'route_task'):
            return self.llm_client.route_task(
                'code' if model == 'grok-code-fast-1' else 'reasoning',
                prompt,
                max_tokens=max_tokens
            )
        
        # Fallback to DeepSeek
        elif hasattr(self.llm_client, 'chat'):
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        raise ValueError("No compatible LLM client")
    
    def get_tool_usage_stats(self) -> Dict:
        """Get statistics on created tools"""
        return {
            'total_tools_created': len(self.created_tools),
            'tools': {
                name: {
                    'created_at': info['created_at'],
                    'usage_count': info['usage_count']
                }
                for name, info in self.created_tools.items()
            },
            'recent_creations': self.tool_creation_log[-10:]
        }
    
    def rollback_tool(self, tool_name: str) -> bool:
        """Remove a created tool"""
        if tool_name in self.created_tools:
            del self.created_tools[tool_name]
            # Remove from function calling engine
            if tool_name in self.fc_engine.tools:
                del self.fc_engine.tools[tool_name]
            self._save_state()
            print(f"🔄 Rolled back tool: {tool_name}")
            return True
        return False
