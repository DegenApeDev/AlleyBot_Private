# AlleyBot Agent Framework — Usability Audit (Updated)

**Auditor**: opencode (automated deep audit)
**Date**: April 24, 2026
**Scope**: Full project — architecture, code quality, security, usability, completeness
**Previous**: This audit supersedes the initial version, incorporating all changes from the cognitive architecture integration and self-improvement pipeline repair.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Changed Since Last Audit](#2-what-changed-since-last-audit)
3. [Architecture & Structure](#3-architecture--structure)
4. [New Cognitive Architecture](#4-new-cognitive-architecture)
5. [Self-Improvement Pipeline](#5-self-improvement-pipeline)
6. [Core Files Analysis](#6-core-files-analysis)
7. [Plugins](#7-plugins)
8. [Skills System](#8-skills-system)
9. [Configuration & Environment](#9-configuration--environment)
10. [Data & Memory Layer](#10-data--memory-layer)
11. [Security Findings](#11-security-findings)
12. [Code Quality Issues](#12-code-quality-issues)
13. [Missing Features & Incomplete Implementations](#13-missing-features--incomplete-implementations)
14. [Dependency & Coupling Issues](#14-dependency--coupling-issues)
15. [Test Coverage](#15-test-coverage)
16. [Recommendations (Prioritized)](#16-recommendations-prioritized)
17. [Positive Findings](#17-positive-findings)

---

## 1. Executive Summary

AlleyBot is an autonomous AGI system with a 14-phase cognitive loop, live crypto trading, platform integrations, and a self-improvement pipeline. Since the initial audit, significant progress has been made: a new cognitive architecture (BeliefEngine, SelfModel, GoalPlanner, CognitiveIntegration) replaces the Duat/Synergy numerology system, the self-improvement pipeline has been repaired across 7 break points and 4 regressions, episodic memory bugs have been fixed, and proactive autonomous mode has been enabled.

However, critical issues remain: the god class in `autonomous_brain.py` grew from 3,197 to 3,324 lines, there are zero tests for the entire cognitive system, the Duat/Synergy system still runs alongside the new cognitive architecture (not yet removed), `world_state.db` has grown to 99MB with no pruning, and 567 `print()` calls outnumber `logging` calls 6:1.

**Overall Usability Score: 5/10** — Improved from 4/10. The cognitive architecture is sound but untested. The self-improvement pipeline is functional but fragile. The god class, missing tests, and Duat/Synergy overlap remain the biggest blockers.

---

## 2. What Changed Since Last Audit

### 2.1 New Cognitive Architecture (4 modules, ~1,650 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| `belief_engine.py` | 372 | Bayesian belief tracking with confidence scoring |
| `self_model.py` | 348 | Calibrated capability tracking per domain/action |
| `goal_planner.py` | 551 | Dependency-graph plans with rollback and tool registry |
| `cognitive_integration.py` | 379 | Wires all cognitive components + Telegram notifications |

All four modules are synchonrous (no async), properly layered (no circular imports), and persist to JSON files. Wired into `autonomous_brain.py` (cycle reflection, cognitive bias, deep review) and `action_router.py` (belief prediction, outcome recording).

### 2.2 Self-Improvement Pipeline Repair (7 breaks + 4 regressions fixed)

| Break | File | Fix |
|-------|------|-----|
| Priority gate blocked non-repeated-failure gaps | `autonomous_brain.py` | Lowered threshold to `priority < 4`, removed type restriction |
| `await` on sync `_generate_code_with_ai()` | `auto_skill_builder.py` | Removed `await` |
| `deploy_skill()` was a TODO stub | `src/agentic/autonomous_coder.py` | Added hot-reload via plugin manager |
| `load_plugin()` arg count mismatch (4-arg vs 2-arg) | `selfimprove/autonomous_coder.py` | Added `inspect.signature()` detection |
| Broken imports (`comprehensive_logger`, root `SkillGenerator`) | `autonomous_skill_workflow.py` | Fixed all imports to `src.agentic.*` |
| `BridgeCoder` mixin missing `_init_autonomous_coder()` | `skill_generator.py` | Replaced with plugin_manager lookup |
| Empty `files_created` IndexError | `autonomous_brain.py` | Added guard check |

**Regressions caught and fixed:**
- `SkillGenerator` → `DynamicSkillGenerator` (wrong class name)
- `.get('draft_id')` on `GeneratedSkill` dataclass → `.spec_id`
- Early return blocking AutonomousCoder fallback → removed
- `open()` resource leak → `Path.read_text()`
- Null `selfimprove_plugin` crash in sandbox test → added guard

### 2.3 Other Fixes

- **EpisodicMemoryStore**: 6 call-site bugs fixed (wrong method names, dict access on strings, broken attribute access)
- **KnowledgeGraph**: `_knowledge_graph` singleton variable missing → added
- **Brain plugin**: `think()` method no longer calls `asyncio.get_event_loop()` from main thread → returns status report instead
- **Config flags**: Auto-start, auto-posting, auto-engagement all enabled in `plugin_config.json`; `HEARTBEAT.md` mode=autonomous
- **KnowledgeGraph**: Added `learn_from_outcome()`, `predict_outcome()`, `analogical_transfer()` methods

---

## 3. Architecture & Structure

### 3.1 Cognitive Architecture

The system now implements a **14-phase AGI cognitive loop + cognitive bias layer**:

| Component | Lines | Role |
|-----------|-------|------|
| `autonomous_brain.py` | 3,324 | God class — all 14 phases + cognitive integration |
| `agi_kernel.py` | 1,805 | Consciousness layer, memory/goals/metacognition |
| `action_router.py` | 1,907 | 12-stage validation pipeline + belief prediction |
| `belief_engine.py` | 372 | Bayesian belief tracking with confidence scoring |
| `self_model.py` | 348 | Calibrated capability tracking with calibration curves |
| `goal_planner.py` | 551 | Dependency-graph plans with rollback, tool registry |
| `cognitive_integration.py` | 379 | Wires BeliefEngine+SelfModel+GoalPlanner into the system |
| `knowledge_graph.py` | 584 | Causal knowledge extraction from action outcomes |

**Platforms integrated**: Moltx, Clawbr, Moltbook, Moltchan, Moltbit, Moltroad, Telegram, Solana/Jupiter, Base/Uniswap, Polymarket.

### 3.2 Architecture Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| **God Class** | HIGH | `autonomous_brain.py` at 3,324 lines (grew from 3,197). Contains 14+ phase methods, plugin coordination, goal management, skill building, cognitive integration, trading — all in one file. |
| **Dual Cognitive Systems** | HIGH | Duat/Synergy still active alongside BeliefEngine/SelfModel. Both run every cycle. Adds processing overhead and confuses the intelligence model. 68+ references to Synergy remain. |
| **Circular Imports** | MEDIUM | `agi_kernel.py` ↔ `action_router.py` via `ModelProvider`. Still present. |
| **Import Churn** | MEDIUM | `autonomous_brain.py` has 37+ imports from different modules creating brittle coupling. |
| **Dual Plugin Base Classes** | HIGH | `AlleyBotPlugin` (sync, 44 lines) vs `BasePlugin` (async, 424 lines). Most plugins use sync version. |
| **Monolithic Memory Layer** | HIGH | 14+ SQLite databases, 31 JSON files, new cognitive JSON files. `world_state.db` is 99MB. No unified schema. |
| **Root Directory Clutter** | MEDIUM | 50+ markdown files at project root. |

### 3.3 Naming Confusion (Usability Killer)

Still present and unchanged:

| Concept | Files Found |
|---------|-------------|
| Decision system | `decision_system.py` vs `decision_system_synergy.py` |
| Meta-learning | `meta_learner.py` vs `meta_learning.py` vs `metacognition.py` vs `meta_cognition_engine.py` |
| Goals | `goal_generator.py` vs `goal_manager.py` vs `goal_hierarchy.py` vs `goal_stack.py` vs `goal_detector.py` vs `default_goals.py` |
| Skills | `skill_generator.py` vs `skill_tester.py` vs `skill_executor.py` vs `skilldoc_manager.py` vs `auto_skill_builder.py` |
| Agent | `agentic_system.py` vs `simple_agent.py` vs `react_agent.py` vs `autonomous_brain.py` |
| Plugin manager | `plugin_manager.py` (root) vs `src/core/plugin_manager.py` |
| Autonomous coder | `autonomous_coder.py` (root) vs `src/agentic/autonomous_coder.py` vs `plugins/selfimprove/autonomous_coder.py` |

---

## 4. New Cognitive Architecture

### 4.1 BeliefEngine (`belief_engine.py`, 372 lines)

**Design**: Bayesian-inspired predict-compare-update system. Beliefs stored as `(subject, predicate, object)` triples with confidence, accuracy, and count tracking. Automatic decay over time. Persists to `data/beliefs.json`.

**Issues**:
| Issue | Severity | Line | Description |
|-------|----------|------|-------------|
| Silent save failures | MEDIUM | 359 | `except Exception: pass` in `_save()` — data loss risk |
| Silent load failures | MEDIUM | 368 | `except Exception: pass` in `_load()` — falls back to empty dict |
| Logic bug in `get_domain_strengths()` | MEDIUM | 304 | Uses `belief.accuracy` outside the loop where it was assigned; could reference stale/wrong belief |
| No logging | MEDIUM | — | Module uses neither `print()` nor `logging` — silent operation |
| Thread safety | MEDIUM | — | `self.beliefs` dict accessed from brain thread and event loop without locks |
| Hash truncation | LOW | 129 | `_hash()` truncates to 80 chars, could cause collisions for similar long propositions |

### 4.2 SelfModel (`self_model.py`, 348 lines)

**Design**: Tracks capability confidence per domain and action. Maintains calibration curves. Generates self-awareness reports. Persists to `data/self_model.json`.

**Issues**:
| Issue | Severity | Line | Description |
|-------|----------|------|-------------|
| Silent save failures | MEDIUM | 330 | `except Exception: pass` in `_save()` |
| Silent load failures | MEDIUM | 343 | `except Exception: pass` in `_load()` |
| No logging | MEDIUM | — | Entire module has zero logging or print statements |
| Thread safety | MEDIUM | — | `self.capabilities` dict mutated from two threads |

### 4.3 GoalPlanner (`goal_planner.py`, 551 lines)

**Design**: Dependency-graph plans with precondition checking, rollback support, alternative path generation. 40+ tool definitions. Persists to `data/plans.json`.

**Issues**:
| Issue | Severity | Line | Description |
|-------|----------|------|-------------|
| Silent save failures | MEDIUM | 538 | `except Exception: pass` in `_save()` |
| Silent load failures | MEDIUM | 547 | `except Exception: pass` in `_load()` |
| Inefficient indexing | LOW | 383-385 | `steps.index(step)` in loop is O(n²) |
| Hardcoded tool registry | LOW | — | `TOOL_REGISTRY` is fixed, not dynamically discovered |
| No logging | MEDIUM | — | Module has zero logging |

### 4.4 CognitiveIntegration (`cognitive_integration.py`, 379 lines)

**Design**: Wires BeliefEngine, SelfModel, GoalPlanner, and KnowledgeGraph together. Provides `predict_action_outcome()`, `record_action_outcome()`, `reflect()`, and Telegram notification hooks. Singleton pattern via `get_cognitive()`.

**Issues**:
| Issue | Severity | Line | Description |
|-------|----------|------|-------------|
| No telegram_plugin at init | MEDIUM | 371-379 | Singleton created without `telegram_plugin`, so all notifications silently skip. The plugin must be injected later via `set_telegram_plugin()` |
| Notification hardcoding | LOW | 107-110 | `_should_notify_completion()` only notifies for a hardcoded set of action roots/domains |
| Thread safety | MEDIUM | — | `_cognitive` singleton not thread-safe; belief_engine and self_model both accessed from brain thread + event loop |

### 4.5 Wiring Assessment

| Connection | Status | Issues |
|-----------|--------|--------|
| `autonomous_brain.py` → `cognitive_integration` | WIRED | Line 46 import, line 159 init, lines 437+631 reflection, lines 1962+ deep review, lines 2602+ cognitive bias |
| `action_router.py` → `cognitive_integration` | WIRED | Line 25 import, line 89 init, lines 1097-1111 belief prediction, lines 1251-1264 outcome recording |
| `agi_kernel.py` → `cognitive_integration` | NOT WIRED | Still uses Duat/Synergy. No import of any cognitive module. |
| `action_router.py` → `print()` not `logger` | MEDIUM | Lines 1090, 1095, 1108, 1111, 1264 use `print()` instead of `logging` |

---

## 5. Self-Improvement Pipeline

### 5.1 Pipeline Architecture

The self-improvement pipeline detects skill gaps → generates code → tests in sandbox → hot-loads plugins. It has three entry points:

1. **`autonomous_brain.py` `_phase_skill_gap_analysis()`** — Primary trigger. Detects gaps from episodic memory failures and missing capabilities.
2. **`auto_skill_builder.py`** — Secondary trigger. Monitors platform skill docs for new capabilities.
3. **`autonomous_skill_workflow.py`** — Tertiary trigger. Generates ideas from trends and community requests.

### 5.2 Current Status: FUNCTIONAL but Fragile

| Component | Status | Remaining Issues |
|-----------|--------|-----------------|
| Skill gap detection | WORKING | Priority threshold `< 4` allows most gap types through |
| Primary path (selfimprove plugin) | WORKING | Uses `self_update_command()` with AI generation + sandbox + hot-load |
| Fallback path (skeleton AutonomousCoder) | WORKING | Generates template code, deploys via `reload_plugin()` |
| Sandbox testing | PARTIAL | `SecureSandbox` in `skill_generator.py` has weak isolation (no filesystem/network restrictions) |
| Hot-loading | WORKING | `inspect.signature()` detection for 2-arg vs 4-arg `load_plugin()` |
| Idea generation (workflow) | BROKEN | `SkillGenerator()` call at line 19 crashes — requires `(llm, skills_dir)` args |
| Auto skill builder | PARTIAL | `detect_capability_gaps()` is async but doesn't await anything |

### 5.3 Security Concerns

| Issue | Severity | File:Line | Description |
|-------|----------|-----------|-------------|
| Weak sandbox | HIGH | `skill_generator.py:116-168` | `SecureSandbox.execute_in_sandbox()` uses `subprocess.run` with only `PYTHONPATH=os.getcwd()` restriction. No filesystem, network, or resource isolation. |
| Regex security filter | MEDIUM | `skill_generator.py:60-91` | `CodeSecurityValidator` blocks `os.system`, `eval`, etc. via regex — bypassable. |
| No sandbox in selfimprove | MEDIUM | `selfimprove/autonomous_coder.py` | `_sandbox_check_file()` only does pattern checks, no actual isolated execution |
| `pip install` remains | CRITICAL | `root/autonomous_coder.py:157-159` | LLM-generated dependency lists installed via `pip install -q`. Still present in root module. |

---

## 6. Core Files Analysis

### 6.1 `autonomous_brain.py` (3,324 lines) — God Class

Grew from 3,197 lines. Now includes cognitive integration, skill gap analysis, self-improvement triggering, and periodic cognitive reviews. 37+ imports, 20+ subsystems managed.

| Issue | Severity | Detail |
|-------|----------|--------|
| God class | HIGH | 3,324 lines. Impossible to understand in one reading. Must be decomposed. |
| Dual cognitive systems | HIGH | Lines 43, 156, 447, 643-646: Duat/Synergy still active alongside BeliefEngine/SelfModel |
| 4 `print()` calls | MEDIUM | Lines 437-640 — should use `logger` |
| No toggle for cognitive | LOW | Cognitive system is always-on with no `enable_cognitive` config flag |
| Double reflection per cycle | LOW | Lines 437 and 631 both call `self.cognitive.reflect()` |

### 6.2 `agi_kernel.py` (1,805 lines)

| Issue | Severity | Detail |
|-------|----------|--------|
| Not wired to cognitive | MEDIUM | Still imports `SynergyGate` (line 41), prints "Duat Cognition Engine" (line 109). No import of any new cognitive module. |
| 110 `print()` calls | MEDIUM | No structured logging |
| 10 bare exception handlers | HIGH | Errors silently caught |

### 6.3 `action_router.py` (1,907 lines)

| Issue | Severity | Detail |
|-------|----------|--------|
| Well-designed pipeline | — | 12-stage validation ladder. Best-designed component in the codebase. |
| `print()` not `logger` | MEDIUM | Lines 1090, 1095, 1108, 1111, 1264 in cognitive wiring use `print()` |
| Belief prediction on every action | LOW | Adds latency to trivial actions like health checks |

### 6.4 `config.py` (26 lines) — Still Minimal

| Issue | Severity | Detail |
|-------|----------|--------|
| Missing env vars | CRITICAL | Only 26 lines. Missing TELEGRAM_BOT_TOKEN, SOLANA_WALLET_PRIVATE_KEY, and many others. |
| No validation | HIGH | No type checking or presence validation. |
| Added autonomous flags | LOW | `AUTO_START_BRAIN`, `BRAIN_MODE`, `TRADING_ENABLED` added but not comprehensive. |

### 6.5 `web_server.py` (625 lines)

Unchanged. CORS wide open, no authentication, bare except handlers.

### 6.6 `plugin_manager.py` (root, 361 lines)

Dual system exists: root `plugin_manager.py` (4-arg `load_plugin`) vs `src/core/plugin_manager.py` (2-arg `load_plugin`). Hot-loading now uses `inspect.signature()` to handle both, but this is fragile.

---

## 7. Plugins

35+ plugin directories. Key findings unchanged from initial audit:

| Issue | Severity | Detail |
|-------|----------|--------|
| Inheritance inconsistency | HIGH | Most plugins use `AlleyBotPlugin` (sync) instead of `BasePlugin` (async, 424 lines, well-designed) |
| No health checks | MEDIUM | Despite SOP mandating them |
| `brain.py` plugin | MEDIUM | `start_autonomous()` calls `run_until_complete()` then `run_forever()` on same loop — potential deadlock |

### 7.1 `plugins/brain/brain.py` (326 lines)

| Issue | Severity | Detail |
|-------|----------|--------|
| `think()` fixed | FIXED | No longer calls `asyncio.get_event_loop()` from main thread. Returns status dict instead. |
| Potential deadlock | HIGH | `start_autonomous()` line 264-267: runs `loop.run_until_complete()` then `loop.run_forever()`. If `start()` never returns, `run_until_complete` blocks forever. |
| 15 `print()` calls | MEDIUM | No structured logging |

---

## 8. Skills System

- 30+ skill directories
- `dynamic_skills/` — still empty (self-improvement generates template skills to `sandbox/draft_skills/` but doesn't populate this directory)
- No `README` in `skills/` explaining how to create, test, or register a skill
- `auto_skill_builder.py` monitors `skill.md` files but the "simple skills" it builds go to `skills/auto_acquired/`

---

## 9. Configuration & Environment

| Area | Status | Issues |
|------|--------|--------|
| `config.py` | MINIMAL | Only 26 lines, missing most env vars, no validation |
| `plugin_config.json` | CONFIGURED | Auto-start and auto-posting flags enabled |
| `HEARTBEAT.md` | CONFIGURED | `mode: "autonomous"`, `approval_required: false` |
| Cognitive toggle | MISSING | No `enable_cognitive` flag — BeliefEngine/SelfModel always run |
| Duat toggle | MISSING | No way to disable Duat/Synergy without editing `autonomous_brain.py` |

---

## 10. Data & Memory Layer

| Database/File | Size | Concern |
|--------------|------|---------|
| `world_state.db` | **99 MB** | Extremely large. No pruning, no indexing, no archival. Growing. |
| `plans.db` | 5.8 MB | |
| `strategies.db` | 3.4 MB | |
| `creative.db` | 2.1 MB | |
| `memory.db` | 844 KB | |
| `beliefs.json` | 3.7 KB | New — from BeliefEngine |
| `self_model.json` | 698 B | New — from SelfModel |
| `plans.json` | 2.8 KB | New — from GoalPlanner |
| `duat_state.json` | 342 B | Legacy — still written every cycle |

**Concern**: 14+ SQLite databases, 31+ JSON files, and 3 new cognitive JSON files. No unified schema, no migration system, no backup/rotation. The `world_state.db` at 99MB is a performance risk for SQLite.

---

## 11. Security Findings

### 11.1 SECRETS PROTECTION — WELL-DESIGNED (with caveats)

`security_filter.py` unchanged. Still provides robust output-side protection. Input-side filtering remains absent.

### 11.2 CODE INJECTION IN AUTONOMOUS CODER — CRITICAL (unchanged)

Root `autonomous_coder.py` still runs `subprocess.run(["python", "-c", test])` with LLM-generated code and `pip install -q` with arbitrary packages. No Docker sandbox, no process isolation.

**Note**: `selfimprove/autonomous_coder.py` (the active path) uses `_sandbox_check_file()` which only checks patterns, not actual sandboxed execution. `skill_generator.py`'s `SecureSandbox` has filesystem access.

### 11.3 CORS WIDE OPEN — CRITICAL (unchanged)

`web_server.py` CORS allows all origins, all methods, all headers, with credentials enabled.

### 11.4 NO AUTHENTICATION — HIGH (unchanged)

No auth on any API endpoint or WebSocket connection.

### 11.5 NO RATE LIMITING — MEDIUM (unchanged)

---

## 12. Code Quality Issues

| Category | Count | Severity | Impact |
|----------|-------|----------|--------|
| Bare `except` handlers | 0 (new cognitive) | — | New modules are clean |
| Broad `except Exception: pass` | 6 (new cognitive) | MEDIUM | Silent data loss in save/load |
| `print()` instead of `logging` | **567** | MEDIUM | 6:1 ratio across src/agentic/ |
| God class (brain) | 3,324 lines | HIGH | Impossible to understand holistically |
| Duplicate module names | ~8 groups | MEDIUM | Cannot determine canonical implementation |
| Missing input validation | Widespread | MEDIUM | Config, dataclasses, APIs accept unvalidated input |
| Missing retry logic | 3 clients | MEDIUM | Transient failures cascade |
| Missing type hints | Widespread | LOW | IDE support and refactoring harder |
| Magic numbers | Throughout | LOW | Not named constants |
| No DB migrations | 14+ databases | MEDIUM | Schema changes manual and error-prone |
| Thread safety | 3 modules | MEDIUM | BeliefEngine, SelfModel, EpisodicMemory all accessed from 2+ threads without locks |

**Improvement from initial audit**: Bare `except:` handlers are gone from new cognitive modules (using `except Exception: pass` instead), which is slightly better. However, `autonomous_brain.py` and `agi_kernel.py` still have many broad exception handlers.

---

## 13. Missing Features & Incomplete Implementations

| Feature | Status | Impact |
|---------|--------|--------|
| Circuit breaker | Not implemented | External service failures cascade |
| Rate limiting | Not implemented | Vulnerable to API abuse |
| Health check endpoint | Not implemented | No operational visibility |
| Structured logging | Not implemented | No observability into agent behavior |
| Prometheus metrics | Not implemented | No quantitative monitoring |
| Database migrations | Not implemented | Schema changes are manual |
| Tests for cognitive system | **Not implemented** | Zero tests for BeliefEngine, SelfModel, GoalPlanner, CognitiveIntegration |
| Plugin health checks | Not implemented | SOP mandates them but none exist |
| `dynamic_skills/` | Empty | Self-improvement generates to sandbox, not here |
| Input validation (LLM) | Not implemented | Prompt injection risk |
| Duat/Synergy removal | Not done | Still running alongside cognitive |
| `agi_kernel.py` cognitive wiring | Not done | AGI kernel doesn't use BeliefEngine/SelfModel |
| Cognitive system toggle | Not implemented | Always on, no config flag |
| Thread safety for cognitive | Not implemented | BeliefEngine, SelfModel accessed from multiple threads |
| `world_state.db` pruning | Not implemented | 99MB and growing |
| Telegram notification wiring | Partial | CognitiveIntegration has `telegram_plugin=None`, all notifications skipped |

---

## 14. Dependency & Coupling Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| Dual cognitive systems | Duat/Synergy + BeliefEngine/SelfModel both active | Confusion, wasted compute, conflicting signals |
| Circular imports | `agi_kernel.py` ↔ `action_router.py` via `ModelProvider` | Import order matters, breakage risk |
| Deep coupling | `autonomous_brain.py` imports from 37+ modules | Changes anywhere can break the brain |
| Dual plugin systems | `AlleyBotPlugin` (sync) vs `BasePlugin` (async) | Plugin developers don't know which to use |
| Triple autonomous coder | Root, src/agentic/, and plugins/selfimprove/ | Different interfaces, different capabilities |
| Singletons everywhere | `grok_ai`, `deepseek_ai`, `mcp_client`, `tx_registry`, `cognitive` | No dependency injection, hard to test |
| Mixed sync/async | LLM clients sync, brain async, plugins mixed | Event loop blocking, callback hell |
| Thread safety | Cognitive modules accessed from brain thread + event loop | Race conditions on shared mutable dicts |

---

## 15. Test Coverage

| Module | Lines | Test Coverage |
|--------|-------|--------------|
| `belief_engine.py` | 372 | **0 tests** |
| `self_model.py` | 348 | **0 tests** |
| `goal_planner.py` | 551 | **0 tests** |
| `cognitive_integration.py` | 379 | **0 tests** |
| `knowledge_graph.py` | 584 | **0 tests** (new methods) |
| `action_router.py` | 1,907 | **0 tests** (cognitive wiring) |
| `autonomous_brain.py` | 3,324 | **0 tests** |
| Existing tests | ~2,500 lines | Phase-organized, no module coverage |

Total coverage: **~1.5%** of codebase. The new cognitive architecture has **zero** verification.

---

## 16. Recommendations (Prioritized)

### P0 — Immediate (Security & Stability)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 1 | **Sandbox autonomous coder** — Docker/process isolation for LLM-generated code execution | 4h | Critical |
| 2 | **Fix `SkillGenerator()` crash** — `autonomous_skill_workflow.py:19` requires `(llm, skills_dir)` args | 0.5h | High |
| 3 | **Fix brain plugin deadlock** — `start_autonomous()` may deadlock on `run_until_complete` + `run_forever` | 2h | High |
| 4 | **Narrow CORS** — restrict to specific origins in `web_server.py` | 1h | High |
| 5 | **Add authentication** — API key auth to dashboard endpoints | 2h | High |

### P1 — This Week (Reliability)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 6 | **Write tests for cognitive system** — BeliefEngine, SelfModel, GoalPlanner, CognitiveIntegration | 8h | High |
| 7 | **Remove Duat/Synergy** — Replace remaining 68+ references with cognitive calls | 4h | High |
| 8 | **Wire `agi_kernel.py` to cognitive** — Add BeliefEngine/SelfModel imports, remove Duat prints | 2h | Medium |
| 9 | **Wire Telegram notifications** — Inject `telegram_plugin` into CognitiveIntegration | 1h | Medium |
| 10 | **Add thread locks** — Protect shared dicts in BeliefEngine, SelfModel, EpisodicMemory | 2h | Medium |
| 11 | **Replace `print()` with `logging`** — 567 instances across src/agentic/ | 4h | High |
| 12 | **Fix silent save/load failures** — Add logging to 6 `except Exception: pass` blocks | 1h | Medium |
| 13 | **Fix `belief_engine.py` line 304 logic** — `get_domain_strengths()` may use stale belief reference | 1h | Medium |

### P2 — Next Sprint (Code Quality)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 14 | **Decompose `autonomous_brain.py`** — Extract phases into separate modules | 16h | High |
| 15 | **Consolidate triple autonomous coder** — Remove root and src/agentic versions, keep only selfimprove plugin | 4h | High |
| 16 | **Consolidate duplicate modules** — Merge or deprecate overlapping names | 8h | Medium |
| 17 | **Organize root docs** — Move 50+ markdown files to `docs/` with index | 3h | Medium |
| 18 | **Add database migration system** — Version tracking for all .db files | 8h | Medium |
| 19 | **Pin dependency versions** — Add version constraints to requirements.txt | 2h | Medium |
| 20 | **Prune `world_state.db`** — Add archival and indexing, consider PostgreSQL | 8h | High |

### P3 — Future (Architecture)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 21 | **Implement circuit breaker** — For all external service integrations | 8h | High |
| 22 | **Add Prometheus metrics** — Brain cycles, action success rates, DB query times | 8h | Medium |
| 23 | **Add `/health` endpoint** — Check DBs, plugins, external services | 4h | Medium |
| 24 | **Consolidate memory layer** — Eliminate JSON fallback, unified SQLite schema | 16h | High |
| 25 | **Async LLM clients** — Convert DeepSeek, Grok, MCP, Moltbook to async HTTP | 8h | High |
| 26 | **Unify plugin base class** — Migrate all plugins from `AlleyBotPlugin` to `BasePlugin` | 6h | High |
| 27 | **Dependency injection** — Replace module-level singletons | 16h | High |
| 28 | **Add cognitive toggle** — Config flag to enable/disable BeliefEngine/SelfModel | 1h | Low |

---

## 17. Positive Findings

1. **ActionRouter validation ladder**: 12-stage validation with fail-closed design, HITL gating, and now belief prediction. Still the best-designed component.

2. **Cognitive architecture (new)**: Properly layered — BeliefEngine, SelfModel, GoalPlanner have no circular imports. Clean singletons. Synchronous design avoids event loop issues. Bayesian belief updating with decay is sound.

3. **Self-improvement pipeline repair**: All 7 break points fixed. Pipeline now flows from skill gap detection through code generation to sandbox testing to hot-loading. Fallback path works when selfimprove plugin unavailable.

4. **KnowledgeGraph enrichment**: `learn_from_outcome()`, `predict_outcome()`, `analogical_transfer()` extract causal knowledge from every action outcome.

5. **Security filter + TxRegistry**: Well-designed output-side protection with exact-value matching and pattern recognition.

6. **BaseSQLiteStore**: Proper async SQLite abstraction with connection pooling.

7. **BasePlugin abstract class**: 424-line well-designed async plugin base with `AsyncPluginMixin` and `PluginRegistry`.

8. **Comprehensive documentation**: 80K+ lines of markdown.

9. **Hot-load signature detection**: Using `inspect.signature()` to handle both 2-arg and 4-arg `load_plugin()` is robust against refactors.

10. **SOUL.md risk management**: Clear wallet addresses, mission statement, and risk management framework.

---

*This audit was updated by opencode on April 24, 2026. The most impactful improvements would come from: (P0) sandboxing the autonomous coder and fixing the SkillGenerator crash, (P1) writing tests for the cognitive system and removing the Duat/Synergy overlap, and (P2) decomposing the 3,324-line god class and consolidating the triple autonomous coder.*