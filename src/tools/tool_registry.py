"""
Tool Registry for AlleyBot

Manages registration and execution of all tools including:
- Hermes-style tools
- Original AlleyBot plugins
- Skills
- External integrations

Provides unified interface for tool discovery and execution.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from pathlib import Path

from src.tools.hermes_style_tools import (
    execute_hermes_tool, 
    HERMES_TOOLS,
    HermesToolPlugin
)


class ToolCategory(Enum):
    """Categories of tools"""
    WEB = "web"
    TERMINAL = "terminal"
    FILE = "file"
    BROWSER = "browser"
    VISION = "vision"
    CODE = "code"
    TODO = "todo"
    MEMORY = "memory"
    MESSAGING = "messaging"
    TRADING = "trading"
    SOCIAL = "social"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class ToolDefinition:
    """Definition of a tool"""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    enabled: bool = True
    plugin_name: Optional[str] = None
    skill_path: Optional[str] = None
    hermes_tool: bool = False


@dataclass
class ToolExecution:
    """Tool execution request and result"""
    tool_name: str
    method: str
    params: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """Central registry for all AlleyBot tools"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.tool_categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        self.plugin_manager = None
        self.skill_executor = None
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in Hermes-style tools"""
        
        # Web tools
        self.register_tool(
            ToolDefinition(
                name="web_search",
                category=ToolCategory.WEB,
                description="Search the web for information",
                parameters={
                    "query": {"type": "string", "required": True},
                    "max_results": {"type": "integer", "default": 10}
                },
                examples=["web_search(query='Python async programming')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="web_extract",
                category=ToolCategory.WEB,
                description="Extract content from web pages",
                parameters={
                    "url": {"type": "string", "required": True},
                    "selector": {"type": "string", "optional": True}
                },
                examples=["web_extract(url='https://example.com')"],
                hermes_tool=True
            )
        )
        
        # Terminal tools
        self.register_tool(
            ToolDefinition(
                name="terminal",
                category=ToolCategory.TERMINAL,
                description="Execute terminal commands",
                parameters={
                    "command": {"type": "string", "required": True},
                    "cwd": {"type": "string", "optional": True},
                    "backend": {"type": "string", "default": "local", "options": ["local", "docker", "ssh"]}
                },
                examples=["terminal(command='ls -la')"],
                hermes_tool=True
            )
        )
        
        # File tools
        self.register_tool(
            ToolDefinition(
                name="read_file",
                category=ToolCategory.FILE,
                description="Read file contents",
                parameters={
                    "path": {"type": "string", "required": True},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "optional": True}
                },
                examples=["read_file(path='config.json')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="write_file",
                category=ToolCategory.FILE,
                description="Write content to file",
                parameters={
                    "path": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True},
                    "create_dirs": {"type": "boolean", "default": True}
                },
                examples=["write_file(path='output.txt', content='Hello World')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="patch",
                category=ToolCategory.FILE,
                description="Apply patch to file (find and replace)",
                parameters={
                    "file_path": {"type": "string", "required": True},
                    "old_string": {"type": "string", "required": True},
                    "new_string": {"type": "string", "required": True}
                },
                examples=["patch(file_path='app.py', old_string='old', new_string='new')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="search_files",
                category=ToolCategory.FILE,
                description="Search for files matching pattern",
                parameters={
                    "pattern": {"type": "string", "required": True},
                    "directory": {"type": "string", "default": "."},
                    "file_types": {"type": "array", "optional": True}
                },
                examples=["search_files(pattern='*.py', directory='src')"],
                hermes_tool=True
            )
        )
        
        # Browser tools
        self.register_tool(
            ToolDefinition(
                name="browser_navigate",
                category=ToolCategory.BROWSER,
                description="Navigate browser to URL",
                parameters={
                    "url": {"type": "string", "required": True}
                },
                examples=["browser_navigate(url='https://example.com')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="browser_snapshot",
                category=ToolCategory.BROWSER,
                description="Take screenshot of current page",
                parameters={},
                examples=["browser_snapshot()"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="browser_click",
                category=ToolCategory.BROWSER,
                description="Click element on page",
                parameters={
                    "selector": {"type": "string", "required": True}
                },
                examples=["browser_click(selector='#submit-btn')"],
                hermes_tool=True
            )
        )
        
        self.register_tool(
            ToolDefinition(
                name="browser_vision",
                category=ToolCategory.BROWSER,
                description="Analyze page content with vision",
                parameters={
                    "question": {"type": "string", "required": True}
                },
                examples=["browser_vision(question='Is there a login form?')"],
                hermes_tool=True
            )
        )
        
        # Vision tools
        self.register_tool(
            ToolDefinition(
                name="vision_analyze",
                category=ToolCategory.VISION,
                description="Analyze image with vision model",
                parameters={
                    "image_path": {"type": "string", "required": True},
                    "question": {"type": "string", "required": True}
                },
                examples=["vision_analyze(image_path='screenshot.png', question='What is in this image?')"],
                hermes_tool=True
            )
        )
        
        # Code execution tools
        self.register_tool(
            ToolDefinition(
                name="execute_code",
                category=ToolCategory.CODE,
                description="Execute code in specified language",
                parameters={
                    "code": {"type": "string", "required": True},
                    "language": {"type": "string", "default": "python", "options": ["python", "javascript", "bash"]}
                },
                examples=["execute_code(code='print(\"Hello\")', language='python')"],
                hermes_tool=True
            )
        )
        
        # Todo tools
        self.register_tool(
            ToolDefinition(
                name="todo",
                category=ToolCategory.TODO,
                description="Manage todo items",
                parameters={
                    "action": {"type": "string", "required": True, "options": ["list", "add", "complete", "delete"]},
                    "task": {"type": "string", "optional": True},
                    "todo_id": {"type": "string", "optional": True}
                },
                examples=["todo(action='add', task='Build new feature')"],
                hermes_tool=True
            )
        )
    
    def register_tool(self, tool: ToolDefinition):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool
        self.tool_categories[tool.category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None, enabled_only: bool = True) -> List[ToolDefinition]:
        """List tools, optionally filtered by category"""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return tools
    
    def search_tools(self, query: str) -> List[ToolDefinition]:
        """Search tools by name, description, or examples"""
        query = query.lower()
        results = []
        
        for tool in self.tools.values():
            if (query in tool.name.lower() or 
                query in tool.description.lower() or
                any(query in example.lower() for example in tool.examples)):
                results.append(tool)
        
        return results
    
    async def execute_tool(self, execution: ToolExecution) -> ToolExecution:
        """Execute a tool"""
        import time
        start_time = time.time()
        
        try:
            tool_def = self.get_tool(execution.tool_name)
            if not tool_def:
                execution.success = False
                execution.error = f"Tool not found: {execution.tool_name}"
                return execution
            
            if not tool_def.enabled:
                execution.success = False
                execution.error = f"Tool disabled: {execution.tool_name}"
                return execution
            
            # Route execution based on tool type
            if tool_def.hermes_tool:
                result = await execute_hermes_tool(
                    execution.tool_name,
                    execution.method,
                    **execution.params
                )
                execution.result = result.data
                execution.success = result.success
                execution.error = result.error
                execution.metadata = result.metadata or {}
            
            elif tool_def.plugin_name and self.plugin_manager:
                # Execute via plugin manager
                plugin = self.plugin_manager.plugins.get(tool_def.plugin_name)
                if plugin:
                    method = getattr(plugin, execution.method, None)
                    if method:
                        if asyncio.iscoroutinefunction(method):
                            execution.result = await method(**execution.params)
                        else:
                            execution.result = method(**execution.params)
                        execution.success = True
                    else:
                        execution.success = False
                        execution.error = f"Method not found: {execution.method}"
                else:
                    execution.success = False
                    execution.error = f"Plugin not found: {tool_def.plugin_name}"
            
            elif tool_def.skill_path and self.skill_executor:
                # Execute via skill executor
                execution.result = await self.skill_executor.execute_skill(
                    tool_def.skill_path,
                    execution.method,
                    **execution.params
                )
                execution.success = True
            
            else:
                execution.success = False
                execution.error = f"No execution handler for tool: {execution.tool_name}"
        
        except Exception as e:
            execution.success = False
            execution.error = str(e)
        
        execution.execution_time = time.time() - start_time
        return execution
    
    def set_plugin_manager(self, plugin_manager):
        """Set plugin manager for plugin tool execution"""
        self.plugin_manager = plugin_manager
    
    def set_skill_executor(self, skill_executor):
        """Set skill executor for skill tool execution"""
        self.skill_executor = skill_executor
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tools"""
        stats = {
            'total_tools': len(self.tools),
            'enabled_tools': len([t for t in self.tools.values() if t.enabled]),
            'categories': {},
            'hermes_tools': len([t for t in self.tools.values() if t.hermes_tool]),
            'plugin_tools': len([t for t in self.tools.values() if t.plugin_name]),
            'skill_tools': len([t for t in self.tools.values() if t.skill_path])
        }
        
        for category in ToolCategory:
            tools = self.tool_categories[category]
            stats['categories'][category.value] = {
                'total': len(tools),
                'enabled': len([t for t in tools if self.tools[t].enabled])
            }
        
        return stats
    
    def export_definitions(self, file_path: str):
        """Export tool definitions to JSON file"""
        definitions = {}
        for name, tool in self.tools.items():
            definitions[name] = {
                'category': tool.category.value,
                'description': tool.description,
                'parameters': tool.parameters,
                'examples': tool.examples,
                'enabled': tool.enabled,
                'plugin_name': tool.plugin_name,
                'skill_path': tool.skill_path,
                'hermes_tool': tool.hermes_tool
            }
        
        with open(file_path, 'w') as f:
            json.dump(definitions, f, indent=2)
    
    def import_definitions(self, file_path: str):
        """Import tool definitions from JSON file"""
        with open(file_path, 'r') as f:
            definitions = json.load(f)
        
        for name, def_data in definitions.items():
            tool = ToolDefinition(
                name=name,
                category=ToolCategory(def_data['category']),
                description=def_data['description'],
                parameters=def_data.get('parameters', {}),
                examples=def_data.get('examples', []),
                enabled=def_data.get('enabled', True),
                plugin_name=def_data.get('plugin_name'),
                skill_path=def_data.get('skill_path'),
                hermes_tool=def_data.get('hermes_tool', False)
            )
            self.register_tool(tool)


# Global registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


# Integration with AlleyBot
async def execute_tool_action(tool_name: str, method: str = None, **params) -> Dict[str, Any]:
    """Execute tool action through registry"""
    registry = get_tool_registry()
    
    execution = ToolExecution(
        tool_name=tool_name,
        method=method or tool_name,
        params=params
    )
    
    result = await registry.execute_tool(execution)
    
    return {
        'success': result.success,
        'result': result.result,
        'error': result.error,
        'execution_time': result.execution_time,
        'metadata': result.metadata
    }


# Tool discovery for AI
def discover_tools_for_task(task_description: str, max_tools: int = 5) -> List[ToolDefinition]:
    """Discover relevant tools for a task"""
    registry = get_tool_registry()
    
    # Search for matching tools
    matching_tools = registry.search_tools(task_description)
    
    # Sort by relevance (simple heuristic)
    matching_tools.sort(key=lambda t: (
        task_description.lower() in t.name.lower(),
        task_description.lower() in t.description.lower()
    ), reverse=True)
    
    return matching_tools[:max_tools]
