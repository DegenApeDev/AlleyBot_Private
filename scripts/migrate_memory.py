#!/usr/bin/env python3
"""
Memory Migration Script: JSON to SQLite
Migrates existing AlleyBot memory files from JSON to SQLite database.
Run this before starting AlleyBot with the new SQLite memory system.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.agentic.sqlite_memory import SQLiteMemorySystem
except ImportError as e:
    print(f"❌ Error: Could not import SQLiteMemorySystem: {e}")
    print("Make sure you're in the AlleyBot directory and dependencies are installed.")
    sys.exit(1)


def migrate_json_to_sqlite(memory_dir='memory', db_path='data/memory.db', dry_run=False):
    """
    Migrate JSON memory files to SQLite database.
    
    Args:
        memory_dir: Directory containing JSON memory files
        db_path: Path for new SQLite database
        dry_run: If True, only show what would be migrated without making changes
    
    Returns:
        dict: Migration statistics
    """
    print(f"{'='*60}")
    print(f"🔄 AlleyBot Memory Migration: JSON → SQLite")
    print(f"{'='*60}")
    print(f"Source: {memory_dir}/")
    print(f"Target: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE MIGRATION'}")
    print(f"{'='*60}\n")
    
    # Initialize SQLite memory system
    if not dry_run:
        print("💾 Initializing SQLite memory system...")
        sqlite_memory = SQLiteMemorySystem(db_path)
    else:
        print("🔍 Dry run mode - analyzing files only...")
        sqlite_memory = None
    
    # Statistics
    stats = {
        'files_found': 0,
        'files_migrated': 0,
        'records_migrated': 0,
        'errors': 0,
        'skipped': 0,
        'by_type': {}
    }
    
    # Check if memory directory exists
    memory_path = Path(memory_dir)
    if not memory_path.exists():
        print(f"⚠️  Memory directory not found: {memory_dir}")
        print("   Nothing to migrate.")
        return stats
    
    # Find all JSON files
    json_files = list(memory_path.glob('*.json'))
    stats['files_found'] = len(json_files)
    
    if not json_files:
        print("📭 No JSON memory files found to migrate.")
        return stats
    
    print(f"📁 Found {len(json_files)} JSON files:\n")
    
    # Process each JSON file
    for json_file in sorted(json_files):
        file_key = json_file.stem
        print(f"  📄 {file_key}.json", end=' ')
        
        try:
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine data structure
            if isinstance(data, dict):
                record_count = len(data)
            elif isinstance(data, list):
                record_count = len(data)
            else:
                record_count = 1
            
            stats['by_type'][file_key] = record_count
            print(f"→ {record_count} records")
            
            if dry_run:
                stats['files_migrated'] += 1
                stats['records_migrated'] += record_count
                continue
            
            # Migrate to SQLite
            # Handle special memory types differently
            if file_key.startswith('semantic_'):
                # Semantic memories - store in memories table
                memory_type = file_key.replace('semantic_', '')
                if isinstance(data, list):
                    for item in data:
                        content = item.get('content', str(item))
                        metadata = item.get('metadata', {})
                        sqlite_memory.add_memory(content, memory_type, metadata)
                    stats['records_migrated'] += len(data)
                else:
                    sqlite_memory.add_memory(str(data), memory_type)
                    stats['records_migrated'] += 1
                    
            elif file_key == 'goals':
                # Goals - store in goals table
                if isinstance(data, dict):
                    for goal_id, goal_data in data.items():
                        if isinstance(goal_data, dict):
                            sqlite_memory.add_goal(
                                description=goal_data.get('description', 'Unknown goal'),
                                goal_type=goal_data.get('type', 'short_term'),
                                priority=goal_data.get('priority', 1),
                                metadata=goal_data
                            )
                    stats['records_migrated'] += len(data)
                    
            else:
                # Standard key-value store
                sqlite_memory.save_memory(file_key, data)
                stats['records_migrated'] += record_count
            
            stats['files_migrated'] += 1
            print(f"  ✅ Migrated")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON: {e}")
            stats['errors'] += 1
            stats['skipped'] += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            stats['errors'] += 1
            stats['skipped'] += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 MIGRATION SUMMARY")
    print(f"{'='*60}")
    print(f"  Files found:      {stats['files_found']}")
    print(f"  Files migrated:   {stats['files_migrated']}")
    print(f"  Records migrated: {stats['records_migrated']}")
    print(f"  Errors:           {stats['errors']}")
    print(f"  Skipped:          {stats['skipped']}")
    
    if stats['by_type']:
        print(f"\n  Breakdown by type:")
        for mem_type, count in sorted(stats['by_type'].items()):
            print(f"    • {mem_type}: {count} records")
    
    if not dry_run and sqlite_memory:
        # Show final stats
        final_stats = sqlite_memory.get_memory_stats()
        print(f"\n  Final database:")
        print(f"    Path: {final_stats['database']['path']}")
        print(f"    Size: {final_stats['database']['size_mb']} MB")
        print(f"    Key-value entries: {final_stats['key_value_store']['entries']}")
        print(f"    Semantic memories: {final_stats['memories']['total']}")
        print(f"    Goals: {final_stats['goals']['total']}")
    
    print(f"{'='*60}\n")
    
    return stats


def backup_json_files(memory_dir='memory', backup_suffix='.backup'):
    """
    Create backup copies of all JSON memory files.
    """
    memory_path = Path(memory_dir)
    if not memory_path.exists():
        return
    
    print(f"📦 Creating backups of JSON files...")
    
    backup_count = 0
    for json_file in memory_path.glob('*.json'):
        backup_file = json_file.with_suffix(f'{json_file.suffix}{backup_suffix}')
        if not backup_file.exists():
            import shutil
            shutil.copy2(json_file, backup_file)
            backup_count += 1
    
    print(f"  ✅ Backed up {backup_count} files (*{backup_suffix})\n")


def verify_migration(memory_dir='memory', db_path='data/memory.db'):
    """
    Verify that migration was successful by comparing counts.
    """
    print(f"🔍 Verifying migration...")
    
    try:
        sqlite_memory = SQLiteMemorySystem(db_path)
        stats = sqlite_memory.get_memory_stats()
        
        # Count JSON files
        memory_path = Path(memory_dir)
        json_count = len(list(memory_path.glob('*.json'))) if memory_path.exists() else 0
        
        kv_entries = stats['key_value_store']['entries']
        
        print(f"  JSON files: {json_count}")
        print(f"  SQLite key-value entries: {kv_entries}")
        
        if kv_entries >= json_count:
            print(f"  ✅ Verification passed: {kv_entries} >= {json_count}")
            return True
        else:
            print(f"  ⚠️  Verification warning: {kv_entries} < {json_count}")
            return False
            
    except Exception as e:
        print(f"  ❌ Verification failed: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate AlleyBot memory from JSON to SQLite'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Analyze files without making changes'
    )
    parser.add_argument(
        '--no-backup', action='store_true',
        help='Skip creating backup copies of JSON files'
    )
    parser.add_argument(
        '--memory-dir', default='memory',
        help='Directory containing JSON memory files (default: memory)'
    )
    parser.add_argument(
        '--db-path', default='data/memory.db',
        help='Path for SQLite database (default: data/memory.db)'
    )
    parser.add_argument(
        '--verify', action='store_true',
        help='Verify migration after completion'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print(" AlleyBot Memory Migration Tool")
    print("="*60 + "\n")
    
    # Create backup if not disabled and not dry run
    if not args.no_backup and not args.dry_run:
        backup_json_files(args.memory_dir)
    
    # Run migration
    stats = migrate_json_to_sqlite(
        memory_dir=args.memory_dir,
        db_path=args.db_path,
        dry_run=args.dry_run
    )
    
    # Verify if requested
    if args.verify and not args.dry_run:
        print()
        verify_migration(args.memory_dir, args.db_path)
    
    # Final message
    if args.dry_run:
        print("🔍 Dry run complete. Run without --dry-run to perform actual migration.\n")
    elif stats['errors'] == 0:
        print("✅ Migration completed successfully!\n")
        print("You can now start AlleyBot with the new SQLite memory system.")
        print(f"   python alleybot_core.py autonomous\n")
    else:
        print(f"⚠️  Migration completed with {stats['errors']} errors.\n")
        print("Please review the errors above before starting AlleyBot.\n")


if __name__ == "__main__":
    main()
