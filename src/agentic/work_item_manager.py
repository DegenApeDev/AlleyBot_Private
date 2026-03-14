"""
Durable work-item persistence for AlleyBot.

Provides a lightweight SQL-backed manager for meaningful work discovered from
existing goals and world-state signals so the AGI kernel can preserve work
continuity across cycles and restarts.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class WorkItemManager:
    """Persist and retrieve lightweight work items for the AGI core."""

    ACTIVE_STATUSES = ('detected', 'active', 'waiting')
    URGENCY_RANKS = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1,
    }

    def __init__(self, db_path: str = 'data/work_items.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            # Create table if not exists
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS work_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    goal_id TEXT,
                    source_event_id TEXT,
                    source_entity_id TEXT,
                    recommended_action_family TEXT,
                    urgency TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'active',
                    topic TEXT,
                    metadata TEXT DEFAULT '{}',
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_attempt_at TEXT,
                    last_outcome TEXT,
                    blocked_reason TEXT,
                    capability_gap_hint TEXT
                )
                '''
            )
            # Migration: Add missing columns if they don't exist
            self._migrate_add_column(conn, 'title', 'TEXT NOT NULL DEFAULT \'\'')  
            self._migrate_add_column(conn, 'status', 'TEXT DEFAULT \'active\'')
            self._migrate_add_column(conn, 'blocked_reason', 'TEXT')
            self._migrate_add_column(conn, 'capability_gap_hint', 'TEXT')
            self._migrate_add_column(conn, 'last_attempt_at', 'TEXT')
            self._migrate_add_column(conn, 'last_outcome', 'TEXT')
            
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_items_status ON work_items(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_items_source ON work_items(source)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_items_goal_id ON work_items(goal_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_items_last_seen ON work_items(last_seen_at DESC)"
            )
            conn.commit()

    def _migrate_add_column(self, conn: sqlite3.Connection, column: str, col_type: str) -> None:
        """Add a column if it doesn't exist (handles schema migrations)."""
        try:
            conn.execute(f"SELECT {column} FROM work_items LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower():
                logger.info(f"🔄 Migrating database: adding column '{column}'")
                conn.execute(f"ALTER TABLE work_items ADD COLUMN {column} {col_type}")
                conn.commit()
            else:
                raise

    def upsert_work_item(self, item: Dict[str, Any]) -> bool:
        if not item or not item.get('id'):
            return False

        now = datetime.now().isoformat()
        status = item.get('status') or 'active'
        metadata = dict(item.get('metadata') or {})

        for field in (
            'goal_id',
            'source_event_id',
            'source_entity_id',
            'topic',
            'urgency',
            'recommended_action_family',
            'blocked_reason',
            'capability_gap_hint',
            'last_outcome',
            'last_attempt_at',
        ):
            if field in item and field not in metadata:
                metadata[field] = item.get(field)

        with self._get_connection() as conn:
            conn.execute(
                '''
                INSERT INTO work_items (
                    id, title, type, source, summary, goal_id, source_event_id,
                    source_entity_id, recommended_action_family, urgency, status, state,
                    topic, metadata, first_seen_at, last_seen_at, updated_at,
                    last_attempt_at, last_outcome, blocked_reason, capability_gap_hint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    type = excluded.type,
                    source = excluded.source,
                    summary = excluded.summary,
                    goal_id = COALESCE(excluded.goal_id, work_items.goal_id),
                    source_event_id = COALESCE(excluded.source_event_id, work_items.source_event_id),
                    source_entity_id = COALESCE(excluded.source_entity_id, work_items.source_entity_id),
                    recommended_action_family = COALESCE(excluded.recommended_action_family, work_items.recommended_action_family),
                    urgency = COALESCE(excluded.urgency, work_items.urgency),
                    status = CASE
                        WHEN work_items.status IN ('completed', 'abandoned') AND excluded.status = 'active' THEN work_items.status
                        ELSE COALESCE(excluded.status, work_items.status)
                    END,
                    state = CASE
                        WHEN work_items.state IN ('completed', 'abandoned') AND excluded.state = 'active' THEN work_items.state
                        ELSE COALESCE(excluded.state, work_items.state)
                    END,
                    topic = COALESCE(excluded.topic, work_items.topic),
                    metadata = excluded.metadata,
                    last_seen_at = excluded.last_seen_at,
                    updated_at = excluded.updated_at,
                    last_attempt_at = COALESCE(excluded.last_attempt_at, work_items.last_attempt_at),
                    last_outcome = COALESCE(excluded.last_outcome, work_items.last_outcome),
                    blocked_reason = COALESCE(excluded.blocked_reason, work_items.blocked_reason),
                    capability_gap_hint = COALESCE(excluded.capability_gap_hint, work_items.capability_gap_hint)
                ''',
                (
                    item['id'],
                    item.get('title') or item.get('summary', '')[:50] or 'work item',
                    item.get('type') or 'unknown',
                    item.get('source') or 'unknown',
                    item.get('summary') or 'meaningful work item',
                    item.get('goal_id'),
                    item.get('source_event_id'),
                    item.get('source_entity_id'),
                    item.get('recommended_action_family'),
                    item.get('urgency') or 'medium',
                    status,
                    status,  # state column (same as status for compatibility)
                    item.get('topic'),
                    json.dumps(metadata),
                    item.get('first_seen_at') or now,
                    now,
                    now,
                    item.get('last_attempt_at'),
                    item.get('last_outcome'),
                    item.get('blocked_reason'),
                    item.get('capability_gap_hint'),
                ),
            )
            conn.commit()
        return True

    def upsert_many(self, items: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for item in items or []:
            if self.upsert_work_item(item):
                count += 1
        return count

    def get_active_work_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        placeholders = ', '.join('?' for _ in self.ACTIVE_STATUSES)
        with self._get_connection() as conn:
            rows = conn.execute(
                f'''
                SELECT * FROM work_items
                WHERE status IN ({placeholders})
                ORDER BY
                    CASE urgency
                        WHEN 'critical' THEN 4
                        WHEN 'high' THEN 3
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 1
                        ELSE 0
                    END DESC,
                    last_seen_at DESC,
                    first_seen_at ASC
                LIMIT ?
                ''',
                (*self.ACTIVE_STATUSES, limit),
            ).fetchall()
        items = [self._row_to_dict(row) for row in rows]
        items.sort(
            key=lambda item: (
                self._get_trust_compatibility_rank(item),
                self._get_upgrade_readiness_rank(item),
                self.URGENCY_RANKS.get(str(item.get('urgency', 'medium')).lower(), 0),
                str(item.get('last_seen_at') or ''),
            ),
            reverse=True,
        )
        return items[:limit]

    def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        if not work_item_id:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM work_items WHERE id = ?",
                (work_item_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def record_attempt(self, work_item_id: str, outcome: Optional[str] = None) -> bool:
        if not work_item_id:
            return False
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                UPDATE work_items
                SET last_attempt_at = ?, last_outcome = COALESCE(?, last_outcome), updated_at = ?
                WHERE id = ?
                ''',
                (now, outcome, now, work_item_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def complete_work_item(self, work_item_id: str, outcome: Optional[str] = None) -> bool:
        if not work_item_id:
            return False
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                UPDATE work_items
                SET status = 'completed', last_attempt_at = ?, last_outcome = COALESCE(?, last_outcome),
                    blocked_reason = NULL, updated_at = ?
                WHERE id = ?
                ''',
                (now, outcome, now, work_item_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def abandon_work_item(self, work_item_id: str, outcome: Optional[str] = None, reason: Optional[str] = None) -> bool:
        if not work_item_id:
            return False
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                UPDATE work_items
                SET status = 'abandoned', last_attempt_at = ?, last_outcome = COALESCE(?, last_outcome),
                    blocked_reason = COALESCE(?, blocked_reason), updated_at = ?
                WHERE id = ?
                ''',
                (now, outcome, reason, now, work_item_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def persist_capability_judgment(self, work_item_id: str, judgment: Dict[str, Any]) -> bool:
        if not work_item_id or not judgment:
            return False

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT metadata, status, blocked_reason, capability_gap_hint FROM work_items WHERE id = ?",
                (work_item_id,),
            ).fetchone()
            if not row:
                return False

            metadata_blob = row['metadata'] if isinstance(row, sqlite3.Row) else row[0]
            try:
                metadata = json.loads(metadata_blob) if metadata_blob else {}
            except Exception:
                metadata = {}

            prior_judgment = metadata.get('capability_judgment') or {}
            prior_evidence = metadata.get('upgrade_evidence') or {}
            repeated_need_count = int(prior_evidence.get('repeated_need_count', 0) or 0)
            if judgment.get('needs_new_skill'):
                if prior_judgment.get('needs_new_skill'):
                    repeated_need_count += 1
                else:
                    repeated_need_count = 1
            else:
                repeated_need_count = 0

            metadata['capability_judgment'] = judgment
            metadata['judgment_updated_at'] = datetime.now().isoformat()
            metadata['upgrade_evidence'] = {
                'repeated_need_count': repeated_need_count,
                'last_primary_reason': judgment.get('primary_reason'),
                'last_summary': judgment.get('summary'),
                'last_evaluated_at': datetime.now().isoformat(),
            }

            if repeated_need_count >= 2 and judgment.get('needs_new_skill'):
                metadata['bounded_upgrade_objective'] = {
                    'objective_type': 'capability_gap_remediation',
                    'work_item_id': work_item_id,
                    'scope': 'bounded',
                    'target_gap': judgment.get('summary') or judgment.get('primary_reason') or 'needs_new_skill',
                    'evidence_count': repeated_need_count,
                    'allowed_actions': ['analyze', 'report', 'propose_safe_upgrade'],
                    'status': 'proposed',
                }

            status = row['status'] if isinstance(row, sqlite3.Row) else row[1]
            blocked_reason = row['blocked_reason'] if isinstance(row, sqlite3.Row) else row[2]
            capability_gap_hint = row['capability_gap_hint'] if isinstance(row, sqlite3.Row) else row[3]

            if judgment.get('blocked_by_policy'):
                status = 'blocked'
                blocked_reason = 'policy_gate'
            elif judgment.get('blocked_by_runtime_readiness'):
                status = 'waiting'
                blocked_reason = judgment.get('blocked_reason') or 'runtime_not_ready'
            elif judgment.get('can_execute_now'):
                status = 'active'
                blocked_reason = None

            if judgment.get('needs_new_skill'):
                capability_gap_hint = judgment.get('summary') or judgment.get('primary_reason') or 'needs_new_skill'

            conn.execute(
                '''
                UPDATE work_items
                SET metadata = ?, status = ?, blocked_reason = ?, capability_gap_hint = ?, updated_at = ?
                WHERE id = ?
                ''',
                (
                    json.dumps(metadata),
                    status,
                    blocked_reason,
                    capability_gap_hint,
                    datetime.now().isoformat(),
                    work_item_id,
                ),
            )
            conn.commit()
            return True

    def update_status(
        self,
        work_item_id: str,
        status: str,
        blocked_reason: Optional[str] = None,
        last_outcome: Optional[str] = None,
    ) -> bool:
        if not work_item_id:
            return False
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                UPDATE work_items
                SET status = ?, blocked_reason = COALESCE(?, blocked_reason),
                    last_outcome = COALESCE(?, last_outcome), updated_at = ?
                WHERE id = ?
                ''',
                (status, blocked_reason, last_outcome, now, work_item_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        metadata = item.get('metadata')
        try:
            parsed_metadata = json.loads(metadata) if metadata else {}
        except Exception:
            parsed_metadata = {}
        item['metadata'] = parsed_metadata
        for key, value in parsed_metadata.items():
            item.setdefault(key, value)
        return item

    def _get_trust_compatibility_rank(self, item: Dict[str, Any]) -> int:
        judgment = item.get('capability_judgment') or (item.get('metadata') or {}).get('capability_judgment') or {}
        if judgment.get('blocked_by_policy'):
            return 0
        if judgment.get('blocked_by_runtime_readiness'):
            return 1
        if judgment.get('needs_new_skill'):
            return 2
        if judgment.get('needs_different_strategy') or judgment.get('needs_more_context'):
            return 3
        if judgment.get('can_execute_now'):
            return 5
        return 4

    def _get_upgrade_readiness_rank(self, item: Dict[str, Any]) -> int:
        metadata = item.get('metadata') or {}
        evidence = metadata.get('upgrade_evidence') or {}
        objective = metadata.get('bounded_upgrade_objective') or {}
        repeated_need_count = int(evidence.get('repeated_need_count', 0) or 0)
        if objective and objective.get('status') == 'proposed':
            return min(repeated_need_count, 3)
        return 0


def create_work_item_manager(core=None) -> WorkItemManager:
    if core and hasattr(core, 'data_dir') and core.data_dir:
        db_path = Path(core.data_dir) / 'work_items.db'
    else:
        db_path = Path('data') / 'work_items.db'
    return WorkItemManager(str(db_path))
