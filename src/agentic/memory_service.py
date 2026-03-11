"""
Memory Service - Unified memory interface for AlleyBot

This service provides clean read/write contracts for all memory operations.
It consolidates scattered memory logic into one coherent interface.

Types of memory:
- Episodic: Action outcomes, events, experiences
- Semantic: Facts, knowledge, learned information
- Conversational: Chat history with users
- Work: Work item context, progress, decisions

This replaces scattered memory access across plugins.
"""

import json
import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory storage."""
    EPISODIC = "episodic"      # Action outcomes, events
    SEMANTIC = "semantic"      # Facts, knowledge
    CONVERSATIONAL = "conversation"  # Chat history
    WORK = "work"              # Work item context
    REFLECTION = "reflection"  # Learning insights


@dataclass
class MemoryRecord:
    """Canonical memory record."""
    id: str
    timestamp: str
    memory_type: MemoryType
    content: str
    
    # Source context
    source_action: Optional[str] = None
    source_work_item: Optional[str] = None
    source_plugin: Optional[str] = None
    
    # Relevance for retrieval
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0  # 0.0-1.0
    
    # For semantic search
    embedding: Optional[List[float]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "source_action": self.source_action,
            "source_work_item": self.source_work_item,
            "source_plugin": self.source_plugin,
            "tags": self.tags,
            "importance": self.importance,
            "metadata": self.metadata,
        }


class MemoryService:
    """
    Unified memory interface for AlleyBot.
    
    Provides clean read/write contracts for:
    - Storing experiences and outcomes
    - Retrieving relevant context
    - Semantic search (if embeddings available)
    - Conversation history
    - Work item context
    
    Usage:
        memory = get_memory_service()
        
        # Store an experience
        memory.store_episodic(
            content="Successfully posted market analysis",
            source_action="moltx:post",
            importance=0.8
        )
        
        # Retrieve relevant context
        results = memory.retrieve_relevant(
            query="market analysis",
            memory_type=MemoryType.EPISODIC,
            k=5
        )
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        """
        Initialize memory service.
        
        Args:
            db_path: SQLite database for memory storage
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # In-memory cache for recent memories
        self._recent_cache: List[MemoryRecord] = []
        self._cache_size = 100
        
        print(f"✅ Memory Service initialized - DB: {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialize SQLite schema with migration support."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if table exists and get current schema
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='memories'"
            )
            existing = cursor.fetchone()
            
            if existing:
                # Table exists - check if we need to migrate
                # For now, simple approach: if source_action column missing, recreate
                try:
                    conn.execute("SELECT source_action FROM memories LIMIT 1")
                except sqlite3.OperationalError:
                    # Column missing - need to recreate
                    print("🔄 Migrating memory database schema...")
                    conn.execute("DROP TABLE memories")
                    conn.execute("DROP TABLE IF EXISTS idx_type")
                    conn.execute("DROP TABLE IF EXISTS idx_timestamp")
                    existing = None
            
            if not existing:
                # Create table
                conn.execute("""
                    CREATE TABLE memories (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_action TEXT,
                        source_work_item TEXT,
                        source_plugin TEXT,
                        tags TEXT,
                        importance REAL DEFAULT 1.0,
                        embedding TEXT,
                        metadata TEXT
                    )
                """)
            
            # Create indexes (ignore errors if they already exist)
            for idx_name, idx_sql in [
                ("idx_type", "CREATE INDEX idx_type ON memories(memory_type)"),
                ("idx_timestamp", "CREATE INDEX idx_timestamp ON memories(timestamp)"),
                ("idx_action", "CREATE INDEX idx_action ON memories(source_action)"),
                ("idx_work", "CREATE INDEX idx_work ON memories(source_work_item)"),
            ]:
                try:
                    conn.execute(idx_sql)
                except sqlite3.OperationalError:
                    pass  # Index already exists or column missing
            
            conn.commit()
    
    def _row_to_record(self, row: tuple) -> MemoryRecord:
        """Convert DB row to MemoryRecord."""
        (
            id_, timestamp, mem_type, content, source_action,
            source_work_item, source_plugin, tags, importance,
            embedding, metadata
        ) = row
        
        return MemoryRecord(
            id=id_,
            timestamp=timestamp,
            memory_type=MemoryType(mem_type),
            content=content,
            source_action=source_action,
            source_work_item=source_work_item,
            source_plugin=source_plugin,
            tags=json.loads(tags) if tags else [],
            importance=importance or 1.0,
            embedding=json.loads(embedding) if embedding else None,
            metadata=json.loads(metadata) if metadata else {},
        )
    
    def _record_to_row(self, record: MemoryRecord) -> tuple:
        """Convert MemoryRecord to DB row."""
        return (
            record.id,
            record.timestamp,
            record.memory_type.value,
            record.content,
            record.source_action,
            record.source_work_item,
            record.source_plugin,
            json.dumps(record.tags) if record.tags else None,
            record.importance,
            json.dumps(record.embedding) if record.embedding else None,
            json.dumps(record.metadata) if record.metadata else None,
        )
    
    # ------------------------------------------------------------------
    # Store Methods
    # ------------------------------------------------------------------
    
    def store(
        self,
        content: str,
        memory_type: MemoryType,
        source_action: Optional[str] = None,
        source_work_item: Optional[str] = None,
        source_plugin: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """
        Store a memory record.
        
        Args:
            content: The memory content
            memory_type: Type of memory
            source_action: Associated action ID
            source_work_item: Associated work item ID
            source_plugin: Source plugin name
            tags: Search tags
            importance: 0.0-1.0 importance score
            metadata: Additional structured data
            
        Returns:
            Stored MemoryRecord
        """
        import uuid
        
        record = MemoryRecord(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now().isoformat(),
            memory_type=memory_type,
            content=content,
            source_action=source_action,
            source_work_item=source_work_item,
            source_plugin=source_plugin,
            tags=tags or [],
            importance=importance,
            metadata=metadata or {},
        )
        
        # Persist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                self._record_to_row(record)
            )
            conn.commit()
        
        # Cache
        self._recent_cache.append(record)
        if len(self._recent_cache) > self._cache_size:
            self._recent_cache.pop(0)
        
        return record
    
    def store_episodic(
        self,
        content: str,
        source_action: Optional[str] = None,
        importance: float = 1.0,
        **kwargs
    ) -> MemoryRecord:
        """Convenience method for episodic memories."""
        return self.store(
            content=content,
            memory_type=MemoryType.EPISODIC,
            source_action=source_action,
            importance=importance,
            **kwargs
        )
    
    def store_semantic(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        **kwargs
    ) -> MemoryRecord:
        """Convenience method for semantic memories."""
        return self.store(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            tags=tags,
            importance=importance,
            **kwargs
        )
    
    def store_conversation(
        self,
        content: str,
        source_plugin: str,
        platform: str = "telegram",
        user_id: Optional[str] = None,
        **kwargs
    ) -> MemoryRecord:
        """Convenience method for conversation memories."""
        metadata = kwargs.pop("metadata", {})
        metadata.update({"platform": platform, "user_id": user_id})
        
        return self.store(
            content=content,
            memory_type=MemoryType.CONVERSATIONAL,
            source_plugin=source_plugin,
            metadata=metadata,
            **kwargs
        )
    
    def store_work_context(
        self,
        content: str,
        source_work_item: str,
        importance: float = 1.0,
        **kwargs
    ) -> MemoryRecord:
        """Convenience method for work item context."""
        return self.store(
            content=content,
            memory_type=MemoryType.WORK,
            source_work_item=source_work_item,
            importance=importance,
            **kwargs
        )
    
    # ------------------------------------------------------------------
    # Retrieve Methods
    # ------------------------------------------------------------------
    
    def retrieve_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> List[MemoryRecord]:
        """
        Retrieve memories by type.
        
        Args:
            memory_type: Type of memory to retrieve
            limit: Maximum number of records
            since: ISO timestamp - only get records after this time
            
        Returns:
            List of MemoryRecords, sorted by timestamp desc
        """
        with sqlite3.connect(self.db_path) as conn:
            if since:
                rows = conn.execute(
                    """SELECT * FROM memories 
                    WHERE memory_type = ? AND timestamp > ?
                    ORDER BY timestamp DESC LIMIT ?""",
                    (memory_type.value, since, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM memories 
                    WHERE memory_type = ?
                    ORDER BY timestamp DESC LIMIT ?""",
                    (memory_type.value, limit)
                ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def retrieve_relevant(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        k: int = 5,
    ) -> List[MemoryRecord]:
        """
        Retrieve memories relevant to a query.
        
        Currently uses simple substring matching.
        Future: semantic search with embeddings.
        
        Args:
            query: Search query
            memory_type: Optional type filter
            k: Number of results
            
        Returns:
            List of relevant MemoryRecords
        """
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Build SQL
        if memory_type:
            sql = "SELECT * FROM memories WHERE memory_type = ?"
            params = [memory_type.value]
        else:
            sql = "SELECT * FROM memories WHERE 1=1"
            params = []
        
        # Search in content and tags
        sql += " AND ("
        sql += " OR ".join(["LOWER(content) LIKE ?"] * len(query_terms))
        sql += ")"
        params.extend([f"%{term}%" for term in query_terms])
        
        sql += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(k * 2)  # Get more for ranking
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
        
        records = [self._row_to_record(row) for row in rows]
        
        # Simple ranking: count matching terms
        def score_record(record: MemoryRecord) -> float:
            content_lower = record.content.lower()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            tag_matches = sum(1 for term in query_terms if any(term in tag.lower() for tag in record.tags))
            return (term_matches + tag_matches * 2) * record.importance
        
        records.sort(key=score_record, reverse=True)
        return records[:k]
    
    def retrieve_by_work_item(
        self,
        work_item_id: str,
        limit: int = 20,
    ) -> List[MemoryRecord]:
        """Retrieve all memories associated with a work item."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM memories 
                WHERE source_work_item = ?
                ORDER BY timestamp DESC LIMIT ?""",
                (work_item_id, limit)
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def retrieve_by_action(
        self,
        action_id: str,
        limit: int = 20,
    ) -> List[MemoryRecord]:
        """Retrieve all memories associated with an action."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM memories 
                WHERE source_action = ?
                ORDER BY timestamp DESC LIMIT ?""",
                (action_id, limit)
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def get_recent(
        self,
        minutes: int = 60,
        memory_type: Optional[MemoryType] = None,
    ) -> List[MemoryRecord]:
        """Get recent memories from the last N minutes."""
        from datetime import timedelta
        since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        if memory_type:
            return self.retrieve_by_type(memory_type, since=since, limit=100)
        
        # Get all types
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM memories 
                WHERE timestamp > ?
                ORDER BY timestamp DESC""",
                (since,)
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    # ------------------------------------------------------------------
    # Summary Methods
    # ------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            
            by_type = conn.execute(
                "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type"
            ).fetchall()
            
            recent_24h = conn.execute(
                """SELECT COUNT(*) FROM memories 
                WHERE timestamp > datetime('now', '-1 day')"""
            ).fetchone()[0]
        
        return {
            "total_records": total,
            "by_type": {t: c for t, c in by_type},
            "recent_24h": recent_24h,
            "cache_size": len(self._recent_cache),
        }
    
    def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
    ) -> List[MemoryRecord]:
        """
        Full-text search across memories.
        
        Args:
            query: Search query
            memory_types: Optional list of types to search
            limit: Maximum results
            
        Returns:
            Matching MemoryRecords
        """
        query_lower = query.lower()
        terms = query_lower.split()
        
        # Build SQL
        params = []
        conditions = []
        
        # Type filter
        if memory_types:
            placeholders = ",".join(["?"] * len(memory_types))
            conditions.append(f"memory_type IN ({placeholders})")
            params.extend([t.value for t in memory_types])
        
        # Content search
        if terms:
            term_conditions = []
            for term in terms:
                term_conditions.append("LOWER(content) LIKE ?")
                params.append(f"%{term}%")
            conditions.append(f"({' OR '.join(term_conditions)})")
        
        sql = "SELECT * FROM memories"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_record(row) for row in rows]


# Singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service(db_path: str = "data/memory.db") -> MemoryService:
    """Get or create memory service singleton."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(db_path)
    return _memory_service


def reset_memory_service() -> None:
    """Reset singleton."""
    global _memory_service
    _memory_service = None
