"""
AlleyBot Autonomous Action Logger

Tracks every action Alley takes with full context for learning.
Part of AGI Core - Phase 1: Self-Reflection System
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActionRecord:
    """Complete record of an autonomous action"""
    id: str
    timestamp: datetime
    action_type: str  # 'like', 'reply', 'post', 'trade', 'alert'
    plugin: str  # Which plugin executed it
    target_id: Optional[str]
    target_name: Optional[str]
    content: Optional[str]  # For replies/posts
    
    # Context at time of action
    confidence: float  # SyMod confidence score
    field_status: str  # Stable/Volatile/Collapse
    impedance: float  # Action difficulty
    justification: str  # Why SyMod chose this
    
    # Trigger context
    trigger_type: str  # 'mention', 'trending', 'scheduled', 'opportunity'
    trigger_data: Dict[str, Any]  # What caused this action
    
    # Outcome (filled later)
    outcome: Optional[str] = None  # 'success', 'failure', 'blocked'
    outcome_data: Optional[Dict] = None  # Detailed result
    engagement_received: float = 0.0  # Likes/replies on our action
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class ActionLogger:
    """
    Logs all autonomous actions for learning and analysis.
    
    Usage:
        logger = ActionLogger()
        
        # Log action start
        record = logger.log_action(
            action_type='reply',
            plugin='moltx',
            target_id='post_123',
            content='Great insight!',
            confidence=0.85,
            field_status='Stable',
            trigger_type='mention',
            trigger_data={'user': '@alice', 'content': 'What do you think?'}
        )
        
        # Later, log outcome
        logger.log_outcome(record.id, 'success', {
            'engagement': 12,
            'replies': 3
        })
    """
    
    def __init__(self, db_path: str = 'data/action_log.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    action_type TEXT,
                    plugin TEXT,
                    target_id TEXT,
                    target_name TEXT,
                    content TEXT,
                    confidence REAL,
                    field_status TEXT,
                    impedance REAL,
                    justification TEXT,
                    trigger_type TEXT,
                    trigger_data TEXT,
                    outcome TEXT,
                    outcome_data TEXT,
                    engagement_received REAL
                )
            ''')
            
            # Indexes for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON actions(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_plugin ON actions(plugin)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_outcome ON actions(outcome)')
            conn.commit()
    
    def log_action(self, 
                   action_type: str,
                   plugin: str,
                   target_id: Optional[str] = None,
                   target_name: Optional[str] = None,
                   content: Optional[str] = None,
                   confidence: float = 0.0,
                   field_status: str = 'Unknown',
                   impedance: float = 0.0,
                   justification: str = '',
                   trigger_type: str = 'scheduled',
                   trigger_data: Optional[Dict] = None) -> ActionRecord:
        """
        Log an action being taken.
        
        Returns:
            ActionRecord with generated ID for later outcome logging
        """
        import uuid
        
        record = ActionRecord(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            action_type=action_type,
            plugin=plugin,
            target_id=target_id,
            target_name=target_name,
            content=content,
            confidence=confidence,
            field_status=field_status,
            impedance=impedance,
            justification=justification,
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            outcome=None,
            outcome_data=None,
            engagement_received=0.0
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO actions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id,
                record.timestamp.isoformat(),
                record.action_type,
                record.plugin,
                record.target_id,
                record.target_name,
                record.content,
                record.confidence,
                record.field_status,
                record.impedance,
                record.justification,
                record.trigger_type,
                json.dumps(record.trigger_data),
                record.outcome,
                json.dumps(record.outcome_data) if record.outcome_data else None,
                record.engagement_received
            ))
            conn.commit()
        
        logger.info(f"📝 Logged action: {action_type} by {plugin} (conf: {confidence:.2f})")
        return record
    
    def log_outcome(self, 
                    action_id: str,
                    outcome: str,
                    outcome_data: Optional[Dict] = None,
                    engagement_received: float = 0.0) -> None:
        """Update action record with outcome"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE actions 
                SET outcome = ?, outcome_data = ?, engagement_received = ?
                WHERE id = ?
            ''', (
                outcome,
                json.dumps(outcome_data) if outcome_data else None,
                engagement_received,
                action_id
            ))
            conn.commit()
        
        logger.info(f"📊 Logged outcome for {action_id}: {outcome}")

    def log_outcome_record(self, outcome_record: Dict[str, Any]) -> Optional[ActionRecord]:
        """Ingest a canonical router outcome record into the action log store."""
        if not outcome_record:
            return None

        validation = outcome_record.get('validation', {})
        field_state = validation.get('field_state') or {}
        trigger = outcome_record.get('trigger', 'scheduled')
        success = outcome_record.get('success', False)
        prediction_evaluation = outcome_record.get('prediction_evaluation', {}) or {}
        reflection_summary = outcome_record.get('reflection_summary') or prediction_evaluation.get('reflection_summary', '')
        mismatch_score = outcome_record.get('mismatch_score', prediction_evaluation.get('mismatch_score'))

        record = ActionRecord(
            id=outcome_record.get('action_id', f"action_{datetime.now().strftime('%Y%m%d%H%M%S')}")[:32],
            timestamp=datetime.fromisoformat(outcome_record.get('timestamp', datetime.now().isoformat())),
            action_type=outcome_record.get('action_type', 'unknown'),
            plugin=outcome_record.get('plugin', 'unknown'),
            target_id=None,
            target_name=outcome_record.get('goal_description'),
            content=outcome_record.get('params_summary'),
            confidence=validation.get('synergy_score') or 0.0,
            field_status=field_state.get('phase', 'Unknown') if isinstance(field_state, dict) else 'Unknown',
            impedance=0.0,
            justification=validation.get('synergy_reasoning', ''),
            trigger_type=trigger,
            trigger_data={
                'goal_id': outcome_record.get('goal_id'),
                'source': outcome_record.get('source'),
                'impact': outcome_record.get('impact'),
                'validation': validation,
                'prediction': outcome_record.get('prediction'),
                'prediction_evaluation': prediction_evaluation,
                'mismatch_score': mismatch_score,
                'reflection_summary': reflection_summary,
            },
            outcome='success' if success else 'failure',
            outcome_data={
                'result_summary': outcome_record.get('result_summary'),
                'prediction_evaluation': prediction_evaluation,
                'mismatch_score': mismatch_score,
                'reflection_summary': reflection_summary,
            },
            engagement_received=0.0,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO actions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id,
                record.timestamp.isoformat(),
                record.action_type,
                record.plugin,
                record.target_id,
                record.target_name,
                record.content,
                record.confidence,
                record.field_status,
                record.impedance,
                record.justification,
                record.trigger_type,
                json.dumps(record.trigger_data),
                record.outcome,
                json.dumps(record.outcome_data) if record.outcome_data else None,
                record.engagement_received
            ))
            conn.commit()

        logger.info(f"🧾 Logged canonical outcome record: {record.action_type} by {record.plugin}")
        return record
    
    def get_recent_actions(self, 
                           plugin: Optional[str] = None,
                           action_type: Optional[str] = None,
                           outcome: Optional[str] = None,
                           limit: int = 50) -> List[ActionRecord]:
        """Get recent actions with optional filters"""
        query = 'SELECT * FROM actions WHERE 1=1'
        params = []
        
        if plugin:
            query += ' AND plugin = ?'
            params.append(plugin)
        if action_type:
            query += ' AND action_type = ?'
            params.append(action_type)
        if outcome:
            query += ' AND outcome = ?'
            params.append(outcome)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def get_success_rate(self, 
                         plugin: Optional[str] = None,
                         action_type: Optional[str] = None,
                         hours: int = 24) -> float:
        """Calculate success rate for given filters"""
        from datetime import timedelta
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        query = '''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes
            FROM actions 
            WHERE timestamp > ?
        '''
        params = [cutoff]
        
        if plugin:
            query += ' AND plugin = ?'
            params.append(plugin)
        if action_type:
            query += ' AND action_type = ?'
            params.append(action_type)
        
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
            
            total = row[0] or 0
            successes = row[1] or 0
            
            return successes / total if total > 0 else 0.0
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        from datetime import timedelta
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Total actions
            total = conn.execute(
                'SELECT COUNT(*) FROM actions WHERE timestamp > ?',
                [cutoff]
            ).fetchone()[0]
            
            # By outcome
            outcomes = conn.execute('''
                SELECT outcome, COUNT(*) 
                FROM actions 
                WHERE timestamp > ?
                GROUP BY outcome
            ''', [cutoff]).fetchall()
            
            # By plugin
            by_plugin = conn.execute('''
                SELECT plugin, COUNT(*), AVG(confidence)
                FROM actions 
                WHERE timestamp > ?
                GROUP BY plugin
            ''', [cutoff]).fetchall()
            
            # By action type
            by_type = conn.execute('''
                SELECT action_type, COUNT(*)
                FROM actions 
                WHERE timestamp > ?
                GROUP BY action_type
            ''', [cutoff]).fetchall()
        
        return {
            'period_hours': hours,
            'total_actions': total,
            'by_outcome': {row[0]: row[1] for row in outcomes if row[0]},
            'by_plugin': {
                row[0]: {'count': row[1], 'avg_confidence': round(row[2] or 0, 2)}
                for row in by_plugin
            },
            'by_action_type': {row[0]: row[1] for row in by_type},
            'success_rate': self.get_success_rate(hours=hours)
        }
    
    def get_action_performance_summary(self, hours: int = 72, limit: int = 25) -> Dict[str, Dict[str, Any]]:
        """Return recent per-action outcome summaries for memory-informed decision ranking."""
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT
                    action_type,
                    plugin,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failures,
                    AVG(confidence) as avg_confidence,
                    AVG(engagement_received) as avg_engagement,
                    MAX(timestamp) as last_seen
                FROM actions
                WHERE timestamp > ?
                  AND action_type IS NOT NULL
                GROUP BY action_type, plugin
                ORDER BY total DESC, last_seen DESC
                LIMIT ?
            ''', [cutoff, limit]).fetchall()

        summary = {}
        for row in rows:
            action_type, plugin, total, successes, failures, avg_confidence, avg_engagement, last_seen = row
            action_id = f"{plugin}:{action_type}" if plugin and plugin != 'unknown' else action_type
            total = total or 0
            successes = successes or 0
            failures = failures or 0
            records = self.get_recent_actions(plugin=plugin, action_type=action_type, limit=min(limit, max(total, 1)))

            mismatch_scores = []
            overconfident_count = 0
            underconfident_count = 0
            well_calibrated_count = 0
            high_mismatch_count = 0
            reflection_summaries = []
            predicted_successes = 0
            predicted_failures = 0

            for record in records:
                outcome_data = record.outcome_data or {}
                prediction_evaluation = outcome_data.get('prediction_evaluation', {}) or {}
                mismatch_score = outcome_data.get('mismatch_score', prediction_evaluation.get('mismatch_score'))
                if isinstance(mismatch_score, (int, float)):
                    mismatch_scores.append(float(mismatch_score))
                    if float(mismatch_score) >= 0.6:
                        high_mismatch_count += 1

                calibration = prediction_evaluation.get('confidence_calibration')
                if calibration == 'overconfident':
                    overconfident_count += 1
                elif calibration == 'underconfident':
                    underconfident_count += 1
                elif calibration == 'well_calibrated':
                    well_calibrated_count += 1

                if prediction_evaluation.get('predicted_success') is True:
                    predicted_successes += 1
                elif prediction_evaluation.get('predicted_success') is False:
                    predicted_failures += 1

                reflection_summary = outcome_data.get('reflection_summary') or prediction_evaluation.get('reflection_summary')
                if reflection_summary:
                    reflection_summaries.append(reflection_summary)

            avg_mismatch = sum(mismatch_scores) / len(mismatch_scores) if mismatch_scores else 0.0
            summary[action_id] = {
                'action_type': action_type,
                'plugin': plugin,
                'total': total,
                'successes': successes,
                'failures': failures,
                'success_rate': (successes / total) if total else 0.0,
                'avg_confidence': float(avg_confidence or 0.0),
                'avg_engagement': float(avg_engagement or 0.0),
                'avg_mismatch_score': round(avg_mismatch, 4),
                'high_mismatch_rate': round((high_mismatch_count / total), 4) if total else 0.0,
                'overconfident_count': overconfident_count,
                'underconfident_count': underconfident_count,
                'well_calibrated_count': well_calibrated_count,
                'calibration_bias': (
                    'overconfident'
                    if overconfident_count > underconfident_count and overconfident_count > 0
                    else 'underconfident'
                    if underconfident_count > overconfident_count and underconfident_count > 0
                    else 'balanced'
                ),
                'predicted_successes': predicted_successes,
                'predicted_failures': predicted_failures,
                'recent_reflections': reflection_summaries[:3],
                'last_seen': last_seen,
            }

        return summary

    def _row_to_record(self, row: sqlite3.Row) -> ActionRecord:
        """Convert database row to ActionRecord"""
        return ActionRecord(
            id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            action_type=row['action_type'],
            plugin=row['plugin'],
            target_id=row['target_id'],
            target_name=row['target_name'],
            content=row['content'],
            confidence=row['confidence'],
            field_status=row['field_status'],
            impedance=row['impedance'],
            justification=row['justification'],
            trigger_type=row['trigger_type'],
            trigger_data=json.loads(row['trigger_data']) if row['trigger_data'] else {},
            outcome=row['outcome'],
            outcome_data=json.loads(row['outcome_data']) if row['outcome_data'] else None,
            engagement_received=row['engagement_received'] or 0.0
        )
    
    def close(self) -> None:
        """Close database connection"""
        pass  # SQLite connections are context-managed

    # =========================================================================
    # ASYNC WRAPPERS (P0-002: Fix Async Blocking I/O)
    # =========================================================================
    # These methods wrap synchronous DB operations in run_in_executor
    # to prevent blocking the async event loop.
    # =========================================================================

    async def alog_action(self, record: ActionRecord) -> bool:
        """Async version of log_action - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.log_action, record)

    async def alog_outcome_record(self, outcome_record: Dict[str, Any]) -> Optional[ActionRecord]:
        """Async version of log_outcome_record - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.log_outcome_record, outcome_record)

    async def aget_recent_actions(self,
                                   plugin: Optional[str] = None,
                                   action_type: Optional[str] = None,
                                   outcome: Optional[str] = None,
                                   limit: int = 50) -> List[ActionRecord]:
        """Async version of get_recent_actions - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_recent_actions, plugin, action_type, outcome, limit
        )

    async def aget_recent_outcomes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Async version of get_recent_outcomes - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_recent_outcomes, limit)

    async def aget_success_rate(self,
                                 plugin: Optional[str] = None,
                                 action_type: Optional[str] = None,
                                 hours: int = 24) -> float:
        """Async version of get_success_rate - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_success_rate, plugin, action_type, hours
        )

    async def aget_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Async version of get_statistics - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_statistics, hours)

    async def aget_action_performance_summary(self, hours: int = 72, limit: int = 25) -> Dict[str, Dict[str, Any]]:
        """Async version of get_action_performance_summary - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_action_performance_summary, hours, limit
        )


# Singleton instance
_action_logger_instance: Optional[ActionLogger] = None


def get_action_logger(db_path: str = 'data/action_log.db') -> ActionLogger:
    """Get or create ActionLogger singleton"""
    global _action_logger_instance
    if _action_logger_instance is None:
        _action_logger_instance = ActionLogger(db_path)
    return _action_logger_instance

