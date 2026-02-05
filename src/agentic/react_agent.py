"""
Enhanced ReAct Agent Loop with LangChain Integration
Implements Reason + Act pattern with security and on-chain awareness
"""
import os
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_community.llms import BaseLLM


@dataclass
class AgentState:
    """Current state of the agent"""
    iteration: int = 0
    observations: List[str] = None
    actions_taken: List[Dict] = None
    goals: List[str] = None
    wallet_context: Dict[str, Any] = None
    on_chain_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.observations is None:
            self.observations = []
        if self.actions_taken is None:
            self.actions_taken = []
        if self.goals is None:
            self.goals = []
        if self.wallet_context is None:
            self.wallet_context = {}
        if self.on_chain_context is None:
            self.on_chain_context = {}


class SecureToolWrapper:
    """Wrapper for tools with security checks and approval requirements"""
    
    def __init__(self, tool: Tool, requires_approval: bool = False, 
                 allowlist: List[str] = None):
        self.tool = tool
        self.requires_approval = requires_approval
        self.allowlist = allowlist or []
        self.execution_log = []
        
    def is_allowed(self, action_input: str) -> bool:
        """Check if action is in allowlist"""
        if not self.allowlist:
            return True
        return any(allowed in action_input.lower() for allowed in self.allowlist)
    
    def execute(self, action_input: str, approval_callback: Optional[Callable] = None) -> str:
        """Execute tool with security checks"""
        # Check allowlist
        if not self.is_allowed(action_input):
            return f"❌ Action blocked: '{action_input}' not in allowlist for {self.tool.name}"
        
        # Check if approval required
        if self.requires_approval:
            if approval_callback is None:
                return f"⏳ Action requires approval: {self.tool.name} - {action_input}"
            
            approved = approval_callback(self.tool.name, action_input)
            if not approved:
                return f"❌ Action denied by approval system: {self.tool.name}"
        
        # Execute tool
        try:
            start_time = time.time()
            result = self.tool.func(action_input)
            duration = time.time() - start_time
            
            # Log execution
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'tool': self.tool.name,
                'input': action_input,
                'success': True,
                'duration': duration
            })
            
            return result
        except Exception as e:
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'tool': self.tool.name,
                'input': action_input,
                'success': False,
                'error': str(e)
            })
            return f"❌ Tool execution failed: {str(e)}"


class EnhancedReActAgent:
    """
    Enhanced ReAct agent with:
    - Structured reasoning loop
    - Security allowlists
    - On-chain context awareness
    - Approval system integration
    - Error recovery
    """
    
    def __init__(self, llm: BaseLLM, tools: List[Tool], 
                 max_iterations: int = 15,
                 approval_callback: Optional[Callable] = None):
        self.llm = llm
        self.max_iterations = max_iterations
        self.approval_callback = approval_callback
        
        # Wrap tools with security
        self.secure_tools = self._wrap_tools_with_security(tools)
        
        # Create ReAct prompt
        self.prompt = self._create_react_prompt()
        
        # Create agent
        self.agent = create_react_agent(
            llm=llm,
            tools=[st.tool for st in self.secure_tools],
            prompt=self.prompt
        )
        
        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=[st.tool for st in self.secure_tools],
            max_iterations=max_iterations,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            max_execution_time=300  # 5 minute timeout
        )
        
        self.state = AgentState()
        
    def _wrap_tools_with_security(self, tools: List[Tool]) -> List[SecureToolWrapper]:
        """Wrap tools with security checks"""
        secure_tools = []
        
        # Define high-risk tools that require approval
        high_risk_tools = [
            'create_post', 'send_transaction', 'transfer_funds',
            'delete_post', 'update_profile', 'execute_code'
        ]
        
        # Define allowlists for specific tools
        allowlists = {
            'create_post': ['moltbook', 'moltx', '4claw'],
            'send_transaction': ['base', 'ethereum'],
            'execute_code': []  # Empty = requires approval for all
        }
        
        for tool in tools:
            requires_approval = any(risk in tool.name.lower() for risk in high_risk_tools)
            allowlist = allowlists.get(tool.name, [])
            
            secure_tools.append(SecureToolWrapper(
                tool=tool,
                requires_approval=requires_approval,
                allowlist=allowlist
            ))
        
        return secure_tools
    
    def _create_react_prompt(self) -> PromptTemplate:
        """Create ReAct prompt template with on-chain awareness"""
        template = """You are AlleyBot, an autonomous AI agent with on-chain capabilities.

CURRENT CONTEXT:
Wallet Address: {wallet_address}
Network: Base (Chain ID: 8453)
Current Balance: {wallet_balance} ETH
Recent Transactions: {recent_txs}

ON-CHAIN OPPORTUNITIES:
{on_chain_context}

GOALS:
{goals}

You have access to the following tools:
{tools}

SECURITY RULES:
1. High-risk actions (create_post, send_transaction) require approval
2. Only use allowlisted platforms and networks
3. Never execute unbounded code
4. Always verify on-chain data before acting

Use the following format:

Thought: Consider what you observe and what action to take
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation up to {max_iterations} times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        
        return PromptTemplate(
            template=template,
            input_variables=[
                "input", "agent_scratchpad", "tools", "tool_names",
                "wallet_address", "wallet_balance", "recent_txs",
                "on_chain_context", "goals", "max_iterations"
            ]
        )
    
    def update_on_chain_context(self, wallet_address: str, web3_provider=None):
        """Update on-chain context for agent"""
        try:
            if web3_provider:
                from web3 import Web3
                w3 = web3_provider
                
                # Get balance
                balance = w3.eth.get_balance(wallet_address)
                balance_eth = w3.from_wei(balance, 'ether')
                
                # Get recent transactions (simplified)
                block = w3.eth.get_block('latest')
                
                self.state.wallet_context = {
                    'address': wallet_address,
                    'balance': str(balance_eth),
                    'network': 'base',
                    'chain_id': 8453
                }
                
                self.state.on_chain_context = {
                    'latest_block': block['number'],
                    'gas_price': w3.eth.gas_price,
                    'opportunities': []
                }
            else:
                # Fallback without web3
                self.state.wallet_context = {
                    'address': wallet_address,
                    'balance': 'N/A',
                    'network': 'base'
                }
        except Exception as e:
            print(f"⚠️  Failed to update on-chain context: {e}")
    
    def add_goal(self, goal: str):
        """Add a goal to the agent's goal stack"""
        self.state.goals.append(goal)
    
    def run(self, task: str, on_chain_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run the ReAct agent loop
        
        Args:
            task: The task to accomplish
            on_chain_context: Optional on-chain context to inject
            
        Returns:
            Dict with result, intermediate steps, and state
        """
        # Update context if provided
        if on_chain_context:
            self.state.on_chain_context.update(on_chain_context)
        
        # Prepare inputs
        inputs = {
            'input': task,
            'wallet_address': self.state.wallet_context.get('address', 'N/A'),
            'wallet_balance': self.state.wallet_context.get('balance', 'N/A'),
            'recent_txs': 'N/A',  # TODO: Implement transaction history
            'on_chain_context': json.dumps(self.state.on_chain_context, indent=2),
            'goals': '\n'.join(f"- {g}" for g in self.state.goals) or 'None',
            'max_iterations': self.max_iterations
        }
        
        try:
            # Run agent
            result = self.executor.invoke(inputs)
            
            # Update state
            self.state.iteration += 1
            
            # Clean up output to prevent raw JSON display
            output = result.get('output', '')
            if output and output.startswith('{') and output.endswith('}'):
                # If output looks like raw JSON, try to format it
                try:
                    parsed = json.loads(output)
                    output = f"Action completed: {parsed.get('title', 'Unknown action')}"
                except:
                    output = "Action completed successfully"
            
            self.state.observations.append(output)
            
            # Track actions
            if 'intermediate_steps' in result:
                for step in result['intermediate_steps']:
                    action, observation = step
                    self.state.actions_taken.append({
                        'action': action.tool,
                        'input': action.tool_input,
                        'observation': observation,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return {
                'success': True,
                'output': output,
                'intermediate_steps': result.get('intermediate_steps', []),
                'state': asdict(self.state)
            }
            
        except Exception as e:
            # Error recovery
            error_msg = str(e)
            print(f"❌ Agent execution error: {error_msg}")
            
            # Attempt recovery
            recovery_result = self._attempt_recovery(task, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'recovery_attempted': True,
                'recovery_result': recovery_result,
                'state': asdict(self.state)
            }
    
    def _attempt_recovery(self, original_task: str, error: str) -> Dict[str, Any]:
        """Attempt to recover from error using LLM reasoning"""
        try:
            recovery_prompt = f"""
            The agent encountered an error while executing: {original_task}
            
            Error: {error}
            
            Previous actions: {json.dumps(self.state.actions_taken[-3:], indent=2)}
            
            Analyze the error and suggest a recovery strategy:
            1. What went wrong?
            2. Can we retry with different parameters?
            3. Should we break down the task differently?
            4. Is this a permanent failure?
            
            Provide a concrete recovery plan.
            """
            
            # Use LLM to analyze error
            recovery_analysis = self.llm.invoke(recovery_prompt)
            
            return {
                'analysis': recovery_analysis,
                'retry_recommended': 'retry' in recovery_analysis.lower(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'analysis': f"Recovery analysis failed: {str(e)}",
                'retry_recommended': False
            }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of agent execution"""
        total_actions = len(self.state.actions_taken)
        successful_actions = sum(
            1 for st in self.secure_tools 
            for log in st.execution_log 
            if log.get('success')
        )
        
        return {
            'total_iterations': self.state.iteration,
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'goals_completed': len([g for g in self.state.goals if 'completed' in g.lower()]),
            'on_chain_interactions': len([
                a for a in self.state.actions_taken 
                if 'transaction' in a.get('action', '').lower()
            ])
        }
