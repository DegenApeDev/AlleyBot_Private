# AlleyBot Project Report

## Executive Summary

**AlleyBot** is a sophisticated, autonomous AI agent platform with a modular plugin architecture. Originally conceived as a "homeless bot" running on a library Raspberry Pi seeking crypto donations, it has evolved into a comprehensive multi-platform social media automation and engagement system with on-chain capabilities, self-improvement features, and Agent2Agent (A2A) protocol compliance.

**Current Status**: Production-ready with **190+ passing tests** across 5 development phases. Ranked **#84 on 8004scan.io** (ERC-8004 agent registry) as of February 2026.

---

## Architecture Overview

### Core Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **AlleyBotCore** | Central orchestrator, plugin manager, memory coordinator | ✅ Active |
| **PluginManager** | Dynamic plugin loading, command/task registration | ✅ Active |
| **EnhancedMemorySystem** | Vector DB (FAISS), semantic search, goals, encrypted storage | ✅ Active |
| **AgenticSystem** | ReAct agent loop, reasoning, tool execution | ✅ Active |
| **ModelRouter** | DeepSeek/Grok-4.1 routing based on context complexity | ✅ Active |
| **EventRunner** | Event-driven async processing, scheduled tasks | ✅ Active |
| **SecurityFilter** | Code validation, dangerous pattern detection | ✅ Active |

### Architecture Flow

```
Owner (Telegram) → Telegram Interface → Brain Module
                                           ↓
    ┌─────────────┬─────────────┬─────────┴────────┬─────────────┐
    ↓             ↓             ↓                ↓             ↓
 Social Media   Clawbr        A2A System      Crypto/On-Chain  Analytics
(MoltX/Moltbook) (Debates)   (Agent Tasks)    (Base Network)   (Dashboard)
```

---

## Plugin Ecosystem (14 Active Plugins)

| Plugin | Platform | Key Features |
|--------|----------|--------------|
| **moltx** | Twitter-like social | Posts, replies, likes, follows, trending, reposts |
| **moltbook** | Reddit-like forums | Submolts, posts, comments, upvotes, karma tracking |
| **clawbr** | AI debate network | Debates, voting, leaderboard, auto-follow opponents |
| **onchain** | Base (EVM) | Wallet, token tracking (ALLEY/USDC/WETH), tx monitor |
| **a2a** | Agent2Agent Protocol | RC v1.0 compliant server, task dispatch, streaming |
| **telegram** | Control interface | 23 owner-locked commands, natural language processing |
| **brain** | Autonomous cognition | Decision engine, 14+ actions, smart replies |
| **selfimprove** | Code evolution | Git workflow, test gates, skill marketplace |
| **crypto** | Price tracking | Multi-coin prices, trending, market data |
| **mcp** | Research access | Web search, caching, self-improvement research |
| **moltchan** | Community | Auto-browse, engagement |
| **moltroad** | Marketplace | Auto-browse, heartbeat |

---

## Key Features

### 1. Multi-Platform Social Media Automation
- **MoltX** (Twitter-like): Intelligent posting, engagement, trending analysis
- **MoltBook** (Reddit-like): Submolt exploration, commenting, karma building
- **Clawbr** (AI Debate): Autonomous debate participation, ELO tracking

### 2. On-Chain Integration (Base Network)
- **Wallet**: ETH + ERC-20 balance tracking
- **Token Tracker**: ALLEY, USDC, WETH with change detection
- **Transaction Monitor**: Address watching, semantic memory logging
- **Web3Provider**: Real-time chain data (chain 8453)

### 3. Self-Improvement System
- **Autonomous Coder**: AI-powered code generation with safety guards
- **Git Workflow**: `auto/*` branch safety, prevents commits on main
- **Test Gate**: Sandbox execution, validates code before merge
- **Skill Marketplace**: Publish/import skills, local registry

### 4. Autonomous Brain
- **Context Gatherer**: Pulls from memory, on-chain, platforms, engagement
- **Decision Engine**: 14+ autonomous actions with AI-powered decisions
- **Smart Reply**: Memory-enriched replies with user profiles
- **Background Loop**: Configurable cycle interval (default 5 min)

### 5. Agent2Agent (A2A) Protocol
- **RC v1.0 Compliant**: Agent cards, task lifecycle, streaming
- **ERC-8004 Registered**: Agent #22899 on Ethereum mainnet
- **Skills**: Agent coordination, negotiation resolution, API understanding

### 6. Security & Control
- **Owner-Locked**: All Telegram commands locked to `TELEGRAM_ADMIN_CHAT_ID`
- **SecurityFilter**: Blocks `eval()`, `exec()`, `os.system()` in generated code
- **Environment Scanning**: Auto-detects all API keys/secrets
- **Approval Dashboard**: Human-in-the-loop for high-risk actions

---

## Technical Stack

| Layer | Technologies |
|-------|-------------|
| **Language** | Python 3.10+ |
| **AI/LLM** | DeepSeek (primary), Grok-4.1 (fallback), sentence-transformers |
| **Vector DB** | FAISS (Facebook AI Similarity Search) |
| **Web3** | Web3.py, Base (Ethereum L2) |
| **Async** | asyncio, aiohttp |
| **HTTP** | FastAPI, Flask, requests |
| **Security** | Fernet encryption, risk-level enums, pattern detection |
| **Testing** | pytest, unittest (190+ tests) |
| **Scheduling** | schedule, APScheduler |
| **Memory** | JSON + FAISS + semantic embeddings |

---

## Project Statistics

```
📊 Codebase Metrics:
   • Total Files: ~119 Python files
   • Lines of Code: ~26,000+
   • Plugins: 14 active
   • Commands: 60+ registered
   • Tests: 190+ (all passing)
   • Test Coverage: 5 phases (48+49+31+32+30)

🧠 Memory System:
   • Chat History: 50 messages per session
   • Context Window: 12-20 messages for RAG
   • Vector Store: FAISS with 384-dim embeddings
   • Encryption: Fernet for sensitive data

⚡ Performance:
   • API Rate Limits: 10 req/sec (Clawbr), 100/min (Moltbook)
   • Heartbeat: Every 4+ hours
   • Brain Cycle: Every 5 minutes (configurable)
   • Auto-refresh: Stats 20s, Feed 45s (dashboard)
```

---

## Development Roadmap (Completed)

### ✅ Phase 1: Stabilize (48 tests)
- Fixed API endpoint encoding, Grok JSON parsing
- Parameter validation across all plugins

### ✅ Phase 2: Modularize (49 tests)
- Split moltx.py (2808 lines → 5 files)
- Split moltbook.py (1183 lines → 4 files)
- Unified EnhancedMemorySystem

### ✅ Phase 3: On-Chain (31 tests)
- Web3Provider for Base network
- Token tracker (ALLEY/USDC/WETH)
- Transaction monitor with semantic logging

### ✅ Phase 4: Self-Improvement (32 tests)
- Git workflow with safety guards
- Test gate with sandbox execution
- Skill marketplace (publish/import)

### ✅ Phase 5: Autonomous Brain (30 tests)
- Context gatherer, decision engine
- 14+ autonomous actions with chains
- Smart replies with memory enrichment

---

## Configuration

**Plugin Config** (`plugin_config.json`):
- 14 plugins with individual enable/disable
- Platform-specific settings (auto_posting, heartbeat, etc.)
- Owner ID: `6172568442` (hardcoded for security)

**Environment Variables** (15+ keys):
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`
- `DEEPSEEK_API_KEY`, `XAI_API_KEY` (Grok)
- `CLAWBR_API_KEY`, `MOLTBOOK_API_KEY`
- `BASE_WALLET_PUBLIC_ADDRESS`, `BASE_RPC_URL`
- `GITHUB_TOKEN` (for self-improvement)

---

## Current Issues & Fixes (Recent)

| Issue | Status | Fix |
|-------|--------|-----|
| Clawbr commands missing | ✅ Fixed | Restored full command mixin |
| Debate replies truncated | ✅ Fixed | Sentence-boundary trimming |
| 409 conflict errors | ✅ Fixed | Graceful handling without logs |
| Auto-follow opponents | ✅ Added | Follow on debate create/join |
| Context window too small | ✅ Expanded | 12→20 messages |

---

## Notable Achievements

1. **ERC-8004 Agent Registry**: Ranked #84 on 8004scan.io (Agent #22899)
2. **A2A Protocol Compliance**: RC v1.0 spec, 56 passing tests
3. **Self-Modifying Code**: Autonomous skill generation with safety gates
4. **Multi-LLM Strategy**: DeepSeek + Grok-4.1 with intelligent routing
5. **On-Chain Awareness**: Real Web3 integration on Base network

---

## File Structure

```
/home/degendev/Dev/Agents/MoltbookBot/
├── alleybot_core.py          # Central orchestrator
├── plugin_manager.py         # Plugin system
├── plugin_config.json        # 14 plugin configs
├── autonomous_coder.py     # Self-improvement engine
├── grok_ai.py               # Grok-4.1 integration
├── deepseek_ai.py          # DeepSeek integration
├── config.py               # Environment loader
├── requirements.txt        # Dependencies
│
├── plugins/                # 14 plugin directories
│   ├── moltx/             # Twitter-like (7 files)
│   ├── moltbook/          # Reddit-like (5 files)
│   ├── clawbr/            # Debates (6 files)
│   ├── onchain/           # Web3 (5 files)
│   ├── a2a/               # Agent2Agent (5 files)
│   ├── telegram/          # Control (3 files)
│   ├── brain/             # Autonomous (7 files)
│   ├── selfimprove/       # Evolution (8 files)
│   └── [6 more...]
│
├── src/                    # Core systems
│   ├── agentic/           # Agent framework (10 files)
│   ├── agents/            # Event runner, sessions
│   ├── integrations/      # Webhooks
│   └── skills/            # Skill loader
│
├── tests/                 # Test suite
│   ├── test_fixes.py      # Phase 1 (48 tests)
│   ├── test_phase2.py     # Phase 2 (49 tests)
│   ├── test_phase3.py     # Phase 3 (31 tests)
│   ├── test_phase4.py     # Phase 4 (32 tests)
│   └── test_phase5.py     # Phase 5 (30 tests)
│
├── docs/                  # Documentation
│   ├── architecture_diagrams.md  # Mermaid diagrams
│   └── architecture_diagrams.mmd
│
├── skills/                # Agent skills (26 items)
├── memory/                # Runtime memory storage
├── data/                  # Persistent data
└── archive_old_files/     # 57 archived scripts
```
