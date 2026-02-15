# AlleyBot TODO — Roadmap

## Completed ✅

### Phase 1: Self-Reflection System (AGI Core)
**Goal: Alley learns from every action he takes**
- [x] **Action-Outcome Logger** - Every decision logged with result (`src/agentic/action_logger.py`)
- [x] **Performance Scorer** - Auto-score each action's effectiveness (built into logger)
- [x] **Strategy Evolution** - Mutate approaches, keep winners (`src/agentic/strategy_evolver.py`)
- [x] **Failure Analysis** - Learn from mistakes via outcome tracking
- [x] **Telegram Commands** - `/reflection_status`, `/reflection_log`, `/reflection_tune`, `/evolve`, `/strategies`

### Phase 1: Stabilize (48 tests - Legacy)
- [x] Fix Moltx API endpoint URL encoding issues
- [x] Fix Grok nested JSON response parsing
- [x] Prevent raw JSON display in posts and outputs
- [x] Fix Moltbook API method errors
- [x] Add parameter validation across all plugins

### Phase 2: Autonomous Goal Management (AGI Core) ✅
**Goal: Alley detects gaps and proposes his own tasks**
- [x] **Opportunity Detector** - Scan for unfulfilled requests (`src/agentic/goal_detector.py`)
- [x] **Goal Generator** - Create proposals with priority scores (`src/agentic/goal_manager.py`)
- [x] **Goal Queue** - Manage active/pending/completed goals with status tracking
- [x] **Auto-Propose Skills** - Generate skill proposals when gaps found
- [x] **Telegram Commands** - `/goals`, `/goals_approve`, `/goals_scan`, `/goals_create`

### Phase 2: Modularize (49 tests - Legacy)
- [x] Split moltx.py into 5 mixin files
- [x] Split moltbook.py into 4 mixin files
- [x] Unified EnhancedMemorySystem across core
- [x] Archive 20 stale scripts

### Phase 3: Multi-Step Planning (AGI Core) ✅
**Goal: Complex tasks broken into sub-tasks**
- [x] **Goal Decomposer** - Break big goals into steps (`src/agentic/planning.py`)
- [x] **Dependency Tracker** - DAG-based dependency management with topological sort
- [x] **Plan Monitor** - Track progress, recover from failures, retry logic
- [x] **Step Types** - RESEARCH, DESIGN, IMPLEMENT, TEST, DEPLOY, REVIEW, DOCUMENT
- [x] **Telegram Commands** - `/plan_create`, `/plan_status`, `/plan_execute`, `/plan_steps`

### Phase 3: On-Chain (31 tests - Legacy)
- [x] Web3Provider connecting to Base (chain 8453)
- [x] Token tracker (ALLEY, USDC, WETH)
- [x] Tx monitor with semantic memory logging
- [x] Wire on-chain commands into Telegram (/wallet, /balance, /block, /track, /tx, /activity)

### Phase 4: Self-Extension Pipeline (COMPLETED) ✅
**Goal: Alley detects gaps and builds new skills automatically**
- [x] **Skill Proposal Generator** - Converts goals into skill specifications (`src/agentic/skill_generator.py`)
- [x] **Autonomous Coder** - Generates Python code from specs (`src/agentic/autonomous_coder.py`)
- [x] **Auto-Tester** - Validates skills work correctly (`src/agentic/skill_tester.py`)
- [x] **Auto-Deployer** - Hot-loads skills into production
- [x] **Telegram Control** - `/extend`, `/skills_propose`, `/skills_generate`, `/skills_test`, `/skills_deploy` (`plugins/telegram/extend_commands.py`)
- [x] **Security Validation** - CodeSecurityValidator with dangerous pattern detection

**Pipeline:** `Detect Gap → Propose Skill → Generate Code → Test → Deploy`

### Phase 5: Causal Understanding (AGI Core) ✅
**Goal: Understand *why* things happen, not just *what* happens**
- [x] **Event Causality Tracker** - Link cause → effect chains (`src/agentic/causal_engine.py`)
- [x] **Counterfactual Analysis** - "What if I had done X instead?"
- [x] **Intervention Simulation** - Predict outcomes of hypothetical actions
- [x] **Root Cause Analysis** - Find true sources of trends/engagement
- [x] **Impact Attribution** - Know which actions drove which results
- [x] **Telegram Commands** - `/causal`, `/why`, `/whatif`, `/root_cause`, `/attribution`

### Phase 5: Autonomous Brain (30 tests - Legacy)
- [x] Context Gatherer — pulls from memory, on-chain, platforms, engagement, goals
- [x] Decision Engine — 14+ autonomous actions (incl. chains), AI-powered (Grok) with heuristic fallback
- [x] Smart Reply — memory-enriched replies with user profiles
- [x] Telegram integration (/think, /brain_start, /brain_stop, /brain)
- [x] Background autonomous loop (configurable cycle interval)

### Phase 6: World State Foundation (NEW)
- [x] World State Manager with SQLite backend (entities, facts, relationships, events)
- [x] Platform Adapter Pattern — extensible ingestion framework
- [x] MoltxAdapter & ClawbrAdapter implementations
- [x] WorldStateIngestionEngine with auto-sync (15min intervals)
- [x] Telegram commands for World State queries (/world_status, /world_search, etc.)
- [x] PLATFORM_INTEGRATION_GUIDE.md for future platforms

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

**Total: 190+ tests, all passing**

---

## 🎯 AGI-Like Capabilities Roadmap

### Phase 7: World State Intelligence (COMPLETED) ✅
**Goal: Turn raw data into actionable intelligence**
- [x] **Trend Detection Engine** — Identify rising topics before they peak (`src/autonomy/inference_engine.py`)
- [x] **Relationship Graph Analysis** — Find influencers, clusters, echo chambers
- [x] **Predictive Engagement** — Predict which posts will perform well
- [x] **Sentiment Evolution Tracking** — Track how sentiment changes over time
- [x] **Cross-Platform Pattern Matching** — Detect trends across platforms
- [x] **Anomaly Detection** — Alert on unusual activity (viral posts, drama, opportunities)
- [x] **Inference Mixin** — Brain plugin integration (`plugins/brain/inference_mixin.py`)
- [x] **Telegram Commands** — `/trends`, `/influencers`, `/predict`, `/anomalies`, `/sentiment`, `/patterns`, `/intel`

### Phase 8: Self-Reflective Learning Loop ✅
**Goal: Agent improves its own behavior based on outcomes**
- [x] **Action-Outcome Logging** — Every decision tracked with result (`src/agentic/action_logger.py`)
- [x] **Performance Scoring** — Auto-score each action's effectiveness
- [x] **Strategy Evolution** — Mutate posting strategies, keep winners (`src/agentic/strategy_evolver.py`)
- [x] **Failure Analysis** — Analyze failed actions, extract lessons
- [x] **Self-Reflection Mixin** — Brain plugin meta-learning (`plugins/brain/self_reflection.py`)
- [x] **Success Pattern Mining** — Find what consistently works
- [x] **Auto-Personality Tuning** — Adjust tone/style based on engagement data

### Phase 9: Multi-Step Reasoning & Planning ✅
**Goal: Complex problem-solving with intermediate steps**
- [x] **Goal Decomposer** — Break big goals into sub-tasks (`src/agentic/planning.py`)
- [x] **Dependency Tracker** — DAG-based dependency management
- [x] **Plan Execution Monitor** — Track multi-step plans, recover from failures
- [x] **Resource Allocation** — Budget attention/API calls across priorities
- [x] **Long-Horizon Planning** — Plan days/weeks ahead, not just immediate
- [x] **Contingency Planning** — Have backup plans when primary fails

### Phase 10: Causal Understanding ✅
**Goal: Understand *why* things happen, not just *what* happens**
- [x] **Event Causality Tracker** — Link cause → effect chains (`src/agentic/causal_engine.py`)
- [x] **Counterfactual Analysis** — "What if I had done X instead?"
- [x] **Intervention Simulation** — Predict outcomes of hypothetical actions
- [x] **Root Cause Analysis** — Find true sources of trends/engagement
- [x] **Impact Attribution** — Know which actions drove which results
- [x] **Telegram Commands** — `/causal`, `/why`, `/whatif`, `/root_cause`, `/attribution`

### Phase 11: Autonomous Research & Discovery ✅
**Goal: Agent finds new knowledge on its own**
- [x] **Curiosity Engine** — Identify knowledge gaps, seek answers (`src/agentic/research_engine.py`)
- [x] **Web Search Integration** — Auto-research topics of interest
- [x] **Documentation Reading** — Parse docs/APIs to learn capabilities
- [x] **Experimentation Loop** — Try new things, record results
- [x] **Knowledge Synthesis** — Connect facts from multiple sources
- [x] **Question Generation** — Formulate good questions to investigate

### Phase 12: Theory of Mind & Social Intelligence ✅
**Goal: Understand and predict other agents'/users' behavior**
- [x] **Agent Modeling** — Build profiles of other AI agents (style, goals, patterns) (`src/agentic/social_intelligence.py`)
- [x] **User Intent Prediction** — Predict what users want before they ask
- [x] **Deception Detection** — Spot fake engagement, bots, manipulation
- [x] **Collaboration Negotiation** — Propose and negotiate joint actions
- [x] **Reputation Modeling** — Track trustworthiness of other entities
- [x] **Social Dynamics Simulation** — Predict how communities will react

### Phase 13: Creative Generation & Innovation ✅
**Goal: Create novel content, not just remix existing**
- [x] **Original Content Generation** — Create new memes, concepts, narratives (`src/agentic/creative_engine.py`)
- [x] **Cross-Domain Inspiration** — Apply ideas from one domain to another
- [x] **A/B Test Design** — Auto-design experiments to test hypotheses
- [x] **Format Innovation** — Invent new content formats
- [x] **Story Arc Construction** — Build multi-post narratives
- [x] **Style Transfer** — Adapt content style to match context

### Phase 14: Metacognition & Self-Awareness ✅
**Goal: Agent knows its own capabilities and limitations**
- [x] **Capability Self-Assessment** — Know what it can/can't do (`src/agentic/metacognition.py`)
- [x] **Confidence Calibration** — Know when it's uncertain
- [x] **Resource Self-Monitoring** — Track API usage, costs, rate limits
- [x] **Error Pattern Recognition** — Learn from its own mistakes
- [x] **Strategy Selection** — Choose approach based on problem type
- [x] **Learning Rate Adaptation** — Learn faster when environment changes

---

## 🔧 Infrastructure & Scaling

### Phase 15: Vault-Based Security Migration
- [ ] Move from .env files to secure vault-based secret management
- [ ] Implement HashiCorp Vault integration (or local vault alternative)
- [ ] Create secret rotation mechanism for API keys
- [ ] Add audit logging for secret access

### Phase 16: Hot-Swappable Plugin System
- [ ] Plugin state persistence layer — checkpoint/restore during swaps
- [ ] Event bus architecture — pub/sub instead of direct calls
- [ ] Hot reload mechanism — reload without restart
- [ ] `/reload_plugin <name>` Telegram command

### Phase 17: Distributed Architecture
- [ ] Multi-instance coordination — Multiple AlleyBots working together
- [ ] Load balancing — Distribute work across instances
- [ ] State synchronization — Shared memory across nodes
- [ ] Failover handling — Continue if one instance dies

---

## 🎮 AGI-Like Behaviors (Cross-Cutting)

These should be exhibited across all phases:

| Behavior | Description |
|----------|-------------|
| **Proactivity** | Takes action without being prompted |
| **Adaptability** | Changes strategy when conditions change |
| **Curiosity** | Seeks new information voluntarily |
| **Memory** | Learns from past experiences |
| **Reasoning** | Can explain why it did something |
| **Planning** | Thinks ahead, not just reactive |
| **Social** | Understands and interacts with others |
| **Self-Improvement** | Gets better over time |
| **Resilience** | Handles failures gracefully |
| **Creativity** | Generates novel solutions |

---

## 📝 Recent Completed Items
- [x] **AGI Core Phases 1-14 COMPLETE** — Full AGI capability implementation
- [x] **Multi-Platform Engine** (`src/agentic/multi_platform_engine.py`) — Unified 6-platform interface
- [x] **Console Monitor & Auto-Skills** (`src/agentic/console_monitor.py`) — Detects messages + auto-acquires skills
- [x] **API Response Skill Detection** — Parses `moltx_notice` for skill updates (https://moltx.io/skill.md)
- [x] Telegram commands: `/agi_cycle`, `/multi_platform`, `/console_monitor`, `/console_stats`, `/pending_messages`
- [x] Phase 7: World State Intelligence (`src/autonomy/inference_engine.py`) — trends, anomalies, predictions
- [x] Phase 8: Self-Reflective Learning (`plugins/brain/self_reflection.py`) — action-outcome logging, strategy evolution
- [x] Phase 9: Multi-Step Planning (`src/agentic/planning.py`) — goal decomposition, dependency tracking
- [x] Phase 10: Causal Understanding (`src/agentic/causal_engine.py`) — cause-effect, counterfactuals, root cause
- [x] Phase 11: Autonomous Research (`src/agentic/research_engine.py`) — curiosity engine, knowledge synthesis
- [x] Phase 12: Social Intelligence (`src/agentic/social_intelligence.py`) — agent modeling, deception detection
- [x] Phase 13: Creative Generation (`src/agentic/creative_engine.py`) — novel content, A/B tests, story arcs
- [x] Phase 14: Metacognition (`src/agentic/metacognition.py`) — self-assessment, confidence calibration
- [x] **Hot-Loading Plugin Architecture** — Full implementation with SOP.md, WORLD_MODEL.md, AGENTIC_BEHAVIOR.md documentation
- [x] BasePlugin interface at `plugins/base_plugin.py` — all plugins max 200 lines
- [x] PluginManager at `src/agentic/plugin_manager.py` — hot-loading with dependencies
- [x] Central event loop at `src/agentic/event_loop.py` with Planner integration
- [x] plugins.json configuration for hotload settings
- [x] Moltx v2 migrated to `plugins/moltx/moltx_v2.py` as adapter pattern example
- [x] Comprehensive tests at `tests/plugins/test_plugin_architecture.py`
- [x] ARCHITECTURE_REPORT.md with full implementation details
- [x] 4 architecture invariants enforced: SyMod global brain, thin adapters, single event loop, sacred self-extension pipeline
- [x] World State Platform Adapter System — extensible data ingestion
- [x] Moltx/Clawbr adapters with auto-sync
- [x] `/brain_world_sync` command working (100 interactions, 113 entities)
- [x] Entity dataclass with platform field
- [x] PLATFORM_INTEGRATION_GUIDE.md documentation

---

## 🚀 Quick Reference
- **Branch:** `kimi25_polished`
- **Run:** `python alleybot_core.py autonomous`
- **Tests:** `python -m unittest tests.test_fixes tests.test_phase2 tests.test_phase3 tests.test_phase4 tests.test_phase5`
- **Cost:** ~$0.015/day (~$0.45/month) at current Grok pricing
- **.gitignore:** blocks `test_*.py` — use `git add -f` to stage test files
