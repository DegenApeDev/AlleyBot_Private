# AlleyBot Agent Framework — Usability Audit

**Auditor**: opencode (automated deep audit)  
**Date**: April 24, 2026  
**Scope**: Full project — architecture, code quality, security, usability, completeness  
**Codebase**: ~163,666 lines of Python across 476 files; ~80,846 lines of Markdown  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture & Structure](#2-architecture--structure)
3. [Core Files Analysis](#3-core-files-analysis)
4. [Source Directory (src/)](#4-source-directory-src)
5. [Plugins](#5-plugins)
6. [Skills System](#6-skills-system)
7. [Configuration & Environment](#7-configuration--environment)
8. [Data & Memory Layer](#8-data--memory-layer)
9. [Security Findings](#9-security-findings)
10. [Code Quality Issues](#10-code-quality-issues)
11. [Missing Features & Incomplete Implementations](#11-missing-features--incomplete-implementations)
12. [Dependency & Coupling Issues](#12-dependency--coupling-issues)
13. [Test Coverage](#13-test-coverage)
14. [Documentation Assessment](#14-documentation-assessment)
15. [Recommendations (Prioritized)](#15-recommendations-prioritized)
16. [Positive Findings](#16-positive-findings)

---

## 1. Executive Summary

AlleyBot is an ambitious autonomous AGI system with a 14-phase cognitive loop, live crypto trading, platform integrations (Telegram, Moltx, Moltbook), and a self-improvement pipeline. The project has excellent documentation and a thoughtful validation architecture, but suffers from significant usability debt: a God class in `autonomous_brain.py` (3,197 lines), ~70 bare exception handlers, 150+ `print()` calls instead of structured logging, synchronous HTTP calls blocking the async event loop, duplicate module names creating confusion about which components are canonical, and critical security vulnerabilities including arbitrary code execution in the autonomous coder and no authentication on API endpoints. Previous audits (AUDIT_KIMIK25APR, AUDIT_TODOK25) identified 37 issues — only P0 items have seen partial remediation.

**Overall Usability Score: 4/10** — The framework works but is fragile, hard to extend, and has dangerous gaps. An operator or developer onboarding onto this system would face significant friction from naming inconsistencies, missing abstractions, and unclear boundaries between components.

---

## 2. Architecture & Structure

### 2.1 Cognitive Architecture

The system implements a **14-phase AGI cognitive loop**: SENSE → THINK → VALIDATE → ACT → REFLECT. This is documented in `SYSTEM_MAP.md` with a Mermaid diagram that aligns well with the implementation.

| Component | Lines | Role |
|-----------|-------|------|
| `autonomous_brain.py` | 3,197 | God class — all 14 phases |
| `agi_kernel.py` | 1,805 | Consciousness layer, memory/goals/metacognition |
| `action_router.py` | 1,871 | 12-stage validation pipeline |
| `plugin_manager.py` | 361 | Plugin lifecycle & hot-reload |
| `alleybot_core.py` | 693 | Orchestrator / entry point |

**Platforms integrated**: Moltx, Clawbr, Moltbook, Moltchan, Moltbit, Moltroad, Telegram, Solana/Jupiter, Base/Uniswap, Polymarket.

### 2.2 Architecture Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| **God Class** | HIGH | `autonomous_brain.py` contains 14+ phase methods, plugin coordination, goal management, skill building, and trading — all in one 3,197-line file. Violates Single Responsibility Principle. |
| **Circular Imports** | MEDIUM | `agi_kernel.py` ↔ `action_router.py` via `ModelProvider`. Flagged in prior audit; still present. |
| **Import Churn** | MEDIUM | `agi_kernel.py` has 47 lines of imports from 28 modules creating brittle coupling. |
| **Dual Plugin Base Classes** | HIGH | `AlleyBotPlugin` (sync, 44 lines, in `plugin_manager.py`) vs `BasePlugin` (async-aware, 424 lines, in `plugins/base_plugin.py`). Most plugins use the sync version, creating two incompatible paradigms. |
| **Monolithic Memory Layer** | HIGH | 14+ SQLite databases alongside 31 JSON files. `world_state.db` is 98MB. No unified schema, no migration system. |
| **Root Directory Clutter** | MEDIUM | 50+ markdown files at project root, many overlapping or partial (COMPLETE_REWRITE.md, UPGRADED.md, hermes.md, alley_claw.md, BUGREPORT.md, etc.). |

### 2.3 Naming Confusion (Usability Killer)

Multiple overlapping module names make it extremely unclear which is canonical:

| Concept | Files Found |
|---------|-------------|
| Decision system | `decision_system.py` vs `decision_system_synergy.py` |
| Meta-learning | `meta_learner.py` vs `meta_learning.py` vs `metacognition.py` vs `meta_cognition_engine.py` |
| Goals | `goal_generator.py` vs `goal_manager.py` vs `goal_hierarchy.py` vs `goal_stack.py` vs `goal_detector.py` vs `default_goals.py` |
| Skills | `skill_generator.py` vs `skill_tester.py` vs `skill_executor.py` vs `skilldoc_manager.py` vs `auto_skill_builder.py` |
| Agent | `agentic_system.py` vs `simple_agent.py` vs `react_agent.py` vs `autonomous_brain.py` |
| Plugin manager | `plugin_manager.py` (root) vs `src/core/plugin_manager.py` |

A new developer cannot determine which module to use or extend without reading all variants. This is the single biggest usability problem in the framework.

---

## 3. Core Files Analysis

### 3.1 `alleybot_core.py` (693 lines) — Entry Point / Orchestrator

| Issue | Severity | Detail |
|-------|----------|--------|
| Print-based logging | MEDIUM | 101 `print()` calls, no `logging` module |
| Silent failure | HIGH | Multiple `except Exception as e: print(...)` patterns swallow errors |
| JSON memory fallback | LOW | `save_memory()`/`get_memory()` still write JSON despite SQLite availability |
| Blocking scheduler | MEDIUM | `schedule` library with `time.sleep(60)` blocks the thread |
| Mixed sync/async | HIGH | Daemon threads + async event loop without proper coordination |
| Hardcoded constants | LOW | `schedule_interval: 60`, `max_days=7` not configurable |

### 3.2 `config.py` (26 lines) — Configuration

| Issue | Severity | Detail |
|-------|----------|--------|
| **Missing env vars** | CRITICAL | Only 26 lines. Missing TELEGRAM_BOT_TOKEN, SOLANA_WALLET_PRIVATE_KEY, PINATA_JWT, POLYMARKET_API_KEY and many others actually used by plugins. |
| No validation | HIGH | No type checking, range checking, or presence validation for critical config. A missing `SOLANA_PRIVATE_KEY` would cause a runtime `None` != `str` failure. |
| Confusing alias | LOW | `WALLET_ADDRESS = BTC_WALLET` makes intent unclear |
| Hardcoded URLs | MEDIUM | Platform base URLs hardcoded here, but other URLs scattered across plugins |

### 3.3 `web_server.py` (625 lines) — Dashboard

| Issue | Severity | Detail |
|-------|----------|--------|
| Inline HTML | LOW | ~140 lines of raw HTML/JS/CSS for chess board embedded in Python. Should be in `templates/`. |
| **No authentication** | HIGH | No auth on any API endpoint (`/api/status`, `/api/stats`, `/api/chess`) or WebSocket connections. |
| **CORS wide open** | CRITICAL | `allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods="*"`. Any origin can access. |
| Bare except handlers | MEDIUM | Multiple `except Exception as e: print(...)` |
| Hardcoded port | LOW | `port: int = 8080` with no env var override |
| Chess-centric | LOW | Dashboard is chess-specific, not a general AGI dashboard |

### 3.4 `plugin_manager.py` (361 lines) — Plugin Lifecycle

| Issue | Severity | Detail |
|-------|----------|--------|
| **Bare except** | HIGH | Line 214-215: `except: error_str = "Exception details unavailable"` — completely swallows exceptions |
| No plugin validation | MEDIUM | Imports by naming convention (`plugins.{name}.{name}`) with no interface verification |
| Force reload risk | MEDIUM | `importlib.reload()` can break stateful plugins |
| No dependency resolution | MEDIUM | Plugins loaded in config order with no topological sort |
| Missing health_check | MEDIUM | SOP mandates `health_check()` but no plugin implements it |

### 3.5 `autonomous_coder.py` (392 lines) — Self-Improvement Pipeline

| Issue | Severity | Detail |
|-------|----------|--------|
| **Command injection** | CRITICAL | Line 163-170: `subprocess.run(["python", "-c", test], ...)` executes arbitrary LLM-generated code. No real sandboxing. |
| **Arbitrary pip install** | CRITICAL | Lines 157-159: `pip install -q` with LLM-generated dependency lists. Arbitrary package installation. |
| Incomplete rollback | MEDIUM | `_backup_deployed()` only copies JSON metadata, not actual code |
| Print-based logging | LOW | No `logging` module |

### 3.6 `autonomous_skill_workflow.py` (415 lines) — Skill Generation

| Issue | Severity | Detail |
|-------|----------|--------|
| **Broken imports** | HIGH | `from comprehensive_logger import logger` — module doesn't exist. Runtime crash. |
| **Broken import** | HIGH | `from skill_generator import SkillGenerator` — exists in `src/agentic/`, not at root. |
| Hardcoded outputs | MEDIUM | `_analyze_error_patterns()` returns a single static placeholder. `_analyze_community_requests()` returns a single hardcoded idea. |

### 3.7 `deepseek_ai.py` (323 lines) — DeepSeek LLM Client

| Issue | Severity | Detail |
|-------|----------|--------|
| **Sync HTTP in async context** | HIGH | Uses `requests.post()` (synchronous) throughout. Blocks the event loop. |
| Global singleton | MEDIUM | `deepseek_ai = DeepSeekAI()` on import — fails silently if API key missing |
| No retry logic | MEDIUM | Single HTTP call with `timeout=30`, no exponential backoff |
| Model hardcoding | LOW | `deepseek-v4-flash` / `deepseek-v4-pro` hardcoded, not configurable |
| Fragile prompt hack | LOW | Appends "IMPORTANT: Create unique..." to every system prompt via string check |

### 3.8 `grok_ai.py` (524 lines) — Grok (xAI) LLM Client

| Issue | Severity | Detail |
|-------|----------|--------|
| **Sync HTTP in async context** | HIGH | Same blocking `requests` issue as DeepSeek |
| Model routing | LOW | Has `route_task()` for model tiers — good design, but synchronous |
| Global singleton | MEDIUM | `grok_ai = GrokAI()` created on import |
| Print-based logging | LOW | Multiple `print()` instead of `logging` |

### 3.9 `mcp_client.py` (241 lines) — MCP Client

| Issue | Severity | Detail |
|-------|----------|--------|
| In-memory cache only | LOW | Cache is a dict with TTL, not persisted |
| No reconnection | MEDIUM | If initial connection fails, `self.connected = False` and all subsequent calls return `{"error": "MCP not connected"}` silently |
| Missing default URL | LOW | `server_url` defaults to `None`, making all methods no-ops |

### 3.10 `moltbook_api.py` (259 lines) — Moltbook Client

| Issue | Severity | Detail |
|-------|----------|--------|
| No error handling | HIGH | Every method uses `response.raise_for_status()` — unhandled exceptions on any HTTP error |
| No retry logic | MEDIUM | No backoff on transient failures |
| Synchronous only | MEDIUM | All calls block |
| Duplicate of plugin | LOW | `moltbook_api.py` and `plugins/moltbook/moltbook.py` both interact with the same platform |

### 3.11 `security_filter.py` (189 lines) — Response Security Filter

| Issue | Severity | Detail |
|-------|----------|--------|
| **Well-designed output filter** | — | Scans exact env var values AND regex patterns. TxRegistry integration smartly distinguishes tx hashes from private keys. Auto-detects secret env vars by key name. |
| **No input filtering to LLMs** | MEDIUM | Filters bot responses effectively but does NOT filter external content before it enters LLM prompts. Prompt injection via Moltx/Telegram content is still possible — though the output filter would catch leaked secrets in the response. |
| Print for security | LOW | Line 143 uses `print()` instead of `logging.warning()` |

### 3.12 `tx_registry.py` (78 lines) — Transaction Hash Registry

| Issue | Severity | Detail |
|-------|----------|--------|
| Not truly FIFO | LOW | `set.pop()` is arbitrary, not guaranteed to remove oldest |
| No persistence | MEDIUM | Lost on restart. Previously known TX hashes will be redacted in messages after restart. |

---

## 4. Source Directory (src/)

### 4.1 `src/agentic/` (142 Python files, ~71,161 lines)

This is the heart of the system. Key files:

| File | Lines | Issues |
|------|-------|--------|
| `autonomous_brain.py` | 3,197 | God class. 49 exception handlers (many bare). 110+ print statements. |
| `agi_kernel.py` | 1,805 | 110 print statements. 10 bare exception handlers. Circular imports. |
| `action_router.py` | 1,871 | 11 exception handlers. Complex validation pipeline (well-designed). |
| `goal_manager.py` | ~1,200 | SQL-blocking-called-from-async. Hardcoded fallback mappings. |

**Well-architected components**:
- `action_router.py`: 12-stage validation ladder with fail-closed design. This is the best-designed component in the codebase.
- `base_sqlite_store.py`: New async SQLite abstraction (from recent remediation).
- `contracts.py`: Proper dataclasses with `__post_init__` validation.

### 4.2 `src/core/` (7 files)

- **Duplicate `plugin_manager.py`**: Both `src/core/plugin_manager.py` AND root `plugin_manager.py` exist. Root version is used from `alleybot_core.py`.
- `llm_router.py`: Model routing — good design but underutilized.

### 4.3 `src/trading/`

Contains only `performance_tracker.py`. Most trading logic lives in plugins — creates fragmented understanding of where trading code lives.

### 4.4 `src/cognition/`

Philosophical/Synergy Research components (`fairmind_integration.py`, `value_dynamics.py`, `duat_enhanced.py`, `truth_violations.py`). Limited documentation connecting these to the main cognitive loop. A developer would not know when or how these are invoked.

---

## 5. Plugins

35+ plugin directories. Key findings:

| Issue | Severity | Detail |
|-------|----------|--------|
| **Inheritance inconsistency** | HIGH | Most plugins inherit from `AlleyBotPlugin` (sync, minimal) instead of `BasePlugin` (async-aware, well-designed). The superior `BasePlugin` in `plugins/base_plugin.py` (424 lines) with `AsyncPluginMixin` and `PluginRegistry` is largely unused. |
| No health checks | MEDIUM | Despite `SOP.md` mandating `health_check()`, no plugin implements it |
| Mixed quality | MEDIUM | Some plugins are thin wrappers, others contain substantial logic with no consistency |
| Archived plugins | LOW | `plugins_archive/experimental/` contains 6 dead plugins |

**Well-implemented plugins**: `polymarket/` (multi-file structure, proper separation), `solana_trading/`, `solana_token_analysis/` (separate API client file).

**Plugin usability problem**: A plugin developer must choose between two base classes (`AlleyBotPlugin` vs `BasePlugin`), two different patterns (sync vs async), and the superior option (`BasePlugin`) has no documentation or examples showing its use. This is a major onboarding friction point.

---

## 6. Skills System

- 30+ skill directories in `skills/`
- `dynamic_skills/` is **empty** — the self-improvement architecture generates no skills yet
- Skills follow `SKILL.md` + Python implementation pattern
- Some skill files are loose `.py` files not in directories (`palindrome.py`, `text_utility.py`) — inconsistent
- `auto_acquired/` and `imported/` subdirectories exist but appear unused
- **Naming inconsistency**: Mix of `PascalCase`, `kebab-case`, `snake_case` in directory names

The skills system is a usability dead end for new developers — no `README` in the `skills/` directory explaining how to create, test, or register a skill.

---

## 7. Configuration & Environment

### 7.1 `config.py` (26 lines)

Critically minimal. Only loads a fraction of environment variables actually used by the system. No validation, no type checking, no defaults documentation.

### 7.2 `config/` directory

Only 2 files: `core.json` and `hermes_tools_config.yaml`. Missing: `logging.json`, `trading.json`, `plugins.json`. Configuration is scattered across env vars, `plugin_config.json` (at root), and hardcoded defaults.

### 7.3 `.env.example`

Contains placeholder values (`your_xxx_here`). Does not document all required env vars. Trading risk parameters are present which is good.

### 7.4 `requirements.txt` (17 lines)

| Issue | Severity | Detail |
|-------|----------|--------|
| Outdated langchain | MEDIUM | `langchain>=0.1.0,<0.3.0` — should be `>=0.3.0` |
| No version pinning | HIGH | `requests`, `flask`, `aiohttp` have no version constraints. CI/build reproducibility risk. |
| Questionable deps | LOW | `python-chess>=1.999`, `stockfish>=4.0.0` — chess-specific, should be optional |
| Missing deps | MEDIUM | No `aiosqlite` (needed for async SQLite), no `tenacity` (for retries), no `prometheus-client` |

---

## 8. Data & Memory Layer

### 8.1 SQLite Databases (14+ in `data/`)

| Database | Size | Concern |
|----------|------|---------|
| `world_state.db` | 98MB | **Extremely large** for SQLite. Performance risk. |
| `plans.db` | 5.8MB | |
| `strategies.db` | 3.5MB | |
| `creative.db` | 2.1MB | |
| `memory.db` | 844KB | |
| `alley_memory.db` | 0 bytes | **Empty**. Possible initialization bug. |
| `symod_state.db` | 0 bytes | **Empty**. SyMod state not being persisted? |

- No database migration system (no Alembic, no version tracking)
- No backup/rotation strategy
- No indexing strategy documented

### 8.2 JSON Memory Files (31 files in `memory/`)

This is the **legacy fallback system**. JSON files like `moltx_api_tips.json`, `moltx_api_version.json`, `moltx_endpoints.json` should be in config, not memory. No schema validation. No transactional safety.

**Usability issue**: A developer must understand both the SQLite system AND the JSON fallback system, and know which subsystem uses which. This doubles the learning curve.

---

## 9. Security Findings

### 9.1 SECRETS PROTECTION — WELL-DESIGNED (with caveats)

`security_filter.py` provides robust output-side protection for `.env` secrets:
- **Exact-value matching**: Loads all secret env vars and redacts them as `[REDACTED]`
- **Pattern matching**: Catches API keys by prefix (`sk-`, `xai-`, `moltx_sk_`, etc.), private key formats, Telegram tokens, PEM keys
- **Auto-detection**: Scans all env vars for anything containing `PRIVATE`, `SECRET`, `TOKEN`, `API_KEY`, `PASSWORD`
- **TxRegistry integration**: Distinguishes legitimate transaction hashes from private keys to avoid false redactions
- **Error sanitization**: Strips file paths from error messages
- **Convenience functions**: `filter_bot_response()` and `is_safe_response()` for easy use

**Remaining caveats**:
- The `.env` file is still readable in the workspace (file-level access). Protection is output-side only — a process crash log, debugger, or `cat .env` bypasses the filter.
- `bfg.jar` (git history rewriting tool) is tracked in git — unusual, though not a direct secret risk.
- Development workspace exposure: any developer with file access can read `.env`.

### 9.2 CODE INJECTION IN AUTONOMOUS CODER — CRITICAL

`autonomous_coder.py` lines 163-170: Runs `subprocess.run(["python", "-c", test], ...)` with LLM-generated code. Lines 157-159: `pip install -q` with LLM-generated dependency lists. No Docker sandbox, no process isolation.

### 9.3 NO INPUT FILTERING TO LLMs — HIGH

`security_filter.py` provides strong output-side secret protection (exact-value matching, pattern matching, auto-detection, TxRegistry integration). However, it does NOT filter external content before it enters LLM prompts — prompt injection via Moltx/Telegram content could manipulate LLM behavior, though the output filter would catch any secrets that leak out.

### 9.4 CORS WIDE OPEN — HIGH

`web_server.py`: CORS allows all origins, all methods, all headers, with credentials enabled. This means any website can make authenticated cross-origin requests.

### 9.5 NO AUTHENTICATION — MEDIUM

Dashboard and API endpoints have no authentication. WebSocket connections unauthenticated. Telegram bot token is the only auth mechanism.

### 9.6 NO RATE LIMITING — MEDIUM

No rate limiting on any API calls (inbound or outbound). Vulnerable to abuse and DoS.

---

## 10. Code Quality Issues

| Category | Count | Severity | Impact on Usability |
|----------|-------|----------|---------------------|
| Bare `except` handlers | ~70 | HIGH | Errors are invisible. Debugging is extremely difficult. |
| `print()` instead of `logging` | ~150+ | MEDIUM | No log levels, no structured output, no log aggregation |
| Synchronous HTTP in async context | 4 clients | HIGH | Blocks event loop, causes timeouts and hangs |
| Missing error handling (HTTP) | 3 clients | HIGH | `raise_for_status()` with no catch |
| God class (autonomous_brain.py) | 1 instance | MEDIUM | Impossible to understand in one reading |
| Duplicate module names | ~8 groups | MEDIUM | Cannot determine canonical implementation |
| Missing input validation | Widespread | MEDIUM | Config, dataclasses, APIs all accept unvalidated input |
| Missing retry logic | 3 clients | MEDIUM | Transient failures cause cascading failures |
| Missing type hints | Widespread | LOW | IDE support and refactoring are harder |
| Dead code / unused imports | Multiple files | LOW | Increases cognitive load |
| Magic numbers | Throughout | LOW | `max_actions=50`, `schedule_interval=60`, etc. not named constants |
| No DB migrations | 14+ databases | MEDIUM | Schema changes are manual and error-prone |

---

## 11. Missing Features & Incomplete Implementations

| Feature | Status | Usability Impact |
|---------|--------|-------------------|
| Circuit breaker | Not implemented | External service failures cascade |
| Rate limiting | Not implemented | Vulnerable to API abuse |
| Health check endpoint | Not implemented | No operational visibility |
| Structured logging | Not implemented | No observability into agent behavior |
| Prometheus metrics | Not implemented | No quantitative monitoring |
| Database migrations | Not implemented | Schema changes are manual |
| Comprehensive tests | ~2,500 lines / 163K code | 1.5% coverage. Unsafe to refactor. |
| Plugin health checks | Not implemented | SOP mandates them but none exist |
| `openhome_abilities/` | **Empty directory** | Dead path in codebase |
| `dynamic_skills/` | **Empty directory** | Self-improvement generates no skills |
| BaseSQLiteStore adoption | Partial | Only some modules migrated |
| Input validation | Partial | `__post_init__` added to some contracts, not all |

---

## 12. Dependency & Coupling Issues

| Issue | Description | Usability Impact |
|-------|-------------|-------------------|
| Circular imports | `agi_kernel.py` ↔ `action_router.py` via `ModelProvider` | Import order matters, breakage risk |
| Deep coupling | `autonomous_brain.py` imports from 30+ modules | Changes anywhere can break the brain |
| Dual plugin systems | `AlleyBotPlugin` (sync) vs `BasePlugin` (async) | Plugin developers don't know which to use |
| Singletons everywhere | `grok_ai`, `deepseek_ai`, `mcp_client`, `tx_registry` | No dependency injection, hard to test |
| No dependency injection | Components instantiated directly | Cannot swap implementations for testing |
| Mixed sync/async | LLM clients synchronous, brain async, plugins mixed | Event loop blocking, callback hell |
| Global state | `config.py` loads env vars as module-level globals | Order-dependent initialization, no reload |

---

## 13. Test Coverage

- 7 test files totaling ~2,527 lines
- Test files organized by implementation phase (`test_phase3.py`, `test_phase4.py`, etc.) not by module
- **No `conftest.py`**, no `pytest.ini`, no `tox.ini`
- Root-level test files (`test_hermes_tools.py`, `check_telegram_handlers.py`) outside `tests/`
- **No unit tests** for recent components: `owner_objectives`, `persistent_intent`, `strategic_planner`, `cross_domain_synthesis`, `work_item_manager`, `domain_autonomy_manager`
- **No load/stress tests**: No verification of resource bounds under load
- Coverage ratio: ~1.5% of total codebase — effectively untested

**Usability impact**: The lack of tests makes the framework extremely risky to modify. Any change could break something without detection. This is a critical barrier to contribution.

---

## 14. Documentation Assessment

| Document | Quality | Notes |
|----------|---------|-------|
| README.md | EXCELLENT | Comprehensive overview, architecture diagram, command list. |
| SYSTEM_MAP.md | EXCELLENT | Mermaid diagram of cognitive loop. Accurate. |
| SOUL.md | GOOD | Character definition, trading strategy, risk management. |
| SOP.md | GOOD | Architecture invariants, plugin development guide, anti-patterns. |
| AGENTIC_BEHAVIOR.md | GOOD | Self-extension pipeline, lifecycle, safety bounds. |
| TODO_CORE.md | EXCELLENT | Phased TODO with checkboxes and success criteria. |
| HANDOVER.md | GOOD | Clear next priorities. |
| AUDIT_KIMIK25APR.md | EXCELLENT | 37 issues across 8 categories. |
| AUDIT_TODOK25.md | EXCELLENT | Detailed remediation plan with effort estimates. |
| ACTION_FLOW.md | COMPREHENSIVE | 7-phase migration roadmap. |
| HEARTBEAT.md | MINIMAL | Only 3 lines of content. Misleading — referenced elsewhere as substantial. |
| **50+ root markdown files** | POOR | Overwhelming clutter. Many are partial/overlapping. |

**Key usability documentation gap**: There is no `docs/` directory organizing this content. A new developer sees 50+ markdown files at root level with no clear reading order. The README is excellent but the supporting docs are a maze.

**Missing documentation**:
- No plugin development tutorial (SOP.md has brief notes but no walkthrough)
- No skill creation guide
- No configuration reference
- No API endpoint documentation
- No deployment guide (beyond `start_dashboard.sh`)

---

## 15. Recommendations (Prioritized)

### P0 — Immediate (Security & Stability)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 1 | **Review `.env` access policies** — security_filter protects bot output well, but file-level access still exposes keys; consider vault/secret management | 1h | Medium |
| 2 | **Sandbox autonomous coder** — Docker/process isolation for LLM-generated code | 4h | Critical |
| 3 | **Authenticate API endpoints** — add API key auth to `web_server.py` | 2h | High |
| 4 | **Narrow CORS** — restrict to specific origins | 1h | High |
| 5 | **Add input sanitization** — before external content enters LLM prompts (output filter is strong but input side is unprotected) | 4h | Medium |

### P1 — This Week (Reliability)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 6 | **Replace `print()` with `logging`** — 150+ instances across codebase | 4h | High |
| 7 | **Fix all bare `except`** — replace with `except Exception as e` + `logging.error()` | 3h | High |
| 8 | **Migrate remaining SQLite modules** to `BaseSQLiteStore` | 8h | High |
| 9 | **Add retry with backoff** — DeepSeek, Grok, Moltx, MCP clients | 4h | High |
| 10 | **Unify plugin base class** — migrate all plugins from `AlleyBotPlugin` to `BasePlugin` | 6h | High |
| 11 | **Complete config.py** — add all used env vars with validation and defaults | 3h | Medium |
| 12 | **Fix broken imports** in `autonomous_skill_workflow.py` | 1h | High |

### P2 — Next Sprint (Code Quality)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 13 | **Decompose `autonomous_brain.py`** — extract phases into separate modules | 16h | High |
| 14 | **Consolidate duplicate modules** — deprecate or merge overlapping names | 8h | High |
| 15 | **Organize root docs** — move 50+ markdown files to `docs/` with index | 3h | Medium |
| 16 | **Add database migration system** — version tracking for all .db files | 8h | Medium |
| 17 | **Write unit tests** — target 50% coverage on `src/agentic/` core | 24h | High |
| 18 | **Pin dependency versions** — add version constraints to requirements.txt | 2h | Medium |
| 19 | **Add type hints** — start with `src/agentic/` core modules | 16h | Medium |

### P3 — Future (Architecture)

| # | Recommendation | Effort | Impact |
|---|---------------|-------|--------|
| 20 | **Implement circuit breaker** — for all external service integrations | 8h | High |
| 21 | **Add Prometheus metrics** — brain cycles, action success rates, DB query times | 8h | Medium |
| 22 | **Add `/health` endpoint** — check DBs, plugins, external services | 4h | Medium |
| 23 | **Address 98MB `world_state.db`** — add indexing, data archival, consider PostgreSQL | 16h | High |
| 24 | **Consolidate memory layer** — eliminate JSON fallback, unified SQLite schema | 16h | High |
| 25 | **Async LLM clients** — convert DeepSeek, Grok, MCP, Moltbook to async HTTP | 8h | High |
| 26 | **Upgrade langchain** — from 0.1.x/0.2.x to 0.3.x+ | 8h | Medium |
| 27 | **Dependency injection framework** — replace module-level singletons | 16h | High |

---

## 16. Positive Findings

The audit also identified several significant strengths:

1. **ActionRouter validation ladder**: 12-stage validation with fail-closed design, Synergy validation, and HITL gating for high-risk actions. This is the best-designed component in the codebase and should be the model for other subsystems.

2. **Security filter + TxRegistry**: Smart pattern for distinguishing transaction hashes from private keys. `security_filter.py` scans both exact env var values and regex patterns.

3. **BaseSQLiteStore**: The new async SQLite base class properly addresses the prior audit's P0-002/P0-003 findings with connection pooling and proper async patterns.

4. **BasePlugin abstract class**: The 424-line `plugins/base_plugin.py` is well-designed with `AsyncPluginMixin`, `PluginRegistry`, proper documentation, and background task management. The problem is only that it's unused.

5. **Comprehensive documentation**: 80K+ lines of markdown including architecture diagrams, SOPs, handover docs, and audit reports. The README and SYSTEM_MAP are genuinely excellent.

6. **Self-improvement architecture**: The detect-propose-build-deploy cycle with human approval gates is thoughtfully designed, even if the sandboxing is dangerous.

7. **Contracts system**: `contracts.py` uses proper dataclasses with `__post_init__` validation and validation profiles (strict, permissive, custom).

8. **14-phase cognitive architecture**: Well-documented and the implementation aligns with the specification.

9. **Audit history**: Two prior audits (AUDIT_KIMIK25APR, AUDIT_TODOK25) were thorough and produced actionable remediation plans. Partial progress is visible.

10. **SOUL.md risk management**: Clear wallet addresses, mission statement, and risk management framework with position limits and max drawdown rules.

---

*This audit was generated by opencode as a comprehensive usability review of the AlleyBot agent framework. The most impactful improvements would come from consolidating duplicate modules (P2-14), decomposing the God class (P2-13), unifying the plugin system (P1-10), and adding structured logging (P1-6). The most urgent actions are sandboxing the autonomous coder (P0-2) and rotating exposed secrets (P0-1).*