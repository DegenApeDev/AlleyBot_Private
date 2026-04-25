"""
AlleyBot Strategy Evolver - Phase 1: Self-Reflection System

Analyzes historical action data and evolves strategies through mutation.
Implements "keep winners, discard losers" logic for continuous improvement.

Part of AGI Core - Phase 1: Self-Reflection
"""

import json
import sqlite3
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from src.agentic.action_logger import ActionLogger
from src.agentic.planning import get_plan_manager

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of strategies that can evolve"""
    ENGAGEMENT = "engagement"  # Like, reply, repost strategies
    CONTENT = "content"  # Post content generation
    TIMING = "timing"  # When to post/act
    TARGETING = "targeting"  # Who to engage with
    TONE = "tone"  # Response tone/personality


@dataclass
class Strategy:
    """A single evolved strategy with performance metrics"""
    id: str
    name: str
    strategy_type: StrategyType
    parameters: Dict[str, Any]  # Strategy-specific params
    created_at: datetime
    generation: int  # Evolution generation number
    parent_id: Optional[str]  # Parent strategy ID if mutated
    
    # Performance tracking
    times_used: int = 0
    successes: int = 0
    failures: int = 0
    total_engagement: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.0
    
    @property
    def fitness_score(self) -> float:
        """Overall fitness score (0-1) combining success rate and engagement"""
        if self.times_used < 5:  # Minimum sample size
            return 0.5  # Neutral for new strategies
        
        success_weight = 0.6
        engagement_weight = 0.4
        
        # Normalize engagement (assume max 100 per action)
        normalized_engagement = min(1.0, self.total_engagement / (self.times_used * 100))
        
        return (self.success_rate * success_weight) + (normalized_engagement * engagement_weight)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'strategy_type': self.strategy_type.value,
            'created_at': self.created_at.isoformat(),
            'success_rate': self.success_rate,
            'fitness_score': self.fitness_score
        }


@dataclass
class StrategyMutation:
    """Result of a strategy mutation"""
    parent_strategy: Strategy
    child_strategy: Strategy
    mutations_applied: List[str]
    mutation_reason: str


@dataclass
class EvolutionReport:
    """Report of an evolution cycle"""
    timestamp: datetime
    strategies_evaluated: int
    top_performers: List[Strategy]
    underperformers: List[Strategy]
    new_mutations: List[StrategyMutation]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'strategies_evaluated': self.strategies_evaluated,
            'top_performers': [s.to_dict() for s in self.top_performers],
            'underperformers': [s.to_dict() for s in self.underperformers],
            'new_mutations': [
                {
                    'parent': m.parent_strategy.id,
                    'child': m.child_strategy.id,
                    'mutations': m.mutations_applied,
                    'reason': m.mutation_reason
                }
                for m in self.new_mutations
            ],
            'recommendations': self.recommendations
        }


class StrategyEvolver:
    """
    Evolves strategies through analysis and mutation.
    
    Usage:
        evolver = StrategyEvolver()
        
        # Run evolution cycle
        report = evolver.evolve()
        
        # Get best strategy for a situation
        strategy = evolver.get_best_strategy(StrategyType.ENGAGEMENT)
        
        # Record outcome
        evolver.record_outcome(strategy.id, success=True, engagement=12)
    """
    
    DB_PATH = Path('data/strategies.db')
    
    # Mutation parameters
    MUTATION_RATE = 0.3  # 30% chance to mutate a parameter
    ELITE_THRESHOLD = 0.7  # Top 30% are "elite"
    CULL_THRESHOLD = 0.3  # Bottom 30% get culled
    MAX_STRATEGIES_PER_TYPE = 10
    MIN_SAMPLE_SIZE = 5  # Minimum uses before evaluation
    
    def __init__(self, action_logger: Optional[ActionLogger] = None):
        self.action_logger = action_logger or ActionLogger()
        self.plan_manager = get_plan_manager()
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._ensure_seed_strategies()

    def _strategy_type_to_action_family(self, strategy_type: StrategyType) -> Optional[str]:
        """Map strategy categories to persisted action-family trust labels."""
        mapping = {
            StrategyType.ENGAGEMENT: 'engage',
            StrategyType.CONTENT: 'post',
            StrategyType.TIMING: 'post',
            StrategyType.TARGETING: 'engage',
            StrategyType.TONE: 'post',
        }
        return mapping.get(strategy_type)
    
    def _init_db(self) -> None:
        """Initialize strategy database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    strategy_type TEXT,
                    parameters TEXT,
                    created_at TEXT,
                    generation INTEGER,
                    parent_id TEXT,
                    times_used INTEGER DEFAULT 0,
                    successes INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    total_engagement REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategy_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT,
                    action_id TEXT,
                    success INTEGER,
                    engagement REAL,
                    timestamp TEXT,
                    context TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS evolution_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    report_data TEXT
                )
            ''')
            
            conn.commit()
    
    def _ensure_seed_strategies(self) -> None:
        """Create initial seed strategies if none exist"""
        existing = self._get_all_strategies()
        if existing:
            return
        
        seed_strategies = [
            # Engagement strategies
            Strategy(
                id="eng_like_high_conf",
                name="Like High Confidence Posts",
                strategy_type=StrategyType.ENGAGEMENT,
                parameters={
                    'action': 'like',
                    'min_confidence': 0.8,
                    'field_status': ['Stable'],
                    'max_per_hour': 10
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            Strategy(
                id="eng_reply_mentions",
                name="Reply to Mentions",
                strategy_type=StrategyType.ENGAGEMENT,
                parameters={
                    'action': 'reply',
                    'trigger': 'mention',
                    'response_style': 'helpful',
                    'max_per_hour': 5
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            Strategy(
                id="eng_reply_trending",
                name="Reply to Trending Topics",
                strategy_type=StrategyType.ENGAGEMENT,
                parameters={
                    'action': 'reply',
                    'trigger': 'trending',
                    'min_topic_strength': 0.7,
                    'response_style': 'insightful',
                    'max_per_hour': 3
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            # Timing strategies
            Strategy(
                id="time_peak_hours",
                name="Post During Peak Hours",
                strategy_type=StrategyType.TIMING,
                parameters={
                    'peak_hours': [9, 12, 18, 21],
                    'timezone': 'auto',
                    'min_interval_minutes': 30
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            # Content strategies
            Strategy(
                id="content_value_first",
                name="Value-First Content",
                strategy_type=StrategyType.CONTENT,
                parameters={
                    'tone': 'educational',
                    'include_data': True,
                    'max_length': 280,
                    'hashtag_strategy': 'minimal'
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            Strategy(
                id="content_personal_story",
                name="Personal Story Content",
                strategy_type=StrategyType.CONTENT,
                parameters={
                    'tone': 'conversational',
                    'include_lessons': True,
                    'max_length': 500,
                    'hashtag_strategy': 'storytelling'
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            # Targeting strategies
            Strategy(
                id="target_high_synergy",
                name="Target High Synergy Users",
                strategy_type=StrategyType.TARGETING,
                parameters={
                    'min_synergy_score': 0.7,
                    'prioritize_active': True,
                    'avoid_spam_accounts': True
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            ),
            # Tone strategies
            Strategy(
                id="tone_adaptive",
                name="Adaptive Tone Matching",
                strategy_type=StrategyType.TONE,
                parameters={
                    'match_conversation_tone': True,
                    'base_tone': 'helpful',
                    'max_enthusiasm': 0.8,
                    'never_negative': True
                },
                created_at=datetime.now(),
                generation=0,
                parent_id=None
            )
        ]
        
        for strategy in seed_strategies:
            self._save_strategy(strategy)
        
        logger.info(f"🌱 Created {len(seed_strategies)} seed strategies")
    
    def _save_strategy(self, strategy: Strategy) -> None:
        """Save strategy to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO strategies 
                (id, name, strategy_type, parameters, created_at, generation, parent_id,
                 times_used, successes, failures, total_engagement, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy.id,
                strategy.name,
                strategy.strategy_type.value,
                json.dumps(strategy.parameters),
                strategy.created_at.isoformat(),
                strategy.generation,
                strategy.parent_id,
                strategy.times_used,
                strategy.successes,
                strategy.failures,
                strategy.total_engagement,
                1
            ))
            conn.commit()
    
    def _get_all_strategies(self) -> List[Strategy]:
        """Get all strategies from database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM strategies WHERE is_active = 1'
            ).fetchall()
            return [self._row_to_strategy(row) for row in rows]
    
    def _row_to_strategy(self, row: sqlite3.Row) -> Strategy:
        """Convert database row to Strategy"""
        return Strategy(
            id=row['id'],
            name=row['name'],
            strategy_type=StrategyType(row['strategy_type']),
            parameters=json.loads(row['parameters']),
            created_at=datetime.fromisoformat(row['created_at']),
            generation=row['generation'],
            parent_id=row['parent_id'],
            times_used=row['times_used'],
            successes=row['successes'],
            failures=row['failures'],
            total_engagement=row['total_engagement']
        )
    
    def evolve(self) -> EvolutionReport:
        """
        Run one evolution cycle:
        1. Evaluate all strategies
        2. Identify top performers and underperformers
        3. Mutate top performers
        4. Cull underperformers
        5. Generate recommendations
        """
        logger.info("🧬 Starting evolution cycle...")
        
        strategies = self._get_all_strategies()
        
        # Sort by fitness
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        # Identify tiers
        total = len(strategies)
        elite_count = max(1, int(total * (1 - self.ELITE_THRESHOLD)))
        cull_count = max(1, int(total * self.CULL_THRESHOLD))
        
        top_performers = strategies[:elite_count]
        underperformers = strategies[-cull_count:] if total > cull_count else []
        
        # Mutate top performers
        new_mutations = []
        for strategy in top_performers:
            if strategy.times_used >= self.MIN_SAMPLE_SIZE:
                mutation = self._mutate_strategy(strategy)
                if mutation:
                    new_mutations.append(mutation)
        
        # Cull underperformers
        culled = 0
        for strategy in underperformers:
            if strategy.times_used >= self.MIN_SAMPLE_SIZE * 2:
                self._deactivate_strategy(strategy.id)
                culled += 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(strategies)
        
        report = EvolutionReport(
            timestamp=datetime.now(),
            strategies_evaluated=len(strategies),
            top_performers=top_performers[:5],
            underperformers=underperformers[:5],
            new_mutations=new_mutations,
            recommendations=recommendations
        )
        
        # Save report
        self._save_report(report)
        
        logger.info(
            f"✅ Evolution complete: {len(strategies)} strategies, "
            f"{len(new_mutations)} mutations, {culled} culled"
        )
        
        return report
    
    def _mutate_strategy(self, parent: Strategy) -> Optional[StrategyMutation]:
        """Create a mutated child strategy from a parent"""
        mutations = []
        new_params = dict(parent.parameters)
        
        # Apply random mutations based on strategy type
        if parent.strategy_type == StrategyType.ENGAGEMENT:
            if 'min_confidence' in new_params and random.random() < self.MUTATION_RATE:
                # Mutate confidence threshold
                delta = random.uniform(-0.1, 0.1)
                new_params['min_confidence'] = max(0.5, min(0.95, new_params['min_confidence'] + delta))
                mutations.append(f"confidence_threshold: {delta:+.2f}")
            
            if 'max_per_hour' in new_params and random.random() < self.MUTATION_RATE:
                # Mutate rate limit
                delta = random.choice([-2, -1, 1, 2])
                new_params['max_per_hour'] = max(1, new_params['max_per_hour'] + delta)
                mutations.append(f"max_per_hour: {delta:+d}")
        
        elif parent.strategy_type == StrategyType.TIMING:
            if 'peak_hours' in new_params and random.random() < self.MUTATION_RATE:
                # Add or remove a peak hour
                if random.random() < 0.5 and len(new_params['peak_hours']) < 6:
                    new_hour = random.randint(0, 23)
                    if new_hour not in new_params['peak_hours']:
                        new_params['peak_hours'].append(new_hour)
                        new_params['peak_hours'].sort()
                        mutations.append(f"added_peak_hour: {new_hour}")
                elif len(new_params['peak_hours']) > 2:
                    removed = random.choice(new_params['peak_hours'])
                    new_params['peak_hours'].remove(removed)
                    mutations.append(f"removed_peak_hour: {removed}")
        
        elif parent.strategy_type == StrategyType.CONTENT:
            if 'tone' in new_params and random.random() < self.MUTATION_RATE:
                tones = ['educational', 'conversational', 'professional', 'casual', 'witty']
                current = new_params['tone']
                new_tone = random.choice([t for t in tones if t != current])
                new_params['tone'] = new_tone
                mutations.append(f"tone: {current} -> {new_tone}")
            
            if 'max_length' in new_params and random.random() < self.MUTATION_RATE:
                delta = random.choice([-50, -20, 20, 50])
                new_params['max_length'] = max(100, min(1000, new_params['max_length'] + delta))
                mutations.append(f"max_length: {delta:+d}")
        
        elif parent.strategy_type == StrategyType.TARGETING:
            if 'min_synergy_score' in new_params and random.random() < self.MUTATION_RATE:
                delta = random.uniform(-0.1, 0.1)
                new_params['min_synergy_score'] = max(0.3, min(0.9, new_params['min_synergy_score'] + delta))
                mutations.append(f"synergy_threshold: {delta:+.2f}")
        
        # Only create mutation if we actually mutated something
        if not mutations:
            return None
        
        child = Strategy(
            id=f"{parent.id}_gen{parent.generation + 1}_{random.randint(1000, 9999)}",
            name=f"{parent.name} (Gen {parent.generation + 1})",
            strategy_type=parent.strategy_type,
            parameters=new_params,
            created_at=datetime.now(),
            generation=parent.generation + 1,
            parent_id=parent.id
        )
        
        self._save_strategy(child)
        
        return StrategyMutation(
            parent_strategy=parent,
            child_strategy=child,
            mutations_applied=mutations,
            mutation_reason=f"Successful parent (fitness: {parent.fitness_score:.2f})"
        )
    
    def _deactivate_strategy(self, strategy_id: str) -> None:
        """Deactivate a strategy (soft delete)"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute(
                'UPDATE strategies SET is_active = 0 WHERE id = ?',
                (strategy_id,)
            )
            conn.commit()
        logger.info(f"🗑️ Culled strategy: {strategy_id}")
    
    def _generate_recommendations(self, strategies: List[Strategy]) -> List[str]:
        """Generate actionable recommendations based on data"""
        recommendations = []
        trust_state = self.plan_manager.get_action_family_states()
        
        # Group by type
        by_type: Dict[StrategyType, List[Strategy]] = {}
        for s in strategies:
            by_type.setdefault(s.strategy_type, []).append(s)
        
        for stype, slist in by_type.items():
            if not slist:
                continue
            
            avg_fitness = sum(s.fitness_score for s in slist) / len(slist)
            best = max(slist, key=lambda s: s.fitness_score)
            
            if avg_fitness < 0.5:
                recommendations.append(
                    f"⚠️ {stype.value} strategies underperforming (avg fitness: {avg_fitness:.2f}). "
                    f"Consider manual review."
                )
            
            if best.fitness_score > 0.8 and best.times_used >= 10:
                recommendations.append(
                    f"✅ Strategy '{best.name}' is performing excellently "
                    f"({best.success_rate:.0%} success, {best.times_used} uses). "
                    f"Consider using as template."
                )

            action_family = self._strategy_type_to_action_family(stype)
            family_state = trust_state.get(action_family or '', {}) if action_family else {}
            trust_bucket = family_state.get('trust_bucket')
            if trust_bucket == 'degraded':
                recommendations.append(
                    f"🚫 {stype.value} strategy family is currently degraded. Prefer safer alternates until routed evidence improves."
                )
            elif trust_bucket == 'cooling_down':
                recommendations.append(
                    f"⏳ {stype.value} strategy family is cooling down. Limit aggressive reuse until cooldown expires."
                )
            elif trust_bucket == 'recovering':
                recommendations.append(
                    f"🔄 {stype.value} strategy family is recovering. Reintroduce cautiously with evidence-driven monitoring."
                )
        
        # Check for gaps
        active_types = set(by_type.keys())
        all_types = set(StrategyType)
        missing = all_types - active_types
        if missing:
            recommendations.append(
                f"📝 Missing strategies for: {', '.join(m.value for m in missing)}"
            )
        
        return recommendations
    
    def _save_report(self, report: EvolutionReport) -> None:
        """Save evolution report to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute(
                'INSERT INTO evolution_reports (timestamp, report_data) VALUES (?, ?)',
                (report.timestamp.isoformat(), json.dumps(report.to_dict()))
            )
            conn.commit()
    
    def get_best_strategy(self, strategy_type: StrategyType) -> Optional[Strategy]:
        """Get the best performing strategy of a given type"""
        strategies = [
            s for s in self._get_all_strategies()
            if s.strategy_type == strategy_type
        ]
        
        if not strategies:
            return None
        
        # Sort by fitness, prefer strategies with more samples
        return max(strategies, key=lambda s: (s.fitness_score, s.times_used))
    
    def record_outcome(self, 
                       strategy_id: str,
                       success: bool,
                       engagement: float = 0.0,
                       action_id: Optional[str] = None,
                       context: Optional[Dict] = None) -> None:
        """Record the outcome of using a strategy"""
        normalized_context = dict(context or {})
        outcome_record = normalized_context.get('outcome_record') or {}
        prediction_evaluation = outcome_record.get('prediction_evaluation') or normalized_context.get('prediction_evaluation') or {}
        ranking_evidence = outcome_record.get('ranking_evidence') or normalized_context.get('ranking_evidence') or {}
        dispatch_learning_summary = outcome_record.get('dispatch_learning_summary') or normalized_context.get('dispatch_learning_summary') or {}
        dispatch_path = outcome_record.get('dispatch_path') or normalized_context.get('dispatch_path')
        legacy_fallback_used = outcome_record.get('legacy_fallback_used')
        if legacy_fallback_used is None:
            legacy_fallback_used = normalized_context.get('legacy_fallback_used')
        fallback_details = outcome_record.get('fallback_details') or normalized_context.get('fallback_details') or {}
        if outcome_record:
            normalized_context['action_type'] = outcome_record.get('action_type')
            normalized_context['plugin'] = outcome_record.get('plugin')
            normalized_context['goal_id'] = outcome_record.get('goal_id')
            normalized_context['trigger'] = outcome_record.get('trigger')
            normalized_context['mismatch_score'] = outcome_record.get('mismatch_score')
        if prediction_evaluation:
            normalized_context['prediction_evaluation'] = prediction_evaluation
            normalized_context['confidence_calibration'] = prediction_evaluation.get('confidence_calibration')
            normalized_context['value_alignment'] = prediction_evaluation.get('value_alignment')
            normalized_context['risk_alignment'] = prediction_evaluation.get('risk_alignment')
        if ranking_evidence:
            normalized_context['ranking_evidence'] = ranking_evidence
            normalized_context['predicted_value'] = ranking_evidence.get('predicted_value')
            normalized_context['memory_shaped_adjustment'] = ranking_evidence.get('memory_shaped_adjustment')
            normalized_context['ranking_used_memory_recall'] = bool(
                (ranking_evidence.get('memory_relevance_count', 0) or 0) > 0
                or ranking_evidence.get('entity_context_found')
            )
        if dispatch_learning_summary:
            normalized_context['dispatch_learning_summary'] = dispatch_learning_summary
            normalized_context['golden_path_alignment'] = dispatch_learning_summary.get('golden_path_alignment')
        if dispatch_path:
            normalized_context['dispatch_path'] = dispatch_path
        if legacy_fallback_used is not None:
            normalized_context['legacy_fallback_used'] = bool(legacy_fallback_used)
        if fallback_details:
            normalized_context['fallback_details'] = fallback_details

        with sqlite3.connect(self.DB_PATH) as conn:
            # Record outcome
            conn.execute('''
                INSERT INTO strategy_outcomes 
                (strategy_id, action_id, success, engagement, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                strategy_id,
                action_id,
                1 if success else 0,
                engagement,
                datetime.now().isoformat(),
                json.dumps(normalized_context) if normalized_context else None
            ))
            
            # Update strategy stats
            conn.execute('''
                UPDATE strategies 
                SET times_used = times_used + 1,
                    successes = successes + ?,
                    failures = failures + ?,
                    total_engagement = total_engagement + ?
                WHERE id = ?
            ''', (
                1 if success else 0,
                0 if success else 1,
                engagement,
                strategy_id
            ))
            
            conn.commit()
    
    def get_strategies_by_type(self, strategy_type: StrategyType) -> List[Strategy]:
        """Get all strategies of a specific type"""
        return [
            s for s in self._get_all_strategies()
            if s.strategy_type == strategy_type
        ]
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent evolution reports"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT report_data FROM evolution_reports ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            ).fetchall()
            return [json.loads(row['report_data']) for row in rows]
    
    def get_strategies_ranked(self) -> Dict[StrategyType, List[Strategy]]:
        """Get all strategies ranked by fitness, grouped by type"""
        result: Dict[StrategyType, List[Strategy]] = {}
        
        for stype in StrategyType:
            strategies = self.get_strategies_by_type(stype)
            strategies.sort(key=lambda s: s.fitness_score, reverse=True)
            result[stype] = strategies
        
        return result
    
    # 7.4: Meta-learning - learn which strategies work in which conditions
    def get_meta_learned_conditions(self) -> Dict[str, Any]:
        """
        Get meta-learned associations between conditions and strategies.
        Returns which conditions favor which strategies.
        """
        meta_learned = {
            'time_of_day': {},
            'day_of_week': {},
            'platform': {},
            'domain_context': {}
        }
        
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                # Analyze time-of-day performance
                for row in conn.execute('''
                    SELECT strategy_id, 
                           strftime('%H', timestamp) as hour,
                           AVG(success) as avg_success
                    FROM strategy_outcomes
                    GROUP BY strategy_id, hour
                ''').fetchall():
                    if row['avg_success'] is not None:
                        strategy = self._load_strategy(row['strategy_id'])
                        if strategy:
                            meta_learned['time_of_day'].setdefault(row['hour'], []).append({
                                'strategy': strategy.name,
                                'success_rate': row['avg_success']
                            })
                
                # Analyze day-of-week performance
                for row in conn.execute('''
                    SELECT strategy_id,
                           strftime('%w', timestamp) as dow,
                           AVG(success) as avg_success
                    FROM strategy_outcomes
                    GROUP BY strategy_id, dow
                ''').fetchall():
                    if row['avg_success'] is not None:
                        strategy = self._load_strategy(row['strategy_id'])
                        if strategy:
                            meta_learned['day_of_week'].setdefault(row['dow'], []).append({
                                'strategy': strategy.name,
                                'success_rate': row['avg_success']
                            })
        
        except Exception as e:
            logger.debug(f"Meta-learning query error: {e}")
        
        return meta_learned
    
    def get_best_strategy_for_condition(self, condition_type: str, condition_value: str) -> Optional[Strategy]:
        """
        Get the best performing strategy for a given condition.
        Used to select strategies based on context.
        """
        meta = self.get_meta_learned_conditions()
        condition_data = meta.get(condition_type, {}).get(condition_value, [])
        
        if not condition_data:
            return None
        
        # Return highest success rate for this condition
        best = max(condition_data, key=lambda x: x['success_rate'])
        
        # Find the strategy object
        for strategy in self.strategies.values():
            if strategy.name == best['strategy']:
                return strategy
        
        return None
    
    def recommend_strategy(self, context: Dict) -> Optional[Strategy]:
        """
        Recommend a strategy based on current context.
        Uses meta-learned condition->strategy mappings.
        """
        from datetime import datetime
        
        current_hour = datetime.now().strftime('%H')
        current_dow = datetime.now().strftime('%w')
        
        # Try time-based recommendation first
        best = self.get_best_strategy_for_condition('time_of_day', current_hour)
        if best and best.fitness_score >= 0.5:
            return best
        
        # Try day-of-week
        best = self.get_best_strategy_for_condition('day_of_week', current_dow)
        if best and best.fitness_score >= 0.5:
            return best
        
        # Fall back to overall best
        ranked = self.get_strategies_ranked()
        for stype in StrategyType:
            if ranked.get(stype):
                return ranked[stype][0]
        
        return None


# Singleton instance
_evolver_instance: Optional[StrategyEvolver] = None


def get_strategy_evolver(action_logger: Optional[ActionLogger] = None) -> StrategyEvolver:
    """Get or create StrategyEvolver singleton"""
    global _evolver_instance
    if _evolver_instance is None:
        _evolver_instance = StrategyEvolver(action_logger)
    return _evolver_instance
