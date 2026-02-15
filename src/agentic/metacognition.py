"""
AlleyBot Metacognition & Self-Awareness Engine - Phase 14

Agent knows its own capabilities and limitations.
Implements capability self-assessment, confidence calibration,
resource self-monitoring, error pattern recognition, and strategy selection.

Part of AGI Core - Phase 14: Metacognition & Self-Awareness
"""

import json
import sqlite3
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import logging
import statistics

logger = logging.getLogger(__name__)


@dataclass
class CapabilityAssessment:
    """Self-assessment of a capability"""
    capability: str
    can_perform: bool
    confidence: float  # How confident in this assessment
    performance_history: List[float]  # Historical success rates
    limitations: List[str]
    last_tested: datetime


@dataclass
class ResourceState:
    """Current resource status"""
    api_calls_today: int
    api_calls_limit: int
    cost_today: float
    cost_budget: float
    rate_limit_status: Dict[str, Any]
    storage_used_mb: float
    storage_limit_mb: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorPattern:
    """Recognized error pattern"""
    error_type: str
    frequency: int
    context_pattern: str
    recovery_success_rate: float
    first_seen: datetime
    last_seen: datetime
    affected_capabilities: List[str]


@dataclass
class StrategyPerformance:
    """Performance of a strategy in different contexts"""
    strategy_name: str
    context_type: str
    success_rate: float
    avg_confidence: float
    times_used: int
    last_used: datetime


class Metacognition:
    """
    Metacognition & Self-Awareness Engine
    
    Capabilities:
    1. Capability Self-Assessment - Know what it can/can't do
    2. Confidence Calibration - Know when it's uncertain
    3. Resource Self-Monitoring - Track API usage, costs, rate limits
    4. Error Pattern Recognition - Learn from its own mistakes
    5. Strategy Selection - Choose approach based on problem type
    6. Learning Rate Adaptation - Learn faster when environment changes
    
    Usage:
        meta = Metacognition()
        
        # Self-assess capability
        assessment = meta.assess_capability('web_search')
        
        # Check confidence
        confidence = meta.calibrate_confidence(task, context)
        
        # Monitor resources
        resources = meta.get_resource_state()
        
        # Check for error patterns
        patterns = meta.recognize_error_patterns()
        
        # Select best strategy
        strategy = meta.select_strategy(problem_type)
        
        # Adapt learning rate
        meta.adapt_learning_rate(recent_performance)
    """
    
    DB_PATH = Path('data/metacognition.db')
    
    # Known capabilities
    CAPABILITIES = [
        'web_search', 'content_generation', 'data_analysis', 'social_interaction',
        'code_generation', 'image_understanding', 'long_term_memory', 'planning',
        'causal_reasoning', 'creative_writing', 'trend_detection', 'sentiment_analysis'
    ]
    
    # Resource limits
    DEFAULT_API_LIMIT = 1000  # Calls per day
    DEFAULT_COST_BUDGET = 5.0  # Dollars per day
    
    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._ensure_capability_assessments()
    
    def _init_db(self) -> None:
        """Initialize metacognition database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS capability_assessments (
                    capability TEXT PRIMARY KEY,
                    can_perform INTEGER,
                    confidence REAL,
                    performance_history TEXT,
                    limitations TEXT,
                    last_tested TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_calls_today INTEGER,
                    api_calls_limit INTEGER,
                    cost_today REAL,
                    cost_budget REAL,
                    rate_limit_status TEXT,
                    storage_used_mb REAL,
                    storage_limit_mb REAL,
                    timestamp TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS error_patterns (
                    error_type TEXT PRIMARY KEY,
                    frequency INTEGER,
                    context_pattern TEXT,
                    recovery_success_rate REAL,
                    first_seen TEXT,
                    last_seen TEXT,
                    affected_capabilities TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategy_performances (
                    strategy_name TEXT,
                    context_type TEXT,
                    success_rate REAL,
                    avg_confidence REAL,
                    times_used INTEGER,
                    last_used TEXT,
                    PRIMARY KEY (strategy_name, context_type)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS self_reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reflection_type TEXT,
                    content TEXT,
                    confidence REAL,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
    
    def _ensure_capability_assessments(self) -> None:
        """Ensure all capabilities have assessments"""
        with sqlite3.connect(self.DB_PATH) as conn:
            for capability in self.CAPABILITIES:
                existing = conn.execute(
                    'SELECT 1 FROM capability_assessments WHERE capability = ?',
                    (capability,)
                ).fetchone()
                
                if not existing:
                    # Create default assessment
                    conn.execute('''
                        INSERT INTO capability_assessments
                        (capability, can_perform, confidence, performance_history, 
                         limitations, last_tested)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        capability,
                        1,  # Assume can perform
                        0.7,  # Moderate confidence
                        json.dumps([0.7]),  # Single data point
                        json.dumps([]),  # No known limitations yet
                        datetime.now().isoformat()
                    ))
            
            conn.commit()
    
    def assess_capability(self, capability: str) -> CapabilityAssessment:
        """
        Self-assess a capability.
        
        Args:
            capability: Capability to assess
            
        Returns:
            CapabilityAssessment
        """
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM capability_assessments WHERE capability = ?',
                (capability,)
            ).fetchone()
        
        if row:
            return CapabilityAssessment(
                capability=row['capability'],
                can_perform=bool(row['can_perform']),
                confidence=row['confidence'],
                performance_history=json.loads(row['performance_history']),
                limitations=json.loads(row['limitations']),
                last_tested=datetime.fromisoformat(row['last_tested'])
            )
        
        # Default: unknown capability
        return CapabilityAssessment(
            capability=capability,
            can_perform=False,
            confidence=0.0,
            performance_history=[],
            limitations=['unknown_capability'],
            last_tested=datetime.now()
        )
    
    def update_capability_performance(self, capability: str, 
                                       success: bool,
                                       error_message: Optional[str] = None) -> None:
        """Update capability performance based on execution result"""
        assessment = self.assess_capability(capability)
        
        # Update performance history
        performance = 1.0 if success else 0.0
        assessment.performance_history.append(performance)
        
        # Keep last 20 data points
        assessment.performance_history = assessment.performance_history[-20:]
        
        # Recalculate confidence
        if assessment.performance_history:
            avg_perf = statistics.mean(assessment.performance_history)
            variance = statistics.variance(assessment.performance_history) if len(assessment.performance_history) > 1 else 0
            
            # Higher variance = lower confidence
            assessment.confidence = avg_perf * (1 - min(0.5, variance))
            assessment.can_perform = avg_perf > 0.3  # Can perform if >30% success
        
        # Add limitation if error
        if error_message and not success:
            limitation = self._extract_limitation(error_message)
            if limitation and limitation not in assessment.limitations:
                assessment.limitations.append(limitation)
        
        assessment.last_tested = datetime.now()
        
        # Save
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO capability_assessments
                (capability, can_perform, confidence, performance_history, limitations, last_tested)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                assessment.capability,
                1 if assessment.can_perform else 0,
                assessment.confidence,
                json.dumps(assessment.performance_history),
                json.dumps(assessment.limitations),
                assessment.last_tested.isoformat()
            ))
            conn.commit()
    
    def _extract_limitation(self, error_message: str) -> Optional[str]:
        """Extract capability limitation from error message"""
        error_lower = error_message.lower()
        
        if 'rate limit' in error_lower or 'too many requests' in error_lower:
            return 'rate_limited'
        elif 'timeout' in error_lower:
            return 'timeout_prone'
        elif 'permission' in error_lower or 'unauthorized' in error_lower:
            return 'insufficient_permissions'
        elif 'not found' in error_lower:
            return 'data_unavailable'
        elif 'parse' in error_lower:
            return 'parsing_unreliable'
        else:
            return 'unstable'
    
    def calibrate_confidence(self, task: str, 
                            context: Dict[str, Any]) -> float:
        """
        Calibrate confidence for a specific task.
        
        Args:
            task: Task description
            context: Context information
            
        Returns:
            Calibrated confidence (0-1)
        """
        base_confidence = 0.7
        
        # Adjust based on capability assessments
        relevant_capabilities = self._identify_relevant_capabilities(task)
        
        if relevant_capabilities:
            cap_confidences = []
            for cap in relevant_capabilities:
                assessment = self.assess_capability(cap)
                cap_confidences.append(assessment.confidence)
            
            # Confidence is bounded by weakest relevant capability
            base_confidence = min(cap_confidences) * 0.9
        
        # Adjust for context complexity
        complexity = context.get('complexity', 0.5)
        base_confidence *= (1 - complexity * 0.3)
        
        # Adjust for time pressure
        if context.get('urgent', False):
            base_confidence *= 0.9  # Slightly lower under pressure
        
        # Adjust for novel situations
        if context.get('novel', False):
            base_confidence *= 0.85
        
        return max(0.1, min(0.95, base_confidence))
    
    def _identify_relevant_capabilities(self, task: str) -> List[str]:
        """Identify which capabilities are relevant for a task"""
        task_lower = task.lower()
        relevant = []
        
        # Simple keyword matching
        capability_keywords = {
            'web_search': ['search', 'find', 'lookup', 'information'],
            'content_generation': ['write', 'create', 'generate', 'draft'],
            'data_analysis': ['analyze', 'calculate', 'compute', 'statistics'],
            'social_interaction': ['reply', 'respond', 'engage', 'social'],
            'code_generation': ['code', 'program', 'script', 'function'],
            'image_understanding': ['image', 'picture', 'visual', 'describe'],
            'long_term_memory': ['remember', 'recall', 'memory', 'past'],
            'planning': ['plan', 'schedule', 'organize', 'steps'],
            'causal_reasoning': ['why', 'cause', 'reason', 'explain'],
            'creative_writing': ['creative', 'story', 'narrative', 'fiction'],
            'trend_detection': ['trend', 'pattern', 'detect', 'emerging'],
            'sentiment_analysis': ['sentiment', 'feeling', 'emotion', 'mood']
        }
        
        for cap, keywords in capability_keywords.items():
            if any(kw in task_lower for kw in keywords):
                relevant.append(cap)
        
        return relevant
    
    def get_resource_state(self) -> ResourceState:
        """
        Get current resource usage state.
        
        Returns:
            ResourceState with current metrics
        """
        # Load from database
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM resource_monitoring ORDER BY timestamp DESC LIMIT 1'
            ).fetchone()
        
        if row:
            return ResourceState(
                api_calls_today=row['api_calls_today'],
                api_calls_limit=row['api_calls_limit'],
                cost_today=row['cost_today'],
                cost_budget=row['cost_budget'],
                rate_limit_status=json.loads(row['rate_limit_status']),
                storage_used_mb=row['storage_used_mb'],
                storage_limit_mb=row['storage_limit_mb'],
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
        
        # Default state
        return ResourceState(
            api_calls_today=0,
            api_calls_limit=self.DEFAULT_API_LIMIT,
            cost_today=0.0,
            cost_budget=self.DEFAULT_COST_BUDGET,
            rate_limit_status={},
            storage_used_mb=0.0,
            storage_limit_mb=1000.0
        )
    
    def record_resource_usage(self, api_calls: int = 0, 
                             cost: float = 0.0,
                             rate_limit_info: Optional[Dict] = None) -> None:
        """Record resource usage"""
        current = self.get_resource_state()
        
        # Update values
        new_state = ResourceState(
            api_calls_today=current.api_calls_today + api_calls,
            api_calls_limit=current.api_calls_limit,
            cost_today=current.cost_today + cost,
            cost_budget=current.cost_budget,
            rate_limit_status=rate_limit_info or current.rate_limit_status,
            storage_used_mb=current.storage_used_mb,
            storage_limit_mb=current.storage_limit_mb
        )
        
        # Save
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO resource_monitoring
                (api_calls_today, api_calls_limit, cost_today, cost_budget,
                 rate_limit_status, storage_used_mb, storage_limit_mb, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_state.api_calls_today,
                new_state.api_calls_limit,
                new_state.cost_today,
                new_state.cost_budget,
                json.dumps(new_state.rate_limit_status),
                new_state.storage_used_mb,
                new_state.storage_limit_mb,
                new_state.timestamp.isoformat()
            ))
            conn.commit()
    
    def check_resource_constraints(self) -> Dict[str, Any]:
        """Check if approaching resource limits"""
        state = self.get_resource_state()
        
        constraints = []
        
        api_usage_ratio = state.api_calls_today / state.api_calls_limit
        if api_usage_ratio > 0.9:
            constraints.append({
                'type': 'api_calls',
                'severity': 'critical',
                'message': f'API usage at {api_usage_ratio:.0%}'
            })
        elif api_usage_ratio > 0.7:
            constraints.append({
                'type': 'api_calls',
                'severity': 'warning',
                'message': f'API usage at {api_usage_ratio:.0%}'
            })
        
        cost_ratio = state.cost_today / state.cost_budget
        if cost_ratio > 0.9:
            constraints.append({
                'type': 'cost',
                'severity': 'critical',
                'message': f'Cost at {cost_ratio:.0%} of budget'
            })
        elif cost_ratio > 0.7:
            constraints.append({
                'type': 'cost',
                'severity': 'warning',
                'message': f'Cost at {cost_ratio:.0%} of budget'
            })
        
        return {
            'has_constraints': len(constraints) > 0,
            'constraints': constraints,
            'can_continue': api_usage_ratio < 1.0 and cost_ratio < 1.0
        }
    
    def recognize_error_patterns(self) -> List[ErrorPattern]:
        """
        Recognize patterns in errors.
        
        Returns:
            List of error patterns
        """
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM error_patterns ORDER BY frequency DESC'
            ).fetchall()
        
        return [
            ErrorPattern(
                error_type=row['error_type'],
                frequency=row['frequency'],
                context_pattern=row['context_pattern'],
                recovery_success_rate=row['recovery_success_rate'],
                first_seen=datetime.fromisoformat(row['first_seen']),
                last_seen=datetime.fromisoformat(row['last_seen']),
                affected_capabilities=json.loads(row['affected_capabilities'])
            )
            for row in rows
        ]
    
    def record_error(self, error_type: str, 
                    context: Dict[str, Any],
                    recovered: bool,
                    affected_capabilities: List[str]) -> None:
        """Record an error for pattern recognition"""
        # Extract context pattern
        context_pattern = self._extract_context_pattern(context)
        
        with sqlite3.connect(self.DB_PATH) as conn:
            # Check if pattern exists
            existing = conn.execute(
                'SELECT * FROM error_patterns WHERE error_type = ? AND context_pattern = ?',
                (error_type, context_pattern)
            ).fetchone()
            
            if existing:
                # Update existing pattern
                new_freq = existing['frequency'] + 1
                
                # Update recovery rate
                total_recoveries = existing['recovery_success_rate'] * existing['frequency']
                if recovered:
                    total_recoveries += 1
                new_recovery_rate = total_recoveries / new_freq
                
                conn.execute('''
                    UPDATE error_patterns 
                    SET frequency = ?, recovery_success_rate = ?, last_seen = ?
                    WHERE error_type = ? AND context_pattern = ?
                ''', (
                    new_freq,
                    new_recovery_rate,
                    datetime.now().isoformat(),
                    error_type,
                    context_pattern
                ))
            else:
                # Create new pattern
                conn.execute('''
                    INSERT INTO error_patterns
                    (error_type, frequency, context_pattern, recovery_success_rate,
                     first_seen, last_seen, affected_capabilities)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error_type,
                    1,
                    context_pattern,
                    1.0 if recovered else 0.0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(affected_capabilities)
                ))
            
            conn.commit()
    
    def _extract_context_pattern(self, context: Dict[str, Any]) -> str:
        """Extract a general pattern from context"""
        # Simplified pattern extraction
        patterns = []
        
        if 'time_of_day' in context:
            patterns.append(f"time:{context['time_of_day']}")
        
        if 'load' in context:
            patterns.append(f"load:{context['load']}")
        
        if 'data_size' in context:
            size = context['data_size']
            if size < 1000:
                patterns.append("size:small")
            elif size < 10000:
                patterns.append("size:medium")
            else:
                patterns.append("size:large")
        
        return '|'.join(patterns) if patterns else 'general'
    
    def select_strategy(self, problem_type: str, 
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Select the best strategy for a problem type.
        
        Args:
            problem_type: Type of problem
            context: Optional context
            
        Returns:
            Strategy recommendation
        """
        # Get strategy performances
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT * FROM strategy_performances 
                   WHERE context_type = ?
                   ORDER BY success_rate DESC''',
                (problem_type,)
            ).fetchall()
        
        if rows:
            best = rows[0]
            return {
                'strategy': best['strategy_name'],
                'confidence': best['success_rate'],
                'estimated_success_rate': best['success_rate'],
                'rationale': f"Best historical performance ({best['times_used']} uses)"
            }
        
        # Default strategies for unknown problem types
        defaults = {
            'information_retrieval': 'search_then_synthesize',
            'decision_making': 'weigh_pros_cons',
            'creative_task': 'brainstorm_then_refine',
            'social_interaction': 'observe_then_respond',
            'analytical_task': 'decompose_then_analyze'
        }
        
        default_strategy = defaults.get(problem_type, 'direct_approach')
        
        return {
            'strategy': default_strategy,
            'confidence': 0.5,
            'estimated_success_rate': 0.6,
            'rationale': 'Default strategy (no historical data)'
        }
    
    def record_strategy_outcome(self, strategy: str, 
                               context_type: str,
                               success: bool,
                               confidence: float) -> None:
        """Record outcome of using a strategy"""
        with sqlite3.connect(self.DB_PATH) as conn:
            existing = conn.execute(
                '''SELECT * FROM strategy_performances 
                   WHERE strategy_name = ? AND context_type = ?''',
                (strategy, context_type)
            ).fetchone()
            
            if existing:
                # Update
                new_uses = existing['times_used'] + 1
                old_rate = existing['success_rate']
                new_rate = (old_rate * existing['times_used'] + (1 if success else 0)) / new_uses
                
                old_conf = existing['avg_confidence']
                new_conf = (old_conf * existing['times_used'] + confidence) / new_uses
                
                conn.execute('''
                    UPDATE strategy_performances
                    SET success_rate = ?, avg_confidence = ?, times_used = ?, last_used = ?
                    WHERE strategy_name = ? AND context_type = ?
                ''', (
                    new_rate, new_conf, new_uses, datetime.now().isoformat(),
                    strategy, context_type
                ))
            else:
                # Create new record
                conn.execute('''
                    INSERT INTO strategy_performances
                    (strategy_name, context_type, success_rate, avg_confidence, times_used, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    strategy, context_type,
                    1.0 if success else 0.0,
                    confidence,
                    1,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
    
    def adapt_learning_rate(self, recent_performance: List[float]) -> float:
        """
        Adapt learning rate based on recent performance.
        
        Higher volatility = lower learning rate (be more conservative)
        Improving trend = higher learning rate (learn faster)
        
        Args:
            recent_performance: List of recent performance scores
            
        Returns:
            Recommended learning rate (0-1)
        """
        if len(recent_performance) < 3:
            return 0.5  # Default
        
        # Calculate volatility
        try:
            volatility = statistics.stdev(recent_performance)
        except:
            volatility = 0
        
        # Calculate trend
        first_half = recent_performance[:len(recent_performance)//2]
        second_half = recent_performance[len(recent_performance)//2:]
        
        if first_half and second_half:
            trend = statistics.mean(second_half) - statistics.mean(first_half)
        else:
            trend = 0
        
        # Base learning rate
        base_lr = 0.5
        
        # Adjust for volatility (higher vol = lower LR)
        vol_adjustment = max(0, 1 - volatility * 2)
        
        # Adjust for trend (improving = higher LR)
        trend_adjustment = 1 + (trend * 2) if trend > 0 else max(0.5, 1 + trend)
        
        learning_rate = base_lr * vol_adjustment * trend_adjustment
        
        return max(0.1, min(0.9, learning_rate))
    
    def self_reflect(self, reflection_type: str, 
                    content: str,
                    confidence: float) -> None:
        """Record a self-reflection"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO self_reflections (reflection_type, content, confidence, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                reflection_type,
                content,
                confidence,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get summary of metacognitive state"""
        # Capability overview
        capabilities = []
        for cap in self.CAPABILITIES:
            assessment = self.assess_capability(cap)
            capabilities.append({
                'capability': cap,
                'can_perform': assessment.can_perform,
                'confidence': assessment.confidence
            })
        
        # Resource state
        resources = self.get_resource_state()
        
        # Error patterns
        patterns = self.recognize_error_patterns()
        
        # Recent reflections
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            reflections = conn.execute(
                '''SELECT * FROM self_reflections 
                   ORDER BY timestamp DESC LIMIT 5'''
            ).fetchall()
        
        return {
            'capabilities_known': len(self.CAPABILITIES),
            'capabilities_functional': sum(1 for c in capabilities if c['can_perform']),
            'avg_capability_confidence': statistics.mean([c['confidence'] for c in capabilities]),
            'resource_usage': {
                'api_calls': f"{resources.api_calls_today}/{resources.api_calls_limit}",
                'cost': f"${resources.cost_today:.2f}/${resources.cost_budget:.2f}"
            },
            'error_patterns_recognized': len(patterns),
            'top_error_types': [p.error_type for p in patterns[:3]],
            'recent_reflections': len(reflections),
            'self_aware': True
        }


# Singleton
_metacognition_instance: Optional[Metacognition] = None


def get_metacognition() -> Metacognition:
    """Get or create Metacognition singleton"""
    global _metacognition_instance
    if _metacognition_instance is None:
        _metacognition_instance = Metacognition()
    return _metacognition_instance
