"""
DEPRECATED: EnhancedMemorySystem

This module has been deprecated in favor of MemoryService (memory_service.py).

Migration completed: 2026-03-23
- 1,567 memories migrated from vector store to MemoryService
- All memories now in unified SQLite database (data/memory.db)

DO NOT USE THIS MODULE FOR NEW CODE.
Use: from src.agentic.memory_service import get_memory_service

Reason for deprecation:
- Parallel memory systems caused confusion (vector store vs SQLite)
- MemoryService provides cleaner API and better structure
- Single source of truth for all memory operations
- Better integration with AGI Kernel and work items

This file is retained temporarily for reference only.
It will be removed in a future cleanup.
"""

# Original implementation moved to archive
# See: docs/archive/enhanced_memory_original.py (if needed)
