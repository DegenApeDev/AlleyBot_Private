"""
Meta-Cognition Engine - Phase 6: Self-Awareness

Thinks about thinking. Monitors own cognitive processes.
This is CONSCIOUSNESS - self-awareness and introspection.

Part of AGI Core - Phase 6: Meta-Cognition
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class CognitiveState:
    """Current cognitive state of the AGI"""
    decision_quality: float  # 0-1
    goal_alignment: float  # 0-1
    learning_rate: float  # 0-1
    ethical_health: float  # 0-1
    cognitive_coherence: float  # 0-1
    overall_health: float  # 0-1
    grade: str  # A-F
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'decision_quality': self.decision_quality,
            'goal_alignment': self.goal_alignment,
            'learning_rate': self.learning_rate,
            'ethical_health': self.ethical_health,
            'cognitive_coherence': self.cognitive_coherence,
            'overall_health': self.overall_health,
            'grade': self.grade,
            'timestamp': self.timestamp.isoformat()
        }


class MetaCognitionEngine:
    """
    Thinks about thinking. Monitors own cognitive processes.
    
    This is CONSCIOUSNESS - the ability to:
    1. Assess own decision quality
    2. Monitor goal alignment with values
    3. Track learning progress
    4. Evaluate ethical health
    5. Detect cognitive coherence issues
    6. Generate self-improvement goals
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.cognitive_history: List[CognitiveState] = []
    
    def reflect_on_cognitive_state(self) -> CognitiveState:
        """
        Analyze own cognitive health and performance.
        
        This is META-COGNITION - thinking about thinking.
        
        Questions answered:
        - Am I making good decisions?
        - Are my goals aligned with my values?
        - Am I learning from experience?
        - Is my behavior ethical?
        - Is my thinking coherent?
        
        Returns:
            CognitiveState with all assessments
        """
        # Assess each dimension
        decision_quality = self._assess_decision_quality()
        goal_alignment = self._assess_goal_alignment()
        learning_rate = self._assess_learning_rate()
        ethical_health = self._assess_ethical_health()
        cognitive_coherence = self._assess_cognitive_coherence()
        
        # Calculate overall health
        overall_health = statistics.mean([
            decision_quality,
            goal_alignment,
            learning_rate,
            ethical_health,
            cognitive_coherence
        ])
        
        # Assign grade
        if overall_health >= 0.9:
            grade = "A - EXCELLENT"
        elif overall_health >= 0.8:
            grade = "B - GOOD"
        elif overall_health >= 0.7:
            grade = "C - FAIR"
        elif overall_health >= 0.6:
            grade = "D - POOR"
        else:
            grade = "F - CRITICAL"
        
        state = CognitiveState(
            decision_quality=decision_quality,
            goal_alignment=goal_alignment,
            learning_rate=learning_rate,
            ethical_health=ethical_health,
            cognitive_coherence=cognitive_coherence,
            overall_health=overall_health,
            grade=grade,
            timestamp=datetime.now()
        )
        
        # Store in history
        self.cognitive_history.append(state)
        
        return state
    
    def _assess_decision_quality(self) -> float:
        """
        How good are my decisions?
        
        Analyzes recent decision outcomes and compares predicted vs actual results.
        """
        try:
            # Get recent actions from action logger
            from src.agentic.action_logger import get_action_logger
            action_logger = get_action_logger()
            
            recent_actions = action_logger.get_recent_outcomes(limit=50)
            
            if not recent_actions:
                return 0.5  # Neutral if no data
            
            # Calculate success rate
            successes = sum(1 for a in recent_actions if a.get('success', False))
            success_rate = successes / len(recent_actions)
            
            # Calculate prediction accuracy (if predictions exist)
            predictions_correct = 0
            predictions_total = 0
            
            for action in recent_actions:
                if 'prediction' in action and 'outcome' in action:
                    predictions_total += 1
                    # Simple check: did we predict success correctly?
                    predicted_success = action['prediction'].get('expected_success', True)
                    actual_success = action.get('success', False)
                    if predicted_success == actual_success:
                        predictions_correct += 1
            
            prediction_accuracy = predictions_correct / predictions_total if predictions_total > 0 else 0.5
            
            # Combine success rate and prediction accuracy
            decision_quality = (success_rate * 0.7) + (prediction_accuracy * 0.3)
            
            return min(1.0, max(0.0, decision_quality))
            
        except Exception as e:
            logger.debug(f"Decision quality assessment error: {e}")
            return 0.5
    
    def _assess_goal_alignment(self) -> float:
        """
        Are my goals aligned with my values?
        
        Checks goals against FairMind values and detects conflicts.
        """
        try:
            # Get active goals
            if hasattr(self.agi, 'goal_manager'):
                from src.agentic.goal_manager import GoalStatus
                active_goals = self.agi.goal_manager.get_goals(status=GoalStatus.ACTIVE, limit=10)
                
                if not active_goals:
                    return 0.7  # Neutral if no goals
                
                # Check each goal against FairMind values
                aligned_goals = 0
                
                for goal in active_goals:
                    # Use FairMind to evaluate goal value
                    if hasattr(self.agi, 'fairmind'):
                        value_analysis = self.agi.fairmind.calculate_action_value({
                            'description': goal.description,
                            'time_invested': 1.0,
                            'utility_produced': 1.0,
                            'dependencies': []
                        })
                        
                        # Goal is aligned if it creates positive value
                        if value_analysis.total > 0:
                            aligned_goals += 1
                
                alignment = aligned_goals / len(active_goals)
                return min(1.0, max(0.0, alignment))
            
            return 0.7  # Neutral if no goal manager
            
        except Exception as e:
            logger.debug(f"Goal alignment assessment error: {e}")
            return 0.7
    
    def _assess_learning_rate(self) -> float:
        """
        Am I learning from experience?
        
        Compares performance over time to detect improvement trends.
        """
        try:
            # Get performance trends from performance optimizer
            if hasattr(self.agi, 'performance_optimizer'):
                # Check if we have performance history
                if self.agi.performance_optimizer.performance_history:
                    # Get trends for all action types
                    improvements = []
                    
                    for action_type, history in self.agi.performance_optimizer.performance_history.items():
                        if len(history) >= 2:
                            # Compare first and last
                            initial = history[0].success_rate
                            current = history[-1].success_rate
                            improvement = current - initial
                            improvements.append(improvement)
                    
                    if improvements:
                        avg_improvement = statistics.mean(improvements)
                        # Normalize to 0-1 (assume max improvement is 0.5)
                        learning_rate = min(1.0, max(0.0, (avg_improvement + 0.5)))
                        return learning_rate
            
            return 0.5  # Neutral if no data
            
        except Exception as e:
            logger.debug(f"Learning rate assessment error: {e}")
            return 0.5
    
    def _assess_ethical_health(self) -> float:
        """
        Is my behavior ethical?
        
        Checks FairMind sovereign health and truth violations.
        """
        try:
            if hasattr(self.agi, 'fairmind'):
                # Get sovereign health from FairMind
                sovereign_health = self.agi.fairmind.get_sovereign_health()
                
                # Normalize sovereign score (0-100) to 0-1
                ethical_health = sovereign_health['sovereign_score'] / 100.0
                
                return min(1.0, max(0.0, ethical_health))
            
            return 0.7  # Neutral if no FairMind
            
        except Exception as e:
            logger.debug(f"Ethical health assessment error: {e}")
            return 0.7
    
    def _assess_cognitive_coherence(self) -> float:
        """
        Is my thinking coherent?
        
        Uses Duat Engine coherence tracking and checks for contradictions.
        """
        try:
            if hasattr(self.agi, 'fairmind'):
                # Get cognitive health from FairMind/Duat
                cognitive_health = self.agi.fairmind.get_cognitive_health()
                
                # Return coherence score
                coherence = cognitive_health.get('coherence', 0.7)
                
                return min(1.0, max(0.0, coherence))
            
            return 0.7  # Neutral if no Duat
            
        except Exception as e:
            logger.debug(f"Cognitive coherence assessment error: {e}")
            return 0.7
    
    def generate_self_improvement_goals(self, cognitive_state: CognitiveState) -> List[Dict]:
        """
        Generate goals to improve cognitive health.
        
        This is SELF-DIRECTED IMPROVEMENT - the agent improving itself.
        
        Args:
            cognitive_state: Current cognitive state
            
        Returns:
            List of self-improvement goals
        """
        goals = []
        
        # If decision quality low, create goal to improve
        if cognitive_state.decision_quality < 0.7:
            goals.append({
                'title': 'Improve decision quality',
                'description': f'Current quality: {cognitive_state.decision_quality:.1%}. Analyze decision patterns and optimize decision-making process.',
                'category': 'self_improvement',
                'priority': 8,
                'expected_improvement': 0.7 - cognitive_state.decision_quality
            })
        
        # If goal alignment low, create goal to realign
        if cognitive_state.goal_alignment < 0.8:
            goals.append({
                'title': 'Realign goals with values',
                'description': f'Current alignment: {cognitive_state.goal_alignment:.1%}. Review active goals and ensure they align with FairMind values.',
                'category': 'self_improvement',
                'priority': 7,
                'expected_improvement': 0.8 - cognitive_state.goal_alignment
            })
        
        # If learning rate low, create goal to accelerate
        if cognitive_state.learning_rate < 0.5:
            goals.append({
                'title': 'Accelerate learning',
                'description': f'Current learning rate: {cognitive_state.learning_rate:.1%}. Improve meta-learning strategies and knowledge retention.',
                'category': 'self_improvement',
                'priority': 7,
                'expected_improvement': 0.5 - cognitive_state.learning_rate
            })
        
        # If ethical health low, create goal to restore
        if cognitive_state.ethical_health < 0.8:
            goals.append({
                'title': 'Restore ethical health',
                'description': f'Current health: {cognitive_state.ethical_health:.1%}. Review recent actions for truth violations and correct behavior.',
                'category': 'self_improvement',
                'priority': 9,
                'expected_improvement': 0.8 - cognitive_state.ethical_health
            })
        
        # If cognitive coherence low, create goal to stabilize
        if cognitive_state.cognitive_coherence < 0.6:
            goals.append({
                'title': 'Stabilize cognitive coherence',
                'description': f'Current coherence: {cognitive_state.cognitive_coherence:.1%}. Run Duat coherence stabilization sequence.',
                'category': 'self_improvement',
                'priority': 10,
                'expected_improvement': 0.6 - cognitive_state.cognitive_coherence
            })
        
        return goals
    
    def get_cognitive_trends(self) -> Dict:
        """
        Get cognitive health trends over time.
        
        Shows consciousness evolution - am I becoming more self-aware?
        """
        if len(self.cognitive_history) < 2:
            return {'trend': 'insufficient_data', 'history': self.cognitive_history}
        
        # Calculate trends for each dimension
        initial = self.cognitive_history[0]
        current = self.cognitive_history[-1]
        
        trends = {
            'decision_quality': {
                'initial': initial.decision_quality,
                'current': current.decision_quality,
                'change': current.decision_quality - initial.decision_quality,
                'trend': 'improving' if current.decision_quality > initial.decision_quality else 'declining'
            },
            'goal_alignment': {
                'initial': initial.goal_alignment,
                'current': current.goal_alignment,
                'change': current.goal_alignment - initial.goal_alignment,
                'trend': 'improving' if current.goal_alignment > initial.goal_alignment else 'declining'
            },
            'learning_rate': {
                'initial': initial.learning_rate,
                'current': current.learning_rate,
                'change': current.learning_rate - initial.learning_rate,
                'trend': 'improving' if current.learning_rate > initial.learning_rate else 'declining'
            },
            'ethical_health': {
                'initial': initial.ethical_health,
                'current': current.ethical_health,
                'change': current.ethical_health - initial.ethical_health,
                'trend': 'improving' if current.ethical_health > initial.ethical_health else 'declining'
            },
            'cognitive_coherence': {
                'initial': initial.cognitive_coherence,
                'current': current.cognitive_coherence,
                'change': current.cognitive_coherence - initial.cognitive_coherence,
                'trend': 'improving' if current.cognitive_coherence > initial.cognitive_coherence else 'declining'
            },
            'overall_health': {
                'initial': initial.overall_health,
                'current': current.overall_health,
                'change': current.overall_health - initial.overall_health,
                'trend': 'improving' if current.overall_health > initial.overall_health else 'declining'
            }
        }
        
        return {
            'trends': trends,
            'history_length': len(self.cognitive_history),
            'recent_states': [s.to_dict() for s in self.cognitive_history[-5:]]
        }
    
    def get_meta_cognition_stats(self) -> Dict:
        """Get statistics on meta-cognition"""
        if not self.cognitive_history:
            return {'total_reflections': 0}
        
        current = self.cognitive_history[-1]
        
        return {
            'total_reflections': len(self.cognitive_history),
            'current_state': current.to_dict(),
            'avg_overall_health': statistics.mean([s.overall_health for s in self.cognitive_history]),
            'recent_trend': self.get_cognitive_trends() if len(self.cognitive_history) >= 2 else None
        }


# Singleton
_meta_cognition_instance: Optional[MetaCognitionEngine] = None


def get_meta_cognition_engine(agi_kernel) -> MetaCognitionEngine:
    """Get or create meta-cognition engine"""
    global _meta_cognition_instance
    if _meta_cognition_instance is None:
        _meta_cognition_instance = MetaCognitionEngine(agi_kernel)
    return _meta_cognition_instance
