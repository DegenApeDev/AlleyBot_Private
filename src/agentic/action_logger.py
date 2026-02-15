"""
AlleyBot Autonomous Action Logger

Tracks every action Alley takes with full context for learning.
Part of AGI Core - Phase 1: Self-Reflection System
"""

import json
import sqlite3
import os
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
