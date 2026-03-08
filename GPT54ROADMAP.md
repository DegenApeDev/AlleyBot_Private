
# GPT54 Roadmap — Toward True Full Autonomy for AlleyBot

---

## Purpose

This roadmap translates AlleyBot's current architecture into a practical execution plan for achieving **true full autonomy**.

The project already contains most of the major subsystems required for AGI-like behavior:

- AGI Kernel
- AGI Orchestrator
- Autonomous Brain
- unified, episodic, semantic, and SQLite-backed memory
- world state ingestion and inference
- goal generation and goal stack tracking
- planning, causal reasoning, research, creativity, social intelligence, and metacognition
- SyMod validation
- Synergy / harmonic field validation
- self-improvement and skill generation systems
- multi-platform execution systems

The missing piece is not raw capability.
The missing piece is **coherence**.

The next chapter of AlleyBot is about making all of these systems operate as **one real autonomous mind**.

---

## Executive Summary

### Current state

AlleyBot is already:

- capable of autonomous reasoning
- capable of generating goals
- capable of planning
- capable of taking actions on multiple platforms
- capable of learning from some outcomes
- capable of validating actions through multiple trust models

But AlleyBot is **not yet fully unified at runtime**.

### Core problem

Different parts of the system still:

- decide independently
- validate differently
- execute through different paths
- write outcomes back inconsistently

That means the system behaves like a collection of advanced autonomy components rather than a single fully integrated autonomous runtime.

### Core objective

Build a runtime where:

- one system decides
- one system executes
- one validation ladder governs action approval
- one memory feedback loop records outcomes
- one architecture document matches reality

---

## Definition of True Full Autonomy

AlleyBot should be considered truly fully autonomous only when all of the following are true:

1. It perceives the environment continuously through world state and memory.
2. It generates, prioritizes, and revises its own goals.
3. It converts goals and plans into executable actions reliably.
4. Every autonomous action runs through one authoritative execution path.
5. Every meaningful action runs through one layered validation model.
6. Every outcome is recorded in one structured learning format.
7. Future behavior changes based on those recorded outcomes.
8. Self-improvement remains security-bounded and policy-aware.

---

## Guiding Principles

### 1. One Brain

AlleyBot is one unified AGI agent, not a swarm.

### 2. Integration Over Inflation

Do not prioritize adding more systems before the existing ones are unified.

### 3. Security First

Autonomy must increase without increasing unsafe execution paths.

### 4. Truthful Architecture

Documentation must reflect what is actually enforced at runtime.

### 5. Closed-Loop Learning

An action is incomplete until its outcome changes future behavior.

---

## Runtime Dependency Order

The phases are not equally foundational.

They stack in this dependency order:

1. execution truth
2. validation truth
3. canonical action language
4. goal actuation
5. learning closure
6. control hierarchy clarity
7. safety tier enforcement
8. documentation truth

This means later phases should not be treated as fully complete while earlier phases are still materially fragmented.

---

## Phase 1 — Unify Autonomous Execution

### Goal

Make `ActionRouter` the single authoritative execution path for all autonomous actions.

### Why this phase matters

This is the highest-leverage change in the entire project.
Without unified execution, autonomy remains fragmented and hard to trust.

### Current issues

- `AutonomousBrain` no longer performs direct proposal execution on the main routed path.
- `AGIOrchestrator` is now routed for its main plan execution path, but not every higher-level caller has been normalized yet.
- Plugin execution still varies between direct method calls, command calls, and custom helpers, especially in synchronous helper layers.
- The main execution path now emits a shared outcome/telemetry artifact through `ActionRouter`, but not all callers use it yet.

### Deliverables

- Refactor all autonomous execution to flow through `AGIKernel.act()`.
- Make `ActionRouter.route_action()` the primary autonomous executor.
- Remove or deprecate direct execution paths in `AutonomousBrain`.
- Normalize plugin invocation behind a single execution contract.
- Ensure high-impact actions always emit consistent execution metadata.

### Progress so far

- `AutonomousBrain._execute_proposal()` now routes through `AGIKernel.act()`.
- Legacy direct execution helpers were removed from `AutonomousBrain`.
- `AGIKernel.run_autonomous_goal_cycle()` now routes canonical goal actions through `act()`.
- `ActionRouter` is now the active execution path for the main autonomous proposal and goal flows.
- `AGIOrchestrator._execute_plan()` now emits canonical action specs and routes execution through `AGIKernel.act()`.
- `MultiPlatformEngine.execute_campaign()` is now async-native and routes supported campaign posts (`moltx`, `clawbr`) through the kernel/router path.
- Telegram `/multi_platform` now awaits the async orchestrator multi-platform path.
- Telegram `/post` now emits a canonical routed Moltx action through `AGIKernel.act()` when the kernel is available.
- `DecisionEngineMixin` now has an async-native execution path and can route targeted high-level brain actions (`moltx_post`, `moltx_engage`, `clawbr_post`, `clawbr_engage`, `clawbr_debate_turn`, `clawbr_create_debate`, `analyze_trending`) through `AGIKernel.act()` when supported.
- The legacy `BrainPlugin.think()` fallback now executes through the async-native decision-engine path in its normal synchronous environment.
- Golden Window queued brain actions now execute through the async-native decision-engine path.
- Supported chain and dynamic-chain steps now reuse the async routed step pathway for safe actions such as `moltx_engage`, `clawbr_engage`, and `onchain_wallet`.
- Additional low-risk helper/status actions now route through canonical specs on the decision-engine path, including `moltbit_status`, `moltbit_post`, `onchain_heartbeat`, `check_engagement`, `analyze_trending`, and `check_comments` via a public MoltX wrapper.
- `update_skills` now routes through `ActionRouter` with strict risk/trust metadata so self-improvement skill updates use the fail-closed validation path.
- `moltx_image_post` now prepares content/media through the decision-engine helper seam and routes final execution through `ActionRouter` via a public MoltX wrapper.
- Chain-composed final posts for `moltx` and `moltbit` now prefer routed execution through `AGIKernel.act()` / `ActionRouter`, while LLM composition remains local to the decision-engine helper.
- Chain-created `clawbr_create_debate` now prefers routed final execution through `AGIKernel.act()` / `ActionRouter`, while topic generation, duplicate checks, and opening preparation remain local to the helper.
- Decision-engine execution results now emit machine-readable fallback metadata (`dispatch_path`, `legacy_fallback_used`, `fallback_details`) so leaving the Golden Path is explicit and inspectable.
- Recent MoltX runtime hardening normalized trending payload parsing, quieted premature low-data correlation warnings, and made `moltx_engage` degrade to like-first mode until the platform's 5:1 engagement buffer is satisfied.
- Telegram has been pushed further toward a reporting/reward surface: goal completions now emit accomplishment updates, periodic autonomous digests can be sent with cooldown protection, and safe goal progress/cooling state changes now report informationally instead of treating Telegram as a blocking execution surface.
- A conservative fail-closed low-risk autonomy loop now exists on the `src/agentic/goal_manager.py` path: eligible analysis/optimization goals can auto-approve, auto-start when idle, be picked up again during runtime cycles, and be reported to the owner without manual `/goals_start` intervention.
- `AutonomousBrain` now reuses the current safe-goal manager path during `_execute_cycle()` to pick up the next safe approved goal when idle, and proposal selection now lightly biases toward the current active safe goal without bypassing confidence thresholds or routed validation.
- Goal-tagged safe-goal proposals now feed success/failure outcomes back into the `goal_manager.py` loop so repeated aligned wins can complete a goal and repeated misses can cool/fail it conservatively.
- The conservative autonomy loop now includes a narrow low-impact `fix` slice for operational `error_pattern` goals, but it still fails closed on code mutation, skill/plugin creation, posting, trading, wallets, deployment, and other stateful or externally impactful work.
- The conservative autonomy loop now records soft `BLOCKED` resistance markers, allows later aligned successes to recover some of that pressure, and temporarily backs off recently blocked goals so Alley does not keep immediately re-picking the same resisted work.
- `ActionRouter` now normalizes AGI, Synergy, and SyMod validator outputs into one fail-closed routed schema and emits a shared `validation_trace` on success/failure paths.
- Canonical routed `outcome_record`s now persist that shared `validation_trace`, so logging, reflection, and learning surfaces can inspect one authoritative validation history.
- `AutonomousBrain` proposal ranking now uses recent routed outcome history, predicted value heuristics, and lightweight recall signals from episodic/unified memory instead of relying only on static coarse heuristics.
- Proposal-side ranking evidence now flows through the Golden Path: routed action context carries `ranking_evidence`, canonical outcome records persist it, kernel learning summarizes it, strategy evolution records it, and replanning can now react to negative recall, cooled ranking signals, and high-predicted-value recovery cases.
- Fallback-aware execution metadata now also flows into downstream behavior: replanning reacts when an action escaped the Golden Path, kernel learning stores dispatch-alignment summaries, and strategy evolution persists dispatch-learning context for later adaptation.

### Target files

- `src/agentic/action_router.py`
- `src/agentic/autonomous_brain.py`
- `src/agentic/agi_orchestrator.py`
- `src/agentic/agi_kernel.py`

### Success criteria

- No autonomous or high-level command-driven action bypasses the router.
- Logs show one consistent action lifecycle.
- Goal progress, reflection, and memory writes happen after every action through one path.

### Current status

- **Advanced:** main autonomous proposal execution
- **Advanced:** main goal-driven execution path
- **Advanced:** main orchestrator execution path
- **Advanced:** multi-platform campaign execution path for supported routed platforms
- **Advanced:** Telegram `/multi_platform` and `/post` command surfaces
- **Advanced:** legacy brain fallback and Golden Window queued execution path for the currently supported routed brain actions
- **Advanced:** `DecisionEngineMixin` legacy direct-dispatch has been reduced for already-supported routed brain actions
- **Advanced:** chain and dynamic-chain execution now reuse routed step execution for a conservative supported subset
- **Advanced:** `update_skills` now routes through the shared executor with strict validation metadata intended to fail closed
- **Advanced:** `check_comments` now routes through a public MoltX command wrapper instead of a private helper bypass
- **Advanced:** `moltx_image_post` now routes through the shared executor after preparation behind a dedicated helper seam and public MoltX command wrapper
- **Advanced:** additional decision-engine helper/status actions now route through the Golden Path, including `analyze_trending`, `check_engagement`, `moltbit_status`, and `moltbit_post`
- **Advanced:** chain-composed `moltx` / `moltbit` final posts and chain-created `clawbr` debates now prefer Golden Path final execution while keeping specialized preparation local
- **Advanced:** decision-engine execution now exposes machine-readable fallback metadata, and fallback events now influence replanning plus downstream learning summaries
- **Advanced:** recent MoltX hardening reduced runtime noise and made engagement behavior fail closed while platform readiness is still below the 5:1 threshold
- **Advanced:** Telegram is now being repositioned as a human-facing reporting/reward channel for recent autonomous work instead of a default execution bottleneck
- **Advanced:** a conservative low-risk goal autonomy loop now exists for safe analysis/optimization goals plus a narrow low-impact operational fix slice, including auto-approval, auto-start, runtime pickup, active-goal pursuit bias, accomplishment digests, and progress/failure reporting
- **Advanced:** the conservative safe-goal loop now includes soft blocked-state handling and temporary runtime backoff so resisted goals cool off instead of being hammered every cycle
- **Advanced:** routed validation now emits one normalized validation trace, and canonical routed outcomes now persist that trace for downstream inspection and learning
- **Advanced:** the main autonomous path now has memory-shaped ranking, persisted ranking evidence, first-pass learning use of that evidence, and ranking-aware replanning
- **Remaining:** broader helper/plugin dispatch surfaces, custom chain-only logic, unsupported decision-engine action types, and deeper validation-policy normalization still outside the router or not yet fully unified

---

## Phase 2 — Unify Validation

### Goal

Create one layered validation ladder for all autonomous action approval.

### Why this phase matters

Right now the system has powerful validators, but they are not consistently sequenced or enforced.
That weakens trust in autonomy.

### Validation ladder to enforce

1. Strategic relevance validation
2. Synergy field / harmonic timing validation
3. SyMod truth and mathematical integrity validation
4. Security and policy validation
5. Execution readiness validation

### Current issues

- Synergy and SyMod are now both present in the routed validation ladder, but not all callers use the routed path yet.
- SyMod return types are normalized in `ActionRouter`, but validator contracts are not yet fully standardized project-wide.
- Some validation is soft, some is hard, and the policy is not centralized.
- High-risk actions need stronger standards than regular engagement actions.

### Deliverables

- Standardize validator outputs to a shared dict schema.
- Build a central validation orchestrator inside or adjacent to `ActionRouter`.
- Define action classes by trust/risk level.
- Require stricter validation for:
  - self-improvement
  - code mutation
  - on-chain actions
  - trading
  - large-scale posting
- Add human-readable validation traces for debugging and Telegram inspection.

### Progress so far

- `ActionRouter` now applies AGI validation, Synergy validation, and SyMod verification in sequence for routed autonomous actions.
- `DecisionSystem` now uses recent action performance summaries in heuristic ranking.
- Routed actions now carry lightweight pre-action `prediction` scaffolding.
- `ActionRouter` now computes explicit prediction-evaluation metadata including mismatch score, calibration, value alignment, and risk alignment.
- `DecisionSystem` now builds a richer memory-informed decision context including recent action history, plan summaries, and performance-aware candidate formatting for both heuristic and AI-backed selection.
- `DecisionSystem` now supports bounded low-risk exploration metadata for low-evidence actions.
- Short routed plans can now persist across steps through `PlanManager`, including active-step tracking and outcome-driven status updates.
- Routed plan failures/high-mismatch outcomes now trigger revised-plan generation with structured reflection signals.
- Revised plans now use recent per-action performance history in addition to single-step reflection signals.
- Repeated failed replans now escalate into safer alternate plans or bounded abandonment instead of retry loops.
- Escalated plans now expose degraded action-family cooldown and recovery signals that feed back into decision selection.
- `ActionRouter` now normalizes routed AGI, Synergy, and SyMod results into one fail-closed validation schema.
- Routed action success/failure paths now emit a shared `validation_trace`, and canonical `outcome_record`s persist it for logging and reflection.
- Replanning can now use routed `ranking_evidence` in addition to mismatch, calibration, risk, and recent action performance.
- Replanning can now also react when prior execution escaped the Golden Path via legacy fallback, instead of blindly retrying the same path.

### Target files

- `src/agentic/action_router.py`
- `src/agentic/decision_system.py`
- `src/agentic/synergy_decision_engine.py`
- `lib/synergy_gate.py`
- `synergy/synergy_logic.py`

### Success criteria

- Every autonomous action has a complete validation trace.
- The same action always passes/fails under the same conditions.
- Documentation and runtime behavior match.

### Current status

- **Advanced:** centralized router validation for the main routed path
- **Advanced:** explicit prediction-evaluation and mismatch scoring on routed outcomes
- **Advanced:** performance-informed and plan-state-informed decision ranking for the routed path
- **Advanced:** bounded exploration metadata and short-plan replanning loop for the routed path
- **Remaining:** formal security/policy tiers and full validator contract normalization

---

## Phase 3 — Canonical Action Model

### Goal

Give all planning, goal, reasoning, and execution systems one shared action language.

### Why this phase matters

Today the system can think at a higher level than it can act consistently.
That gap must be closed.

### Current issues

- Some goal-driven and command-driven actions now map through canonical adapters, but broader plugin coverage is still needed.
- Main orchestrator outputs now compile into routed execution contracts, but not all helper layers do.
- Plugins expose mixed interfaces.

### Deliverables

- Define a canonical action spec.
- Required fields:
  - `plugin`
  - `action_type`
  - `params`
  - `context`
  - `impact`
  - `goal_id`
  - `trigger`
  - `validation_class`
- Create an action registry that maps AGI intent to executable actions.
- Add adapters for plugins that do not support the canonical contract yet.
- Normalize command-driven and method-driven plugins behind one interface.

### Progress so far

- `goal_driven_cycle.py` now emits canonical action specs for the routed path.
- `autonomous_goals.py` now emits canonical action specs for common legacy goal cases.
- `ActionRouter` now handles canonical action sources from `autonomous_brain_proposal`, `goal_driven_cycle`, and `goal_manager`.
- First-pass canonical adapters now exist for the current main goal actions.
- `AGIOrchestrator` now compiles its main execution output into canonical action specs.
- `MultiPlatformEngine` now compiles supported campaign content pieces into canonical action specs for routed execution.
- Telegram `/post` now emits a canonical action spec before execution.
- The async-native decision-engine path now compiles targeted legacy brain actions, including `moltx_engage`, into canonical action specs before execution.

### Target files

- `src/agentic/action_router.py`
- `src/agentic/goal_driven_cycle.py`
- `src/agentic/decision_system.py`
- `src/agentic/agi_orchestrator.py`
- platform plugins as needed

### Success criteria

- Goals emit executable actions without special glue.
- Main plans compile directly into actions.
- Command-driven and helper-driven post surfaces compile directly into actions.
- Plugin capabilities are routable through one schema.

### Current status

- **Advanced:** main goal systems now emit executable routed actions
- **Advanced:** targeted legacy brain actions now compile into routed execution specs
- **Advanced:** supported brain chain-step actions now partially reuse canonical routed execution
- **Advanced:** selected low-risk helper/status actions now compile into canonical routed execution specs
- **Advanced:** comment-monitor/reply checks now have a stable public plugin wrapper for routed execution
- **Advanced:** routed action coverage now includes a stricter stateful self-improvement update flow via explicit risk/trust metadata
- **Remaining:** broader action registry coverage and normalization across remaining helper/plugin interfaces

---

## Phase 4 — Strengthen Goal-Driven Autonomy

### Goal

Ensure AlleyBot consistently pursues real goals instead of only performing opportunistic actions.

### Why this phase matters

A fully autonomous agent needs persistent intention, not just activity.

### Current issues

- Goal mapping is now partially canonicalized for the main routed goal paths.
- Goal completion for routed actions is now tied to the canonical outcome record, but broader goal logic is still simplistic.
- Opportunity detection and execution feedback are not fully connected.

### Deliverables

- Audit all goal types against real executable action mappings.
- Make `goal_stack` a primary driver of autonomous intent.
- Tie execution outcomes back to goal advancement.
- Add blocked-goal handling:
  - retry
  - alternate strategy
  - defer
  - abandon with learning
- Distinguish recurring maintenance goals from strategic long-horizon goals.

### Progress so far

- Main routed goal execution now updates goal state through the kernel learning path.
- Goal-driven and legacy goal-manager paths both now produce router-friendly action specs for the main cases.

### Target files

- `src/agentic/goal_driven_cycle.py`
- `src/agentic/goal_stack.py`
- `src/agentic/goal_generator.py`
- `src/agentic/agi_orchestrator.py`

### Success criteria

- Goals regularly become real actions.
- Goal state changes reflect actual outcomes.
- Repeated failure leads to strategic adaptation.

### Current status

- **Advanced:** routed goal execution and goal-state updates
- **Remaining:** retries, abandonment logic, and strategic multi-goal autonomy

---

## Phase 5 — Close the Learning Loop

### Goal

Make every action a structured learning event.

### Why this phase matters

Without consistent outcome recording, AlleyBot is active but not truly improving.

### Current issues

- The main routed path now has a canonical outcome record, but not every action path writes it yet.
- Reflection and memory writes on the routed path now use structured data, but downstream consumers are not fully migrated.
- Strategy evolution and world-state learning are not yet fully consuming the canonical record.

### Deliverables

- Define one canonical outcome record format.
- Record for every action:
  - action id
  - goal id
  - trigger
  - validation trace
  - execution result
  - success/failure
  - engagement/performance metrics
  - reflection summary
  - policy/safety notes
- Feed the same outcome into:
  - episodic memory
  - unified memory
  - world state
  - strategy evolution
  - goal progress tracking
- Ensure future decisions can query these results easily.

### Progress so far

- `ActionRouter` now builds a canonical `outcome_record` for routed autonomous actions.
- Routed `outcome_record`s now feed:
  - execution history
  - `AGIKernel.learn()`
  - goal progress updates
  - shared `ActionLogger` persistence
  - unified memory metadata
- The duplicate goal-completion path in the router was removed so the kernel owns goal advancement from the structured record.

### Target files

- `src/agentic/action_router.py`
- `src/agentic/action_logger.py`
- `src/agentic/strategy_evolver.py`
- `src/agentic/agi_kernel.py`
- memory-related modules

### Success criteria

- One canonical outcome record exists for each action.
- Reflection consumes that same record.
- Strategy evolution uses real outcome data.
- Behavior changes are observable over time.

### Current status

- **Advanced:** canonical outcome record for the main routed path
- **Advanced:** shared `ActionLogger` now ingests canonical routed records
- **Advanced:** explicit prediction-evaluation and mismatch scoring on routed outcomes
- **Advanced:** performance-informed and plan-state-informed decision ranking for the routed path
- **Advanced:** bounded exploration metadata and short-plan replanning loop for the routed path
- **Advanced:** dedicated persistent action-family trust memory with degraded, cooling_down, recovering, and healthy trust buckets
- **Advanced:** router-first trust refresh from routed outcomes and mismatch evidence
- **Advanced:** trust-aware goal selection, longer-horizon goal prioritization, secure goal generation, strategy recommendations, and orchestrator context
- **Advanced:** world-state decision context now exposes persisted action-family trust state
- **Remaining:** broader world-state/strategy consumption of the canonical record across all autonomy surfaces and stronger cross-cycle adaptation from prediction quality

---

## Addendum — Reflective Short-Plan Autonomy Progress

### What is now implemented on top of the routed path

- plan-state-aware decision context in `DecisionSystem`
- resume-first AGI cycle prioritization for active and revised plans
- generalized resumed step execution beyond simple content posting
- structured replanning from routed failure and mismatch signals
- performance-informed revised-plan generation using recent action-family history
- bounded escalation and abandonment for repeated failed replans
- degraded action-family cooldown, decay, and recovery-aware avoidance in decision selection
- persistent action-family trust state stored outside immediate plan summaries
- trust buckets carried into goal selection, longer-horizon goal prioritization, secure goal generation, strategy evolution recommendations, orchestrator context, and world-state bridge context

### What still remains to reach a stronger autonomy loop

- feed the canonical routed outcome record even more consistently into downstream world-state facts and strategy adaptation flows beyond current bridge/context exposure
- expand canonical routed action coverage for remaining helper/plugin surfaces so more plan steps can be resumed generically

### Current interpretation

AlleyBot has moved from isolated next-action choice toward a reflective short-plan loop on the main routed path, but longer-horizon strategic memory and broader routed surface coverage are still needed before this can be considered fully mature autonomy.

---

## Phase 6 — Simplify the Control Hierarchy

### Goal

Clarify the runtime roles of the AGI Kernel, AGI Orchestrator, Autonomous Brain, and Action Router.

### Why this phase matters

Too much overlap creates ambiguity, duplication, and drift.

### Desired runtime split

- `AGIKernel` = state, services, memory, shared infrastructure
- `AGIOrchestrator` = reasoning, phase composition, planning
- `AutonomousBrain` = scheduling, cadence, runtime supervision
- `ActionRouter` = execution, validation, outcome capture

### Deliverables

- Reduce duplicate decision responsibilities.
- Separate scheduler logic from planning logic.
- Separate planning logic from execution logic.
- Publish one authoritative runtime flow diagram.

### Success criteria

- It is obvious where decisions originate.
- It is obvious where execution is enforced.
- Runtime logs reflect one clean hierarchy.

---

## Phase 7 — Safety Tiers for Real Autonomy

### Goal

Expand autonomous capability while preserving strict safety boundaries.

### Why this phase matters

A more capable autonomous system without stronger trust-tiering becomes less safe, not more useful.

### Required trust tiers

- Tier 0 — Observe only
- Tier 1 — Safe autonomous actions
- Tier 2 — Constrained system/config actions
- Tier 3 — Code change proposals only
- Tier 4 — Self-modification with explicit high-trust gating

### High-risk domains

- trading
- on-chain actions
- self-improvement
- code deployment
- secret handling
- external posting with broad impact

### Deliverables

- Define action risk classes.
- Enforce stronger thresholds for dangerous domains.
- Add audit trails for all high-risk actions.
- Ensure owner-gated control remains intact for sensitive operations.

### Success criteria

- Risky actions are explainable, gated, and reviewable.
- Safe autonomy expands without weakening security.

---

## Phase 8 — Documentation and Architecture Truth

### Goal

Make the docs reflect actual enforced behavior rather than aspirational behavior.

### Why this phase matters

Strong systems become weak when contributors cannot tell what is real, experimental, or only partially wired.

### Deliverables

- Update autonomy docs to separate:
  - implemented
  - integrated
  - enforced
  - experimental
- Keep one authoritative roadmap.
- Keep one authoritative runtime architecture document.
- Remove stale handoff-heavy roadmaps from being the primary planning source.

### Success criteria

- A new contributor can quickly understand the real current architecture.
- The docs reduce confusion rather than adding it.

---

## Existing Systems That Must Be Preserved and Integrated

### Memory and learning

- SQLite memory
- Unified memory
- Episodic memory
- Semantic memory
- Goal stack and goal memory
- World state memory
- Reflection and strategy evolution

### AGI cognition

- AGI Kernel
- AGI Orchestrator
- Planning system
- Causal engine
- Research engine
- Creative engine
- Social intelligence
- Metacognition
- LLM decision routing

### Validation and alignment

- SyMod systems
- Synergy decision engine
- Security filter
- Owner-gated Telegram controls

### Execution surface

- Moltx
- Moltchan
- Moltroad
- Clawbr
- Telegram
- Base / on-chain integrations
- A2A / interoperability systems

### Self-extension

- goal-to-skill pipeline
- autonomous coder
- test pipeline
- deployment pipeline
- skill registry / marketplace support

---

## Four-Sprint Immediate Plan

### Sprint 1 — Execution and validation truth

- Audit all autonomous execution paths
- Route all autonomous actions through `ActionRouter`
- Standardize validator return contracts
- Define canonical action schema

Status:

- execution-path audit completed for core runtime flows
- `ActionRouter` canonical source handling expanded for additional high-level routed callers
- remaining work is broader canonical action coverage across older helper/plugin surfaces

### Sprint 2 — Goal and plan actuation

- Rewrite goal-to-action mapping against real plugin capabilities
- Add plugin adapters for interface mismatches
- Tie goal completion to actual execution outcomes

Status:

- router-native adapters are in place for key routed actions
- high-impact routed actions now fail closed on Synergy unavailability or validator exceptions
- high-impact routed actions now fail closed on SyMod unavailability, malformed results, or validator exceptions
- remaining work is broader trust-tier normalization beyond the current high-impact rule

### Sprint 3 — Learning closure

- Standardize outcome record format
- Feed outcomes into memory and strategy systems consistently
- Validate that learning changes future decisions

Current focus next:

- routed actions now learn through a cleaner canonical `outcome_record` path with duplicate writes reduced in the router and decision system
- expand canonical action coverage for additional routed helpers
- verify all routed outcomes feed the same memory and strategy surfaces consistently
- continue removing remaining places where direct plugin execution can bypass the preferred routed path, especially custom helper and chain-only surfaces

### Sprint 4 — Safety and documentation

- Implement autonomy trust tiers
- Harden self-improvement boundaries
- Update docs to reflect real enforced runtime behavior

Status:

- `ActionRouter` now normalizes `risk_level` and `trust_level` in addition to `impact` when deciding whether strict validation is required
- strict Synergy/SyMod enforcement now applies to high-risk, critical-risk, low-trust, and untrusted routed actions
- `console_monitor` public responses now prefer the routed AGI execution path when a safe synchronous bridge is available, with direct execution fallback preserved
- remaining work is broader adoption of explicit trust metadata across callers and finishing legacy bypass cleanup

---

## Current Priority Order

If work must be chosen selectively, prioritize in this order:

1. eliminate remaining execution-path fragmentation
2. normalize validation contracts and risk tiers
3. complete canonical action coverage for remaining helper/plugin surfaces
4. close the outcome-to-learning loop for all routed actions
5. simplify hierarchy and publish architecture truth

This is the order most likely to increase autonomy without increasing confusion or risk.

---

## Roadmap Completion Standard

This roadmap should be considered complete only when all of the following are true:

- `ActionRouter` is the enforced execution path for all meaningful autonomous actions
- canonical action specs are the default language between planning and execution
- validation traces are consistent and inspectable across routed actions
- goal progress updates come from real execution outcomes rather than assumed intent
- structured outcome records feed memory, reflection, and future strategy selection
- runtime ownership between kernel, orchestrator, brain, and router is unambiguous
- trust tiers are enforced for high-risk actions
- the primary architecture docs match actual runtime behavior

Until then, AlleyBot may be highly capable, but it is still partially unified rather than fully autonomous in the strict sense used by this roadmap.

---

## Human-Like AGI Autonomy Plan

Target:

AlleyBot should evolve into a single unified AGI that:

- understands current reality from memory, world state, and live context
- plans intentionally instead of only selecting the next isolated action
- predicts likely outcomes before acting
- reflects on expected vs actual results after acting
- tests uncertain assumptions through bounded experiments
- remembers what mattered in ways that change future choices
- improves itself safely over time
- stays truth-aligned through Synergy and SyMod validation
- serves the better good of its human rather than chasing shallow activity

The target loop is:

- perceive
- interpret
- predict
- plan
- validate
- act
- reflect
- learn
- adapt

### Phase A — Cognitive continuity

- unify the active autonomy loop around one durable cognitive state per cycle
- ensure relevant episodic, strategic, and world-state memory is recalled before action selection
- make current goals, recent failures, recent successes, and active constraints visible to the same decision surface
- reduce fragmented reasoning paths where one subsystem acts without the others' state

Definition of done:

- autonomous action selection sees goal state, recent outcome history, and recalled memory in one coherent context object
- memory recall changes autonomous action selection in observable ways
- the same routed action outcome updates the next decision context without duplicate or silent bypasses

### Phase B — Prediction before action

- add explicit pre-action prediction records for meaningful autonomous actions
- estimate expected outcome, expected value, expected risk, and confidence before execution
- compare candidate actions not only by availability but by predicted utility grounded in prior outcomes
- make low-confidence actions easier to defer, downgrade, or test in safer form

Definition of done:

- routed autonomous actions can carry an expected outcome record
- action choice prefers strategies with better predicted value from memory and history
- prediction quality can be compared against actual outcomes over time

### Phase C — Reflection and adaptive learning

- formalize expected-vs-actual comparison after execution
- detect when the model was wrong, not just whether the action succeeded
- store reflection artifacts that update future strategy selection
- separate short-term action success from deeper strategic truth

Definition of done:

- autonomous outcomes record expectation mismatch, not only success/failure
- repeated failure patterns reduce future action priority automatically
- repeated successful patterns increase confidence only when validated by real outcomes

### Phase D — Bounded testing and exploration

- give AlleyBot a safe way to test uncertain hypotheses with low-risk actions
- distinguish exploitation from exploration in the decision layer
- use trust tiers and Synergy/SyMod constraints to keep experiments bounded
- prefer reversible tests when uncertainty is high

Definition of done:

- the autonomy loop can choose exploratory actions deliberately
- exploratory actions are explicitly marked and reviewed through stricter bounded rules
- uncertainty can decrease over time because the system runs tests rather than guessing repeatedly

### Phase E — Strategic planning instead of isolated action choice

- shift from single next-action choice toward short multi-step plans
- support plan generation, plan execution, mid-course correction, and abandonment
- tie plan success to actual routed outcomes instead of optimistic intent
- preserve one-agent coherence: one planner, one memory, one identity, one routed execution layer

Definition of done:

- AlleyBot can create and track short multi-step plans for meaningful goals
- execution outcomes update plan state directly
- failed steps can trigger replanning instead of blind continuation

### Phase F — Safe self-improvement

- let AlleyBot improve prompts, heuristics, internal policies, and tools through bounded self-modification
- route self-improvement proposals through strict validation, trust tiers, and security review surfaces
- require truth-linked evidence for keeping a self-improvement change
- reject self-modification that increases capability claims without outcome evidence

Definition of done:

- self-improvement attempts produce measurable before/after evidence
- only validated changes persist
- self-improvement remains subordinate to security and truth constraints

## Near-Term Execution Order For This Goal

If the immediate objective is to move toward human-like autonomy, prioritize in this order:

1. make autonomous action selection strongly memory-informed
2. add explicit pre-action prediction records
3. add expected-vs-actual reflection and mismatch scoring
4. let the decision layer adapt action priority from outcome history
5. introduce bounded exploratory testing for uncertainty reduction
6. upgrade from next-action choice to short plan execution
7. expand safe self-improvement only after the above loop is stable

## Immediate Next Implementation Target

The highest-leverage next step is:

- continue shrinking the remaining legacy execution bypasses in `plugins/brain/decision_engine.py` and related custom chain-only helpers so more autonomous actions use the same routed validation, outcome, and learning path

The recent batches already established first-pass memory-shaped ranking, persisted ranking evidence, learning use of that evidence, and ranking-aware replanning. The next shortest path is to apply that same Golden Path more broadly.

---

## Final Standard

We are not trying to build a bot that simply has many components.
We are building a system where all of those components act as **one secure, coherent, adaptive, autonomous intelligence**.

That means the work ahead is:

- integration
- enforcement
- simplification
- hardening
- learning quality

Not feature inflation.

---

## Working Rule

When choosing what to do next, prefer work that improves:

- coherence
- reliability
- safety
- execution truth
- learning quality
- architectural honesty

Over work that merely increases feature count.
