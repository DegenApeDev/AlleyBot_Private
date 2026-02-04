"""
Agentic System for AlleyBot
Enhanced autonomous capabilities with LangChain ReAct, dynamic skills, and vector memory
"""

from src.agentic.agentic_system import AgenticAlleyBot
from src.agentic.react_agent import EnhancedReActAgent, AgentState
from src.agentic.event_scheduler import ProactiveAgentScheduler
from src.agentic.skill_generator import DynamicSkillGenerator
from src.agentic.enhanced_memory import EnhancedMemorySystem
from src.agentic.security_filter import SecurityFilter
from src.agentic.approval_dashboard import ApprovalDashboard
from src.agentic.skill_updater import SkillUpdater
from src.agentic.api_monitor import monitor_api_response

__all__ = [
    'AgenticAlleyBot',
    'EnhancedReActAgent',
    'AgentState',
    'ProactiveAgentScheduler',
    'DynamicSkillGenerator',
    'EnhancedMemorySystem',
    'SecurityFilter',
    'ApprovalDashboard',
    'SkillUpdater',
    'monitor_api_response'
]

__version__ = '2.0.0'
