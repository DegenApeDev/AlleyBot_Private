"""
Tool Use Commands for AlleyBot Brain
Enables high-level tool use and autonomous tool creation
"""

from typing import Dict, Optional


class ToolCommandsMixin:
    """Commands for advanced tool use capabilities"""
    
    def _init_tool_commands(self):
        """Initialize tool orchestrator"""
        self.tool_orchestrator = None
        
        try:
            # Check if tool orchestrator module exists
            import os
            tool_orchestrator_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'src', 'tools', 'tool_orchestrator.py'
            )
            
            if not os.path.exists(tool_orchestrator_path):
                print("ℹ️  Tool orchestrator not available (module not found)")
                return
            
            from src.tools.tool_orchestrator import ToolOrchestrator
            from grok_ai import grok_ai
            
            # Use Grok for tool operations (better at code generation)
            llm_client = grok_ai if grok_ai.enabled else None
            
            if llm_client:
                self.tool_orchestrator = ToolOrchestrator(self.core, llm_client)
                print("🎯 Tool orchestrator ready")
            else:
                print("ℹ️  Tool orchestrator disabled (no LLM client)")
        except ImportError as e:
            print(f"ℹ️  Tool orchestrator not available: {e}")
        except Exception as e:
            print(f"⚠️  Tool orchestrator init failed: {e}")
            import traceback
            traceback.print_exc()
    
    def tools_list_command(self, args: str = "") -> str:
        """
        List all available tools
        
        Usage: /tools_list [type]
        Types: all, function, plugin, mcp, created
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        tool_type = args.strip().lower() or "all"
        
        try:
            if tool_type == "all":
                tools = self.tool_orchestrator.list_all_tools()
                stats = self.tool_orchestrator.get_tool_usage_stats()
                
                return f"""🔧 **Available Tools** ({len(tools)} total)

**By Type:**
- Function Calling: {stats['by_type']['function_calling']}
- Plugin Commands: {stats['by_type']['plugin']}
- MCP Tools: {stats['by_type']['mcp']}
- Created Tools: {stats['created_tools']['total_tools_created']}

**All Tools:**
{chr(10).join(f"  • {tool}" for tool in tools[:50])}
{"  ... and more" if len(tools) > 50 else ""}

Use `/tools_info <tool_name>` for details"""
            
            elif tool_type == "function":
                tools = self.tool_orchestrator.fc_engine.list_tools()
                return f"🔧 **Function Calling Tools** ({len(tools)}):\n" + "\n".join(f"  • {t}" for t in tools)
            
            elif tool_type == "plugin":
                tools = list(self.tool_orchestrator.plugin_tools.keys())
                return f"🔌 **Plugin Tools** ({len(tools)}):\n" + "\n".join(f"  • {t}" for t in tools)
            
            elif tool_type == "mcp":
                tools = list(self.tool_orchestrator.mcp_tools.keys())
                return f"🌐 **MCP Tools** ({len(tools)}):\n" + "\n".join(f"  • {t}" for t in tools)
            
            elif tool_type == "created":
                stats = self.tool_orchestrator.tool_creator.get_tool_usage_stats()
                tools = stats['tools']
                
                result = f"🔨 **Autonomously Created Tools** ({len(tools)}):\n\n"
                for name, info in tools.items():
                    result += f"  • **{name}**\n"
                    result += f"    Created: {info['created_at']}\n"
                    result += f"    Used: {info['usage_count']} times\n\n"
                
                return result
            
            else:
                return f"❌ Unknown type: {tool_type}\nValid types: all, function, plugin, mcp, created"
        
        except Exception as e:
            return f"❌ Error listing tools: {e}"
    
    def tools_info_command(self, tool_name: str) -> str:
        """
        Get detailed information about a specific tool
        
        Usage: /tools_info <tool_name>
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        if not tool_name:
            return "❌ Usage: /tools_info <tool_name>"
        
        try:
            info = self.tool_orchestrator.get_tool_info(tool_name)
            
            if not info:
                return f"❌ Tool not found: {tool_name}"
            
            result = f"🔧 **Tool: {info['name']}**\n\n"
            result += f"**Type:** {info['type']}\n"
            
            if info['type'] == 'function_calling':
                result += f"**Description:** {info['description']}\n\n"
                result += "**Parameters:**\n"
                for param in info['parameters']:
                    req = "required" if param['required'] else "optional"
                    result += f"  • `{param['name']}` ({param['type']}, {req})\n"
                    result += f"    {param['description']}\n"
            
            elif info['type'] == 'plugin':
                result += f"**Plugin:** {info['plugin']}\n"
                result += f"**Command:** {info['command']}\n"
            
            elif info['type'] == 'mcp':
                result += f"**MCP Server:** {info['server']}\n"
                result += f"**Capability:** {info['capability']['name']}\n"
            
            return result
        
        except Exception as e:
            return f"❌ Error getting tool info: {e}"
    
    def tools_create_command(self, capability: str) -> str:
        """
        Create a new tool for a specific capability
        
        Usage: /tools_create <capability_description>
        Example: /tools_create analyze sentiment of text
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        if not capability:
            return "❌ Usage: /tools_create <capability_description>"
        
        try:
            print(f"🔨 Creating tool for: {capability}")
            tool_name = self.tool_orchestrator.create_tool_on_demand(capability, urgency='normal')
            
            if tool_name:
                return f"✅ **Tool Created:** `{tool_name}`\n\nYou can now use it with `/tools_call {tool_name} <args>`"
            else:
                return "❌ Tool creation failed. Check logs for details."
        
        except Exception as e:
            return f"❌ Error creating tool: {e}"
    
    def tools_call_command(self, args: str) -> str:
        """
        Call a specific tool with arguments
        
        Usage: /tools_call <tool_name> <arg1=value1> <arg2=value2>
        Example: /tools_call analyze_sentiment text="This is great!"
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        if not args:
            return "❌ Usage: /tools_call <tool_name> <arg1=value1> <arg2=value2>"
        
        try:
            # Parse tool name and arguments
            parts = args.split(maxsplit=1)
            tool_name = parts[0]
            
            kwargs = {}
            if len(parts) > 1:
                # Parse key=value arguments
                import re
                arg_pattern = r'(\w+)=(["\']?)([^"\']+)\2'
                matches = re.findall(arg_pattern, parts[1])
                for key, _, value in matches:
                    kwargs[key] = value
            
            result = self.tool_orchestrator.call_tool_by_name(tool_name, **kwargs)
            
            return f"🔧 **Tool Result:**\n\n```\n{result}\n```"
        
        except Exception as e:
            return f"❌ Error calling tool: {e}"
    
    def tools_execute_command(self, task: str) -> str:
        """
        Execute a complex task using available tools (AI-powered)
        
        Usage: /tools_execute <task_description>
        Example: /tools_execute Check crypto prices and post summary to Moltx
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        if not task:
            return "❌ Usage: /tools_execute <task_description>"
        
        try:
            print(f"🎯 Executing task with tools: {task}")
            result = self.tool_orchestrator.execute_task_with_tools(
                task,
                context={},
                max_iterations=10,
                auto_create_tools=True
            )
            
            if result['success']:
                output = f"✅ **Task Completed**\n\n"
                output += f"**Result:** {result['result']}\n\n"
                output += f"**Tools Used:** {', '.join(result['tools_used'])}\n"
                output += f"**Iterations:** {result['iterations']}\n"
                
                if result['tool_calls']:
                    output += f"\n**Tool Calls:**\n"
                    for call in result['tool_calls'][:5]:  # Show first 5
                        output += f"  • {call['name']}\n"
                
                return output
            else:
                return f"❌ **Task Failed**\n\nError: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"❌ Error executing task: {e}"
    
    def tools_suggest_command(self, task: str) -> str:
        """
        Suggest best tools for a task
        
        Usage: /tools_suggest <task_description>
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        if not task:
            return "❌ Usage: /tools_suggest <task_description>"
        
        try:
            suggestions = self.tool_orchestrator.suggest_tool_for_task(task)
            
            if not suggestions:
                return "❌ No suggestions available"
            
            result = f"💡 **Suggested Tools for:** {task}\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                result += f"{i}. **{suggestion['tool_name']}** (confidence: {suggestion['confidence']:.0%})\n"
                result += f"   {suggestion['reasoning']}\n\n"
            
            return result
        
        except Exception as e:
            return f"❌ Error suggesting tools: {e}"
    
    def tools_stats_command(self, args: str = "") -> str:
        """
        Show tool usage statistics
        
        Usage: /tools_stats
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        try:
            stats = self.tool_orchestrator.get_tool_usage_stats()
            
            result = "📊 **Tool Usage Statistics**\n\n"
            result += f"**Total Tools:** {stats['total_tools']}\n\n"
            
            result += "**By Type:**\n"
            for tool_type, count in stats['by_type'].items():
                result += f"  • {tool_type}: {count}\n"
            
            result += f"\n**Autonomously Created:** {stats['created_tools']['total_tools_created']}\n"
            
            if stats['created_tools']['recent_creations']:
                result += "\n**Recent Creations:**\n"
                for creation in stats['created_tools']['recent_creations'][-5:]:
                    result += f"  • {creation['tool_name']} ({creation['timestamp'][:10]})\n"
            
            return result
        
        except Exception as e:
            return f"❌ Error getting stats: {e}"
    
    def tools_refresh_command(self, args: str = "") -> str:
        """
        Refresh tool discovery (re-scan plugins and MCP servers)
        
        Usage: /tools_refresh
        """
        if not self.tool_orchestrator:
            return "❌ Tool orchestrator not available"
        
        try:
            self.tool_orchestrator.refresh_tool_discovery()
            tools = self.tool_orchestrator.list_all_tools()
            return f"✅ Tool discovery refreshed: {len(tools)} tools available"
        
        except Exception as e:
            return f"❌ Error refreshing tools: {e}"
