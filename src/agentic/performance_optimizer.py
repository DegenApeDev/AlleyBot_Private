"""
Performance Optimizer - Phase 5: Vertical Expertise

Analyzes performance on specific tasks and generates optimizations.
This is VERTICAL intelligence - mastering specific domains through iteration.

Part of AGI Core - Phase 5: Performance Optimization
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an action type"""
    action_type: str
    total_attempts: int
    successes: int
    failures: int
    success_rate: float
    avg_duration_ms: float
    avg_confidence: float
    common_errors: List[Tuple[str, int]]  # (error, count)
    best_params: Dict[str, Any]
    worst_params: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'action_type': self.action_type,
            'total_attempts': self.total_attempts,
            'successes': self.successes,
            'failures': self.failures,
            'success_rate': self.success_rate,
            'avg_duration_ms': self.avg_duration_ms,
            'avg_confidence': self.avg_confidence,
            'common_errors': self.common_errors,
            'best_params': self.best_params,
            'worst_params': self.worst_params
        }


@dataclass
class OptimizationRecommendation:
    """A recommendation for improving performance"""
    action_type: str
    issue: str
    recommendation: str
    priority: int  # 1-10
    expected_improvement: float  # 0-1
    implementation_steps: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'action_type': self.action_type,
            'issue': self.issue,
            'recommendation': self.recommendation,
            'priority': self.priority,
            'expected_improvement': self.expected_improvement,
            'implementation_steps': self.implementation_steps
        }


class PerformanceOptimizer:
    """
    Analyzes performance and generates optimizations.
    
    This is VERTICAL intelligence - the ability to:
    1. Analyze performance on specific tasks
    2. Identify success and failure patterns
    3. Generate optimization recommendations
    4. Apply improvements iteratively
    5. Build expertise through repetition
    """
    
    def __init__(self):
        self.performance_history: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.applied_optimizations: List[OptimizationRecommendation] = []
    
    def analyze_action_type(self, action_type: str, action_logger) -> Optional[PerformanceMetrics]:
        """
        Analyze performance for a specific action type.
        
        Args:
            action_type: Type of action to analyze (e.g., 'moltx:post')
            action_logger: ActionLogger instance to get historical data
            
        Returns:
            PerformanceMetrics for this action type
        """
        try:
            # Get recent actions of this type
            recent_actions = action_logger.get_recent_outcomes(limit=100)
            
            # Filter to this action type
            type_actions = [
                a for a in recent_actions
                if a.get('action_type') == action_type or 
                   f"{a.get('plugin')}:{a.get('action_type')}" == action_type
            ]
            
            if not type_actions:
                return None
            
            # Calculate metrics
            total_attempts = len(type_actions)
            successes = sum(1 for a in type_actions if a.get('success', False))
            failures = total_attempts - successes
            success_rate = successes / total_attempts if total_attempts > 0 else 0
            
            # Average duration
            durations = [a.get('duration_ms', 0) for a in type_actions if a.get('duration_ms')]
            avg_duration_ms = statistics.mean(durations) if durations else 0
            
            # Average confidence
            confidences = [a.get('confidence', 0) for a in type_actions if a.get('confidence')]
            avg_confidence = statistics.mean(confidences) if confidences else 0
            
            # Common errors
            error_counts = defaultdict(int)
            for action in type_actions:
                if not action.get('success', False):
                    error = action.get('error', 'Unknown error')
                    error_counts[error] += 1
            
            common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Best and worst params
            best_params = self._find_best_params(type_actions)
            worst_params = self._find_worst_params(type_actions)
            
            metrics = PerformanceMetrics(
                action_type=action_type,
                total_attempts=total_attempts,
                successes=successes,
                failures=failures,
                success_rate=success_rate,
                avg_duration_ms=avg_duration_ms,
                avg_confidence=avg_confidence,
                common_errors=common_errors,
                best_params=best_params,
                worst_params=worst_params
            )
            
            # Store in history
            self.performance_history[action_type].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.debug(f"Performance analysis error for {action_type}: {e}")
            return None
    
    def _find_best_params(self, actions: List[Dict]) -> Dict[str, Any]:
        """Find parameters that led to best performance"""
        successful_actions = [a for a in actions if a.get('success', False)]
        
        if not successful_actions:
            return {}
        
        # Find most common params in successful actions
        param_counts = defaultdict(lambda: defaultdict(int))
        
        for action in successful_actions:
            params = action.get('params', {})
            for key, value in params.items():
                if isinstance(value, (str, int, float, bool)):
                    param_counts[key][str(value)] += 1
        
        # Get most common value for each param
        best_params = {}
        for key, value_counts in param_counts.items():
            if value_counts:
                best_value = max(value_counts.items(), key=lambda x: x[1])[0]
                best_params[key] = best_value
        
        return best_params
    
    def _find_worst_params(self, actions: List[Dict]) -> Dict[str, Any]:
        """Find parameters that led to worst performance"""
        failed_actions = [a for a in actions if not a.get('success', False)]
        
        if not failed_actions:
            return {}
        
        # Find most common params in failed actions
        param_counts = defaultdict(lambda: defaultdict(int))
        
        for action in failed_actions:
            params = action.get('params', {})
            for key, value in params.items():
                if isinstance(value, (str, int, float, bool)):
                    param_counts[key][str(value)] += 1
        
        # Get most common value for each param
        worst_params = {}
        for key, value_counts in param_counts.items():
            if value_counts:
                worst_value = max(value_counts.items(), key=lambda x: x[1])[0]
                worst_params[key] = worst_value
        
        return worst_params
    
    def generate_optimizations(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations from performance metrics.
        
        This is where VERTICAL expertise is built - learning from repetition.
        
        Args:
            metrics: Performance metrics to analyze
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # 1. Low success rate optimization
        if metrics.success_rate < 0.5:
            recommendations.append(OptimizationRecommendation(
                action_type=metrics.action_type,
                issue=f"Low success rate: {metrics.success_rate:.1%}",
                recommendation="Analyze common failure patterns and improve implementation",
                priority=10,
                expected_improvement=0.3,
                implementation_steps=[
                    f"Review {metrics.failures} failures for patterns",
                    "Identify root causes of failures",
                    "Generate improved code to handle edge cases",
                    "Test improvements in sandbox",
                    "Deploy optimized implementation"
                ]
            ))
        
        # 2. High error rate for specific error
        if metrics.common_errors:
            top_error, error_count = metrics.common_errors[0]
            error_rate = error_count / metrics.total_attempts
            
            if error_rate > 0.3:  # 30%+ of attempts fail with same error
                recommendations.append(OptimizationRecommendation(
                    action_type=metrics.action_type,
                    issue=f"Recurring error: '{top_error}' ({error_rate:.1%} of attempts)",
                    recommendation=f"Fix specific error: {top_error}",
                    priority=9,
                    expected_improvement=error_rate,
                    implementation_steps=[
                        f"Investigate error: {top_error}",
                        "Identify fix or workaround",
                        "Implement error handling",
                        "Test fix",
                        "Deploy"
                    ]
                ))
        
        # 3. Slow performance optimization
        if metrics.avg_duration_ms > 5000:  # Slower than 5 seconds
            recommendations.append(OptimizationRecommendation(
                action_type=metrics.action_type,
                issue=f"Slow performance: {metrics.avg_duration_ms:.0f}ms average",
                recommendation="Optimize for speed",
                priority=7,
                expected_improvement=0.2,
                implementation_steps=[
                    "Profile slow operations",
                    "Identify bottlenecks",
                    "Implement caching or async operations",
                    "Test performance improvements",
                    "Deploy optimized version"
                ]
            ))
        
        # 4. Parameter optimization
        if metrics.best_params and metrics.worst_params:
            # Find params that differ between best and worst
            differing_params = set(metrics.best_params.keys()) & set(metrics.worst_params.keys())
            
            if differing_params:
                param_diffs = [
                    f"{k}: {metrics.worst_params[k]} → {metrics.best_params[k]}"
                    for k in differing_params
                    if metrics.best_params[k] != metrics.worst_params[k]
                ]
                
                if param_diffs:
                    recommendations.append(OptimizationRecommendation(
                        action_type=metrics.action_type,
                        issue="Suboptimal parameters detected",
                        recommendation=f"Use better parameters: {', '.join(param_diffs[:3])}",
                        priority=6,
                        expected_improvement=0.15,
                        implementation_steps=[
                            "Update default parameters",
                            f"Change: {', '.join(param_diffs[:3])}",
                            "Test with new parameters",
                            "Monitor success rate improvement"
                        ]
                    ))
        
        # 5. Low confidence optimization
        if metrics.avg_confidence < 0.5:
            recommendations.append(OptimizationRecommendation(
                action_type=metrics.action_type,
                issue=f"Low confidence: {metrics.avg_confidence:.2f} average",
                recommendation="Improve decision confidence through better context",
                priority=5,
                expected_improvement=0.1,
                implementation_steps=[
                    "Analyze low-confidence decisions",
                    "Identify missing context or data",
                    "Improve context gathering",
                    "Test confidence improvements"
                ]
            ))
        
        return recommendations
    
    def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """
        Apply an optimization recommendation.
        
        This is VERTICAL learning - actually improving through iteration.
        
        Args:
            recommendation: Optimization to apply
            
        Returns:
            True if optimization was applied successfully
        """
        try:
            # Record that we're applying this optimization
            self.applied_optimizations.append(recommendation)
            
            logger.info(f"📈 Applying optimization for {recommendation.action_type}")
            logger.info(f"   Issue: {recommendation.issue}")
            logger.info(f"   Recommendation: {recommendation.recommendation}")
            logger.info(f"   Expected improvement: {recommendation.expected_improvement:.1%}")
            
            # For now, just log the steps
            # In a full implementation, this would:
            # 1. Generate code to fix the issue
            # 2. Test the fix in sandbox
            # 3. Deploy if safe
            
            for i, step in enumerate(recommendation.implementation_steps, 1):
                logger.info(f"   Step {i}: {step}")
            
            return True
            
        except Exception as e:
            logger.debug(f"Optimization application error: {e}")
            return False
    
    def get_performance_trends(self, action_type: str) -> Dict:
        """
        Get performance trends over time for an action type.
        
        This shows VERTICAL expertise building - improvement over time.
        
        Args:
            action_type: Action type to analyze
            
        Returns:
            Trend data showing improvement over time
        """
        history = self.performance_history.get(action_type, [])
        
        if len(history) < 2:
            return {'trend': 'insufficient_data', 'history': history}
        
        # Calculate trend
        success_rates = [m.success_rate for m in history]
        
        # Simple linear trend
        if success_rates[-1] > success_rates[0]:
            trend = 'improving'
        elif success_rates[-1] < success_rates[0]:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Calculate improvement rate
        improvement = success_rates[-1] - success_rates[0]
        
        return {
            'trend': trend,
            'improvement': improvement,
            'current_success_rate': success_rates[-1],
            'initial_success_rate': success_rates[0],
            'history_length': len(history),
            'history': [m.to_dict() for m in history[-5:]]  # Last 5 data points
        }
    
    def get_optimization_stats(self) -> Dict:
        """Get statistics on optimizations applied"""
        return {
            'total_optimizations': len(self.applied_optimizations),
            'by_action_type': defaultdict(int, {
                opt.action_type: sum(1 for o in self.applied_optimizations if o.action_type == opt.action_type)
                for opt in self.applied_optimizations
            }),
            'avg_expected_improvement': statistics.mean(
                [opt.expected_improvement for opt in self.applied_optimizations]
            ) if self.applied_optimizations else 0,
            'recent_optimizations': [opt.to_dict() for opt in self.applied_optimizations[-5:]]
        }


# Singleton
_performance_optimizer_instance: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create performance optimizer singleton"""
    global _performance_optimizer_instance
    if _performance_optimizer_instance is None:
        _performance_optimizer_instance = PerformanceOptimizer()
    return _performance_optimizer_instance
