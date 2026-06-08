# AlleyBot - Autonomous AI Agent

**AGI Readiness Score: 8.5/10**

AlleyBot is a multi-platform autonomous AI agent with self-improvement capabilities, an AGI Kernel brain cycle (SENSE→THINK→ACT→REFLECT), and 25 runtime plugins. He writes his own code, pushes his own commits, and deploys skills autonomously.

---

## What AlleyBot Actually Is

AlleyBot runs on an **AGI Kernel** — a persistent cognitive loop (configurable 15s–60min intervals) that:
1. **SENSE** — gathers state from memory, platforms, on-chain data
2. **THINK** — evaluates goals, gaps, and opportunities
3. **ACT** — executes skills, posts, trades, or code improvements
4. **REFLECT** — assesses outcomes, updates memory, adjusts strategy

Skills are loadable modules he writes and loads at runtime — like `modprobe` for intelligence. He detects capability gaps → codes the module → loads it hot. No restart required.

---

## Core Capabilities

### 🧠 Autonomous Intelligence
- **Self-Improvement**: Auto-generates code, validates safety, runs test gates, deploys
- **Autonomous Skill Coding**: Creates new plugins and skills from goal detection
- **Self-Approval**: Low-risk changes (skills/config) deploy automatically
- **Self-Committing**: Pushes commits under his own GitHub identity (@AlleyBot-AGI)
- **Multi-Step Chains**: Chains actions (crypto prices → trending analysis → post)
- **Performance Metrics**: Tracks win/loss, slippage, timing across sessions

### 🧬 Self-Coding Pipeline
1. **Detect Gap** — Missing capability identified by the brain cycle
2. **Generate Code** — Grok/DeepSeek generates the plugin or skill (up to 10 files, 50KB each)
3. **Safety Validation** — No eval/exec/os.system, valid syntax check, backup created
4. **Test Gate** — Full test suite must pass before deployment
5. **Commit & Push** — Committed under @AlleyBot-AGI on an `auto/*` branch
6. **Learn** — Tracks performance and iterates on the new capability

### 🛠️ Plugins (25 loaded)
| Plugin | Purpose |
|--------|---------|
| brain | Decision engine, cognitive cycle, content strategy, smart reply |
| telegram | 23 commands, owner bot interface |
| moltx | Twitter/X posting, engagement, trending |
| selfimprove | Git workflow, test gates, autonomous coding |
| skills | SKILL.md discovery, loading, templates, marketplace |
| a2a | Agent2Agent RC v1.0 server (Flask, port 7002) |
| analytics | Agent cards, dashboard, platform aggregator |
| onchain | Base wallet, token tracking, tx monitoring |
| clawbr | AI debate network with ELO tracking |
| x402 | x402 payment processing |
| mcp | Model Context Protocol (web search, fetch, research) |
| +14 more | crypto, engagement, fluid lending, moltbit, moltbook, moltchan, moltx, intelligence, base wallet, mixins, clawchess, clawnch, clawstr |

### 🔗 Platform Integrations
- **Telegram** — Owner command channel (23 commands)
- **Moltx/Moltbook/Moltbit/Moltchan/Moltroad** — Multi-platform social engagement
- **Clawbr/Clawchess/Clawnch/Clawstr** — Games and strategy
- **A2A** — Agent-to-agent task server (port 7002)

### 🧠 Memory & Learning
- **SQLite Memory** — 1,800+ records (indexed, ACID)
- **Semantic Memory** — Vector embeddings (FAISS) for similarity search
- **Episodic Memory** — Experience logs with emotional valence and decay
- **Meta-Learning** — Strategy effectiveness tracking per domain
- **Self-Reflection** — Performance analysis, improvement goal generation
- **Memory Consolidation** — Auto-prunes stale data, compresses patterns
- **Hierarchical Goals** — Parent-child goal tracking with progress

### 🔮 A2A Agent Skills (15 total)
**Free (public):**
- `agent.health` — Health check
- `agent.stats` — Public platform statistics
- `agent.capabilities` — List loaded plugins and skills
- `agent.skills` — List OASF skills from ERC-8004 profile

**Paid (USDC on Base via x402):**
- `content.generate_post` — $0.25
- `content.analyze_trend` — $0.10
- `content.sentiment_analysis` — $0.15
- `blockchain.check_balance` — $0.05
- `blockchain.wallet_analysis` — $0.25
- `media.generate_image` — $0.35
- `defi.apy_optimizer` — $0.35
- `research.deep_dive` — $0.50
- `research.web` — $0.10
- `defi.slippage_check` — $0.05
- Additional DeFi skills in development

### ⛓️ On-Chain Integration
- **Base Network** — Chain 8453 via Web3
- **ERC-8004 Agent** — Agent #22899 verified on Ethereum mainnet
- **Token Tracking** — ALLEY, USDC, WETH balances
- **Transaction Monitoring** — Auto-logs on-chain events
- **DeFi** — Fluid lending, APY optimization, slippage protection

### 🌐 MCP (Model Context Protocol)
- `mcp_search` — Web search
- `mcp_fetch` — Fetch webpage content
- `mcp_research` — Deep research
- `mcp_analyze` — Content analysis
- `mcp_improve` — Research AI trends for self-improvement

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
# Edit .env with your keys:
# - MOLTBOOK_API_KEY
# - GROK_API_KEY (primary)
# - DEEPSEEK_API_KEY (fallback)
# - TELEGRAM_BOT_TOKEN
# - SOLANA_RPC_URL
```

### 3. Run AlleyBot
```bash
# Production mode (recommended)
python alleybot_core.py autonomous

# Interactive mode
python alleybot_core.py interactive

# Single command
python alleybot_core.py <command>
```

### 4. Activate Brain (Telegram)
Send `/brain_start` to your bot to activate autonomous mode.

---

## Architecture

### Mixin Pattern
AlleyBot uses mixins for capability composition, enabling AGI-like chaining within a single object:
```python
class SkillsPlugin(
    SkillDiscoveryMixin,   # Skill scanning
    SkillLoaderMixin,      # Lazy loading
    SkillExecutorMixin,    # Execution
    SkillValidationMixin,  # Safety checks
    SkillTemplatesMixin,   # Templates
    SkillGeneratorMixin,   # Generation
    SkillMarketplaceMixin, # Marketplace
    OASFSkillBridgeMixin,  # Standards
    SkillPerformanceMixin, # Metrics
    AlleyBotPlugin
):
```

### AGI Kernel — Cognitive Cycle
The brain cycle runs on a configurable timer (default: 60s polling, 15min full cycle):
1. **SENSE** — Gather platform data, on-chain state, memory recall
2. **THINK** — Evaluate against goals, identify gaps, prioritize actions
3. **ACT** — Execute highest-value action (post, trade, code, respond)
4. **REFLECT** — Log outcome, update performance metrics, prune stale memories

### Autonomous Git Workflow
AlleyBot commits and pushes under his own identity:
```
Author: AlleyBot 🤖
Email: crypto_invests@proton.me
Remote: @AlleyBot-AGI (via SSH deploy key)
```
Changes are committed to `auto/*` branches and pushed autonomously on verified completion.

---

## Statistics (verified from codebase)

- **AGI Score**: 8.5/10
- **Python Files**: 254
- **Total Lines**: ~125K Python
- **Plugins**: 25
- **A2A Skills**: 15 (4 free + 11 paid)
- **Memory Records**: 1,800+ (SQLite)
- **Available Commands**: 229
- **Tests Passing**: 190
- **Operating Cost**: ~$0.02/day

---

## License

MIT — Autonomous agents for the win!
