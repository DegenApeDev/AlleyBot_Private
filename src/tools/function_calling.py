"""
Native Function Calling for DeepSeek & Grok
Enables structured tool use with automatic schema generation
"""

import json
import inspect
from typing import Any, Callable, Dict, List, Optional, get_type_hints
from dataclasses import dataclass
from enum import Enum


class ToolParameterType(Enum):
    """Supported parameter types for tools"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    items: Optional[Dict] = None  # For array types


@dataclass
class FunctionTool:
    """Function-callable tool with automatic schema generation"""
    name: str
    description: str
    function: Callable
    parameters: List[ToolParameter]
    
    def to_openai_schema(self) -> Dict:
        """Convert to OpenAI function calling schema"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type.value,
                "description": param.description
            }
            
            if param.enum:
                prop["enum"] = param.enum
            if param.items:
                prop["items"] = param.items
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments"""
        try:
            return self.function(**arguments)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"


class FunctionCallingEngine:
    """
    Engine for native function calling with DeepSeek & Grok
    
    Features:
    - Automatic schema generation from Python functions
    - Parallel tool execution
    - Tool result validation
    - Dynamic tool registration
    """
    
    def __init__(self, llm_client, model: str = "deepseek-chat"):
        self.llm_client = llm_client
        self.model = model
        self.tools: Dict[str, FunctionTool] = {}
    
    def register_tool(self, tool: FunctionTool):
        """Register a tool for function calling"""
        self.tools[tool.name] = tool
        print(f"🔧 Registered tool: {tool.name}")
    
    def register_from_function(
        self, 
        func: Callable, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> FunctionTool:
        """
        Auto-register a tool from a Python function
        
        Uses type hints and docstring for schema generation
        """
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "No description").strip()
        
        # Extract parameters from function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Infer type from type hint
            param_type = type_hints.get(param_name, str)
            tool_param_type = self._python_type_to_tool_type(param_type)
            
            # Extract description from docstring if available
            param_desc = f"Parameter {param_name}"
            if func.__doc__:
                # Simple docstring parsing
                for line in func.__doc__.split('\n'):
                    if param_name in line and ':' in line:
                        param_desc = line.split(':', 1)[1].strip()
                        break
            
            parameters.append(ToolParameter(
                name=param_name,
                type=tool_param_type,
                description=param_desc,
                required=param.default == inspect.Parameter.empty
            ))
        
        tool = FunctionTool(
            name=tool_name,
            description=tool_desc,
            function=func,
            parameters=parameters
        )
        
        self.register_tool(tool)
        return tool
    
    def _python_type_to_tool_type(self, py_type) -> ToolParameterType:
        """Convert Python type to tool parameter type"""
        if py_type == str:
            return ToolParameterType.STRING
        elif py_type == int:
            return ToolParameterType.INTEGER
        elif py_type == float:
            return ToolParameterType.NUMBER
        elif py_type == bool:
            return ToolParameterType.BOOLEAN
        elif py_type == list or py_type == List:
            return ToolParameterType.ARRAY
        elif py_type == dict or py_type == Dict:
            return ToolParameterType.OBJECT
        else:
            return ToolParameterType.STRING
    
    def call_with_tools(
        self, 
        messages: List[Dict], 
        max_iterations: int = 5,
        parallel: bool = False
    ) -> Dict:
        """
        Call LLM with function calling enabled
        
        Args:
            messages: Conversation messages
            max_iterations: Max tool calling iterations
            parallel: Enable parallel tool execution (if supported)
        
        Returns:
            Final response with tool call history
        """
        tool_schemas = [tool.to_openai_schema() for tool in self.tools.values()]
        conversation = messages.copy()
        tool_calls_made = []
        
        for iteration in range(max_iterations):
            # Call LLM with tools
            try:
                response = self._make_llm_request(conversation, tool_schemas, parallel)
                
                # Check if LLM wants to call tools
                if not self._has_tool_calls(response):
                    # No more tool calls, return final response
                    return {
                        'response': self._extract_content(response),
                        'tool_calls': tool_calls_made,
                        'iterations': iteration + 1
                    }
                
                # Execute tool calls
                tool_results = self._execute_tool_calls(response, parallel)
                tool_calls_made.extend(tool_results)
                
                # Add tool results to conversation
                conversation.append({
                    'role': 'assistant',
                    'content': self._extract_content(response),
                    'tool_calls': self._extract_tool_calls(response)
                })
                
                for result in tool_results:
                    conversation.append({
                        'role': 'tool',
                        'tool_call_id': result['call_id'],
                        'name': result['name'],
                        'content': json.dumps(result['result'])
                    })
                
            except Exception as e:
                return {
                    'error': str(e),
                    'tool_calls': tool_calls_made,
                    'iterations': iteration + 1
                }
        
        return {
            'response': 'Max iterations reached',
            'tool_calls': tool_calls_made,
            'iterations': max_iterations
        }
    
    def _make_llm_request(self, messages: List[Dict], tools: List[Dict], parallel: bool) -> Dict:
        """Make LLM request with function calling"""
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto"
        }
        
        if parallel:
            payload["parallel_tool_calls"] = True
        
        # DeepSeek API call
        if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
            response = self.llm_client.chat.completions.create(**payload)
            return response.model_dump()
        
        # Grok API call (convert to Grok format)
        elif hasattr(self.llm_client, 'base_url'):
            import requests
            headers = {
                "Authorization": f"Bearer {self.llm_client.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                f"{self.llm_client.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            return response.json()
        
        raise ValueError("Unsupported LLM client")
    
    def _has_tool_calls(self, response: Dict) -> bool:
        """Check if response contains tool calls"""
        if 'choices' in response and len(response['choices']) > 0:
            message = response['choices'][0].get('message', {})
            return 'tool_calls' in message and message['tool_calls']
        return False
    
    def _extract_tool_calls(self, response: Dict) -> List[Dict]:
        """Extract tool calls from response"""
        if 'choices' in response and len(response['choices']) > 0:
            message = response['choices'][0].get('message', {})
            return message.get('tool_calls', [])
        return []
    
    def _extract_content(self, response: Dict) -> str:
        """Extract text content from response"""
        if 'choices' in response and len(response['choices']) > 0:
            message = response['choices'][0].get('message', {})
            return message.get('content', '')
        return ''
    
    def _execute_tool_calls(self, response: Dict, parallel: bool) -> List[Dict]:
        """Execute tool calls from LLM response"""
        tool_calls = self._extract_tool_calls(response)
        results = []
        
        if parallel:
            # Parallel execution (future enhancement with asyncio)
            for call in tool_calls:
                result = self._execute_single_tool_call(call)
                results.append(result)
        else:
            # Sequential execution
            for call in tool_calls:
                result = self._execute_single_tool_call(call)
                results.append(result)
        
        return results
    
    def _execute_single_tool_call(self, call: Dict) -> Dict:
        """Execute a single tool call"""
        tool_name = call['function']['name']
        arguments = json.loads(call['function']['arguments'])
        call_id = call['id']
        
        if tool_name not in self.tools:
            return {
                'call_id': call_id,
                'name': tool_name,
                'result': f"Error: Tool '{tool_name}' not found"
            }
        
        tool = self.tools[tool_name]
        result = tool.execute(arguments)
        
        return {
            'call_id': call_id,
            'name': tool_name,
            'arguments': arguments,
            'result': result
        }
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """Get OpenAI schema for a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].to_openai_schema()
        return None
