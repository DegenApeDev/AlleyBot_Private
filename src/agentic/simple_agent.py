"""
Simple Agent Implementation (No LangChain dependency)
For Python 3.14 compatibility when LangChain isn't available
"""
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass


@dataclass
class AgentState:
    """Simple agent state"""
    current_task: str = ""
    iteration: int = 0
    observations: List[str] = None
    actions_taken: List[str] = None
    goal_stack: List[str] = None
    
    def __post_init__(self):
        if self.observations is None:
            self.observations = []
        if self.actions_taken is None:
            self.actions_taken = []
        if self.goal_stack is None:
            self.goal_stack = []


class SimpleTool:
    """Simple tool wrapper"""
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description
    
    def run(self, input_str: str) -> str:
        """Run the tool"""
        try:
            return str(self.func(input_str))
        except Exception as e:
            return f"Error: {str(e)}"


class SimpleReActAgent:
    """
    Simple ReAct agent without LangChain dependency
    Implements basic Reason + Act loop
    """
    
    def __init__(self, llm, tools: List[SimpleTool], max_iterations: int = 15):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.state = AgentState()
        
    def run(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run the agent on a task
        
        Args:
            task: Task description
            context: Optional context dictionary
            
        Returns:
            Result dictionary
        """
        self.state = AgentState(current_task=task)
        context = context or {}
        
        print(f"🎯 Task: {task}")
        
        for iteration in range(self.max_iterations):
            self.state.iteration = iteration + 1
            print(f"\n🔄 Iteration {self.state.iteration}/{self.max_iterations}")
            
            # Reason: What should we do?
            thought = self._reason(task, context)
            print(f"💭 Thought: {thought}")
            
            # Act: Execute action
            action_result = self._act(thought)
            print(f"⚡ Action Result: {action_result[:200]}...")
            
            # Observe: Record result
            self.state.observations.append(action_result)
            
            # Check if done
            if self._is_task_complete(task, action_result):
                print(f"✅ Task complete after {iteration + 1} iterations")
                return {
                    'success': True,
                    'output': action_result,
                    'iterations': iteration + 1,
                    'actions': self.state.actions_taken
                }
        
        print(f"⚠️  Max iterations reached")
        return {
            'success': False,
            'output': 'Max iterations reached',
            'iterations': self.max_iterations,
            'actions': self.state.actions_taken
        }
    
    def _reason(self, task: str, context: Dict) -> str:
        """Reason about what to do next"""
        # Build prompt
        tools_desc = "\n".join([f"- {name}: {tool.description}" 
                               for name, tool in self.tools.items()])
        
        recent_obs = "\n".join(self.state.observations[-3:]) if self.state.observations else "None"
        
        prompt = f"""You are an AI agent working on this task: {task}

Available tools:
{tools_desc}

Recent observations:
{recent_obs}

Context:
{json.dumps(context, indent=2)}

What should you do next? Respond with:
1. Your reasoning (1-2 sentences)
2. The tool to use (or "DONE" if task is complete)
3. The input for the tool

Format:
REASONING: <your reasoning>
TOOL: <tool_name or DONE>
INPUT: <tool input>
"""
        
        try:
            # Use DeepSeek to reason
            response = self.llm.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"REASONING: Error in reasoning: {e}\nTOOL: DONE\nINPUT: none"
    
    def _act(self, thought: str) -> str:
        """Execute action based on thought"""
        # Parse thought
        lines = thought.split('\n')
        tool_name = None
        tool_input = ""
        
        for line in lines:
            if line.startswith('TOOL:'):
                tool_name = line.replace('TOOL:', '').strip()
            elif line.startswith('INPUT:'):
                tool_input = line.replace('INPUT:', '').strip()
        
        if not tool_name or tool_name == "DONE":
            return "Task marked as complete"
        
        # Execute tool
        if tool_name in self.tools:
            self.state.actions_taken.append(f"{tool_name}({tool_input})")
            result = self.tools[tool_name].run(tool_input)
            return result
        else:
            return f"Error: Unknown tool '{tool_name}'"
    
    def _is_task_complete(self, task: str, last_result: str) -> bool:
        """Check if task is complete"""
        # Simple heuristics
        if "DONE" in last_result or "complete" in last_result.lower():
            return True
        
        if "error" in last_result.lower() and len(self.state.observations) > 3:
            return True  # Give up after multiple errors
        
        return False
    
    def add_goal(self, goal: str):
        """Add a goal to the stack"""
        self.state.goal_stack.append(goal)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        return {
            'total_iterations': self.state.iteration,
            'total_actions': len(self.state.actions_taken),
            'successful_actions': len([a for a in self.state.actions_taken if 'error' not in a.lower()]),
            'goals': self.state.goal_stack
        }
