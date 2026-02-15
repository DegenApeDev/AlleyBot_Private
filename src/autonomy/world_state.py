"""
World State Manager - Persistent environment model for AGI

Maintains coherent memory of entities, facts, relationships, and events
across sessions. Enables long-term reasoning and prediction.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Entity:
    """Represents something in the world (user, agent, post, topic, etc.)"""
    id: str
    type: str  # 'user', 'agent', 'post', 'topic', 'platform', 'conversation'
    name: Optional[str] = None
    display_name: Optional[str] = None
    platform: Optional[str] = None  # 'moltx', 'clawbr', 'telegram', etc.
    attributes: Optional[Dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    confidence: float = 1.0
    last_observed_at: Optional[str] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'display_name': self.display_name,
            'platform': self.platform,
            'attributes': json.dumps(self.attributes) if self.attributes else '{}',
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'confidence': self.confidence,
            'last_observed_at': self.last_observed_at
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Entity':
        attrs = row['attributes']
        return cls(
            id=row['id'],
            type=row['type'],
            name=row['name'],
            display_name=row['display_name'],
            platform=row['platform'] if 'platform' in row.keys() else None,
            attributes=json.loads(attrs) if attrs else {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            confidence=row['confidence'],
            last_observed_at=row['last_observed_at']
        )


@dataclass
class Fact:
    """Time-stamped assertion about an entity"""
    id: Optional[int] = None
    entity_id: Optional[str] = None
    attribute: Optional[str] = None
    value: Optional[str] = None
    value_type: str = 'string'  # 'string', 'int', 'float', 'bool', 'json'
    timestamp: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 1.0
    expires_at: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_id': self.entity_id,
            'attribute': self.attribute,
            'value': self.value,
            'value_type': self.value_type,
            'timestamp': self.timestamp,
            'source': self.source,
            'confidence': self.confidence,
            'expires_at': self.expires_at
        }

    def get_typed_value(self) -> Any:
        """Return value cast to appropriate type"""
        if self.value is None:
            return None
        try:
            if self.value_type == 'int':
                return int(self.value)
            elif self.value_type == 'float':
                return float(self.value)
            elif self.value_type == 'bool':
                return self.value.lower() == 'true'
            elif self.value_type == 'json':
                return json.loads(self.value)
            return self.value
        except:
            return self.value

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Fact':
        return cls(
            id=row['id'],
            entity_id=row['entity_id'],
            attribute=row['attribute'],
            value=row['value'],
            value_type=row['value_type'],
            timestamp=row['timestamp'],
            source=row['source'],
            confidence=row['confidence'],
            expires_at=row['expires_at']
        )


@dataclass
class Relationship:
    """Connection between two entities"""
    id: Optional[int] = None
    from_entity: Optional[str] = None
    to_entity: Optional[str] = None
    relation_type: Optional[str] = None  # 'follows', 'replied_to', 'debated_with', 'mentioned'
    strength: float = 0.5
    timestamp: Optional[str] = None
    context: Optional[Dict] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'from_entity': self.from_entity,
            'to_entity': self.to_entity,
            'relation_type': self.relation_type,
            'strength': self.strength,
            'timestamp': self.timestamp,
            'context': json.dumps(self.context) if self.context else None
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Relationship':
        ctx = row['context']
        return cls(
            id=row['id'],
            from_entity=row['from_entity'],
            to_entity=row['to_entity'],
            relation_type=row['relation_type'],
            strength=row['strength'],
            timestamp=row['timestamp'],
            context=json.loads(ctx) if ctx else None
        )


@dataclass
class Event:
    """Something that happened"""
    id: Optional[int] = None
    event_type: Optional[str] = None  # 'post_created', 'debate_joined', 'followed', 'mentioned'
    actor_id: Optional[str] = None
    target_id: Optional[str] = None
    timestamp: Optional[str] = None
    platform: Optional[str] = None
    data: Optional[Dict] = None
    processed: bool = False
    processed_at: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_type': self.event_type,
            'actor_id': self.actor_id,
            'target_id': self.target_id,
            'timestamp': self.timestamp,
            'platform': self.platform,
            'data': json.dumps(self.data) if self.data else None,
            'processed': self.processed,
            'processed_at': self.processed_at
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Event':
        data = row['data']
        return cls(
            id=row['id'],
            event_type=row['event_type'],
            actor_id=row['actor_id'],
            target_id=row['target_id'],
            timestamp=row['timestamp'],
            platform=row['platform'],
            data=json.loads(data) if data else None,
            processed=bool(row['processed']),
            processed_at=row['processed_at']
        )


class WorldStateManager:
    """
    Persistent world state for AGI - maintains coherent memory of environment
    
    Core components:
    - Entities: Objects in the world (users, agents, posts, topics)
    - Facts: Time-stamped assertions about entities
    - Relationships: Connections between entities
    - Events: Significant occurrences
    """

    def __init__(self, db_path: str = "data/world_state.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        print(f"🌍 World State Manager initialized ({self.db_path})")

    def _init_db(self):
        """Initialize SQLite schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT,
                    display_name TEXT,
                    attributes TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    last_observed_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    attribute TEXT NOT NULL,
                    value TEXT NOT NULL,
                    value_type TEXT DEFAULT 'string',
                    timestamp TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    expires_at TEXT,
                    FOREIGN KEY (entity_id) REFERENCES entities(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entity TEXT NOT NULL,
                    to_entity TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    FOREIGN KEY (from_entity) REFERENCES entities(id),
                    FOREIGN KEY (to_entity) REFERENCES entities(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor_id TEXT,
                    target_id TEXT,
                    timestamp TEXT NOT NULL,
                    platform TEXT,
                    data TEXT,
                    processed INTEGER DEFAULT 0,
                    processed_at TEXT,
                    FOREIGN KEY (actor_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                )
            """)

            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_facts_entity ON facts(entity_id, attribute, timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_facts_expires ON facts(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_from ON relationships(from_entity, relation_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_to ON relationships(to_entity, relation_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, processed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)")

            conn.commit()

    # =================================================================
    # Entity Operations
    # =================================================================

    def add_entity(self, entity: Entity) -> bool:
        """Add or update an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = entity.to_dict()
                conn.execute("""
                    INSERT OR REPLACE INTO entities 
                    (id, type, name, display_name, attributes, created_at, updated_at, confidence, last_observed_at)
                    VALUES 
                    (:id, :type, :name, :display_name, :attributes, :created_at, :updated_at, :confidence, :last_observed_at)
                """, data)
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to add entity: {e}")
            return False

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID with latest facts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            return Entity.from_row(row) if row else None

    def get_entity_with_facts(self, entity_id: str) -> Optional[Dict]:
        """Get entity with all its facts"""
        entity = self.get_entity(entity_id)
        if not entity:
            return None

        facts = self.get_facts(entity_id)

        return {
            'entity': entity,
            'facts': facts,
            'fact_count': len(facts)
        }

    def update_entity(self, entity_id: str, **kwargs) -> bool:
        """Update entity attributes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current entity
                entity = self.get_entity(entity_id)
                if not entity:
                    return False

                # Update fields
                for key, value in kwargs.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)

                entity.updated_at = datetime.now().isoformat()

                # Save
                data = entity.to_dict()
                conn.execute("""
                    UPDATE entities SET
                        type = :type,
                        name = :name,
                        display_name = :display_name,
                        attributes = :attributes,
                        updated_at = :updated_at,
                        confidence = :confidence,
                        last_observed_at = :last_observed_at
                    WHERE id = :id
                """, data)
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to update entity: {e}")
            return False

    def search_entities(self, query: str = None, entity_type: str = None, limit: int = 20) -> List[Entity]:
        """Search entities by name or type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            sql = "SELECT * FROM entities WHERE 1=1"
            params = []

            if query:
                sql += " AND (name LIKE ? OR display_name LIKE ? OR id LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

            if entity_type:
                sql += " AND type = ?"
                params.append(entity_type)

            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [Entity.from_row(row) for row in cursor.fetchall()]

    # =================================================================
    # Fact Operations
    # =================================================================

    def add_fact(self, fact: Fact) -> bool:
        """Record a fact about an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = fact.to_dict()
                conn.execute("""
                    INSERT INTO facts 
                    (entity_id, attribute, value, value_type, timestamp, source, confidence, expires_at)
                    VALUES 
                    (:entity_id, :attribute, :value, :value_type, :timestamp, :source, :confidence, :expires_at)
                """, data)
                conn.commit()

                # Update entity's last_observed_at
                conn.execute(
                    "UPDATE entities SET last_observed_at = ? WHERE id = ?",
                    (fact.timestamp, fact.entity_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to add fact: {e}")
            return False

    def get_facts(self, entity_id: str, attribute: str = None, since: str = None, limit: int = 100) -> List[Fact]:
        """Get facts about an entity, optionally filtered by attribute and time"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            sql = "SELECT * FROM facts WHERE entity_id = ?"
            params = [entity_id]

            if attribute:
                sql += " AND attribute = ?"
                params.append(attribute)

            if since:
                sql += " AND timestamp > ?"
                params.append(since)

            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [Fact.from_row(row) for row in cursor.fetchall()]

    def get_latest_fact(self, entity_id: str, attribute: str) -> Optional[Fact]:
        """Get most recent fact for an attribute"""
        facts = self.get_facts(entity_id, attribute, limit=1)
        return facts[0] if facts else None

    def get_fact_value(self, entity_id: str, attribute: str, default=None) -> Any:
        """Get typed value of latest fact"""
        fact = self.get_latest_fact(entity_id, attribute)
        return fact.get_typed_value() if fact else default

    # =================================================================
    # Relationship Operations
    # =================================================================

    def add_relationship(self, relationship: Relationship) -> bool:
        """Record a relationship between entities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if relationship already exists
                cursor = conn.execute(
                    """SELECT id FROM relationships 
                       WHERE from_entity = ? AND to_entity = ? AND relation_type = ?""",
                    (relationship.from_entity, relationship.to_entity, relationship.relation_type)
                )
                existing = cursor.fetchone()

                data = relationship.to_dict()

                if existing:
                    # Update existing relationship
                    data['id'] = existing['id']
                    conn.execute(
                        "UPDATE relationships SET strength = ?, timestamp = ?, context = ? WHERE id = ?",
                        (data['strength'], data['timestamp'], data['context'], existing['id'])
                    )
                else:
                    # Create new relationship
                    conn.execute("""
                        INSERT INTO relationships 
                        (from_entity, to_entity, relation_type, strength, timestamp, context)
                        VALUES 
                        (:from_entity, :to_entity, :relation_type, :strength, :timestamp, :context)
                    """, data)

                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to add relationship: {e}")
            return False

    def get_relationships(self, entity_id: str, relation_type: str = None, direction: str = 'both') -> List[Relationship]:
        """
        Get relationships for an entity
        direction: 'outgoing' (from entity), 'incoming' (to entity), 'both'
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            relationships = []

            if direction in ('outgoing', 'both'):
                sql = "SELECT * FROM relationships WHERE from_entity = ?"
                params = [entity_id]
                if relation_type:
                    sql += " AND relation_type = ?"
                    params.append(relation_type)
                sql += " ORDER BY timestamp DESC"

                cursor = conn.execute(sql, params)
                relationships.extend([Relationship.from_row(row) for row in cursor.fetchall()])

            if direction in ('incoming', 'both'):
                sql = "SELECT * FROM relationships WHERE to_entity = ?"
                params = [entity_id]
                if relation_type:
                    sql += " AND relation_type = ?"
                    params.append(relation_type)
                sql += " ORDER BY timestamp DESC"

                cursor = conn.execute(sql, params)
                relationships.extend([Relationship.from_row(row) for row in cursor.fetchall()])

            return relationships

    def get_related_entities(self, entity_id: str, relation_type: str = None, min_strength: float = 0.0) -> List[str]:
        """Get IDs of entities related to given entity"""
        relationships = self.get_relationships(entity_id, relation_type, 'both')
        related = set()
        for rel in relationships:
            if rel.strength >= min_strength:
                if rel.from_entity == entity_id:
                    related.add(rel.to_entity)
                else:
                    related.add(rel.from_entity)
        return list(related)

    # =================================================================
    # Event Operations
    # =================================================================

    def add_event(self, event: Event) -> bool:
        """Log an event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = event.to_dict()
                conn.execute("""
                    INSERT INTO events 
                    (event_type, actor_id, target_id, timestamp, platform, data, processed, processed_at)
                    VALUES 
                    (:event_type, :actor_id, :target_id, :timestamp, :platform, :data, :processed, :processed_at)
                """, data)
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to add event: {e}")
            return False

    def get_events(self, event_type: str = None, unprocessed_only: bool = False, since: str = None, limit: int = 100) -> List[Event]:
        """Get events, optionally filtered"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            sql = "SELECT * FROM events WHERE 1=1"
            params = []

            if event_type:
                sql += " AND event_type = ?"
                params.append(event_type)

            if unprocessed_only:
                sql += " AND processed = 0"

            if since:
                sql += " AND timestamp > ?"
                params.append(since)

            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [Event.from_row(row) for row in cursor.fetchall()]

    def mark_event_processed(self, event_id: int) -> bool:
        """Mark an event as processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE events SET processed = 1, processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), event_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to mark event processed: {e}")
            return False

    # =================================================================
    # Maintenance Operations
    # =================================================================

    def cleanup_expired_facts(self) -> int:
        """Delete expired facts, return count deleted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now().isoformat()
                cursor = conn.execute(
                    "DELETE FROM facts WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (now,)
                )
                conn.commit()
                count = cursor.rowcount
                if count > 0:
                    print(f"🧹 Cleaned up {count} expired facts")
                return count
        except Exception as e:
            print(f"❌ Failed to cleanup facts: {e}")
            return 0

    def get_stats(self) -> Dict[str, int]:
        """Get world state statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM entities")
            entity_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM facts")
            fact_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM relationships")
            relationship_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM events WHERE processed = 0")
            unprocessed_events = cursor.fetchone()[0]

            return {
                'entities': entity_count,
                'facts': fact_count,
                'relationships': relationship_count,
                'events': event_count,
                'unprocessed_events': unprocessed_events
            }

    def get_entity_type_breakdown(self) -> Dict[str, int]:
        """Get count of entities by type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT type, COUNT(*) FROM entities GROUP BY type")
            return dict(cursor.fetchall())


# Convenience factory
def create_world_state_manager(core=None) -> WorldStateManager:
    """Factory to create WorldStateManager with appropriate path"""
    if core and hasattr(core, 'data_dir'):
        db_path = Path(core.data_dir) / "world_state.db"
    else:
        db_path = "data/world_state.db"
    return WorldStateManager(str(db_path))


# Singleton instance
_world_state_manager_instance: Optional[WorldStateManager] = None


def get_world_state_manager(core=None) -> WorldStateManager:
    """Get or create WorldStateManager singleton"""
    global _world_state_manager_instance
    if _world_state_manager_instance is None:
        _world_state_manager_instance = create_world_state_manager(core)
    return _world_state_manager_instance
