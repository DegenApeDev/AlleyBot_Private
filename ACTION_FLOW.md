# AlleyBot Action Flow - Migration to AGI-Like Autonomy

**Document:** ACTION_FLOW.md  
**Date:** 2026-02-14  
**Purpose:** Concrete implementation roadmap from current command-driven flow to goal-driven autonomous agent  
**Target:** Enable AlleyBot to "do as it pleases" with reasoning, safety, and skill building

---

## Current State Summary

AlleyBot today is **event-driven with reactive command handling**:
- Telegram commands trigger immediate plugin actions
- Brain runs action chains from `AUTONOMOUS_ACTIONS` list
- Memory exists (SQLite + BERT) but is fetch-on-demand, not predictive
- No explicit goal stack or planning layer
- Security filters exist but aren't unified gates

**Missing for true autonomy:**
- Goal persistence and prioritization
- Multi-step planning with option generation
- Pre-action reasoning with tradeoffs
- Outcome-based learning loop
- Dynamic skill synthesis
- **Explicit world-state / world-model module** (structured environment for planning)

---

**Note on timelines:** Time estimates (2-week chunks) may be optimistic for Policy Learner, Capability Catalog, and robust Synergy integration, given how much design and testing these usually take in production agentic systems. Adjust based on team capacity and complexity encountered.

---

## Phase 1: Foundation (Week 1-2)
**Goal:** Stabilize before adding autonomy complexity

### 1.1 Plugin Contract Hardening
**Files:** @plugin_manager.py, @plugins/*/ directories

**Actions:**
1. Add `REQUIRED_METHODS` registry per plugin type in `plugin_manager.py`
2. Create startup validation that fails fast if critical plugins missing methods
3. Add smoke test: iterate all `get_commands()` return values, assert callable
4. Standardize: every plugin exposes `health_check()` → `{ok: bool, error?: str}`

**Deliverable:** Plugin failures block startup with clear error, not silent degradation.

---

### 1.2 Endpoint Ownership Consolidation
**Files:** @plugins/moltx/moltx_api.py, @plugins/moltx/moltx_messaging.py, @plugins/moltx/moltx_engagement.py

**Actions:**
1. Move ALL Moltx endpoint paths into `moltx_api.py` as canonical methods
2. Refactor `moltx_messaging.py` and `moltx_engagement.py` to call API mixin, never `_make_request` directly
3. Repeat for Clawbr: single `clawbr_api.py` owns all `/v1/*` paths
4. Document: "If you add an endpoint, it goes in API mixin only"

**Deliverable:** One source of truth per platform; no more endpoint drift.

---

### 1.3 Configuration Standardization
**Files:** @plugins/telegram/telegram.py, @src/main.py, @config.py

**Actions:**
1. Replace all `TELEGRAM_OWNER_ID` references with `TELEGRAM_ADMIN_CHAT_ID`
2. Remove hardcoded fallback IDs in production paths
3. Add startup assertion: `TELEGRAM_ADMIN_CHAT_ID` must be set and valid integer

**Deliverable:** One env var, no ambiguity, no hardcoded secrets.

---

### 1.4 Security Filter Unification
**Files:** @security_filter.py, @src/agentic/security_filter.py

**Actions:**
1. Create `src/security/policy_engine.py` with shared `SecurityPolicy` class
2. Migrate both filters to use shared policy
3. Harden `_is_allowed_domain` with `urllib.parse.urlparse` + exact host checks
4. Add test: malicious URL containing allowed domain substring must be blocked

**Deliverable:** Single security policy enforced everywhere.

---

## Phase 2: Autonomy Core (Week 3-4)
**Goal:** Add goal-driven reasoning layer

### 2.1 Goal Stack Manager
**New File:** `src/autonomy/goal_manager.py`

**Actions:**
1. Implement `GoalStack` with priority queue, deadlines, and success criteria
2. Goals have: `id`, `description`, `priority`, `created_at`, `deadline`, `success_fn`, `status`
3. Integrate into `AlleyBotCore` initialization
4. Persist goals to SQLite with CRUD ops
5. Expose methods: `push_goal()`, `pop_completed()`, `get_active()`, `evaluate_success()`

**Deliverable:** Persistent, prioritized goal stack accessible to all components.

---

### 2.2 Planner Module
**New File:** `src/autonomy/planner.py`

**Actions:**
1. Implement `Planner` that takes a goal and generates 2-4 action plan options
2. Each option = list of capability calls with estimated cost/risk
3. Options scored by: success probability, resource cost, alignment with current state
4. Integrate into Brain: before executing, ask Planner for options

**Deliverable:** Every autonomous cycle considers multiple paths, not single action chain.

---

### 2.3 Model Upgrade (Word/Reasoning Model)
**Files:** @src/config/models.py, @src/agents/event_runner.py

**Actions:**
1. **Add reasoning model tier:**
   - Fast: DeepSeek-Chat (routine actions)
   - Deep: Grok-4.1-reasoning (planning, strategy, debate analysis)
   - Synergy: Local BERT (embedding, sentiment, lightweight classification)
2. Update `ModelRouter` with `select_model(task_type)`:
   - `task_type: "fast" | "reasoning" | "embedding"`
3. Route planner queries to Grok-reasoning
4. Route memory retrieval to local BERT
5. Add cost tracking per model tier

**Deliverable:** Reasoning-heavy tasks use capable models; routine tasks stay cheap.

---

### 2.4 Synergy Gate Integration
**Files:** @src/synergy/synergy_logic.py, @plugins/brain/decision_engine.py

**Actions:**
1. Import `SynergyStandardModel` and `ContextToVectorBridge` into decision engine
2. Before any high-impact action (`create_post`, `vote_debate`, `send_transaction`):
   - Run `validate_debate_argument()` or `validate_defi_trade()`
   - Check `impedance`, `digital_root_contradiction`, `golden_window_aligned`
3. If Synergy flags high risk: downgrade to observation or request owner approval
4. Log all Synergy decisions to memory for learning

**Deliverable:** Mathematical truth validation gates autonomous actions.

---

### 2.5 World State Model
**New File:** `src/autonomy/world_state.py`

**Actions:**
1. Implement `WorldState` class maintaining typed snapshot of:
   - Platform health/status (Moltx, Clawbr, Moltbook connectivity)
   - Active campaigns and their progress
   - Budget consumption (tokens, time, actions used)
   - Recent action outcomes and their deltas
2. Provide structured queries: `get_platform_status()`, `get_campaign_state()`, `get_budget_consumed()`
3. Update via Reflection/Feedback loop after every action
4. Expose to Planner and Policy Learner as primary read source (not raw memory stitching)
5. Enable Synergy to use richer context for risk checks

**Deliverable:** Structured world model that planning and policy can reason over, not just raw memory retrieval.

---

## Phase 3: Learning + World State (Week 5-8)
**Goal:** Close the feedback loop for continuous improvement

### 3.1 Reflection Engine
**New File:** `src/autonomy/reflection.py`

**Actions:**
1. After every executed action, capture:
   - Action taken
   - Expected outcome (from planner)
   - Actual outcome (from platform response)
   - Delta (success, partial, failure)
2. Score outcome with Synergy: `sentiment_mass`, `pressure_vector`, `field_status`
3. Update goal progress if action contributed
4. If goal blocked, trigger replanning

**Deliverable:** Every action produces a reflection record in memory.

---

### 3.2 Policy Learner
**New File:** `src/autonomy/policy_learner.py`

**Actions:**
1. Maintain `strategy_success_db`: action_type + context_hash → outcome scores
2. Weekly (or every N actions), retrain policy weights:
   - Which strategies succeed in which contexts?
   - Update Planner scoring weights
3. Expose: `get_best_strategy(context)` → recommended action_type
4. Gradually shift from static `AUTONOMOUS_ACTIONS` to learned policy

**Deliverable:** Agent improves action selection based on historical success.

---

### 3.3 Autonomy Budget
**New File:** `src/autonomy/budget.py`

**Actions:**
1. Implement `AutonomyBudget` per cycle:
   - Max tokens (API cost limit)
   - Max time (response latency limit)
   - Max actions (depth limit)
2. Planner respects budget: discard options exceeding limits
3. If budget exhausted mid-cycle, save state and resume next cycle

**Deliverable:** Bounded autonomy prevents runaway cost/latency.

---

### 3.4 World State Integration
**Files:** `src/autonomy/world_state.py`, @plugins/brain/decision_engine.py, @plugins/brain/feedback_loop.py

**Actions:**
1. Wire Feedback Loop to update World State after every action outcome
2. Modify Planner to query World State for context, not stitch from raw memory
3. Add Policy Learner context enrichment from World State (what worked in similar platform states)
4. Use World State in Synergy risk calculations (platform health affects action confidence)

**Deliverable:** Planner, Policy, and Synergy reason over structured world model, not ad-hoc memory queries.

---

## Phase 4: Skill & Strategy Expansion (Week 9-12)
**Goal:** Self-expanding capabilities

### 4.1 Capability Catalog
**New File:** `src/autonomy/capability_catalog.py`

**Actions:**
1. Normalize all plugins to expose `CAPABILITIES = { "post": {...}, "search": {...} }`
2. Catalog maintains registry: capability_id → plugin → method → parameters
3. Planner queries catalog: "What can do 'post'?" → [Moltx, Moltbook, Clawbr]
4. Enable cross-platform strategies: "Post to Moltx + link in Moltbook"

**Deliverable:** Planner reasons over capabilities, not specific plugins.

---

### 4.2 Dynamic Skill Generation (Experimental/Gated)
**Files:** @plugins/selfimprove/, @src/agentic/skill_generator.py

**Actions:**
1. **Lock down static tool guardrails first** — ensure existing skills have full auditability and permission checks
2. When Planner encounters missing capability, trigger skill synthesis request (not auto-execution)
3. Skill generator creates YAML skill definition + minimal Python wrapper in isolated sandbox
4. **Require owner approval** before deploying any generated skill
5. Synergy validates: new skill must pass `check_golden_window()` or equivalent
6. Deploy to `dynamic_skills/` with explicit experimental flag and full audit logging
7. Hot-load only after owner approval (or require restart with warning)
8. Log all generated skills with generation trace for review

**Safety guardrails:**
- Owner approval required for all generated skills
- Sandbox execution environment for testing
- Separate permission model for dynamic vs static skills
- Audit trail: who approved, when, what was generated
- Rollback capability if skill causes issues

**Deliverable:** Agent can propose new skills, but deployment is gated and auditable.

---

## Integration Points (Where to Wire)

| New Component | Hooks Into | File Location |
|--------------|------------|---------------|
| World State | Brain init, every cycle, Feedback updates | `src/autonomy/world_state.py` |
| Goal Stack | Brain init, every cycle | `@plugins/brain/decision_engine.py` |
| Planner | Before action selection, reads World State | `@plugins/brain/decision_engine.py` |
| Synergy Gate | Pre-action in decision engine | `@plugins/brain/decision_engine.py` |
| Reflection | Post-action, updates World State | `@plugins/brain/feedback_loop.py` |
| Policy Learner | Weekly cron + reflection + World State data | New file |
| Budget | Planner constraints | New file |
| Capability Catalog | Plugin registration | `@plugin_manager.py` |

---

## Success Metrics

By end of Phase 4, AlleyBot should:
1. **Persist 5-10 active goals** with automatic priority adjustment
2. **Generate 2-4 plan options** before every autonomous action
3. **Block/refine 15-30% of actions** via Synergy validation
4. **Improve action success rate 10-20%** via policy learning over 4 weeks
5. **Synthesize 1-2 novel skills/month** without human coding
6. **Stay within autonomy budget** 95% of cycles

---

## Model Upgrade Details (Word/Reasoning)

### Current
- Single model path: DeepSeek default, Grok fallback
- No reasoning tier distinction

### Target
```python
class ModelRouter:
    def select_model(self, task: Task) -> Model:
        if task.requires_reasoning or task.is_planning:
            return grok_reasoning  # Deep analysis, strategy
        elif task.requires_embedding:
            return local_bert      # On-device, fast
        else:
            return deepseek_chat   # Fast, cheap
```

**Benefits:**
- Better planning quality (Grok reasoning)
- Lower API costs (BERT for local tasks)
- Faster routine responses (DeepSeek)

---

## Appendix: Quick Reference

**Start here:**
1. Week 1: Plugin contracts + endpoint consolidation
2. Week 3: Goal Stack + Planner (minimal viable)
3. Week 5: Synergy Gate + Reflection
4. Week 7: Capability Catalog + Dynamic Skills

**Key Files to Create:**
- `src/autonomy/world_state.py`
- `src/autonomy/goal_manager.py`
- `src/autonomy/planner.py`
- `src/autonomy/reflection.py`
- `src/autonomy/policy_learner.py`
- `src/autonomy/budget.py`
- `src/autonomy/capability_catalog.py`

**Key Files to Modify:**
- `@plugin_manager.py` — contract validation
- `@plugins/brain/decision_engine.py` — planner + synergy integration
- `@plugins/brain/feedback_loop.py` — reflection hook
- `@src/config/models.py` — reasoning tier routing

---

## FUTURISTIC: Beyond Current Roadmap (Research-Inspired)

Based on arxiv.org/html/2508.09561 — "Edge General Intelligence Through World Models and Agentic AI"

### Vision: From Reactive Agent to Imagination-Driven Intelligence

Current roadmap builds a goal-driven agent. The frontier is an agent that **simulates futures internally** before acting — dramatically reducing costly real-world mistakes.

---

### Core Insight from Research

World models enable three capabilities:
1. **Policy learning via imagination** — replace costly real interactions with simulated rollouts
2. **High-fidelity prediction** — forecast outcomes 100+ steps ahead
3. **Structural reasoning** — causal analysis of action→consequence chains

**Key result:** PlaNet achieved strong performance with **200x less environment interaction** than model-free methods.

---

### Phase 5: Predictive World Model (Month 4-6)

Upgrade `WorldState` from static snapshot to **generative simulator**:

#### 5.1 Latent State Encoder (BERT-Powered)
**New File:** `src/worldmodel/encoder.py`

**Actions:**
1. Compress platform observations into compact latent vectors
2. Use BERT embeddings to encode: posts, debates, sentiment, engagement patterns
3. Discard noise (billboard text), retain predictive features (sentiment trajectory, engagement velocity)
4. Output: 32-128 dimensional latent state per platform

**Deliverable:** Compact, meaningful state representations for fast simulation.

---

#### 5.2 Dynamics Predictor (Lightweight RNN)
**New File:** `src/worldmodel/dynamics.py`

**Actions:**
1. Train RNN/Transformer on historical (state, action, next_state) triples
2. Predict: "If I post X on Moltx, what will engagement be in 1h, 6h, 24h?"
3. Support multi-step rollout: simulate 10-50 future steps in milliseconds
4. Uncertainty-aware: output distribution, not point estimate

**Deliverable:** Internal "physics engine" for social platform dynamics.

---

#### 5.3 Imagination Rollout Engine
**New File:** `src/worldmodel/rollout.py`

**Actions:**
1. For each plan option, simulate N trajectories (10-100 rollouts)
2. Score trajectories by predicted reward, risk, resource consumption
3. Return: expected value + variance for each plan
4. Enable "what if" queries without API calls

**Deliverable:** Planner evaluates imagined futures, not just static context.

---

#### 5.4 Dreamer-Style Policy Learning
**New File:** `src/worldmodel/dreamer_policy.py`

**Actions:**
1. Train policy entirely in latent space via imagination
2. Actor-critic: actor proposes actions, critic evaluates imagined outcomes
3. Backpropagate through dynamics model to improve policy
4. Bootstrap value predictions beyond imagination horizon

**Deliverable:** Policy improves from imagined experience, reducing real API costs.

---

### Phase 6: MuZero-Style Tree Search (Month 7-9)

For high-stakes decisions (major campaigns, debates, investments):

#### 6.1 Monte Carlo Tree Search in Latent Space
**New File:** `src/worldmodel/mcts_planner.py`

**Actions:**
1. Represent current situation as latent root node
2. Expand tree: each node = action, edges = predicted transitions
3. Rollout to terminal: evaluate cumulative reward
4. Select action with highest expected value + exploration bonus

**Deliverable:** Superhuman planning for complex multi-step campaigns.

---

#### 6.2 Value-Equivalent Model (MuZero-Style)
**New File:** `src/worldmodel/muzero_model.py`

**Actions:**
1. Abandon pixel/text reconstruction (expensive)
2. Learn dynamics focused only on reward-relevant features
3. Representation function → dynamics → reward/value/policy heads
4. No explicit environment rules needed (learn from data)

**Deliverable:** Model ignores billboard text, focuses on what drives engagement.

---

### Phase 7: Edge-Optimized Deployment (Month 10-12)

#### 7.1 Quantized World Model
**Actions:**
1. Quantize encoder/dynamics to 4-bit precision
2. Target: <500MB RAM for full world model
3. Maintain performance within 5% of full model

**Deliverable:** World model runs on-device, no cloud dependency for imagination.

---

#### 7.2 Hybrid Cloud-Edge Architecture
**Actions:**
1. Imagination rollouts: on-device (fast, cheap, offline-capable)
2. High-stakes MCTS: cloud Grok-4.1 for deep reasoning
3. Automatic fallback: if cloud unavailable, rely on edge imagination

**Deliverable:** Graceful degradation, autonomy even in disconnected environments.

---

### Research-Backed Success Metrics

By end of Phase 7:
1. **10-50x reduction in API calls** — agent practices in imagination first
2. **Sub-100ms planning** — N trajectories evaluated faster than single real action
3. **Human-level debate/social performance** — purely from imagined practice
4. **Graceful offline operation** — edge world model sustains autonomy without cloud

---

### Why This Matters for AlleyBot

| Current | Futuristic |
|---------|-----------|
| Try action → observe result → learn (costly) | Imagine 100 actions → pick best → execute once (cheap) |
| Static context for planning | Dynamic simulation of futures |
| Learns from mistakes (expensive) | Practices safely in latent space |
| Cloud-dependent for reasoning | Edge-imagination + cloud-deep-reasoning hybrid |

**The ultimate goal:** An agent that can "think" for hours internally, then execute a minimal, optimal set of real actions.

---

### Key Papers Referenced

- Ha & Schmidhuber 2018: "World Models" — VAE-based latent planning
- PlaNet (2019): Model-predictive control in latent space, 200x sample efficiency
- DreamerV2 (2020): Discrete latent spaces, human-level Atari from imagination
- MuZero (2020): MCTS in latent space without environment rules
- DreamerPro: Prototype-driven abstraction, reconstruction-free

---

*Generated for AlleyBot AGI migration — from reactive to imagination-driven intelligence.*

---

*Generated for AlleyBot AGI migration — actionable, phased, measurable.*
