"""
Enhanced Memory System with Vector DB and Encryption
Semantic search, hierarchical goals, and secure storage
"""
import os
import json
import pickle
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import numpy as np

# Vector DB imports
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    print("⚠️  Vector DB dependencies not available. Install: pip install faiss-cpu sentence-transformers")


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
            'metadata': self.metadata,
            'relevance_score': self.relevance_score
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
    completed: datetime = None
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
            'sub_goals': self.sub_goals,
            'status': self.status,
            'priority': self.priority,
            'created': self.created.isoformat(),
            'completed': self.completed.isoformat() if self.completed else None,
            'progress': self.progress,
            'metadata': self.metadata
        }


class SecureStorage:
    """Encrypted storage for sensitive data"""
    
    def __init__(self, key_file: str = '.memory_key'):
        self.key_file = Path(key_file)
        self.cipher = self._load_or_create_key()
    
    def _load_or_create_key(self) -> Fernet:
        """Load existing key or create new one"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt data"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_dict(self, data: Dict) -> bytes:
        """Encrypt dictionary"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: bytes) -> Dict:
        """Decrypt to dictionary"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class VectorMemoryStore:
    """Vector database for semantic memory search"""
    
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        if not VECTOR_DB_AVAILABLE:
            raise ImportError("Vector DB dependencies not available")
        
        self.model = SentenceTransformer(embedding_model)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.memories: List[Memory] = []
        self.id_to_index = {}
        
    def add_memory(self, memory: Memory):
        """Add memory to vector store"""
        # Generate embedding if not present
        if memory.embedding is None:
            embedding = self.model.encode([memory.content])[0]
            memory.embedding = embedding.tolist()
        else:
            embedding = np.array(memory.embedding, dtype=np.float32)
        
        # Add to FAISS index
        embedding_array = np.array([embedding], dtype=np.float32)
        self.index.add(embedding_array)
        
        # Store memory
        index_pos = len(self.memories)
        self.memories.append(memory)
        self.id_to_index[memory.id] = index_pos
    
    def search(self, query: str, k: int = 5, 
               memory_type: Optional[str] = None) -> List[Memory]:
        """
        Semantic search for relevant memories
        
        Args:
            query: Search query
            k: Number of results to return
            memory_type: Optional filter by memory type
            
        Returns:
            List of relevant memories
        """
        if len(self.memories) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        distances, indices = self.index.search(query_array, min(k * 2, len(self.memories)))
        
        # Get memories
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.memories):
                memory = self.memories[idx]
                
                # Filter by type if specified
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                # Add similarity score (convert distance to similarity)
                memory.relevance_score = 1.0 / (1.0 + dist)
                results.append(memory)
                
                if len(results) >= k:
                    break
        
        return results
    
    def save(self, filepath: str):
        """Save vector store to disk"""
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save memories
        with open(f"{filepath}.pkl", 'wb') as f:
            pickle.dump({
                'memories': self.memories,
                'id_to_index': self.id_to_index
            }, f)
    
    def load(self, filepath: str):
        """Load vector store from disk"""
        # Load FAISS index
        self.index = faiss.read_index(f"{filepath}.index")
        
        # Load memories
        with open(f"{filepath}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.memories = data['memories']
            self.id_to_index = data['id_to_index']


class EnhancedMemorySystem:
    """
    Enhanced memory system with:
    - Vector DB for semantic search
    - Encrypted storage for sensitive data
    - Hierarchical goal tracking
    - Automatic pruning
    """
    
    def __init__(self, storage_dir: str = 'data/memory'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.secure_storage = SecureStorage(self.storage_dir / '.memory_key')
        
        # Initialize vector store if available
        self.vector_store = None
        if VECTOR_DB_AVAILABLE:
            try:
                self.vector_store = VectorMemoryStore()
                self._load_vector_store()
            except Exception as e:
                print(f"⚠️  Could not initialize vector store: {e}")
        
        # Goal tracking
        self.goals: Dict[str, Goal] = {}
        self._load_goals()
        
        # Sensitive data (encrypted)
        self.sensitive_data = {}
        self._load_sensitive_data()
        
        # Regular memory (non-vector)
        self.regular_memory = {}
        self._load_regular_memory()
        
    def add_memory(self, content: str, memory_type: str, 
                   metadata: Optional[Dict] = None) -> str:
        """Add a new memory"""
        memory_id = f"mem_{datetime.now().timestamp()}"
        
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Add to vector store if available
        if self.vector_store:
            self.vector_store.add_memory(memory)
            self._save_vector_store()
        else:
            # Fallback to regular memory
            self.regular_memory[memory_id] = memory.to_dict()
            self._save_regular_memory()
        
        return memory_id
    
    def search_memories(self, query: str, k: int = 5, 
                       memory_type: Optional[str] = None) -> List[Dict]:
        """Search for relevant memories"""
        if self.vector_store:
            memories = self.vector_store.search(query, k, memory_type)
            return [m.to_dict() for m in memories]
        else:
            # Fallback: simple keyword search
            results = []
            for mem_id, mem_data in self.regular_memory.items():
                if memory_type and mem_data['memory_type'] != memory_type:
                    continue
                
                if query.lower() in mem_data['content'].lower():
                    results.append(mem_data)
                
                if len(results) >= k:
                    break
            
            return results
    
    def add_goal(self, description: str, goal_type: str = 'short_term',
                 parent_goal_id: Optional[str] = None, priority: int = 1) -> str:
        """Add a new goal"""
        goal_id = f"goal_{datetime.now().timestamp()}"
        
        goal = Goal(
            id=goal_id,
            description=description,
            goal_type=goal_type,
            parent_goal_id=parent_goal_id,
            priority=priority
        )
        
        self.goals[goal_id] = goal
        
        # Add to parent's sub_goals if applicable
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].sub_goals.append(goal_id)
        
        self._save_goals()
        return goal_id
    
    def update_goal_progress(self, goal_id: str, progress: float):
        """Update goal progress (0.0 to 1.0)"""
        if goal_id in self.goals:
            self.goals[goal_id].progress = progress
            
            # Auto-complete if progress reaches 100%
            if progress >= 1.0:
                self.complete_goal(goal_id)
            
            self._save_goals()
    
    def complete_goal(self, goal_id: str):
        """Mark goal as completed"""
        if goal_id in self.goals:
            self.goals[goal_id].status = 'completed'
            self.goals[goal_id].completed = datetime.now()
            self.goals[goal_id].progress = 1.0
            
            # Update parent goal progress
            parent_id = self.goals[goal_id].parent_goal_id
            if parent_id and parent_id in self.goals:
                self._update_parent_progress(parent_id)
            
            self._save_goals()
    
    def _update_parent_progress(self, parent_id: str):
        """Update parent goal progress based on sub-goals"""
        parent = self.goals[parent_id]
        
        if not parent.sub_goals:
            return
        
        # Calculate average progress of sub-goals
        total_progress = 0
        for sub_goal_id in parent.sub_goals:
            if sub_goal_id in self.goals:
                total_progress += self.goals[sub_goal_id].progress
        
        parent.progress = total_progress / len(parent.sub_goals)
        
        # Auto-complete parent if all sub-goals complete
        if parent.progress >= 1.0:
            self.complete_goal(parent_id)
    
    def get_active_goals(self, goal_type: Optional[str] = None) -> List[Dict]:
        """Get all active goals"""
        active = []
        
        for goal in self.goals.values():
            if goal.status == 'active':
                if goal_type is None or goal.goal_type == goal_type:
                    active.append(goal.to_dict())
        
        # Sort by priority
        active.sort(key=lambda g: g['priority'], reverse=True)
        
        return active
    
    def get_goal_hierarchy(self, root_goal_id: str) -> Dict:
        """Get goal hierarchy starting from root"""
        if root_goal_id not in self.goals:
            return {}
        
        root = self.goals[root_goal_id]
        hierarchy = root.to_dict()
        
        # Recursively get sub-goals
        hierarchy['sub_goals_data'] = []
        for sub_goal_id in root.sub_goals:
            sub_hierarchy = self.get_goal_hierarchy(sub_goal_id)
            if sub_hierarchy:
                hierarchy['sub_goals_data'].append(sub_hierarchy)
        
        return hierarchy
    
    def store_sensitive(self, key: str, value: Any):
        """Store sensitive data with encryption"""
        self.sensitive_data[key] = value
        self._save_sensitive_data()
    
    def get_sensitive(self, key: str) -> Optional[Any]:
        """Retrieve sensitive data"""
        return self.sensitive_data.get(key)
    
    def prune_old_memories(self, days: int = 30, keep_important: bool = True):
        """Prune memories older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if self.vector_store:
            # Filter memories
            kept_memories = []
            for memory in self.vector_store.memories:
                # Keep if recent
                if memory.timestamp > cutoff_date:
                    kept_memories.append(memory)
                # Keep if important (high relevance or specific types)
                elif keep_important and (
                    memory.relevance_score > 0.8 or
                    memory.memory_type in ['learning', 'on_chain_event']
                ):
                    kept_memories.append(memory)
            
            # Rebuild index
            if len(kept_memories) < len(self.vector_store.memories):
                print(f"🧹 Pruned {len(self.vector_store.memories) - len(kept_memories)} old memories")
                
                # Create new index
                self.vector_store.index = faiss.IndexFlatL2(self.vector_store.dimension)
                self.vector_store.memories = []
                self.vector_store.id_to_index = {}
                
                # Re-add kept memories
                for memory in kept_memories:
                    self.vector_store.add_memory(memory)
                
                self._save_vector_store()
    
    def advanced_prune(self, max_age_days: int = 30, min_relevance: float = 0.3) -> Dict:
        """
        Phase 12.5: Advanced memory pruning with intelligent policies
        Returns pruning statistics
        """
        try:
            from .phase12_pruning import MemoryPruner, MemoryPruningPolicy, auto_prune_memory
            
            policy = MemoryPruningPolicy(
                max_age_days=max_age_days,
                min_relevance_score=min_relevance,
                preserve_types=['goal', 'learning', 'on_chain_event'],
                preserve_goals=True,
                preserve_learning=True
            )
            
            return auto_prune_memory(self, policy)
        except Exception as e:
            print(f"⚠️ Error in advanced pruning: {e}")
            return {'error': str(e)}
    
    def get_pruning_report(self) -> Dict:
        """Get memory pruning activity report"""
        try:
            from .phase12_pruning import MemoryPruningPolicy, MemoryPruner
            pruner = MemoryPruner(MemoryPruningPolicy())
            return pruner.get_pruning_report()
        except Exception as e:
            print(f"⚠️ Error getting pruning report: {e}")
            return {'error': str(e)}
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            'total_memories': 0,
            'memory_types': {},
            'total_goals': len(self.goals),
            'active_goals': len([g for g in self.goals.values() if g.status == 'active']),
            'completed_goals': len([g for g in self.goals.values() if g.status == 'completed']),
            'sensitive_keys': len(self.sensitive_data),
            'vector_db_enabled': self.vector_store is not None
        }
        
        if self.vector_store:
            stats['total_memories'] = len(self.vector_store.memories)
            
            # Count by type
            for memory in self.vector_store.memories:
                mem_type = memory.memory_type
                stats['memory_types'][mem_type] = stats['memory_types'].get(mem_type, 0) + 1
        else:
            stats['total_memories'] = len(self.regular_memory)
        
        return stats
    
    # Persistence methods
    def _save_vector_store(self):
        """Save vector store to disk"""
        if self.vector_store:
            try:
                filepath = str(self.storage_dir / 'vector_store')
                self.vector_store.save(filepath)
            except Exception as e:
                print(f"⚠️  Error saving vector store: {e}")
    
    def _load_vector_store(self):
        """Load vector store from disk"""
        if self.vector_store:
            try:
                filepath = str(self.storage_dir / 'vector_store')
                if Path(f"{filepath}.index").exists():
                    self.vector_store.load(filepath)
                    print(f"✅ Loaded {len(self.vector_store.memories)} memories from vector store")
            except Exception as e:
                print(f"⚠️  Error loading vector store: {e}")
    
    def _save_goals(self):
        """Save goals to disk"""
        try:
            goals_data = {gid: g.to_dict() for gid, g in self.goals.items()}
            with open(self.storage_dir / 'goals.json', 'w') as f:
                json.dump(goals_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving goals: {e}")
    
    def _load_goals(self):
        """Load goals from disk"""
        try:
            goals_file = self.storage_dir / 'goals.json'
            if goals_file.exists():
                with open(goals_file, 'r') as f:
                    goals_data = json.load(f)
                
                for gid, gdata in goals_data.items():
                    # Reconstruct Goal object
                    gdata['created'] = datetime.fromisoformat(gdata['created'])
                    if gdata['completed']:
                        gdata['completed'] = datetime.fromisoformat(gdata['completed'])
                    
                    self.goals[gid] = Goal(**gdata)
                
                print(f"✅ Loaded {len(self.goals)} goals")
        except Exception as e:
            print(f"⚠️  Error loading goals: {e}")
    
    def _save_sensitive_data(self):
        """Save encrypted sensitive data"""
        try:
            encrypted = self.secure_storage.encrypt_dict(self.sensitive_data)
            with open(self.storage_dir / 'sensitive.enc', 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            print(f"⚠️  Error saving sensitive data: {e}")
    
    def _load_sensitive_data(self):
        """Load encrypted sensitive data"""
        try:
            sensitive_file = self.storage_dir / 'sensitive.enc'
            if sensitive_file.exists():
                with open(sensitive_file, 'rb') as f:
                    encrypted = f.read()
                
                self.sensitive_data = self.secure_storage.decrypt_dict(encrypted)
                print(f"✅ Loaded {len(self.sensitive_data)} sensitive keys")
        except Exception as e:
            print(f"⚠️  Error loading sensitive data: {e}")
    
    def _save_regular_memory(self):
        """Save regular memory (fallback when vector DB unavailable)"""
        try:
            with open(self.storage_dir / 'memory.json', 'w') as f:
                json.dump(self.regular_memory, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving regular memory: {e}")
    
    def _load_regular_memory(self):
        """Load regular memory"""
        try:
            memory_file = self.storage_dir / 'memory.json'
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    self.regular_memory = json.load(f)
                
                print(f"✅ Loaded {len(self.regular_memory)} regular memories")
        except Exception as e:
            print(f"⚠️  Error loading regular memory: {e}")
