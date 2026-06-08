"""
Skill Executor
Execute skill instructions with tool access and script execution.

SKILL COMPOSITION: Skills can call other skills via self.call_skill() during execution.
This enables complex multi-skill workflows and emergent capabilities.
"""
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts with composition support"""

    def __init__(self, config):
        super().__init__(config)
        self.execution_log: List[Dict] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)
        self._composition_stack: List[str] = []  # Track nested skill calls
        self._max_composition_depth = 5  # Prevent infinite recursion
        self._composition_results: Dict[str, Any] = {}  # Store intermediate results

    def execute_skill(self, skill_name: str, task: str, context: str = "") -> Dict[str, Any]:
        """
        Execute a skill with given task and context.
        
        SKILL COMPOSITION: Skills can call other skills via the injected
        `call_skill()` method, enabling complex multi-skill workflows.
        """
        #