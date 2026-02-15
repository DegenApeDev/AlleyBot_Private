"""
AlleyBot Causal Understanding Engine - Phase 5: Causal Understanding

Understands *why* things happen, not just *what* happens.
Implements cause-effect tracking, counterfactual analysis, and root cause detection.

Part of AGI Core - Phase 5: Causal Understanding
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import logging

from src.agentic.action_logger import ActionLogger, get_action_logger

logger = logging.getLogger(__name__)


@dataclass
class CausalLink:
    """A causal relationship between cause and effect"""
    id: str
    cause_action_id: str
    effect_action_id: str
    cause_type: str  # 'action', 'event', 'condition'
    effect_type: str
    strength: float  # 0-1 correlation strength
    time_delay_seconds: float  # Typical delay between cause and effect
    evidence_count: int = 0  # Number of times this link was observed
    created_at: datetime = field(default_factory=datetime.now)
    last_observed: Optional[datetime] = None
    
    @property
    def confidence(self) -> float:
        """Calculate confidence based on evidence"""
        # More evidence = higher confidence, asymptotic to 1.0
        import math
        return min(0.95, 1 - math.exp(-self.evidence_count / 10))


@dataclass
class Counterfactual:
    """A counterfactual scenario: 'What if I had done X instead?'"""
    id: str
    actual_action_id: str
    hypothetical_action: str  # What could have been done
    actual_outcome: Dict[str, Any]
    predicted_outcome: Dict[str, Any]  # AI-predicted hypothetical outcome
    confidence: float  # Confidence in prediction
    created_at: datetime = field(default_factory=datetime.now)
    
    # Later, compare when we know the actual result
    validated: bool = False
    actual_vs_predicted_diff: Optional[float] = None


@dataclass
class RootCauseAnalysis:
    """Result of root cause analysis"""
    target_event_id: str
    root_causes: List[Dict[str, Any]]  # Chain of causes leading to event
    contributing_factors: List[str]
    analysis_depth: int
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class CausalEngine:
    """
    Tracks and analyzes cause-effect relationships.
    
    Capabilities:
    1. Event Causality Tracker - Link cause → effect chains
    2. Counterfactual Analysis - "What if I had done X instead?"
    3. Intervention Simulation - Predict outcomes of hypothetical actions
    4. Root Cause Analysis - Find true sources of trends/engagement
    5. Impact Attribution - Know which actions drove which results
    
    Usage:
        engine = CausalEngine()
        
        # Record an observation
        engine.record_observation(
            action_id="action_123",
            context={"field_status": "Stable", "time": "morning"},
            outcome={"engagement": 45, "success": True}
        )
        
        # Analyze cause of high engagement
        causes = engine.find_causes("action_123", outcome_type="high_engagement")
        
        # Counterfactual: what if I had posted at night?
        counterfactual = engine.simulate_counterfactual(
            actual_action_id="action_123",
            hypothetical_change={"time": "night"}
        )
        
        # Root cause analysis
        root = engine.analyze_root_cause(event_id="action_123", depth=3)
    """
    
    DB_PATH = Path('data/causal.db')
    
    # Minimum correlation to consider causal
    MIN_CORRELATION_THRESHOLD = 0.6
    
    # Time window for cause-effect (seconds)
    CAUSAL_WINDOW_SECONDS = 3600  # 1 hour
    
    def __init__(self, action_logger: Optional[ActionLogger] = None):
        self.action_logger = action_logger or get_action_logger()
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize causal database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS causal_links (
                    id TEXT PRIMARY KEY,
                    cause_action_id TEXT,
                    effect_action_id TEXT,
                    cause_type TEXT,
                    effect_type TEXT,
                    strength REAL,
                    time_delay_seconds REAL,
                    evidence_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    last_observed TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT,
                    context TEXT,
                    outcome TEXT,
                    timestamp TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS counterfactuals (
                    id TEXT PRIMARY KEY,
                    actual_action_id TEXT,
                    hypothetical_action TEXT,
                    actual_outcome TEXT,
                    predicted_outcome TEXT,
                    confidence REAL,
                    created_at TEXT,
                    validated INTEGER DEFAULT 0,
                    actual_vs_predicted_diff REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS root_cause_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_event_id TEXT,
                    root_causes TEXT,
                    contributing_factors TEXT,
                    analysis_depth INTEGER,
                    confidence REAL,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
    
    def record_observation(self,
                          action_id: str,
                          context: Dict[str, Any],
                          outcome: Dict[str, Any]) -> None:
        """
        Record an observation for causal analysis.
        
        Args:
            action_id: ID of the action
            context: Conditions at time of action (field_status, time, etc.)
            outcome: Results (engagement, success, etc.)
        """
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO observations (action_id, context, outcome, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                action_id,
                json.dumps(context),
                json.dumps(outcome),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        logger.debug(f"📝 Recorded observation for {action_id}")
    
    def find_correlations(self,
                         outcome_type: str,
                         min_strength: float = 0.6) -> List[CausalLink]:
        """
        Find correlations between context factors and outcomes.
        
        Args:
            outcome_type: Type of outcome to analyze (e.g., 'high_engagement', 'success')
            min_strength: Minimum correlation strength (0-1)
            
        Returns:
            List of CausalLinks sorted by strength
        """
        correlations = []
        
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM observations ORDER BY timestamp'
            ).fetchall()
        
        if len(rows) < 10:
            logger.warning("Insufficient data for correlation analysis")
            return []
        
        # Parse observations
        observations = []
        for row in rows:
            observations.append({
                'action_id': row['action_id'],
                'context': json.loads(row['context']),
                'outcome': json.loads(row['outcome']),
                'timestamp': datetime.fromisoformat(row['timestamp'])
            })
        
        # Find correlations for each context factor
        context_keys = set()
        for obs in observations:
            context_keys.update(obs['context'].keys())
        
        for key in context_keys:
            strength = self._calculate_correlation(observations, key, outcome_type)
            if strength >= min_strength:
                link = CausalLink(
                    id=f"cor_{key}_{outcome_type}",
                    cause_action_id="context",
                    effect_action_id=outcome_type,
                    cause_type=f"context:{key}",
                    effect_type=outcome_type,
                    strength=strength,
                    time_delay_seconds=0,
                    evidence_count=len(observations)
                )
                correlations.append(link)
        
        # Sort by strength
        correlations.sort(key=lambda x: x.strength, reverse=True)
        
        return correlations
    
    def _calculate_correlation(self,
                               observations: List[Dict],
                               context_key: str,
                               outcome_type: str) -> float:
        """Calculate correlation strength between context factor and outcome"""
        # Simple correlation: does this context factor appear more in positive outcomes?
        
        with_factor = []
        without_factor = []
        
        for obs in observations:
            has_factor = context_key in obs['context']
            outcome_val = obs['outcome'].get(outcome_type) or obs['outcome'].get('success', 0)
            
            if isinstance(outcome_val, bool):
                outcome_val = 1 if outcome_val else 0
            elif isinstance(outcome_val, (int, float)):
                pass
            else:
                outcome_val = 0
            
            if has_factor:
                with_factor.append(outcome_val)
            else:
                without_factor.append(outcome_val)
        
        if not with_factor or not without_factor:
            return 0.0
        
        # Calculate difference in means
        mean_with = sum(with_factor) / len(with_factor)
        mean_without = sum(without_factor) / len(without_factor)
        
        # Normalize to 0-1 scale
        max_possible = max(max(with_factor, default=1), max(without_factor, default=1))
        if max_possible == 0:
            return 0.0
        
        diff = abs(mean_with - mean_without) / max_possible
        
        return min(1.0, diff)
    
    def find_causes(self,
                   action_id: str,
                   outcome_type: str,
                   max_depth: int = 2) -> List[CausalLink]:
        """
        Find probable causes of a specific outcome.
        
        Args:
            action_id: The action to analyze
            outcome_type: Type of outcome we're investigating
            max_depth: How far back to search
            
        Returns:
            List of probable causes ranked by confidence
        """
        causes = []
        
        # Get observation for this action
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM observations WHERE action_id = ?',
                (action_id,)
            ).fetchone()
        
        if not row:
            return []
        
        context = json.loads(row['context'])
        outcome = json.loads(row['outcome'])
        timestamp = datetime.fromisoformat(row['timestamp'])
        
        # Find correlations that match this context
        correlations = self.find_correlations(outcome_type, min_strength=0.5)
        
        for link in correlations:
            # Check if this context factor was present
            factor_key = link.cause_type.replace("context:", "")
            if factor_key in context:
                link.last_observed = timestamp
                causes.append(link)
        
        # Sort by confidence
        causes.sort(key=lambda x: x.confidence * x.strength, reverse=True)
        
        return causes[:5]  # Top 5 causes
    
    def simulate_counterfactual(self,
                                actual_action_id: str,
                                hypothetical_change: Dict[str, Any]) -> Counterfactual:
        """
        Simulate "what if I had done X instead?"
        
        Args:
            actual_action_id: The action that was actually taken
            hypothetical_change: What would have been different (e.g., {"time": "night"})
            
        Returns:
            Counterfactual with predicted outcome
        """
        # Get actual observation
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM observations WHERE action_id = ?',
                (actual_action_id,)
            ).fetchone()
        
        if not row:
            raise ValueError(f"Action {actual_action_id} not found")
        
        actual_context = json.loads(row['context'])
        actual_outcome = json.loads(row['outcome'])
        
        # Create hypothetical context
        hypothetical_context = {**actual_context, **hypothetical_change}
        
        # Find similar past scenarios
        similar = self._find_similar_observations(hypothetical_context)
        
        # Predict outcome based on similar scenarios
        if similar:
            predicted_outcome = self._aggregate_outcomes(similar)
            confidence = min(0.9, len(similar) / 20)  # More data = higher confidence
        else:
            # No similar scenarios - make conservative prediction
            predicted_outcome = {"success_probability": 0.5, "estimated_engagement": 10}
            confidence = 0.3
        
        counterfactual = Counterfactual(
            id=f"cf_{actual_action_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            actual_action_id=actual_action_id,
            hypothetical_action=json.dumps(hypothetical_change),
            actual_outcome=actual_outcome,
            predicted_outcome=predicted_outcome,
            confidence=confidence
        )
        
        # Store counterfactual
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO counterfactuals 
                (id, actual_action_id, hypothetical_action, actual_outcome, 
                 predicted_outcome, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                counterfactual.id,
                counterfactual.actual_action_id,
                counterfactual.hypothetical_action,
                json.dumps(counterfactual.actual_outcome),
                json.dumps(counterfactual.predicted_outcome),
                counterfactual.confidence,
                counterfactual.created_at.isoformat()
            ))
            conn.commit()
        
        return counterfactual
    
    def _find_similar_observations(self, context: Dict[str, Any], limit: int = 20) -> List[Dict]:
        """Find past observations with similar context"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM observations ORDER BY timestamp DESC LIMIT 100'
            ).fetchall()
        
        similar = []
        for row in rows:
            obs_context = json.loads(row['context'])
            
            # Calculate similarity score
            matches = sum(1 for k, v in context.items() if obs_context.get(k) == v)
            total_keys = len(context)
            
            if total_keys > 0 and matches / total_keys >= 0.7:  # 70% match threshold
                similar.append({
                    'action_id': row['action_id'],
                    'context': obs_context,
                    'outcome': json.loads(row['outcome'])
                })
            
            if len(similar) >= limit:
                break
        
        return similar
    
    def _aggregate_outcomes(self, observations: List[Dict]) -> Dict[str, Any]:
        """Aggregate outcomes from similar observations"""
        if not observations:
            return {}
        
        result = {}
        
        # Collect all outcome keys
        all_keys = set()
        for obs in observations:
            all_keys.update(obs['outcome'].keys())
        
        for key in all_keys:
            values = [obs['outcome'][key] for obs in observations if key in obs['outcome']]
            
            if values:
                if isinstance(values[0], (int, float)):
                    result[key] = sum(values) / len(values)  # Average
                elif isinstance(values[0], bool):
                    result[key] = sum(values) / len(values) > 0.5  # Majority
                else:
                    result[key] = max(set(values), key=values.count)  # Mode
        
        return result
    
    def analyze_root_cause(self,
                          event_id: str,
                          depth: int = 3) -> RootCauseAnalysis:
        """
        Perform root cause analysis on an event.
        
        Traces back through causal chains to find ultimate causes.
        
        Args:
            event_id: The event to analyze
            depth: How many levels deep to trace
            
        Returns:
            RootCauseAnalysis with cause chain
        """
        root_causes = []
        contributing = []
        
        current_id = event_id
        current_depth = 0
        
        while current_depth < depth:
            # Find causes of current event
            with sqlite3.connect(self.DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                # Look for links where this is the effect
                links = conn.execute(
                    '''SELECT * FROM causal_links 
                       WHERE effect_action_id = ? 
                       ORDER BY strength DESC''',
                    (current_id,)
                ).fetchall()
            
            if not links:
                break
            
            for link in links:
                link_data = {
                    'cause_id': link['cause_action_id'],
                    'strength': link['strength'],
                    'confidence': CausalLink(
                        id=link['id'],
                        cause_action_id=link['cause_action_id'],
                        effect_action_id=link['effect_action_id'],
                        cause_type=link['cause_type'],
                        effect_type=link['effect_type'],
                        strength=link['strength'],
                        time_delay_seconds=link['time_delay_seconds'],
                        evidence_count=link['evidence_count']
                    ).confidence,
                    'depth': current_depth
                }
                
                if current_depth == 0:
                    contributing.append(link['cause_action_id'])
                
                root_causes.append(link_data)
                current_id = link['cause_action_id']
                break  # Follow strongest link
            
            current_depth += 1
        
        # Calculate overall confidence
        if root_causes:
            confidence = sum(c['confidence'] for c in root_causes) / len(root_causes)
        else:
            confidence = 0.0
        
        analysis = RootCauseAnalysis(
            target_event_id=event_id,
            root_causes=root_causes,
            contributing_factors=list(set(contributing)),
            analysis_depth=current_depth,
            confidence=confidence
        )
        
        # Store analysis
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO root_cause_analyses 
                (target_event_id, root_causes, contributing_factors, 
                 analysis_depth, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis.target_event_id,
                json.dumps(analysis.root_causes),
                json.dumps(analysis.contributing_factors),
                analysis.analysis_depth,
                analysis.confidence,
                analysis.timestamp.isoformat()
            ))
            conn.commit()
        
        return analysis
    
    def get_impact_attribution(self,
                              outcome_metric: str,
                              time_window_hours: int = 24) -> Dict[str, float]:
        """
        Attribute outcomes to specific actions/factors.
        
        Returns a breakdown of which actions contributed most to a metric.
        
        Example:
            {"post_morning": 0.35, "reply_insightful": 0.25, "like_high_conf": 0.15}
        """
        attribution = defaultdict(float)
        
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT * FROM observations 
                   WHERE timestamp > ? 
                   ORDER BY timestamp''',
                (cutoff.isoformat(),)
            ).fetchall()
        
        for row in rows:
            context = json.loads(row['context'])
            outcome = json.loads(row['outcome'])
            
            value = outcome.get(outcome_metric, 0)
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            
            # Attribute to context factors
            for key, val in context.items():
                factor_name = f"{key}={val}"
                attribution[factor_name] += value
        
        # Normalize
        total = sum(attribution.values())
        if total > 0:
            attribution = {k: v/total for k, v in attribution.items()}
        
        # Sort by contribution
        return dict(sorted(attribution.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def get_causal_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of causal relationships discovered"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Recent observations
            obs_count = conn.execute(
                'SELECT COUNT(*) FROM observations WHERE timestamp > ?',
                (cutoff.isoformat(),)
            ).fetchone()[0]
            
            # Causal links
            links = conn.execute(
                'SELECT COUNT(*) FROM causal_links WHERE evidence_count > 0'
            ).fetchone()[0]
            
            # Top correlations
            top_links = conn.execute(
                '''SELECT cause_type, effect_type, strength 
                   FROM causal_links 
                   ORDER BY strength DESC 
                   LIMIT 5'''
            ).fetchall()
        
        return {
            'observations_recorded': obs_count,
            'causal_links_discovered': links,
            'top_correlations': [
                {
                    'cause': row['cause_type'],
                    'effect': row['effect_type'],
                    'strength': row['strength']
                }
                for row in top_links
            ]
        }


# Singleton
_causal_engine_instance: Optional[CausalEngine] = None


def get_causal_engine(action_logger: Optional[ActionLogger] = None) -> CausalEngine:
    """Get or create CausalEngine singleton"""
    global _causal_engine_instance
    if _causal_engine_instance is None:
        _causal_engine_instance = CausalEngine(action_logger)
    return _causal_engine_instance
