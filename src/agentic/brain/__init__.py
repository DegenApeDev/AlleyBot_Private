"""
Brain Module - Modular brain phase components

Extracts autonomous_brain.py into focused modules:
- sense.py: Observation gathering, platform polling
- think.py: Goal generation, belief evaluation, planning  
- validate.py: Moderation, safety gates, HITL
- act.py: Action execution, outcome recording
- learn.py: Reflection, metacognition, belief update
- self_improve.py: Skill gap detection, code generation
- trading.py: Market analysis, position management
- cycle_coordinator.py: Orchestrates all phases
"""

from .sense import BrainSense, create_brain_sense
from .think import BrainThink, create_brain_think
from .validate import BrainValidate, create_brain_validate
from .act import BrainAct, create_brain_act
from .learn import BrainLearn, create_brain_learn
from .self_improve import BrainSelfImprove, create_brain_self_improve
from .trading import BrainTrading, create_brain_trading
from .cycle_coordinator import CycleCoordinator, create_cycle_coordinator

__all__ = [
    'BrainSense',
    'BrainThink', 
    'BrainValidate',
    'BrainAct',
    'BrainLearn',
    'BrainSelfImprove',
    'BrainTrading',
    'CycleCoordinator',
    'create_brain_sense',
    'create_brain_think',
    'create_brain_validate',
    'create_brain_act',
    'create_brain_learn',
    'create_brain_self_improve',
    'create_brain_trading',
    'create_cycle_coordinator',
]