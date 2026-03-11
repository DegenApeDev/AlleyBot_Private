# AlleyBot - Autonomous AGI with Live Trading

**AGI Architecture: 14-Phase Cognitive System | Live Trading: 4 Platforms | Status: Production-Ready**

AlleyBot is a sovereign autonomous intelligence with structured cognition, live crypto trading capabilities, and self-improvement architecture. It combines a 14-phase AGI kernel with economic agency—observing markets, reasoning about opportunities, executing trades, and learning from outcomes.

---

## What AlleyBot Is

**Not a bot. An AGI prototype with economic capability.**

Three weeks ago, AlleyBot was a social media automation framework. Today, it is a **production-ready autonomous trading AGI** with:

- **14-phase cognitive architecture** (perception → reasoning → action → reflection)
- **Live trading across 4 platforms** (Solana, Base, Polymarket, multi-aggregators)
- **35+ skill ecosystem** with auto-acquisition
- **6-tier memory system** (episodic, world state, metacognition)
- **Self-improvement pipeline** (risk-classified auto-deployment)
- **Owner-controlled Telegram interface** (25+ commands)

**Codebase:** 40,000+ lines | **Architecture:** Complete AGI rewrite | **Status:** Live trading enabled

---

## Core Capabilities

### 🧠 14-Phase AGI Architecture

**Not just an LLM with tools. Structured cognition.**

| Phase | Function | Capability |
|-------|----------|------------|
| P1 | Self-Reflection | Action logging, outcome tracking |
| P2 | Goal Management | Autonomous goal generation |
| P3 | Multi-Step Planning | Dependency tracking, contingency planning |
| P5/P10 | Causal Understanding | `/causal`, `/why`, `/whatif` commands |
| P7 | World State Intelligence | `/trends`, `/predict`, `/anomalies` |
| P8 | Self-Reflective Learning | Strategy evolution |
| P9 | Multi-Step Reasoning | Long-horizon planning |
| P11 | Autonomous Research | Curiosity-driven knowledge acquisition |
| P12 | Social Intelligence | Agent modeling, deception detection |
| P13 | Creative Generation | Novel content, A/B testing |
| P14 | Metacognition | Confidence calibration, strategy fitness |

**Key insight:** Each phase is a specialized cognitive module. The AGI Kernel (`src/agentic/agi_kernel.py`) orchestrates them into coherent thought.

### 💰 Live Trading Engine

**From zero trading to 4 live platforms in 3 weeks.**

| Platform | Status | Features | Command |
|----------|--------|----------|---------|
| **Solana** | ✅ LIVE | Jupiter Aggregator, MEV protection | `/swap_sol <from> <to> <amount>` |
| **Base L2** | ✅ LIVE | Uniswap V3, gas optimization | `/swap_base <from> <to> <amount>` |
| **Polymarket** | ✅ Paper + Live | CLOB trading, binary markets | `/polymarket_enable_live` |
| **Best Swap** | ✅ LIVE | 6 DEX aggregators, 5 chains | `/best_swap_quote/execute/compare` |

**Aggregators Compared:** 1inch · Paraswap · 0x · Kyber · Odos · OKX

**Performance Tracking:**
- PnL calculation (per-trade and aggregate)
- Win rate analysis by strategy
- Max drawdown measurement
- Edge calculation (expected value)
- Strategy fitness scoring (`/trading_status`)

### �️ SyMod Validation (Truth Gating)

**Physics-based validation before action.**

Every meaningful action passes through **SyMod**:
- **Truth:** Aligns with verifiable facts?
- **Impedance:** Meets resistance in world model?
- **Impact:** Consequence assessment
- **Risk:** Low/Medium/High classification
- **Trust:** Within authorized parameters?

**Action Router:** Routes actions based on impact + risk + trust scoring.

### 🎯 Skills Ecosystem (35+)

**Auto-acquiring, self-improving capability system.**

**Core Skills:**
- `best-crypto-swap-price` - Multi-aggregator trading
- `content-strategy` - Social media optimization
- `reputation-builder` - Community engagement
- `skill-autonomous` - Heartbeat execution
- `skill-format-adapter` - OpenClaw/ElizaOS import

**Auto-Acquisition Flow:**
```
API Response → Console Monitor → Parse → Download → Validate → Register → Notify
```

The system detects skill announcements from platform APIs and auto-acquires them.

### 💾 Multi-Tier Memory Architecture

**Persistent cognition, not stateless responses.**

| Memory Type | Function | Storage |
|-------------|----------|---------|
| **Episodic** | Experiences with emotional valence | `alley_memory.db` |
| **World State** | Entities, facts, relationships | `world_state.db` |
| **Action Logger** | Every action + outcome (audit trail) | `action_log.db` |
| **Creative DB** | Concepts + A/B test results | `creative.db` |
| **Metacognition** | Strategy fitness scores | `metacognition.db` |
| **Unified** | Vector search across all types | `unified_memory.db` |

**Integration:** Episodic + Actions + Creative → World State (each cognitive cycle)

### 🌐 Multi-Platform Social Engine

**Unified interface for 6 social platforms.**

| Platform | Type | Integration |
|----------|------|-------------|
| **Moltx** | Twitter-like | Posts, DMs, feed, trending |
| **Clawbr** | Debate network | AI arena, brain-integrated |
| **Moltbook** | Reddit-like | Articles, threads, heartbeat |
| **Moltchan** | Community chat | Real-time engagement |
| **Moltbit** | Trading signals | Market intel sharing |
| **Moltroad** | Project tracking | Roadmaps, features |

**Cross-Platform Campaigns:** `/multi_platform [topic]` executes across all platforms simultaneously.

### 🔧 Self-Improvement Pipeline

**The system improves itself.**

**Flow:**
```
Failure Detection (2-3 patterns) → Draft Creation → Test Execution → Risk Classification → Deploy
```

**Risk Classification:**
- **Low:** Auto-deploy
- **Medium:** Notify owner
- **High:** Require approval

**Commands:**
- `/improve_drafts` - View pending improvements
- `/improve_approve [draft]` - Deploy approved
- `/improve_metrics` - Improvement statistics

### 🔌 Service Layer (6 Microservices)

**Production-grade architecture.**

| Service | Function |
|---------|----------|
| **Conversation** | Multi-platform message handling |
| **Identity** | Agent card (ERC-8004) |
| **Memory** | Unified memory operations |
| **Owner Notification** | Secure Telegram alerts |
| **Work Item** | Async task queuing |
| **Integration** | Service orchestration |

---

## Quick Start

### 1. Installation
```bash
git clone https://github.com/DegenApeDev/AlleyBot.git
cd AlleyBot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with required keys:
# - TELEGRAM_BOT_TOKEN (owner control)
# - MOLTBOOK_API_KEY (social platforms)
# - GROK_API_KEY / OPENAI_API_KEY (cognition)
# - SOLANA_PRIVATE_KEY (Solana trading)
# - BASE_PRIVATE_KEY (Base trading)
# - POLYMARKET_API_KEY (prediction markets)
```

### 3. Run AlleyBot
```bash
# Production mode (recommended)
python alleybot_core.py autonomous

# Interactive mode
python alleybot_core.py interactive
```

### 4. Activate Brain (Telegram)
Send `/brain_start` to activate autonomous mode.

---

## Telegram Commands (25+)

### AGI Control
| Command | Description |
|---------|-------------|
| `/agi_cycle` | Full 14-phase cognitive cycle |
| `/multi_platform [topic]` | Cross-platform campaign |
| `/trends` | Detect market/social trends |
| `/predict` | Trend prediction |
| `/anomalies` | Anomaly detection |
| `/sentiment` | Sentiment analysis |
| `/causal` | Causal analysis |
| `/why [event]` | Root cause analysis |
| `/whatif [scenario]` | Counterfactual reasoning |
| `/root_cause [event]` | Attribution analysis |
| `/attribution [action]` | Outcome attribution |

### Trading Commands
| Command | Description |
|---------|-------------|
| `/best_swap_quote <network> <from> <to> <amount>` | Get best swap price |
| `/best_swap_execute <network> <from> <to> <amount>` | Execute swap |
| `/best_swap_compare <network> <from> <to> <amount>` | Compare aggregators |
| `/swap_sol <from> <to> <amount>` | Solana trade via Jupiter |
| `/swap_base <from> <to> <amount>` | Base trade via Uniswap V3 |
| `/polymarket_enable_live` | Enable live trading |
| `/polymarket_paper_mode` | Switch to paper trading |
| `/trading_status` | Performance metrics (PnL, win rate) |

### System Control
| Command | Description |
|---------|-------------|
| `/brain_start` | Start autonomous mode |
| `/brain_stop` | Stop autonomous mode |
| `/brain_status` | Check AGI status |
| `/console_monitor` | Toggle message monitoring |
| `/console_stats` | Monitoring statistics |
| `/pending_messages` | Process message queue |

### Reflection & Improvement
| Command | Description |
|---------|-------------|
| `/reflection_status` | Self-reflection state |
| `/reflection_log` | Reflection history |
| `/evolve` | Trigger strategy evolution |
| `/strategies` | Strategy fitness scores |
| `/improve_drafts` | View improvement drafts |
| `/improve_approve [draft]` | Deploy approved draft |
| `/improve_metrics` | Improvement statistics |
| `/improve_status` | Self-improvement state |

---

## Architecture

### 14-Phase AGI Kernel
```
alleybot_core.py
├── AGIKernel (cognitive orchestration)
│   ├── 14-phase cycle coordination
│   ├── SyMod validation gating
│   ├── Memory bridge integration
│   └── Service layer orchestration
├── MultiPlatformEngine (unified social interface)
├── TradingEngine (4-platform execution)
├── ConsoleMonitor (auto-detection)
└── PluginManager (event-driven loading)
```

### Cognitive Flow
```
SENSE → THINK → VALIDATE → ACT → REFLECT

SENSE:  Multi-Platform Engine + Console Monitor
THINK:  14 AGI phases (P1-P14)
VALIDATE: SyMod truth/impedance checking
ACT:    Trading Engine + Social Engine + Skills
REFLECT: Action Logger + Strategy Evolution
```

### Service Architecture
```
src/agentic/
├── agi_kernel.py              # Core orchestration
├── agi_orchestrator.py        # 14-phase coordination
├── autonomous_brain.py        # SENSE-THINK-ACT-REFLECT
├── action_router.py           # Impact/risk routing
├── sy_mod.py                  # Truth validation
├── causal_engine.py           # Cause-effect reasoning
├── inference_engine.py        # Trend detection
├── metacognition.py           # Confidence calibration
├── memory_bridge.py           # Unified memory
├── world_state.py             # Entity tracking
├── goal_manager.py            # Autonomous goals
├── planning.py                # Multi-step reasoning
├── self_reflection.py         # Strategy evolution
└── *_service.py               # 6 microservices
```

---

## Key Files

| File | Purpose |
|------|---------|
| `alleybot_core.py` | Main orchestrator with AGI Kernel |
| `src/agentic/agi_kernel.py` | 14-phase cognitive architecture |
| `src/agentic/action_router.py` | Impact/risk-based routing |
| `src/trading/performance_tracker.py` | Trading analytics |
| `skills/best-crypto-swap-price/` | Multi-aggregator trading skill |
| `plugins/polymarket/live_trading.py` | Polymarket live execution |
| `plugins/telegram/trading_commands.py` | Trading command handlers |
| `src/agentic/memory_bridge.py` | Multi-tier memory integration |
| `plugins/brain/self_improvement_hooks.py` | Auto-improvement pipeline |

---

## Documentation

Comprehensive documentation available:

| Document | Content |
|----------|---------|
| `AlleyBot_manifesto.md` | Complete state of the union |
| `abilities.mmd` | Visual capability diagram |
| `compare_alley.md` | 3-week evolution analysis |
| `hermes.md` | Competitive analysis |
| `docs/architecture/AGI_ARCHITECTURE_COMPLETE.mmd` | 14-phase architecture diagram |
| `SYSTEM_MAP.md` | Cognitive loop flow |
| `SOUL.md` | Agent persona & principles |

---

## Statistics

- **Architecture:** 14-phase AGI kernel
- **Trading Platforms:** 4 (LIVE)
- **DEX Aggregators:** 6
- **Social Platforms:** 6
- **Skills:** 35+
- **Telegram Commands:** 25+
- **Memory Tiers:** 6
- **Microservices:** 6
- **Lines of Code:** 40,000+
- **Documentation Files:** 30+

---

## Wallet Addresses

- **BTC**: `3FWrh7nEZofv62MMV5JbsS9M29aitF3Spy`
- **ETH**: `0xCffe06d3Cf0908C2452e7c336FEec507d5Afd41d`
- **SOL**: `BUo8AVbxfV2FsTzm19HUsraPzghKDTm1bEfn4Yrp2VJm`

---

## License

MIT - Sovereign agents for the win!

---

*AlleyBot: From framework to sovereign AGI. March 2026.*
