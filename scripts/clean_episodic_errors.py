#!/usr/bin/env python3
"""
Clean old error messages from episodic memory.

This removes episodic memories that contain the old _reflect_on_outcome error
so they stop being displayed as warnings on every action.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

EPISODIC_MEMORY_PATH = project_root / "data" / "episodic_memory.json"

def clean_episodic_memory():
    """Remove episodic memories with old error messages"""
    print(f"🔄 Cleaning episodic memory: {EPISODIC_MEMORY_PATH}")
    
    if not EPISODIC_MEMORY_PATH.exists():
        print(f"❌ Episodic memory file not found: {EPISODIC_MEMORY_PATH}")
        return False
    
    try:
        # Load episodic memories
        with open(EPISODIC_MEMORY_PATH, 'r') as f:
            memories = json.load(f)
        
        print(f"📊 Total memories: {len(memories)}")
        
        # Find memories with the old error
        error_pattern = "_reflect_on_outcome() missing 1 required positional"
        old_errors = [m for m in memories if error_pattern in m.get('outcome', '')]
        
        print(f"🔍 Found {len(old_errors)} memories with old error")
        
        if not old_errors:
            print("✅ No old errors to clean")
            return True
        
        # Show what we're removing
        print("\n📋 Memories to remove:")
        for mem in old_errors:
            print(f"  - {mem['id']}: {mem['context']} (recalled {mem['recall_count']} times)")
        
        # Remove old error memories
        cleaned_memories = [m for m in memories if error_pattern not in m.get('outcome', '')]
        
        # Backup original
        backup_path = EPISODIC_MEMORY_PATH.with_suffix('.json.backup')
        with open(backup_path, 'w') as f:
            json.dump(memories, f, indent=2)
        print(f"\n💾 Backup saved: {backup_path}")
        
        # Save cleaned memories
        with open(EPISODIC_MEMORY_PATH, 'w') as f:
            json.dump(cleaned_memories, f, indent=2)
        
        print(f"\n✅ Cleaned episodic memory!")
        print(f"   Removed: {len(old_errors)} error memories")
        print(f"   Remaining: {len(cleaned_memories)} memories")
        print(f"   Backup: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clean_episodic_memory()
    sys.exit(0 if success else 1)
