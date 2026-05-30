"""
Enhanced Memory System — stub for backward compatibility.

The full implementation was deprecated in favor of unified_memory + sqlite_memory.
This stub ensures all existing import paths resolve without crashing.
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class EnhancedMemorySystem:
    """Backward-compatible stub. Real implementation lives in unified_memory."""

    def __init__(self, storage_dir: str = 'data/memory'):
        self.storage_dir = storage_dir
        self.vector_store = None
        self.goals: Dict = {}
        logger.debug("EnhancedMemorySystem stub loaded (use unified_memory instead)")

    def add_memory(self, content: str, memory_type: str = 'interaction', metadata: Optional[Dict] = None) -> bool:
        return False

    def search_memories(self, query: str, k: int = 5, memory_type: Optional[str] = None) -> List[Dict]:
        return []

    def add_goal(self, description: str, goal_type: str = 'short_term', parent_goal_id: Optional[str] = None, priority: int = 1) -> Optional[str]:
        return None

    def get_active_goals(self, goal_type: Optional[str] = None) -> List[Dict]:
        return []

    def get_memory_stats(self) -> Dict[str, Any]:
        return {'status': 'stub', 'message': 'Use unified_memory for actual storage'}
