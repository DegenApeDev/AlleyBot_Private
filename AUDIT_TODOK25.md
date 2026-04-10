# AlleyBot Code Audit - Fix Plan (AUDIT_TODOK25)
**Source:** AUDIT_KIMIK25APR.md  
**Created:** April 10, 2026  
**Objective:** Systematic remediation of all audit findings

---

## EXECUTION PHILOSOPHY

> **Fix root causes, not symptoms.**  
> **Test as you go.**  
> **One issue per commit.**

---

## PHASE 0: CRITICAL HOTFIXES (Do First - Before Anything Else)

### [P0-001] Fix Silent Failure Anti-Patterns
**Priority:** CRITICAL  
**Effort:** 4 hours  
**Files:** 28 files with 50+ instances  
**Issue:** Bare `except: pass` and `logger.debug()` swallowing critical errors  

**Tasks:**
- [ ] Run grep to find all bare except clauses: `grep -rn "except:.*pass\|except Exception.*pass" src/agentic/`
- [ ] Replace with specific exception handling in:
  - [ ] `autonomous_brain.py` (3 instances)
  - [ ] `action_router.py` (1 instance)
  - [ ] `agi_kernel.py` (2 instances)
  - [ ] `cross_plugin_orchestrator.py` (1 instance)
  - [ ] `skilldoc_manager.py` (2 instances)
  - [ ] `contextual_awareness.py` (2 instances)
  - [ ] `predictive_suggestions.py` (2 instances)
  - [ ] `social_intelligence.py` (2 instances)
  - [ ] `tool_capability_registry.py` (2 instances)
  - [ ] Plus 15 other files

**Pattern to Apply:**
```python
# BEFORE (bad):
except Exception as e:
    logger.debug(f"Error: {e}")
    pass

# AFTER (good):
except ValueError as e:
    logger.warning(f"Invalid value in X: {e}")
    return default_value
except sqlite3.OperationalError as e:
    logger.error(f"Database error in X: {e}")
    raise  # Critical errors must propagate
except Exception as e:
    logger.error(f"Unexpected error in X: {e}", exc_info=True)
    raise  # Never swallow unknown errors
```

**Acceptance:** All bare except clauses eliminated. Tests still pass.

---

### [P0-002] Fix Async Blocking I/O
**Priority:** CRITICAL  
**Effort:** 4 hours  
**Files:** `autonomous_brain.py`, `persistent_intent.py`, `goal_manager.py`  
**Issue:** SQLite operations block async event loop  

**Tasks:**
- [ ] Identify all blocking SQLite calls in async methods
- [ ] Wrap in thread pool executor:
  ```python
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, blocking_func, args)
  ```
- [ ] Priority locations:
  - [ ] `autonomous_brain.py:_phase_maintain_persistent_intents()` - `intent_mgr.get_ready_intents()`
  - [ ] `autonomous_brain.py:_phase_cross_domain_synthesis_and_planning()` - DB reads
  - [ ] `goal_manager.py` methods called from async context
- [ ] Test: Verify Telegram polling isn't blocked during DB operations

**Acceptance:** Brain cycles don't block other async tasks.

---

### [P0-003] Create BaseSQLiteStore Abstraction
**Priority:** CRITICAL  
**Effort:** 6 hours  
**Files:** New `src/agentic/persistence/base.py`, refactor 5 managers  
**Issue:** Copy-pasted SQLite code across all database modules  

**Tasks:**
- [ ] Create `src/agentic/persistence/__init__.py`
- [ ] Create `BaseSQLiteStore` class:
  ```python
  class BaseSQLiteStore:
      def __init__(self, db_path: str, schema: str)
      def _init_db(self) -> None
      def _execute(self, query: str, params: tuple) -> sqlite3.Cursor
      def _fetchone(self, query: str, params: tuple) -> Optional[Row]
      def _fetchall(self, query: str, params: tuple) -> List[Row]
  ```
- [ ] Refactor to use base class:
  - [ ] `goal_manager.py` - GoalManager extends BaseSQLiteStore
  - [ ] `owner_objectives.py` - OwnerObjectivesManager extends BaseSQLiteStore
  - [ ] `persistent_intent.py` - PersistentIntentManager extends BaseSQLiteStore
  - [ ] `strategic_planner.py` - StrategicPlanner extends BaseSQLiteStore
  - [ ] `cross_domain_synthesis.py` - CrossDomainSynthesizer extends BaseSQLiteStore
- [ ] Add migration helper method to base class
- [ ] Verify all existing data remains accessible

**Acceptance:** 200+ lines of duplication eliminated. All tests pass.

---

## PHASE 1: SECURITY HARDENING

### [P1-001] Add Input Validation to Dataclasses
**Priority:** HIGH  
**Effort:** 3 hours  
**Files:** `persistent_intent.py`, `owner_objectives.py`, `strategic_planner.py`  
**Issue:** No validation on field values  

**Tasks:**
- [ ] Add `__post_init__` to `PersistentIntent`:
  - [ ] Validate `cooldown_hours >= 0`
  - [ ] Validate `1 <= priority <= 10`
  - [ ] Validate `max_daily_actions > 0`
- [ ] Add `__post_init__` to `OwnerObjective`:
  - [ ] Validate `priority` range
  - [ ] Validate `objective_type` is in allowed set
- [ ] Add `__post_init__` to `StrategicPlan`:
  - [ ] Validate `horizon_days > 0`
  - [ ] Validate milestones have valid dates
- [ ] Add tests for validation errors

**Acceptance:** Invalid data raises ValueError with clear message.

---

### [P1-002] Fix ActionRouter Validation Enforcement
**Priority:** HIGH  
**Effort:** 2 hours  
**File:** `action_router.py`  
**Issue:** Validation stages may be skipped  

**Tasks:**
- [ ] Add `self._validate_stage_execution()` method
- [ ] Track executed stages in `route_action()`
- [ ] Assert all required stages completed before execution
- [ ] Log warning if any stage skipped
- [ ] Add test: Verify all 12 stages execute for sample action

**Acceptance:** ActionRouter enforces complete validation ladder.

---

### [P1-003] Add Path Traversal Protection
**Priority:** MEDIUM  
**Effort:** 1 hour  
**Files:** All modules with `db_path` parameter  
**Issue:** Potential path traversal if db_path from user input  

**Tasks:**
- [ ] Add path validation helper:
  ```python
  def validate_db_path(path: str, allowed_base: str = 'data/') -> Path:
      p = Path(path).resolve()
      base = Path(allowed_base).resolve()
      if not str(p).startswith(str(base)):
          raise ValueError(f"Path {path} outside allowed directory {allowed_base}")
      return p
  ```
- [ ] Apply to all database-using modules
- [ ] Add test for path traversal attempt

**Acceptance:** Path outside `data/` rejected with clear error.

---

## PHASE 2: CODE QUALITY IMPROVEMENTS

### [P2-001] Decompose autonomous_brain.py God Class
**Priority:** MEDIUM  
**Effort:** 8 hours  
**File:** `autonomous_brain.py` (3,195 lines → target: <500 lines each)  
**Issue:** Single file violates SRP, contains 15+ phases  

**New Structure:**
```
src/agentic/brain/
├── __init__.py              # Re-export AutonomousBrain
├── core.py                  # AutonomousBrain class (~400 lines)
├── config.py                # BrainConfig dataclass
├── phases/
│   ├── __init__.py
│   ├── sense.py             # _phase_sense, _gather_observations
│   ├── think.py             # _phase_decide, _phase_skill_gap_analysis
│   ├── act.py               # _phase_assemble_proposals, _phase_execute_proposals
│   ├── reflect.py           # _phase_reflect, _phase_meta_learn
│   ├── goals.py             # _phase_goal_management
│   ├── persistent.py        # _phase_maintain_persistent_intents
│   └── strategy.py          # _phase_cross_domain_synthesis_and_planning
└── coordination/
    ├── __init__.py
    ├── proposal_assembler.py
    └── action_executor.py
```

**Tasks:**
- [ ] Create new directory structure
- [ ] Extract `BrainConfig` to `config.py`
- [ ] Extract phase methods to respective modules
- [ ] Use dependency injection for shared dependencies (agi_kernel, plugin_manager)
- [ ] Update imports in dependent files
- [ ] Verify no circular imports
- [ ] Run full test suite

**Acceptance:** Each file <500 lines. All tests pass.

---

### [P2-002] Replace Print Statements with Logging
**Priority:** MEDIUM  
**Effort:** 2 hours  
**Files:** `src/agentic/*.py`  
**Issue:** Library code uses print() instead of logger  

**Tasks:**
- [ ] Find all print statements: `grep -rn "print(" src/agentic/*.py`
- [ ] Replace with appropriate log level:
  - [ ] Startup messages → `logger.info()`
  - [ ] Debug info → `logger.debug()`
  - [ ] Errors → `logger.error()`
- [ ] Keep prints only in CLI entry points (`alleybot_core.py`, `web_server.py`)

**Acceptance:** Zero print statements in `src/agentic/` (except __main__ blocks).

---

### [P2-003] Remove Dead Code and Unused Imports
**Priority:** LOW  
**Effort:** 1 hour  
**Files:** All new AGI files  
**Issue:** Unused imports cluttering codebase  

**Tasks:**
- [ ] Run `vulture src/agentic/` or `pylint --enable=unused-imports`
- [ ] Remove unused imports:
  - [ ] `persistent_intent.py:14` - `from typing import Set`
  - [ ] `autonomous_brain.py:19` - `import os` (used once)
- [ ] Remove unreachable code
- [ ] Verify with tests

**Acceptance:** Clean import sections, no linter warnings.

---

### [P2-004] Extract Magic Numbers to Constants
**Priority:** LOW  
**Effort:** 2 hours  
**Files:** `autonomous_brain.py`, `goal_manager.py`  
**Issue:** Hardcoded values scattered throughout  

**Tasks:**
- [ ] Create `src/agentic/config/constants.py`:
  ```python
  class BrainLimits:
      MAX_ACTIONS_PER_HOUR = 50
      MIN_GOALS_PER_HOUR = 3
      MIN_CONFIDENCE = 0.35
      COOLDOWN_HOURS_DEFAULT = 6.0
  
  class GoalLimits:
      AUTO_APPROVAL_FAILURE_THRESHOLD = 3
      DUPLICATE_WINDOW_DAYS = 7
  
  class IntentLimits:
      MAX_DAILY_ACTIONS_DEFAULT = 3
      PRIORITY_DEFAULT = 5
  ```
- [ ] Replace all magic numbers with constants
- [ ] Update BrainConfig to reference constants

**Acceptance:** No raw numbers in business logic (except 0, 1, -1).

---

## PHASE 3: ERROR HANDLING & RESILIENCE

### [P3-001] Add Retry Logic with Exponential Backoff
**Priority:** HIGH  
**Effort:** 4 hours  
**Files:** External API callers  
**Issue:** No retry on transient failures  

**Tasks:**
- [ ] Create `src/agentic/utils/retry.py`:
  ```python
  from functools import wraps
  import asyncio
  
  def retry_async(max_attempts=3, backoff_base=1, max_backoff=10):
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              for attempt in range(max_attempts):
                  try:
                      return await func(*args, **kwargs)
                  except (ConnectionError, TimeoutError) as e:
                      if attempt == max_attempts - 1:
                          raise
                      wait = min(backoff_base * (2 ** attempt), max_backoff)
                      logger.warning(f"Retry {attempt+1}/{max_attempts} after {wait}s: {e}")
                      await asyncio.sleep(wait)
          return wrapper
      return decorator
  ```
- [ ] Apply to:
  - [ ] MoltX API calls
  - [ ] Telegram API calls
  - [ ] Web3 RPC calls
- [ ] Add tests for retry behavior

**Acceptance:** Transient failures retried automatically.

---

### [P3-002] Implement Circuit Breaker Pattern
**Priority:** MEDIUM  
**Effort:** 3 hours  
**Files:** External service integrations  
**Issue:** Continuous calls to failing services  

**Tasks:**
- [ ] Create `src/agentic/utils/circuit_breaker.py`:
  ```python
  class CircuitBreaker:
      CLOSED = 'closed'      # Normal operation
      OPEN = 'open'          # Failing, reject fast
      HALF_OPEN = 'half_open'  # Testing recovery
      
      def __init__(self, failure_threshold=5, recovery_timeout=60):
          self.failure_threshold = failure_threshold
          self.recovery_timeout = recovery_timeout
          self.state = self.CLOSED
          self.failure_count = 0
          self.last_failure_time = None
  ```
- [ ] Integrate with external service wrappers
- [ ] Add health check endpoint monitoring
- [ ] Log state transitions

**Acceptance:** Service fails fast after threshold, recovers after timeout.

---

### [P3-003] Add Graceful Degradation for Plugins
**Priority:** MEDIUM  
**Effort:** 2 hours  
**Files:** `autonomous_brain.py`, `action_router.py`  
**Issue:** No health checks before using plugins  

**Tasks:**
- [ ] Add health check interface to plugins
- [ ] Check plugin health before use:
  ```python
  if moltx and moltx.is_healthy() and agi_kernel:
  ```
- [ ] Degrade gracefully: skip plugin-dependent phases if unhealthy
- [ ] Notify owner of degraded state

**Acceptance:** Brain continues operating with reduced functionality if plugins fail.

---

## PHASE 4: AI/AGENT-SPECIFIC IMPROVEMENTS

### [P4-001] Implement Context Window Management
**Priority:** HIGH  
**Effort:** 4 hours  
**Files:** `autonomous_brain.py`, `agi_kernel.py`  
**Issue:** Unbounded context growth  

**Tasks:**
- [ ] Add context size tracking
- [ ] Implement sliding window for observations (keep last 100)
- [ ] Add context summarization for old items
- [ ] Evict low-relevance items based on scoring
- [ ] Add metrics: context_size, evicted_items, summarized_items

**Acceptance:** Context stays bounded (<1000 items). Relevant info retained.

---

### [P4-002] Optimize Token Usage in Goal Generation
**Priority:** MEDIUM  
**Effort:** 3 hours  
**Files:** `agi_orchestrator.py`  
**Issue:** All observations processed every cycle (O(N))  

**Tasks:**
- [ ] Pre-filter observations by relevance score
- [ ] Use embedding similarity to owner objectives
- [ ] Prioritize recent high-impact observations
- [ ] Batch process observations (don't send one-by-one)
- [ ] Add token usage metrics

**Acceptance:** Token usage reduced 50% without quality loss.

---

### [P4-003] Add Prediction Validation
**Priority:** MEDIUM  
**Effort:** 2 hours  
**Files:** `action_router.py`  
**Issue:** Predictions not sanity-checked  

**Tasks:**
- [ ] Add prediction bounds checking:
  - [ ] Success probability must be 0-1
  - [ ] Expected value must be reasonable magnitude
  - [ ] Confidence must correlate with evidence
- [ ] Flag outlier predictions for review
- [ ] Log prediction accuracy over time

**Acceptance:** Unreasonable predictions flagged before execution.

---

## PHASE 5: DEPENDENCIES & TESTING

### [P5-001] Upgrade LangChain Dependencies
**Priority:** MEDIUM  
**Effort:** 2 hours  
**Files:** `requirements.txt`  
**Issue:** Outdated langchain (0.1.x vs current 0.3.x)  

**Tasks:**
- [ ] Update constraints:
  ```
  langchain>=0.3.0,<0.4.0
  langchain-community>=0.3.0,<0.4.0
  ```
- [ ] Test for breaking changes
- [ ] Update import paths if changed
- [ ] Run full test suite

**Acceptance:** All tests pass with latest langchain.

---

### [P5-002] Add Comprehensive Tests for New AGI Components
**Priority:** HIGH  
**Effort:** 8 hours  
**Files:** `tests/test_owner_objectives.py`, `test_persistent_intent.py`, etc.  
**Issue:** Zero tests for TODO_KIMI_K25 components  

**Tasks:**
- [ ] `tests/test_owner_objectives.py`:
  - [ ] Test CRUD operations
  - [ ] Test engagement preferences
  - [ ] Test objective scoring
  - [ ] Test database migrations
- [ ] `tests/test_persistent_intent.py`:
  - [ ] Test intent lifecycle (create → update → complete)
  - [ ] Test cooldown enforcement
  - [ ] Test daily action caps
  - [ ] Test action generation
- [ ] `tests/test_strategic_planner.py`:
  - [ ] Test plan creation
  - [ ] Test milestone advancement
  - [ ] Test adaptive replanning
  - [ ] Test plan decomposition into intents
- [ ] `tests/test_cross_domain_synthesis.py`:
  - [ ] Test pattern detection
  - [ ] Test scoring algorithm
  - [ ] Test database persistence
  - [ ] Test opportunity ranking

**Acceptance:** >80% coverage on new files.

---

### [P5-003] Add Negative/Failure Path Tests
**Priority:** MEDIUM  
**Effort:** 4 hours  
**Files:** `tests/test_integration_opus.py`  
**Issue:** Only happy paths tested  

**Tasks:**
- [ ] Test database locked errors
- [ ] Test plugin unavailable scenarios
- [ ] Test validation stage failures
- [ ] Test auto-approval safety valve (3+ failures)
- [ ] Test circuit breaker triggers
- [ ] Test retry exhaustion

**Acceptance:** All critical failure paths have tests.

---

### [P5-004] Add Load/Stress Tests
**Priority:** MEDIUM  
**Effort:** 3 hours  
**Files:** `tests/test_stress.py`  
**Issue:** No verification of resource bounds  

**Tasks:**
- [ ] Mock plugins for fast execution
- [ ] Run 1000 brain cycles
- [ ] Monitor memory usage (must stay bounded)
- [ ] Verify 50 actions/hour doesn't exhaust resources
- [ ] Test with 1000+ goals in database
- [ ] Test with 100+ persistent intents

**Acceptance:** Memory stable after 1000 cycles. No OOM.

---

## PHASE 6: MONITORING & OBSERVABILITY

### [P6-001] Add Prometheus Metrics
**Priority:** MEDIUM  
**Effort:** 3 hours  
**Files:** `src/agentic/metrics.py`  
**Issue:** No visibility into production behavior  

**Tasks:**
- [ ] Create metrics module with counters:
  - [ ] `brain_cycles_total` - Total cycles run
  - [ ] `actions_executed_total` - Actions by result
  - [ ] `goals_completed_total` - Goals by status
  - [ ] `validation_failures_total` - Failures by stage
  - [ ] `db_query_duration_seconds` - Query latency
  - [ ] `context_size` - Current observation count
- [ ] Add gauge for active intents, pending goals
- [ ] Export endpoint on `/metrics`

**Acceptance:** Metrics visible at `localhost:7000/metrics`.

---

### [P6-002] Add Health Check Endpoint
**Priority:** LOW  
**Effort:** 1 hour  
**Files:** `web_server.py`  
**Issue:** No way to verify system health  

**Tasks:**
- [ ] Add `/health` endpoint
- [ ] Check database connectivity
- [ ] Check critical plugins health
- [ ] Return JSON: `{"status": "healthy", "checks": {...}}`
- [ ] Return 503 if degraded

**Acceptance:** Health endpoint returns comprehensive status.

---

### [P6-003] Add Structured Logging
**Priority:** LOW  
**Effort:** 2 hours  
**Files:** All modules  
**Issue:** Logs are plain text, hard to parse  

**Tasks:**
- [ ] Configure JSON formatter for logs
- [ ] Add correlation IDs to track requests
- [ ] Add structured context (goal_id, intent_id, etc.)
- [ ] Centralize log aggregation config

**Acceptance:** Logs parseable by log aggregation tools.

---

## ROLLBACK PLAN

For each phase, maintain ability to revert:

1. **Database migrations:** Backup before schema changes
2. **Architecture changes:** Keep old imports working during transition
3. **Dependency upgrades:** Pin previous versions in `requirements.txt.backup`

---

## COMPLETION CRITERIA

All phases complete when:
- [ ] Zero bare except clauses
- [ ] All new AGI components have >80% test coverage
- [ ] No blocking I/O in async context
- [ ] Database code consolidated in base class
- [ ] All CI checks pass (lint, type check, test)
- [ ] Load tests pass (1000 cycles, stable memory)
- [ ] Documentation updated

---

## TIME ESTIMATES

| Phase | Effort | Cumulative |
|-------|--------|------------|
| P0 Critical | 14 hours | 14 hours |
| P1 Security | 6 hours | 20 hours |
| P2 Quality | 13 hours | 33 hours |
| P3 Resilience | 9 hours | 42 hours |
| P4 AI/Agent | 9 hours | 51 hours |
| P5 Testing | 17 hours | 68 hours |
| P6 Observability | 6 hours | 74 hours |

**Total Estimated:** ~74 hours (9 days @ 8h/day)

---

## RECOMMENDED ORDER

**Week 1:** P0 (Critical) + P1-001 (Validation)  
**Week 2:** P2-001 (Decompose) + P3-001 (Retry)  
**Week 3:** P5-002 (Tests) + P4-001 (Context)  
**Week 4:** Remaining items + polish

---

**Start with P0-001 (Silent Failures). That single issue is masking all other problems.**
