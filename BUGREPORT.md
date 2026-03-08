# AlleyBot Bug Report
**Generated:** 2026-03-07  
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## Executive Summary

This report documents **47 bugs** found across AlleyBot's codebase, categorized by severity and subsystem. The most critical issues involve async/threading race conditions, resource leaks, and silent exception swallowing that can cause system instability.

**Critical Issues:** 8  
**High Priority:** 15  
**Medium Priority:** 18  
**Low Priority:** 6

---

## 🔴 CRITICAL BUGS

### 1. Telegram Polling Race Condition (FIXED)
**File:** `src/integrations/telegram_webhook.py:98`  
**Status:** ✅ Fixed in current session  
**Issue:** `get_updates()` debug call was stealing updates from the updater, preventing handlers from processing messages.  
**Impact:** Telegram commands completely non-functional.

### 2. Intent Classifier Blocking Startup
**File:** `plugins/telegram/conversational_ai.py:50-65`  
**Status:** ✅ Fixed in current session  
**Issue:** Pre-warming intent classifier synchronously encodes 1500+ phrases, blocking startup for 10 minutes.  
**Impact:** Bot takes 10 minutes to start instead of 30 seconds.  
**Fix Applied:** Disabled prewarm, loads lazily on first message.

### 3. Uncaught Event Loop Exceptions
**File:** `src/main.py:98`  
**Issue:** `event_runner.start()` blocks indefinitely with no exception handling for the polling task.
```python
# Current code - polling_task exceptions are never caught
self._polling_task = asyncio.create_task(self.telegram_webhook.start_polling_async())
await self.event_runner.start()  # Blocks forever, polling_task errors silently lost
```
**Impact:** If polling crashes, the error is silently swallowed and bot appears running but is dead.  
**Fix:** Use `asyncio.gather()` to run both tasks and catch exceptions:
```python
await asyncio.gather(
    self._polling_task,
    self.event_runner.start(),
    return_exceptions=False
)
```

### 4. SQLite Connection Not Thread-Safe
**File:** `src/agentic/creative_engine.py:124`, `research_engine.py:107`, multiple files  
**Issue:** Multiple `sqlite3.connect()` calls without connection pooling or thread-local storage.
```python
with sqlite3.connect(self.DB_PATH) as conn:  # Creates new connection every time
    conn.execute(...)
```
**Impact:** Race conditions, database locks, potential corruption with concurrent access.  
**Fix:** Use connection pooling or thread-local connections via `SQLiteMemoryMixin`.

### 5. Autonomous Brain Event Loop Leak
**File:** `src/agentic/autonomous_brain.py:241-250`  
**Issue:** Creates new event loop if none exists, but never closes it on shutdown.
```python
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()  # Created but never closed
    asyncio.set_event_loop(loop)
```
**Impact:** Event loop leaks on brain restart, accumulating resources.  
**Fix:** Store loop reference and close in `stop()` method.

### 6. Background Tasks Not Tracked
**File:** `plugin_manager.py:297-310`  
**Issue:** `start_all_background()` creates tasks but doesn't store references.
```python
await plugin.start_background()  # Task created but not tracked
```
**Impact:** Tasks can be garbage collected, causing silent failures. No way to monitor or cancel them.  
**Fix:** Store task references in `_async_tasks` dict and await on shutdown.

### 7. HTTP Requests Without Timeouts
**File:** `plugins/telegram/telegram.py:1036`, `plugins/moltx/moltx_core.py:140`, multiple files  
**Issue:** Many `requests.get/post()` calls missing timeout parameter.
```python
resp = requests.post(url, json={...})  # No timeout - can hang forever
```
**Impact:** Bot can hang indefinitely on network issues.  
**Fix:** Add `timeout=10` to all HTTP requests.

### 8. Startup Notification Blocks Event Loop (FIXED)
**File:** `src/integrations/telegram_webhook.py:97-104`  
**Status:** ✅ Fixed in current session  
**Issue:** Synchronous HTTP call in async context blocks event loop.  
**Fix Applied:** Moved to executor thread.

---

## 🟠 HIGH PRIORITY BUGS

### 9. Silent Exception Swallowing
**Files:** 25+ locations across codebase  
**Issue:** Bare `except Exception: pass` blocks hide errors.
```python
except Exception:  # Error silently ignored
    pass
```
**Locations:**
- `src/agentic/reply_system.py:67, 75, 144, 165, 197, 218`
- `src/agentic/context_system.py:104, 243, 312`
- `src/agentic/memory_bridge.py:60, 93, 285`
- `src/agents/event_runner.py:264`
- `src/integrations/telegram_webhook.py:103`

**Impact:** Bugs go unnoticed, debugging becomes impossible.  
**Fix:** Log exceptions at minimum:
```python
except Exception as e:
    logger.debug(f"Non-critical error: {e}")
```

### 10. Thread Leaks - Daemon Threads Never Joined
**Files:** Multiple plugins  
**Issue:** Daemon threads created but never tracked or joined on shutdown.
```python
threading.Thread(target=_warm, daemon=True).start()  # Never joined
```
**Locations:**
- `plugins/telegram/conversational_ai.py:65`
- `plugins/telegram/telegram.py:48, 1185`
- `plugins/brain/operational_resilience.py:452`
- `plugins/brain/brain.py:271, 292`
- `plugins/analytics/agent_card.py:427`
- `plugins/clawbr/clawbr_runner.py:318`
- `plugins/a2a/a2a_server.py:185`

**Impact:** Threads continue running after plugin unload, resource leak.  
**Fix:** Store thread references and join on cleanup.

### 11. Cleanup Methods Not Called on Shutdown
**File:** `alleybot_core.py:525-538`  
**Issue:** Plugin cleanup only called in `finally` block, but many exit paths bypass it.
```python
# Cleanup only happens if finally block is reached
finally:
    core.cleanup()
```
**Impact:** Resources not released on SIGTERM, SIGKILL, or unhandled exceptions.  
**Fix:** Register signal handlers and atexit hooks.

### 12. Race Condition in Plugin Manager
**File:** `plugin_manager.py:297-310`  
**Issue:** `start_all_background()` iterates plugins dict while it may be modified.
```python
for name, plugin in self.plugins.items():  # Dict may change during iteration
    await plugin.start_background()
```
**Impact:** RuntimeError: dictionary changed size during iteration.  
**Fix:** Use `list(self.plugins.items())` to snapshot.

### 13. Memory Leak in Event Queue
**File:** `src/agents/event_runner.py:63-82`  
**Issue:** Event queue processes events but never limits queue size.
```python
while self.running:
    event = await self.event_queue.get()  # Unbounded queue
```
**Impact:** If events arrive faster than processing, queue grows unbounded.  
**Fix:** Use `asyncio.Queue(maxsize=1000)` with backpressure handling.

### 14. Hardcoded Owner ID Fallback
**File:** `src/main.py:59`  
**Issue:** Hardcoded owner ID used as fallback.
```python
owner_id = os.getenv('TELEGRAM_OWNER_ID', '6172568442')  # Hardcoded!
```
**Impact:** Security risk if env var not set.  
**Fix:** Fail fast if env var missing.

### 15. Database Connections Not Closed
**File:** `src/agentic/sqlite_memory.py:130-135`  
**Issue:** Context manager doesn't guarantee connection close on exception.
```python
try:
    yield self._local.connection
except Exception:
    self._local.connection.rollback()
    raise  # Connection never closed
```
**Impact:** Connection leaks on exceptions.  
**Fix:** Add `finally: self._local.connection.close()`.

### 16. Async Task Created in Sync Init
**File:** `plugins/clawgame/clawgame.py:37`  
**Issue:** `asyncio.create_task()` called in `__init__` before event loop exists.
```python
def initialize(self, api, core):
    asyncio.create_task(self._init_wallet())  # May fail if no loop
```
**Impact:** RuntimeError: no running event loop.  
**Fix:** Move to `start_background()` method.

### 17. Polymarket Autonomous Trading Task Not Tracked
**File:** `plugins/polymarket/polymarket.py:700`  
**Issue:** Background task created but not stored.
```python
asyncio.create_task(autonomous_trading_loop(self))  # Lost reference
```
**Impact:** Task can be garbage collected, trading stops silently.  
**Fix:** Store in `self._trading_task`.

### 18. No Rate Limiting on API Calls
**Files:** All platform plugins  
**Issue:** No rate limiting on external API calls.  
**Impact:** API bans, 429 errors, service degradation.  
**Fix:** Implement token bucket rate limiter per API.

### 19. Telegram Application Not Properly Stopped
**File:** `plugins/telegram/telegram.py:1204`  
**Issue:** `application.stop()` called but not awaited.
```python
self.application.stop()  # Should be: await self.application.stop()
```
**Impact:** Cleanup incomplete, resources leaked.  
**Fix:** Make `stop_telegram_bot()` async and await.

### 20. Event Loop Closed While Tasks Running
**File:** `plugins/telegram/telegram.py:1180`  
**Issue:** Event loop closed without canceling tasks.
```python
loop.close()  # Tasks still running!
```
**Impact:** RuntimeError: Event loop is closed.  
**Fix:** Cancel all tasks before closing loop.

### 21. Health Monitor Infinite Loop on Error
**File:** `src/agentic/autonomous_startup.py:84-103`  
**Issue:** Health monitor catches all exceptions and continues, even fatal ones.
```python
except Exception as e:
    logger.error(f"❌ Health monitor error: {e}")
    # Continues looping even on fatal errors
```
**Impact:** Masks critical failures, infinite error loop.  
**Fix:** Re-raise critical exceptions.

### 22. Brain Restart Rate Limit Bypass
**File:** `src/agentic/autonomous_startup.py:105-113`  
**Issue:** Rate limit counter resets after 1 hour, but doesn't account for rapid restarts.
```python
if self.last_restart and (now - self.last_restart) > timedelta(hours=1):
    self.restart_count = 0  # Resets even if restarting every 59 minutes
```
**Impact:** Can restart infinitely by timing restarts just under 1 hour apart.  
**Fix:** Use sliding window rate limiter.

### 23. No Validation on Plugin Config
**File:** `plugin_manager.py:59-76`  
**Issue:** Plugin config loaded from JSON without validation.
```python
config = json.load(f)  # No schema validation
```
**Impact:** Malformed config causes runtime errors.  
**Fix:** Validate against schema before loading.

---

## 🟡 MEDIUM PRIORITY BUGS

### 24. Deprecated drop_pending_updates=False (FIXED)
**File:** `src/integrations/telegram_webhook.py:81`  
**Status:** ✅ Fixed - changed to `True`  
**Issue:** Replays stale updates on restart.

### 25. Process Update Monkey-Patch (FIXED)
**File:** `plugins/telegram/telegram.py:109-113`  
**Status:** ✅ Fixed - removed  
**Issue:** Broken signature, could suppress errors.

### 26. Debug Handler Crashes on Non-Message Updates (FIXED)
**File:** `plugins/telegram/telegram.py:97-102`  
**Status:** ✅ Fixed - removed  
**Issue:** `update.message.text` without null check.

### 27. Inconsistent Error Handling Patterns
**Files:** Throughout codebase  
**Issue:** Mix of `try/except`, `safe_execute()`, and no handling.  
**Impact:** Inconsistent error reporting and recovery.  
**Fix:** Standardize on `ErrorHandler` class.

### 28. No Logging Configuration
**File:** `src/main.py:13-19`  
**Issue:** Basic logging config, no rotation, no file output.
```python
logging.basicConfig(level=logging.WARNING)  # Only console, no files
```
**Impact:** Logs lost on restart, no audit trail.  
**Fix:** Use `RotatingFileHandler`.

### 29. Memory System Initialization Race
**File:** `alleybot_core.py:67-71`  
**Issue:** SQLite memory initialized before plugins, but plugins may need it.  
**Impact:** Plugins accessing memory before ready.  
**Fix:** Initialize memory first, then plugins.

### 30. AGI Kernel Initialization Failures Ignored
**File:** `alleybot_core.py:106-110`  
**Issue:** AGI kernel init errors caught and ignored.
```python
except Exception as e:
    print(f"⚠️ AGI Kernel decision systems initialization failed: {e}")
    # Continues anyway
```
**Impact:** Bot runs with broken AGI kernel.  
**Fix:** Fail fast or disable dependent features.

### 31. Plugin Load Order Not Guaranteed
**File:** `plugin_manager.py:72-76`  
**Issue:** Plugins loaded in dict iteration order (undefined).  
**Impact:** Dependency issues if plugin A needs plugin B.  
**Fix:** Implement dependency graph and topological sort.

### 32. No Health Checks for External Services
**Files:** All platform plugins  
**Issue:** No periodic health checks for APIs.  
**Impact:** Silent failures when services are down.  
**Fix:** Add health check endpoints and monitoring.

### 33. Skill Loader No Error Recovery
**File:** `src/skills/skill_loader.py`  
**Issue:** Skill load failures not handled gracefully.  
**Impact:** One bad skill breaks all skill loading.  
**Fix:** Isolate skill loading with try/except.

### 34. Session Manager File Corruption Risk
**File:** `src/agents/session_manager.py`  
**Issue:** JSON files written without atomic writes.  
**Impact:** Corruption on crash during write.  
**Fix:** Write to temp file, then atomic rename.

### 35. Model Router No Fallback
**File:** `src/config/models.py`  
**Issue:** If both DeepSeek and Grok fail, no fallback.  
**Impact:** Bot stops responding.  
**Fix:** Add fallback to simple template responses.

### 36. World State Database Lock Timeout
**File:** `src/agentic/world_state_manager.py`  
**Issue:** No timeout on database locks.  
**Impact:** Deadlocks freeze bot.  
**Fix:** Set `timeout` parameter on connections.

### 37. Episodic Memory Unbounded Growth
**File:** `src/agentic/episodic_memory.py`  
**Issue:** No pruning of old memories.  
**Impact:** Database grows indefinitely.  
**Fix:** Implement LRU eviction or time-based pruning.

### 38. No Metrics Collection
**Files:** Throughout codebase  
**Issue:** No prometheus/statsd metrics.  
**Impact:** No observability, can't diagnose issues.  
**Fix:** Add metrics instrumentation.

### 39. Hardcoded File Paths
**Files:** Multiple  
**Issue:** Paths like `data/memory.db` hardcoded.  
**Impact:** Can't customize data directory.  
**Fix:** Use config or env vars.

### 40. No Request ID Tracing
**Files:** All API integrations  
**Issue:** No correlation IDs for request tracing.  
**Impact:** Can't trace requests across systems.  
**Fix:** Add request ID headers.

### 41. Timezone Handling Inconsistent
**Files:** Multiple  
**Issue:** Mix of `datetime.now()` and `datetime.utcnow()`.  
**Impact:** Timezone bugs in logs and timestamps.  
**Fix:** Use UTC everywhere, convert on display.

---

## 🟢 LOW PRIORITY BUGS

### 42. TODO Comments Not Tracked
**Files:** 200+ TODO comments  
**Issue:** TODOs in code not tracked in issue tracker.  
**Impact:** Technical debt accumulates.  
**Fix:** Convert to GitHub issues.

### 43. Debug Commands in Production
**Files:** `plugins/telegram/menu_registry_*.py`  
**Issue:** Debug commands like `/moltx_debug`, `/menu_debug` exposed.  
**Impact:** Information disclosure.  
**Fix:** Hide behind admin-only flag.

### 44. Inconsistent Naming Conventions
**Files:** Throughout  
**Issue:** Mix of snake_case, camelCase, PascalCase.  
**Impact:** Code readability.  
**Fix:** Standardize on snake_case for Python.

### 45. No Type Hints in Legacy Code
**Files:** Older plugins  
**Issue:** Missing type annotations.  
**Impact:** IDE support degraded, harder to maintain.  
**Fix:** Add gradual typing.

### 46. Duplicate Code in Platform Plugins
**Files:** `plugins/moltx/`, `plugins/moltchan/`, `plugins/moltroad/`  
**Issue:** Similar API request code duplicated.  
**Impact:** Maintenance burden.  
**Fix:** Extract common base class.

### 47. No API Versioning
**Files:** All platform integrations  
**Issue:** No version pinning on external APIs.  
**Impact:** Breaking changes break bot.  
**Fix:** Pin API versions, add version detection.

---

## Recommendations by Priority

### Immediate Actions (This Week)
1. ✅ Fix Telegram polling race condition (DONE)
2. ✅ Fix intent classifier blocking startup (DONE)
3. Fix event loop exception handling (#3)
4. Fix SQLite thread safety (#4)
5. Add timeouts to all HTTP requests (#7)

### Short Term (This Month)
6. Implement proper task tracking (#6)
7. Fix silent exception swallowing (#9)
8. Add cleanup signal handlers (#11)
9. Fix thread leaks (#10)
10. Implement rate limiting (#18)

### Medium Term (This Quarter)
11. Standardize error handling (#27)
12. Add proper logging (#28)
13. Implement health checks (#32)
14. Add metrics collection (#38)
15. Fix database connection pooling (#4, #15)

### Long Term (Ongoing)
16. Reduce technical debt (TODOs → issues)
17. Add type hints to legacy code
18. Refactor duplicate code
19. Improve test coverage
20. Document architecture

---

## Testing Recommendations

1. **Add Integration Tests** for Telegram polling lifecycle
2. **Add Stress Tests** for event queue under load
3. **Add Chaos Tests** for network failures and timeouts
4. **Add Memory Leak Tests** with long-running scenarios
5. **Add Concurrency Tests** for database access

---

## Monitoring Recommendations

1. **Add Alerts** for:
   - Event queue depth > 100
   - Task count > 60
   - Memory usage > 80%
   - API error rate > 5%
   - Database lock waits > 1s

2. **Add Dashboards** for:
   - System health metrics
   - Plugin status
   - API call latencies
   - Error rates by subsystem

---

**Report End**
