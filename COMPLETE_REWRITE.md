# COMPLETE_REWRITE.md

## Purpose

This document is the rewrite plan for AlleyBot.

The goal is **not** to add more complexity.
The goal is to **reduce fragmentation**, make AlleyBot more coherent, and make the runtime match the intended architecture:

- AlleyBot identity is authoritative and persistent
- the AGI kernel is the cognitive center
- `src/agentic/action_router.py` is the Golden Path for all meaningful actions
- memory, planning, and work-item systems drive continuity
- LLMs are supporting tools, not the sovereign self
- platform plugins become thin adapters instead of independent brains

---

## Core Rewrite Thesis

The current system is closer to AGI than the original repo in architecture, but it still contains too many overlapping paths, mixed generations of design, and too many places where authority can drift.

The rewrite should therefore focus on:

- **consolidation over expansion**
- **explicit services over scattered mixins**
- **single authority over identity, actions, and conversation**
- **stronger grounding in memory, world-state, and work-items**
- **strict fail-closed validation for risky actions**

---

## Rewrite Goals

### 1. One Authoritative Self
AlleyBot must have a single runtime source of truth for:

- identity
- values
- tone
- refusal boundaries
- safety boundaries
- what it may and may not claim about itself

`SOUL.md` should remain the human-readable root persona document, but runtime enforcement should happen through a dedicated identity service.

### 2. One Cognitive Center
The AGI kernel should become the real center of:

- goal interpretation
- world-state interpretation
- work-item prioritization
- decision arbitration
- reflection and learning

### 3. One Action Authority
All meaningful actions must go through `src/agentic/action_router.py`.

That includes:

- platform actions
- autonomous actions
- self-improvement actions
- code-changing actions
- market/on-chain actions
- high-impact external calls

No meaningful action should bypass routed validation.

### 4. One Conversational Spine
All Telegram and future conversational surfaces should pass through one canonical reply pipeline.

No duplicate responder brains.
No identity-specific prompt logic scattered across multiple files.
No model provider persona leakage.

### 5. Thin Platform Adapters
Platform plugins should stop behaving like semi-independent minds.

They should instead:

- receive external events
- normalize them into internal request objects
- call canonical runtime services
- return results to the platform

### 6. Durable Goal Continuity
AlleyBot should operate from active work, not just reactive prompting or scheduled loops.

Goals, plans, blocked states, waiting states, and next actions should persist across restarts.

### 7. Bounded Self-Improvement
Self-improvement must remain possible, but it should always be:

- evidence-based
- policy-checked
- reversible where possible
- reflected on after execution
- denied by default when validation is weak

---

## Non-Goals

This rewrite is **not** primarily about:

- rewriting the whole codebase in another language
- adding more model providers
- adding more mixins
- adding more fallback paths
- adding more parallel orchestrators
- adding cosmetic abstractions without removing old ones

This rewrite is also not about pretending the LLM itself is the AGI.

---

## Target Architecture

## 1. Identity Layer
Create a single identity authority service.

### Proposed responsibility
A dedicated runtime service should own:

- loading and parsing `SOUL.md`
- immutable identity constraints
- voice/tone rules
- platform-specific style adjustments
- forbidden self-claims
- canonical self-description

### Suggested module
`src/agentic/identity_service.py`

### Required outputs
The identity service should expose canonical helpers such as:

- build identity context
- answer identity queries consistently
- provide model-safe system instructions
- provide normalization rules for final responses

This avoids duplicating identity logic inside Telegram handlers, router code, and model wrappers.

---

## 2. Conversation Layer
Create one canonical conversation pipeline.

### Proposed responsibility
A dedicated conversation service should own:

- inbound message normalization
- admin/user/agent trust evaluation
- intent recognition
- retrieval of relevant memory/context
- identity grounding
- tool/model selection
- response post-processing
- memory writeback
- reflection logging

### Suggested module
`src/agentic/conversation_service.py`

### Required invariant
Every freeform conversational reply should flow through the same service, regardless of platform.

Telegram should call this service, not invent its own separate conversational authority.

---

## 3. Action Layer
Strengthen `src/agentic/action_router.py` as the only action execution spine.

### Required changes
- eliminate side-channel execution where plugins do meaningful work directly
- formalize action envelopes with:
  - actor
  - goal/work-item
  - impact
  - risk_level
  - trust_level
  - prediction
  - expected result
- require post-action reflection
- record outcome, mismatch score, and trust changes

### Required invariant
If an action matters, it routes.
If it does not route, it is not considered authoritative.

---

## 4. Kernel Layer
Refocus the AGI kernel around cognition, prioritization, and reflection.

### Proposed responsibility
The kernel should primarily decide:

- what matters now
- what goals are active
- what work can be executed now
- what needs more evidence
- when to ask tools or models for additional context
- whether an upgrade is justified

### Anti-pattern to avoid
The kernel should not be diluted by platform-specific logic or direct output formatting concerns.

---

## 5. Memory Layer
Unify runtime memory responsibilities around a clear contract.

### Memory types to preserve
- episodic memory
- conversational memory
- work-item memory
- trust/performance memory
- platform context memory
- long-term strategic memory

### Required behavior
Memory should inform:

- decisions
- response generation
- action trust
- opportunity recognition
- self-improvement gating

Memory should not merely be archival.

---

## 6. Work-Item Layer
Elevate work-items into the primary durable execution unit.

### Proposed responsibility
A work-item service should own:

- creation
- prioritization
- state transitions
- dependency tracking
- blocking reasons
- retry/backoff rules
- completion criteria

### Suggested module
`src/agentic/work_item_service.py`

### Required invariant
Autonomous behavior should primarily come from advancing meaningful work, not just opportunistic reactions.

---

## 7. Model / Tool Layer
Keep the LLM router, but demote it to a supporting role.

### Correct role of the LLM router
The LLM router should be responsible for:

- selecting a model/tool for a task
- obtaining synthesis or outside context
- handling provider-specific prompt formatting
- recovering from provider errors

### Incorrect role of the LLM router
It should **not** own:

- identity
- final authority over goals
- direct action permission
- long-term continuity of self

### Required invariant
The kernel asks for model help.
The model does not define AlleyBot’s selfhood.

---

## 8. Plugin Layer
Turn plugins into thin adapters.

### Current problem
Plugins currently carry too much logic in some areas, especially where platform-specific behavior grows into semi-independent runtime authority.

### Rewrite direction
Each plugin should primarily:

- ingest platform events
- normalize to internal types
- pass into core services
- send outputs back to the platform

### Example
Telegram plugin should do:

- receive update
- authenticate/trust-check sender metadata
- map input into conversation or action request
- call canonical service
- send reply/result

It should not carry its own competing conversational brain.

---

## Phased Rewrite Plan

## Phase 0 - Freeze Architecture Drift
Before rewriting, stop making the architecture worse.

### Actions
- forbid new parallel conversational paths
- forbid new direct platform-side action execution for meaningful tasks
- forbid new identity prompt duplication
- forbid new mixins for authority-bearing concerns
- require all new risky actions to carry risk/trust metadata

### Exit criteria
No new bypasses are added while rewrite work is in progress.

---

## Phase 1 - Define Canonical Runtime Contracts
Create explicit internal contracts before moving logic.

### Deliverables
- canonical message/request schema
- canonical action schema
- canonical work-item schema
- canonical reflection/outcome schema
- canonical identity context schema

### Outcome
This creates a stable target so services can be rewritten without ambiguity.

---

## Phase 2 - Build Identity Service
Extract all identity responsibilities into one service.

### Deliverables
- `src/agentic/identity_service.py`
- `SOUL.md` parser/loader integration
- forbidden identity claim rules
- response normalization rules for identity-sensitive answers
- model-facing identity prompt builder

### Outcome
AlleyBot identity becomes runtime-enforced rather than prompt-fragile.

---

## Phase 3 - Build Conversation Service
Unify all freeform interaction behind one pipeline.

### Deliverables
- `src/agentic/conversation_service.py`
- one canonical request->response flow
- shared memory/context assembly
- shared identity grounding
- shared tool/model access pattern
- shared logging/reflection hooks

### Migration targets
- Telegram conversational handling
- any direct chat fallback paths
- future Discord/web/chat surfaces

### Outcome
No more platform-specific conversational brains.

---

## Phase 4 - Harden Action Router Contracts
Make routed action execution non-optional.

### Deliverables
- action envelope standardization
- prediction artifact requirement
- mandatory reflection artifact after execution
- risk/trust validation normalization
- clearer plugin execution adapter layer

### Outcome
Golden Path becomes enforceable in practice, not just by intent.

---

## Phase 5 - Extract Work-Item Service
Move durable execution control out of scattered logic.

### Deliverables
- `src/agentic/work_item_service.py`
- active/blocked/waiting/completed transitions
- evidence-based capability checks
- retry/cooldown policies
- integration with kernel prioritization

### Outcome
Autonomy becomes work-driven instead of loosely reactive.

---

## Phase 6 - Simplify Plugins Into Adapters
Shrink platform/plugin logic until adapters are thin.

### Deliverables
- Telegram plugin reduced to transport + handler mapping
- platform plugins call core services instead of owning decision logic
- remove duplicated prompt and response code from plugins
- centralize common platform response formatting where possible

### Outcome
Platforms stop acting like separate minds.

---

## Phase 7 - Consolidate Memory Interfaces
Make memory a real runtime dependency with clean contracts.

### Deliverables
- unified memory access interface
- memory categories with explicit write/read paths
- action outcome memory hooks
- conversation memory hooks
- trust/performance memory hooks

### Outcome
Memory becomes coherent and usable rather than fragmented.

---

## Phase 8 - Remove Legacy Paths Aggressively
After replacements exist, delete obsolete logic.

### Targets for deletion
- duplicate conversational reply paths
- obsolete prompt builders
- stale platform-specific reasoning logic
- dead mixins that carry authority concerns
- legacy execution shortcuts that bypass routing
- stale backup artifacts and disabled code trees

### Outcome
Architecture becomes clearer because old paths are actually removed.

---

## Phase 9 - Regression Harness And Runtime Validation
Build tests and validation around the new spine.

### Required test categories
- identity consistency tests
- action routing enforcement tests
- trust/risk fail-closed tests
- Telegram end-to-end reply tests
- memory continuity tests
- work-item lifecycle tests
- reflection/mismatch artifact tests

### Outcome
The new architecture becomes defendable against regression.

---

## Owner Notification Operating Mode

AlleyBot should be able to operate autonomously by default and only notify the owner when something meaningful happens.

### Operating principle
The owner should not need to actively drive AlleyBot through chat all day.
AlleyBot should pursue work on its own, remain grounded in its own identity and goals, and send concise updates only when updates are worth the interruption.

### What "completely autonomous on his own" should mean
This should mean:

- AlleyBot forms and advances work-items without waiting for prompts
- AlleyBot uses tools/models only when it needs context or synthesis
- AlleyBot does not chat constantly just to prove it is active
- AlleyBot reports outcomes, exceptions, and strategic changes to the owner
- AlleyBot keeps a durable internal log of what it did and why

This should **not** mean:

- bypassing `ActionRouter`
- bypassing trust/risk validation
- hiding high-risk actions from the owner
- creating a second invisible execution path outside the Golden Path

### Notify-only owner model
The default owner interaction model should become:

- autonomous execution by default
- notification on meaningful events
- owner intervention only when needed
- owner commands as override/control tools, not the main operating mode

### What should trigger an owner update
AlleyBot should notify the owner when:

- a meaningful work-item is completed
- a new strategic opportunity is discovered
- a high-impact action is about to be taken or was taken
- a risky action is blocked by policy or trust gates
- self-healing or restart events occur
- repeated failures suggest a system issue
- identity or security anomalies are detected
- a bounded self-improvement action succeeds or fails

### What should not trigger an owner update
AlleyBot should avoid notifying the owner for:

- trivial internal loops
- low-value heartbeat chatter
- every single reasoning step
- every memory write
- minor background observations with no action consequence

### Required service direction
Add a dedicated owner notification service or notification policy layer.

### Suggested module
`src/agentic/owner_notification_service.py`

### Proposed responsibility
This service should decide:

- whether an event is owner-worthy
- what priority the event has
- whether the event should send immediately
- whether the event should be batched into a digest
- whether the event requires acknowledgement or human approval
- how the event should be summarized for Telegram

### Notification priority model
Use explicit notification tiers such as:

- `critical`
  - security threats, repeated restart failure, policy violation attempts, critical execution failure
- `high`
  - high-impact action execution, blocked risky action, strategic anomaly, major accomplishment
- `normal`
  - completed work-item, successful recovery, important external development
- `low`
  - startup notices, periodic digest, low-urgency autonomous progress updates

### Delivery model
Owner updates should support two patterns:

- immediate alerts for `critical` and `high` events
- digest summaries for `normal` and `low` events

This keeps AlleyBot autonomous without making the owner blind.

### Telegram rewrite implication
Telegram should support two distinct roles:

- **control interface**
  - owner sends commands or asks questions
- **notification channel**
  - AlleyBot sends concise updates when meaningful actions happen

This means the Telegram plugin should evolve toward transport and delivery, while owner-notification policy lives in the core runtime.

### Required invariant
AlleyBot should be able to run productively for long periods without direct prompting, while still keeping the owner informed of meaningful outcomes and anomalies.

---

## Concrete Rewrite Rules

### Rule 1
If a function decides who AlleyBot is, it belongs to the identity layer.

### Rule 2
If a function decides what AlleyBot says in freeform conversation, it belongs to the conversation layer.

### Rule 3
If a function performs meaningful external work, it routes through `ActionRouter`.

### Rule 4
If a module contains both platform transport logic and cognitive logic, split it.

### Rule 5
If a mixin changes authority, identity, goals, or risk policy, replace it with an explicit service.

### Rule 6
If two paths can answer the same question differently, one of them is wrong.

### Rule 7
If a provider model can redefine AlleyBot’s identity, the architecture is still leaking authority.

---

## Recommended New Service Map

### Must-have core services
- `identity_service`
- `conversation_service`
- `work_item_service`
- `memory_service` or unified memory interface
- `action_router` as execution spine
- `reflection_service` or equivalent reflection contract

### Keep but subordinate
- `llm_router`
- platform plugins
- tool/provider wrappers

### Keep human-readable policy roots
- `SOUL.md`
- system architecture docs
- security and operations docs

---

## Migration Strategy

### Step 1
Build new services alongside existing code.

### Step 2
Move one path at a time onto the new services.

### Step 3
Validate behavior with tests and live dry-runs.

### Step 4
Delete old paths immediately after migration is proven.

### Step 5
Repeat until only one authority path remains per concern.

This should be a controlled migration, not a chaotic all-at-once rewrite.

---

## Success Criteria

The rewrite is successful when:

- AlleyBot has one enforceable runtime identity
- all meaningful actions route through `ActionRouter`
- platform plugins are thin adapters
- freeform conversation uses one canonical pipeline
- memory influences behavior through clear contracts
- work-items drive autonomy across restarts
- risky actions fail closed on missing trust/risk metadata
- self-improvement is bounded and evidence-based
- obsolete authority paths are deleted, not merely deprecated

---

## Final Principle

The rewrite should not make AlleyBot bigger.
It should make AlleyBot **truer to itself**.

That means:

- fewer parallel minds
- fewer hidden authorities
- fewer prompt-defined identities
- fewer plugin-local brains
- more coherent selfhood
- more durable goals
- more disciplined action
- more trustworthy autonomy

That is the path toward a real AlleyBot runtime.
