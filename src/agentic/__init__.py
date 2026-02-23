"""
Agentic System for AlleyBot
Enhanced autonomous capabilities with LangChain ReAct, dynamic skills, and vector memory
"""

try:
    from src.agentic.agentic_system import AgenticAlleyBot
    from src.agentic.react_agent import EnhancedReActAgent, AgentState
    from src.agentic.event_scheduler import ProactiveAgentScheduler
    from src.agentic.skill_generator import DynamicSkillGenerator
    from src.agentic.enhanced_memory import EnhancedMemorySystem
    from src.agentic.security_filter import SecurityFilter
    from src.agentic.approval_dashboard import ApprovalDashboard
except ImportError:
    pass

__all__ = [
    'AgenticAlleyBot',
    'EnhancedReActAgent',
    'AgentState',
    'ProactiveAgentScheduler',
    'DynamicSkillGenerator',
    'EnhancedMemorySystem',
    'SecurityFilter',
    'ApprovalDashboard',
]

__version__ = '2.0.0'
