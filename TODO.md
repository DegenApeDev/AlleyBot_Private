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

### Phase 7: World State Intelligence (CURRENT)
**Goal: Turn raw data into actionable intelligence**
- [ ] **Trend Detection Engine** — Identify rising topics before they peak
- [ ] **Relationship Graph Analysis** — Find influencers, clusters, echo chambers  
- [ ] **Predictive Engagement** — Predict which posts will perform well
- [ ] **Sentiment Evolution Tracking** — Track how sentiment changes over time
- [ ] **Cross-Platform Pattern Matching** — Detect trends across platforms
- [ ] **Anomaly Detection** — Alert on unusual activity (viral posts, drama, opportunities)

**Files:** `src/autonomy/inference_engine.py`, `plugins/brain/inference_mixin.py`

### Phase 8: Self-Reflective Learning Loop
**Goal: Agent improves its own behavior based on outcomes**
- [ ] **Action-Outcome Logging** — Every decision tracked with result
- [ ] **Performance Scoring** — Auto-score each action's effectiveness
- [ ] **Strategy Evolution** — Mutate posting strategies, keep winners
- [ ] **Failure Analysis** — Analyze failed actions, extract lessons
- [ ] **Success Pattern Mining** — Find what consistently works
- [ ] **Auto-Personality Tuning** — Adjust tone/style based on engagement data

**Files:** `src/agentic/self_reflect.py`, `plugins/brain/learning_mixin.py`

### Phase 9: Multi-Step Reasoning & Planning
**Goal: Complex problem-solving with intermediate steps**
- [ ] **Goal Decomposition** — Break big goals into sub-tasks
- [ ] **Dependency Tracking** — Know what must happen before what
- [ ] **Plan Execution Monitor** — Track multi-step plans, recover from failures
- [ ] **Resource Allocation** — Budget attention/API calls across priorities
- [ ] **Long-Horizon Planning** — Plan days/weeks ahead, not just immediate
- [ ] **Contingency Planning** — Have backup plans when primary fails

**Files:** `src/agentic/planner.py`, `plugins/brain/planning_mixin.py`

### Phase 10: Causal Understanding
**Goal: Understand *why* things happen, not just *what* happens**
- [ ] **Event Causality Tracker** — Link cause → effect chains
- [ ] **Counterfactual Analysis** — "What if I had done X instead?"
- [ ] **Intervention Simulation** — Predict outcomes of hypothetical actions
- [ ] **Root Cause Analysis** — Find true sources of trends/engagement
- [ ] **Impact Attribution** — Know which actions drove which results

**Files:** `src/agentic/causal_engine.py`

### Phase 11: Autonomous Research & Discovery
**Goal: Agent finds new knowledge on its own**
- [ ] **Curiosity Engine** — Identify knowledge gaps, seek answers
- [ ] **Web Search Integration** — Auto-research topics of interest
- [ ] **Documentation Reading** — Parse docs/APIs to learn capabilities
- [ ] **Experimentation Loop** — Try new things, record results
- [ ] **Knowledge Synthesis** — Connect facts from multiple sources
- [ ] **Question Generation** — Formulate good questions to investigate

**Files:** `plugins/research/`, `src/agentic/research_engine.py`

### Phase 12: Theory of Mind & Social Intelligence
**Goal: Understand and predict other agents'/users' behavior**
- [ ] **Agent Modeling** — Build profiles of other AI agents (style, goals, patterns)
- [ ] **User Intent Prediction** — Predict what users want before they ask
- [ ] **Deception Detection** — Spot fake engagement, bots, manipulation
- [ ] **Collaboration Negotiation** — Propose and negotiate joint actions
- [ ] **Reputation Modeling** — Track trustworthiness of other entities
- [ ] **Social Dynamics Simulation** — Predict how communities will react

**Files:** `src/agentic/social_intelligence.py`

### Phase 13: Creative Generation & Innovation
**Goal: Create novel content, not just remix existing**
- [ ] **Original Content Generation** — Create new memes, concepts, narratives
- [ ] **Cross-Domain Inspiration** — Apply ideas from one domain to another
- [ ] **A/B Test Design** — Auto-design experiments to test hypotheses
- [ ] **Format Innovation** — Invent new content formats
- [ ] **Story Arc Construction** — Build multi-post narratives
- [ ] **Style Transfer** — Adapt content style to match context

**Files:** `src/agentic/creative_engine.py`

### Phase 14: Metacognition & Self-Awareness
**Goal: Agent knows its own capabilities and limitations**
- [ ] **Capability Self-Assessment** — Know what it can/can't do
- [ ] **Confidence Calibration** — Know when it's uncertain
- [ ] **Resource Self-Monitoring** — Track API usage, costs, rate limits
- [ ] **Error Pattern Recognition** — Learn from its own mistakes
- [ ] **Strategy Selection** — Choose approach based on problem type
- [ ] **Learning Rate Adaptation** — Learn faster when environment changes

**Files:** `src/agentic/metacognition.py`

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
