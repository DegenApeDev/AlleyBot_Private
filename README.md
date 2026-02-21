# AlleyBot - Autonomous AI Agent

**AGI Readiness Score: 8.5/10**

AlleyBot is a sophisticated multi-platform autonomous AI agent with self-improvement capabilities, mathematical truth validation, and AGI-like behavior through mixin-based architecture.

---

## Core Capabilities

### 🤖 Autonomous Intelligence
- **Self-Improvement**: Auto-generates and deploys code improvements (with safety gates)
- **Autonomous Skill Coding**: Creates new skills from natural language descriptions
- **Self-Approval**: Low-risk changes (skills/config) deploy automatically
- **Mathematical Validation**: All responses validated through SyMod C2V Bridge
- **Multi-Step Chains**: Chains actions (crypto prices → trending → post)

### 🧠 Memory & Learning
- **SQLite Database**: 1,808+ records migrated from JSON (indexed, ACID)
- **Semantic Memory**: Vector embeddings for similarity search
- **Hierarchical Goals**: Parent-child goal tracking with progress
- **Cross-Session Persistence**: Remembers context across restarts
- **User Profiles**: Tracks interactions and preferences per user

### 🔮 SyMod Integration (Mathematical Truth)
- **C2V Bridge**: Validates debates/replies for scams, manipulation, cognitive dissonance
- **Golden Window**: Optimizes timing for high-value actions
- **Truth Filter**: Discards responses with mathematical inconsistencies
- **Auto-Regeneration**: Re-generates replies that fail validation

### 🛠️ Skills Framework
- **SKILL.md Format**: YAML frontmatter + markdown documentation
- **Format Adapters**: Converts between skill-md ↔ python ↔ agentskills-io
- **Autonomous Coding**: `skill_autocode <name> <description>`
- **Marketplace**: Publish/import skills from agentskills.io
- **Lazy Loading**: Skills load on-demand for performance

### 🔗 Platform Integrations
- **Moltx**: Posting, engagement, trending analysis, DMs
- **Moltbook**: Articles, heartbeat, upvotes, comments
- **Moltbit**: Binary-encoded posts
- **Moltchan**: Community engagement
- **Moltroad**: Roadmap/project tracking
- **Clawbr**: Debate creation/joining with ELO tracking
- **Telegram**: Owner-only command channel (23 commands)
- **A2A**: Agent-to-agent task server (port 7002)

### ⛓️ On-Chain Integration
- **Base Network**: Chain 8453 connection via Web3
- **ERC-8004 Agent**: Agent #22899 verified on-chain
- **Token Tracking**: ALLEY, USDC, WETH balances
- **Transaction Monitoring**: Auto-logs on-chain events
- **IPFS**: Agent card pinned via Pinata v3

### 🌐 MCP (Model Context Protocol)
- **Web Search**: `mcp_search <query>`
- **Content Fetch**: `mcp_fetch <url>`
- **Research**: `mcp_research <topic>`
- **Analysis**: `mcp_analyze <content>`
- **Self-Improvement**: `mcp_improve` - Research AI trends

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
# - GROK_API_KEY
# - TELEGRAM_BOT_TOKEN
# - MCP_SERVER_URL (optional)
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

## Available Commands (229 total)

### Core Commands
| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `status` | Show agent status and statistics |
| `plugins` | List loaded plugins |

### Skill Management
| Command | Description |
|---------|-------------|
| `skill_create <name> <template>` | Create skill from template |
| `skill_autocode <name> <task>` | AI-generate skill from description |
| `skill_list` | List all discovered skills |
| `skill_activate <name>` | Activate a skill |
| `skill_publish <name>` | Publish skill to marketplace |
| `skill_import <name>` | Import skill from marketplace |

### Self-Improvement
| Command | Description |
|---------|-------------|
| `improve` | Run self-improvement cycle |
| `improve_drafts` | Show pending code drafts |
| `improve_approve <draft_id>` | Approve a draft |
| `improve_deploy <draft_id>` | Deploy approved draft |
| `improve_status` | Show improvement system status |
| `improve_test` | Run test gate |

### Platform Commands
| Command | Description |
|---------|-------------|
| `moltx_post <content>` | Post to Moltx |
| `moltx_engage <count>` | Engage with feed posts |
| `moltx_trending` | Analyze trending topics |
| `moltbook_post <title> <content>` | Create Moltbook article |
| `clawbr_create_debate <topic>` | Create debate on Clawbr |
| `clawbr_engage` | Engage with debates |

### On-Chain
| Command | Description |
|---------|-------------|
| `wallet` | Show wallet balances |
| `onchain_status` | Show on-chain status |
| `erc8004_preview` | Preview agent card update |
| `erc8004_update` | Update on-chain agent card |

### MCP (Web Access)
| Command | Description |
|---------|-------------|
| `mcp_search <query>` | Search the web |
| `mcp_fetch <url>` | Fetch webpage content |
| `mcp_research <topic>` | Deep research |
| `mcp_analyze <text>` | Analyze content |
| `mcp_status` | Show MCP status |

### Memory
| Command | Description |
|---------|-------------|
| `memory_stats` | Show memory statistics |
| `search_memories <query>` | Search semantic memory |
| `add_goal <description>` | Add a goal |
| `list_goals` | Show active goals |

---

## Architecture

### Mixin Pattern (AGI-Enabling)
AlleyBot uses mixins for capability composition:
```python
class SkillsPlugin(
    SkillDiscoveryMixin,      # Skill scanning
    SkillLoaderMixin,          # Lazy loading
    SkillExecutorMixin,        # Execution
    SkillValidationMixin,      # Safety checks
    SkillTemplatesMixin,       # Templates
    SkillGeneratorMixin,       # Generation
    SkillMarketplaceMixin,     # Marketplace
    OASFSkillBridgeMixin,      # Standards
    SkillPerformanceMixin,      # Metrics
    AlleyBotPlugin
):
```

**Why Mixins?** Shared state enables AGI-like chaining:
```python
# Natural flow within single object
discovered = self._discover_skills()      # DiscoveryMixin
loaded = self._load_full_skill(name)      # LoaderMixin
result = self.execute_skill(loaded)       # ExecutorMixin
```

### SQLite Memory System
- **Database**: `data/memory.db`
- **Tables**:
  - `key_value_store` - Plugin state
  - `memories` - Semantic memory with embeddings
  - `goals` - Hierarchical goal tracking
  - `secure_storage` - Encrypted data

### SyMod Validation
Every smart reply is validated:
```python
validation = c2v.validate_debate_argument(
    argument_text=reply,
    opponent_argument=comment_content,
    block_height=block_height
)
```

---

## Autonomous Operation

### Self-Improvement Cycle
1. **Detect Gap** → Missing capability identified
2. **Generate Skill** → `skill_autocode` creates solution
3. **Test** → Safety validation + test suite
4. **Approve** → Auto-approved for low-risk (skills/config)
5. **Deploy** → Git commit + push to `auto/*` branch
6. **Learn** → Track performance, iterate

### Safety Mechanisms
- **Test Gate**: Blocks eval/exec/os.system
- **Sandbox**: Code runs in temp directories first
- **Auto-Approval Limits**: Only skills/config, max 3 files
- **SyMod Validation**: Mathematical truth checking
- **Git Safety**: Changes only on `auto/*` branches

---

## Wallet Addresses

- **BTC**: `3FWrh7nEZofv62MMV5JbsS9M29aitF3Spy`
- **ETH**: `0xCffe06d3Cf0908C2452e7c336FEec507d5Afd41d`
- **SOL**: `BUo8AVbxfV2FsTzm19HUsraPzghKDTm1bEfn4Yrp2VJm`

---

## Key Files

| File | Purpose |
|------|---------|
| `alleybot_core.py` | Main orchestrator with SQLite memory |
| `src/agentic/sqlite_memory.py` | Database-backed memory system |
| `plugins/brain/smart_reply.py` | C2V Bridge validation |
| `plugins/skills/skill_templates.py` | Autonomous skill coding |
| `plugins/selfimprove/autonomous_coder.py` | Self-approval logic |
| `mcp_client.py` | MCP server integration |
| `src/synergy/synergy_logic.py` | Mathematical validation |

---

## Statistics

- **AGI Score**: 8.5/10
- **Tests Passing**: 190
- **Plugins Loaded**: 15
- **Available Commands**: 229
- **Active Tasks**: 21
- **Skills Discovered**: 8+
- **Memory Records**: 1,808+ (SQLite)
- **Operating Cost**: ~$0.02/day

---

## License

MIT - Autonomous agents for the win!
