"""
Action Router Integration for Hermes Tools

Integrates the new Hermes-style tools with AlleyBot's existing action router.
This allows seamless execution of tools through the AGI Kernel's action pipeline.
"""

from typing import Dict, Any, Optional
import asyncio

from src.agentic.action_router import ActionRouter
from src.tools.tool_registry import get_tool_registry, execute_tool_action, ToolExecution


class HermesToolsActionRouter(ActionRouter):
    """Extended action router with Hermes tools support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_registry = get_tool_registry()
        self._register_tool_actions()
    
    def _register_tool_actions(self):
        """Register all tools as actions in the router"""
        tools = self.tool_registry.list_tools()
        
        for tool in tools:
            # Register each tool as an action
            self.register_action(f"tool_{tool.name}", self._execute_tool_action)
    
    async def _execute_tool_action(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool action"""
        try:
            # Extract tool name from action type
            action_type = action_spec.get('action_type', '')
            
            # Handle both "tool_<name>" and direct "<name>" formats
            if action_type.startswith('tool_'):
                tool_name = action_type[5:]  # Remove "tool_" prefix
            else:
                tool_name = action_type
            
            # Get parameters
            params = action_spec.get('params', {})
            
            # Add any context from action_spec
            if 'context' in action_spec:
                params.update(action_spec['context'])
            
            # Execute tool
            result = await execute_tool_action(
                tool_name=tool_name,
                method=tool_name,
                **params
            )
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Tool action failed: {str(e)}',
                'action_type': action_spec.get('action_type')
            }
    
    async def route_action(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Route action with tool support"""
        action_type = action_spec.get('action_type', '')
        
        # Check if this is a tool action
        if (action_type.startswith('tool_') or 
            self.tool_registry.get_tool(action_type)):
            
            return await self._execute_tool_action(action_spec)
        
        # Fall back to parent routing
        return await super().route_action(action_spec)


class ToolDiscoveryService:
    """Service for AI-driven tool discovery and selection"""
    
    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry or get_tool_registry()
    
    async def discover_tools_for_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Discover tools that can handle a request"""
        try:
            from src.tools.tool_registry import discover_tools_for_task
            
            # Discover relevant tools
            tools = discover_tools_for_task(request)
            
            # Build tool recommendations
            recommendations = []
            for tool in tools:
                recommendation = {
                    'name': tool.name,
                    'category': tool.category.value,
                    'description': tool.description,
                    'parameters': tool.parameters,
                    'examples': tool.examples,
                    'confidence': self._calculate_confidence(request, tool),
                    'enabled': tool.enabled
                }
                recommendations.append(recommendation)
            
            # Sort by confidence
            recommendations.sort(key=lambda r: r['confidence'], reverse=True)
            
            return {
                'success': True,
                'request': request,
                'tools': recommendations,
                'count': len(recommendations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Tool discovery failed: {str(e)}',
                'request': request
            }
    
    def _calculate_confidence(self, request: str, tool) -> float:
        """Calculate confidence score for tool relevance"""
        request_lower = request.lower()
        confidence = 0.0
        
        # Name match
        if tool.name.lower() in request_lower:
            confidence += 0.5
        
        # Category keywords
        category_keywords = {
            'web': ['web', 'internet', 'search', 'website', 'url', 'http'],
            'terminal': ['command', 'terminal', 'shell', 'execute', 'run'],
            'file': ['file', 'read', 'write', 'save', 'open', 'edit'],
            'browser': ['browser', 'click', 'navigate', 'page', 'website'],
            'vision': ['image', 'picture', 'see', 'look', 'analyze'],
            'code': ['code', 'python', 'javascript', 'execute', 'run'],
            'todo': ['todo', 'task', 'list', 'remember', 'track']
        }
        
        keywords = category_keywords.get(tool.category.value, [])
        for keyword in keywords:
            if keyword in request_lower:
                confidence += 0.2
        
        # Description match
        desc_words = tool.description.lower().split()
        matches = sum(1 for word in desc_words if word in request_lower)
        if matches > 0:
            confidence += min(matches * 0.1, 0.3)
        
        return min(confidence, 1.0)


# Tool execution monitoring
class ToolExecutionMonitor:
    """Monitor and log tool executions"""
    
    def __init__(self, log_path: str = "logs/tool_executions.json"):
        self.log_path = log_path
        self.execution_history = []
        self._load_history()
    
    def _load_history(self):
        """Load execution history"""
        import json
        from pathlib import Path
        
        try:
            if Path(self.log_path).exists():
                with open(self.log_path, 'r') as f:
                    self.execution_history = json.load(f)
        except:
            self.execution_history = []
    
    def _save_history(self):
        """Save execution history"""
        import json
        from pathlib import Path
        
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w') as f:
            json.dump(self.execution_history[-1000:], f, indent=2)  # Keep last 1000
    
    def log_execution(self, execution: ToolExecution):
        """Log a tool execution"""
        import datetime
        
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'tool_name': execution.tool_name,
            'method': execution.method,
            'params': execution.params,
            'success': execution.success,
            'error': execution.error,
            'execution_time': execution.execution_time,
            'metadata': execution.metadata
        }
        
        self.execution_history.append(log_entry)
        self._save_history()
    
    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for tool executions"""
        if tool_name:
            executions = [e for e in self.execution_history if e['tool_name'] == tool_name]
        else:
            executions = self.execution_history
        
        if not executions:
            return {'total': 0}
        
        total = len(executions)
        successful = len([e for e in executions if e['success']])
        avg_time = sum(e['execution_time'] for e in executions) / total
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': successful / total,
            'average_execution_time': avg_time,
            'last_execution': executions[-1]['timestamp'] if executions else None
        }


# Integration helper
async def setup_hermes_tools_integration(alleybot_core):
    """Setup Hermes tools integration with AlleyBot core"""
    try:
        # Get tool registry
        tool_registry = get_tool_registry()
        
        # Set plugin manager if available
        if hasattr(alleybot_core, 'plugin_manager'):
            tool_registry.set_plugin_manager(alleybot_core.plugin_manager)
        
        # Set skill executor if available
        if hasattr(alleybot_core, 'skill_executor'):
            tool_registry.set_skill_executor(alleybot_core.skill_executor)
        
        # Replace action router with enhanced version
        if hasattr(alleybot_core, 'agi_kernel') and alleybot_core.agi_kernel:
            original_router = alleybot_core.agi_kernel.action_router
            
            # Create enhanced router (ActionRouter only takes agi_kernel and plugin_manager)
            enhanced_router = HermesToolsActionRouter(
                alleybot_core.agi_kernel,
                alleybot_core.plugin_manager,
            )
            
            # Copy existing actions
            enhanced_router.actions = original_router.actions.copy()
            enhanced_router._register_tool_actions()
            
            # Replace router
            alleybot_core.agi_kernel.action_router = enhanced_router
            print(f"   📊 Registered {len(enhanced_router.actions)} total actions")
        
        # Setup execution monitor
        monitor = ToolExecutionMonitor()
        
        # Hook into action execution for monitoring
        original_act = alleybot_core.agi_kernel.act
        
        async def monitored_act(action_spec):
            result = await original_act(action_spec)
            
            # Log tool executions
            if action_spec.get('action_type', '').startswith('tool_'):
                tool_name = action_spec.get('action_type')[5:]
                execution = ToolExecution(
                    tool_name=tool_name,
                    method=tool_name,
                    params=action_spec.get('params', {}),
                    success=result.get('success', False),
                    error=result.get('error'),
                    metadata=result.get('metadata', {})
                )
                monitor.log_execution(execution)
            
            return result
        
        alleybot_core.agi_kernel.act = monitored_act
        
        print(f"✅ Hermes tools integrated: {len(tool_registry.tools)} tools registered")
        
        return {
            'success': True,
            'tools_registered': len(tool_registry.tools),
            'categories': list(tool_registry.tool_categories.keys()),
            'monitor': monitor
        }
        
    except Exception as e:
        print(f"❌ Failed to integrate Hermes tools: {e}")
        return {
            'success': False,
            'error': str(e)
        }
