#!/usr/bin/env python3
"""
Migrate goals database schema from old format to new AGI format.

This script adds missing columns to the goals table to support the new
GoalManager implementation with full AGI capabilities.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "data" / "goals.db"

def migrate_schema():
    """Add missing columns to goals table"""
    print(f"🔄 Migrating goals database schema: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Get existing columns
            cursor = conn.execute("PRAGMA table_info(goals)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            print(f"📊 Found {len(existing_columns)} existing columns")
            
            # Define required columns with defaults
            required_columns = {
                'title': ('TEXT', None),
                'category': ('TEXT', "'general'"),
                'impact_score': ('REAL', '5.0'),
                'effort_estimate': ('TEXT', "'days'"),
                'confidence': ('REAL', '0.7'),
                'trigger_type': ('TEXT', "'manual'"),
                'trigger_data': ('TEXT', "'{}'"),
                'evidence': ('TEXT', "'[]'"),
                'approved_at': ('TEXT', None),
                'started_at': ('TEXT', None),
                'proposed_solution': ('TEXT', None),
                'implementation_plan': ('TEXT', None),
                'actual_effort': ('TEXT', None),
                'outcome': ('TEXT', None),
                'owner_notes': ('TEXT', None),
                'owner_priority_override': ('INTEGER', None),
            }
            
            # Add missing columns
            added = 0
            for col_name, (col_type, default) in required_columns.items():
                if col_name not in existing_columns:
                    default_clause = f" DEFAULT {default}" if default else ""
                    sql = f"ALTER TABLE goals ADD COLUMN {col_name} {col_type}{default_clause}"
                    try:
                        conn.execute(sql)
                        print(f"  ✅ Added column: {col_name}")
                        added += 1
                    except sqlite3.OperationalError as e:
                        print(f"  ⚠️  Column {col_name} already exists or error: {e}")
            
            # Update title from description for existing rows
            if 'title' in required_columns and 'title' not in existing_columns:
                conn.execute("UPDATE goals SET title = description WHERE title IS NULL")
                print(f"  ✅ Populated title from description")
            
            # Convert old priority integers to new priority enum strings
            cursor = conn.execute("SELECT DISTINCT priority FROM goals WHERE typeof(priority) = 'integer'")
            old_priorities = [row[0] for row in cursor.fetchall()]
            
            if old_priorities:
                print(f"  🔄 Converting {len(old_priorities)} old priority values to enum...")
                # Map old integer priorities to new enum values
                # Old: 0-10 scale, New: LOW, MEDIUM, HIGH, CRITICAL
                conn.execute("""
                    UPDATE goals 
                    SET priority = CASE 
                        WHEN CAST(priority AS INTEGER) >= 8 THEN 'CRITICAL'
                        WHEN CAST(priority AS INTEGER) >= 6 THEN 'HIGH'
                        WHEN CAST(priority AS INTEGER) >= 4 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END
                    WHERE typeof(priority) = 'integer'
                """)
                print(f"  ✅ Converted priority values to enum")
            
            # Convert old status values to new enum if needed
            cursor = conn.execute("SELECT DISTINCT status FROM goals")
            statuses = [row[0] for row in cursor.fetchall()]
            
            # Map old statuses to new enum: DETECTED, APPROVED, ACTIVE, COMPLETED, FAILED, CANCELLED
            status_mapping = {
                'pending': 'DETECTED',
                'active': 'ACTIVE',
                'completed': 'COMPLETED',
                'failed': 'FAILED',
                'cancelled': 'CANCELLED'
            }
            
            for old_status, new_status in status_mapping.items():
                if old_status in statuses and old_status.lower() != new_status.lower():
                    conn.execute(
                        "UPDATE goals SET status = ? WHERE status = ?",
                        (new_status, old_status)
                    )
                    print(f"  ✅ Converted status '{old_status}' → '{new_status}'")
            
            conn.commit()
            
            print(f"\n✅ Migration complete!")
            print(f"   Added {added} new columns")
            print(f"   Database ready for new GoalManager")
            
            # Show summary
            cursor = conn.execute("SELECT COUNT(*), status FROM goals GROUP BY status")
            print(f"\n📊 Goals by status:")
            for count, status in cursor.fetchall():
                print(f"   {status}: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_schema()
    sys.exit(0 if success else 1)
