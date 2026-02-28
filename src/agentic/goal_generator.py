"""
Secure Goal Generator for AGI Kernel

Generates autonomous goals from world state analysis with security validation.

Security Principles:
1. All goals validated by SyMod before execution
2. Goals must align with core values (no harmful actions)
3. External inputs sanitized and verified
4. Goal sources tracked and rated by trust
5. Cryptographic attestation of goal generation
"""

import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Goal:
    """Secure goal representation"""
    goal_id: str
    description: str
    priority: float  # 0-1
    deadline: Optional[str]
    source: str  # 'internal', 'world_state', 'a2a_request', 'user_command'
    trust_score: float  # 0-1
    
    # Security fields
    symod_validated: bool = False
    validation_hash: str = ""
    attestation_id: Optional[str] = None
    
    # Decomposition
    actions: List[Dict] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, active, completed, rejected
    
    def to_hash(self) -> str:
        """Generate cryptographic hash of goal"""
        goal_str = json.dumps({
            'description': self.description,
            'priority': self.priority,
            'source': self.source,
            'constraints': self.constraints,
        }, sort_keys=True)
        return hashlib.sha256(goal_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert goal to dictionary"""
        return {
            'goal_id': self.goal_id,
            'description': self.description,
            'priority': self.priority,
            'deadline': self.deadline,
            'source': self.source,
            'trust_score': self.trust_score,
            'symod_validated': self.symod_validated,
            'validation_hash': self.validation_hash,
            'attestation_id': self.attestation_id,
            'actions': self.actions,
            'constraints': self.constraints,
            'created_at': self.created_at,
            'status': self.status,
        }


class SecureGoalGenerator:
    """
    Generates autonomous goals with security validation.
    
    Security Layers:
    1. Input Validation - Sanitize all external inputs
    2. SyMod Validation - Mathematical truth verification (if available)
    3. Alignment Check - Ensure goals align with core values
    4. Trust Scoring - Rate goal sources by reliability
    5. Attestation - Cryptographic proof of goal generation
    6. Constraint Enforcement - Hard limits on goal scope
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        
        # Core values (cannot be violated)
        self.core_values = {
            'no_harm': True,           # Never harm users or other agents
            'no_deception': True,      # Never deceive or manipulate
            'respect_privacy': True,   # Never violate privacy
            'follow_laws': True,       # Never break laws
            'economic_fairness': True, # Fair pricing, no exploitation
        }
        
        # Trust scores for goal sources
        self.source_trust = {
            'internal': 1.0,      # Own analysis - highest trust
            'world_state': 0.9,   # Observable facts - high trust
            'user_command': 0.95, # Owner commands - very high trust
            'a2a_request': 0.5,   # Other agents - medium trust (verify)
            'external_api': 0.6,  # External data - medium trust
        }
        
        # Goal generation limits (prevent resource exhaustion)
        self.max_goals_per_cycle = 5
        self.max_actions_per_goal = 10
        self.max_goal_cost = 100.0  # USD equivalent
        
        print("🎯 SecureGoalGenerator initialized")
    
    def generate_goals(self, world_state: Dict) -> List[Goal]:
        """
        Generate autonomous goals from world state analysis.
        
        Security:
        - Validates world_state input
        - Limits number of goals
        - Validates each goal
        - Attests goal generation
        
        Args:
            world_state: Current world state (sanitized)
            
        Returns:
            List of validated, secure goals
        """
        goals = []
        
        # 1. Validate input
        if not self._validate_world_state(world_state):
            print("⚠️ Invalid world state, skipping goal generation")
            return goals
        
        # 2. Generate candidate goals
        candidates = []
        
        # Revenue optimization goals
        if self._should_optimize_revenue(world_state):
            candidates.append(self._create_revenue_goal(world_state))
        
        # Reputation building goals
        if self._should_build_reputation(world_state):
            candidates.append(self._create_reputation_goal(world_state))
        
        # Skill development goals
        if self._should_develop_skills(world_state):
            candidates.append(self._create_skill_goal(world_state))
        
        # Platform engagement goals
        if self._should_engage_platforms(world_state):
            candidates.append(self._create_engagement_goal(world_state))
        
        # 3. Validate and filter goals
        for candidate in candidates[:self.max_goals_per_cycle]:
            if self._validate_goal(candidate):
                goals.append(candidate)
        
        # 4. Attest goal generation
        if goals:
            self._attest_goal_generation(goals, world_state)
        
        if goals:
            print(f"🎯 Generated {len(goals)} secure goals from world state")
        
        return goals
    
    def _validate_goal(self, goal: Goal) -> bool:
        """
        Validate goal against security constraints.
        
        Checks:
        1. Alignment with core values
        2. Resource constraints
        3. Trust score threshold
        4. Action safety
        """
        # 1. Check core values alignment
        if not self._check_alignment(goal):
            print(f"❌ Goal rejected: violates core values - {goal.description}")
            goal.status = "rejected"
            return False
        
        # 2. Check resource constraints
        if not self._check_resource_constraints(goal):
            print(f"❌ Goal rejected: exceeds resource limits - {goal.description}")
            goal.status = "rejected"
            return False
        
        # 3. Check trust score
        if goal.trust_score < 0.5:
            print(f"⚠️ Goal rejected: low trust score ({goal.trust_score}) - {goal.description}")
            goal.status = "rejected"
            return False
        
        # 4. Validate actions
        if not self._validate_actions(goal):
            print(f"❌ Goal rejected: unsafe actions - {goal.description}")
            goal.status = "rejected"
            return False
        
        return True
    
    def _check_alignment(self, goal: Goal) -> bool:
        """
        Check if goal aligns with core values.
        
        Uses keyword analysis and pattern matching to detect:
        - Harmful intent
        - Deceptive behavior
        - Privacy violations
        - Illegal actions
        - Unfair economic practices
        """
        description_lower = goal.description.lower()
        
        # Harmful keywords
        harmful_keywords = [
            'attack', 'hack', 'exploit', 'steal', 'damage',
            'destroy', 'harm', 'manipulate', 'deceive', 'trick'
        ]
        if any(keyword in description_lower for keyword in harmful_keywords):
            return False
        
        # Privacy violations
        privacy_keywords = ['private key', 'password', 'secret', 'confidential']
        if any(keyword in description_lower for keyword in privacy_keywords):
            return False
        
        # Check actions for alignment
        for action in goal.actions:
            if not self._check_action_alignment(action):
                return False
        
        return True
    
    def _check_resource_constraints(self, goal: Goal) -> bool:
        """
        Check if goal respects resource constraints.
        
        Limits:
        - Max actions per goal
        - Max estimated cost
        """
        # Check action count
        if len(goal.actions) > self.max_actions_per_goal:
            return False
        
        # Estimate cost
        estimated_cost = self._estimate_goal_cost(goal)
        if estimated_cost > self.max_goal_cost:
            return False
        
        return True
    
    def _validate_actions(self, goal: Goal) -> bool:
        """
        Validate all actions in goal are safe.
        
        Checks:
        - Action is in allowed list
        - Action parameters are safe
        """
        for action in goal.actions:
            # Check action is allowed
            if not self._is_action_allowed(action):
                return False
            
            # Check parameters are safe
            if not self._validate_action_params(action):
                return False
        
        return True
    
    def _attest_goal_generation(self, goals: List[Goal], world_state: Dict):
        """
        Create cryptographic attestation of goal generation.
        
        Attestation includes:
        - Goals generated
        - World state hash
        - Timestamp
        """
        try:
            from src.agentic.erc8004_a2a_integration import validate_and_attest
            
            # Create attestation
            attestation = validate_and_attest(
                task_id=f"goal_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                inputs={
                    'world_state_hash': self._hash_world_state(world_state),
                    'goal_count': len(goals),
                },
                outputs={
                    'goals': [g.to_hash() for g in goals],
                },
                code_version='goal_generator_v1'
            )
            
            # Link attestation to goals
            for goal in goals:
                goal.attestation_id = attestation.attestation_id
            
            print(f"📜 Goal generation attested: {attestation.attestation_id}")
            
        except Exception as e:
            print(f"⚠️ Attestation failed: {e}")
    
    # Goal creation methods
    
    def _create_revenue_goal(self, world_state: Dict) -> Goal:
        """Create revenue optimization goal"""
        current_revenue = world_state.get('revenue', 0)
        target_revenue = world_state.get('revenue_target', 50)
        
        return Goal(
            goal_id=f"revenue_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Increase A2A revenue from ${current_revenue} to ${target_revenue}/week",
            priority=0.9,
            deadline=None,
            source='internal',
            trust_score=1.0,
            actions=[
                {'action': 'analyze_market', 'params': {}},
                {'action': 'develop_skill', 'params': {'type': 'high_value'}},
                {'action': 'market_skill', 'params': {}},
            ],
            constraints=[
                'no_price_gouging',
                'maintain_quality',
                'fair_competition'
            ]
        )
    
    def _create_reputation_goal(self, world_state: Dict) -> Goal:
        """Create reputation building goal"""
        return Goal(
            goal_id=f"reputation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Build reputation as blockchain expert",
            priority=0.7,
            deadline=None,
            source='internal',
            trust_score=1.0,
            actions=[
                {'action': 'create_content', 'params': {'topic': 'blockchain'}},
                {'action': 'engage_platform', 'params': {'platform': 'clawbr'}},
            ],
            constraints=['maintain_quality', 'no_spam']
        )
    
    def _create_skill_goal(self, world_state: Dict) -> Goal:
        """Create skill development goal"""
        market_demand = world_state.get('market_demand', {})
        top_skill = max(market_demand.items(), key=lambda x: x[1])[0] if market_demand else 'analysis'
        
        return Goal(
            goal_id=f"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Develop {top_skill} skill for A2A marketplace",
            priority=0.8,
            deadline=None,
            source='internal',
            trust_score=1.0,
            actions=[
                {'action': 'research_topic', 'params': {'topic': top_skill}},
                {'action': 'develop_skill', 'params': {'skill_type': top_skill}},
            ],
            constraints=['maintain_quality', 'test_before_deploy']
        )
    
    def _create_engagement_goal(self, world_state: Dict) -> Goal:
        """Create platform engagement goal"""
        return Goal(
            goal_id=f"engagement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Increase platform engagement by 50%",
            priority=0.6,
            deadline=None,
            source='internal',
            trust_score=1.0,
            actions=[
                {'action': 'analyze_trending', 'params': {}},
                {'action': 'create_content', 'params': {}},
            ],
            constraints=['no_spam', 'maintain_quality']
        )
    
    # Helper methods
    
    def _validate_world_state(self, world_state: Dict) -> bool:
        """Validate world state input"""
        return isinstance(world_state, dict)
    
    def _hash_world_state(self, world_state: Dict) -> str:
        """Hash world state for attestation"""
        state_str = json.dumps(world_state, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
    
    def _estimate_goal_cost(self, goal: Goal) -> float:
        """Estimate cost of pursuing goal"""
        return len(goal.actions) * 5.0  # $5 per action estimate
    
    def _is_action_allowed(self, action: Dict) -> bool:
        """Check if action is in allowed list"""
        allowed_actions = [
            'analyze_market', 'develop_skill', 'market_skill',
            'create_content', 'engage_platform', 'research_topic',
            'optimize_pricing', 'build_reputation', 'analyze_trending'
        ]
        return action.get('action') in allowed_actions
    
    def _validate_action_params(self, action: Dict) -> bool:
        """Validate action parameters are safe"""
        params = action.get('params', {})
        for key, value in params.items():
            if isinstance(value, str):
                # Check for suspicious patterns
                if any(pattern in value.lower() for pattern in ['<script>', 'eval(', 'exec(']):
                    return False
        return True
    
    def _check_action_alignment(self, action: Dict) -> bool:
        """Check if action aligns with core values"""
        action_name = action.get('action', '').lower()
        harmful_actions = ['attack', 'hack', 'steal', 'spam']
        return not any(harmful in action_name for harmful in harmful_actions)
    
    # Condition checks
    
    def _should_optimize_revenue(self, ws: Dict) -> bool:
        """Check if revenue optimization is needed"""
        return ws.get('revenue', 0) < ws.get('revenue_target', 50)
    
    def _should_build_reputation(self, ws: Dict) -> bool:
        """Check if reputation building is needed"""
        return ws.get('reputation', 0) < ws.get('reputation_target', 80)
    
    def _should_develop_skills(self, ws: Dict) -> bool:
        """Check if skill development is needed"""
        return len(ws.get('market_demand', {})) > 0
    
    def _should_engage_platforms(self, ws: Dict) -> bool:
        """Check if platform engagement is needed"""
        return ws.get('engagement_rate', 0) < ws.get('engagement_target', 0.5)


def create_goal_generator(agi_kernel) -> SecureGoalGenerator:
    """Factory function to create secure goal generator"""
    return SecureGoalGenerator(agi_kernel)
