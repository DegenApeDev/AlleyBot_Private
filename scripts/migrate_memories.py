#!/usr/bin/env python3
"""
Memory Migration Script

Migrates memories from EnhancedMemorySystem (vector store) to MemoryService (SQLite).
This consolidates the two parallel memory systems into a single source of truth.

Usage:
    python scripts/migrate_memories.py [--dry-run] [--limit N]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agentic.enhanced_memory import EnhancedMemorySystem
from src.agentic.memory_service import get_memory_service, MemoryType


def migrate_memories(dry_run=False, limit=None):
    """
    Migrate memories from vector store to SQLite.
    
    Args:
        dry_run: If True, only print what would be migrated
        limit: Maximum number of memories to migrate (None = all)
    """
    print("🔄 Starting memory migration...")
    print(f"   Dry run: {dry_run}")
    print(f"   Limit: {limit if limit else 'all'}")
    print()
    
    # Initialize systems
    print("📂 Loading EnhancedMemorySystem (source)...")
    enhanced_memory = EnhancedMemorySystem()
    
    print("📂 Loading MemoryService (destination)...")
    memory_service = get_memory_service()
    
    # Get source memories
    if not enhanced_memory.vector_store:
        print("❌ No vector store available in EnhancedMemorySystem")
        return
    
    source_memories = enhanced_memory.vector_store.memories
    total = len(source_memories)
    
    print(f"✅ Found {total} memories in vector store")
    print()
    
    # Limit if specified
    if limit:
        source_memories = source_memories[:limit]
        print(f"📊 Limiting migration to {len(source_memories)} memories")
        print()
    
    # Migrate each memory
    migrated = 0
    skipped = 0
    errors = 0
    
    for i, memory in enumerate(source_memories, 1):
        try:
            # Map memory type (MemoryService only has: EPISODIC, SEMANTIC, CONVERSATIONAL, WORK, REFLECTION)
            memory_type_map = {
                'episodic': MemoryType.EPISODIC,
                'semantic': MemoryType.SEMANTIC,
                'procedural': MemoryType.SEMANTIC,  # Map procedural to semantic
                'conversation': MemoryType.CONVERSATIONAL,
                'conversational': MemoryType.CONVERSATIONAL,
                'work': MemoryType.WORK,
                'reflection': MemoryType.REFLECTION,
            }
            
            # Get memory type as lowercase string
            old_type = str(memory.memory_type).lower() if memory.memory_type else 'episodic'
            mem_type = memory_type_map.get(old_type, MemoryType.EPISODIC)
            
            if dry_run:
                print(f"[{i}/{len(source_memories)}] Would migrate: {memory.content[:60]}...")
                migrated += 1
            else:
                # Store in new system (content is first parameter, then memory_type)
                memory_service.store(
                    content=memory.content,
                    memory_type=mem_type,
                    source_plugin='vector_store_migration',
                    tags=memory.tags if hasattr(memory, 'tags') else [],
                    importance=memory.importance if hasattr(memory, 'importance') else 1.0,
                    metadata={
                        'migrated_from': 'vector_store',
                        'original_id': memory.id,
                        'original_timestamp': memory.timestamp.isoformat() if hasattr(memory.timestamp, 'isoformat') else str(memory.timestamp),
                    }
                )
                
                if i % 100 == 0:
                    print(f"✅ Migrated {i}/{len(source_memories)} memories...")
                
                migrated += 1
                
        except Exception as e:
            print(f"❌ Error migrating memory {i}: {e}")
            errors += 1
    
    print()
    print("=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"Total source memories: {total}")
    print(f"Processed: {len(source_memories)}")
    print(f"Migrated: {migrated}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print()
    
    if not dry_run:
        # Verify migration
        stats = memory_service.get_stats()
        print(f"✅ MemoryService now has {stats['total_records']} total records")
        print(f"   By type: {stats['by_type']}")
        print()
        print("🎉 Migration complete!")
        print()
        print("Next steps:")
        print("1. Verify memories are accessible via MemoryService")
        print("2. Test memory retrieval and search")
        print("3. Once confirmed, deprecate EnhancedMemorySystem")
    else:
        print("ℹ️  This was a dry run. Run without --dry-run to perform actual migration.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate memories from vector store to SQLite')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be migrated without actually migrating')
    parser.add_argument('--limit', type=int, help='Limit number of memories to migrate')
    
    args = parser.parse_args()
    
    migrate_memories(dry_run=args.dry_run, limit=args.limit)
