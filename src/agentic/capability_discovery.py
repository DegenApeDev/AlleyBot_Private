"""
Capability Discovery - Intelligent command search before taking action

This module enables AlleyBot to search his entire command library before
attempting to solve a problem or generate new code. Prevents reinventing
the wheel when a capability already exists.

Part of Sovereignty Enhancement - Phase 1: Global Plugin Awareness
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .command_registry import get_command_registry, CommandMetadata

logger = logging.getLogger(__name__)


@dataclass
class CapabilityGap:
    """Represents a gap in AlleyBot's capabilities"""
    required_capability: str
    gap_type: str  # 'missing_command', 'missing_plugin', 'needs_new_skill'
    suggested_commands: List[CommandMetadata]
    suggested_skill_name: Optional[str] = None
    confidence: float = 0.0


class CapabilityDiscovery:
    """
    Intelligent capability discovery system.
    
    Before AlleyBot attempts to solve a problem:
    1. Search existing 412+ commands
    2. Identify if capability already exists
    3. If not, suggest skill generation
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.command_registry = None
        logger.info("🔍 Capability Discovery initialized")
    
    def _ensure_registry(self):
        """Ensure command registry is available"""
        if not self.command_registry:
            self.command_registry = get_command_registry(
                self.agi.core.plugin_manager if self.agi.core else None
            )
    
    def find_capability(self, intent: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for existing capabilities that match the intent.
        
        Args:
            intent: Natural language description of what needs to be done
            domain: Optional domain filter (social, trading, etc.)
        
        Returns:
            {
                'has_capability': bool,
                'commands': List[CommandMetadata],
                'gap': Optional[CapabilityGap],
                'recommendation': str
            }
        """
        self._ensure_registry()
        
        # Search for matching commands
        matches = self.command_registry.search_semantic(intent, domain=domain, top_k=5)
        
        if matches and len(matches) > 0:
            # Found existing capabilities
            return {
                'has_capability': True,
                'commands': matches,
                'gap': None,
                'recommendation': f"Use existing command: {matches[0].command_id}"
            }
        else:
            # No existing capability found
            gap = CapabilityGap(
                required_capability=intent,
                gap_type='missing_command',
                suggested_commands=[],
                suggested_skill_name=f"auto_{intent.replace(' ', '_')[:30]}",
                confidence=0.0
            )
            
            return {
                'has_capability': False,
                'commands': [],
                'gap': gap,
                'recommendation': f"Generate new skill: {gap.suggested_skill_name}"
            }
    
    def analyze_problem(self, problem: str) -> Dict[str, Any]:
        """
        Analyze a problem and determine the best approach.
        
        Returns:
            {
                'approach': str,  # 'use_existing', 'combine_commands', 'generate_skill'
                'commands': List[CommandMetadata],
                'workflow': Optional[List[str]],  # Sequence of commands
                'confidence': float
            }
        """
        self._ensure_registry()
        
        # Search for relevant commands
        matches = self.command_registry.search_semantic(problem, top_k=10)
        
        if not matches:
            return {
                'approach': 'generate_skill',
                'commands': [],
                'workflow': None,
                'confidence': 0.0
            }
        
        # Check if single command can solve it
        if len(matches) > 0 and self._is_direct_match(matches[0], problem):
            return {
                'approach': 'use_existing',
                'commands': [matches[0]],
                'workflow': [matches[0].command_id],
                'confidence': 0.9
            }
        
        # Check if combination of commands can solve it
        workflow = self._build_workflow(matches, problem)
        if workflow:
            return {
                'approach': 'combine_commands',
                'commands': matches[:len(workflow)],
                'workflow': workflow,
                'confidence': 0.7
            }
        
        # Need to generate new skill
        return {
            'approach': 'generate_skill',
            'commands': matches,  # Related commands for reference
            'workflow': None,
            'confidence': 0.5
        }
    
    def _is_direct_match(self, command: CommandMetadata, problem: str) -> bool:
        """Check if a command directly solves the problem"""
        # Simple heuristic: check if key words match
        problem_words = set(problem.lower().split())
        command_words = set(command.function_name.lower().split('_'))
        command_words.update(command.description.lower().split())
        
        overlap = len(problem_words & command_words)
        return overlap >= min(3, len(problem_words) * 0.5)
    
    def _build_workflow(self, commands: List[CommandMetadata], problem: str) -> Optional[List[str]]:
        """
        Attempt to build a workflow from multiple commands.
        
        This is a simple heuristic - will be enhanced with better planning.
        """
        # For now, return None (workflow building not implemented)
        # This will be enhanced in Priority 2: Cross-Plugin Orchestrator
        return None
    
    def get_domain_capabilities(self, domain: str) -> Dict[str, Any]:
        """Get all capabilities for a specific domain"""
        self._ensure_registry()
        
        commands = self.command_registry.get_by_domain(domain)
        
        return {
            'domain': domain,
            'total_commands': len(commands),
            'commands': commands,
            'plugins': list(set(cmd.plugin for cmd in commands))
        }
    
    def suggest_related_commands(self, command_id: str, top_k: int = 5) -> List[CommandMetadata]:
        """Suggest commands related to a given command"""
        self._ensure_registry()
        
        command = self.command_registry.get_command(command_id)
        if not command:
            return []
        
        # Search for similar commands
        query = f"{command.function_name} {command.description}"
        matches = self.command_registry.search_semantic(query, top_k=top_k + 1)
        
        # Filter out the original command
        return [cmd for cmd in matches if cmd.command_id != command_id][:top_k]


# Singleton instance
_capability_discovery: Optional[CapabilityDiscovery] = None


def get_capability_discovery(agi_kernel) -> CapabilityDiscovery:
    """Get or create capability discovery system"""
    global _capability_discovery
    if _capability_discovery is None:
        _capability_discovery = CapabilityDiscovery(agi_kernel)
    return _capability_discovery


def create_capability_discovery(agi_kernel) -> CapabilityDiscovery:
    """Create capability discovery system"""
    return CapabilityDiscovery(agi_kernel)
