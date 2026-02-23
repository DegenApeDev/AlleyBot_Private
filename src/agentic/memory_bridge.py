"""
AGI Memory Bridge

Pumps data from all existing memory stores into world_state.facts so the
inference engine's detect_trends() has real signal data, and seeds the
metacognition capability DB from actual action success rates.

Sources:
- data/memory/alley_memory.db  → 396 platform interactions (posts, comments)
- data/action_log.db           → 170 logged actions with outcomes
- data/creative.db             → 184 creative concepts
- data/world_state.db events   → 200 platform events already recorded

Runs once at AGI cycle start (idempotent — skips already-imported rows).
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

WORLD_STATE_DB = Path('data/world_state.db')
ALLEY_MEMORY_DB = Path('data/memory/alley_memory.db')
ACTION_LOG_DB = Path('data/action_log.db')
CREATIVE_DB = Path('data/creative.db')
METACOGNITION_DB = Path('data/metacognition.db')

# Sentinel entity used for platform-level facts
PLATFORM_ENTITY_ID = 'platform_alleybot'


def _ensure_platform_entity(ws_conn: sqlite3.Connection) -> None:
    """Ensure the platform entity exists in world_state entities table."""
    existing = ws_conn.execute(
        'SELECT id FROM entities WHERE id = ?', (PLATFORM_ENTITY_ID,)
    ).fetchone()
    if not existing:
        now = datetime.now().isoformat()
        ws_conn.execute('''
            INSERT INTO entities (id, type, name, display_name, attributes,
                                  created_at, updated_at, confidence, last_observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            PLATFORM_ENTITY_ID, 'platform', 'AlleyBot Platform',
            'AlleyBot Platform', '{}', now, now, 1.0, now
        ))


def _already_imported(ws_conn: sqlite3.Connection, source_id: str) -> bool:
    """Check if a source record was already imported (by source field)."""
    try:
        row = ws_conn.execute(
            "SELECT 1 FROM facts WHERE source = ? LIMIT 1", (source_id,)
        ).fetchone()
        return row is not None
    except Exception:
        return False


def bridge_alley_memory(ws_conn: sqlite3.Connection, limit: int = 200) -> int:
    """
    Import platform interactions from alley_memory.db into world_state.facts.
    Each memory becomes a 'content' fact so detect_trends() can find it.
    """
    if not ALLEY_MEMORY_DB.exists():
        return 0

    imported = 0
    try:
        with sqlite3.connect(ALLEY_MEMORY_DB) as mem_conn:
            mem_conn.row_factory = sqlite3.Row
            # Get recent memories, convert to dicts inside context
            rows = [dict(r) for r in mem_conn.execute('''
                SELECT id, content, memory_type, timestamp, metadata
                FROM memories
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,)).fetchall()]

        for row in rows:
            source_tag = f'alley_memory:{row["id"]}'
            if _already_imported(ws_conn, source_tag):
                continue

            # Parse content — ensure result is always a dict
            try:
                parsed = json.loads(row['content'])
                content_data = parsed if isinstance(parsed, dict) else {'content': str(parsed)}
            except Exception:
                content_data = {'content': str(row['content'])}

            # Build a searchable content string
            post_title = content_data.get('post_title', '')
            message = content_data.get('message', '')
            author = content_data.get('author', 'unknown')
            content_str = f"{post_title} {message}".strip() or str(row['content'])[:200]

            # Determine entity — use author as entity if known
            entity_id = PLATFORM_ENTITY_ID
            if author and author != 'unknown':
                entity_id = f'user_{author[:40]}'
                _ensure_user_entity(ws_conn, entity_id, author, row['timestamp'])

            ts = row['timestamp'] or datetime.now().isoformat()

            ws_conn.execute('''
                INSERT INTO facts
                    (entity_id, attribute, value, value_type, timestamp, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                row['memory_type'] or 'interaction',
                json.dumps({'content': content_str, 'platform': 'moltx',
                            'author': author, 'raw': content_data}),
                'json',
                ts,
                source_tag,
                0.8,
            ))
            imported += 1

        ws_conn.commit()
    except Exception as e:
        logger.warning(f'memory_bridge: alley_memory import failed: {e}')

    return imported


def _ensure_user_entity(ws_conn: sqlite3.Connection, entity_id: str,
                         name: str, ts: str) -> None:
    """Ensure a user entity exists."""
    existing = ws_conn.execute(
        'SELECT id FROM entities WHERE id = ?', (entity_id,)
    ).fetchone()
    if not existing:
        now = ts or datetime.now().isoformat()
        ws_conn.execute('''
            INSERT INTO entities (id, type, name, display_name, attributes,
                                  created_at, updated_at, confidence, last_observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (entity_id, 'user', name, name, '{}', now, now, 0.9, now))


def bridge_action_log(ws_conn: sqlite3.Connection, limit: int = 100) -> int:
    """
    Import executed actions from action_log.db into world_state.facts.
    Successful content actions become 'post' facts for trend detection.
    """
    if not ACTION_LOG_DB.exists():
        return 0

    imported = 0
    try:
        with sqlite3.connect(ACTION_LOG_DB) as al_conn:
            al_conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in al_conn.execute('''
                SELECT id, action_type, plugin, content, confidence,
                       field_status, outcome, timestamp
                FROM actions
                WHERE content IS NOT NULL AND content != ''
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,)).fetchall()]

        for row in rows:
            source_tag = f'action_log:{row["id"]}'
            if _already_imported(ws_conn, source_tag):
                continue

            attribute = 'post' if row['outcome'] == 'success' else 'interaction'
            ws_conn.execute('''
                INSERT INTO facts
                    (entity_id, attribute, value, value_type, timestamp, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                PLATFORM_ENTITY_ID,
                attribute,
                json.dumps({
                    'content': row['content'][:500],
                    'platform': row['plugin'] or 'unknown',
                    'action_type': row['action_type'],
                    'outcome': row['outcome'],
                    'field_status': row['field_status'],
                }),
                'json',
                row['timestamp'] or datetime.now().isoformat(),
                source_tag,
                min(1.0, (row['confidence'] or 0.5) + 0.1),
            ))
            imported += 1

        ws_conn.commit()
    except Exception as e:
        logger.warning(f'memory_bridge: action_log import failed: {e}')

    return imported


def bridge_creative_concepts(ws_conn: sqlite3.Connection, limit: int = 50) -> int:
    """
    Import creative concepts into world_state.facts as 'content' facts.
    These give the inference engine topic signals even before live posts.
    """
    if not CREATIVE_DB.exists():
        return 0

    imported = 0
    try:
        with sqlite3.connect(CREATIVE_DB) as cr_conn:
            cr_conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in cr_conn.execute('''
                SELECT id, concept_type, title, description,
                       novelty_score, estimated_impact, created_at
                FROM creative_concepts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()]

        for row in rows:
            source_tag = f'creative:{row["id"]}'
            if _already_imported(ws_conn, source_tag):
                continue

            content_str = f"{row['title']}: {row['description'] or ''}".strip()
            ws_conn.execute('''
                INSERT INTO facts
                    (entity_id, attribute, value, value_type, timestamp, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                PLATFORM_ENTITY_ID,
                'content',
                json.dumps({
                    'content': content_str,
                    'platform': 'creative_engine',
                    'concept_type': row['concept_type'],
                    'novelty': row['novelty_score'],
                    'impact': row['estimated_impact'],
                }),
                'json',
                row['created_at'] or datetime.now().isoformat(),
                source_tag,
                float(row['novelty_score'] or 0.7),
            ))
            imported += 1

        ws_conn.commit()
    except Exception as e:
        logger.warning(f'memory_bridge: creative import failed: {e}')

    return imported


def bridge_world_state_events(ws_conn: sqlite3.Connection, limit: int = 100) -> int:
    """
    Convert world_state events into facts so detect_trends() can see them.
    Events are already in the DB but not in the facts table.
    """
    imported = 0
    try:
        # Fetch with row_factory so dict() works
        ws_conn.row_factory = sqlite3.Row
        raw_rows = ws_conn.execute('''
            SELECT id, event_type, actor_id, target_id, timestamp, platform, data
            FROM events
            WHERE data IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        rows = [dict(r) for r in raw_rows]
        ws_conn.row_factory = None  # Reset so inserts work normally

        for row in rows:
            source_tag = f'ws_event:{row["id"]}'
            if _already_imported(ws_conn, source_tag):
                continue

            try:
                event_data = json.loads(row['data']) if row['data'] else {}
                if not isinstance(event_data, dict):
                    event_data = {}
            except Exception:
                event_data = {}

            content_str = (
                event_data.get('content_preview') or
                event_data.get('content') or
                event_data.get('title') or
                event_data.get('message') or
                row['event_type']
            )
            entity_id = row['actor_id'] or PLATFORM_ENTITY_ID
            platform = row['platform'] or 'unknown'

            ws_conn.execute('''
                INSERT INTO facts
                    (entity_id, attribute, value, value_type, timestamp, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                'interaction',
                json.dumps({'content': str(content_str)[:300],
                            'platform': platform,
                            'event_type': row['event_type']}),
                'json',
                row['timestamp'] or datetime.now().isoformat(),
                source_tag,
                0.75,
            ))
            imported += 1

        ws_conn.commit()
    except Exception as e:
        logger.warning(f'memory_bridge: events import failed: {e}')

    return imported


def seed_metacognition_from_actions() -> None:
    """
    Update metacognition capability_assessments with real success rates
    derived from action_log.db so calibrate_confidence() returns accurate values.
    """
    if not ACTION_LOG_DB.exists() or not METACOGNITION_DB.exists():
        return

    try:
        with sqlite3.connect(ACTION_LOG_DB) as al_conn:
            al_conn.row_factory = sqlite3.Row
            rows = al_conn.execute('''
                SELECT action_type,
                       COUNT(*) as total,
                       SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes,
                       AVG(confidence) as avg_confidence
                FROM actions
                WHERE outcome IS NOT NULL
                GROUP BY action_type
            ''').fetchall()

        # Map action_type → metacognition capability
        action_to_capability = {
            'clawbr_like': 'social_interaction',
            'clawbr_comment': 'content_generation',
            'clawbr_post': 'content_generation',
            'moltx_post': 'content_generation',
            'moltx_reply': 'social_interaction',
            'moltx_like': 'social_interaction',
            'clawchess': 'planning',
            'research': 'data_analysis',
            'web_search': 'web_search',
        }

        cap_updates: Dict[str, List] = {}
        for row in rows:
            cap = action_to_capability.get(row['action_type'])
            if not cap:
                # Infer from action_type name
                at = row['action_type'].lower()
                if 'post' in at or 'comment' in at or 'reply' in at or 'write' in at:
                    cap = 'content_generation'
                elif 'like' in at or 'follow' in at or 'engage' in at:
                    cap = 'social_interaction'
                elif 'search' in at or 'research' in at:
                    cap = 'web_search'
                elif 'plan' in at or 'chess' in at:
                    cap = 'planning'
                else:
                    cap = 'data_analysis'

            success_rate = (row['successes'] or 0) / max(1, row['total'])
            avg_conf = row['avg_confidence'] or 0.5

            if cap not in cap_updates:
                cap_updates[cap] = []
            cap_updates[cap].append((success_rate, avg_conf, row['total']))

        with sqlite3.connect(METACOGNITION_DB) as meta_conn:
            for cap, data_points in cap_updates.items():
                # Weighted average by sample count
                total_samples = sum(d[2] for d in data_points)
                weighted_conf = sum(d[0] * d[2] for d in data_points) / max(1, total_samples)
                # Blend with avg_confidence from action log
                avg_action_conf = sum(d[1] * d[2] for d in data_points) / max(1, total_samples)
                final_confidence = weighted_conf * 0.6 + avg_action_conf * 0.4
                final_confidence = max(0.4, min(0.95, final_confidence))

                meta_conn.execute('''
                    UPDATE capability_assessments
                    SET confidence = ?,
                        can_perform = 1,
                        performance_history = ?,
                        last_tested = ?
                    WHERE capability = ?
                ''', (
                    final_confidence,
                    json.dumps([round(d[0], 3) for d in data_points]),
                    datetime.now().isoformat(),
                    cap,
                ))
            meta_conn.commit()

        logger.info(f'memory_bridge: seeded metacognition for {len(cap_updates)} capabilities')

    except Exception as e:
        logger.warning(f'memory_bridge: metacognition seeding failed: {e}')


def run_memory_bridge(force: bool = False) -> Dict:
    """
    Run the full memory bridge — idempotent, safe to call every AGI cycle.

    Returns a summary dict with counts of imported records.
    """
    if not WORLD_STATE_DB.exists():
        logger.warning('memory_bridge: world_state.db not found, skipping')
        return {}

    summary = {}
    try:
        with sqlite3.connect(WORLD_STATE_DB) as ws_conn:
            _ensure_platform_entity(ws_conn)

            n = bridge_alley_memory(ws_conn)
            summary['alley_memory'] = n

            n = bridge_action_log(ws_conn)
            summary['action_log'] = n

            n = bridge_creative_concepts(ws_conn)
            summary['creative'] = n

            n = bridge_world_state_events(ws_conn)
            summary['events'] = n

        seed_metacognition_from_actions()
        summary['metacognition_seeded'] = True

        total = sum(v for v in summary.values() if isinstance(v, int))
        if total > 0:
            logger.info(f'🔗 Memory bridge: imported {total} records → world_state.facts '
                        f'({summary})')
        else:
            logger.debug('memory_bridge: all records already imported (idempotent)')

    except Exception as e:
        logger.error(f'memory_bridge: run failed: {e}')
        summary['error'] = str(e)

    return summary
