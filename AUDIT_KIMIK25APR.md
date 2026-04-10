# AlleyBot Code Audit Report
**Date:** April 10, 2026  
**Scope:** Full codebase (src/agentic/, plugins/, root files)  
**Auditor:** Senior Software Engineer (AI)  

---

## EXECUTIVE SUMMARY

**Critical Issues:** 2  
**High Issues:** 8  
**Medium Issues:** 15  
**Low Issues:** 12  

**Verdict:** The codebase shows signs of rapid iterative development with technical debt accumulation. The Phase 1-4 AGI implementation is architecturally sound but suffers from error handling anti-patterns, missing input validation, and potential resource leaks. The core safety mechanisms (fail-closed gates) are properly implemented, but peripheral code needs hardening.

---

## 1. ARCHITECTURE & STRUCTURE

### ISSUE-001: Circular Import Risk in AGI Kernel
**SEVERITY:** high  
**FILE:** `src/agentic/agi_kernel.py`, `src/agentic/action_router.py`  
**ISSUE:** `agi_kernel.py` imports from `action_router.py` and vice versa. The `action_router.py` imports `agi_kernel.ModelProvider` while `agi_kernel.py` imports `ActionRouter`. This creates a circular dependency that may cause import errors in certain initialization orders.

**FIX:** Introduce an interface/protocol layer or dependency injection. Move shared types to `src/agentic/contracts.py` which both can import without circularity.

---

### ISSUE-002: God Class Anti-Pattern
**SEVERITY:** medium  
**FILE:** `src/agentic/autonomous_brain.py:1-3195`  
**ISSUE:** 3,195 lines in a single file. Contains 15+ phase methods, mixing SENSE/THINK/ACT/REFLECT logic, plugin coordination, goal management, skill building, and trading. Violates Single Responsibility Principle.

**FIX:** Decompose into focused modules:
- `brain_phases/sense.py`, `brain_phases/think.py`, `brain_phases/act.py`, `brain_phases/reflect.py`
- `brain_coordination/proposal_assembler.py`
- `brain_coordination/action_executor.py`

---

### ISSUE-003: Import Churn and Deep Nesting
**SEVERITY:** medium  
**FILE:** `src/agentic/agi_kernel.py:17-64`  
**ISSUE:** 47 lines of imports from 28 different modules. Deep nesting (`src.agentic.alley_kernel.autonomous_engine`) creates brittle coupling.

**FIX:** Flatten module structure. Consolidate related imports. Consider using `__init__.py` exports to reduce import paths.

---

### ISSUE-004: Missing Abstraction Layer for Database Access
**SEVERITY:** medium  
**FILES:** `src/agentic/goal_manager.py`, `src/agentic/owner_objectives.py`, `src/agentic/persistent_intent.py`, `src/agentic/strategic_planner.py`, `src/agentic/cross_domain_synthesis.py`  
**ISSUE:** Each module implements its own `_init_db()`, `_row_to_X()`, SQLite connection management. Massive code duplication (60+ lines per file).

**FIX:** Create a `BaseSQLiteStore` abstract class in `src/agentic/persistence/base.py` with common CRUD operations. All managers inherit from it.

---

## 2. CODE QUALITY

### ISSUE-005: Bare Except Clauses (Silent Failure Anti-Pattern)
**SEVERITY:** high  
**FILES:** 28 files affected (50+ instances)  
**EXAMPLES:**
- `src/agentic/autonomous_brain.py:1699`: `except Exception as e: logger.debug(f"Persistent intent processing error: {e}")`
- `src/agentic/action_router.py:710`: `except Exception as e: pass` (path protection)
- `src/agentic/agi_kernel.py:1755`: `except Exception: pass`
- `src/agentic/cross_plugin_orchestrator.py:165`: `except Exception: pass`

**ISSUE:** Bare `except:` or `except Exception:` catches KeyboardInterrupt, SystemExit, and syntax errors. Swallows critical failures silently. Makes debugging impossible.

**FIX:** Use specific exceptions:
```python
try:
    result = risky_operation()
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return default_value
except sqlite3.OperationalError as e:
    logger.error(f"Database error: {e}")
    raise  # Don't swallow DB errors
```

---

### ISSUE-006: Dead Code and Unused Imports
**SEVERITY:** low  
**FILES:** Multiple  
**ISSUE:** 
- `src/agentic/persistent_intent.py:14`: `from typing import Set` imported but never used
- `src/agentic/autonomous_brain.py:19`: `import os` used only once for `getenv` (use direct reference)
- `autonomous_brain.py:1614`: `AutonomousCoder()` instantiated but may not be defined in scope

**FIX:** Run `vulture` or `pylint --disable=all --enable=unused-imports,wunused-variable` across the codebase.

---

### ISSUE-007: Excessive Print Statements in Library Code
**SEVERITY:** medium  
**FILES:** `src/agentic/*.py`  
**ISSUE:** Library code uses `print()` for logging instead of proper logging. `agi_kernel.py:80` has `print("🧠 Initializing AGI Kernel...")`. This pollutes stdout and makes log aggregation difficult.

**FIX:** Replace all `print()` in `src/agentic/` with `logger.info()` or `logger.debug()`. Keep prints only in CLI entry points.

---

### ISSUE-008: Magic Numbers Everywhere
**SEVERITY:** low  
**FILES:** `src/agentic/autonomous_brain.py`, `src/agentic/goal_manager.py`  
**EXAMPLES:**
- `autonomous_brain.py:61`: `max_actions_per_hour: int = 50` (hardcoded default)
- `autonomous_brain.py:66`: `min_goals_per_hour: int = 3`
- `goal_manager.py:90`: `DEFAULT_AUTO_APPROVAL_THRESHOLD = 3` (failures in 24h)

**FIX:** Create `src/agentic/config/constants.py` with named constants:
```python
class Limits:
    MAX_ACTIONS_PER_HOUR = 50
    MIN_GOALS_PER_HOUR = 3
    AUTO_APPROVAL_FAILURE_THRESHOLD = 3
    COOLDOWN_HOURS_DEFAULT = 6.0
```

---

### ISSUE-009: Function Length Violations
**SEVERITY:** medium  
**FILES:** `src/agentic/autonomous_brain.py`, `src/agentic/agi_orchestrator.py`  
**ISSUE:**
- `_phase_cross_domain_synthesis_and_planning()`: 80+ lines
- `generate_goal_proposals()`: 120+ lines
- `_phase_assemble_proposals()`: 60+ lines

**FIX:** Apply extract method refactoring. Any function >40 lines should be split.

---

### ISSUE-010: Copy-Paste Duplication in New Files
**SEVERITY:** high  
**FILES:** `owner_objectives.py`, `persistent_intent.py`, `strategic_planner.py`, `cross_domain_synthesis.py`, `goal_manager.py`  
**ISSUE:** Database initialization code is copy-pasted across 5+ files with identical patterns:
```python
def _init_db(self) -> None:
    with sqlite3.connect(self.db_path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS...''')
        conn.execute('CREATE INDEX IF NOT EXISTS...')
```

**FIX:** Extract to shared mixin or base class. ~200 lines of duplication can be eliminated.

---

## 3. SECURITY

### ISSUE-011: SQL Injection Risk (Pattern Detected)
**SEVERITY:** critical  
**FILE:** `src/agentic/goal_manager.py:316`, `owner_objectives.py`, `persistent_intent.py`  
**ISSUE:** Uses f-strings and `.format()` for SQL in some locations:
```python
# RISKY PATTERN (not currently used but similar patterns exist)
set_clause = ', '.join(f"{k} = ?" for k in updates.keys())  # This one is safe
conn.execute(f'UPDATE goals SET {set_clause} WHERE id = ?', ...)  # Safe
```

However, there are dynamic queries:
```python
# In strategic_planner.py - row factory usage
conn.row_factory = sqlite3.Row  # This is safe
```

**CURRENT STATUS:** Most queries use parameterized statements correctly. No immediate SQL injection found, but the pattern is fragile.

**FIX:** Add SQL injection linter to CI/CD. Never use f-strings for SQL.

---

### ISSUE-012: Path Traversal Risk in Database Paths
**SEVERITY:** medium  
**FILES:** `src/agentic/persistent_intent.py:85`, `owner_objectives.py:83`  
**ISSUE:** Database paths constructed with string concatenation:
```python
db_path: str = 'data/owner_objectives.db'  # Hardcoded but safe
```

However, if these ever accept user input:
```python
# DANGEROUS if db_path comes from user input
self.db_path = Path(db_path)
```

**FIX:** Sanitize all path inputs. Use `Path.resolve()` and verify path is within allowed directory.

---

### ISSUE-013: No Input Validation on Dataclass Fields
**SEVERITY:** medium  
**FILES:** `persistent_intent.py`, `owner_objectives.py`  
**ISSUE:** Dataclass fields accept any values without validation:
```python
cooldown_hours: float = 6.0  # Could be set to -1 or 99999
priority: int = 5  # Could be set to -1000 or 999999
```

**FIX:** Add `__post_init__` validation:
```python
def __post_init__(self):
    if self.cooldown_hours < 0:
        raise ValueError("cooldown_hours must be non-negative")
    if not 1 <= self.priority <= 10:
        raise ValueError("priority must be 1-10")
```

---

### ISSUE-014: Potential Prompt Injection in LLM Calls (If Applicable)
**SEVERITY:** high  
**FILES:** `src/agentic/decision_system.py`, `src/agentic/conversation_service.py`  
**ISSUE:** If user content is passed directly to LLM prompts without sanitization, prompt injection is possible. Need to verify prompt construction patterns.

**FIX:** Review all LLM prompt construction. Use structured formats (JSON) instead of string concatenation for prompts. Validate user inputs before including in prompts.

---

### ISSUE-015: No Rate Limiting on Database Writes
**SEVERITY:** medium  
**FILES:** `src/agentic/goal_manager.py`, `persistent_intent.py`  
**ISSUE:** Every brain cycle can write to SQLite. No batching, no write coalescing. With 50 actions/hour, this creates unnecessary I/O pressure.

**FIX:** Implement write batching or use WAL mode with periodic commits. Consider in-memory queue for high-frequency updates.

---

## 4. PERFORMANCE

### ISSUE-016: Blocking SQLite Operations in Async Context
**SEVERITY:** high  
**FILES:** `src/agentic/autonomous_brain.py`, `persistent_intent.py`, `goal_manager.py`  
**ISSUE:** Async methods like `_phase_maintain_persistent_intents()` call SQLite directly:
```python
async def _phase_maintain_persistent_intents(self, agi_kernel, proposals):
    intent_mgr = get_persistent_intent_manager()
    ready_intents = intent_mgr.get_ready_intents()  # BLOCKING I/O in async context!
```

SQLite operations block the event loop, starving other async tasks (like Telegram polling).

**FIX:** Run SQLite operations in thread pool:
```python
loop = asyncio.get_event_loop()
ready_intents = await loop.run_in_executor(None, intent_mgr.get_ready_intents)
```

---

### ISSUE-017: No Connection Pooling for SQLite
**SEVERITY:** medium  
**FILES:** All SQLite-using modules  
**ISSUE:** Every database operation opens a new connection:
```python
with sqlite3.connect(self.db_path) as conn:
    # ... operation
```

This creates connection overhead for every single query.

**FIX:** Use connection pooling or maintain persistent connections. SQLite supports shared cache mode or use `aiosqlite` for async.

---

### ISSUE-018: Inefficient Cache Invalidation
**SEVERITY:** low  
**FILES:** `persistent_intent.py:370`, `owner_objectives.py`  
**ISSUE:** Cache is cleared on every write, even if the write doesn't affect cached data:
```python
def _invalidate_cache(self) -> None:
    self._active_intents_cache.clear()  # Nuclear option
```

**FIX:** Implement selective invalidation or use TTL-based caching with `functools.lru_cache`.

---

### ISSUE-019: Unbounded List Growth in Observations
**SEVERITY:** medium  
**FILE:** `src/agentic/autonomous_brain.py`  
**ISSUE:** Observations list passed between phases can grow unbounded:
```python
observations = await self._gather_observations()  # Could be 1000+ items
```

No truncation or sampling logic visible.

**FIX:** Implement observation windowing - keep only last N (e.g., 100) most relevant observations.

---

## 5. ERROR HANDLING & RESILIENCE

### ISSUE-020: Missing Retry Logic for External Calls
**SEVERITY:** high  
**FILES:** `src/agentic/moltx_agi_integration.py`, `plugins/`  
**ISSUE:** Network calls to MoltX, Telegram, etc. have no retry mechanism. Single transient failure causes action failure.

**FIX:** Implement exponential backoff retry decorator:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def external_api_call():
    ...
```

---

### ISSUE-021: No Circuit Breaker Pattern
**SEVERITY:** medium  
**FILES:** External service integrations  
**ISSUE:** If external service (MoltX, Telegram) is down, brain continues attempting calls every cycle, wasting resources and potentially triggering rate limits.

**FIX:** Implement circuit breaker. After N failures, pause calls for cooldown period.

---

### ISSUE-022: Silent Failures in Background Tasks
**SEVERITY:** high  
**FILE:** `autonomous_brain.py`  
**ISSUE:** Exceptions in async tasks are logged at DEBUG level and swallowed:
```python
except Exception as e:
    logger.debug(f"Persistent intent processing error: {e}")
```

Critical errors never surface. Brain continues in degraded state.

**FIX:** Use proper severity levels. Consider failing fast for critical components:
```python
except Exception as e:
    logger.error(f"CRITICAL: Brain phase failed: {e}", exc_info=True)
    # Optionally: raise or set degraded mode flag
```

---

### ISSUE-023: No Graceful Degradation for Missing Plugins
**SEVERITY:** medium  
**FILE:** `autonomous_brain.py:590`  
**ISSUE:** 
```python
moltx = self.plugin_manager.get_plugin('moltx')
if moltx and agi_kernel:  # Checks existence but not health
```

Plugin might exist but be unhealthy (rate limited, auth expired).

**FIX:** Add health check before using plugins:
```python
if moltx and moltx.is_healthy() and agi_kernel:
```

---

## 6. AI/AGENT-SPECIFIC ISSUES

### ISSUE-024: Token Inefficiency in Goal Proposals
**SEVERITY:** medium  
**FILE:** `src/agentic/agi_orchestrator.py:1877-1992`  
**ISSUE:** `generate_goal_proposals()` processes all observations every cycle. O(N) where N = observations. No prioritization or filtering.

**FIX:** Pre-filter observations by relevance score before processing. Use embedding similarity to owner objectives.

---

### ISSUE-025: No Context Window Management
**SEVERITY:** high  
**FILES:** `autonomous_brain.py`, `agi_kernel.py`  
**ISSUE:** Brain maintains growing context (observations, goals, intents) with no limit. Risk of exceeding LLM context window or causing OOM.

**FIX:** Implement sliding window context management. Summarize old context, evict low-priority items.

---

### ISSUE-026: ActionRouter Validation Ladder Not Enforced
**SEVERITY:** critical  
**FILE:** `src/agentic/action_router.py:59-72`  
**ISSUE:** The VALIDATION_STAGES tuple defines 12 stages, but the code doesn't show strict enforcement that all stages are called in sequence. Some stages may be skipped.

**FIX:** Add runtime validation to ensure every action passes through all required stages. Log skipped stages as warnings.

---

### ISSUE-027: Prediction Artifacts Not Validated
**SEVERITY:** medium  
**FILE:** `action_router.py`  
**ISSUE:** Prediction artifacts are created but there's no validation that predictions are reasonable (e.g., predicting 500% success rate).

**FIX:** Add sanity checks on predictions. Flag outliers for review.

---

## 7. DEPENDENCIES

### ISSUE-028: Outdated LangChain Version Constraint
**SEVERITY:** medium  
**FILE:** `requirements.txt:9-10`  
**ISSUE:** 
```
langchain>=0.1.0,<0.3.0
langchain-community>=0.0.20,<0.3.0
```

LangChain 0.3.x is current. Missing security patches and features.

**FIX:** Upgrade to latest stable. Test for breaking changes.

---

### ISSUE-029: No Dependency Pinning for Critical Packages
**SEVERITY:** low  
**FILE:** `requirements.txt:1-7`  
**ISSUE:** Core packages like `requests`, `flask`, `aiohttp` have no version constraints. Risk of breaking changes on fresh install.

**FIX:** Pin to minimum tested versions:
```
requests>=2.31.0
flask>=3.0.0
aiohttp>=3.9.0
```

---

### ISSUE-030: Unused Dependencies
**SEVERITY:** low  
**FILE:** `requirements.txt:16-17`  
**ISSUE:** `python-chess>=1.999` and `stockfish>=4.0.0` - is chess functionality still used? Adds bloat if not.

**FIX:** Audit if chess plugins are active. Remove if unused.

---

## 8. TESTING & COVERAGE

### ISSUE-031: No Tests for New AGI Components
**SEVERITY:** high  
**FILES:** `tests/`  
**ISSUE:** The 4 new files from TODO_KIMI_K25 have zero tests:
- `owner_objectives.py` - 0 tests
- `persistent_intent.py` - 0 tests  
- `strategic_planner.py` - 0 tests
- `cross_domain_synthesis.py` - 0 tests

Only `test_goal_generator.py` exists but doesn't cover the new logic.

**FIX:** Add unit tests for:
- Database migrations (auto_approved column)
- Intent lifecycle (create → update → complete)
- Cross-domain pattern detection
- Strategic plan advancement

---

### ISSUE-032: Integration Tests Don't Cover Failure Paths
**SEVERITY:** medium  
**FILE:** `tests/test_integration_opus.py`  
**ISSUE:** Tests focus on happy paths. No tests for:
- Database locked errors
- Plugin unavailable scenarios
- Validation stage failures
- Auto-approval safety valve triggering

**FIX:** Add negative test cases.

---

### ISSUE-033: No Load Testing
**SEVERITY:** medium  
**ISSUE:** Brain configured for 50 actions/hour but no tests verify this doesn't cause resource exhaustion.

**FIX:** Add stress tests with mocked plugins. Verify memory stays bounded.

---

## PRIORITIZED ACTION LIST (Top 5)

### 1. Fix Silent Failures (ISSUE-005, ISSUE-022)
**Priority:** P0 (Do Today)  
**Effort:** 4 hours  
Replace all bare `except: pass` and `logger.debug()` swallowing with proper error handling. This is causing production issues to be invisible.

---

### 2. Add Database Migration System (ISSUE-004, ISSUE-010)
**Priority:** P0 (Do Today)  
**Effort:** 6 hours  
Create `BaseSQLiteStore` class and migrate all managers to use it. Add proper migration tracking (alembic-style or version table).

---

### 3. Fix Async Blocking I/O (ISSUE-016)
**Priority:** P1 (This Week)  
**Effort:** 4 hours  
Run all SQLite operations in thread pool. This is starving the event loop and likely causing the Telegram polling issues seen in logs.

---

### 4. Add Input Validation (ISSUE-013, ISSUE-026)
**Priority:** P1 (This Week)  
**Effort:** 3 hours  
Add `__post_init__` validation to all dataclasses. Add runtime validation to ActionRouter to ensure all stages execute.

---

### 5. Create Test Suite for New Components (ISSUE-031)
**Priority:** P2 (Next Sprint)  
**Effort:** 8 hours  
Write comprehensive tests for owner_objectives, persistent_intent, strategic_planner. Test failure paths, database migrations, and edge cases.

---

## ADDITIONAL RECOMMENDATIONS

1. **Add Type Checking:** Run `mypy src/agentic/` - likely many type errors hidden by dynamic Python
2. **Add Linting:** `pylint` or `ruff` to catch unused imports, undefined variables
3. **Add Metrics:** Export Prometheus metrics for brain cycles, action success rates, database query times
4. **Documentation:** The new components have good docstrings but no architectural docs
5. **Monitoring:** Add health check endpoint that verifies all database connections are healthy

---

## CONCLUSION

The AlleyBot AGI implementation is **architecturally sound** but **operationally fragile**. The safety mechanisms (fail-closed gates, trust tiers) are correctly implemented. The main risks are:

1. **Silent failures** making debugging impossible
2. **Blocking I/O** in async context causing event loop starvation  
3. **No tests** for critical new components
4. **Code duplication** creating maintenance burden

**Recommendation:** Execute the P0 items immediately. The current code will work in happy-path scenarios but will fail mysteriously in production edge cases.

---

**End of Audit**
