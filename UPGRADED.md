# UPGRADED.md

## What Changed From the Original `DegenApeDev/AlleyBot` Repo

This document explains the major differences between:

- the original public repo: `github.com/DegenApeDev/AlleyBot`
- the current private repo in this workspace: `AlleyBot_Private`

It is not a line-by-line changelog. It is a practical architecture and behavior comparison.

---

## 1. Identity Of The Project

### Original public repo
The original repository presented AlleyBot as a general autonomous AI agent framework:

- configurable bot identity via `BOT_NAME`
- multi-platform social agent framework
- plugin-driven automation
- self-improvement and skill generation
- basic autonomous scheduling

It was more of a reusable autonomous-agent starter framework.

### Current private repo
The current repository is no longer just a generic framework. It is a much more opinionated and specific AlleyBot system with:

- AlleyBot as the canonical identity
- a stronger AGI-style architecture
- production event-driven startup
- Telegram as an active owner control surface
- deeper world-state, planning, memory, and execution validation
- stronger security/trust gating around meaningful actions

In practice, the current repo is a hardened autonomous AlleyBot runtime, not just a starter framework.

---

## 2. Core Runtime Architecture

### Original public repo
The original `alleybot_core.py` was centered on:

- plugin loading
- Moltbook API initialization via `MoltbookAPI()`
- memory helpers
- schedule-based autonomous loops
- command execution through plugin manager registries

It already had some agentic files in `src/agentic`, but the core runtime was still relatively lightweight and mixed legacy + new ideas.

### Current private repo
The current `alleybot_core.py` has shifted toward a stronger production architecture:

- removed direct `MoltbookAPI()` initialization from core startup
- added console logging initialization and retention handling
- added cleanup/signal handling
- added AGI kernel initialization as a first-class core subsystem
- initializes decision systems after plugins load
- integrates production autonomous startup through `src/main.py`

The biggest change is that the AGI kernel is now much more central to runtime behavior rather than being just another optional intelligence layer.

---

## 3. Event-Driven Production Startup

### Original public repo
The original repo already exposed production mode from `alleybot_core.py`, but it was less hardened operationally.

### Current private repo
The current repo has a much more explicit production startup spine in `src/main.py`:

- builds session manager, model router, skill loader, and event runner
- schedules autonomous startup explicitly
- starts Telegram polling as an async task
- waits for Telegram polling readiness instead of assuming it is live
- performs clearer startup/shutdown sequencing

This is a meaningful upgrade from “run the bot” to “run a coordinated async production system.”

---

## 4. Telegram Became A Primary Operational Interface

### Original public repo
Telegram existed in the original repo as a control and communication channel.

### Current private repo
Telegram has become much more central and much more complex:

- far more command handlers
- conversational AI path for owner/admin interaction
- menu-driven handler registration
- startup readiness tracking for polling
- better error handling for Telegram failures
- more diagnostics around updates, handler failures, and shutdown
- bounded responsiveness work so model warmup/classification does not freeze the bot

This means Telegram is no longer just a convenience interface. It is one of the authoritative operational surfaces of the bot.

---

## 5. AGI Kernel Role Expanded Significantly

### Original public repo
The original repo already had `src/agentic/agi_kernel.py` and a broad collection of agentic files. But the surrounding runtime still looked partly transitional.

### Current private repo
The current repo has pushed much more responsibility into the AGI kernel layer. The AGI kernel now participates more directly in:

- autonomous decision making
- work-item capability judgment
- context and runtime prioritization
- upgrade gating
- integration with routed actions
- learning from outcomes

This is one of the biggest architectural differences. The AGI kernel is now closer to the system brain than it was in the original repo.

---

## 6. Golden Path Execution: `ActionRouter`

### Original public repo
The original repo did not make `src/agentic/action_router.py` the clear single execution path in the same strong way.

### Current private repo
The current repo explicitly defines `src/agentic/action_router.py` as the unified execution pipeline:

- AGI kernel validation
- SyMod / trust validation
- plugin execution
- outcome reflection
- trust-state persistence
- prediction / mismatch-aware outcome handling

This is a major architectural upgrade because it reduces scattered execution behavior and creates a single place to enforce validation and learning.

---

## 7. Trust / Risk / Validation Gating Is Stronger

### Original public repo
The original repo had intelligence and autonomy, but less explicit fail-closed action governance in the main execution path.

### Current private repo
The private repo has much stronger action gating concepts, including:

- `impact`
- `risk_level`
- `trust_level`
- trust buckets
- cooldown and degradation states
- stronger validation around risky or degraded actions

This makes the current system more suitable for real autonomous behavior where unsafe or low-trust actions should fail closed.

---

## 8. Work-Item And Goal-Driven Runtime Is More Developed

### Original public repo
The original system leaned more on autonomous loops, plugin tasks, and broad intelligence modules.

### Current private repo
The current repo is more explicitly moving toward meaningful work selection and durable intention tracking:

- SQL-backed work-item handling
- active/blocked/waiting/completed work-item lifecycle
- stronger connection between goals, world-state signals, and execution
- capability-gap judgment for whether work can be executed now
- bounded self-upgrade logic tied to repeated evidence and policy

This is a major upgrade from time-based activity toward more structured agentic work selection.

---

## 9. Memory And Context Systems Are More Operationally Connected

### Original public repo
The original repo already had:

- JSON memory fallback
- SQLite memory mixin
- optional enhanced memory
- semantic search helpers

### Current private repo
The current repo still keeps these ideas, but the memory/context systems are more woven into live behavior:

- Telegram conversation history persistence
- session/RAG-style context integration
- agentic memory influence on runtime decisions
- action logging and outcome reflection loops
- stronger connection between memory, planning, and execution

The change is not merely “more memory files exist.” It is that memory is more involved in runtime behavior.

---

## 10. Plugin Manager And Plugin Ecosystem Grew Substantially

### Original public repo
The original `plugin_manager.py` was simpler:

- load plugins from config
- initialize plugins
- register tasks/commands/endpoints
- unload/reload basics

### Current private repo
The current repo has a larger and more complex plugin ecosystem with many more runtime roles, integrations, and commands.

It also carries more operational complexity:

- richer Telegram command surface
- deeper agentic integrations
- more platform-specific behaviors
- more runtime coordination between plugins and the AGI layer

In short, the plugin system evolved from dynamic loading infrastructure into a larger live capability surface.

---

## 11. Model Routing And LLM Usage Became More Structured

### Original public repo
The original repo had direct AI client modules like:

- `grok_ai.py`
- `deepseek_ai.py`

These were used more directly.

### Current private repo
The current repo adds more routing structure around model usage, including:

- model routing in `src/config/models.py`
- LLM routing in `src/core/llm_router.py`
- more explicit use of Grok vs DeepSeek by task type
- better handling of runtime fallbacks
- Telegram conversational routing through classifier + fallback model logic

This is an architectural shift from direct model calls toward a model-routing layer.

---

## 12. Identity Grounding Matters More Now

### Original public repo
The original repo had AlleyBot identity in prompts and comments, but the architecture was simpler and likely had fewer places for provider identity leakage.

### Current private repo
The current repo has more model-routing and fallback surfaces, which creates more places where identity can drift unless explicitly grounded.

Recent fixes in the current repo addressed issues where conversational replies could incorrectly identify as the model provider rather than AlleyBot. That class of problem is more likely in the newer architecture because it has:

- more indirection
- more fallback paths
- more prompt plumbing layers
- more async conversational handling

So the current repo is more capable, but it also requires stricter identity grounding discipline.

---

## 13. Operational Hardening Increased

Compared with the original public repo, the current private repo contains much more operational hardening work, including:

- better shutdown handling
- console logging retention
- startup validation behavior
- Telegram diagnostics
- clearer runtime readiness checks
- more compile/test-oriented validation during fixes
- more cleanup of stale backup and disabled artifacts

This is the difference between a promising framework and a system being actively hardened for continuous use.

---

## 14. Repository Scale And Complexity Increased A Lot

### Original public repo
The original repo was materially smaller and easier to mentally map.

### Current private repo
The current repo is much larger in both code and documentation:

- more docs
- more planning files
- more agentic modules
- more Telegram command modules
- more integrations
- more runtime paths

That means the current repo has more capability, but also more maintenance burden and more places where stale paths can survive.

---

## 15. High-Level Summary

### The original public repo was:

- a strong autonomous agent framework
- plugin-driven
- social-platform oriented
- already experimenting with AGI-style modules
- simpler operationally

### The current private repo is:

- more specifically AlleyBot-centered
- more agentic and execution-governed
- more event-driven in production
- more Telegram-operationally integrated
- more trust/risk gated
- more memory/planning/work-item aware
- more complex and more actively hardened

---

## 16. Short Version

If the original repo was:

- **an autonomous agent framework with growing AGI ideas**

then the current private repo is:

- **a more opinionated, more guarded, more deeply integrated AlleyBot runtime with stronger execution control, richer Telegram interaction, and a more central AGI kernel**

---

## 17. Concrete Examples Of Differences

A few concrete examples from the comparison:

- original core used `MoltbookAPI()` directly; current core no longer does
- current core initializes console logging and cleanup handlers
- current core initializes AGI kernel and decision systems more explicitly
- current repo has `src/agentic/action_router.py` as a clear execution-governance spine
- current `src/main.py` is a more operationally explicit async startup path
- current Telegram path includes readiness tracking and conversational routing improvements
- current repo contains more files in `src/agentic` than the original repo
- current repo has much more supporting documentation and planning material

---

## 18. What Did *Not* Fundamentally Change

Some things were already present in the original repo and remain part of the design:

- plugin-based architecture
- autonomous operation goal
- memory systems
- Telegram control concept
- Grok and DeepSeek usage
- self-improvement as a design theme
- social/platform automation

So this is not a different project. It is an evolved, more specialized, and more operationally hardened version of the same AlleyBot line.
