"""
Global Command Registry - Systematic awareness of all 412+ commands

This module provides AlleyBot with complete awareness of his own capabilities.
Before attempting to solve a problem, he can search his entire command library
to see if he already has the tool to solve it.

Part of Sovereignty Enhancement - Phase 1: Global Plugin Awareness
"""

import inspect
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommandMetadata:
    """Metadata for a single command"""
    command_id: str  # e.g., "moltx.create_post"
    plugin: str
    function_name: str
    description: str
    parameters: List[str]
    domain: str  # social, trading, analysis, etc.
    risk_level: str  # low, medium, high
    requires_auth: bool
    example_usage: Optional[str] = None
    related_commands: List[str] = None
    
    def __post_init__(self):
        if self.related_commands is None:
            self.related_commands = []


class GlobalCommandRegistry:
    """
    Centralized registry of all commands across the plugin ecosystem.
    
    Provides:
    - Semantic search across all commands
    - Domain-based filtering
    - Capability discovery
    - Command metadata and documentation
    """
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        self.commands: Dict[str, CommandMetadata] = {}
        self.embeddings: Dict[str, Any] = {}
        self.sentence_model = None
        
        # Domain classification keywords
        self.domain_keywords = {
            'social': ['post', 'reply', 'comment', 'engage', 'follow', 'like', 'debate', 'mention'],
            'trading': ['swap', 'trade', 'buy', 'sell', 'price', 'quote', 'liquidity', 'yield'],
            'analysis': ['analyze', 'check', 'monitor', 'track', 'report', 'stats', 'metrics'],
            'content': ['generate', 'create', 'write', 'compose', 'draft'],
            'blockchain': ['wallet', 'balance', 'transaction', 'token', 'contract', 'onchain'],
            'self_improvement': ['improve', 'fix', 'upgrade', 'optimize', 'learn', 'skill'],
        }
        
        logger.info("🗂️ Global Command Registry initialized")
    
    def scan_all_plugins(self) -> int:
        """
        Scan all loaded plugins and catalog their commands.
        
        Returns:
            Number of commands discovered
        """
        if not self.plugin_manager:
            logger.warning("No plugin manager available, skipping scan")
            return 0
        
        logger.info("🔍 Scanning plugin ecosystem for commands...")
        
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            self._scan_plugin(plugin_name, plugin)
        
        logger.info(f"✅ Discovered {len(self.commands)} commands across {len(self.plugin_manager.plugins)} plugins")
        return len(self.commands)
    
    def _scan_plugin(self, plugin_name: str, plugin: Any):
        """Scan a single plugin for commands"""
        try:
            # Get all methods from plugin
            for name, method in inspect.getmembers(plugin, predicate=inspect.ismethod):
                # Skip private methods and inherited methods
                if name.startswith('_'):
                    continue
                
                # Check if it's a command (has specific patterns)
                if self._is_command(name, method):
                    metadata = self._extract_metadata(plugin_name, name, method)
                    command_id = f"{plugin_name}.{name}"
                    self.commands[command_id] = metadata
                    
        except Exception as e:
            logger.debug(f"Error scanning plugin {plugin_name}: {e}")
    
    def _is_command(self, name: str, method: Callable) -> bool:
        """Determine if a method is a command"""
        # Commands typically end with _command or are in get_commands()
        if name.endswith('_command'):
            return True
        
        # Check if method is callable and not a property
        if not callable(method):
            return False
        
        # Check docstring for command indicators
        doc = inspect.getdoc(method)
        if doc and any(keyword in doc.lower() for keyword in ['command', 'usage:', 'execute']):
            return True
        
        return False
    
    def _extract_metadata(self, plugin_name: str, function_name: str, method: Callable) -> CommandMetadata:
        """Extract metadata from a command method"""
        # Get docstring
        doc = inspect.getdoc(method) or "No description available"
        
        # Get parameters
        sig = inspect.signature(method)
        params = [p for p in sig.parameters.keys() if p not in ['self', 'args', 'kwargs']]
        
        # Classify domain
        domain = self._classify_domain(function_name, doc)
        
        # Determine risk level
        risk_level = self._determine_risk_level(plugin_name, function_name, domain)
        
        # Check if requires auth
        requires_auth = 'owner' in doc.lower() or 'admin' in doc.lower()
        
        return CommandMetadata(
            command_id=f"{plugin_name}.{function_name}",
            plugin=plugin_name,
            function_name=function_name,
            description=doc.split('\n')[0] if doc else "No description",
            parameters=params,
            domain=domain,
            risk_level=risk_level,
            requires_auth=requires_auth,
        )
    
    def _classify_domain(self, function_name: str, doc: str) -> str:
        """Classify command into a domain"""
        text = f"{function_name} {doc}".lower()
        
        scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[domain] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return 'general'
    
    def _determine_risk_level(self, plugin_name: str, function_name: str, domain: str) -> str:
        """Determine risk level of a command"""
        # High risk: trading, wallet operations, self-improvement
        high_risk_domains = ['trading', 'blockchain', 'self_improvement']
        high_risk_keywords = ['swap', 'trade', 'send', 'transfer', 'delete', 'fix', 'upgrade']
        
        if domain in high_risk_domains:
            return 'high'
        
        if any(keyword in function_name.lower() for keyword in high_risk_keywords):
            return 'high'
        
        # Medium risk: social posting, content creation
        medium_risk_domains = ['social', 'content']
        if domain in medium_risk_domains:
            return 'medium'
        
        # Low risk: analysis, monitoring
        return 'low'
    
    def search(self, query: str, domain: Optional[str] = None, max_results: int = 10) -> List[CommandMetadata]:
        """
        Search for commands using semantic similarity.
        
        Args:
            query: Natural language description of what you want to do
            domain: Optional domain filter (social, trading, etc.)
            max_results: Maximum number of results to return
        
        Returns:
            List of matching commands, ranked by relevance
        """
        # Filter by domain if specified
        candidates = list(self.commands.values())
        if domain:
            candidates = [cmd for cmd in candidates if cmd.domain == domain]
        
        if not candidates:
            return []
        
        # Simple keyword matching (will be enhanced with sentence transformers)
        query_lower = query.lower()
        scored_commands = []
        
        for cmd in candidates:
            score = 0
            
            # Check function name
            if any(word in cmd.function_name.lower() for word in query_lower.split()):
                score += 3
            
            # Check description
            if any(word in cmd.description.lower() for word in query_lower.split()):
                score += 2
            
            # Check domain match
            if cmd.domain in query_lower:
                score += 1
            
            if score > 0:
                scored_commands.append((score, cmd))
        
        # Sort by score and return top results
        scored_commands.sort(reverse=True, key=lambda x: x[0])
        return [cmd for score, cmd in scored_commands[:max_results]]
    
    def search_semantic(self, query: str, domain: Optional[str] = None, top_k: int = 5) -> List[CommandMetadata]:
        """
        Search using sentence transformers for better semantic matching.
        
        This will be the primary search method once embeddings are generated.
        """
        # Load sentence transformer model if not already loaded
        if not self.sentence_model:
            try:
                from plugins.telegram.intent_classifier import get_sentence_model
                self.sentence_model = get_sentence_model()
            except Exception as e:
                logger.debug(f"Sentence model not available: {e}")
                # Fallback to keyword search
                return self.search(query, domain, top_k)
        
        # Filter by domain
        candidates = list(self.commands.values())
        if domain:
            candidates = [cmd for cmd in candidates if cmd.domain == domain]
        
        if not candidates:
            return []
        
        # Generate embeddings for query and commands
        try:
            query_embedding = self.sentence_model.encode([query])[0]
            
            # Get or generate command embeddings
            command_texts = [f"{cmd.function_name} {cmd.description}" for cmd in candidates]
            command_embeddings = self.sentence_model.encode(command_texts)
            
            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity([query_embedding], command_embeddings)[0]
            
            # Rank by similarity
            ranked_indices = similarities.argsort()[::-1][:top_k]
            
            return [candidates[i] for i in ranked_indices if similarities[i] > 0.3]
            
        except Exception as e:
            logger.debug(f"Semantic search failed: {e}")
            # Fallback to keyword search
            return self.search(query, domain, top_k)
    
    def get_by_domain(self, domain: str) -> List[CommandMetadata]:
        """Get all commands for a specific domain"""
        return [cmd for cmd in self.commands.values() if cmd.domain == domain]
    
    def get_by_plugin(self, plugin_name: str) -> List[CommandMetadata]:
        """Get all commands for a specific plugin"""
        return [cmd for cmd in self.commands.values() if cmd.plugin == plugin_name]
    
    def get_command(self, command_id: str) -> Optional[CommandMetadata]:
        """Get metadata for a specific command"""
        return self.commands.get(command_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        domain_counts = {}
        risk_counts = {}
        
        for cmd in self.commands.values():
            domain_counts[cmd.domain] = domain_counts.get(cmd.domain, 0) + 1
            risk_counts[cmd.risk_level] = risk_counts.get(cmd.risk_level, 0) + 1
        
        return {
            'total_commands': len(self.commands),
            'total_plugins': len(set(cmd.plugin for cmd in self.commands.values())),
            'by_domain': domain_counts,
            'by_risk_level': risk_counts,
        }
    
    def find_capability_gaps(self, required_capability: str) -> Dict[str, Any]:
        """
        Determine if AlleyBot has the capability to do something.
        
        Returns:
            {
                'has_capability': bool,
                'matching_commands': List[CommandMetadata],
                'suggested_skill': Optional[str]  # If gap exists
            }
        """
        matches = self.search_semantic(required_capability, top_k=3)
        
        if matches and len(matches) > 0:
            return {
                'has_capability': True,
                'matching_commands': matches,
                'suggested_skill': None
            }
        else:
            return {
                'has_capability': False,
                'matching_commands': [],
                'suggested_skill': f"auto_skill_{required_capability.replace(' ', '_')}"
            }


# Singleton instance
_registry: Optional[GlobalCommandRegistry] = None


def get_command_registry(plugin_manager=None) -> GlobalCommandRegistry:
    """Get or create the global command registry"""
    global _registry
    if _registry is None:
        _registry = GlobalCommandRegistry(plugin_manager)
        if plugin_manager:
            _registry.scan_all_plugins()
    return _registry


def create_command_registry(plugin_manager) -> GlobalCommandRegistry:
    """Create and initialize the command registry"""
    registry = GlobalCommandRegistry(plugin_manager)
    registry.scan_all_plugins()
    return registry
