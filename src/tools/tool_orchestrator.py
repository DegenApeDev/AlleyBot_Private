"""
Tool Orchestrator - High-Level Tool Use Coordinator
Integrates function calling, autonomous tool creation, and existing plugins
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ToolOrchestrator:
    """
    Orchestrates all tool capabilities:
    - Native function calling (DeepSeek/Grok)
    - Autonomous tool creation
    - MCP server tools
    - Plugin commands
    - Dynamic tool discovery
    
    Provides unified interface for super high-level tool use
    """
    
    def __init__(self, core, llm_client):
        self.core = core
        self.llm_client = llm_client
        
        # Initialize components
        from src.tools.function_calling import FunctionCallingEngine
        from src.tools.autonomous_tool_creator import AutonomousToolCreator
        
        self.fc_engine = FunctionCallingEngine(llm_client)
        self.tool_creator = AutonomousToolCreator(llm_client, self.fc_engine, core)
        
        # Tool registries
        self.plugin_tools: Dict[str, Any] = {}
        self.mcp_tools: Dict[str, Any] = {}
        
        # Initialize with existing capabilities
        self._discover_plugin_tools()
        self._discover_mcp_tools()
        
        print(f"🎯 Tool Orchestrator initialized")
        print(f"   Function calling: {len(self.fc_engine.tools)} tools")
        print(f"   Plugin commands: {len(self.plugin_tools)} tools")
        print(f"   MCP tools: {len(self.mcp_tools)} tools")
    
    def _discover_plugin_tools(self):
        """Discover and register tools from plugins"""
        if not hasattr(self.core, 'plugin_manager'):
            return
        
        for plugin_name, plugin in self.core.plugin_manager.plugins.items():
            if hasattr(plugin, 'get_commands'):
                commands = plugin.get_commands()
                for cmd_name, cmd_func in commands.items():
                    tool_key = f"{plugin_name}_{cmd_name}"
                    self.plugin_tools[tool_key] = {
                        'plugin': plugin_name,
                        'command': cmd_name,
                        'function': cmd_func,
                        'type': 'plugin'
                    }
                    
                    # Auto-register with function calling engine
                    try:
                        self.fc_engine.register_from_function(
                            cmd_func,
                            name=tool_key,
                            description=f"{plugin_name} plugin: {cmd_name}"
                        )
                    except Exception as e:
                        # Skip if registration fails
                        pass
    
    def _discover_mcp_tools(self):
        """Discover tools from MCP servers"""
        try:
            # Check if core and plugin_manager exist
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                return
            
            if not self.core.plugin_manager:
                return
            
            mcp_plugin = self.core.plugin_manager.plugins.get('mcp')
            if mcp_plugin and hasattr(mcp_plugin, 'server_manager'):
                for server_name, capabilities in mcp_plugin.server_manager.dynamic_capabilities.items():
                    tool_key = f"mcp_{capabilities['name']}"
                    self.mcp_tools[tool_key] = {
                        'server': server_name,
                        'capability': capabilities,
                        'type': 'mcp'
                    }
        except Exception as e:
            print(f"⚠️ MCP tool discovery failed: {e}")
    
    def execute_task_with_tools(
        self,
        task: str,
        context: Optional[Dict] = None,
        max_iterations: int = 10,
        auto_create_tools: bool = True
    ) -> Dict:
        """
        Execute a task using all available tools
        
        Features:
        - Automatic tool selection
        - Parallel tool execution
        - Auto-create missing tools
        - Error recovery
        
        Args:
            task: Task description
            context: Additional context
            max_iterations: Max reasoning iterations
            auto_create_tools: Create tools if capability missing
        
        Returns:
            Execution result with tool usage history
        """
        print(f"🎯 Executing task: {task}")
        
        context = context or {}
        messages = [
            {
                "role": "system",
                "content": """You are AlleyBot, an AGI agent with advanced tool use capabilities.
You can use any available tool to accomplish tasks. If a tool is missing, request it and it will be created.
Be efficient and use parallel tool calls when possible."""
            },
            {
                "role": "user",
                "content": f"Task: {task}\n\nContext: {json.dumps(context, indent=2)}"
            }
        ]
        
        # Check for capability gaps
        if auto_create_tools:
            available_tools = self.list_all_tools()
            gap = self.tool_creator.detect_capability_gap(task, available_tools)
            
            if gap:
                print(f"🔍 Capability gap detected: {gap.capability_needed}")
                tool_name = self.tool_creator.create_tool(gap)
                if tool_name:
                    print(f"✅ Created tool: {tool_name}")
                    messages.append({
                        "role": "system",
                        "content": f"New tool created: {tool_name} - {gap.capability_needed}"
                    })
        
        # Execute with function calling
        try:
            result = self.fc_engine.call_with_tools(
                messages,
                max_iterations=max_iterations,
                parallel=True
            )
            
            return {
                'success': True,
                'result': result.get('response', ''),
                'tool_calls': result.get('tool_calls', []),
                'iterations': result.get('iterations', 0),
                'tools_used': [tc['name'] for tc in result.get('tool_calls', [])]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool_calls': [],
                'iterations': 0
            }
    
    def call_tool_by_name(self, tool_name: str, **kwargs) -> Any:
        """
        Call a specific tool by name
        
        Searches across all tool sources:
        - Function calling tools
        - Plugin commands
        - MCP tools
        """
        # Check function calling tools
        if tool_name in self.fc_engine.tools:
            return self.fc_engine.tools[tool_name].execute(kwargs)
        
        # Check plugin tools
        if tool_name in self.plugin_tools:
            tool_info = self.plugin_tools[tool_name]
            return tool_info['function'](**kwargs)
        
        # Check MCP tools
        if tool_name in self.mcp_tools:
            tool_info = self.mcp_tools[tool_name]
            mcp_plugin = self.core.plugin_manager.plugins.get('mcp')
            if mcp_plugin:
                return mcp_plugin.server_manager.call_capability(
                    tool_info['capability']['name'],
                    **kwargs
                )
        
        return f"❌ Tool not found: {tool_name}"
    
    def list_all_tools(self) -> List[str]:
        """List all available tools across all sources"""
        tools = []
        tools.extend(self.fc_engine.list_tools())
        tools.extend(self.plugin_tools.keys())
        tools.extend(self.mcp_tools.keys())
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get detailed information about a tool"""
        # Function calling tool
        if tool_name in self.fc_engine.tools:
            tool = self.fc_engine.tools[tool_name]
            return {
                'name': tool.name,
                'description': tool.description,
                'type': 'function_calling',
                'schema': tool.to_openai_schema(),
                'parameters': [
                    {
                        'name': p.name,
                        'type': p.type.value,
                        'description': p.description,
                        'required': p.required
                    }
                    for p in tool.parameters
                ]
            }
        
        # Plugin tool
        if tool_name in self.plugin_tools:
            tool_info = self.plugin_tools[tool_name]
            return {
                'name': tool_name,
                'type': 'plugin',
                'plugin': tool_info['plugin'],
                'command': tool_info['command']
            }
        
        # MCP tool
        if tool_name in self.mcp_tools:
            tool_info = self.mcp_tools[tool_name]
            return {
                'name': tool_name,
                'type': 'mcp',
                'server': tool_info['server'],
                'capability': tool_info['capability']
            }
        
        return None
    
    def create_tool_on_demand(self, capability_description: str, urgency: str = 'normal') -> Optional[str]:
        """
        Create a tool on-demand for a specific capability
        
        Args:
            capability_description: What the tool should do
            urgency: Priority level
        
        Returns:
            Tool name if created successfully
        """
        from src.tools.autonomous_tool_creator import ToolCreationRequest
        
        request = ToolCreationRequest(
            capability_needed=capability_description,
            context={'on_demand': True},
            urgency=urgency
        )
        
        return self.tool_creator.create_tool(request)
    
    def get_tool_usage_stats(self) -> Dict:
        """Get comprehensive tool usage statistics"""
        return {
            'total_tools': len(self.list_all_tools()),
            'by_type': {
                'function_calling': len(self.fc_engine.tools),
                'plugin': len(self.plugin_tools),
                'mcp': len(self.mcp_tools)
            },
            'created_tools': self.tool_creator.get_tool_usage_stats(),
            'most_used': self._get_most_used_tools()
        }
    
    def _get_most_used_tools(self) -> List[Dict]:
        """Get most frequently used tools"""
        # This would track usage over time
        # For now, return empty list
        return []
    
    def suggest_tool_for_task(self, task: str) -> List[Dict]:
        """
        Suggest best tools for a given task using AI
        
        Returns:
            List of suggested tools with confidence scores
        """
        available_tools = self.list_all_tools()
        
        prompt = f"""Given this task and available tools, suggest the 3 best tools to use.

Task: {task}

Available tools: {', '.join(available_tools[:50])}  # Limit to avoid token overflow

Respond with JSON array:
[
    {{
        "tool_name": "exact_tool_name",
        "confidence": 0.9,
        "reasoning": "why this tool is suitable"
    }}
]
"""
        
        try:
            response = self.llm_client.route_task('reasoning', prompt, max_tokens=400)
            suggestions = json.loads(response)
            return suggestions
        except Exception as e:
            print(f"⚠️ Tool suggestion failed: {e}")
            return []
    
    def refresh_tool_discovery(self):
        """Re-discover all tools (useful after plugin updates)"""
        self.plugin_tools.clear()
        self.mcp_tools.clear()
        self._discover_plugin_tools()
        self._discover_mcp_tools()
        print(f"🔄 Tool discovery refreshed: {len(self.list_all_tools())} total tools")
