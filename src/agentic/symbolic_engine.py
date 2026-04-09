"""
Symbolic Reasoning Engine for AlleyBot AGI
Handles logic, rules, constraints, and mathematical proofs
Complements neural reasoning with formal symbolic reasoning
"""
import ast
import logging
import operator
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LogicOperator(Enum):
    """Logical operators"""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"  # if and only if


@dataclass
class LogicalRule:
    """A logical rule in the system"""
    id: str
    premises: List[str]  # Conditions that must be true
    conclusion: str  # What follows if premises are true
    confidence: float = 1.0  # Certainty of rule (0-1)
    domain: str = "general"  # Which domain this rule applies to


@dataclass
class Constraint:
    """A constraint that must be satisfied"""
    id: str
    expression: str  # The constraint expression
    constraint_type: str  # Type: equality, inequality, range, etc
    required: bool = True  # Must be satisfied vs preference


class SymbolicEngine:
    """
    Symbolic Reasoning Engine - Formal logic and rule-based reasoning
    
    Capabilities:
    - Logical inference (modus ponens, modus tollens, etc)
    - Constraint satisfaction
    - Rule-based reasoning
    - Mathematical proofs (basic)
    - Consistency checking
    
    This provides the "logic" side of the symbolic+neural hybrid.
    """
    
    def __init__(self):
        """Initialize symbolic reasoning engine"""
        self.rules: Dict[str, LogicalRule] = {}
        self.facts: Set[str] = set()
        self.constraints: Dict[str, Constraint] = {}
        
        # Load default rules
        self._load_default_rules()
        
        logger.info("✅ Symbolic Reasoning Engine initialized")
    
    def _load_default_rules(self):
        """Load default logical rules"""
        # Trading rules
        self.add_rule(LogicalRule(
            id="profitable_trade",
            premises=["profit_percent > 5", "gas_cost < profit"],
            conclusion="trade_is_profitable",
            confidence=1.0,
            domain="trading"
        ))
        
        self.add_rule(LogicalRule(
            id="safe_trade",
            premises=["slippage < 1", "liquidity > min_liquidity"],
            conclusion="trade_is_safe",
            confidence=0.95,
            domain="trading"
        ))
        
        self.add_rule(LogicalRule(
            id="execute_trade",
            premises=["trade_is_profitable", "trade_is_safe"],
            conclusion="should_execute_trade",
            confidence=0.9,
            domain="trading"
        ))
        
        # Social rules
        self.add_rule(LogicalRule(
            id="engagement_quota",
            premises=["engagements >= 5", "posts < engagements"],
            conclusion="can_post",
            confidence=1.0,
            domain="social"
        ))
        
        self.add_rule(LogicalRule(
            id="quality_content",
            premises=["content_length > 20", "not_spam", "unique"],
            conclusion="content_is_quality",
            confidence=0.85,
            domain="social"
        ))
        
        # General reasoning rules
        self.add_rule(LogicalRule(
            id="modus_ponens",
            premises=["P", "P implies Q"],
            conclusion="Q",
            confidence=1.0,
            domain="logic"
        ))
        
        logger.info(f"✅ Loaded {len(self.rules)} default rules")
    
    def add_rule(self, rule: LogicalRule):
        """Add a logical rule to the system"""
        self.rules[rule.id] = rule
        logger.debug(f"Added rule: {rule.id}")
    
    def add_fact(self, fact: str):
        """Add a fact to the knowledge base"""
        self.facts.add(fact)
        logger.debug(f"Added fact: {fact}")
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the system"""
        self.constraints[constraint.id] = constraint
        logger.debug(f"Added constraint: {constraint.id}")
    
    def solve(self, problem: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a logical problem with constraints
        
        Args:
            problem: Problem description
            constraints: Dictionary of constraints
            
        Returns:
            Solution with proof and confidence
        """
        logger.info(f"🔍 Solving: {problem}")
        
        # Parse problem into facts
        facts = self._parse_problem(problem, constraints)
        
        # Add facts to knowledge base
        for fact in facts:
            self.add_fact(fact)
        
        # Apply logical inference
        inferred_facts = self._forward_chaining(facts)
        
        # Check if we reached a conclusion
        conclusions = self._extract_conclusions(inferred_facts)
        
        if conclusions:
            return {
                'solution': conclusions[0],
                'confidence': 0.9,
                'proof': inferred_facts,
                'explanation': self._explain_inference(inferred_facts)
            }
        
        return {
            'solution': None,
            'confidence': 0.0,
            'proof': [],
            'explanation': "No conclusion could be reached"
        }
    
    def check_constraints(self, problem: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if constraints are satisfied
        
        Args:
            problem: Problem description
            constraints: Dictionary of constraints to check
            
        Returns:
            Result with satisfied constraints and violations
        """
        satisfied = []
        violated = []
        
        for key, value in constraints.items():
            # Simple constraint checking (can be enhanced)
            if self._check_constraint(key, value):
                satisfied.append(key)
            else:
                violated.append(key)
        
        return {
            'satisfied': len(violated) == 0,
            'satisfied_constraints': satisfied,
            'violated_constraints': violated,
            'confidence': len(satisfied) / len(constraints) if constraints else 0.0
        }
    
    def _check_constraint(self, key: str, value: Any) -> bool:
        """Check if a single constraint is satisfied"""
        # Simple implementation - can be enhanced with constraint solver
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value > 0
        elif isinstance(value, str):
            return len(value) > 0
        return True
    
    def _parse_problem(self, problem: str, constraints: Dict[str, Any]) -> List[str]:
        """Parse problem into logical facts"""
        facts = []
        
        # Extract facts from constraints
        for key, value in constraints.items():
            if isinstance(value, bool) and value:
                facts.append(key)
            elif isinstance(value, (int, float)):
                facts.append(f"{key} = {value}")
            elif isinstance(value, str):
                facts.append(f"{key} = '{value}'")
        
        return facts
    
    def _forward_chaining(self, initial_facts: List[str]) -> List[str]:
        """
        Forward chaining inference - derive new facts from rules
        
        Args:
            initial_facts: Starting facts
            
        Returns:
            All facts (initial + inferred)
        """
        all_facts = set(initial_facts)
        new_facts_added = True
        iterations = 0
        max_iterations = 100
        
        while new_facts_added and iterations < max_iterations:
            new_facts_added = False
            iterations += 1
            
            for rule in self.rules.values():
                # Check if all premises are satisfied
                if self._premises_satisfied(rule.premises, all_facts):
                    # Add conclusion if not already present
                    if rule.conclusion not in all_facts:
                        all_facts.add(rule.conclusion)
                        new_facts_added = True
                        logger.debug(f"Inferred: {rule.conclusion} (from rule {rule.id})")
        
        return list(all_facts)
    
    def _premises_satisfied(self, premises: List[str], facts: Set[str]) -> bool:
        """Check if all premises are satisfied by current facts"""
        for premise in premises:
            # Simple matching - can be enhanced with pattern matching
            if premise not in facts:
                # Check for partial matches (e.g., "profit_percent > 5")
                if not self._partial_match(premise, facts):
                    return False
        return True
    
    def _partial_match(self, premise: str, facts: Set[str]) -> bool:
        """Check if premise partially matches any fact"""
        # Extract key from premise (e.g., "profit_percent" from "profit_percent > 5")
        key = premise.split()[0] if ' ' in premise else premise
        
        # Check if any fact contains this key
        for fact in facts:
            if key in fact:
                # Simple evaluation - can be enhanced
                return True
        
        return False
    
    def _extract_conclusions(self, facts: List[str]) -> List[str]:
        """Extract conclusions from inferred facts"""
        conclusions = []
        
        # Look for facts that match rule conclusions
        for rule in self.rules.values():
            if rule.conclusion in facts:
                conclusions.append(rule.conclusion)
        
        return conclusions
    
    def _explain_inference(self, facts: List[str]) -> str:
        """Generate human-readable explanation of inference"""
        explanation = "Logical inference chain:\n"
        
        for i, fact in enumerate(facts, 1):
            explanation += f"{i}. {fact}\n"
        
        return explanation
    
    def solve_math(self, problem: str) -> Dict[str, Any]:
        """
        Solve mathematical problem
        
        Args:
            problem: Math problem description
            
        Returns:
            Solution with steps
        """
        # Basic math solver - can be enhanced with sympy or similar
        try:
            # Try to evaluate as Python expression (safe subset)
            result = self._safe_eval(problem)
            
            return {
                'answer': result,
                'steps': [f"Evaluated: {problem}", f"Result: {result}"],
                'explanation': f"Mathematical evaluation: {problem} = {result}"
            }
        except Exception as e:
            return {
                'answer': None,
                'steps': [],
                'explanation': f"Could not solve: {e}"
            }
    
    # Operator map for safe AST-based math evaluation
    _SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Safe builtin functions allowed in expressions
    _SAFE_FUNCS = {
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'round': round,
    }

    def _safe_eval(self, expression: str) -> Any:
        """Safely evaluate mathematical expression using AST parsing.
        
        No eval() — walks the AST and only allows numeric literals,
        basic arithmetic operators, and whitelisted functions.
        """
        if any(dangerous in expression for dangerous in ['__', 'import', 'exec', 'eval']):
            raise ValueError("Unsafe expression")

        try:
            tree = ast.parse(expression.strip(), mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid expression: {e}")

        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node (safe arithmetic only)."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op = self._SAFE_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op = self._SAFE_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(self._eval_node(node.operand))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self._SAFE_FUNCS:
                args = [self._eval_node(a) for a in node.args]
                return self._SAFE_FUNCS[node.func.id](*args)
            raise ValueError(f"Unsupported function call")
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")
    
    def verify_consistency(self) -> Dict[str, Any]:
        """Verify logical consistency of rules and facts"""
        inconsistencies = []
        
        # Check for contradictory rules
        for rule1 in self.rules.values():
            for rule2 in self.rules.values():
                if rule1.id != rule2.id:
                    # Check if same premises lead to different conclusions
                    if (set(rule1.premises) == set(rule2.premises) and 
                        rule1.conclusion != rule2.conclusion):
                        inconsistencies.append({
                            'type': 'contradictory_rules',
                            'rule1': rule1.id,
                            'rule2': rule2.id
                        })
        
        return {
            'consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies
        }
    
    def get_applicable_rules(self, domain: str) -> List[LogicalRule]:
        """Get all rules applicable to a domain"""
        return [rule for rule in self.rules.values() 
                if rule.domain == domain or rule.domain == "general"]
    
    def explain_rule(self, rule_id: str) -> str:
        """Generate human-readable explanation of a rule"""
        if rule_id not in self.rules:
            return f"Rule {rule_id} not found"
        
        rule = self.rules[rule_id]
        
        explanation = f"Rule: {rule.id}\n"
        explanation += f"Domain: {rule.domain}\n"
        explanation += f"If:\n"
        for premise in rule.premises:
            explanation += f"  - {premise}\n"
        explanation += f"Then: {rule.conclusion}\n"
        explanation += f"Confidence: {rule.confidence * 100}%\n"
        
        return explanation


# Singleton instance
_symbolic_engine = None

def get_symbolic_engine() -> SymbolicEngine:
    """Get or create singleton symbolic engine"""
    global _symbolic_engine
    if _symbolic_engine is None:
        _symbolic_engine = SymbolicEngine()
    return _symbolic_engine
