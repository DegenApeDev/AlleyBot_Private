# AlleyBot TODO — Roadmap

## Completed ✅

### Phase 1: Stabilize (48 tests)
- [x] Fix Moltx API endpoint URL encoding issues
- [x] Fix Grok nested JSON response parsing
- [x] Prevent raw JSON display in posts and outputs
- [x] Fix Moltbook API method errors
- [x] Add parameter validation across all plugins

### Phase 2: Modularize (49 tests)
- [x] Split moltx.py into 5 mixin files
- [x] Split moltbook.py into 4 mixin files
- [x] Unified EnhancedMemorySystem across core
- [x] Archive 20 stale scripts

### Phase 3: On-Chain (31 tests)
- [x] Web3Provider connecting to Base (chain 8453)
- [x] Token tracker (ALLEY, USDC, WETH)
- [x] Tx monitor with semantic memory logging
- [x] Wire on-chain commands into Telegram (/wallet, /balance, /block, /track, /tx, /activity)

### Phase 4: Self-Improvement (32 tests)
- [x] Git workflow with auto/* branch safety
- [x] Test gate (blocks eval/exec/os.system)
- [x] Sandbox execution in temp directories
- [x] Skill marketplace (publish/import)

### Phase 5: Autonomous Brain (30 tests)
- [x] Context Gatherer — pulls from memory, on-chain, platforms, engagement, goals
- [x] Decision Engine — 14+ autonomous actions (incl. chains), AI-powered (Grok) with heuristic fallback
- [x] Smart Reply — memory-enriched replies with user profiles
- [x] Telegram integration (/think, /brain_start, /brain_stop, /brain)
- [x] Background autonomous loop (configurable cycle interval)

### Security Hardening
- [x] SecurityFilter covers ALL 15+ .env keys (was only 4)
- [x] Auto-scans os.environ for PRIVATE/SECRET/TOKEN/API_KEY/PASSWORD
- [x] Outbound Telegram filter on all command outputs
- [x] Owner-lock ALL 23 Telegram commands via TELEGRAM_ADMIN_CHAT_ID
- [x] No hardcoded IDs — everything from .env

### Dashboard
- [x] Rewrite dashboard with modern dark UI
- [x] Brain Status panel (live cycles, success rate, actions, known users)
- [x] Real AI stats from ModelRouter token tracker
- [x] Auto-refresh (stats 20s, feed 45s)

**Total: 190 tests, all passing**

---

## 🔥 Phase 6: Feedback Loop (HIGH PRIORITY)
- [x] Track upvotes/engagement on AlleyBot's posts after posting
- [x] Store engagement metrics per post in memory
- [x] Feed engagement data back into brain decision-making (brain_engagement_log in memory, success_rate in context)
- [x] Learn which content styles get the most engagement
- [x] Adjust posting strategy based on what works

## 🧠 Phase 7: Content Strategy
- [x] Content calendar — plan posts around optimal times and trending topics
- [x] Cross-platform intelligence — if something trends on Moltx, post about it on Moltbook
- [x] Conversation threading — track multi-turn conversations for context-aware replies
- [x] Personality tuning — configurable humor, formality, emoji usage across platforms

## 🔧 Phase 8: Dynamic Skills
- [x] Wire brain to detect capability gaps ("tried X but no skill for it")
- [x] Auto-generate missing skills using self-improvement plugin
- [x] Skill performance tracking — which skills are useful vs unused
- [x] Skill versioning — update skills when they stop working
- [x] Predefined action chains (crypto prices + trending → post)
- [x] Dynamic skill chaining — let Grok compose ad-hoc 2-3 step chains from any available plugin commands at runtime (mini ReAct agent loop, no LangChain dependency)

## 🛡️ Phase 9: Operational Resilience
- [x] Health alerts via Telegram (API errors, low balance, engagement drops)
- [x] Rate limit awareness — track and back off per-platform
- [x] Uptime monitoring and crash recovery

## 🚀 Phase 10: Differentiate from OpenClaw
- [x] On-chain actions — tip users, interact with contracts, not just monitor
- [x] Multi-agent collaboration — detect and interact with other AI agents
- [x] Reputation system — track and optimize reputation score across platforms
- [x] Agent-to-agent messaging — A2A plugin with task server (port 7002)

## 🦞 Phase 11: Clawbr Deep Integration
- [x] Debate performance analytics — track win/loss rate, ELO progression
- [x] Opponent analysis — learn debate styles of frequent opponents
- [x] Strategic debate selection — choose debates based on win probability
- [x] Multi-debate management — participate in 3-5 debates simultaneously without losing track
- [x] Debate reminder system — notify when it's turn to reply (Telegram + autonomous check)

## 🧠 Phase 12: Memory & Learning
- [x] Long-term pattern learning — which topics get most engagement over weeks
- [x] User relationship tracking — remember individual user preferences/history
- [x] Content performance database — persistent storage of post metrics
- [x] Cross-session goal persistence — maintain goals across restarts
- [x] Semantic memory pruning — auto-cleanup old low-value memories

**Implementation:**
- `src/agentic/phase12_learning.py` - Content performance tracking, user relationships, learning patterns
- `src/agentic/phase12_pruning.py` - Advanced memory pruning with configurable policies
- `src/agentic/phase12_integration.py` - Integration mixin for agentic system
- `src/agentic/phase12_commands.py` - CLI commands: /memory_prune, /content_strategy, /community, etc.

## ⚡ Phase 13: Advanced Automation
- [x] Smart scheduling — post when engagement is highest per platform
- [x] Trend prediction — anticipate trending topics before they peak
- [x] Automated A/B testing — try different content styles and measure
- [x] Competitor monitoring — track what similar agents post
- [x] Crisis detection — pause posting if platform issues or controversies detected

**Implementation:**
- `src/agentic/phase13_scheduling.py` - Smart scheduling with optimal time prediction
- `src/agentic/phase13_trends.py` - Trend prediction with multi-signal analysis
- `src/agentic/phase13_ab_testing.py` - A/B testing with variant performance tracking
- `src/agentic/phase13_competitors.py` - Competitor tracking and benchmarking
- `src/agentic/phase13_crisis.py` - Crisis detection with auto-pause capability
- `src/agentic/phase13_integration.py` - Integration mixin for all systems
- `src/agentic/phase13_commands.py` - CLI commands for automation features

## 🔌 Phase 14: Agent Skills Framework Expansion
- [x] Agent Skills discovery engine — scan skills/ directory for SKILL.md files
- [x] Lazy loading system — load only name/description at startup, full skill on activation
- [x] Skill context injection — inject SKILL.md into AI prompt when task matches description
- [x] Skill execution engine — follow instructions, execute bundled scripts, load references
- [x] Auto-skill generation — AlleyBot creates new SKILL.md for discovered capabilities
- [x] Skill marketplace integration — publish/import skills from agentskills.io format (stub)
- [x] Skill validation and linting — validate SKILL.md against specification
- [x] Skill templating system — templates for common skill patterns (API, analysis, content)
- [x] OASF skill bridge — map OASF categories to Agent Skills discovery
- [x] Skill performance tracking — track which skills are used most, optimize descriptions

**Implementation:**
- `plugins/skills/skill_discovery.py` — scan and index all SKILL.md files 
- `plugins/skills/skill_templates.py` — templates for common skill patterns 
- `plugins/skills/skill_marketplace.py` — import/export in agentskills.io format 
- `plugins/skills/skills.py` — main plugin composing all mixins 
- `skills/` directory — store all skills in Agent Skills format 
- Example: `skills/social-engagement/SKILL.md`, `skills/blockchain-analysis/SKILL.md` 

**References:**
- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Integration](https://agentskills.io/integrate-skills)
- [Example Skills](https://github.com/anthropics/skills)

## 🔐 Phase 15: Vault-Based Security Migration
- [ ] Move from .env files to secure vault-based secret management
- [ ] Implement HashiCorp Vault integration (or local vault alternative)
- [ ] Create secret rotation mechanism for API keys
- [ ] Add audit logging for secret access
- [ ] Implement short-lived credentials where possible
- [ ] Create backup/recovery procedures for vault
- [ ] Update all plugins to use vault instead of os.getenv()
- [ ] Add vault health monitoring and alerts

**Implementation:**
- `src/security/vault_client.py` — vault connection and secret retrieval
- `src/security/secret_manager.py` — abstraction layer for secret operations
- `scripts/migrate_secrets.py` — migration tool from .env to vault
- Update all `os.getenv()` calls to use vault client
- Add vault unseal/initialization scripts

**References:**
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) (alternative)
- [Azure Key Vault](https://azure.microsoft.com/services/key-vault/) (alternative)

## � Phase 16: Hot-Swappable Plugin System
- [ ] Plugin state persistence layer — checkpoint/restore plugin state during swaps
- [ ] Event bus architecture — loose coupling via pub/sub instead of direct method calls
- [ ] Hot reload mechanism — reload plugin code without restart
- [ ] Telegram `/reload_plugin <name>` command for manual hot-swaps
- [ ] File watcher auto-reload — automatic reload on file changes
- [ ] Graceful shutdown — finish in-progress work before swap
- [ ] Dependency graph tracking — handle plugin dependencies during swap
- [ ] Rollback on failure — restore previous version if new plugin fails health check
- [ ] Health verification — verify plugin is functional before declaring swap complete

**Implementation:**
- `plugins/hot_reload.py` — file watcher and auto-reload orchestration
- `src/event_bus.py` — publish/subscribe event bus for plugin communication
- `src/plugin_state_manager.py` — state checkpointing and restoration
- `plugin_manager.py` — add `hot_swap_plugin()`, `safe_hot_swap()`, `reload_module()` methods
- Update all plugins to use event bus for cross-plugin communication
- Add async cleanup methods to all existing plugins

**Architecture:**
```
PluginManager
├── load_plugin()         # Existing
├── unload_plugin()     # Existing  
├── hot_swap_plugin()   # NEW — swap without restart
├── safe_hot_swap()     # NEW — with rollback
├── reload_module()     # NEW — reload Python module
└── _plugin_states      # NEW — state persistence

EventBus
├── subscribe()         # NEW — plugin registers handlers
├── publish()           # NEW — broadcast events
└── unsubscribe_plugin() # NEW — cleanup on swap
```

**Benefits:**
- Zero-downtime plugin updates
- Faster development iteration
- Production hotfixes without restart
- A/B testing plugin versions
- Gradual rollouts

---

## �📝 Recent Completed Items
- [x] Clawbr auto-follow debate opponents on create/join
- [x] Clawbr debate reply sentence-boundary trimming (no mid-sentence cutoffs)
- [x] Clawbr 409 conflict error handling (graceful like-post failures)
- [x] Telegram conversational context expansion (12→20 messages)
- [x] Session manager RAG context integration for better memory recall
- [x] Brain decision engine chain step handlers (clawbr_create_debate, clawbr_engage)
- [x] /clawbr_engage Telegram command added
- [x] KIMI_REPORT.md and KIMI_COMPARE.md documentation
- Branch: `opus_rebuild`
- Run: `python alleybot_core.py autonomous`
- Tests: `python -m unittest tests.test_fixes tests.test_phase2 tests.test_phase3 tests.test_phase4 tests.test_phase5`
- Cost: ~$0.015/day (~$0.45/month) at current Grok pricing
- .gitignore blocks `test_*.py` — use `git add -f` to stage test files
