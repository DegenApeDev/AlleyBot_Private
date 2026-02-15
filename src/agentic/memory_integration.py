"""
SQLite Memory Integration for AlleyBot Core
Replaces the existing JSON-based memory with SQLite backend.
Maintains backward compatibility with all existing memory interfaces.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import the new SQLite memory system
try:
    from src.agentic.sqlite_memory import SQLiteMemorySystem
    SQLITE_MEMORY_AVAILABLE = True
except ImportError:
    SQLITE_MEMORY_AVAILABLE = False
    print("⚠️ SQLite memory not available, falling back to JSON")


class SQLiteMemoryMixin:
    """
    Mixin to add SQLite memory support to AlleyBotCore.
    Replaces JSON file storage with SQLite database.
    """
    
    def _init_sqlite_memory(self, db_path: str = 'data/memory.db'):
        """Initialize SQLite memory system"""
        if SQLITE_MEMORY_AVAILABLE:
            try:
                self.memory_db = SQLiteMemorySystem(db_path)
                
                # Migrate existing JSON memory files if they exist (one-time only)
                migration_marker = Path('data/.migration_complete')
                if Path('memory').exists() and not migration_marker.exists():
                    stats = self.memory_db.migrate_from_json('memory')
                    if stats['files_migrated'] > 0:
                        print(f"✅ Migrated {stats['files_migrated']} JSON files to SQLite")
                    # Create marker to prevent future migrations
                    migration_marker.parent.mkdir(parents=True, exist_ok=True)
                    migration_marker.touch()
                
                print("💾 SQLite memory system ready")
                return True
            except Exception as e:
                print(f"⚠️ SQLite memory init failed: {e}, using fallback")
                self.memory_db = None
                return False
        else:
            self.memory_db = None
            return False
    
    def get_memory(self, memory_type: str = 'state') -> Dict:
        """
        Get memory storage - SQLite backend with JSON fallback
        Maintains exact same interface as original
        """
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.get_memory(memory_type, default={})
        
        # Fallback to original JSON implementation
        return self._get_memory_json(memory_type)
    
    def save_memory(self, memory_type: str, data: Any) -> None:
        """
        Save memory storage - SQLite backend with JSON fallback
        Maintains exact same interface as original
        """
        if hasattr(self, 'memory_db') and self.memory_db:
            self.memory_db.save_memory(memory_type, data)
            return
        
        # Fallback to original JSON implementation
        self._save_memory_json(memory_type, data)
    
    def _get_memory_json(self, memory_type: str = 'state') -> Dict:
        """Original JSON implementation (fallback)"""
        import json
        from pathlib import Path
        
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)
        
        memory_file = memory_dir / f'{memory_type}.json'
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_memory_json(self, memory_type: str, data: Any) -> None:
        """Original JSON implementation (fallback)"""
        import json
        from pathlib import Path
        
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)
        
        memory_file = memory_dir / f'{memory_type}.json'
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_semantic_memory(self, content: str, memory_type: str = 'interaction', 
                           metadata: Dict = None) -> Optional[str]:
        """Add semantic memory with embedding"""
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.add_memory(content, memory_type, metadata)
        
        # Fallback: store in JSON
        fallback_data = self.get_memory(f'semantic_{memory_type}')
        if not isinstance(fallback_data, list):
            fallback_data = []
        
        import datetime
        fallback_data.append({
            'content': content,
            'type': memory_type,
            'metadata': metadata or {},
            'timestamp': datetime.datetime.now().isoformat()
        })
        self.save_memory(f'semantic_{memory_type}', fallback_data)
        return None
    
    def search_memories(self, query: str, k: int = 5, memory_type: str = None) -> list:
        """Search semantic memories"""
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.search_memories(query, memory_type, k)
        
        # Fallback: simple text search in JSON
        fallback_data = self.get_memory(f'semantic_{memory_type}') if memory_type else []
        if isinstance(fallback_data, dict):
            fallback_data = list(fallback_data.values())
        
        # Simple substring matching
        results = []
        for item in fallback_data:
            if isinstance(item, dict) and 'content' in item:
                if query.lower() in item['content'].lower():
                    results.append(item)
        return results[:k]
    
    def add_goal(self, description: str, goal_type: str = 'short_term',
                 parent_goal_id: str = None, priority: int = 1) -> Optional[str]:
        """Add a hierarchical goal"""
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.add_goal(description, goal_type, parent_goal_id, priority)
        
        # Fallback: store in JSON
        fallback_data = self.get_memory('goals')
        if not isinstance(fallback_data, dict):
            fallback_data = {}
        
        import datetime
        goal_id = f"goal_{len(fallback_data)}"
        fallback_data[goal_id] = {
            'description': description,
            'type': goal_type,
            'status': 'active',
            'priority': priority,
            'created': datetime.datetime.now().isoformat()
        }
        self.save_memory('goals', fallback_data)
        return goal_id
    
    def get_active_goals(self, goal_type: str = None) -> list:
        """Get active goals"""
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.get_active_goals(goal_type)
        
        # Fallback: simple filtering from JSON
        fallback_data = self.get_memory('goals')
        if not isinstance(fallback_data, dict):
            return []
        
        goals = []
        for goal_id, goal in fallback_data.items():
            if goal.get('status') == 'active':
                if goal_type is None or goal.get('type') == goal_type:
                    goals.append({**goal, 'id': goal_id})
        return goals
    
    def store_sensitive(self, key: str, value: Any) -> None:
        """Store encrypted sensitive data"""
        if hasattr(self, 'memory_db') and self.memory_db:
            try:
                self.memory_db.store_sensitive(key, value)
                return
            except RuntimeError:
                pass  # Fallback if encryption not available
        
        print("⚠️ Secure storage not available, value not stored")
    
    def get_sensitive(self, key: str) -> Optional[Any]:
        """Retrieve encrypted sensitive data"""
        if hasattr(self, 'memory_db') and self.memory_db:
            try:
                return self.memory_db.get_sensitive(key)
            except RuntimeError:
                pass
        
        return None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if hasattr(self, 'memory_db') and self.memory_db:
            return self.memory_db.get_memory_stats()
        
        # Fallback: count JSON files
        from pathlib import Path
        memory_dir = Path('memory')
        if memory_dir.exists():
            json_files = list(memory_dir.glob('*.json'))
            return {
                'sqlite': None,
                'json_fallback': {
                    'file_count': len(json_files),
                    'files': [f.stem for f in json_files]
                }
            }
        return {'sqlite': None, 'json_fallback': {'file_count': 0, 'files': []}}
    
    def close_memory(self):
        """Close memory connections on cleanup"""
        if hasattr(self, 'memory_db') and self.memory_db:
            self.memory_db.close()
