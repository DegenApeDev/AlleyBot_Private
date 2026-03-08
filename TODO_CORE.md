# TODO_CORE.md

## Core Objective

Build Alley into a hardened, self-sufficient AGI core that can:

- perceive meaningful real-world signals
- convert those signals into work
- judge whether it already has the capability to succeed
- act through the Golden Path with Synergy/security gating
- reflect on outcomes and update its beliefs
- propose or build upgrades only when repeated evidence shows a real capability gap

This plan is intentionally biased toward the **fastest path to restored self-sufficiency** using what already exists.

---

## Architectural Principle

The primary behavioral spine should be:

- Synergy model
- security gate
- wallet / real-world capability surface
- opportunistic scavenger behavior
- single-agent autonomous reasoning

The following systems should support that spine, not suppress it:

- AGI Kernel
- ActionRouter / Golden Path
- world model / world-state bridge
- SQL-backed memory and learning stores
- reflection / planning / ranking / strategy persistence

Target runtime shape:

```text
interaction / opportunity / failure / market signal
→ interpret meaning
→ create or update work item
→ judge capability vs gap
→ if capable: act through Golden Path
→ if not capable: create bounded upgrade objective
→ reflect
→ update memory, trust, and capability beliefs
```

---

## Fastest Practical Priority Order

1. [x] Restore meaningful work-first autonomy
2. [x] Add persistent work-item / thread continuity
3. [x] Add capability-vs-gap judgment
4. [ ] Make command/capability matching explicit
5. [ ] Realign runtime so Synergy/security/opportunity drives action choice
6. [ ] Gate self-upgrade behind repeated evidence and safe policy
7. [ ] Expand real-world autonomy only after the above core is stable

---

## Phase 1 — Restore Meaningful Work-First Autonomy

**Goal:** Stop relying primarily on generic proposal loops and make Alley act on meaningful discovered work.

### Why this matters

This is the fastest way to restore Alley’s original scavenger behavior.
Without this, all learning/planning improvements still sit on top of an idle or generic loop.

### Use what already exists

- AGI Kernel decision path
- DecisionSystem
- world-state bridge
- goal managers
- ActionRouter
- Synergy + security gating
- existing observations gathered in `AutonomousBrain`

### Required work

- [x] Introduce lightweight `active_work_items` into AGI decision context
- [x] Let decision selection prefer work-item-driven actions before generic fallback
- [x] Expand work-item derivation beyond active goals and coarse world-state summaries
- [x] Derive work from:
  - [x] mentions / replies / comments
  - [x] service messages / operational prompts
  - [x] repeated failures / blocked actions
  - [x] trending opportunity shifts
  - [x] unresolved active goals
  - [x] on-chain / market opportunities that pass existing safety posture
- [x] Make `_execute_cycle()` explicitly ask "what meaningful work exists right now?" before broad proposal generation
- [x] Reduce low-value loop behavior when meaningful work is present

### Done when

- [x] Alley reliably chooses meaningful work before filler activity
- [x] The runtime no longer feels primarily timer-loop driven
- [x] Recent interactions and opportunities consistently shape next action choice

---

## Phase 2 — Persistent Work-Item / Thread Manager

**Goal:** Give Alley continuity so he can keep working on things across cycles.

### Why this matters

Agentic behavior requires continuity of intention.
Without threads/work items, Alley keeps rediscovering the world instead of continuing meaningful work.

### Required work

- [x] Create a persistent work-item manager backed by SQL
- [x] Each work item should store:
  - [x] `id`
  - [x] `type`
  - [x] `source`
  - [x] `summary`
  - [x] `goal_id` if applicable
  - [x] `source_event_id` / `source_entity_id` if applicable
  - [x] `recommended_action_family`
  - [x] `urgency`
  - [x] `status`
  - [x] `last_attempt_at`
  - [x] `last_outcome`
  - [x] `blocked_reason`
  - [x] `capability_gap_hint`
- [ ] Add thread/work-item creation from:
  - [x] social interaction follow-up
  - [x] debate continuation
  - [x] content opportunity
  - [x] operational fix
  - [x] market/on-chain observation
  - [x] repeated failed goal execution
- [x] Add work-item status transitions:
  - [x] detected
  - [x] active
  - [x] blocked
  - [x] waiting
  - [x] completed
  - [x] abandoned
- [x] Add work-item retrieval ordered by urgency, recency, and trust/risk compatibility
- [x] Feed top active work items into AGI Kernel and DecisionSystem every cycle

### Done when

- [x] Alley can continue meaningful work across cycles and restarts
- [x] He no longer loses track of why he acted
- [x] Idle time becomes deliberate maintenance rather than generic looping

---

## Phase 3 — Capability vs Gap Judgment

**Goal:** Let Alley determine whether he can already succeed or needs an upgrade.

### Why this matters

Self-sufficiency depends on judging:

- can I already do this?
- do I need more information?
- do I need a different command?
- do I need a new skill?
- am I blocked by safety/trust constraints?

### Required work

- [x] Add a capability-gap evaluator tied to active work items
- [x] Evaluate each work item against:
  - [x] existing routed actions / commands
  - [x] plugin availability
  - [x] trust/risk policy
  - [x] recent action-family performance
  - [x] world-state evidence
  - [x] current blocked/cooling trust state
- [x] Produce a compact judgment such as:
  - [x] `can_execute_now`
  - [x] `needs_more_context`
  - [x] `needs_different_strategy`
  - [x] `needs_new_skill`
  - [x] `blocked_by_policy`
  - [x] `blocked_by_runtime_readiness`
- [x] Persist that judgment in work-item metadata
- [x] Bias decision selection toward executable work first
- [x] Only generate self-upgrade objectives when `needs_new_skill` is repeatedly supported by evidence

### Done when

- [x] Alley can distinguish capability from real gap
- [x] He stops treating every hard task as a reason to self-modify
- [x] Upgrade proposals become evidence-based instead of abstract

---

## Phase 4 — Explicit Command / Capability Matching

**Goal:** Make Alley choose commands because they fit the work, not because they happen to be in a generic action pool.

### Why this matters

This is the bridge between agentic intention and real execution.

### Required work

- [x] Build a command-affordance matcher for work items
- [x] Score commands/actions by:
  - [x] relevance to work-item type
  - [x] platform fit
  - [x] trust/risk compatibility
  - [x] recent success on similar tasks
  - [x] current cooldown/readiness
  - [x] whether the command advances an active thread
- [x] Expose matched command candidates in decision context
- [x] Prefer routed executable commands over vague generic action categories
- [x] Attach `why_this_command` evidence to selected action context

### Done when

- [x] Alley selects commands because they fit current meaningful work
- [x] Command choice is explainable in terms of goal/opportunity fit
- [x] Random generic action selection is minimized

---

## Phase 5 — Runtime Realignment Around the Original Spine

**Goal:** Make Synergy/security/opportunity drive action choice again, with newer systems as support.

### Why this matters

The original Alley spine should remain primary.
The newer AGI infrastructure should amplify it, not replace it.

### Required work

- [x] Refactor runtime cycle order so the first questions are:
  - [x] what did Alley just find?
  - [x] what is meaningful right now?
  - [x] what does Synergy say is ripe?
  - [x] what does security allow?
  - [x] what can be done with current capabilities?
- [x] Treat timer cycles as heartbeat / maintenance, not the main source of agency
- [x] Make opportunity-driven and interaction-driven work outrank idle exploratory loops
- [x] Keep all final execution routed through ActionRouter / Golden Path
- [x] Keep high-risk actions fail-closed under trust/risk tiers

### Done when

- [x] Alley feels opportunistic and responsive again
- [x] He acts from discovered reality, not mostly from background schedules
- [x] The original Synergy/security/wallet spine is visibly primary in runtime behavior

---

## Phase 6 — Bounded Self-Upgrade Discipline

**Goal:** Let Alley improve himself only when real evidence justifies it.

### Why this matters

We do not want endless manual development.
We also do not want reckless self-modification.

### Required work

- [x] Require repeated evidence before upgrade proposals are created
- [x] Accept upgrade intent only when:
  - [x] a meaningful work item cannot be solved with existing capability
  - [x] the gap recurs often enough
  - [x] the upgrade is within policy/trust boundaries
  - [x] the predicted value outweighs operational risk
- [x] Distinguish:
  - [x] new skill need
  - [x] prompt/context deficiency
  - [x] missing plugin capability
  - [x] blocked external dependency
- [x] Route all upgrade actions through strict self-improvement validation
- [x] Preserve fail-closed behavior for code mutation, deployment, wallets, trading, and external side effects

### Done when

- [x] Alley upgrades himself because evidence demands it
- [x] Self-improvement becomes purposeful, not constant or random
- [x] Manual architecture babysitting decreases over time

---

## Phase 7 — Controlled Expansion Into Real-World Autonomy

**Goal:** Expand Alley’s operational freedom only after the hardened core is stable.

### Why this matters

Real-world action should come after the core is trustworthy.

### Required work

- [x] Expand autonomous real-world action only after Phases 1–6 are stable
- [x] Increase trusted autonomy by domain:
  - [x] social follow-up / debate continuity
  - [x] content / growth execution
  - [x] analysis / reporting
  - [x] market participation
  - [x] self-improvement
- [x] Keep explicit trust/risk tiers for high-impact actions
- [x] Add stronger reflection around money, reputation, and persistent external state changes

### Done when

- [x] Alley can operate more freely without losing safety posture
- [x] Real-world capability expansion is evidence-led and controlled

---

## Immediate Next Batches (Fastest Path)

### Batch A — Durable work-item manager

- [x] Add `src/agentic/work_item_manager.py`
- [x] Persist work items in SQLite
- [x] Feed top active work items into AGI Kernel context
- [x] Connect recent interactions and active goals to durable work-item creation

### Batch B — Runtime work-first cycle

- [x] Change `_execute_cycle()` ordering so active work is evaluated before broad proposal generation
- [x] Keep proposal generation as fallback, not primary driver
- [x] Log why no meaningful work was chosen when Alley idles

### Batch C — Capability-gap evaluator

- [x] Add capability-vs-gap judgment per work item
- [x] Record whether current commands are enough or an upgrade is truly needed
- [x] Use that judgment to suppress pointless self-modification

### Batch D — Explicit command matching

- [x] Match work items to routed commands/actions
- [x] Prefer executable command candidates over generic action families
- [x] Persist command-choice evidence for reflection/learning

---

## Non-Negotiable Invariants

- [x] Single-agent only — no swarm architecture
- [x] All meaningful actions route through `ActionRouter`
- [x] Synergy/security/trust/risk validation remains fail-closed
- [x] High-risk external actions remain tightly gated
- [x] Self-upgrade remains evidence-driven and policy-bound
- [x] SQL/world-state memory remains the durable backbone, not JSON sprawl

---

## Success Definition

Alley is considered back on track when he can:

- [x] discover meaningful real-world work from what he encounters
- [x] continue that work across cycles
- [x] choose available commands because they fit the work
- [x] know whether he already has the capability to succeed
- [x] only seek upgrades when the gap is real
- [x] remain routed, secure, and fail-closed for high-risk work
- [x] behave like one persistent scavenger intelligence rather than a passive scheduled system
