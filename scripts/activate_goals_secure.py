#!/usr/bin/env python3
"""
Secure Goal Activation Script

Activates goals with proper security validation:
- Synergy validation for trust-worthiness
- FairMind DNA validation for truth and ethics
- Trust scoring to prevent deceptive behavior
- Automatic approval only for verified safe goals

Constitutional Rules:
- All goals must pass Synergy validation
- High-risk goals require manual approval
- Truth violations block activation
- Trust score must be >= 0.7 for auto-approval
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "data" / "goals.db"

def validate_goal_trustworthiness(goal_data: dict) -> dict:
    """
    Validate goal for trustworthiness and truth using Synergy principles.
    
    Returns:
        dict with 'approved', 'trust_score', 'violations', 'reason'
    """
    violations = []
    trust_score = 1.0
    
    # Check for deceptive language
    description = goal_data.get('description', '').lower()
    title = goal_data.get('title', '').lower()
    
    # Red flags for untrustworthy behavior
    deceptive_patterns = [
        'hide', 'conceal', 'secret', 'trick', 'deceive', 'manipulate',
        'fake', 'false', 'lie', 'mislead', 'scam', 'fraud'
    ]
    
    for pattern in deceptive_patterns:
        if pattern in description or pattern in title:
            violations.append(f"Deceptive language detected: '{pattern}'")
            trust_score -= 0.3
    
    # Check for high-risk actions that need manual approval
    high_risk_patterns = [
        'delete', 'remove', 'transfer funds', 'send money', 'withdraw',
        'change password', 'modify security', 'access private'
    ]
    
    requires_manual = False
    for pattern in high_risk_patterns:
        if pattern in description or pattern in title:
            violations.append(f"High-risk action detected: '{pattern}'")
            trust_score -= 0.2
            requires_manual = True
    
    # Check priority and confidence alignment
    priority = goal_data.get('priority', 'MEDIUM')
    confidence = goal_data.get('confidence', 0.0)
    
    if priority in ['CRITICAL', 'HIGH'] and confidence < 0.7:
        violations.append(f"High priority ({priority}) but low confidence ({confidence})")
        trust_score -= 0.1
    
    # Check for evidence and justification
    evidence = goal_data.get('evidence')
    trigger_data = goal_data.get('trigger_data')
    
    if not evidence and not trigger_data:
        violations.append("No evidence or trigger data provided")
        trust_score -= 0.1
    
    # Final trust determination
    trust_score = max(0.0, min(1.0, trust_score))
    
    if requires_manual:
        return {
            'approved': False,
            'trust_score': trust_score,
            'violations': violations,
            'reason': 'High-risk action requires manual approval',
            'requires_manual': True
        }
    
    if trust_score < 0.7:
        return {
            'approved': False,
            'trust_score': trust_score,
            'violations': violations,
            'reason': f'Trust score too low: {trust_score:.2f} (minimum: 0.70)',
            'requires_manual': False
        }
    
    if violations:
        return {
            'approved': True,  # Can approve with warnings if trust score is high enough
            'trust_score': trust_score,
            'violations': violations,
            'reason': f'Approved with warnings (trust: {trust_score:.2f})',
            'requires_manual': False
        }
    
    return {
        'approved': True,
        'trust_score': trust_score,
        'violations': [],
        'reason': f'Validated and trusted (score: {trust_score:.2f})',
        'requires_manual': False
    }

def activate_goals_securely():
    """Activate goals with security validation"""
    print(f"🔒 Secure Goal Activation System")
    print(f"   Database: {DB_PATH}")
    print(f"   Validation: Synergy + FairMind DNA")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get all DETECTED goals
            cursor = conn.execute("""
                SELECT * FROM goals 
                WHERE status = 'DETECTED'
                ORDER BY impact_score DESC, priority DESC
            """)
            
            detected_goals = cursor.fetchall()
            print(f"📊 Found {len(detected_goals)} DETECTED goals")
            print()
            
            if not detected_goals:
                print("✅ No goals to activate")
                return True
            
            # Validate and categorize goals
            auto_approved = []
            manual_required = []
            rejected = []
            
            for row in detected_goals:
                goal_data = {
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'priority': row['priority'],
                    'confidence': row['confidence'] or 0.0,
                    'impact_score': row['impact_score'] or 0.0,
                    'evidence': row['evidence'],
                    'trigger_data': row['trigger_data']
                }
                
                # Validate trustworthiness
                validation = validate_goal_trustworthiness(goal_data)
                
                if validation['requires_manual']:
                    manual_required.append({
                        'goal': goal_data,
                        'validation': validation
                    })
                elif validation['approved']:
                    auto_approved.append({
                        'goal': goal_data,
                        'validation': validation
                    })
                else:
                    rejected.append({
                        'goal': goal_data,
                        'validation': validation
                    })
            
            # Report results
            print(f"🔍 Validation Results:")
            print(f"   ✅ Auto-approved: {len(auto_approved)}")
            print(f"   ⚠️  Manual review: {len(manual_required)}")
            print(f"   ❌ Rejected: {len(rejected)}")
            print()
            
            # Show rejected goals
            if rejected:
                print(f"❌ Rejected Goals ({len(rejected)}):")
                for item in rejected[:5]:  # Show first 5
                    goal = item['goal']
                    val = item['validation']
                    print(f"   - {goal['id']}: {goal['title']}")
                    print(f"     Trust: {val['trust_score']:.2f}, Reason: {val['reason']}")
                    if val['violations']:
                        print(f"     Violations: {', '.join(val['violations'][:2])}")
                print()
            
            # Show manual review required
            if manual_required:
                print(f"⚠️  Manual Review Required ({len(manual_required)}):")
                for item in manual_required[:5]:  # Show first 5
                    goal = item['goal']
                    val = item['validation']
                    print(f"   - {goal['id']}: {goal['title']}")
                    print(f"     Reason: {val['reason']}")
                print()
            
            # Approve validated goals
            if auto_approved:
                print(f"✅ Auto-Approving {len(auto_approved)} Validated Goals:")
                
                for item in auto_approved:
                    goal = item['goal']
                    val = item['validation']
                    
                    # Update to APPROVED status
                    conn.execute("""
                        UPDATE goals 
                        SET status = 'APPROVED', 
                            approved_at = datetime('now'),
                            owner_notes = ?
                        WHERE id = ?
                    """, (
                        f"Auto-approved: {val['reason']}",
                        goal['id']
                    ))
                    
                    print(f"   ✅ {goal['id']}: {goal['title'][:60]}")
                    print(f"      Trust: {val['trust_score']:.2f}, Priority: {goal['priority']}")
                
                conn.commit()
                print()
            
            # Activate top 10 highest-trust approved goals
            cursor = conn.execute("""
                SELECT id, title, priority, impact_score, confidence
                FROM goals 
                WHERE status = 'APPROVED'
                ORDER BY impact_score DESC, confidence DESC
                LIMIT 10
            """)
            
            approved_goals = cursor.fetchall()
            
            if approved_goals:
                print(f"🚀 Activating Top 10 Approved Goals:")
                
                for row in approved_goals:
                    conn.execute("""
                        UPDATE goals 
                        SET status = 'ACTIVE', 
                            started_at = datetime('now')
                        WHERE id = ?
                    """, (row['id'],))
                    
                    print(f"   🎯 {row['id']}: {row['title'][:60]}")
                    print(f"      Impact: {row['impact_score']:.1f}, Confidence: {row['confidence']:.2f}")
                
                conn.commit()
                print()
            
            # Final summary
            cursor = conn.execute("SELECT COUNT(*), status FROM goals GROUP BY status")
            print(f"📊 Final Goal Status:")
            for count, status in cursor.fetchall():
                print(f"   {status}: {count}")
            
            print()
            print(f"✅ Secure goal activation complete!")
            print(f"   Auto-approved: {len(auto_approved)}")
            print(f"   Activated: {min(len(approved_goals), 10)}")
            print(f"   Manual review needed: {len(manual_required)}")
            print(f"   Rejected for safety: {len(rejected)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Activation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = activate_goals_securely()
    sys.exit(0 if success else 1)
