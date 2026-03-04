"""
Transfer Learning Engine for AlleyBot AGI
Identifies patterns across domains and applies successful strategies to new contexts
Enables true generalization - the hallmark of AGI
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A pattern identified in a domain"""
    id: str
    name: str
    domain: str  # Source domain
    description: str
    structure: Dict[str, Any]  # Abstract structure of pattern
    success_rate: float = 0.0  # How successful this pattern is
    applications: int = 0  # Number of times applied
    examples: List[str] = field(default_factory=list)


@dataclass
class TransferMapping:
    """Mapping of a pattern from source to target domain"""
    source_pattern: Pattern
    target_domain: str
    adapted_pattern: Dict[str, Any]
    confidence: float  # Confidence in transfer (0-1)
    reasoning: str  # Why this transfer makes sense


class TransferLearner:
    """
    Transfer Learning Engine - Apply knowledge across domains
    
    Core capability of AGI: Learn in one domain, apply to another
    
    Examples:
    - Chess tactics → Trading strategies
    - Social engagement → Content strategy
    - Planning patterns → Goal decomposition
    
    This is what makes AlleyBot truly general intelligence.
    """
    
    def __init__(self, knowledge_graph=None):
        """
        Initialize transfer learning engine
        
        Args:
            knowledge_graph: Unified knowledge representation
        """
        self.knowledge_graph = knowledge_graph
        
        # Pattern library
        self.patterns: Dict[str, Pattern] = {}
        
        # Transfer history
        self.transfer_history: List[TransferMapping] = []
        
        # Domain similarity cache
        self.domain_similarity: Dict[Tuple[str, str], float] = {}
        
        # Initialize with known patterns
        self._init_core_patterns()
        
        logger.info("✅ Transfer Learning Engine initialized")
    
    def _init_core_patterns(self):
        """Initialize core patterns that can transfer across domains"""
        
        # Pattern: Control Center, Attack Flanks (Chess → Trading → Social)
        self.add_pattern(Pattern(
            id="pattern_center_control",
            name="Control Center, Attack Flanks",
            domain="chess",
            description="Establish strong position in center, then expand to edges",
            structure={
                'phase1': 'establish_core_position',
                'phase2': 'strengthen_core',
                'phase3': 'expand_to_periphery',
                'principle': 'secure_foundation_before_expansion'
            },
            success_rate=0.85,
            examples=[
                "Chess: Control d4/e4, then attack kingside",
                "Trading: Build 60% core position, diversify to alts",
                "Social: Build engagement base, then post content"
            ]
        ))
        
        # Pattern: Sacrifice for Position (Chess → Trading → Social)
        self.add_pattern(Pattern(
            id="pattern_sacrifice_position",
            name="Sacrifice for Position",
            domain="chess",
            description="Accept short-term loss for long-term advantage",
            structure={
                'action': 'accept_small_loss',
                'goal': 'gain_strategic_advantage',
                'timeframe': 'short_term_loss_long_term_gain',
                'principle': 'strategic_sacrifice'
            },
            success_rate=0.78,
            examples=[
                "Chess: Sacrifice pawn for better piece placement",
                "Trading: Take small loss to reposition portfolio",
                "Social: Spend time engaging (cost) to build audience"
            ]
        ))
        
        # Pattern: Timing is Everything
        self.add_pattern(Pattern(
            id="pattern_optimal_timing",
            name="Optimal Timing",
            domain="general",
            description="Success depends on when action is taken",
            structure={
                'analyze': 'assess_conditions',
                'wait': 'wait_for_optimal_moment',
                'act': 'execute_when_conditions_right',
                'principle': 'timing_over_action'
            },
            success_rate=0.82,
            examples=[
                "Chess: Move when opponent is weak",
                "Trading: Buy when market dips",
                "Social: Post when audience is active",
                "Planning: Act when resources are ready"
            ]
        ))
        
        # Pattern: Momentum Exploitation
        self.add_pattern(Pattern(
            id="pattern_momentum",
            name="Ride the Momentum",
            domain="general",
            description="Capitalize on existing momentum rather than fighting it",
            structure={
                'identify': 'detect_momentum',
                'align': 'align_with_direction',
                'amplify': 'amplify_momentum',
                'principle': 'flow_with_energy'
            },
            success_rate=0.80,
            examples=[
                "Chess: Press advantage when opponent is defensive",
                "Trading: Follow trend, don't fight it",
                "Social: Engage with trending topics",
                "Content: Build on successful themes"
            ]
        ))
        
        # Pattern: Diversification
        self.add_pattern(Pattern(
            id="pattern_diversification",
            name="Diversification",
            domain="general",
            description="Spread risk across multiple options",
            structure={
                'avoid': 'single_point_of_failure',
                'spread': 'distribute_across_options',
                'balance': 'maintain_portfolio_balance',
                'principle': 'risk_distribution'
            },
            success_rate=0.88,
            examples=[
                "Chess: Develop multiple pieces, not just one",
                "Trading: Hold multiple tokens, not just one",
                "Social: Post on multiple platforms",
                "Skills: Learn multiple domains"
            ]
        ))
        
        logger.info(f"✅ Initialized {len(self.patterns)} core patterns")
    
    def add_pattern(self, pattern: Pattern):
        """Add a pattern to the library"""
        self.patterns[pattern.id] = pattern
        logger.debug(f"Added pattern: {pattern.name}")
    
    def identify_pattern(self, domain: str, observations: List[Dict[str, Any]]) -> Optional[Pattern]:
        """
        Identify patterns in observations from a domain
        
        Args:
            domain: Domain to analyze
            observations: List of observations/events
            
        Returns:
            Identified pattern or None
        """
        # Analyze observations for recurring structures
        structures = self._extract_structures(observations)
        
        # Match against known patterns
        for pattern in self.patterns.values():
            if self._matches_pattern(structures, pattern.structure):
                logger.info(f"✅ Identified pattern: {pattern.name} in {domain}")
                return pattern
        
        # No known pattern found - could create new one
        return None
    
    def transfer_pattern(self, pattern_id: str, target_domain: str, context: Dict[str, Any] = None) -> Optional[TransferMapping]:
        """
        Transfer a pattern from source domain to target domain
        
        Args:
            pattern_id: ID of pattern to transfer
            target_domain: Domain to transfer to
            context: Additional context for transfer
            
        Returns:
            Transfer mapping with adapted pattern
        """
        if pattern_id not in self.patterns:
            logger.warning(f"⚠️ Pattern {pattern_id} not found")
            return None
        
        source_pattern = self.patterns[pattern_id]
        
        logger.info(f"🔄 Transferring pattern '{source_pattern.name}' from {source_pattern.domain} to {target_domain}")
        
        # Adapt pattern to target domain
        adapted = self._adapt_pattern(source_pattern, target_domain, context)
        
        # Calculate transfer confidence
        confidence = self._calculate_transfer_confidence(source_pattern, target_domain)
        
        # Generate reasoning
        reasoning = self._explain_transfer(source_pattern, target_domain, adapted)
        
        transfer = TransferMapping(
            source_pattern=source_pattern,
            target_domain=target_domain,
            adapted_pattern=adapted,
            confidence=confidence,
            reasoning=reasoning
        )
        
        # Record transfer
        self.transfer_history.append(transfer)
        
        logger.info(f"✅ Transfer complete (confidence: {confidence:.2f})")
        
        return transfer
    
    def find_applicable_patterns(self, domain: str, problem: str) -> List[Tuple[Pattern, float]]:
        """
        Find patterns from other domains applicable to current problem
        
        Args:
            domain: Current domain
            problem: Problem description
            
        Returns:
            List of (pattern, relevance_score) tuples
        """
        applicable = []
        
        for pattern in self.patterns.values():
            # Skip patterns from same domain (not transfer learning)
            if pattern.domain == domain:
                continue
            
            # Calculate relevance
            relevance = self._calculate_relevance(pattern, domain, problem)
            
            if relevance > 0.5:  # Threshold for applicability
                applicable.append((pattern, relevance))
        
        # Sort by relevance
        applicable.sort(key=lambda x: x[1], reverse=True)
        
        return applicable
    
    def _adapt_pattern(self, pattern: Pattern, target_domain: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Adapt pattern structure to target domain"""
        adapted = {}
        
        # Map abstract structure to domain-specific implementation
        structure = pattern.structure
        
        if target_domain == "trading":
            adapted = self._adapt_to_trading(structure)
        elif target_domain == "social":
            adapted = self._adapt_to_social(structure)
        elif target_domain == "planning":
            adapted = self._adapt_to_planning(structure)
        elif target_domain == "chess":
            adapted = self._adapt_to_chess(structure)
        else:
            # Generic adaptation
            adapted = structure.copy()
        
        return adapted
    
    def _adapt_to_trading(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt pattern to trading domain"""
        adapted = {}
        
        # Map abstract concepts to trading concepts
        mapping = {
            'establish_core_position': 'build_primary_holdings',
            'strengthen_core': 'increase_core_allocation',
            'expand_to_periphery': 'diversify_to_altcoins',
            'accept_small_loss': 'take_stop_loss',
            'gain_strategic_advantage': 'reposition_portfolio',
            'assess_conditions': 'analyze_market',
            'wait_for_optimal_moment': 'wait_for_dip',
            'execute_when_conditions_right': 'execute_trade'
        }
        
        for key, value in structure.items():
            if isinstance(value, str) and value in mapping:
                adapted[key] = mapping[value]
            else:
                adapted[key] = value
        
        return adapted
    
    def _adapt_to_social(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt pattern to social domain"""
        adapted = {}
        
        mapping = {
            'establish_core_position': 'build_engagement_base',
            'strengthen_core': 'increase_engagement',
            'expand_to_periphery': 'post_content',
            'accept_small_loss': 'spend_time_engaging',
            'gain_strategic_advantage': 'build_audience',
            'assess_conditions': 'check_audience_activity',
            'wait_for_optimal_moment': 'wait_for_peak_hours',
            'execute_when_conditions_right': 'post_content'
        }
        
        for key, value in structure.items():
            if isinstance(value, str) and value in mapping:
                adapted[key] = mapping[value]
            else:
                adapted[key] = value
        
        return adapted
    
    def _adapt_to_planning(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt pattern to planning domain"""
        adapted = {}
        
        mapping = {
            'establish_core_position': 'secure_foundation',
            'strengthen_core': 'build_capabilities',
            'expand_to_periphery': 'expand_scope',
            'accept_small_loss': 'invest_resources',
            'gain_strategic_advantage': 'achieve_strategic_goal',
            'assess_conditions': 'evaluate_resources',
            'wait_for_optimal_moment': 'wait_for_readiness',
            'execute_when_conditions_right': 'execute_plan'
        }
        
        for key, value in structure.items():
            if isinstance(value, str) and value in mapping:
                adapted[key] = mapping[value]
            else:
                adapted[key] = value
        
        return adapted
    
    def _adapt_to_chess(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt pattern to chess domain"""
        adapted = {}
        
        mapping = {
            'establish_core_position': 'control_center',
            'strengthen_core': 'develop_pieces',
            'expand_to_periphery': 'attack_flanks',
            'accept_small_loss': 'sacrifice_material',
            'gain_strategic_advantage': 'improve_position',
            'assess_conditions': 'evaluate_position',
            'wait_for_optimal_moment': 'wait_for_weakness',
            'execute_when_conditions_right': 'execute_tactic'
        }
        
        for key, value in structure.items():
            if isinstance(value, str) and value in mapping:
                adapted[key] = mapping[value]
            else:
                adapted[key] = value
        
        return adapted
    
    def _calculate_transfer_confidence(self, pattern: Pattern, target_domain: str) -> float:
        """Calculate confidence in pattern transfer"""
        confidence = 0.5  # Base confidence
        
        # Boost if pattern has high success rate
        confidence += pattern.success_rate * 0.3
        
        # Boost if pattern has been applied many times
        if pattern.applications > 10:
            confidence += 0.1
        
        # Boost if domains are similar
        similarity = self._get_domain_similarity(pattern.domain, target_domain)
        confidence += similarity * 0.2
        
        # Cap at 0.95 (never 100% certain)
        return min(confidence, 0.95)
    
    def _get_domain_similarity(self, domain1: str, domain2: str) -> float:
        """Get similarity between two domains"""
        key = tuple(sorted([domain1, domain2]))
        
        if key in self.domain_similarity:
            return self.domain_similarity[key]
        
        # Calculate similarity
        similarity = self._calculate_domain_similarity(domain1, domain2)
        self.domain_similarity[key] = similarity
        
        return similarity
    
    def _calculate_domain_similarity(self, domain1: str, domain2: str) -> float:
        """Calculate similarity between domains"""
        # Use knowledge graph if available
        if self.knowledge_graph:
            analogies = self.knowledge_graph.find_analogies(domain1, domain2)
            if analogies:
                # Average similarity of top analogies
                top_analogies = analogies[:5]
                avg_similarity = sum(a['similarity'] for a in top_analogies) / len(top_analogies)
                return avg_similarity
        
        # Fallback: Simple heuristic
        similar_pairs = [
            ('chess', 'trading'),
            ('chess', 'planning'),
            ('trading', 'social'),
            ('social', 'content'),
        ]
        
        pair = tuple(sorted([domain1, domain2]))
        if pair in similar_pairs:
            return 0.7
        
        return 0.3  # Default low similarity
    
    def _calculate_relevance(self, pattern: Pattern, domain: str, problem: str) -> float:
        """Calculate relevance of pattern to problem"""
        relevance = 0.0
        
        # Check if pattern principle appears in problem
        principle = pattern.structure.get('principle', '')
        if principle:
            # Simple keyword matching (can be enhanced with semantic similarity)
            keywords = re.findall(r'\w+', principle.lower())
            problem_lower = problem.lower()
            
            matches = sum(1 for kw in keywords if kw in problem_lower)
            relevance += (matches / len(keywords)) * 0.5 if keywords else 0
        
        # Boost if pattern has high success rate
        relevance += pattern.success_rate * 0.3
        
        # Boost if domains are similar
        similarity = self._get_domain_similarity(pattern.domain, domain)
        relevance += similarity * 0.2
        
        return min(relevance, 1.0)
    
    def _explain_transfer(self, pattern: Pattern, target_domain: str, adapted: Dict[str, Any]) -> str:
        """Generate explanation of why transfer makes sense"""
        explanation = f"Transferring '{pattern.name}' from {pattern.domain} to {target_domain}:\n\n"
        explanation += f"Original principle: {pattern.structure.get('principle', 'N/A')}\n\n"
        explanation += f"Adaptation:\n"
        
        for key, value in adapted.items():
            original = pattern.structure.get(key, 'N/A')
            explanation += f"  {key}: {original} → {value}\n"
        
        explanation += f"\nThis transfer makes sense because the underlying strategic principle remains valid across domains."
        
        return explanation
    
    def _extract_structures(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract abstract structures from observations"""
        structures = []
        
        for obs in observations:
            structure = {
                'type': obs.get('type'),
                'action': obs.get('action'),
                'outcome': obs.get('outcome'),
                'success': obs.get('success', False)
            }
            structures.append(structure)
        
        return structures
    
    def _matches_pattern(self, structures: List[Dict[str, Any]], pattern_structure: Dict[str, Any]) -> bool:
        """Check if observed structures match a pattern"""
        # Simple matching - can be enhanced with more sophisticated pattern matching
        if not structures:
            return False
        
        # Check if key elements of pattern appear in structures
        pattern_keys = set(pattern_structure.keys())
        structure_keys = set()
        
        for struct in structures:
            structure_keys.update(struct.keys())
        
        # At least 50% overlap
        overlap = len(pattern_keys.intersection(structure_keys))
        return overlap >= len(pattern_keys) * 0.5
    
    def get_transfer_statistics(self) -> Dict[str, Any]:
        """Get statistics about transfer learning"""
        return {
            'total_patterns': len(self.patterns),
            'total_transfers': len(self.transfer_history),
            'patterns_by_domain': self._count_patterns_by_domain(),
            'average_transfer_confidence': self._average_transfer_confidence(),
            'most_transferred_pattern': self._most_transferred_pattern()
        }
    
    def _count_patterns_by_domain(self) -> Dict[str, int]:
        """Count patterns by source domain"""
        counts = defaultdict(int)
        for pattern in self.patterns.values():
            counts[pattern.domain] += 1
        return dict(counts)
    
    def _average_transfer_confidence(self) -> float:
        """Calculate average confidence of transfers"""
        if not self.transfer_history:
            return 0.0
        
        total = sum(t.confidence for t in self.transfer_history)
        return total / len(self.transfer_history)
    
    def _most_transferred_pattern(self) -> Optional[str]:
        """Find most frequently transferred pattern"""
        if not self.transfer_history:
            return None
        
        counts = defaultdict(int)
        for transfer in self.transfer_history:
            counts[transfer.source_pattern.id] += 1
        
        if counts:
            most_common = max(counts.items(), key=lambda x: x[1])
            return most_common[0]
        
        return None


# Singleton instance
_transfer_learner = None

def get_transfer_learner(knowledge_graph=None) -> TransferLearner:
    """Get or create singleton transfer learner"""
    global _transfer_learner
    if _transfer_learner is None:
        _transfer_learner = TransferLearner(knowledge_graph)
    return _transfer_learner
