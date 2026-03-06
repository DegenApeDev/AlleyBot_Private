"""
Self-Reflection Mixin for Meta-Learning
Enables AlleyBot to learn from experience and improve decision-making over time.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict


class SelfReflectionMixin:
    """
    Meta-learning through self-reflection.
    """
    
    # Mixin metadata for documentation and validation
    REQUIRES = ["world_state", "goals"]
    PROVIDES = ["reflect", "learn_from_experience", "meta_learn"]
    INIT_ORDER = 12
    
    """
    
    Every 24 hours, AlleyBot:
    1. Reviews action history (successes/failures)
    2. Identifies patterns in performance
    3. Adjusts decision weights and strategies
    4. Updates its own understanding of what works
    """
    
    def _init_self_reflection(self):
        """Initialize self-reflection system"""
        self.reflection_memory = {
            'action_outcomes': [],  # History of actions and results
            'pattern_analysis': {},  # Detected patterns
            'decision_weights': defaultdict(lambda: 1.0),  # Action type weights
            'last_reflection': None,
            'learning_insights': [],
        }
        self._load_reflection_state()
    
    def _load_reflection_state(self):
        """Load reflection state from memory"""
        try:
            state = self.core.get_memory('brain_reflection_state')
            if state:
                self.reflection_memory.update(state)
        except Exception:
            pass
    
    def _save_reflection_state(self):
        """Save reflection state to memory"""
        try:
            self.core.save_memory('brain_reflection_state', {
                'action_outcomes': self.reflection_memory['action_outcomes'][-100:],  # Keep last 100
                'pattern_analysis': self.reflection_memory['pattern_analysis'],
                'decision_weights': dict(self.reflection_memory['decision_weights']),
                'last_reflection': self.reflection_memory['last_reflection'],
                'learning_insights': self.reflection_memory['learning_insights'][-20:],
            })
        except Exception as e:
            print(f"⚠️ Failed to save reflection state: {e}")
    
    def record_action_outcome(self, action_id: str, action_type: str, 
                             success: bool, metrics: Dict[str, Any]):
        """
        Record the outcome of an action for later analysis.
        
        Args:
            action_id: Unique identifier for the action
            action_type: Category (post, engage, skill_exec, etc.)
            success: Whether the action achieved its goal
            metrics: Additional metrics (engagement, time, etc.)
        """
        outcome = {
            'action_id': action_id,
            'action_type': action_type,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
        }
        
        self.reflection_memory['action_outcomes'].append(outcome)
        
        # Update decision weight based on outcome
        current_weight = self.reflection_memory['decision_weights'][action_type]
        if success:
            # Increase weight slightly for successful actions
            new_weight = min(current_weight * 1.05, 2.0)
        else:
            # Decrease weight for failed actions
            new_weight = max(current_weight * 0.95, 0.5)
        
        self.reflection_memory['decision_weights'][action_type] = new_weight
        
        # Save periodically (every 10 outcomes)
        if len(self.reflection_memory['action_outcomes']) % 10 == 0:
            self._save_reflection_state()
    
    def run_self_reflection(self) -> Dict[str, Any]:
        """
        Run comprehensive self-reflection analysis.
        Called periodically (e.g., every 24 hours) to learn from experience.
        
        Returns:
            Dict with insights, pattern analysis, and recommended adjustments
        """
        print("🧠 Running self-reflection analysis...")
        
        outcomes = self.reflection_memory['action_outcomes']
        if len(outcomes) < 10:
            print("📊 Not enough data for meaningful reflection (< 10 outcomes)")
            return {'insights': [], 'patterns': {}, 'recommendations': []}
        
        # Only analyze last 24 hours of data
        cutoff = datetime.now() - timedelta(hours=24)
        recent_outcomes = [
            o for o in outcomes 
            if datetime.fromisoformat(o['timestamp']) > cutoff
        ]
        
        if not recent_outcomes:
            print("📊 No recent outcomes to analyze")
            return {'insights': [], 'patterns': {}, 'recommendations': []}
        
        # Analyze patterns
        patterns = self._analyze_patterns(recent_outcomes)
        
        # Generate insights
        insights = self._generate_insights(patterns, recent_outcomes)
        
        # Create recommendations
        recommendations = self._create_recommendations(insights, patterns)
        
        # Update learning state
        self.reflection_memory['pattern_analysis'] = patterns
        self.reflection_memory['learning_insights'].extend(insights)
        self.reflection_memory['last_reflection'] = datetime.now().isoformat()
        self._save_reflection_state()
        
        print(f"✅ Self-reflection complete: {len(insights)} insights, {len(recommendations)} recommendations")
        
        return {
            'insights': insights,
            'patterns': patterns,
            'recommendations': recommendations,
            'outcomes_analyzed': len(recent_outcomes),
        }
    
    def _analyze_patterns(self, outcomes: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in action outcomes"""
        patterns = {
            'by_type': defaultdict(lambda: {'success': 0, 'failure': 0, 'total': 0}),
            'by_hour': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'by_platform': defaultdict(lambda: {'success': 0, 'failure': 0}),
        }
        
        for outcome in outcomes:
            action_type = outcome['action_type']
            success = outcome['success']
            hour = datetime.fromisoformat(outcome['timestamp']).hour
            
            # By type
            patterns['by_type'][action_type]['total'] += 1
            if success:
                patterns['by_type'][action_type]['success'] += 1
            else:
                patterns['by_type'][action_type]['failure'] += 1
            
            # By hour
            if success:
                patterns['by_hour'][hour]['success'] += 1
            else:
                patterns['by_hour'][hour]['failure'] += 1
            
            # By platform (if in metrics)
            platform = outcome.get('metrics', {}).get('platform', 'unknown')
            if success:
                patterns['by_platform'][platform]['success'] += 1
            else:
                patterns['by_platform'][platform]['failure'] += 1
        
        # Calculate success rates
        for category in patterns.values():
            for key, stats in category.items():
                total = stats['success'] + stats['failure']
                stats['success_rate'] = stats['success'] / total if total > 0 else 0
        
        return dict(patterns)
    
    def _generate_insights(self, patterns: Dict, outcomes: List[Dict]) -> List[Dict]:
        """Generate insights from pattern analysis"""
        insights = []
        
        # Best/worst performing action types
        by_type = patterns.get('by_type', {})
        if by_type:
            sorted_types = sorted(
                by_type.items(), 
                key=lambda x: x[1].get('success_rate', 0), 
                reverse=True
            )
            
            if sorted_types:
                best_type, best_stats = sorted_types[0]
                if best_stats['total'] >= 3:  # At least 3 attempts
                    insights.append({
                        'type': 'performance',
                        'category': 'best_action_type',
                        'finding': f"{best_type} has highest success rate ({best_stats['success_rate']:.1%})",
                        'recommendation': f"Prioritize {best_type} actions",
                        'confidence': min(best_stats['total'] / 10, 1.0),
                    })
                
                if len(sorted_types) > 1:
                    worst_type, worst_stats = sorted_types[-1]
                    if worst_stats['total'] >= 3 and worst_stats['success_rate'] < 0.5:
                        insights.append({
                            'type': 'performance',
                            'category': 'worst_action_type',
                            'finding': f"{worst_type} has low success rate ({worst_stats['success_rate']:.1%})",
                            'recommendation': f"Review {worst_type} implementation or reduce frequency",
                            'confidence': min(worst_stats['total'] / 10, 1.0),
                        })
        
        # Best performing hours
        by_hour = patterns.get('by_hour', {})
        if by_hour:
            best_hours = sorted(
                by_hour.items(),
                key=lambda x: x[1].get('success_rate', 0),
                reverse=True
            )[:3]
            
            if best_hours and best_hours[0][1].get('success', 0) >= 3:
                insights.append({
                    'type': 'timing',
                    'category': 'optimal_hours',
                    'finding': f"Best performing hours: {[h[0] for h in best_hours]}",
                    'recommendation': f"Schedule high-priority actions around hour {best_hours[0][0]}",
                    'confidence': 0.7,
                })
        
        # Trend analysis (improving or declining)
        if len(outcomes) >= 20:
            first_half = outcomes[:len(outcomes)//2]
            second_half = outcomes[len(outcomes)//2:]
            
            first_success_rate = sum(1 for o in first_half if o['success']) / len(first_half)
            second_success_rate = sum(1 for o in second_half if o['success']) / len(second_half)
            
            if second_success_rate > first_success_rate + 0.1:
                insights.append({
                    'type': 'trend',
                    'category': 'improving',
                    'finding': f"Performance improving ({first_success_rate:.1%} → {second_success_rate:.1%})",
                    'recommendation': "Current strategies are working, continue approach",
                    'confidence': 0.8,
                })
            elif second_success_rate < first_success_rate - 0.1:
                insights.append({
                    'type': 'trend',
                    'category': 'declining',
                    'finding': f"Performance declining ({first_success_rate:.1%} → {second_success_rate:.1%})",
                    'recommendation': "Consider adjusting strategy or investigating issues",
                    'confidence': 0.8,
                })
        
        return insights
    
    def _create_recommendations(self, insights: List[Dict], patterns: Dict) -> List[str]:
        """Convert insights into actionable recommendations"""
        recommendations = []
        
        for insight in insights:
            rec = insight.get('recommendation', '')
            if rec:
                recommendations.append(rec)
        
        # Add general recommendations based on patterns
        by_type = patterns.get('by_type', {})
        for action_type, stats in by_type.items():
            if stats['total'] >= 5 and stats['success_rate'] < 0.3:
                recommendations.append(
                    f"Consider disabling or fixing {action_type} "
                    f"(only {stats['success_rate']:.0%} success rate)"
                )
        
        return recommendations
    
    def get_decision_weight(self, action_type: str) -> float:
        """Get the learned weight for an action type (higher = more likely to choose)"""
        return self.reflection_memory['decision_weights'].get(action_type, 1.0)
    
    def reflection_summary_command(self, *args) -> str:
        """Command to show reflection summary. Usage: reflect_summary"""
        last_reflection = self.reflection_memory.get('last_reflection')
        insights = self.reflection_memory.get('learning_insights', [])
        weights = dict(self.reflection_memory.get('decision_weights', {}))
        
        output = "🧠 Self-Reflection Summary\n\n"
        
        if last_reflection:
            last_dt = datetime.fromisoformat(last_reflection)
            hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
            output += f"Last reflection: {hours_ago:.1f} hours ago\n"
        else:
            output += "No reflection run yet\n"
        
        output += f"\n📊 Total Insights: {len(insights)}\n"
        
        if weights:
            output += "\n⚖️ Decision Weights:\n"
            for action_type, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(weight * 5) + "░" * (10 - int(weight * 5))
                output += f"  {action_type:15} {bar} {weight:.2f}\n"
        
        if insights:
            output += "\n💡 Recent Insights:\n"
            for insight in insights[-5:]:
                output += f"  • {insight.get('finding', 'Unknown')}\n"
        
        return output
    
    def reflection_run_command(self, *args) -> str:
        """Command to manually trigger reflection. Usage: reflect_run"""
        result = self.run_self_reflection()
        
        insights = result.get('insights', [])
        recommendations = result.get('recommendations', [])
        
        if not insights:
            return "📊 No new insights from reflection. Keep gathering data..."
        
        output = "🧠 Self-Reflection Results\n\n"
        output += f"📊 Analyzed {result.get('outcomes_analyzed', 0)} recent outcomes\n"
        output += f"💡 Generated {len(insights)} insights\n"
        output += f"📝 Created {len(recommendations)} recommendations\n\n"
        
        output += "Key Insights:\n"
        for i, insight in enumerate(insights[:5], 1):
            output += f"  {i}. {insight.get('category', 'general').upper()}: {insight.get('finding', '')}\n"
        
        if recommendations:
            output += "\nRecommendations:\n"
            for i, rec in enumerate(recommendations[:3], 1):
                output += f"  {i}. {rec}\n"
        
        return output
