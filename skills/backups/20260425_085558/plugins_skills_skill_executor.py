"""
Skill Executor
Execute skill instructions with tool access and script execution.

SKILL COMPOSITION: Skills can call other skills via self.call_skill() during execution.
This enables complex multi-skill workflows and emergent capabilities.
"""
import os
import subprocess
import sys
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from plugin_manager import AlleyBotPlugin


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts with composition support"""

    def __init__(self, config):
        self.config = config
        self.execution_log: List[Dict] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)
        self._composition_stack: List[str] = []  # Track nested skill calls
        self._max_composition_depth = 5  # Prevent infinite recursion
        self._composition_results: Dict