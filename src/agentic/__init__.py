"""
Agentic System for AlleyBot
Enhanced autonomous capabilities with security and on-chain focus
"""

from .agentic_system import AgenticAlleyBot
from .react_agent import EnhancedReActAgent, AgentState
from .event_scheduler import ProactiveAgentScheduler, OnChainOpportunityDetector
from .skill_generator import DynamicSkillGenerator
from .enhanced_memory import EnhancedMemorySystem
from .security_filter import SecurityFilter, RiskLevel
from .approval_dashboard import ApprovalDashboard, TelegramApprovalHandler

__all__ = [
    'AgenticAlleyBot',
    'EnhancedReActAgent',
    'AgentState',
    'ProactiveAgentScheduler',
    'OnChainOpportunityDetector',
    'DynamicSkillGenerator',
    'EnhancedMemorySystem',
    'SecurityFilter',
    'RiskLevel',
    'ApprovalDashboard',
    'TelegramApprovalHandler'
]

__version__ = '2.0.0'
