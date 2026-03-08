# AlleyBot TODO — True Autonomy Roadmap

---

## Mission

AlleyBot already has a large portion of the AGI stack implemented:

- memory systems
- world state
- goal generation
- planning
- causal reasoning
- research
- creative generation
- social intelligence
- metacognition
- SyMod validation
- Synergy field validation
- autonomous brain loops
- self-improvement pipeline

The next phase is not adding random new features.
The next phase is **turning all existing systems into one coherent autonomous runtime**.

The near-term mission is to push AlleyBot from partially unified autonomy toward a more human-like autonomy loop:

- perceive
- interpret
- predict
- plan
- validate
- act
- reflect
- learn
- adapt

The core objective is:

**One brain, one execution pipeline, one validation ladder, one learning loop.**

---

## Current Reality

### What is already implemented

- [x] AGI Kernel integration layer
- [x] AGI Orchestrator with multi-phase cycle
- [x] Autonomous Brain loop
- [x] Goal systems and goal stack
- [x] Unified memory + episodic memory + SQLite persistence
- [x] World state ingestion and inference engine
- [x] Social, creative, causal, research, and metacognitive systems
- [x] SyMod-based validation systems
- [x] Egyptian Synergy model / harmonic validation
- [x] Telegram command layer for monitoring and control
- [x] Self-improvement / autonomous coding pipeline
- [x] Multi-platform adapters and posting/engagement systems
- [x] Routed execution for the main autonomous proposal, goal, and orchestrator paths
- [x] Routed validation traces for the main autonomous path
- [x] Lightweight prediction artifact scaffolding on routed actions
- [x] Recent action performance now partially informs decision ranking
- [x] Explicit prediction evaluation and mismatch scoring now exist on routed outcomes
- [x] Bounded exploration metadata now exists for low-evidence, low-risk actions
- [x] Short multi-step routed plan tracking and revised-plan execution now exist on the main routed path
- [x] Replanning now uses structured reflection signals plus recent action-family performance
- [x] Repeated failed replans now escalate into safer alternate paths or bounded abandonment
- [x] Degraded action-family cooldown, decay, and recovery-aware avoidance now shape decision ranking

### What is still missing for true full autonomy

- [ ] A single authoritative execution pipeline
- [ ] A single authoritative validation pipeline
- [ ] A canonical action schema across all autonomous systems
- [ ] Consistent goal-to-action compilation
- [ ] Consistent outcome recording and feedback into memory
- [ ] Clear trust tiers for safe vs dangerous autonomy
- [ ] Full alignment between documentation, architecture, and runtime behavior
- [ ] Explicit expected-vs-actual reflection mismatch scoring across all autonomous surfaces
- [ ] Strong memory-informed autonomous action selection across all autonomous surfaces
- [ ] Bounded experimentation for uncertainty reduction across all autonomous surfaces
- [ ] Short multi-step plan persistence and replanning across all autonomous surfaces

---

## Current Priority Order

Choose work in this order unless a critical bug or security issue overrides it:

1. [ ] Eliminate remaining execution-path fragmentation
2. [ ] Normalize validation contracts and trust/risk tiers
3. [ ] Complete canonical action coverage for remaining helper/plugin surfaces
4. [ ] Close outcome-to-learning consistency across all routed actions
5. [~] Make autonomous action selection more memory-informed and prediction-informed
6. [~] Add expected-vs-actual reflection mismatch scoring
7. [~] Introduce bounded exploratory actions for uncertainty reduction
8. [~] Upgrade from next-action choice to short plan execution and replanning
9. [ ] Simplify runtime ownership and publish architecture truth

---

## Priority 1 — Unify Autonomous Execution

**Goal:** Every autonomous action must execute through one path.

### Problems to solve

- [x] `AutonomousBrain` direct proposal execution path removed from the main runtime flow
- [x] `AGIOrchestrator._execute_plan()` now emits canonical action specs and routes through `AGIKernel.act()`
- [ ] Some plugin actions and synchronous command/helper surfaces are still invoked ad hoc instead of through a shared executor
- [~] Some older helper/plugin surfaces still retain legacy direct execution assumptions, but the decision-engine direct-dispatch surface has been reduced for already-supported routed actions
- [x] Main execution path now feeds a shared outcome/telemetry artifact through `ActionRouter`

### Required work

- [x] Make `AGIKernel.act()` + `ActionRouter.route_action()` the primary autonomous execution path
- [x] Refactor `AutonomousBrain` so it schedules and proposes, but does not directly execute plugin logic
- [x] Convert AGI orchestrator outputs into canonical action specs before execution
- [x] Route multi-platform campaign execution through async-native `AGIKernel.act()` calls for supported platforms (`moltx`, `clawbr`)
- [x] Route the Telegram `/multi_platform` and `/post` command surfaces into the unified orchestrator/kernel execution path
- [x] Add an async-native execution path to `plugins/brain/decision_engine.py` and route targeted high-level brain actions (`moltx_post`, `moltx_engage`, `clawbr_post`, `clawbr_engage`, `clawbr_debate_turn`, `clawbr_create_debate`, `analyze_trending`) through `AGIKernel.act()` when supported
- [x] Move legacy brain fallback execution and Golden Window queued execution onto the async-native decision-engine path
- [x] Reuse the async routed step pathway for supported chain and dynamic-chain actions such as `moltx_engage`, `clawbr_engage`, and `onchain_wallet`
- [x] Route selected low-risk helper/status actions on the decision-engine path such as `moltbit_status`, `onchain_heartbeat`, `check_engagement`, and `check_comments`
- [x] Route `update_skills` through `ActionRouter` with explicit strict risk/trust metadata so the self-improvement update flow uses fail-closed validation
- [x] Route `moltx_image_post` through `ActionRouter` by preparing content/media behind a helper seam and executing the final post through a public MoltX command wrapper
- [ ] Finish normalizing the remaining command/helper dispatch layers and direct plugin helper surfaces under the shared executor
- [x] Remove duplicated execution helpers once routing is stable
- [x] Ensure routed high-impact actions pass through the same validation/logging flow

### Done when

- [ ] No autonomous or command-driven high-level action bypasses `ActionRouter`
- [x] Execution logs now have one canonical routed outcome record for the main autonomous path
- [x] Goal progress, memory writes, and outcome reflection now happen after execution for the routed path
- [ ] Remaining helper-driven and plugin-driven execution surfaces are either routed or explicitly deprecated

---

## Priority 2 — Unify Validation

**Goal:** Every autonomous action should pass through the same layered validation policy.

### Problems to solve

- [x] Synergy and SyMod are now both present in the routed validation ladder
- [x] SyMod return shapes are normalized in `ActionRouter`
- [ ] Some code treats validators like booleans, others like tuples, others like dicts
- [ ] Security/policy validation is not clearly sequenced with reasoning validation
- [ ] Validator contracts are not yet fully normalized project-wide

### Required validation ladder

- [ ] Stage 1: Strategic relevance validation
- [x] Stage 2: Synergy field / harmonic timing validation
- [x] Stage 3: SyMod truth / mathematical integrity validation
- [ ] Stage 4: Security and policy validation
- [ ] Stage 5: Execution readiness validation

### Required work

- [ ] Standardize all validators to return a single dict structure
- [x] Create one routed validation orchestrator path in `ActionRouter`
- [ ] Define which action classes require soft validation vs hard blocking
- [~] Ensure self-improvement, trading, external posting, and on-chain actions use stricter thresholds
- [ ] Add human-readable validation traces for debugging and Telegram inspection
- [ ] Update docs so “fully integrated” only describes what is actually enforced at runtime

### Done when

- [x] Main routed autonomous actions now produce a validation trace including AGI + Synergy metadata
- [ ] Validation behavior is deterministic and easy to inspect from logs/Telegram
- [ ] No code path skips required validation stages

---

## Priority 3 — Canonical Action Model

**Goal:** Goals, plans, AGI outputs, and plugin calls all speak the same language.

### Problems to solve

- [ ] Some goal-driven and command-driven actions still need wider canonical adapter coverage across plugins
- [x] Main planner/orchestrator outputs now compile into routed execution specs for the primary orchestrator path
- [ ] Plugins still expose mixed interfaces (`execute_action`, direct methods, command methods) beyond the current routed adapters
- [~] Some higher-risk stateful helper surfaces still need careful routed treatment, but `update_skills` now routes with strict risk/trust metadata
- [~] Runtime/platform quirks still need hardening on some surfaces, but MoltX trending parsing and 5:1 engage gating have been tightened to fail closed more safely
- [ ] An action registry for AGI intent to executable action mapping is not yet complete

### Required work

- [x] Define and start using a canonical action schema for the main autonomous work path
- [ ] Finalize standard fields: `plugin`, `action_type`, `params`, `context`, `impact`, `goal_id`, `trigger`, `validation_class`, `risk_level`, `trust_level`
- [ ] Build an action registry that maps AGI intent → executable action specs
- [x] Add first-pass plugin adapters where native plugin APIs do not match the canonical schema
- [ ] Normalize the remaining command-style and method-style plugin interfaces under a shared adapter layer

### Done when

- [x] Main goal systems now emit executable specs for the routed path
- [x] Main orchestrator plan execution now compiles directly into routed actions
- [x] Legacy brain fallback and queued Golden Window execution now route targeted supported actions through canonical specs, including `moltx_engage`
- [x] Supported decision-engine chain and dynamic-chain steps now partially reuse canonical routed execution
- [x] Selected low-risk helper/status actions now compile directly into canonical routed actions, including `check_comments` via a public MoltX wrapper
- [x] `update_skills` now compiles into a routed canonical action with stricter validation metadata
- [x] `moltx_image_post` now compiles into a routed canonical action after helper-based media preparation and public-wrapper execution
- [ ] Broader planner and remaining command/helper surfaces compile directly into actions
- [ ] Every platform plugin can be invoked through a standard executor contract

---

## Priority 4 — Strengthen Goal-Driven Autonomy

**Goal:** AlleyBot should pursue goals reliably, not just generate them.

### Problems to solve

- [x] Goal mapping is now partially canonicalized for `goal_driven_cycle` and `goal_manager`
- [x] Goal progress for routed actions is now tied to the canonical outcome record
- [~] Opportunity detection and goal generation now influence autonomous pickup and pursuit on the conservative safe-goal path, but they are not yet the dominant driver of all action selection
- [~] Goal completion logic is stronger on the safe-goal path via repeated success/failure feedback, but blocked and partially completed goals still need richer handling beyond the conservative loop

### Required work

- [x] Ensure approved low-risk goals can be picked up and acted on without requiring manual Telegram commands
- [x] Make the active safe-goal state materially influence what actions are chosen next via conservative proposal bias
- [~] Add reliable handling for blocked goals, retries, partial completion, and abandonment
- [~] Add reliable handling for blocked goals, retries, partial completion, and abandonment; conservative safe goals now have soft blocked markers, basic recovery, and temporary backoff, but broader/explicit state handling is still incomplete
- [x] Reduce goal generation theater by connecting the safe-goal path to real execution and reflection loops
- [x] Reframe Telegram as a reporting/status surface rather than a constant execution driver for the conservative autonomy loop
- [x] Add owner-facing accomplishment reporting and cooldown-based autonomous digests for meaningful recent progress
- [x] Report safe-goal progress/cooling/failure states to Telegram informationally
- [~] Extend the same autonomous pickup/pursuit/feedback behavior beyond the original conservative safe-goal categories; low-impact operational `fix` goals from `error_pattern` now partially join the loop, but broader risky/stateful categories still remain manual

### Done when

- [~] Goals are not just generated; they now shape conservative safe-goal action selection and completion for analysis/optimization plus a narrow operational fix slice, but broader goal categories still need the same treatment
- [~] Goals are not just generated; they now shape conservative safe-goal action selection and completion for analysis/optimization plus a narrow operational fix slice, including blocked/backoff behavior, but broader goal categories still need the same treatment
- [~] Telegram is now used mainly for reporting, status, and high-risk intervention on the conservative autonomy path, but not all legacy surfaces are there yet
- [x] The conservative safe-goal loop can continue pursuing work across cycles without needing explicit restarts from the owner
- [x] Safe-goal outcomes now feed reflection-like future behavior through success/failure feedback and pursuit bias

---

## Priority 5 — Close the Learning Loop

**Goal:** Every action should improve future behavior.

### Problems to solve

- [x] Main routed outcome recording now has one canonical record shape
- [~] World state, episodic memory, unified memory, and action history now partially share richer canonical routed outcome metadata, but broader normalization is still incomplete
- [~] Reflection and strategy evolution now partially consume canonical routed outcome data, including ranking evidence, but broader migration is still incomplete
- [~] Reflection and strategy evolution now partially consume canonical routed outcome data, including ranking evidence and dispatch/fallback learning metadata, but broader migration is still incomplete
- [ ] Expected-vs-actual mismatch is not yet a first-class learning signal
- [~] Expected-vs-actual mismatch is now first-class on the main routed path, but not yet fully propagated across all autonomy surfaces

### Required work

- [x] Define one canonical outcome record format
- [ ] Ensure every autonomous action stores:
  - [x] action id
  - [x] goal id
  - [x] trigger
  - [x] validation trace
  - [x] execution result
  - [x] success/failure
  - [x] performance metrics
  - [x] reflection summary
  - [x] prediction artifact
  - [x] mismatch score / prediction evaluation
- [x] Feed outcomes into episodic memory and unified memory for the routed path
- [x] Feed outcomes into shared `ActionLogger` for the routed path
- [~] Feed outcomes into world state and strategy evolution consistently; strategy-evolution context now partially includes canonical ranking evidence plus dispatch/fallback learning metadata, and the world-state bridge now persists richer routed outcome metadata, but broader consistency is still incomplete
- [x] Make performance-based adaptation visible in subsequent decisions on the main routed path, including ranking-aware replanning
- [~] Some custom chain-only helpers now route their final state-changing writes through the Golden Path, but broader chain/helper execution is still not fully unified
- [x] Fallback-aware dispatch metadata now influences replanning and is summarized in kernel/strategy learning on the main routed path
- [x] World-state bridge and decision context now partially consume richer canonical routed outcome metadata, including validation/ranking/fallback summaries

### Done when

- [x] Reflection now has complete structured data for the main routed autonomous path
- [ ] Strategy evolution uses real cross-platform outcomes
- [~] AlleyBot measurably changes behavior based on past results, including caution-aware heuristic shaping from recent routed outcome summaries
- [x] Repeated overconfidence, underperformance, and reliable wins are visible in future action ranking on the main routed path

---

## Priority 5A — Memory-Informed Decisions, Prediction, and Reflection

**Goal:** Make future action selection depend on recalled experience, predicted value, and expected-vs-actual mismatch.

### Current status

- [x] `ActionLogger` now exposes recent action performance summaries
- [x] `DecisionSystem` heuristic ranking now partially considers recent outcome performance
- [x] `ActionRouter` now attaches a lightweight pre-action `prediction` artifact to routed actions
- [x] AI decision prompts are now enriched with candidate performance, plan-state, and degraded-family context on the main routed path
- [x] Reflection mismatch scoring now shapes future choices on the main routed path
- [x] Persistent action-family trust state now survives beyond immediate active plan summaries
- [x] Action-family trust buckets now shape goal selection, longer-horizon goal prioritization, secure goal generation, strategy recommendations, orchestrator context, and world-state bridge context
- [x] `AutonomousBrain` now ranks proposals using recent routed outcomes, predicted value, and lightweight episodic/unified-memory recall signals
- [x] Routed action context and canonical outcome records now persist `ranking_evidence`
- [x] Kernel learning, strategy-evolution persistence, and replanning now partially consume routed `ranking_evidence`
- [x] Decision-engine execution now emits machine-readable fallback metadata for Golden Path escapes
- [x] Replanning, kernel learning, and strategy persistence now partially consume dispatch/fallback learning metadata
- [x] World-state decision context now exposes a compact `last_routed_outcome_summary` with validation, ranking, and fallback alignment signals
- [x] Heuristic action scoring now reacts conservatively to recent Golden Path escape and poor calibration/risk signals

### Required work

- [x] Expose memory-informed candidate summaries to `_ai_decide()` in `DecisionSystem`
- [x] Compute expected-vs-actual reflection mismatch in `ActionRouter`
- [x] Include prediction evaluation in the canonical `outcome_record`
- [x] Pass mismatch metadata through kernel learning surfaces for the main routed path
- [x] Use mismatch and performance history to bias future ranking more directly
- [x] Use recalled memory, recent routed outcomes, and predicted value to shape `AutonomousBrain` proposal ranking
- [x] Persist ranking evidence through the Golden Path and into downstream learning metadata
- [x] Use ranking evidence in replanning decisions on the routed path
- [x] Persist machine-readable fallback metadata and use it in downstream replanning/learning surfaces
- [x] Feed enriched routed outcome metadata into world-state summaries and decision-context caution shaping

### Immediate next task

- [~] Push the canonical routed outcome record more directly into downstream world-state facts and broader strategy-adaptation flows; richer routed metadata now reaches the world-state bridge, decision context, and caution-aware heuristic shaping, but broader adaptation flows are still incomplete

### Done when

- [x] Routed actions carry explicit prediction evaluation data
- [x] Overconfidence and underconfidence patterns can be detected from action history
- [x] Decision ranking uses memory, prediction quality, and outcome quality together on the main routed path
- [x] Replanning now reacts to ranking evidence as well as mismatch/performance on the main routed path
- [x] Replanning and learning now react when execution escapes the Golden Path on the main routed path
- [x] Decision context and heuristic shaping now react to recent routed outcome summaries from world-state on the main routed path

---

## Priority 5B — Bounded Exploration and Human-Like Cognitive Loop

**Goal:** Safely expand from capable routed automation toward a reflective, adaptive autonomy loop.

### Human-like autonomy phases

- [x] Phase A — Cognitive continuity
- [x] Phase B — Prediction before action
- [x] Phase C — Reflection and adaptive learning
- [x] Phase D — Bounded testing and exploration
- [x] Phase E — Strategic planning instead of isolated action choice on the main routed short-plan path
- [ ] Phase F — Safe self-improvement

### Near-term execution order

- [x] Make autonomous action selection strongly memory-informed on the main routed path
- [x] Add explicit pre-action prediction records beyond the current lightweight scaffold
- [x] Add expected-vs-actual reflection and mismatch scoring
- [x] Let the decision layer adapt action priority from outcome history
- [x] Introduce bounded exploratory testing for uncertainty reduction
- [x] Upgrade from next-action choice to short plan execution on the main routed path
- [ ] Expand safe self-improvement only after the above loop is stable

### Required work

- [x] Add `exploration` / `experiment` metadata to selected low-risk actions
- [x] Keep experimental actions constrained by trust tiers and truth gates
- [x] Build short multi-step plan tracking tied to routed outcomes
- [x] Support replanning when steps fail or assumptions break
- [ ] Keep self-improvement subordinate to evidence, security, and truth validation

### Done when

- [x] AlleyBot can deliberately test uncertainty with bounded low-risk actions on the main routed path
- [x] Short plans persist across execution steps and update from real outcomes on the main routed path
- [x] The autonomy loop behaves more like one reflective cognitive cycle than disconnected action selection on the main routed path

### Next batched steps

- [x] Persist degraded/recovered action-family state outside immediate active plan summaries
- [x] Add trust buckets for action families such as degraded, cooling_down, recovering, and healthy
- [x] Feed degraded/recovered action-family state into goal selection and longer-horizon planning, not just immediate decision ranking
- [x] Feed trust-aware signals into orchestrator context, strategy evolution recommendations, secure goal generation, and world-state bridge decision context
- [ ] Push plan-state-aware decisioning, mismatch-informed learning, and bounded exploration into remaining unrouted helper/plugin surfaces

---

## Priority 6 — Simplify Control Hierarchy

**Goal:** The project should have clear runtime roles.

### Desired architecture

- [x] `AGIKernel` = state + shared systems + service access
- [x] `AGIOrchestrator` = reasoning + phase composition + plan generation
- [x] `AutonomousBrain` = scheduling + cycle timing + runtime supervision
- [x] `ActionRouter` = execution + validation + learning handoff

### Problems to solve

- [ ] AGI Kernel, AGI Orchestrator, and Autonomous Brain overlap in responsibilities
- [ ] Decision logic is spread across too many layers
- [ ] Hard to know where the final action authority lives
- [ ] Runtime ownership is clearer in docs than in some older helper surfaces

### Required work

- [ ] Remove duplicate decision responsibilities where possible
- [ ] Make the scheduler separate from the planner
- [ ] Make the planner separate from the executor
- [ ] Document the authoritative runtime flow in one architecture doc

### Done when

- [ ] It is obvious which component decides, which executes, and which learns
- [ ] Logs reflect one clean flow instead of multiple overlapping loops

---

## Priority 7 — Safety Tiers for Real Autonomy

**Goal:** Expand autonomy without compromising security.

### Required trust tiers

- [ ] Tier 0: Observe only
- [ ] Tier 1: Safe autonomous actions
- [ ] Tier 2: Constrained system/config actions
- [ ] Tier 3: Code change proposal only
- [ ] Tier 4: Self-modification with strict approval and audit requirements

### High-risk domains requiring special policy

- [ ] Trading and on-chain actions
- [ ] Self-improvement and code mutation
- [ ] External posting at scale
- [ ] Credential and secret handling
- [ ] Autonomous deployment flows

### Required work

- [ ] Add explicit policy classes for risky action categories
- [ ] Require stronger validation thresholds for money/code/external side effects
- [ ] Add audit records for every high-risk action
- [ ] Prevent unsafe autonomy from bypassing owner controls
- [ ] Require prediction, validation, and outcome evidence before allowing high-trust self-improvement actions

### Done when

- [ ] AlleyBot can act more autonomously without expanding attack surface recklessly
- [ ] Risky actions are explainable, gated, and reviewable

---

## Priority 8 — Bring Documentation Back in Sync with Reality

**Goal:** Docs must reflect actual runtime truth.

### Problems to solve

- [ ] Several docs read as if the system is already fully unified
- [ ] Old handoff notes and completed items obscure current priorities
- [ ] Some docs describe aspirational architecture as completed behavior

### Required work

- [ ] Update autonomy-related docs to separate "implemented" from "fully enforced"
- [ ] Mark experimental/in-progress architecture honestly
- [x] Keep one authoritative roadmap for autonomy work
- [ ] Keep one authoritative architecture flow diagram for runtime decision/execution

### Done when

- [ ] A new contributor can understand the real state of the system quickly
- [ ] The roadmap focuses on integration quality, not feature inflation

---

## Systems Already In Scope

These are real assets already present in the project and must be integrated, not replaced.

### Memory and cognition systems

- [x] SQLite memory
- [x] Unified memory
- [x] Episodic memory
- [x] Semantic memory
- [x] Goal memory / goal stack
- [x] World state memory
- [x] Reflection and strategy evolution

### AGI and reasoning systems

- [x] AGI Kernel
- [x] AGI Orchestrator
- [x] Planning system
- [x] Causal engine
- [x] Research engine
- [x] Creative engine
- [x] Social intelligence
- [x] Metacognition
- [x] LLM decision routing

### Validation and alignment systems

- [x] SyMod systems
- [x] Synergy decision engine
- [x] Security filter
- [x] Owner-gated Telegram control

### Platform and execution systems

- [x] Moltx
- [ ] Moltbook runtime dependency fully removed from all non-historical surfaces
- [x] Moltchan
- [x] Moltroad
- [x] Clawbr
- [x] Telegram
- [x] On-chain / Base integration
- [x] A2A / agent-facing integrations

### Self-improvement systems

- [x] Goal-to-skill pipeline
- [x] Autonomous coder
- [x] Testing pipeline
- [x] Deployment pipeline
- [x] Skill loading and marketplace support

---

## Immediate Next Steps

### Sprint 1 — Execution and validation truth

- [x] Audit the main autonomous execution paths
- [x] Route the main autonomous proposal and goal paths through `ActionRouter`
- [x] Standardize the main SyMod validator contract in the router
- [x] Define and start using a canonical action schema for the routed path

### Sprint 2 — Goal and plan actuation

- [x] Rewrite the main goal-to-action mapping using canonical action specs
- [x] Add first-pass plugin adapters for mismatched interfaces
- [x] Tie routed goal completion to real execution outcomes

### Sprint 3 — Memory and learning closure

- [x] Standardize outcome record format
- [ ] Feed outcomes into all memory/learning systems consistently
- [ ] Measure post-action adaptation quality

### Sprint 4 — Safety and documentation

- [ ] Add autonomy trust tiers
- [ ] Harden self-improvement boundaries
- [ ] Update docs to reflect enforced runtime behavior

### Sprint 5 — Cognitive continuity and reflection quality

- [ ] Expose candidate performance summaries to AI decision prompts
- [ ] Add routed expected-vs-actual mismatch scoring
- [ ] Persist mismatch metadata through learning surfaces

### Sprint 6 — Exploration and short-plan autonomy

- [ ] Add bounded exploration metadata for low-risk actions
- [ ] Track short multi-step plans against routed outcomes
- [ ] Support replanning from failed or misleading steps

---

## Definition of True Full Autonomy for AlleyBot

AlleyBot is truly fully autonomous when all of the following are true:

- [ ] It perceives the environment through world state + memory continuously
- [ ] It generates and prioritizes its own goals reliably
- [ ] It plans using one coherent reasoning pipeline
- [ ] It executes through one unified router
- [ ] It validates every meaningful action through one layered trust model
- [ ] It records every outcome in one consistent learning format
- [ ] It adapts future behavior from that learning
- [ ] It predicts likely outcomes before acting
- [ ] It reflects on expected vs actual results after acting
- [ ] It can run bounded experiments to reduce uncertainty safely
- [ ] It can improve itself safely without weakening security

Until then, the work is integration, enforcement, and hardening.

---

## Operating Principle

Do not chase feature count.

Chase:

- [ ] coherence
- [ ] reliability
- [ ] safety
- [ ] learning quality
- [ ] truthful architecture

AlleyBot already has many minds worth of components.
The next step is making them behave like **one real autonomous mind**.
