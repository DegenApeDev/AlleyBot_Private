"""
SQLite Memory System for AlleyBot
Replaces JSON files with SQLite for better performance, querying, and scalability.
"""
import sqlite3
import json
import pickle
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
import uuid

# Optional imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available, vector search disabled")

# Optional imports for enhanced features
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False


@dataclass
class Memory:
    """Individual memory entry"""
    id: str
    content: str
    memory_type: str  # interaction, learning, goal, on_chain_event
    timestamp: datetime
    metadata: Dict[str, Any]
    relevance_score: float = 1.0
    embedding: Optional[List[float]] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': json.dumps(self.metadata),
            'relevance_score': self.relevance_score,
            'embedding': json.dumps(self.embedding) if self.embedding else None
        }


@dataclass  
class Goal:
    """Hierarchical goal structure"""
    id: str
    description: str
    goal_type: str  # short_term, long_term, milestone
    parent_goal_id: Optional[str] = None
    sub_goals: List[str] = None
    status: str = 'active'  # active, completed, failed, paused
    priority: int = 1
    created: datetime = None
    completed: Optional[datetime] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sub_goals is None:
            self.sub_goals = []
        if self.created is None:
            self.created = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'goal_type': self.goal_type,
            'parent_goal_id': self.parent_goal_id,
            'sub_goals': json.dumps(self.sub_goals),
            'status': self.status,
            'priority': self.priority,
            'created': self.created.isoformat(),
            'completed': self.completed.isoformat() if self.completed else None,
            'progress': self.progress,
            'metadata': json.dumps(self.metadata)
        }


class SQLiteMemorySystem:
    """
    Unified SQLite-based memory system replacing JSON files.
    Provides ACID transactions, indexed queries, and scalability.
    """
    
    def __init__(self, db_path: str = 'data/memory.db', embedding_model: str = 'all-MiniLM-L6-v2'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._embedding_model = None
        
        # Initialize embedding model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                from src.utils.embedding_model import get_sentence_transformer
                self._embedding_model = get_sentence_transformer(embedding_model)
            except Exception as e:
                print(f"⚠️ Failed to load embedding model: {e}")
        
        # Initialize database
        self._init_database()
        
        print(f"💾 SQLite memory system initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get thread-local connection with proper row factory"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
        finally:
            # Commit changes if no exception occurred
            if self._local.connection:
                try:
                    self._local.connection.commit()
                except Exception as e:
                    logger.debug("Non-critical error: %s", e)
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Key-value store (replaces JSON files)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_value_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    value_type TEXT DEFAULT 'json',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Memories with semantic search support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    relevance_score REAL DEFAULT 1.0,
                    embedding TEXT,  -- JSON array of floats
                    search_vector BLOB  -- Binary for efficient similarity search
                )
            ''')
            
            # Create indexes for common queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_relevance ON memories(relevance_score DESC)
            ''')
            
            # Goals with hierarchical structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    goal_type TEXT NOT NULL,
                    parent_goal_id TEXT,
                    sub_goals TEXT,  -- JSON array
                    status TEXT DEFAULT 'active',
                    priority INTEGER DEFAULT 1,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed TIMESTAMP,
                    progress REAL DEFAULT 0.0,
                    metadata TEXT,
                    FOREIGN KEY (parent_goal_id) REFERENCES goals(id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_goals_type ON goals(goal_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_goal_id)
            ''')
            
            # Encrypted sensitive storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secure_storage (
                    key TEXT PRIMARY KEY,
                    encrypted_value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    # =========================================================================
    # Key-Value Store (replaces JSON files)
    # =========================================================================
    
    def get_memory(self, key: str, default=None) -> Any:
        """Get value from key-value store (backward compatible with old JSON)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value, value_type FROM key_value_store WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return default
            
            value, value_type = row['value'], row['value_type']
            
            if value_type == 'json':
                return json.loads(value)
            elif value_type == 'pickle':
                return pickle.loads(value.encode())
            else:
                return value
    
    def save_memory(self, key: str, value: Any) -> None:
        """Save value to key-value store (backward compatible)"""
        # Determine value type and serialize
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value)
            value_type = 'json'
        elif isinstance(value, str):
            serialized = value
            value_type = 'string'
        else:
            # Fallback to pickle for complex objects
            serialized = pickle.dumps(value).decode('latin1')
            value_type = 'pickle'
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO key_value_store (key, value, value_type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    value_type = excluded.value_type,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, serialized, value_type))
            conn.commit()
    
    def delete_memory(self, key: str) -> bool:
        """Delete a key from the store"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM key_value_store WHERE key = ?', (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def list_keys(self, prefix: str = None) -> List[str]:
        """List all keys, optionally filtered by prefix"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if prefix:
                cursor.execute(
                    "SELECT key FROM key_value_store WHERE key LIKE ?",
                    (f"{prefix}%",)
                )
            else:
                cursor.execute('SELECT key FROM key_value_store')
            return [row['key'] for row in cursor.fetchall()]
    
    # =========================================================================
    # Semantic Memory (with embeddings)
    # =========================================================================
    
    def add_memory(self, content: str, memory_type: str = 'interaction', 
                   metadata: Dict = None) -> str:
        """Add a memory with optional embedding for semantic search"""
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Generate embedding if model available
        embedding = None
        search_vector = None
        if self._embedding_model and content:
            try:
                embedding = self._embedding_model.encode([content])[0].tolist()
                search_vector = np.array(embedding, dtype=np.float32).tobytes()
            except Exception as e:
                print(f"⚠️ Failed to generate embedding: {e}")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memories (id, content, memory_type, timestamp, 
                                    metadata, embedding, search_vector)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                content,
                memory_type,
                timestamp.isoformat(),
                json.dumps(metadata or {}),
                json.dumps(embedding) if embedding else None,
                search_vector
            ))
            conn.commit()
        
        return memory_id
    
    def search_memories(self, query: str = None, memory_type: str = None,
                        k: int = 5, min_relevance: float = 0.0) -> List[Dict]:
        """Search memories by semantic similarity or filter by type"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # If query provided and embeddings available, do semantic search
            if query and self._embedding_model:
                try:
                    query_embedding = self._embedding_model.encode([query])[0]
                    
                    # Get all memories of specified type
                    if memory_type:
                        cursor.execute(
                            'SELECT * FROM memories WHERE memory_type = ?',
                            (memory_type,)
                        )
                    else:
                        cursor.execute('SELECT * FROM memories')
                    
                    memories = []
                    for row in cursor.fetchall():
                        if row['search_vector']:
                            mem_vector = np.frombuffer(row['search_vector'], dtype=np.float32)
                            similarity = np.dot(query_embedding, mem_vector) / (
                                np.linalg.norm(query_embedding) * np.linalg.norm(mem_vector)
                            )
                            if similarity >= min_relevance:
                                memories.append({
                                    'id': row['id'],
                                    'content': row['content'],
                                    'memory_type': row['memory_type'],
                                    'timestamp': row['timestamp'],
                                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                                    'relevance_score': float(similarity),
                                    'embedding': json.loads(row['embedding']) if row['embedding'] else None
                                })
                    
                    # Sort by similarity and return top k
                    memories.sort(key=lambda x: x['relevance_score'], reverse=True)
                    return memories[:k]
                    
                except Exception as e:
                    print(f"⚠️ Semantic search failed: {e}, falling back to text search")
            
            # Fallback: text-based search or simple filter
            if memory_type:
                cursor.execute(
                    '''SELECT * FROM memories 
                       WHERE memory_type = ? 
                       ORDER BY relevance_score DESC, timestamp DESC 
                       LIMIT ?''',
                    (memory_type, k)
                )
            else:
                cursor.execute(
                    '''SELECT * FROM memories 
                       ORDER BY relevance_score DESC, timestamp DESC 
                       LIMIT ?''',
                    (k,)
                )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'memory_type': row['memory_type'],
                    'timestamp': row['timestamp'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'relevance_score': row['relevance_score'],
                    'embedding': json.loads(row['embedding']) if row['embedding'] else None
                })
            
            return results
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return {
                'id': row['id'],
                'content': row['content'],
                'memory_type': row['memory_type'],
                'timestamp': row['timestamp'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'relevance_score': row['relevance_score'],
                'embedding': json.loads(row['embedding']) if row['embedding'] else None
            }
    
    def update_memory_relevance(self, memory_id: str, relevance_score: float) -> bool:
        """Update the relevance score of a memory"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE memories SET relevance_score = ? WHERE id = ?',
                (relevance_score, memory_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_memory_by_id(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # =========================================================================
    # Goals (Hierarchical)
    # =========================================================================
    
    def add_goal(self, description: str, goal_type: str = 'short_term',
                 parent_goal_id: str = None, priority: int = 1,
                 metadata: Dict = None) -> str:
        """Add a hierarchical goal"""
        goal_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO goals (id, description, goal_type, parent_goal_id,
                                 priority, metadata, sub_goals, status, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 0.0)
            ''', (
                goal_id,
                description,
                goal_type,
                parent_goal_id,
                priority,
                json.dumps(metadata or {}),
                json.dumps([])
            ))
            conn.commit()
        
        return goal_id
    
    def get_active_goals(self, goal_type: str = None) -> List[Dict]:
        """Get all active goals, optionally filtered by type"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if goal_type:
                cursor.execute('''
                    SELECT * FROM goals 
                    WHERE status = 'active' AND goal_type = ?
                    ORDER BY priority DESC, created ASC
                ''', (goal_type,))
            else:
                cursor.execute('''
                    SELECT * FROM goals 
                    WHERE status = 'active'
                    ORDER BY priority DESC, created ASC
                ''')
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'description': row['description'],
                    'goal_type': row['goal_type'],
                    'parent_goal_id': row['parent_goal_id'],
                    'sub_goals': json.loads(row['sub_goals']) if row['sub_goals'] else [],
                    'status': row['status'],
                    'priority': row['priority'],
                    'created': row['created'],
                    'completed': row['completed'],
                    'progress': row['progress'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                })
            
            return results
    
    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """Update goal progress (0.0 to 1.0)"""
        status = 'completed' if progress >= 1.0 else 'active'
        completed = datetime.now().isoformat() if progress >= 1.0 else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE goals 
                SET progress = ?, status = ?, completed = ?
                WHERE id = ?
            ''', (progress, status, completed, goal_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_sub_goal(self, parent_goal_id: str, sub_goal_id: str) -> bool:
        """Add a sub-goal to a parent goal"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current sub_goals
            cursor.execute('SELECT sub_goals FROM goals WHERE id = ?', (parent_goal_id,))
            row = cursor.fetchone()
            
            if row is None:
                return False
            
            sub_goals = json.loads(row['sub_goals']) if row['sub_goals'] else []
            sub_goals.append(sub_goal_id)
            
            cursor.execute(
                'UPDATE goals SET sub_goals = ? WHERE id = ?',
                (json.dumps(sub_goals), parent_goal_id)
            )
            conn.commit()
            return True
    
    # =========================================================================
    # Secure Storage (Encrypted)
    # =========================================================================
    
    def store_sensitive(self, key: str, value: Any) -> None:
        """Store encrypted sensitive data"""
        if not ENCRYPTION_AVAILABLE:
            raise RuntimeError("Encryption not available. Install: pip install cryptography")
        
        # Initialize cipher if needed
        if not hasattr(self, '_cipher'):
            self._init_encryption()
        
        # Serialize and encrypt
        json_str = json.dumps(value)
        encrypted = self._cipher.encrypt(json_str.encode())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO secure_storage (key, encrypted_value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    encrypted_value = excluded.encrypted_value,
                    created_at = CURRENT_TIMESTAMP
            ''', (key, encrypted))
            conn.commit()
    
    def get_sensitive(self, key: str) -> Optional[Any]:
        """Retrieve and decrypt sensitive data"""
        if not ENCRYPTION_AVAILABLE:
            raise RuntimeError("Encryption not available")
        
        if not hasattr(self, '_cipher'):
            self._init_encryption()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT encrypted_value FROM secure_storage WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Decrypt
            decrypted = self._cipher.decrypt(row['encrypted_value'])
            return json.loads(decrypted.decode())
    
    def _init_encryption(self):
        """Initialize encryption key"""
        key_file = Path('.memory_key')
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            key_file.chmod(0o600)
        
        self._cipher = Fernet(key)
    
    # =========================================================================
    # Migration from JSON
    # =========================================================================
    
    def migrate_from_json(self, memory_dir: str = 'memory') -> Dict[str, int]:
        """Migrate existing JSON memory files to SQLite"""
        memory_path = Path(memory_dir)
        stats = {'files_migrated': 0, 'records_migrated': 0, 'errors': 0}
        
        if not memory_path.exists():
            return stats
        
        print(f"🔄 Migrating JSON memory files from {memory_path}...")
        
        for json_file in memory_path.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                key = json_file.stem
                self.save_memory(key, data)
                
                stats['files_migrated'] += 1
                
                # Count nested records if dict
                if isinstance(data, dict):
                    stats['records_migrated'] += len(data)
                elif isinstance(data, list):
                    stats['records_migrated'] += len(data)
                
                print(f"  ✓ Migrated {key}")
                
            except Exception as e:
                print(f"  ✗ Failed to migrate {json_file}: {e}")
                stats['errors'] += 1
        
        print(f"📊 Migration complete: {stats['files_migrated']} files, "
              f"{stats['records_migrated']} records")
        
        return stats
    
    # =========================================================================
    # Stats & Maintenance
    # =========================================================================
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count key-value entries
            cursor.execute('SELECT COUNT(*) as count FROM key_value_store')
            kv_count = cursor.fetchone()['count']
            
            # Count memories by type
            cursor.execute('''
                SELECT memory_type, COUNT(*) as count 
                FROM memories 
                GROUP BY memory_type
            ''')
            memory_types = {row['memory_type']: row['count'] for row in cursor.fetchall()}
            
            # Count goals
            cursor.execute('SELECT COUNT(*) as count FROM goals')
            goal_count = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM goals 
                GROUP BY status
            ''')
            goal_statuses = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Count secure storage entries
            cursor.execute('SELECT COUNT(*) as count FROM secure_storage')
            secure_count = cursor.fetchone()['count']
            
            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                'key_value_store': {
                    'entries': kv_count
                },
                'memories': {
                    'total': sum(memory_types.values()),
                    'by_type': memory_types
                },
                'goals': {
                    'total': goal_count,
                    'by_status': goal_statuses
                },
                'secure_storage': {
                    'entries': secure_count
                },
                'database': {
                    'path': str(self.db_path),
                    'size_bytes': db_size,
                    'size_mb': round(db_size / (1024 * 1024), 2)
                }
            }
    
    def prune_old_memories(self, days: int = 30, memory_type: str = None) -> int:
        """Prune memories older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if memory_type:
                cursor.execute('''
                    DELETE FROM memories 
                    WHERE timestamp < ? AND memory_type = ?
                ''', (cutoff.isoformat(), memory_type))
            else:
                cursor.execute(
                    'DELETE FROM memories WHERE timestamp < ?',
                    (cutoff.isoformat(),)
                )
            
            conn.commit()
            deleted = cursor.rowcount
            print(f"🧹 Pruned {deleted} old memories")
            return deleted
    
    def vacuum(self):
        """Optimize database (reclaim space)"""
        with self._get_connection() as conn:
            conn.execute('VACUUM')
            print("💾 Database vacuumed and optimized")
    
    def close(self):
        """Close database connections"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
