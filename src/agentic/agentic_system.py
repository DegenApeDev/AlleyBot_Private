"""
Integrated Agentic System for AlleyBot
Combines ReAct agent, event scheduler, skill generation, enhanced memory, and security
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Try to import LangChain components, fallback to simple agent if incompatible
try:
    from src.agentic.react_agent import EnhancedReActAgent, AgentState
    from langchain.tools import Tool
    from langchain_community.llms import BaseLLM
    LANGCHAIN_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"⚠️  LangChain not available (Python {sys.version_info.major}.{sys.version_info.minor}): {e}")
    print("📦 Using simple agent implementation instead")
    from src.agentic.simple_agent import SimpleReActAgent, SimpleTool, AgentState
    LANGCHAIN_AVAILABLE = False
    Tool = SimpleTool  # Alias for compatibility
    BaseLLM = None

# Import other agentic components
from src.agentic.event_scheduler import ProactiveAgentScheduler, OnChainOpportunityDetector
from src.agentic.skill_generator import DynamicSkillGenerator
from src.agentic.enhanced_memory import EnhancedMemorySystem
from src.agentic.security_filter import SecurityFilter
from src.agentic.approval_dashboard import ApprovalDashboard


class AgenticAlleyBot:
    """
    Main agentic system integrating all components
    
    Features:
    - ReAct reasoning loop with LangChain
    - Proactive event-driven behavior
    - Dynamic skill generation
    - Vector memory with hierarchical goals
    - Security filtering with approval system
    - On-chain awareness
    """
    
    def __init__(self, llm: BaseLLM, core, config: Optional[Dict] = None):
        """
        Initialize agentic system
        
        Args:
            llm: Language model for reasoning
            core: AlleyBot core instance
            config: Optional configuration
        """
        self.llm = llm
        self.core = core
        self.config = config or {}
        
        print("🤖 Initializing Agentic AlleyBot System...")
        
        # Reuse core's enhanced memory if available, otherwise create our own
        if hasattr(core, 'enhanced_memory') and core.enhanced_memory:
            self.memory = core.enhanced_memory
            print("✅ Reusing core's enhanced memory system")
        else:
            self.memory = EnhancedMemorySystem(
                storage_dir=self.config.get('memory_dir', 'data/memory')
            )
            print("✅ Enhanced memory system initialized (standalone)")
        
        # Initialize security filter
        self.security_filter = SecurityFilter()
        print("✅ Security filter initialized")
        
        # Initialize approval dashboard
        # Note: telegram_bot will be None initially, can be set later if needed
        self.approval_dashboard = ApprovalDashboard(
            telegram_bot=None,
            admin_chat_id=os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        )
        print("✅ Approval dashboard initialized")
        
        # Initialize skill generator
        self.skill_generator = DynamicSkillGenerator(
            llm=llm,
            skills_dir='dynamic_skills'
        )
        print("✅ Dynamic skill generator initialized")
        
        # Load existing dynamic skills
        loaded_skills = self.skill_generator.load_dynamic_skills()
        if loaded_skills:
            print(f"✅ Loaded {len(loaded_skills)} dynamic skills")
        
        # Build tool list
        self.tools = self._build_tools()
        print(f"✅ Built {len(self.tools)} tools")
        
        # Initialize ReAct agent with LangChain
        if LANGCHAIN_AVAILABLE:
            self.agent = EnhancedReActAgent(
                llm=llm,
                tools=self.tools,
                max_iterations=self.config.get('max_iterations', 15),
                approval_callback=self.approval_dashboard.request_approval
            )
            print("✅ Enhanced ReAct agent initialized (LangChain)")
        else:
            # Fallback only if LangChain not available at all
            self.agent = SimpleReActAgent(
                llm=llm,
                tools=self.tools,
                max_iterations=self.config.get('max_iterations', 15)
            )
            print("✅ ReAct agent initialized (fallback mode)")
        
        # Update on-chain context (only for LangChain agent)
        wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        if wallet_address and LANGCHAIN_AVAILABLE and hasattr(self.agent, 'update_on_chain_context'):
            self.agent.update_on_chain_context(wallet_address)
            print(f"✅ On-chain context updated for {wallet_address[:10]}...")
        
        # Initialize opportunity detector with real Web3 provider from onchain plugin
        onchain_plugin = core.plugin_manager.plugins.get('onchain')
        web3_prov = getattr(onchain_plugin, 'web3_provider', None) if onchain_plugin else None
        w3_instance = getattr(web3_prov, 'w3', None) if web3_prov and getattr(web3_prov, 'connected', False) else None
        self.onchain_plugin = onchain_plugin
        self.selfimprove_plugin = core.plugin_manager.plugins.get('selfimprove')
        if self.selfimprove_plugin:
            print("✅ Self-improvement plugin linked")
        self.opportunity_detector = OnChainOpportunityDetector(
            moltbook_api=getattr(core.plugin_manager.plugins.get('moltbook'), 'api', None),
            web3_provider=w3_instance
        )
        if w3_instance:
            print("✅ Opportunity detector initialized (Web3 connected)")
        else:
            print("✅ Opportunity detector initialized (Web3 not available)")
        
        # Initialize proactive scheduler
        self.scheduler = ProactiveAgentScheduler(
            agent_executor=self._execute_agent_task,
            opportunity_detector=self.opportunity_detector
        )
        print("✅ Proactive scheduler initialized")
        
        # Set up hierarchical goals
        self._setup_initial_goals()
        
        print("✅ Agentic AlleyBot System ready!")
    
    def _build_tools(self) -> List[Tool]:
        """Build tool list from core plugins and dynamic skills"""
        tools = []
        
        # Add core plugin tools
        if hasattr(self.core, 'plugin_manager'):
            for plugin_name, plugin in self.core.plugin_manager.plugins.items():
                if hasattr(plugin, 'get_commands'):
                    commands = plugin.get_commands()
                    
                    for cmd_name, cmd_func in commands.items():
                        tool = Tool(
                            name=cmd_name,
                            func=lambda x, f=cmd_func: self._safe_tool_execution(f, x),
                            description=f"Execute {cmd_name} from {plugin_name} plugin"
                        )
                        tools.append(tool)
        
        # Add memory tools
        tools.extend([
            Tool(
                name="search_memory",
                func=lambda x: self._search_memory_tool(x),
                description="Search agent memory for relevant information. Input: search query"
            ),
            Tool(
                name="add_memory",
                func=lambda x: self._add_memory_tool(x),
                description="Add information to agent memory. Input: JSON with 'content' and 'type'"
            ),
            Tool(
                name="get_active_goals",
                func=lambda x: self._get_goals_tool(x),
                description="Get active goals. Input: goal_type (short_term/long_term) or 'all'"
            ),
            Tool(
                name="update_goal_progress",
                func=lambda x: self._update_goal_tool(x),
                description="Update goal progress. Input: JSON with 'goal_id' and 'progress' (0-1)"
            )
        ])
        
        # Add skill generation tool
        tools.append(
            Tool(
                name="generate_skill",
                func=lambda x: self._generate_skill_tool(x),
                description="Generate a new skill for missing capability. Input: JSON with 'capability' and 'skill_name'"
            )
        )
        
        # Add on-chain tools
        tools.extend([
            Tool(
                name="check_wallet_balance",
                func=lambda x: self._check_balance_tool(x),
                description="Check wallet balance on Base network. Input: wallet address or 'self'"
            ),
            Tool(
                name="get_on_chain_opportunities",
                func=lambda x: self._get_opportunities_tool(x),
                description="Get current on-chain opportunities. Input: 'all' or platform name"
            )
        ])
        
        # Add self-improvement tools
        tools.extend([
            Tool(
                name="run_tests",
                func=lambda x: self._run_tests_tool(x),
                description="Run project test suite. Input: 'all' or specific test module name"
            ),
            Tool(
                name="self_improve",
                func=lambda x: self._self_improve_tool(x),
                description="Run autonomous self-improvement cycle. Input: 'full' or 'ideas'"
            ),
        ])
        
        return tools
    
    def _safe_tool_execution(self, func, input_str: str) -> str:
        """Execute tool with security checks"""
        try:
            # Parse input if JSON
            try:
                params = json.loads(input_str) if input_str else {}
            except (json.JSONDecodeError, TypeError):
                params = {'input': input_str} if input_str else {}
            
            # Security check
            action_name = func.__name__ if hasattr(func, '__name__') else 'unknown'
            
            # Check if function takes arguments
            import inspect
            sig = inspect.signature(func)
            takes_args = len(sig.parameters) > 0
            
            # Extract actual content from JSON if it's a post command
            if 'moltbook_post' in action_name or 'moltx_post' in action_name:
                if isinstance(params, dict) and 'content' in params:
                    # For post commands, extract the content
                    content = params['content']
                    if isinstance(content, list):
                        content = ' '.join(str(c) for c in content)
                    security_result = self.security_filter.execute_with_security(
                        action=action_name,
                        params={'content': content},
                        executor=lambda a, p: func(content)
                    )
                elif isinstance(params, dict) and 'input' in params:
                    content = params['input']
                    security_result = self.security_filter.execute_with_security(
                        action=action_name,
                        params={'content': content},
                        executor=lambda a, p: func(content)
                    )
                else:
                    # Plain string input
                    security_result = self.security_filter.execute_with_security(
                        action=action_name,
                        params={'input': input_str},
                        executor=lambda a, p: func(input_str)
                    )
            elif takes_args and input_str:
                security_result = self.security_filter.execute_with_security(
                    action=action_name,
                    params=params,
                    executor=lambda a, p: func(input_str)
                )
            else:
                # Function takes no arguments
                security_result = self.security_filter.execute_with_security(
                    action=action_name,
                    params=params,
                    executor=lambda a, p: func()
                )
            
            if security_result['success']:
                result = security_result.get('result', 'Success')
                # Clean up result to prevent raw JSON display
                if isinstance(result, str) and result.startswith('{') and result.endswith('}'):
                    try:
                        parsed = json.loads(result)
                        if 'title' in parsed:
                            return f"✅ Post created: {parsed.get('title', 'Unknown')}"
                        return "✅ Action completed successfully"
                    except (json.JSONDecodeError, KeyError):
                        return "✅ Action completed successfully"
                return str(result)
            else:
                return f"❌ {security_result.get('error', 'Execution failed')}"
                
        except Exception as e:
            return f"❌ Tool execution error: {str(e)}"
    
    def _search_memory_tool(self, query: str) -> str:
        """Search memory tool"""
        results = self.memory.search_memories(query, k=5)
        
        if not results:
            return "No relevant memories found"
        
        output = f"Found {len(results)} relevant memories:\n\n"
        for i, mem in enumerate(results, 1):
            output += f"{i}. [{mem['memory_type']}] {mem['content'][:100]}...\n"
        
        return output
    
    def _add_memory_tool(self, input_str: str) -> str:
        """Add memory tool"""
        try:
            data = json.loads(input_str)
            content = data.get('content')
            mem_type = data.get('type', 'interaction')
            
            mem_id = self.memory.add_memory(content, mem_type)
            return f"✅ Memory added: {mem_id}"
            
        except Exception as e:
            return f"❌ Failed to add memory: {str(e)}"
    
    def _get_goals_tool(self, goal_type: str) -> str:
        """Get goals tool"""
        if goal_type == 'all':
            goals = self.memory.get_active_goals()
        else:
            goals = self.memory.get_active_goals(goal_type)
        
        if not goals:
            return "No active goals"
        
        output = f"Active goals ({len(goals)}):\n\n"
        for goal in goals:
            output += f"• [{goal['goal_type']}] {goal['description']}\n"
            output += f"  Progress: {goal['progress']*100:.0f}% | Priority: {goal['priority']}\n"
        
        return output
    
    def _update_goal_tool(self, input_str: str) -> str:
        """Update goal progress tool"""
        try:
            data = json.loads(input_str)
            goal_id = data.get('goal_id')
            progress = float(data.get('progress', 0))
            
            self.memory.update_goal_progress(goal_id, progress)
            return f"✅ Goal progress updated: {progress*100:.0f}%"
            
        except Exception as e:
            return f"❌ Failed to update goal: {str(e)}"
    
    def _generate_skill_tool(self, input_str: str) -> str:
        """Generate new skill tool"""
        try:
            data = json.loads(input_str)
            capability = data.get('capability')
            skill_name = data.get('skill_name')
            is_on_chain = data.get('is_on_chain', False)
            
            result = self.skill_generator.generate_and_register_skill(
                capability, skill_name, is_on_chain
            )
            
            if result['success']:
                # Reload tools to include new skill
                self.tools = self._build_tools()
                return f"✅ Skill generated and registered: {skill_name}"
            else:
                return f"❌ Skill generation failed: {result.get('error')}"
                
        except Exception as e:
            return f"❌ Failed to generate skill: {str(e)}"
    
    def _check_balance_tool(self, address: str) -> str:
        """Check wallet balance tool using onchain plugin"""
        if address == 'self':
            address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')

        if not address:
            return "❌ No wallet address provided"

        # Use onchain plugin if available
        if self.onchain_plugin and hasattr(self.onchain_plugin, 'web3_provider'):
            provider = self.onchain_plugin.web3_provider
            if provider and provider.connected:
                result = provider.get_eth_balance(address)
                if result['success']:
                    output = f"💰 Balance for {address[:10]}...{address[-6:]}\n"
                    output += f"  Ξ {result['balance_eth']:.6f} ETH ({result['network']})\n"

                    # Also check tracked tokens
                    for symbol, token_info in self.onchain_plugin.tracked_tokens.items():
                        tok_result = provider.get_token_balance(token_info['address'], address)
                        if tok_result['success']:
                            output += f"  🪙 {tok_result['balance']:,.4f} {symbol}\n"

                    return output
                else:
                    return f"❌ Balance check failed: {result['error']}"

        return f"❌ Web3 not connected. Enable the onchain plugin."
    
    def _get_opportunities_tool(self, platform: str) -> str:
        """Get on-chain opportunities tool"""
        opportunities = self.opportunity_detector.get_all_opportunities()
        
        if platform != 'all':
            opportunities = [o for o in opportunities if o['platform'] == platform]
        
        if not opportunities:
            return "No opportunities found"
        
        output = f"Found {len(opportunities)} opportunities:\n\n"
        for opp in opportunities:
            output += f"• [{opp['platform']}] {opp['type']} - Priority: {opp['priority']}\n"
            output += f"  Action: {opp['action_suggested']}\n"
        
        return output
    
    def _run_tests_tool(self, input_str: str) -> str:
        """Run project test suite tool"""
        if not self.selfimprove_plugin:
            return "❌ Self-improvement plugin not available"

        if input_str and input_str != 'all':
            modules = [input_str]
        else:
            modules = None

        result = self.selfimprove_plugin.run_test_suite(modules)
        if result.get('success'):
            return f"✅ Tests passed: {result['tests_run']} tests, 0 failures"
        elif result.get('error'):
            return f"❌ Test error: {result['error']}"
        else:
            return (
                f"❌ Tests failed: {result.get('tests_run', 0)} tests, "
                f"{result.get('failures', '?')} failures, "
                f"{result.get('errors', '?')} errors"
            )

    def _self_improve_tool(self, input_str: str) -> str:
        """Run self-improvement cycle tool"""
        if not self.selfimprove_plugin:
            return "❌ Self-improvement plugin not available"

        if input_str == 'ideas' and self.selfimprove_plugin.skill_workflow:
            ideas = self.selfimprove_plugin.skill_workflow.generate_skill_ideas()
            if not ideas:
                return "📭 No skill ideas generated"
            output = f"💡 {len(ideas)} skill ideas:\n"
            for idea in ideas[:5]:
                output += f"  • {idea.get('topic', '?')} (score: {idea.get('score', 0):.2f})\n"
            return output

        return self.selfimprove_plugin.improve_command()

    def _setup_initial_goals(self):
        """Set up initial hierarchical goals"""
        # Long-term goal
        long_term_goal = self.memory.add_goal(
            "Build strong on-chain reputation and community presence",
            goal_type='long_term',
            priority=3
        )
        
        # Short-term goals under long-term
        self.memory.add_goal(
            "Reach 1000 karma on Moltbook",
            goal_type='short_term',
            parent_goal_id=long_term_goal,
            priority=2
        )
        
        self.memory.add_goal(
            "Create 10 high-quality posts this week",
            goal_type='short_term',
            parent_goal_id=long_term_goal,
            priority=2
        )
        
        self.memory.add_goal(
            "Engage with 50 community members",
            goal_type='short_term',
            parent_goal_id=long_term_goal,
            priority=1
        )
        
        # Add to agent's goal stack
        self.agent.add_goal("Build karma on Moltbook")
        self.agent.add_goal("Engage proactively with community")
        self.agent.add_goal("Identify and fill capability gaps")
    
    def _execute_agent_task(self, task: str, on_chain_context: Optional[Dict] = None) -> Dict:
        """Execute agent task (used by scheduler)"""
        try:
            # Add task to memory
            self.memory.add_memory(
                f"Executing task: {task}",
                memory_type='interaction',
                metadata={'source': 'scheduler'}
            )
            
            # Run agent
            result = self.agent.run(task, on_chain_context)
            
            # Store result in memory
            if result['success']:
                self.memory.add_memory(
                    f"Task completed: {task}",
                    memory_type='learning',
                    metadata={'result': result}
                )
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_task(self, task: str, on_chain_context: Optional[Dict] = None) -> Dict:
        """
        Run a task with the agentic system
        
        Args:
            task: Task description
            on_chain_context: Optional on-chain context
            
        Returns:
            Task execution result
        """
        print(f"🎯 Running task: {task}")
        
        # Check for capability gaps
        available_tools = [t.name for t in self.tools]
        gap = self.skill_generator.identify_capability_gap(task, available_tools)
        
        if gap:
            print(f"🔍 Capability gap identified: {gap}")
            
            # Generate skill if needed
            skill_name = f"skill_{datetime.now().timestamp()}"
            result = self.skill_generator.generate_and_register_skill(
                gap, skill_name, is_on_chain='on-chain' in gap.lower()
            )
            
            if result['success']:
                print(f"✅ New skill generated: {skill_name}")
                # Reload tools
                self.tools = self._build_tools()
        
        # Execute task
        result = self._execute_agent_task(task, on_chain_context)
        
        # Get execution summary
        summary = self.agent.get_execution_summary()
        print(f"\n📊 Execution Summary:")
        print(f"  Iterations: {summary['total_iterations']}")
        print(f"  Actions: {summary['total_actions']}")
        print(f"  Success Rate: {summary['successful_actions']}/{summary['total_actions']}")
        
        return result
    
    def start_proactive_mode(self):
        """Start proactive autonomous behavior"""
        print("🚀 Starting proactive mode...")
        self.scheduler.start()
    
    def stop_proactive_mode(self):
        """Stop proactive behavior"""
        print("🛑 Stopping proactive mode...")
        self.scheduler.stop()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'memory': self.memory.get_memory_stats(),
            'security': self.security_filter.get_security_stats(),
            'approvals': self.approval_dashboard.get_approval_stats(),
            'scheduler': self.scheduler.get_job_status() if self.scheduler.enabled else {'enabled': False},
            'agent': self.agent.get_execution_summary(),
            'dynamic_skills': len(self.skill_generator.generated_skills),
            'tools': len(self.tools)
        }
    
    def prune_old_data(self, days: int = 30):
        """Prune old data from memory"""
        print(f"🧹 Pruning data older than {days} days...")
        self.memory.prune_old_memories(days)
        print("✅ Pruning complete")
    
