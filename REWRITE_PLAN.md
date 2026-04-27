# AlleyBot AGI Rewrite Plan

## Why Rewrite

The current codebase has **133k lines** (75k in src/agentic, 58k in plugins) with deep systemic issues that patching cannot fix:

| Problem | Impact |
|---------|--------|
| **140 files in src/agentic/** (many orphaned) | 20+ files have zero imports — dead code bloating load time and confusing development |
| **72 methods on autonomous_brain.py alone** | No single file should be a 3700-line god class |
| **Two plugin managers** (`plugin_manager.py` + `src/core/plugin_manager.py`) | Plugins import from different paths, causing "not loaded" errors |
| **initialize() crash = plugin gone** | One network hiccup in moltx = entire plugin missing from registry |
| **Dict-of-dicts parsed as lists** | API returns `{data: {posts: [...]}}` but code assumes `{data: [...]}` — crashes silently |
| **Circular coupling** | brain ↔ kernel ↔ router ↔ goals ↔ planner all import each other |
| **48 references to `get_plugin()`** from autonomous_brain alone | Agent reaches deep into plugin internals instead of using clean API |
| **No test coverage for plugin loading** | Bugs like the moltx crash go undetected until runtime |

The result: every fix reveals 3 more bugs. We need a clean foundation.

---

## Architecture Overview

```
alleybot/                      # Clean package structure
├── core/                     # Minimal runtime kernel
│   ├── bus.py                # Event bus (pub/sub, no direct coupling)
│   ├── config.py             # Typed config from .env
│   ├── loop.py               # Main autonomous loop (sense→think→act→learn)
│   ├── plugin_loader.py      # Resilient plugin loading (always register, degrade gracefully)
│   ├── state.py              # Shared agent state (thread-safe, observable)
│   └── errors.py             # Structured error types, not bare exceptions
│
├── brain/                    # AGI cognition (the actual intelligence)
│   ├── sense.py              # Observe world + internal state
│   ├── think.py              # Reason about what to do (LLM-augmented)
│   ├── act.py                # Execute chosen action
│   ├── learn.py              # Update beliefs, skills, goals from outcomes
│   └── reflect.py            # Meta-cognition: am I improving? what do I not know?
│
├── goals/                    # Goal system (clean, not 5 overlapping files)
│   ├── store.py              # SQLite-backed goal CRUD
│   ├── planner.py            # Goal decomposition + ordering
│   └── pursuit.py            # Goal-driven action selection
│
├── memory/                   # Unified memory (3 backends, 1 API)
│   ├── sqlite_store.py       # Persistent key/value + vectors
│   ├── working.py            # Short-term scratchpad
│   └── episodic.py           # Episode storage for learning
│
├── skills/                   # Skill acquisition system
│   ├── registry.py           # What the agent knows how to do
│   ├── learner.py            # Acquire new skills from observation/API
│   ├── executor.py           # Run skills safely (sandboxed, timeout-bounded)
│   └── basis/                # Built-in skills the agent starts with
│       ├── social.py         # Social platform interactions
│       ├── trading.py        # Market analysis + execution
│       ├── research.py       # Information gathering
│       └── coding.py         # Code generation and self-modification
│
├── plugins/                  # External integrations (isolated, optional)
│   ├── base.py               # Plugin protocol (ABC, typed)
│   ├── runner.py             # Safe plugin lifecycle (load/initialize/run/die)
│   └── platforms/            # Platform adapters
│       ├── moltx.py          # MoltX (Twitter for agents)
│       ├── moltchan.py       # Moltchan boards
│       ├── moltroad.py       # Moltroad
│       ├── telegram.py       # Telegram bot interface
│       ├── polymarket.py     # Prediction markets
│       ├── clawbr.py         # Clawbr
│       └── ...
│
├── interfaces/               # Human-agent interaction
│   ├── telegram_bot.py       # Telegram commands handler
│   ├── approval.py           # HITL approval gate
│   └── dashboard.py         # Web dashboard for monitoring
│
└── main.py                   # Single entry point, clean startup
```

---

## Core Principles

### 1. Crash Isolation
Every external call (plugin, API, LLM) runs inside an error boundary. A failure in moltx's first-boot protocol never prevents the plugin from loading. A bad API response never crashes the autonomous loop.

```python
# BEFORE (current):
plugin = plugin_class(config)
plugin.initialize(api, core)          # if this crashes, plugin gone
self.plugins[name] = plugin          # never reached

# AFTER (rewrite):
plugin = plugin_class(config)
try:
    plugin.initialize(api, core)
except Exception as e:
    logger.warning(f"Plugin {name} init partial failure: {e}")
    plugin.health = "degraded"
self.plugins[name] = plugin          # ALWAYS register, even degraded
```

### 2. Event Bus, Not Direct Coupling
No more `self.plugin_manager.get_plugin('moltx')` scattered across 48 locations. Systems communicate through events.

```python
# BEFORE (current):
moltx = self.plugin_manager.get_plugin('moltx')
if moltx and moltx.initialized:
    result = moltx.feed_command('global', 10)

# AFTER (rewrite):
result = await bus.request('social.feed', platform='moltx', feed='global', limit=10)
# If moltx is down, bus returns a degraded response. No crash.
```

### 3. Typed API Responses
Every external API has a response model that handles real-world structures.

```python
@dataclass
class FeedResponse:
    posts: List[Post]
    cursor: Optional[str] = None

    @classmethod
    def from_api(cls, raw: dict) -> 'FeedResponse':
        """Handles {data: {posts: [...]}} OR {data: [...]} OR {posts: [...]}"""
        data = raw.get('data', raw)
        posts = data.get('posts', data) if isinstance(data, dict) else data
        return cls(posts=[Post.from_api(p) for p in (posts or []) if isinstance(p, dict)])
```

### 4. Single Plugin Manager
One canonical plugin loader. Period.

### 5. Delete Dead Code
The following files have **zero imports** and will not be carried over:

- `phase12_commands.py`, `phase12_integration.py`, `phase12_pruning.py`
- `phase13_commands.py`, `phase13_integration.py`, `phase13_ab_testing.py`, `phase13_crisis.py`, `phase13_scheduling.py`, `phase13_trends.py`, `phase13_competitors.py`
- `duat_cognition.py`
- `decision_system_synergy.py`
- `capability_discovery.py`
- `workflow_templates.py`
- `horizontal_connector.py`
- `deepseek_llm.py`
- `DEPRECATED_enhanced_memory.py`

~120k lines of dead code removed immediately.

---

## Migration Plan

### Phase 1: Foundation (3-4 days)
Build the core package with zero legacy code:
- `core/bus.py` — Event bus with typed channels
- `core/config.py` — Typed config
- `core/loop.py` — The autonomous sense→think→act→learn loop
- `core/plugin_loader.py` — Resilient plugin loading
- `core/state.py` — Thread-safe shared state
- `core/errors.py` — Error hierarchy

**Test:** Run a minimal brain cycle that observes nothing but doesn't crash.

### Phase 2: Plugin System (2-3 days)
- `plugins/base.py` — Clean Plugin protocol
- `plugins/runner.py` — Lifecycle manager with health tracking
- Migrate: **moltx**, **moltchan**, **moltroad**, **telegram**, **onchain**, **crypto**
- Each plugin gets typed response models (like `FeedResponse` above)
- Plugin loading always registers, initial failures = degraded mode

**Test:** All 6 platforms load, moltx survives init partial failure, feed parsing works on all response shapes.

### Phase 3: Brain (3-4 days)
- `brain/sense.py` — Collect state from event bus, not plugin_manager
- `brain/think.py` — LLM-augmented reasoning
- `brain/act.py` — Execute via bus requests, not direct method calls
- `brain/learn.py` — Update beliefs from outcomes
- `brain/reflect.py` — Meta-cognition: "what don't I know?"

**Test:** Brain runs a full cycle: sense → think → act → learn with a mock platform.

### Phase 4: Goals & Memory (2-3 days)
- `goals/store.py` — SQLite goal CRUD (carry schema from current goal_manager)
- `goals/planner.py` — Decomposition + ordering
- `goals/pursuit.py` — Goal-driven action selection
- `memory/` — Unified with SQLite, working, episodic backends

**Test:** Agent creates a goal, decomposes it, pursues it, learns from outcome.

### Phase 5: Skills (3-4 days)
- `skills/registry.py` — Known capabilities with confidence scores
- `skills/learner.py` — Acquire skills from platform skill.md, observation
- `skills/executor.py` — Safe execution with timeouts + error boundaries

**Test:** Agent learns a new skill from moltx's skill.md and uses it.

### Phase 6: Interfaces (2-3 days)
- `interfaces/telegram_bot.py` — Migrate commands to bus-based
- `interfaces/approval.py` — HITL for high-risk actions
- `interfaces/dashboard.py` — Web monitoring

**Test:** Send /start in Telegram, get a response. Agent pursues a goal autonomously.

### Phase 7: Curriculum & Shutdown (2-3 days)
- Run old and new side-by-side if needed
- Migrate remaining platforms (clawbr, clawchess, mcp, etc.)
- Transfer all Telegram command handlers
- Final integration test
- Delete old codebase

---

## File-by-File Migration Map

### KEEP (port logic, rewrite structure)

| Current File | Lines | Becomes | Notes |
|---|---|---|---|
| `autonomous_brain.py` | 3698 | `brain/sense.py`, `brain/think.py`, `brain/act.py`, `brain/learn.py` | Split 72 methods into 4 focused modules |
| `goal_manager.py` | 1262 | `goals/store.py` | SQLite schema + CRUD, clean up |
| `goal_planner.py` | 880 | `goals/planner.py` | Decomposition logic |
| `curiosity.py` | 640 | `brain/sense.py` + `goals/pursuit.py` | Split exploration from goal pursuit |
| `planning.py` | 1371 | `goals/planner.py` | Merge with goal_planner |
| `action_router.py` | 1953 | `brain/act.py` + `skills/executor.py` | Routing logic → bus requests |
| `episodic_memory.py` | 763 | `memory/episodic.py` | Clean SQLite backend |
| `sqlite_memory.py` | 730 | `memory/sqlite_store.py` | Same schema, cleaner API |
| `agi_kernel.py` | 1830 | `core/loop.py` + `core/state.py` | 33 methods → event bus |
| `decision_system.py` | 1588 | `brain/think.py` | Merge decision logic |
| `belief_engine.py` | — | `brain/learn.py` | Belief tracking |
| `meta_learner.py` | 729 | `brain/learn.py` + `skills/learner.py` | Outcome learning |
| `error_recovery.py` | — | `core/errors.py` | Structured recovery |
| `console_monitor.py` | 898 | `core/bus.py` subscriber | Skill detection → event |
| `symod_core.py` | — | `core/loop.py` integration | Cycle management |

### KEEP (port as-is, wrap in typed interface)

| Plugin | Lines | Notes |
|---|---|---|
| `moltx/` | ~3400 | Split into `core` (API client) + `social` (commands) + `protocol` (skill.md rules). Add typed response models. |
| `moltchan/` | ~800 | Add typed response models |
| `moltroad/` | ~600 | Minimal changes, add error bounds |
| `telegram/` | ~6000 | Split command handlers into separate files, use bus instead of direct plugin access |
| `onchain/` | ~500 | Port as-is |
| `crypto/` | ~400 | Port as-is |
| `intelligence/` | ~600 | Port as decision engine input |
| `brain/` | ~2100 | Merge into `brain/think.py` |
| `clawbr/` | ~2100 | Port as-is with typed models |
| `polymarket/` | ~740 | Port as-is |
| `selfimprove/` | ~1800 | Merge into `brain/reflect.py` + `skills/learner.py` |
| `mcp/` | ~860 | Port as-is |
| `a2a/` | ~500 | Port as-is |

### DELETE (dead code, zero imports)

~120k lines across 15+ files. See list above.

---

## Key Design Decisions

### 1. Event Bus over Direct Method Calls

```
Current:  autonomous_brain → plugin_manager.get_plugin('moltx') → moltx.feed_command()
Rewrite:  brain → bus.request('social.feed', platform='moltx') → moltx adapter → API
```

Benefits:
- Plugins can crash/restart independently
- New platforms register by subscribing to events
- No import cycles
- Easy to mock for testing

### 2. Typed Response Models for Every API

```python
# Every platform API returns a typed response
@dataclass
class FeedResponse:
    posts: List[Post]
    success: bool
    error: Optional[str] = None
    cursor: Optional[str] = None

# Parsing handles all real-world response shapes
class Post:
    id: str
    author: str
    content: str
    likes: int
    replies: int
    created_at: datetime

    @classmethod
    def from_api(cls, raw: dict) -> 'Post':
        # Handles: {id, author: {name}, content, ...}
        # Handles: {post_id, author_name, text, ...}
        # Handles: {id, author: str, body, ...}
        ...
```

### 3. Plugin Health States

```python
class PluginState(Enum):
    LOADING = "loading"
    HEALTHY = "healthy"
    DEGRADED = "degraded"    # init partially failed, some features work
    FAILED = "failed"        # init fully failed, retry later
    DISABLED = "disabled"    # manually disabled

# Bus checks health before routing:
if await bus.get_state('social.moltx') in (PluginState.HEALTHY, PluginState.DEGRADED):
    result = await bus.request('social.feed', platform='moltx')
```

### 4. Skills as First-Class Citizens

```python
class Skill(Protocol):
    name: str
    confidence: float           # 0-1, how well the agent can do this
    min_confidence: float       # threshold to attempt
    prerequisites: List[str]    # other skills needed
    
    async def execute(self, context: SkillContext) -> SkillResult:
        ...
    
    def assess(self, outcome: SkillResult) -> float:
        """Update confidence based on outcome"""
        ...

# Agent discovers skills from platforms:
# moltx skill.md → parsed → Skill registered → confidence tracked
```

### 5. Self-Improvement Loop

```
┌─────────────────────────────────────────┐
│                                         │
│   sense ──→ think ──→ act ──→ learn     │
│     │                              │     │
│     │         ┌────reflect─────────┘     │
│     │         │                           │
│     │    "Am I improving?"               │
│     │    "What skills do I lack?"         │
│     │    "What failed and why?"           │
│     │         │                           │
│     └───── update beliefs/skills ─────────┘
│                                         │
└─────────────────────────────────────────┘
```

### 6. One Plugin Manager

```python
# core/plugin_loader.py — single source of truth
class PluginLoader:
    def __init__(self, config: Config, bus: EventBus):
        self._plugins: Dict[str, PluginHandle] = {}
        self._bus = bus
    
    async def load(self, name: str) -> PluginHandle:
        """Load plugin. NEVER raises. Returns handle with state."""
        ...
    
    async def load_all(self, config_path: Path) -> None:
        """Load all enabled plugins. Partial failures are OK."""
        ...
    
    def get(self, name: str) -> Optional[PluginHandle]:
        """Returns handle even if plugin is degraded."""
        ...
```

---

## What NOT to Carry Over

1. **Phase 12/13 code** — ~75k lines of dead code, zero imports
2. **Duat cognition** — unused, 14k lines
3. **synergy_constants.py, synergy_decision_engine.py** — replaced by event bus
4. **cross_domain_pattern_detector.py, cross_domain_synthesis.py** — over-engineered for current needs
5. **Two plugin managers** — one is enough
6. **`core.config` vs `core.config()` inconsistency** — typed config struct
7. **God classes** (autonomous_brain, agi_kernel) — split into focused modules
8. **Direct `get_plugin()` calls scattered everywhere** — event bus requests instead
9. **`slice(None, 10, None)` style crashes** — typed response models prevent this class of bug entirely

---

## Testing Strategy

Every module gets tests BEFORE implementation:

```python
# tests/test_plugin_loader.py
def test_load_plugin_init_failure_still_registers():
    """Plugin with crashing initialize() should still be available in degraded state"""
    
def test_feed_response_handles_dict_data():
    """Moltx returns {data: {posts: [...]}} — should parse correctly"""
    
def test_feed_response_handles_list_data():
    """Some APIs return {data: [...]} — should parse correctly"""
    
def test_bus_request_degraded_plugin():
    """Requesting social.feed when moltx is degraded should return graceful fallback"""
```

---

## Quick Start (New Repo)

```bash
mkdir alleybot-v2 && cd alleybot-v2
python -m venv .venv && source .venv/bin/activate
pip install pytest asyncio aiohttp python-dotenv

# Create package structure
mkdir -p alleybot/{core,brain,goals,memory,skills,plugins,interfaces}
touch alleybot/__init__.py alleybot/core/{__init__,bus,config,loop,plugin_loader,state,errors}.py
touch alleybot/brain/{__init__,sense,think,act,learn,reflect}.py
touch alleybot/goals/{__init__,store,planner,pursuit}.py
```

Start with `core/bus.py` and `core/plugin_loader.py` — the two things that broke the most in the current system.