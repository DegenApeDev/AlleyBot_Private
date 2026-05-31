"""
Meta-Learning System for AlleyBot AGI
Learns how to learn better - optimizes learning strategies themselves
Analyzes what works and adapts learning approach over time
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class LearningStrategy:
    """A strategy for learning"""
    id: str
    name: str
    description: str
    domain: str  # Which domain this applies to
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    success_rate: float = 0.0  # 0-1
    avg_learning_speed: float = 0.0  # How fast it learns
    retention_rate: float = 0.0  # How well it retains
    transfer_ability: float = 0.0  # How well it transfers
    
    # Usage statistics
    times_used: int = 0
    total_outcomes: int = 0
    successful_outcomes: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    evolved_from: Optional[str] = None  # Parent strategy ID


@dataclass
class LearningOutcome:
    """Result of a learning attempt"""
    id: str
    strategy_id: str
    domain: str
    task: str
    
    # Outcome
    success: bool
    learning_time: timedelta
    quality_score: float  # 0-1
    retention_score: float  # 0-1 (tested later)
    
    # Context
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Feedback
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


@dataclass
class StrategyEvolution:
    """Record of strategy evolution"""
    id: str
    parent_strategy_id: str
    child_strategy_id: str
    mutations: List[str]  # What changed
    reason: str  # Why it evolved
    improvement: float  # Performance delta
    timestamp: datetime = field(default_factory=datetime.now)


class MetaLearner:
    """
    Meta-Learning System - Learn How to Learn
    
    Core AGI capability: Optimize the learning process itself
    
    Capabilities:
    - Track learning strategies and their effectiveness
    - Identify which strategies work best for which domains
    - Evolve strategies based on performance
    - Transfer successful strategies across domains
    - Optimize learning parameters (rate, batch size, etc)
    - Detect and fix learning plateaus
    
    This is what enables continuous improvement - AlleyBot gets better at getting better.
    """
    
    def __init__(self, knowledge_graph=None, storage_path: Optional[str] = None):
        """
        Initialize meta-learning system
        
        Args:
            knowledge_graph: Unified knowledge representation
            storage_path: Path to persistent storage
        """
        self.knowledge_graph = knowledge_graph
        self.storage_path = storage_path or "data/meta_learning.json"
        
        # Learning strategies
        self.strategies: Dict[str, LearningStrategy] = {}
        
        # Learning outcomes
        self.outcomes: List[LearningOutcome] = []
        
        # Strategy evolution history
        self.evolutions: List[StrategyEvolution] = []
        
        # Performance tracking
        self.domain_performance: Dict[str, List[float]] = defaultdict(list)
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize with default strategies
        self._init_default_strategies()
        
        # Load existing data
        self._load_data()
        
        logger.info("✅ Meta-Learning System initialized")
    
    def _init_default_strategies(self):
        """Initialize default learning strategies"""
        
        # Strategy: Deliberate Practice
        self.add_strategy(LearningStrategy(
            id="strategy_deliberate_practice",
            name="Deliberate Practice",
            description="Focus on specific weaknesses with immediate feedback",
            domain="general",
            parameters={
                'focus': 'weaknesses',
                'feedback_frequency': 'immediate',
                'difficulty': 'challenging',
                'repetition': 'spaced'
            }
        ))
        
        # Strategy: Transfer Learning
        self.add_strategy(LearningStrategy(
            id="strategy_transfer_learning",
            name="Transfer Learning",
            description="Apply knowledge from one domain to another",
            domain="general",
            parameters={
                'source_domain': 'similar',
                'adaptation': 'gradual',
                'validation': 'continuous'
            }
        ))
        
        # Strategy: Active Experimentation
        self.add_strategy(LearningStrategy(
            id="strategy_active_experimentation",
            name="Active Experimentation",
            description="Learn by trying different approaches and observing results",
            domain="general",
            parameters={
                'exploration_rate': 0.3,
                'hypothesis_testing': True,
                'failure_tolerance': 'high'
            }
        ))
        
        # Strategy: Pattern Recognition
        self.add_strategy(LearningStrategy(
            id="strategy_pattern_recognition",
            name="Pattern Recognition",
            description="Identify and memorize recurring patterns",
            domain="general",
            parameters={
                'pattern_threshold': 3,  # Minimum occurrences
                'abstraction_level': 'medium',
                'generalization': True
            }
        ))
        
        # Strategy: Incremental Learning
        self.add_strategy(LearningStrategy(
            id="strategy_incremental",
            name="Incremental Learning",
            description="Build knowledge gradually from simple to complex",
            domain="general",
            parameters={
                'start_difficulty': 'easy',
                'progression_rate': 'adaptive',
                'mastery_threshold': 0.8
            }
        ))
        
        # Strategy: Social Learning
        self.add_strategy(LearningStrategy(
            id="strategy_social_learning",
            name="Social Learning",
            description="Learn from observing and interacting with others",
            domain="social",
            parameters={
                'observation': True,
                'imitation': 'selective',
                'feedback_seeking': True
            }
        ))
        
        logger.info(f"✅ Initialized {len(self.strategies)} default learning strategies")
    
    def add_strategy(self, strategy: LearningStrategy):
        """Add a learning strategy"""
        self.strategies[strategy.id] = strategy
        logger.debug(f"Added learning strategy: {strategy.name}")
    
    def record_outcome(self, outcome: LearningOutcome):
        """Record a learning outcome"""
        self.outcomes.append(outcome)
        
        # Update strategy statistics
        strategy = self.strategies.get(outcome.strategy_id)
        if strategy:
            strategy.times_used += 1
            strategy.total_outcomes += 1
            if outcome.success:
                strategy.successful_outcomes += 1
            
            # Update success rate
            strategy.success_rate = strategy.successful_outcomes / strategy.total_outcomes
            
            # Update learning speed (inverse of time)
            time_hours = outcome.learning_time.total_seconds() / 3600
            if time_hours > 0:
                speed = 1.0 / time_hours
                strategy.avg_learning_speed = (
                    (strategy.avg_learning_speed * (strategy.times_used - 1) + speed) / 
                    strategy.times_used
                )
            
            # Update retention rate
            strategy.retention_rate = (
                (strategy.retention_rate * (strategy.times_used - 1) + outcome.retention_score) / 
                strategy.times_used
            )
            
            strategy.last_used = datetime.now()
        
        # Track domain performance
        self.domain_performance[outcome.domain].append(outcome.quality_score)
        
        # Track strategy performance
        self.strategy_performance[outcome.strategy_id].append(outcome.quality_score)
        
        logger.info(f"📊 Recorded learning outcome: {outcome.task} ({'✅' if outcome.success else '❌'})")
        
        # Save data
        self._save_data()
        
        # Check if strategy should evolve
        if strategy and strategy.times_used % 10 == 0:  # Every 10 uses
            self._consider_evolution(strategy)
    
    def get_best_strategy(self, domain: str, task: str, context: Dict[str, Any] = None) -> Optional[LearningStrategy]:
        """
        Get the best learning strategy for a task
        
        Args:
            domain: Domain of the task
            task: Task description
            context: Additional context
            
        Returns:
            Best strategy or None
        """
        # Filter strategies by domain
        applicable = [
            s for s in self.strategies.values()
            if s.domain == domain or s.domain == "general"
        ]
        
        if not applicable:
            return None
        
        # Score strategies
        scored = []
        for strategy in applicable:
            score = self._score_strategy(strategy, domain, task, context)
            scored.append((strategy, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best_strategy = scored[0][0] if scored else None
        
        if best_strategy:
            logger.info(f"🎯 Selected strategy: {best_strategy.name} for {task}")
        
        return best_strategy
    
    def _score_strategy(self, strategy: LearningStrategy, domain: str, task: str, context: Dict[str, Any] = None) -> float:
        """Score a strategy for a specific task"""
        score = 0.0
        
        # Base score from success rate
        score += strategy.success_rate * 0.4
        
        # Bonus for learning speed
        score += min(strategy.avg_learning_speed, 1.0) * 0.2
        
        # Bonus for retention
        score += strategy.retention_rate * 0.2
        
        # Bonus for transfer ability
        score += strategy.transfer_ability * 0.1
        
        # Bonus for recent use (recency bias)
        if strategy.last_used:
            days_since_use = (datetime.now() - strategy.last_used).days
            recency_score = max(0, 1.0 - (days_since_use / 30))  # Decay over 30 days
            score += recency_score * 0.1
        
        return score
    
    def analyze_learning_performance(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze learning performance
        
        Args:
            domain: Specific domain to analyze (None for all)
            
        Returns:
            Performance analysis
        """
        if domain:
            outcomes = [o for o in self.outcomes if o.domain == domain]
        else:
            outcomes = self.outcomes
        
        if not outcomes:
            return {
                'total_outcomes': 0,
                'success_rate': 0.0,
                'avg_quality': 0.0,
                'avg_learning_time': 0.0,
                'recommendations': []
            }
        
        # Calculate metrics
        total = len(outcomes)
        successful = sum(1 for o in outcomes if o.success)
        success_rate = successful / total
        
        avg_quality = sum(o.quality_score for o in outcomes) / total
        avg_retention = sum(o.retention_score for o in outcomes) / total
        
        total_time = sum(o.learning_time.total_seconds() for o in outcomes)
        avg_time_hours = (total_time / total) / 3600
        
        # Identify trends
        recent_outcomes = sorted(outcomes, key=lambda o: o.timestamp, reverse=True)[:10]
        recent_success_rate = sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes)
        
        trend = "improving" if recent_success_rate > success_rate else "declining" if recent_success_rate < success_rate else "stable"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(outcomes, success_rate, avg_quality, trend)
        
        return {
            'total_outcomes': total,
            'success_rate': success_rate,
            'avg_quality': avg_quality,
            'avg_retention': avg_retention,
            'avg_learning_time_hours': avg_time_hours,
            'trend': trend,
            'recent_success_rate': recent_success_rate,
            'recommendations': recommendations,
            'best_strategies': self._identify_best_strategies(outcomes)
        }
    
    def _generate_recommendations(self, outcomes: List[LearningOutcome], success_rate: float, avg_quality: float, trend: str) -> List[str]:
        """Generate learning recommendations"""
        recommendations = []
        
        # Low success rate
        if success_rate < 0.6:
            recommendations.append("Success rate is low. Consider using more proven strategies or breaking tasks into smaller steps.")
        
        # Low quality
        if avg_quality < 0.7:
            recommendations.append("Quality scores are low. Focus on deliberate practice and immediate feedback.")
        
        # Declining trend
        if trend == "declining":
            recommendations.append("Performance is declining. Review recent failures and adjust learning approach.")
        
        # Analyze what's working
        successful = [o for o in outcomes if o.success]
        if successful:
            # Find common patterns in successful outcomes
            common_strategies = defaultdict(int)
            for outcome in successful:
                common_strategies[outcome.strategy_id] += 1
            
            if common_strategies:
                best_strategy_id = max(common_strategies.items(), key=lambda x: x[1])[0]
                best_strategy = self.strategies.get(best_strategy_id)
                if best_strategy:
                    recommendations.append(f"'{best_strategy.name}' strategy is working well. Use it more often.")
        
        # Analyze what's failing
        failed = [o for o in outcomes if not o.success]
        if len(failed) > len(successful):
            recommendations.append("More failures than successes. Consider trying different learning strategies or seeking guidance.")
        
        return recommendations
    
    def _identify_best_strategies(self, outcomes: List[LearningOutcome]) -> List[Dict[str, Any]]:
        """Identify best performing strategies"""
        strategy_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'avg_quality': 0.0})
        
        for outcome in outcomes:
            stats = strategy_stats[outcome.strategy_id]
            stats['total'] += 1
            if outcome.success:
                stats['successful'] += 1
            stats['avg_quality'] += outcome.quality_score
        
        # Calculate success rates and average quality
        best_strategies = []
        for strategy_id, stats in strategy_stats.items():
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                continue
            
            success_rate = stats['successful'] / stats['total']
            avg_quality = stats['avg_quality'] / stats['total']
            
            best_strategies.append({
                'strategy': strategy.name,
                'success_rate': success_rate,
                'avg_quality': avg_quality,
                'times_used': stats['total']
            })
        
        # Sort by success rate
        best_strategies.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return best_strategies[:5]  # Top 5
    
    def _consider_evolution(self, strategy: LearningStrategy):
        """Consider evolving a strategy based on performance"""
        # Only evolve if we have enough data
        if strategy.times_used < 20:
            return
        
        # Check if performance is suboptimal
        if strategy.success_rate < 0.7:
            logger.info(f"🧬 Considering evolution for strategy: {strategy.name} (success rate: {strategy.success_rate:.2f})")
            
            # Evolve strategy
            evolved = self._evolve_strategy(strategy)
            if evolved:
                logger.info(f"✨ Evolved strategy: {evolved.name}")
    
    def _evolve_strategy(self, parent: LearningStrategy) -> Optional[LearningStrategy]:
        """Evolve a strategy to improve performance"""
        # Create mutated version
        child = LearningStrategy(
            id=f"{parent.id}_evolved_{len(self.evolutions)}",
            name=f"{parent.name} v2",
            description=f"Evolved version of {parent.name}",
            domain=parent.domain,
            parameters=parent.parameters.copy(),
            evolved_from=parent.id
        )
        
        # Apply mutations
        mutations = []
        
        # Mutation 1: Adjust exploration rate
        if 'exploration_rate' in child.parameters:
            old_rate = child.parameters['exploration_rate']
            # Increase if low success, decrease if high success
            if parent.success_rate < 0.6:
                child.parameters['exploration_rate'] = min(old_rate * 1.2, 0.5)
                mutations.append(f"Increased exploration rate: {old_rate:.2f} → {child.parameters['exploration_rate']:.2f}")
            else:
                child.parameters['exploration_rate'] = max(old_rate * 0.8, 0.1)
                mutations.append(f"Decreased exploration rate: {old_rate:.2f} → {child.parameters['exploration_rate']:.2f}")
        
        # Mutation 2: Adjust difficulty progression
        if 'progression_rate' in child.parameters:
            # Make progression more gradual if success rate is low
            if parent.success_rate < 0.6:
                child.parameters['progression_rate'] = 'slower'
                mutations.append("Changed progression rate to slower")
        
        # Mutation 3: Adjust mastery threshold
        if 'mastery_threshold' in child.parameters:
            old_threshold = child.parameters['mastery_threshold']
            # Lower threshold if success rate is low
            if parent.success_rate < 0.6:
                child.parameters['mastery_threshold'] = max(old_threshold - 0.1, 0.6)
                mutations.append(f"Lowered mastery threshold: {old_threshold:.2f} → {child.parameters['mastery_threshold']:.2f}")
        
        if not mutations:
            return None
        
        # Add evolved strategy
        self.add_strategy(child)
        
        # Record evolution
        evolution = StrategyEvolution(
            id=f"evolution_{len(self.evolutions)}",
            parent_strategy_id=parent.id,
            child_strategy_id=child.id,
            mutations=mutations,
            reason=f"Parent success rate ({parent.success_rate:.2f}) below threshold",
            improvement=0.0  # Will be measured over time
        )
        self.evolutions.append(evolution)
        
        self._save_data()
        
        return child
    
    def optimize_learning_parameters(self, domain: str) -> Dict[str, Any]:
        """
        Optimize learning parameters for a domain
        
        Args:
            domain: Domain to optimize for
            
        Returns:
            Optimized parameters
        """
        # Analyze domain performance
        domain_outcomes = [o for o in self.outcomes if o.domain == domain]
        
        if not domain_outcomes:
            return {}
        
        # Find best performing parameters
        param_performance = defaultdict(lambda: {'total': 0, 'successful': 0})
        
        for outcome in domain_outcomes:
            strategy = self.strategies.get(outcome.strategy_id)
            if not strategy:
                continue
            
            for param, value in strategy.parameters.items():
                key = f"{param}={value}"
                param_performance[key]['total'] += 1
                if outcome.success:
                    param_performance[key]['successful'] += 1
        
        # Calculate success rates
        optimal_params = {}
        for key, stats in param_performance.items():
            if stats['total'] < 3:  # Need minimum data
                continue
            
            success_rate = stats['successful'] / stats['total']
            param_name, param_value = key.split('=', 1)
            
            if param_name not in optimal_params or success_rate > optimal_params[param_name]['success_rate']:
                optimal_params[param_name] = {
                    'value': param_value,
                    'success_rate': success_rate
                }
        
        logger.info(f"🎛️ Optimized {len(optimal_params)} parameters for {domain}")
        
        return optimal_params
    
    def get_learning_insights(self) -> List[str]:
        """Get insights about learning patterns"""
        insights = []
        
        # Overall performance
        if self.outcomes:
            total = len(self.outcomes)
            successful = sum(1 for o in self.outcomes if o.success)
            success_rate = successful / total
            
            insights.append(f"Overall learning success rate: {success_rate:.1%} ({successful}/{total} attempts)")
        
        # Best domain
        if self.domain_performance:
            domain_avg = {
                domain: sum(scores) / len(scores)
                for domain, scores in self.domain_performance.items()
            }
            best_domain = max(domain_avg.items(), key=lambda x: x[1])
            insights.append(f"Best performing domain: {best_domain[0]} (avg quality: {best_domain[1]:.2f})")
        
        # Best strategy
        if self.strategy_performance:
            strategy_avg = {
                sid: sum(scores) / len(scores)
                for sid, scores in self.strategy_performance.items()
            }
            best_strategy_id = max(strategy_avg.items(), key=lambda x: x[1])[0]
            best_strategy = self.strategies.get(best_strategy_id)
            if best_strategy:
                insights.append(f"Most effective strategy: {best_strategy.name} (avg quality: {strategy_avg[best_strategy_id]:.2f})")
        
        # Evolution insights
        if self.evolutions:
            insights.append(f"Evolved {len(self.evolutions)} strategies to improve performance")
        
        # Learning speed trend
        if len(self.outcomes) >= 10:
            recent = self.outcomes[-10:]
            old = self.outcomes[:10]
            
            recent_avg_time = sum(o.learning_time.total_seconds() for o in recent) / len(recent)
            old_avg_time = sum(o.learning_time.total_seconds() for o in old) / len(old)
            
            if recent_avg_time < old_avg_time:
                speedup = ((old_avg_time - recent_avg_time) / old_avg_time) * 100
                insights.append(f"Learning speed improved by {speedup:.1f}% over time")
        
        return insights
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get meta-learning statistics"""
        return {
            'total_strategies': len(self.strategies),
            'total_outcomes': len(self.outcomes),
            'total_evolutions': len(self.evolutions),
            'domains_tracked': len(self.domain_performance),
            'overall_success_rate': (
                sum(1 for o in self.outcomes if o.success) / len(self.outcomes)
                if self.outcomes else 0.0
            ),
            'avg_learning_time_hours': (
                sum(o.learning_time.total_seconds() for o in self.outcomes) / len(self.outcomes) / 3600
                if self.outcomes else 0.0
            ),
            'best_strategies': self._identify_best_strategies(self.outcomes)
        }
    
    def _save_data(self):
        """Save meta-learning data to persistent storage"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'strategies': [
                    {
                        **s.__dict__,
                        'created_at': s.created_at.isoformat() if s.created_at else None,
                        'last_used': s.last_used.isoformat() if s.last_used else None
                    }
                    for s in self.strategies.values()
                ],
                'outcomes': [
                    {
                        **o.__dict__,
                        'timestamp': o.timestamp.isoformat(),
                        'learning_time': o.learning_time.total_seconds()
                    }
                    for o in self.outcomes
                ],
                'evolutions': [
                    {
                        **e.__dict__,
                        'timestamp': e.timestamp.isoformat()
                    }
                    for e in self.evolutions
                ],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved meta-learning data to {self.storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save meta-learning data: {e}")
    
    def _load_data(self):
        """Load meta-learning data from persistent storage"""
        try:
            import os
            if not os.path.exists(self.storage_path):
                logger.info("No existing meta-learning data found")
                return
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load strategies (merge with defaults, don't overwrite)
            for strategy_data in data.get('strategies', []):
                if strategy_data['id'] not in self.strategies:
                    strategy_data['created_at'] = datetime.fromisoformat(strategy_data['created_at']) if strategy_data.get('created_at') else datetime.now()
                    strategy_data['last_used'] = datetime.fromisoformat(strategy_data['last_used']) if strategy_data.get('last_used') else None
                    strategy = LearningStrategy(**strategy_data)
                    self.strategies[strategy.id] = strategy
            
            # Load outcomes
            for outcome_data in data.get('outcomes', []):
                outcome_data['timestamp'] = datetime.fromisoformat(outcome_data['timestamp'])
                outcome_data['learning_time'] = timedelta(seconds=outcome_data['learning_time'])
                outcome = LearningOutcome(**outcome_data)
                self.outcomes.append(outcome)
            
            # Load evolutions
            for evolution_data in data.get('evolutions', []):
                evolution_data['timestamp'] = datetime.fromisoformat(evolution_data['timestamp'])
                evolution = StrategyEvolution(**evolution_data)
                self.evolutions.append(evolution)
            
            logger.info(f"📂 Loaded meta-learning data: {len(self.outcomes)} outcomes, {len(self.evolutions)} evolutions")
        except Exception as e:
            logger.error(f"❌ Failed to load meta-learning data: {e}")


# Singleton instance
_meta_learner = None

def get_meta_learner(knowledge_graph=None, storage_path: Optional[str] = None) -> MetaLearner:
    """Get or create singleton meta-learner"""
    global _meta_learner
    if _meta_learner is None:
        _meta_learner = MetaLearner(knowledge_graph, storage_path)
    return _meta_learner
