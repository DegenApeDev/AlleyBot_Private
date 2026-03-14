"""
Meta-Learning System for AGI

This is learning at the cognitive level:
- Learning which learning strategies work best
- Adapting how the agent learns from experience
- Optimizing the learning process itself

Instead of just storing memories, this system tracks:
- Which types of memories lead to successful outcomes
- Which learning rates work best for different domains
- When to explore vs exploit based on past learning efficiency

This enables the agent to become a better learner over time.
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict


@dataclass
class LearningEpisode:
    """
    A learning attempt and its effectiveness
    
    Tracks not just what was learned, but how well the learning worked.
    """
    id: str
    timestamp: datetime
    
    # What was the learning situation
    domain: str  # 'social', 'content', 'onchain', 'coding', etc.
    context: str  # Description of situation
    
    # What learning strategy was used
    strategy: str  # 'trial_error', 'pattern_matching', 'analogy', 'deduction'
    
    # Outcome
    success: bool
    time_to_success: float  # Seconds or interactions
    retention_score: float  # How well remembered (0-1)
    transfer_score: float  # How applicable to other situations (0-1)
    
    # Learning parameters used
    exploration_rate: float  # 0 = pure exploitation, 1 = pure exploration
    memory_depth: int  # How far back memories were considered
    
    # Meta-feedback
    would_repeat: bool  # Was this a good approach
    notes: str = ""


class MetaLearningEngine:
    """
    Learns about learning itself
    
    Tracks effectiveness of different learning strategies across domains
    and adapts future learning based on what works best.
    """
    
    def __init__(self, storage_path: str = 'data/meta_learning.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Learning history
        self.episodes: List[LearningEpisode] = []
        
        # Strategy effectiveness by domain
        # domain -> strategy -> [successes, total_attempts]
        self.strategy_stats: Dict[str, Dict[str, List[int]]] = defaultdict(
            lambda: defaultdict(lambda: [0, 0])
        )
        
        # Optimal parameters by domain (learned)
        self.optimal_params: Dict[str, Dict[str, float]] = {
            'social': {'exploration_rate': 0.3, 'memory_depth': 10},
            'content': {'exploration_rate': 0.2, 'memory_depth': 20},
            'onchain': {'exploration_rate': 0.1, 'memory_depth': 5},
            'coding': {'exploration_rate': 0.4, 'memory_depth': 15}
        }
        
        self._load()
    
    def record_learning_attempt(self, domain: str, context: str, strategy: str,
                                success: bool, time_to_success: float = 0,
                                exploration_rate: float = 0.3, 
                                memory_depth: int = 10,
                                notes: str = "") -> str:
        """
        Record a learning episode for meta-analysis
        
        This is called whenever the system learns something new.
        It tracks whether the learning was effective.
        """
        episode_id = f"learn_{datetime.now().timestamp()}"
        
        episode = LearningEpisode(
            id=episode_id,
            timestamp=datetime.now(),
            domain=domain,
            context=context,
            strategy=strategy,
            success=success,
            time_to_success=time_to_success,
            retention_score=0.5,  # Will be updated later
            transfer_score=0.5,   # Will be updated later
            exploration_rate=exploration_rate,
            memory_depth=memory_depth,
            would_repeat=success,  # Assume yes if successful
            notes=notes
        )
        
        self.episodes.append(episode)
        
        # Update strategy stats
        stats = self.strategy_stats[domain][strategy]
        if success:
            stats[0] += 1  # successes
        stats[1] += 1    # total
        
        # Update optimal parameters based on success
        self._update_optimal_params(domain, exploration_rate, memory_depth, success)
        
        self._save()
        return episode_id
    
    def _update_optimal_params(self, domain: str, exploration: float, 
                               memory_depth: int, success: bool):
        """
        Gradually adjust optimal parameters based on outcomes
        
        Uses simple gradient descent-like approach:
        - If successful, move params slightly toward what was used
        - If failed, move away
        """
        if domain not in self.optimal_params:
            self.optimal_params[domain] = {
                'exploration_rate': 0.3,
                'memory_depth': 10
            }
        
        params = self.optimal_params[domain]
        learning_rate = 0.1
        
        # Update exploration rate
        current_exploration = params['exploration_rate']
        if success:
            # Move toward successful rate
            params['exploration_rate'] = current_exploration + learning_rate * (exploration - current_exploration)
        else:
            # Move away from unsuccessful rate
            params['exploration_rate'] = current_exploration - learning_rate * (exploration - current_exploration) * 0.5
        
        # Clamp to valid range
        params['exploration_rate'] = max(0.0, min(1.0, params['exploration_rate']))
        
        # Update memory depth (discrete, so just adjust if successful)
        if success:
            current_depth = params['memory_depth']
            if memory_depth > current_depth:
                params['memory_depth'] = min(50, current_depth + 1)
            elif memory_depth < current_depth:
                params['memory_depth'] = max(1, current_depth - 1)
    
    def get_best_strategy(self, domain: str) -> Tuple[str, float]:
        """
        Get the best learning strategy for a domain
        
        Returns:
            (strategy_name, expected_success_rate)
        """
        if domain not in self.strategy_stats:
            return ('trial_error', 0.5)  # Default
        
        strategies = self.strategy_stats[domain]
        best_strategy = None
        best_rate = 0.0
        
        for strategy, stats in strategies.items():
            successes, total = stats
            if total > 0:
                rate = successes / total
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy
        
        return (best_strategy or 'trial_error', best_rate)
    
    def get_optimal_params(self, domain: str) -> Dict[str, Any]:
        """
        Get learned optimal parameters for a domain
        
        These are the parameters that have worked best historically.
        """
        return self.optimal_params.get(domain, {
            'exploration_rate': 0.3,
            'memory_depth': 10
        })
    
    def should_explore(self, domain: str, situation_novelty: float) -> bool:
        """
        Decide whether to explore or exploit based on meta-learning
        
        Args:
            domain: Learning domain
            situation_novelty: 0-1 score of how novel this situation is
            
        Returns:
            True = try something new (explore)
            False = use known good approach (exploit)
        """
        params = self.get_optimal_params(domain)
        base_exploration = params['exploration_rate']
        
        # Adjust based on novelty - more novel = more exploration needed
        adjusted_threshold = base_exploration * (1 + situation_novelty) / 2
        
        return np.random.random() < adjusted_threshold
    
    def estimate_learning_difficulty(self, domain: str, context: str) -> float:
        """
        Estimate how hard it will be to learn something
        
        Based on historical success rate in similar contexts.
        Returns 0-1 where 1 = very difficult.
        """
        # Get recent episodes in this domain
        recent_episodes = [
            e for e in self.episodes 
            if e.domain == domain 
            and (datetime.now() - e.timestamp).days < 30
        ]
        
        if not recent_episodes:
            return 0.5  # Unknown difficulty
        
        # Calculate historical success rate
        success_rate = sum(1 for e in recent_episodes if e.success) / len(recent_episodes)
        
        # Estimate time required
        avg_time = np.mean([e.time_to_success for e in recent_episodes if e.time_to_success > 0])
        
        # Combine into difficulty score (inverse of success, normalized time)
        difficulty = (1 - success_rate) * 0.7
        if avg_time > 0:
            time_factor = min(1.0, avg_time / 300)  # Normalize to 5 minutes
            difficulty += time_factor * 0.3
        
        return min(1.0, difficulty)
    
    def get_learning_insights(self) -> List[str]:
        """
        Generate insights about learning effectiveness
        
        Returns actionable insights like:
        - "Pattern matching works best for content optimization"
        - "I learn social interactions faster with lower exploration"
        """
        insights = []
        
        # Strategy effectiveness by domain
        for domain in self.strategy_stats.keys():
            best_strategy, rate = self.get_best_strategy(domain)
            if best_strategy and rate > 0.6:
                insights.append(
                    f"{best_strategy.replace('_', ' ').title()} is most effective for {domain} "
                    f"({rate:.0%} success rate)"
                )
        
        # Optimal parameter recommendations
        for domain, params in self.optimal_params.items():
            exploration = params['exploration_rate']
            depth = params['memory_depth']
            insights.append(
                f"For {domain}: use {exploration:.0%} exploration, "
                f"consider last {depth} memories"
            )
        
        # Trend analysis
        if len(self.episodes) > 10:
            recent = self.episodes[-10:]
            older = self.episodes[-20:-10]
            
            recent_success = sum(1 for e in recent if e.success) / len(recent)
            older_success = sum(1 for e in older if e.success) / len(older) if older else 0.5
            
            if recent_success > older_success + 0.2:
                insights.append(f"Learning efficiency improving (+{(recent_success - older_success):.0%})")
            elif recent_success < older_success - 0.2:
                insights.append(f"Learning efficiency declining (-{(older_success - recent_success):.0%})")
        
        return insights
    
    def adapt_learning_approach(self, domain: str, current_approach: Dict) -> Dict:
        """
        Suggest improvements to current learning approach
        
        This is the key meta-learning function - it actively changes
        how the agent learns based on what's worked before.
        """
        optimal = self.get_optimal_params(domain)
        best_strategy, _ = self.get_best_strategy(domain)
        
        adapted = current_approach.copy()
        
        # Adjust exploration
        if abs(current_approach.get('exploration_rate', 0.3) - optimal['exploration_rate']) > 0.1:
            adapted['exploration_rate'] = optimal['exploration_rate']
        
        # Adjust memory depth
        if abs(current_approach.get('memory_depth', 10) - optimal['memory_depth']) > 5:
            adapted['memory_depth'] = optimal['memory_depth']
        
        # Suggest strategy
        if best_strategy and current_approach.get('strategy') != best_strategy:
            adapted['strategy'] = best_strategy
        
        return adapted
    
    def _save(self):
        """Persist meta-learning data"""
        try:
            data = {
                'episodes': [
                    {
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat(),
                        'domain': e.domain,
                        'context': e.context,
                        'strategy': e.strategy,
                        'success': e.success,
                        'time_to_success': e.time_to_success,
                        'retention_score': e.retention_score,
                        'transfer_score': e.transfer_score,
                        'exploration_rate': e.exploration_rate,
                        'memory_depth': e.memory_depth,
                        'would_repeat': e.would_repeat,
                        'notes': e.notes
                    }
                    for e in self.episodes
                ],
                'strategy_stats': dict(self.strategy_stats),
                'optimal_params': self.optimal_params
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save meta-learning: {e}")
    
    def _load(self):
        """Load meta-learning data"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Restore episodes
                for edata in data.get('episodes', []):
                    episode = LearningEpisode(
                        id=edata['id'],
                        timestamp=datetime.fromisoformat(edata['timestamp']),
                        domain=edata['domain'],
                        context=edata['context'],
                        strategy=edata['strategy'],
                        success=edata['success'],
                        time_to_success=edata.get('time_to_success', 0),
                        retention_score=edata.get('retention_score', 0.5),
                        transfer_score=edata.get('transfer_score', 0.5),
                        exploration_rate=edata.get('exploration_rate', 0.3),
                        memory_depth=edata.get('memory_depth', 10),
                        would_repeat=edata.get('would_repeat', edata['success']),
                        notes=edata.get('notes', '')
                    )
                    self.episodes.append(episode)
                
                # Restore stats
                self.strategy_stats = defaultdict(lambda: defaultdict(lambda: [0, 0]))
                for domain, strategies in data.get('strategy_stats', {}).items():
                    for strategy, stats in strategies.items():
                        self.strategy_stats[domain][strategy] = stats
                
                # Restore optimal params
                self.optimal_params = data.get('optimal_params', self.optimal_params)
                
                print(f"✅ Loaded {len(self.episodes)} learning episodes")
        except Exception as e:
            print(f"⚠️ Failed to load meta-learning: {e}")


class AdaptiveLearner:
    """
    High-level interface that combines all learning systems
    
    This is what the agent actually uses - it orchestrates:
    - Episodic memory (what happened)
    - Meta-learning (how to learn)
    - Unified memory (storage)
    """
    
    def __init__(self, meta_engine: MetaLearningEngine, 
                 episodic_store=None, unified_memory=None):
        self.meta = meta_engine
        self.episodic = episodic_store
        self.unified = unified_memory
    
    def learn(self, domain: str, context: str, attempt_action: str,
              strategy: str = None) -> Dict:
        """
        Execute a learning attempt with full tracking
        
        This is the main entry point - it:
        1. Decides whether to explore or exploit
        2. Gets optimal parameters for the domain
        3. Records the attempt
        4. Returns recommended approach
        """
        start_time = datetime.now()
        
        # Get optimal strategy if not specified
        if strategy is None:
            strategy, _ = self.meta.get_best_strategy(domain)
        
        # Get optimal parameters
        params = self.meta.get_optimal_params(domain)
        
        # Decide exploration vs exploitation
        should_explore = self.meta.should_explore(domain, situation_novelty=0.5)
        
        # Adjust based on meta-learning
        if should_explore:
            # Try something slightly different
            params['exploration_rate'] = min(1.0, params['exploration_rate'] + 0.1)
        
        return {
            'strategy': strategy,
            'exploration_rate': params['exploration_rate'],
            'memory_depth': params['memory_depth'],
            'should_explore': should_explore,
            'attempt_action': attempt_action,
            'estimated_difficulty': self.meta.estimate_learning_difficulty(domain, context)
        }
    
    def feedback(self, learning_attempt: Dict, success: bool, 
                 outcome_description: str, time_taken: float = 0):
        """
        Provide feedback on a learning attempt
        
        This closes the learning loop and updates all systems.
        """
        domain = learning_attempt.get('domain', 'general')
        context = learning_attempt.get('context', '')
        strategy = learning_attempt.get('strategy', 'trial_error')
        
        # Record in meta-learning
        self.meta.record_learning_attempt(
            domain=domain,
            context=context,
            strategy=strategy,
            success=success,
            time_to_success=time_taken,
            exploration_rate=learning_attempt.get('exploration_rate', 0.3),
            memory_depth=learning_attempt.get('memory_depth', 10),
            notes=outcome_description
        )
        
        # Record in episodic memory
        if self.episodic:
            self.episodic.record(
                context=context,
                action=learning_attempt.get('attempt_action', 'unknown'),
                outcome=outcome_description,
                emotional_valence=0.5 if success else -0.5,
                behavior_delta=learning_attempt.get('behavior_delta', {}),
                trigger_patterns=[domain, strategy]
            )
    
    def get_learning_report(self) -> Dict:
        """Get comprehensive learning report"""
        return {
            'meta_learning_insights': self.meta.get_learning_insights(),
            'total_episodes': len(self.meta.episodes),
            'strategy_effectiveness': dict(self.meta.strategy_stats),
            'optimal_parameters': self.meta.optimal_params,
            'recent_success_rate': self._calculate_recent_success_rate()
        }
    
    def _calculate_recent_success_rate(self) -> float:
        """Calculate success rate of recent learning attempts"""
        recent = [e for e in self.meta.episodes 
                  if (datetime.now() - e.timestamp).days < 7]
        if not recent:
            return 0.5
        return sum(1 for e in recent if e.success) / len(recent)


# Factory function
def create_meta_learning_engine() -> MetaLearningEngine:
    """Create meta-learning engine"""
    return MetaLearningEngine()

def create_adaptive_learner(meta_engine=None, episodic=None, unified=None) -> AdaptiveLearner:
    """Create adaptive learner with all components"""
    if meta_engine is None:
        meta_engine = create_meta_learning_engine()
    return AdaptiveLearner(meta_engine, episodic, unified)
