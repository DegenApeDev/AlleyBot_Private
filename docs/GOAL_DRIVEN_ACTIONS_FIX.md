# Goal-Driven Actions Fix

**Problem:** AlleyBot wasn't executing actions based on goals despite having 951 pending goals in the database.

**Root Cause:** Database schema mismatch between old goal system and new AGI GoalManager.

---

## The Issue

### **Symptoms:**
- AlleyBot not taking many actions
- Errors when attempting to execute
- Terminal shows: `⚠️ No active goals in context`
- 951 goals stuck in database unable to be loaded

### **Root Cause:**

The old goal system used a simple schema:
```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    description TEXT,
    priority INTEGER,  -- Simple 0-10 scale
    status TEXT,       -- 'pending', 'completed'
    ...
)
```

The new AGI GoalManager expects a rich schema:
```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    category TEXT,
    priority TEXT,              -- Enum: LOW, MEDIUM, HIGH, CRITICAL
    impact_score REAL,
    effort_estimate TEXT,
    confidence REAL,
    trigger_type TEXT,
    trigger_data TEXT,
    evidence TEXT,
    status TEXT,                -- Enum: DETECTED, APPROVED, ACTIVE, COMPLETED, FAILED, CANCELLED
    implementation_plan TEXT,   -- JSON array of steps
    ...
)
```

**Result:** GoalManager couldn't load goals → No goal-driven actions → AlleyBot inactive

---

## The Fix

### **Migration Script:** `scripts/migrate_goals_schema.py`

**What it does:**
1. Adds 16 missing columns to goals table
2. Populates `title` from `description`
3. Converts old integer priorities (0-10) to enum (LOW/MEDIUM/HIGH/CRITICAL)
4. Converts old status values ('pending') to new enum ('DETECTED')
5. Sets sensible defaults for new columns

**Migration Results:**
```
✅ Added 4 new columns
✅ Converted priority values to enum
✅ Converted status 'pending' → 'DETECTED'

📊 Goals by status:
   DETECTED: 951
   completed: 3
```

---

## How Goal→Action Pipeline Works

### **1. Brain Loop Checks for Goals**

Every cycle, the brain loop:
```python
# Get active goals
active_goals = goal_manager.get_goals(status=GoalStatus.ACTIVE, limit=5)

if active_goals:
    # Get next action for highest priority goal
    for goal in sorted(active_goals, key=lambda g: g.impact_score, reverse=True):
        next_action = goal_manager.get_next_action_for_goal(goal)
        if next_action:
            goal_driven_action = next_action
            break

# If no active goals, scan for new opportunities
if not active_goals:
    new_goals = goal_manager.scan_and_generate(onchain_plugin=onchain_plugin)
```

### **2. GoalManager Converts Goals to Actions**

```python
def get_next_action_for_goal(self, goal: Goal) -> Optional[Dict]:
    # Get implementation plan
    plan_steps = goal.implementation_plan or self._generate_basic_plan(goal)
    
    # Find next incomplete step
    for step in plan_steps:
        if step['status'] != 'completed':
            # Convert step to action
            action = self._step_to_action(step, goal)
            return action
```

### **3. Step→Action Conversion**

```python
def _step_to_action(self, step: Dict, goal: Goal) -> Dict:
    description = step['description'].lower()
    
    # Map keywords to actions
    if 'analyze' in description:
        return {'action_type': 'analyze', 'plugin': 'brain', ...}
    elif 'post' in description:
        return {'action_type': 'post', 'plugin': 'moltx', ...}
    elif 'trade' in description:
        return {'action_type': 'trade', 'plugin': 'onchain', ...}
```

### **4. Action Execution**

```python
# Add goal-driven action as high-priority proposal
if goal_driven_action:
    goal_proposal = SyModActionProposal(
        action_type=goal_driven_action['action_type'],
        confidence=0.85,  # High confidence for goal-driven
        justification=f"Pursuing active goal: {goal.title}"
    )
    proposals.insert(0, goal_proposal)  # Priority position
```

---

## What This Enables

### **Before Fix:**
```
Brain Cycle:
→ Check for goals: ❌ Schema mismatch, can't load
→ No goals found
→ Scan for opportunities: ❌ Can't create new goals (schema mismatch)
→ Fall back to random proposals
→ Limited action execution
```

### **After Fix:**
```
Brain Cycle:
→ Check for goals: ✅ Load 951 DETECTED goals
→ Auto-approve high-priority goals (priority >= 8, confidence >= 0.8)
→ Get next action for top goal
→ Generate implementation plan if missing
→ Convert plan step to executable action
→ Execute action via ActionRouter
→ Mark step complete, move to next
→ Complete goal when all steps done
```

---

## Goal Status Flow

```
DETECTED (951 goals)
    ↓
    Auto-approve if: priority >= 8 AND confidence >= 0.8
    Manual approve via: /approve_goal [id]
    ↓
APPROVED
    ↓
    Start execution (first action)
    ↓
ACTIVE
    ↓
    Execute implementation plan steps
    ↓
COMPLETED / FAILED / CANCELLED
```

---

## Example: Goal Execution

**Goal:** "Improve engagement on MoltX"

**Implementation Plan:**
```json
[
  {"description": "Analyze current MoltX performance", "status": "pending"},
  {"description": "Identify optimization opportunities", "status": "pending"},
  {"description": "Implement improvements", "status": "pending"},
  {"description": "Test and validate results", "status": "pending"}
]
```

**Execution Flow:**

**Cycle 1:**
```
→ Get next action for goal
→ Step 1: "Analyze current MoltX performance"
→ Convert to action: {'action_type': 'analyze', 'plugin': 'brain', 'params': {'topic': 'moltx performance'}}
→ Execute via ActionRouter
→ Mark step 1 as 'completed'
```

**Cycle 2:**
```
→ Get next action for goal
→ Step 2: "Identify optimization opportunities"
→ Convert to action: {'action_type': 'analyze', 'plugin': 'brain', 'params': {'topic': 'optimization opportunities'}}
→ Execute via ActionRouter
→ Mark step 2 as 'completed'
```

**Cycle 3:**
```
→ Get next action for goal
→ Step 3: "Implement improvements"
→ Convert to action: {'action_type': 'post', 'plugin': 'moltx', 'params': {'topic': 'Improve engagement on MoltX'}}
→ Execute via ActionRouter
→ Mark step 3 as 'completed'
```

**Cycle 4:**
```
→ Get next action for goal
→ Step 4: "Test and validate results"
→ Convert to action: {'action_type': 'analyze', 'plugin': 'brain', 'params': {'topic': 'test and validate results'}}
→ Execute via ActionRouter
→ Mark step 4 as 'completed'
→ All steps complete → Mark goal as COMPLETED
```

---

## Running the Migration

**If you need to run it again:**

```bash
# Stop AlleyBot first
python scripts/migrate_goals_schema.py
```

**Output:**
```
🔄 Migrating goals database schema
📊 Found 23 existing columns
  ✅ Added column: proposed_solution
  ✅ Added column: actual_effort
  ✅ Added column: owner_notes
  ✅ Added column: owner_priority_override
  🔄 Converting old priority values to enum
  ✅ Converted priority values to enum
  ✅ Converted status 'pending' → 'DETECTED'

✅ Migration complete!
   Database ready for new GoalManager

📊 Goals by status:
   DETECTED: 951
   completed: 3
```

---

## Next Steps

1. **Restart AlleyBot** - Goals will now load properly
2. **Monitor terminal** - Look for `🎯 Goal-driven action:` messages
3. **Approve high-value goals** - Use `/approve_goal [id]` for manual approval
4. **Watch execution** - AlleyBot will work through implementation plans

---

## Key Files

- **Migration Script:** `scripts/migrate_goals_schema.py`
- **GoalManager:** `src/agentic/goal_manager.py`
- **Brain Loop:** `src/agentic/autonomous_brain.py` (lines 842-876)
- **Database:** `data/goals.db`

---

**Status:** ✅ Fixed  
**Date:** March 26, 2026  
**Impact:** AlleyBot can now execute goal-driven actions autonomously
