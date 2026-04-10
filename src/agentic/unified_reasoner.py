"""
Unified Reasoning Engine for AlleyBot AGI
Combines symbolic (logic) and neural (LLM) reasoning into single coherent system
Handles all reasoning tasks: logic, math, language, planning, social, trading
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning the unified system can perform"""
    LOGICAL = "logical"  # Symbolic logic, rules, proofs
    MATHEMATICAL = "mathematical"  # Math, calculations, proofs
    LINGUISTIC = "linguistic"  # Language understanding, generation
    STRATEGIC = "strategic"  # Planning, decision-making
    SOCIAL = "social"  # Social intelligence, relationships
    CAUSAL = "causal"  # Cause-effect reasoning
    ANALOGICAL = "analogical"  # Pattern transfer across domains
    TEMPORAL = "temporal"  # Time-based reasoning
    SPATIAL = "spatial"  # Physical space reasoning


@dataclass
class ReasoningContext:
    """Context for a reasoning request"""
    problem: str  # The problem to reason about
    domain: str  # Primary domain (social, trading, chess, etc)
    reasoning_type: ReasoningType  # Type of reasoning needed
    related_domains: List[str] = None  # Other relevant domains
    constraints: Dict[str, Any] = None  # Constraints on reasoning
    goal: str = None  # What we're trying to achieve
    confidence_threshold: float = 0.7  # Minimum confidence for decision


@dataclass
class ReasoningResult:
    """Result of reasoning process"""
    decision: Any  # The decision/answer
    confidence: float  # Confidence in decision (0-1)
    reasoning_path: List[str]  # Steps taken to reach decision
    evidence: Dict[str, Any]  # Evidence supporting decision
    alternative_decisions: List[Tuple[Any, float]] = None  # Other options considered
    explanation: str = None  # Human-readable explanation
    knowledge_used: List[str] = None  # Knowledge sources used


class UnifiedReasoner:
    """
    Unified Reasoning Engine - Single system for all reasoning tasks
    
    Combines:
    - Symbolic reasoning (logic, rules, constraints)
    - Neural reasoning (LLM-based pattern matching)
    - Knowledge graph (unified knowledge representation)
    - Transfer learning (cross-domain pattern application)
    
    This is the foundation of AGI - one reasoner for everything.
    """
    
    def __init__(self, knowledge_graph=None, symbolic_engine=None, plugin_manager=None):
        """
        Initialize unified reasoner
        
        Args:
            knowledge_graph: Unified knowledge representation
            symbolic_engine: Symbolic reasoning engine (logic, rules)
            plugin_manager: Access to domain-specific plugins
        """
        self.knowledge_graph = knowledge_graph
        self.symbolic_engine = symbolic_engine
        self.plugin_manager = plugin_manager
        
        # Neural reasoning (LLM)
        self.llm = None
        self._init_llm()
        
        # Reasoning cache for efficiency
        self.reasoning_cache = {}
        
        logger.info("✅ Unified Reasoning Engine initialized")
    
    def _init_llm(self):
        """Initialize LLM for neural reasoning"""
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                self.llm = deepseek_ai
                logger.info("✅ Neural reasoning (DeepSeek) available")
        except Exception as e:
            logger.warning(f"⚠️ Neural reasoning not available: {e}")
    
    def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Main reasoning entry point - handles all reasoning types
        
        Args:
            context: Reasoning context with problem, domain, type
            
        Returns:
            ReasoningResult with decision, confidence, explanation
        """
        logger.info(f"🧠 Reasoning: {context.problem} (type: {context.reasoning_type.value})")
        
        # Route to appropriate reasoning method
        if context.reasoning_type == ReasoningType.LOGICAL:
            return self._reason_logical(context)
        elif context.reasoning_type == ReasoningType.MATHEMATICAL:
            return self._reason_mathematical(context)
        elif context.reasoning_type == ReasoningType.LINGUISTIC:
            return self._reason_linguistic(context)
        elif context.reasoning_type == ReasoningType.STRATEGIC:
            return self._reason_strategic(context)
        elif context.reasoning_type == ReasoningType.SOCIAL:
            return self._reason_social(context)
        elif context.reasoning_type == ReasoningType.CAUSAL:
            return self._reason_causal(context)
        elif context.reasoning_type == ReasoningType.ANALOGICAL:
            return self._reason_analogical(context)
        elif context.reasoning_type == ReasoningType.TEMPORAL:
            return self._reason_temporal(context)
        elif context.reasoning_type == ReasoningType.SPATIAL:
            return self._reason_spatial(context)
        else:
            # Default: hybrid reasoning
            return self._reason_hybrid(context)
    
    def _reason_logical(self, context: ReasoningContext) -> ReasoningResult:
        """Symbolic logic reasoning using rules and constraints"""
        reasoning_path = ["Starting logical reasoning"]
        
        # Use symbolic engine if available
        if self.symbolic_engine:
            try:
                result = self.symbolic_engine.solve(
                    problem=context.problem,
                    constraints=context.constraints or {}
                )
                
                if result:
                    reasoning_path.append(f"Symbolic engine solved: {result}")
                    return ReasoningResult(
                        decision=result.get('solution'),
                        confidence=result.get('confidence', 1.0),
                        reasoning_path=reasoning_path,
                        evidence={'symbolic_proof': result.get('proof')},
                        explanation=result.get('explanation')
                    )
            except Exception as e:
                reasoning_path.append(f"Symbolic engine failed: {e}")
        
        # Fallback: Neural reasoning with logical prompt
        if self.llm:
            reasoning_path.append("Using neural reasoning for logic")
            return self._neural_logical_reasoning(context, reasoning_path)
        
        # No reasoning available
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No logical reasoning engine available"
        )
    
    def _reason_mathematical(self, context: ReasoningContext) -> ReasoningResult:
        """Mathematical reasoning and calculations"""
        reasoning_path = ["Starting mathematical reasoning"]
        
        # Try symbolic engine for math
        if self.symbolic_engine and hasattr(self.symbolic_engine, 'solve_math'):
            try:
                result = self.symbolic_engine.solve_math(context.problem)
                reasoning_path.append(f"Solved mathematically: {result}")
                
                return ReasoningResult(
                    decision=result.get('answer'),
                    confidence=1.0,  # Math is certain
                    reasoning_path=reasoning_path,
                    evidence={'calculation': result.get('steps')},
                    explanation=result.get('explanation')
                )
            except Exception as e:
                reasoning_path.append(f"Math solver failed: {e}")
        
        # Fallback: Neural reasoning
        if self.llm:
            reasoning_path.append("Using neural reasoning for math")
            prompt = f"""Solve this mathematical problem step by step:

Problem: {context.problem}

Show your work and provide the final answer."""
            
            response = self.llm.chat(prompt, max_tokens=500)
            
            return ReasoningResult(
                decision=response,
                confidence=0.8,  # Neural math less certain
                reasoning_path=reasoning_path,
                evidence={'llm_response': response},
                explanation=response
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No mathematical reasoning available"
        )
    
    def _reason_strategic(self, context: ReasoningContext) -> ReasoningResult:
        """Strategic reasoning for planning and decision-making"""
        reasoning_path = ["Starting strategic reasoning"]
        
        # Pull knowledge from relevant domains
        domain_knowledge = self._get_domain_knowledge(
            [context.domain] + (context.related_domains or [])
        )
        reasoning_path.append(f"Gathered knowledge from {len(domain_knowledge)} domains")
        
        # Check for analogous strategies in other domains
        analogies = self._find_analogous_strategies(context, domain_knowledge)
        if analogies:
            reasoning_path.append(f"Found {len(analogies)} analogous strategies")
        
        # Use LLM for strategic reasoning with domain knowledge
        if self.llm:
            prompt = self._build_strategic_prompt(context, domain_knowledge, analogies)
            response = self.llm.chat(prompt, max_tokens=800)
            
            reasoning_path.append("Generated strategic decision")
            
            return ReasoningResult(
                decision=response,
                confidence=0.85,
                reasoning_path=reasoning_path,
                evidence={
                    'domain_knowledge': domain_knowledge,
                    'analogies': analogies,
                    'llm_response': response
                },
                explanation=response,
                knowledge_used=[context.domain] + (context.related_domains or [])
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No strategic reasoning available"
        )
    
    def _reason_social(self, context: ReasoningContext) -> ReasoningResult:
        """Social intelligence reasoning"""
        reasoning_path = ["Starting social reasoning"]
        
        # Get social context from knowledge graph
        social_knowledge = self._get_social_context(context)
        reasoning_path.append(f"Retrieved social context: {len(social_knowledge)} facts")
        
        # Use LLM with social intelligence
        if self.llm:
            prompt = f"""As an AI with social intelligence, reason about this situation:

Problem: {context.problem}
Domain: {context.domain}
Goal: {context.goal or 'Optimal social outcome'}

Social Context:
{self._format_social_context(social_knowledge)}

Provide a socially intelligent decision that considers:
1. Relationship dynamics
2. Social norms and expectations
3. Long-term relationship building
4. Authenticity and trust

Decision:"""
            
            response = self.llm.chat(prompt, max_tokens=500)
            
            return ReasoningResult(
                decision=response,
                confidence=0.82,
                reasoning_path=reasoning_path,
                evidence={'social_context': social_knowledge},
                explanation=response
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No social reasoning available"
        )
    
    def _reason_causal(self, context: ReasoningContext) -> ReasoningResult:
        """Causal reasoning - understand cause and effect"""
        reasoning_path = ["Starting causal reasoning"]
        
        # Build causal model from knowledge graph
        causal_model = self._build_causal_model(context)
        reasoning_path.append(f"Built causal model with {len(causal_model)} relationships")
        
        # Trace causal chains
        if self.llm:
            prompt = f"""Analyze the causal relationships in this situation:

Problem: {context.problem}

Causal Model:
{self._format_causal_model(causal_model)}

Identify:
1. Root causes
2. Causal chains
3. Likely effects
4. Intervention points

Analysis:"""
            
            response = self.llm.chat(prompt, max_tokens=600)
            
            return ReasoningResult(
                decision=response,
                confidence=0.78,
                reasoning_path=reasoning_path,
                evidence={'causal_model': causal_model},
                explanation=response
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No causal reasoning available"
        )
    
    def _reason_analogical(self, context: ReasoningContext) -> ReasoningResult:
        """Analogical reasoning - transfer patterns across domains"""
        reasoning_path = ["Starting analogical reasoning"]
        
        # Find analogous situations in other domains
        analogies = self._find_cross_domain_analogies(context)
        reasoning_path.append(f"Found {len(analogies)} cross-domain analogies")
        
        if not analogies:
            return ReasoningResult(
                decision=None,
                confidence=0.0,
                reasoning_path=reasoning_path,
                evidence={},
                explanation="No analogies found"
            )
        
        # Apply analogical reasoning
        if self.llm:
            prompt = f"""Use analogical reasoning to solve this problem:

Problem: {context.problem}
Domain: {context.domain}

Analogies from other domains:
{self._format_analogies(analogies)}

Apply the patterns from these analogies to solve the current problem.
Explain how the analogy transfers and what solution it suggests.

Solution:"""
            
            response = self.llm.chat(prompt, max_tokens=700)
            
            return ReasoningResult(
                decision=response,
                confidence=0.75,
                reasoning_path=reasoning_path,
                evidence={'analogies': analogies},
                explanation=response,
                knowledge_used=[a['source_domain'] for a in analogies]
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=reasoning_path,
            evidence={},
            explanation="No analogical reasoning available"
        )
    
    def _reason_hybrid(self, context: ReasoningContext) -> ReasoningResult:
        """Hybrid reasoning - combines symbolic and neural"""
        reasoning_path = ["Starting hybrid reasoning"]
        
        # Step 1: Symbolic reasoning for constraints
        symbolic_result = None
        if self.symbolic_engine:
            try:
                symbolic_result = self.symbolic_engine.check_constraints(
                    context.problem,
                    context.constraints or {}
                )
                reasoning_path.append(f"Symbolic: {symbolic_result}")
            except Exception as e:
                reasoning_path.append(f"Symbolic failed: {e}")
        
        # Step 2: Neural reasoning for pattern matching
        neural_result = None
        if self.llm:
            prompt = f"""Reason about this problem:

Problem: {context.problem}
Domain: {context.domain}
Goal: {context.goal or 'Find best solution'}

Constraints:
{context.constraints or 'None'}

Provide a well-reasoned decision with explanation.

Decision:"""
            
            neural_result = self.llm.chat(prompt, max_tokens=500)
            reasoning_path.append("Neural reasoning complete")
        
        # Step 3: Combine results
        if symbolic_result and neural_result:
            # Both available - combine
            decision = {
                'symbolic': symbolic_result,
                'neural': neural_result,
                'combined': f"Symbolic constraints satisfied: {symbolic_result.get('satisfied', False)}\nNeural decision: {neural_result}"
            }
            confidence = 0.9
            explanation = decision['combined']
        elif neural_result:
            # Only neural
            decision = neural_result
            confidence = 0.75
            explanation = neural_result
        elif symbolic_result:
            # Only symbolic
            decision = symbolic_result
            confidence = 0.85
            explanation = str(symbolic_result)
        else:
            # Neither available
            decision = None
            confidence = 0.0
            explanation = "No reasoning engines available"
        
        return ReasoningResult(
            decision=decision,
            confidence=confidence,
            reasoning_path=reasoning_path,
            evidence={
                'symbolic': symbolic_result,
                'neural': neural_result
            },
            explanation=explanation
        )
    
    # Helper methods
    
    def _get_domain_knowledge(self, domains: List[str]) -> Dict[str, Any]:
        """Get knowledge from specified domains"""
        knowledge = {}
        
        if self.knowledge_graph:
            for domain in domains:
                domain_facts = self.knowledge_graph.get_domain_facts(domain)
                if domain_facts:
                    knowledge[domain] = domain_facts
        
        return knowledge
    
    def _find_analogous_strategies(self, context: ReasoningContext, domain_knowledge: Dict) -> List[Dict]:
        """Find analogous strategies from other domains"""
        analogies = []
        
        # This will be enhanced with transfer learning engine
        # For now, return empty list
        
        return analogies
    
    def _find_cross_domain_analogies(self, context: ReasoningContext) -> List[Dict]:
        """Find analogous patterns from other domains using knowledge graph."""
        analogies = []
        
        if not self.knowledge_graph:
            return analogies
        
        # Search for similar patterns in related domains
        related_domains = context.related_domains or []
        
        for domain in related_domains:
            # Query knowledge graph for successful patterns in this domain
            try:
                domain_patterns = self.knowledge_graph.query_patterns(
                    domain=domain,
                    pattern_type='successful_strategy',
                    limit=3
                )
                
                for pattern in domain_patterns:
                    analogies.append({
                        'source_domain': domain,
                        'pattern': pattern.get('description'),
                        'success_rate': pattern.get('success_rate', 0.0),
                        'transferability': self._estimate_transferability(
                            pattern, context.domain
                        )
                    })
            except Exception as e:
                logger.debug(f"Failed to process pattern for analogy: {e}")
        
        # Sort by transferability
        analogies.sort(key=lambda x: x.get('transferability', 0), reverse=True)
        return analogies[:5]
    
    def _estimate_transferability(self, pattern: Dict, target_domain: str) -> float:
        """Estimate how well a pattern transfers to target domain."""
        # Simple heuristic: domains with similar characteristics transfer better
        domain_similarity = {
            ('social', 'content'): 0.8,
            ('trading', 'analysis'): 0.7,
            ('chess', 'trading'): 0.6,  # Strategic thinking transfers
            ('social', 'trading'): 0.5,  # Sentiment analysis transfers
        }
        
        source = pattern.get('domain', 'unknown')
        key = tuple(sorted([source, target_domain]))
        
        return domain_similarity.get(key, 0.3)
    
    def _find_cross_domain_analogies_fallback(self, context: ReasoningContext) -> List[Dict]:
        """Find analogies across different domains"""
        analogies = []
        
        # This will be enhanced with transfer learning engine
        # For now, return empty list
        
        return analogies
    
    def _get_social_context(self, context: ReasoningContext) -> Dict[str, Any]:
        """Get social context from knowledge graph"""
        if self.knowledge_graph:
            return self.knowledge_graph.get_social_context(context.domain)
        return {}
    
    def _build_causal_model(self, context: ReasoningContext) -> Dict[str, Any]:
        """Build causal model from knowledge graph"""
        if self.knowledge_graph:
            return self.knowledge_graph.get_causal_relationships(context.domain)
        return {}
    
    def _build_strategic_prompt(self, context: ReasoningContext, knowledge: Dict, analogies: List) -> str:
        """Build prompt for strategic reasoning"""
        prompt = f"""As a strategic reasoner, analyze this situation:

Problem: {context.problem}
Domain: {context.domain}
Goal: {context.goal or 'Optimal outcome'}

Domain Knowledge:
{self._format_knowledge(knowledge)}

"""
        
        if analogies:
            prompt += f"""
Analogous Strategies:
{self._format_analogies(analogies)}
"""
        
        prompt += """
Provide a strategic decision that:
1. Considers all available knowledge
2. Applies successful patterns from analogies
3. Optimizes for the stated goal
4. Accounts for constraints and risks

Strategic Decision:"""
        
        return prompt
    
    def _format_knowledge(self, knowledge: Dict) -> str:
        """Format knowledge for prompt"""
        if not knowledge:
            return "No domain knowledge available"
        
        formatted = []
        for domain, facts in knowledge.items():
            formatted.append(f"{domain}: {len(facts)} facts")
        
        return "\n".join(formatted)
    
    def _format_analogies(self, analogies: List[Dict]) -> str:
        """Format analogies for prompt"""
        if not analogies:
            return "No analogies found"
        
        formatted = []
        for i, analogy in enumerate(analogies, 1):
            formatted.append(f"{i}. {analogy.get('description', 'Unknown analogy')}")
        
        return "\n".join(formatted)
    
    def _format_social_context(self, context: Dict) -> str:
        """Format social context for prompt"""
        if not context:
            return "No social context available"
        
        return str(context)
    
    def _format_causal_model(self, model: Dict) -> str:
        """Format causal model for prompt"""
        if not model:
            return "No causal relationships identified"
        
        return str(model)
    
    def _neural_logical_reasoning(self, context: ReasoningContext, reasoning_path: List[str]) -> ReasoningResult:
        """Use LLM for logical reasoning"""
        prompt = f"""Use logical reasoning to solve this problem:

Problem: {context.problem}

Constraints:
{context.constraints or 'None'}

Apply formal logic to reach a conclusion.
Show your reasoning steps.

Logical Conclusion:"""
        
        response = self.llm.chat(prompt, max_tokens=500)
        reasoning_path.append("Neural logical reasoning complete")
        
        return ReasoningResult(
            decision=response,
            confidence=0.75,
            reasoning_path=reasoning_path,
            evidence={'llm_response': response},
            explanation=response
        )
    
    def _reason_temporal(self, context: ReasoningContext) -> ReasoningResult:
        """Temporal reasoning - time-based logic"""
        # Placeholder for temporal reasoning
        return ReasoningResult(
            decision="Temporal reasoning not yet implemented",
            confidence=0.0,
            reasoning_path=["Temporal reasoning placeholder"],
            evidence={},
            explanation="Temporal reasoning coming soon"
        )
    
    def _reason_spatial(self, context: ReasoningContext) -> ReasoningResult:
        """Spatial reasoning - physical space logic"""
        # Placeholder for spatial reasoning
        return ReasoningResult(
            decision="Spatial reasoning not yet implemented",
            confidence=0.0,
            reasoning_path=["Spatial reasoning placeholder"],
            evidence={},
            explanation="Spatial reasoning coming soon"
        )
    
    def _reason_linguistic(self, context: ReasoningContext) -> ReasoningResult:
        """Linguistic reasoning - language understanding"""
        if self.llm:
            response = self.llm.chat(context.problem, max_tokens=500)
            
            return ReasoningResult(
                decision=response,
                confidence=0.88,
                reasoning_path=["Linguistic reasoning via LLM"],
                evidence={'llm_response': response},
                explanation=response
            )
        
        return ReasoningResult(
            decision=None,
            confidence=0.0,
            reasoning_path=["No linguistic reasoning available"],
            evidence={},
            explanation="No LLM available"
        )


# Singleton instance
_unified_reasoner = None

def get_unified_reasoner(knowledge_graph=None, symbolic_engine=None, plugin_manager=None) -> UnifiedReasoner:
    """Get or create singleton unified reasoner"""
    global _unified_reasoner
    if _unified_reasoner is None:
        _unified_reasoner = UnifiedReasoner(knowledge_graph, symbolic_engine, plugin_manager)
    return _unified_reasoner
