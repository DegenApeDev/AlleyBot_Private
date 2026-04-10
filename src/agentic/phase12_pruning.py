"""
Phase 12.5: Semantic Memory Pruning
Auto-cleanup old low-value memories with configurable policies
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sqlite3


class MemoryPruningPolicy:
    """Configuration for memory pruning behavior"""
    
    def __init__(self,
                 max_age_days: int = 30,
                 min_relevance_score: float = 0.3,
                 preserve_types: List[str] = None,
                 preserve_goals: bool = True,
                 preserve_learning: bool = True,
                 max_memories_per_type: int = 1000):
        self.max_age_days = max_age_days
        self.min_relevance_score = min_relevance_score
        self.preserve_types = preserve_types or ['goal', 'learning', 'on_chain_event']
        self.preserve_goals = preserve_goals
        self.preserve_learning = preserve_learning
        self.max_memories_per_type = max_memories_per_type


class MemoryPruner:
    """
    Intelligent memory pruning system
    Removes low-value memories while preserving important ones
    """
    
    def __init__(self, policy: MemoryPruningPolicy = None):
        self.policy = policy or MemoryPruningPolicy()
        self.pruning_log: List[Dict] = []
    
    def should_keep_memory(self, memory: Dict) -> Tuple[bool, str]:
        """
        Determine if a memory should be kept
        Returns (keep: bool, reason: str)
        """
        # Parse timestamp
        try:
            timestamp_str = memory.get('timestamp') or memory.get('created_at')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse timestamp: {e}")
            timestamp = datetime.now()
        
        age_days = (datetime.now() - timestamp).days
        
        # Check memory type
        mem_type = memory.get('memory_type', 'unknown')
        
        # Always preserve certain types
        if mem_type in self.policy.preserve_types:
            return True, f"Preserved type: {mem_type}"
        
        # Check age
        if age_days > self.policy.max_age_days:
            # Even old memories can be kept if highly relevant
            relevance = memory.get('relevance_score', 0.5)
            if relevance < self.policy.min_relevance_score:
                return False, f"Too old ({age_days} days) and low relevance ({relevance:.2f})"
        
        # Check relevance score
        relevance = memory.get('relevance_score', 0.5)
        if relevance < self.policy.min_relevance_score and age_days > 7:
            return False, f"Low relevance ({relevance:.2f}) and not recent"
        
        return True, "Passes all criteria"
    
    def prune_vector_memories(self, vector_store) -> Dict[str, int]:
        """
        Prune memories from vector store
        Returns stats: {'examined': int, 'removed': int, 'preserved': int}
        """
        if not vector_store or not hasattr(vector_store, 'memories'):
            return {'examined': 0, 'removed': 0, 'preserved': 0}
        
        stats = {'examined': 0, 'removed': 0, 'preserved': 0}
        memories_to_keep = []
        
        for memory in vector_store.memories:
            stats['examined'] += 1
            
            memory_dict = memory.to_dict() if hasattr(memory, 'to_dict') else memory
            keep, reason = self.should_keep_memory(memory_dict)
            
            if keep:
                memories_to_keep.append(memory)
                stats['preserved'] += 1
            else:
                stats['removed'] += 1
                self.pruning_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'memory_id': memory_dict.get('id', 'unknown'),
                    'reason': reason,
                    'type': memory_dict.get('memory_type', 'unknown')
                })
        
        # Rebuild vector store with kept memories
        if stats['removed'] > 0:
            try:
                import faiss
                import numpy as np
                
                # Create new index
                new_index = faiss.IndexFlatL2(vector_store.dimension)
                vector_store.index = new_index
                vector_store.memories = []
                vector_store.id_to_index = {}
                
                # Re-add kept memories
                for memory in memories_to_keep:
                    if memory.embedding is None:
                        # Regenerate embedding if needed
                        embedding = vector_store.model.encode([memory.content])[0]
                        memory.embedding = embedding.tolist()
                    
                    embedding_array = np.array([memory.embedding], dtype=np.float32)
                    vector_store.index.add(embedding_array)
                    
                    index_pos = len(vector_store.memories)
                    vector_store.memories.append(memory)
                    vector_store.id_to_index[memory.id] = index_pos
                
                print(f"🧹 Pruned {stats['removed']} memories, kept {stats['preserved']}")
            except Exception as e:
                print(f"⚠️ Error rebuilding vector store: {e}")
        
        return stats
    
    def prune_regular_memories(self, regular_memory: Dict) -> Tuple[Dict, Dict[str, int]]:
        """
        Prune regular (non-vector) memories
        Returns (pruned_memory_dict, stats)
        """
        stats = {'examined': 0, 'removed': 0, 'preserved': 0}
        pruned = {}
        
        for mem_id, mem_data in regular_memory.items():
            stats['examined'] += 1
            
            keep, reason = self.should_keep_memory(mem_data)
            
            if keep:
                pruned[mem_id] = mem_data
                stats['preserved'] += 1
            else:
                stats['removed'] += 1
                self.pruning_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'memory_id': mem_id,
                    'reason': reason,
                    'type': mem_data.get('memory_type', 'unknown')
                })
        
        if stats['removed'] > 0:
            print(f"🧹 Pruned {stats['removed']} regular memories, kept {stats['preserved']}")
        
        return pruned, stats
    
    def prune_goals(self, goals: Dict) -> Tuple[Dict, int]:
        """
        Prune completed/failed goals older than threshold
        Returns (pruned_goals, count_removed)
        """
        cutoff = datetime.now() - timedelta(days=self.policy.max_age_days * 2)
        pruned = {}
        removed = 0
        
        for goal_id, goal in goals.items():
            # Keep active goals
            if goal.status == 'active':
                pruned[goal_id] = goal
                continue
            
            # Check completion date for completed/failed goals
            if goal.completed and goal.completed < cutoff:
                removed += 1
                self.pruning_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'goal_id': goal_id,
                    'reason': f"Old {goal.status} goal",
                    'type': 'goal'
                })
            else:
                pruned[goal_id] = goal
        
        if removed > 0:
            print(f"🧹 Pruned {removed} old goals")
        
        return pruned, removed
    
    def get_pruning_report(self) -> Dict:
        """Get report of recent pruning activity"""
        if not self.pruning_log:
            return {'message': 'No pruning activity recorded'}
        
        # Group by type
        by_type = {}
        for entry in self.pruning_log[-100:]:  # Last 100
            mem_type = entry.get('type', 'unknown')
            by_type[mem_type] = by_type.get(mem_type, 0) + 1
        
        # Group by reason
        by_reason = {}
        for entry in self.pruning_log[-100:]:
            reason = entry.get('reason', 'unknown')
            # Simplify reason for grouping
            if 'old' in reason.lower():
                simplified = 'Too old'
            elif 'relevance' in reason.lower():
                simplified = 'Low relevance'
            else:
                simplified = reason[:30]
            by_reason[simplified] = by_reason.get(simplified, 0) + 1
        
        return {
            'total_pruned': len(self.pruning_log),
            'recent_pruned': len([e for e in self.pruning_log 
                                 if datetime.fromisoformat(e['timestamp']) > 
                                 datetime.now() - timedelta(days=7)]),
            'by_type': by_type,
            'by_reason': by_reason,
            'current_policy': {
                'max_age_days': self.policy.max_age_days,
                'min_relevance': self.policy.min_relevance_score,
                'preserve_types': self.policy.preserve_types
            }
        }


class LearningDatabase:
    """
    SQLite database for storing learned patterns and insights
    Persists across sessions
    """
    
    def __init__(self, db_path: str = 'data/learning.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize learning database"""
        with sqlite3.connect(self.db_path) as conn:
            # Learned patterns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,  -- topic, timing, style, etc.
                    pattern_key TEXT NOT NULL,
                    value REAL,
                    confidence REAL DEFAULT 0.5,
                    sample_size INTEGER DEFAULT 0,
                    first_observed TIMESTAMP,
                    last_updated TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Content insights
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,  -- what_works, what_fails, trend
                    description TEXT NOT NULL,
                    evidence_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.5,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_validated TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            """)
            
            # Learning sessions log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    items_processed INTEGER,
                    insights_generated INTEGER,
                    status TEXT
                )
            """)
            
            conn.commit()
    
    def record_pattern(self, pattern_type: str, pattern_key: str, 
                      value: float, confidence: float = 0.5,
                      sample_size: int = 1, metadata: Dict = None) -> bool:
        """Record a learned pattern"""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                # Check if pattern exists
                cursor = conn.execute(
                    "SELECT id, value, confidence, sample_size FROM learned_patterns "
                    "WHERE pattern_type = ? AND pattern_key = ?",
                    (pattern_type, pattern_key)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing with weighted average
                    old_id, old_value, old_conf, old_samples = existing
                    total_samples = old_samples + sample_size
                    new_value = ((old_value * old_samples) + (value * sample_size)) / total_samples
                    new_conf = ((old_conf * old_samples) + (confidence * sample_size)) / total_samples
                    
                    conn.execute(
                        "UPDATE learned_patterns SET value = ?, confidence = ?, "
                        "sample_size = ?, last_updated = ?, metadata = ? WHERE id = ?",
                        (new_value, new_conf, total_samples, now,
                         json.dumps(metadata) if metadata else None, old_id)
                    )
                else:
                    # Insert new pattern
                    conn.execute(
                        "INSERT INTO learned_patterns "
                        "(pattern_type, pattern_key, value, confidence, sample_size, "
                        "first_observed, last_updated, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (pattern_type, pattern_key, value, confidence, sample_size,
                         now, now, json.dumps(metadata) if metadata else None)
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording pattern: {e}")
            return False
    
    def record_insight(self, insight_type: str, description: str,
                      evidence_count: int = 0, confidence: float = 0.5) -> bool:
        """Record a content/engagement insight"""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO content_insights "
                    "(insight_type, description, evidence_count, confidence, last_validated) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (insight_type, description, evidence_count, confidence, now)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording insight: {e}")
            return False
    
    def get_patterns(self, pattern_type: str = None, min_confidence: float = 0.3) -> List[Dict]:
        """Get learned patterns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if pattern_type:
                    cursor = conn.execute(
                        "SELECT * FROM learned_patterns WHERE pattern_type = ? AND confidence >= ? "
                        "ORDER BY confidence DESC, last_updated DESC",
                        (pattern_type, min_confidence)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM learned_patterns WHERE confidence >= ? "
                        "ORDER BY confidence DESC, last_updated DESC",
                        (min_confidence,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting patterns: {e}")
            return []
    
    def get_insights(self, active_only: bool = True, min_confidence: float = 0.3) -> List[Dict]:
        """Get content insights"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if active_only:
                    cursor = conn.execute(
                        "SELECT * FROM content_insights WHERE active = 1 AND confidence >= ? "
                        "ORDER BY confidence DESC, discovered_at DESC",
                        (min_confidence,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM content_insights WHERE confidence >= ? "
                        "ORDER BY confidence DESC, discovered_at DESC",
                        (min_confidence,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting insights: {e}")
            return []


# Convenience function for easy pruning
def auto_prune_memory(enhanced_memory_system, 
                     policy: MemoryPruningPolicy = None) -> Dict:
    """
    Auto-prune memory with given policy
    Returns stats dict
    """
    pruner = MemoryPruner(policy)
    stats = {'vector': {}, 'regular': {}, 'goals': 0}
    
    # Prune vector memories
    if enhanced_memory_system.vector_store:
        stats['vector'] = pruner.prune_vector_memories(
            enhanced_memory_system.vector_store
        )
    
    # Prune regular memories
    pruned_regular, reg_stats = pruner.prune_regular_memories(
        enhanced_memory_system.regular_memory
    )
    enhanced_memory_system.regular_memory = pruned_regular
    stats['regular'] = reg_stats
    
    # Prune goals
    if enhanced_memory_system.goals:
        pruned_goals, goal_removed = pruner.prune_goals(
            enhanced_memory_system.goals
        )
        enhanced_memory_system.goals = pruned_goals
        stats['goals'] = goal_removed
    
    # Save changes
    enhanced_memory_system._save_regular_memory()
    enhanced_memory_system._save_goals()
    if enhanced_memory_system.vector_store:
        enhanced_memory_system._save_vector_store()
    
    return stats
