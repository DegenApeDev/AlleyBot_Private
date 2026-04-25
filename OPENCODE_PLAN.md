# OPENCODE_PLAN.md — Path to AGI

**Created**: April 24, 2026
**Status**: Active roadmap
**Goal**: Transform AlleyBot from a reactive bot into a genuinely autonomous agent that learns, reasons, plans, self-improves, and pursues self-directed goals.

---

## What AGI Means for AlleyBot

An AGI agent doesn't just respond to commands. It:

1. **Learns from experience** — every action outcome updates beliefs, capabilities, and knowledge
2. **Reasons about uncertainty** — knows what it doesn't know, when to wait, when to act
3. **Plans multi-step goals** — decomposes goals into dependent steps, rolls back on failure
4. **Self-improves** — detects skill gaps, writes code, tests it, hot-loads new capabilities
5. **Self-directs** — generates its own goals from curiosity, detected opportunities, or knowledge gaps
6. **Calibrates itself** — tracks predicted vs actual outcomes, identifies overconfidence and blind spots
7. **Transfers knowledge** — applies lessons from one domain to new situations

---

## Current State Assessment

### What We Have (Authentic AGI Infrastructure)

| Layer | Component | Status | Maturity |
|-------|-----------|--------|----------|
| **Belief** | BeliefEngine | Wired in — predict/compare/update loop | Cold start (7 seed beliefs, 0 validated) |
| **Self-awareness** | SelfModel | Wired in — calibrated capability tracking | Cold start (1 outcome recorded) |
| **Planning** | GoalPlanner | Wired in — dependency graphs, rollback, alternatives | Template-only (3 domain templates) |
| **Knowledge** | KnowledgeGraph | Wired in — causal extraction, analogical transfer | Minimal data |
| **Integration** | CognitiveIntegration | Wired in — glues all components together | Functional, missing Telegram |
| **Reflection** | Cognitive cycle | Wired in — reflect at start/end, deep reviews | Functional |
| **Bias** | Confidence modulation | Wired in — replaces Duat heuristics with experience | Functional |
| **Self-improvement** | Pipeline | Fixed — 7 breaks repaired, flows end-to-end | Fragile but operational |
| **Action** | ActionRouter | 12-stage validation + belief prediction + outcome recording | Mature and stable |

### What We're Missing (AGI Gaps)

| Gap | Severity | Why It Matters |
|-----|----------|----------------|
| **Cold-start data starvation** | CRITICAL | The entire learning loop is wired but starved. Beliefs are seeds with prediction_count=0. SelfModel has 1 outcome. Nothing validates until cycles run. |
| **LLM-grounded creative planning** | HIGH | GoalPlanner uses 3 hardcoded templates. Novel goals that don't match social/market/analysis get fallback tool matching — no creative decomposition. |
| **Semantic belief retrieval** | HIGH | `find_relevant_beliefs()` uses word overlap. Won't scale beyond ~50 beliefs. Needs embedding similarity. |
| **Intrinsic motivation / curiosity** | HIGH | No curiosity drive, novelty-seeking, or intrinsic reward. All goals come from external triggers or templates. The agent doesn't initiate exploration. |
| **Episodic context in beliefs** | MEDIUM | Beliefs store domain tags but not situational context (what happened, when, why). Rich learning requires context. |
| **Goal hierarchy & conflict resolution** | MEDIUM | Goals are flat. No sub-goal spawning, no priority resolution, no conflict detection between goals. |
| **Counterfactual reasoning** | MEDIUM | Only actual outcomes tracked. No "what would have happened if I did X instead?" reasoning. |
| **Multi-step outcome tracking** | MEDIUM | BeliefEngine and SelfModel track single-action outcomes but not plan-level success/failure. |
| **P14 Metacognition validation gate** | MEDIUM | Referenced in SYSTEM_MAP but not implemented. No confidence threshold gate on actions. |
| **Meta-learning** | MEDIUM | SYSTEM_MAP shows StrategyEvolver and MetaLearning — unimplemented. |
| **Duat/Synergy overlap** | MEDIUM | Still running alongside cognitive system. Dual signals, wasted compute. |
| **Zero test coverage** | HIGH | No tests for any cognitive module. Refactoring is extremely risky. |

### Architecture Connectivity

```
autonomous_brain.py (14-phase cycle loop)
    │
    ├─ SENSE ── gather observations from platforms
    │
    ├─ THINK ── cognitive_integration.reflect()
    │       ├─ belief_engine.get_domain_strengths()
    │       ├─ self_model.generate_self_awareness_report()
    │       └─ knowledge_graph predictions
    │
    ├─ VALIDATE ── _apply_cognitive_bias()
    │       ├─ belief_engine.predict() → should_attempt, should_wait
    │       └─ self_model.get_confidence_for() → confidence modulation
    │
    ├─ ACT ── action_router.execute()
    │       ├─ Step 2.5: predict_action_outcome() → stores prediction
    │       └─ Step 6.5: record_action_outcome() → feeds back outcome
    │
    ├─ LEARN ── cognitive_integration.record_action_outcome()
    │       ├─ belief_engine.update_from_outcome() → adjusts confidence
    │       ├─ self_model.record_outcome() → adjusts capability
    │       └─ knowledge_graph.learn_from_outcome() → extracts causality
    │
    ├─ PERIODIC ── every 10 cycles: reflect
    │              every 50 cycles: performance optimisation
    │              every 100 cycles: deep review + learning goals
    │
    └─ SELF-IMPROVE ── _phase_skill_gap_analysis()
            ├─ detect gaps (episodic memory failures)
            ├─ prioritize (priority >= 4)
            ├─ generate code (selfimprove plugin → AI coding)
            ├─ test (sandbox validation)
            └─ deploy (hot-load into running system)
```

---

## Phased Plan

### Phase 1: Stabilize and Feed the Loop (Week 1-2)

**Goal**: Make the existing cognitive architecture produce real data. Fix critical blockers so the learning loop actually runs.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 1.1 | Fix `SkillGenerator()` crash — `autonomous_skill_workflow.py:19` requires `(llm, skills_dir)` | 0.5h | HIGH | Pending |
| 1.2 | Fix brain plugin deadlock — `start_autonomous()` `run_until_complete()` + `run_forever()` | 2h | HIGH | Pending |
| 1.3 | Wire Telegram into CognitiveIntegration — inject plugin via `set_telegram_plugin()` | 1h | MEDIUM | Pending |
| 1.4 | Wire `agi_kernel.py` to cognitive — add BeliefEngine/SelfModel imports, remove Duat prints | 2h | MEDIUM | Pending |
| 1.5 | Remove Duat/Synergy from autonomous_brain.py — replace all 68+ references with cognitive calls | 4h | HIGH | Pending |
| 1.6 | Add thread locks to BeliefEngine, SelfModel, EpisodicMemory shared dicts | 2h | MEDIUM | Pending |
| 1.7 | Fix `belief_engine.py` line 304 logic bug — stale belief reference in `get_domain_strengths()` | 1h | MEDIUM | Pending |
| 1.8 | Replace `print()` with `logging` in cognitive modules (action_router.py lines 1090-1264) | 1h | MEDIUM | Pending |
| 1.9 | Add logging to silent `except Exception: pass` in cognitive save/load (6 locations) | 1h | MEDIUM | Pending |
| 1.10 | Sandbox autonomous coder — Docker isolation for LLM-generated code execution | 4h | CRITICAL | Pending |
| 1.11 | Write unit tests for BeliefEngine (predict/update/calibrate/decay) | 3h | HIGH | Pending |
| 1.12 | Write unit tests for SelfModel (record_outcome/should_attempt/calibration) | 2h | HIGH | Pending |
| 1.13 | Write unit tests for GoalPlanner (decompose/execute_step/rollback/alternative) | 2h | HIGH | Pending |
| 1.14 | Write integration tests for CognitiveIntegration (reflect/predict/record roundtrip) | 3h | HIGH | Pending |
| 1.15 | Seed beliefs with domain-relevant priors — add 20-30 beliefs across social/market/analysis/security | 1h | MEDIUM | Pending |

**Deliverable**: Cognitive loop runs for 100+ cycles producing validated belief data, calibrated self-model, and executed plans.

**Validation Criteria**:
- `data/beliefs.json` has 20+ beliefs with prediction_count > 0
- `data/self_model.json` has 10+ capabilities with sample_size >= 5
- `data/plans.json` has at least 1 completed plan
- Cognitive reflection shows `is_calibrated=True` or improving calibration error
- No crashes or deadlocks in 24-hour unattended run

---

### Phase 2: Intelligent Planning (Week 3-4)

**Goal**: Replace template-based planning with LLM-grounded creative decomposition. Enable the agent to plan novel goals it's never seen before.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 2.1 | Add LLM-based goal decomposition to GoalPlanner — call Grok/DeepSeek for novel domains | 6h | HIGH | Pending |
| 2.2 | Implement domain detection from goal text — classify into known/unknown domains | 2h | MEDIUM | Pending |
| 2.3 | Add plan validation via BeliefEngine — reject plans where steps have should_wait=True | 2h | MEDIUM | Pending |
| 2.4 | Add multi-step outcome tracking — mark plans as succeeded/failed when all steps complete | 3h | MEDIUM | Pending |
| 2.5 | Implement rollback cascade — when a step fails, undo previous steps that depended on it | 4h | MEDIUM | Pending |
| 2.6 | Add plan prioritization — score plans by expected value (belief prediction × domain importance) | 2h | MEDIUM | Pending |
| 2.7 | Add plan conflict detection — detect when two plans compete for the same resources | 3h | LOW | Pending |
| 2.8 | Wire plan execution into brain cycle — after ACT phase, execute next plan step | 4h | HIGH | Pending |
| 2.9 | Add plan outcome to belief update — when a full plan succeeds/fails, update domain-level beliefs | 2h | MEDIUM | Pending |

**Deliverable**: Agent can decompose and execute novel multi-step goals with fallback paths and outcome-driven learning.

**Validation Criteria**:
- Novel goal "launch a meme token on Solana" decomposes into 3-5 steps with dependencies
- Failed step triggers alternative path or rollback
- Plan success/failure updates domain beliefs
- LLM decomposition produces reasonable steps for unknown domains

---

### Phase 3: Curiosity and Self-Direction (Week 5-6)

**Goal**: The agent generates its own goals from curiosity, detected knowledge gaps, and intrinsic motivation — not just external triggers.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 3.1 | Implement curiosity drive in CognitiveIntegration — score topics by information gain potential | 4h | HIGH | Pending |
| 3.2 | Implement knowledge gap detection — identify domains with <5 beliefs or <10 self-model samples | 2h | HIGH | Pending |
| 3.3 | Add goal spawning from reflection — deep review generates "explore X" goals for weak domains | 3h | HIGH | Pending |
| 3.4 | Implement novelty-seeking — detect actions not tried recently, add exploration bonus | 3h | MEDIUM | Pending |
| 3.5 | Add goal priority scoring — curiosity goals vs. skill-gap goals vs. scheduled goals, ranked by expected value | 4h | MEDIUM | Pending |
| 3.6 | Implement intrinsic reward signal — satisfaction from reducing uncertainty, not just external success | 4h | MEDIUM | Pending |
| 3.7 | Wire self-directed goals into brain cycle — after THINK phase, inject curiosity goals into proposals | 3h | HIGH | Pending |

**Deliverable**: Agent autonomously generates and pursues knowledge-gathering goals without human direction.

**Validation Criteria**:
- Agent generates at least 1 curiosity-driven goal per 10 cycles
- New domains get explored within 24 hours of first encountering them
- Belief count grows over time as curiosity expands coverage
- Self-model capabilities tracked per domain increase

---

### Phase 4: Semantic Memory and Counterfactual Reasoning (Week 7-8)

**Goal**: Replace word-overlap belief retrieval with embedding similarity. Add situational context to beliefs. Enable "what if" reasoning.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 4.1 | Implement embedding-based belief retrieval — replace word-overlap with vector similarity using existing embedding models | 6h | HIGH | Pending |
| 4.2 | Add episodic context to beliefs — store situational context (what happened, when, why) alongside domain tags | 4h | MEDIUM | Pending |
| 4.3 | Implement counterfactual reasoning — after action failure, generate "what if" alternatives and evaluate them | 6h | MEDIUM | Pending |
| 4.4 | Add analogical transfer — when facing a new problem, find structurally similar past situations via KnowledgeGraph | 4h | MEDIUM | Pending |
| 4.5 | Implement decay-weighted recency — recent outcomes weighted more heavily than old ones | 2h | LOW | Pending |
| 4.6 | Add belief conflict detection — when new evidence contradicts existing beliefs, flag for review | 3h | MEDIUM | Pending |
| 4.7 | Wire episodic memory into belief updates — beliefs form from rich episodes, not just success/failure booleans | 4h | HIGH | Pending |

**Deliverable**: Agent retrieves relevant past experiences via semantic similarity, not keyword matching. Can reason about alternatives.

**Validation Criteria**:
- Belief retrieval finds relevant beliefs even without keyword overlap
- Counterfactual "what if" explanations appear in action failure outcomes
- Analogical transfer suggests solutions from other domains
- Beliefs accumulate rich situational context over time

---

### Phase 5: Decompose the God Class (Week 9-10)

**Goal**: Break the 3,324-line `autonomous_brain.py` into focused modules. This is prerequisite for Phase 6+ complexity.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 5.1 | Extract sense phases into `brain/sense.py` — observation gathering, platform polling | 4h | HIGH | Pending |
| 5.2 | Extract think phases into `brain/think.py` — goal generation, belief evaluation, planning | 4h | HIGH | Pending |
| 5.3 | Extract validate phases into `brain/validate.py` — moderation, safety gates, HITL | 3h | HIGH | Pending |
| 5.4 | Extract act phases into `brain/act.py` — action execution, outcome recording | 3h | HIGH | Pending |
| 5.5 | Extract learn phases into `brain/learn.py` — reflection, metacognition, belief update | 3h | HIGH | Pending |
| 5.6 | Extract self-improve into `brain/self_improve.py` — skill gap detection, code generation | 3h | HIGH | Pending |
| 5.7 | Extract trading into `brain/trading.py` — market analysis, position management | 2h | MEDIUM | Pending |
| 5.8 | Create `brain/cycle_coordinator.py` — orchestrates phases by importing from extracted modules | 4h | HIGH | Pending |
| 5.9 | Consolidate triple autonomous coder — keep only `plugins/selfimprove/autonomous_coder.py` | 4h | HIGH | Pending |
| 5.10 | Run full test suite after each extraction — regression check | 2h | HIGH | Pending |

**Deliverable**: `autonomous_brain.py` reduced to <300 lines (coordinator only). Each phase module is <400 lines with clear interfaces.

**Validation Criteria**:
- Each extracted module has its own test file
- Brain cycle runs identically before and after decomposition
- No circular imports between brain modules
- `autonomous_brain.py` < 300 lines

---

### Phase 6: Self-Improvement at Scale (Week 11-12)

**Goal**: The self-improvement pipeline generates high-quality plugins that pass real tests and solve real skill gaps. The agent writes code, tests it in an isolated sandbox, and hot-loads working plugins.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 6.1 | Docker sandbox for code execution — isolate LLM-generated code from host filesystem | 6h | CRITICAL | Pending |
| 6.2 | Implement real test generation — given a skill spec, generate pytest test cases, run in sandbox | 6h | HIGH | Pending |
| 6.3 | Add test coverage requirement — plugin must pass >=80% of generated tests before deployment | 2h | MEDIUM | Pending |
| 6.4 | Implement fall-safe deployment — if hot-load fails, revert to previous state, log failure to beliefs | 3h | MEDIUM | Pending |
| 6.5 | Wire skill gap detection to belief data — use SelfModel.what_should_i_learn() to drive gap detection | 3h | HIGH | Pending |
| 6.6 | Add skill quality scoring — rate generated plugins by test pass rate, code style, documentation | 3h | MEDIUM | Pending |
| 6.7 | Implement skill deprecation — when a generated skill fails repeatedly, remove it and update beliefs | 2h | MEDIUM | Pending |
| 6.8 | Add cumulative skill registry — track all generated skills with quality scores, usage counts, failure rates | 3h | MEDIUM | Pending |

**Deliverable**: Agent autonomously writes, tests, and deploys working plugins that solve identified skill gaps.

**Validation Criteria**:
- At least 1 auto-generated plugin passes all tests and hot-loads successfully
- Self-improvement triggers from SelfModel.what_should_i_learn() data
- Failed plugins are automatically deprecated
- Skill registry tracks quality over time

---

### Phase 7: Metacognition and Strategy Evolution (Week 13-14)

**Goal**: The agent monitors its own thinking quality, identifies systematic biases, and evolves its strategy over time.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 7.1 | Implement P14 validation gate — confidence threshold on actions, refuse actions below calibrated threshold | 4h | HIGH | Pending |
| 7.2 | Implement overconfidence correction — when SelfModel detects overconfidence, scale down predictions | 3h | MEDIUM | Pending |
| 7.3 | Implement strategy evolution — generate strategy variants, A/B test them, promote winners | 6h | HIGH | Pending |
| 7.4 | Add meta-learning — learn which strategies work in which conditions, build meta-beliefs | 4h | MEDIUM | Pending |
| 7.5 | Implement reflection depth control — simple reflection every 10 cycles, deep reflection every 100, adversarial every 1000 | 2h | LOW | Pending |
| 7.6 | Add adversarial self-critique — periodically challenge own beliefs, look for disconfirming evidence | 4h | MEDIUM | Pending |
| 7.7 | Implement strategy persistence — successful strategies stored to knowledge_graph for future retrieval | 3h | MEDIUM | Pending |

**Deliverable**: Agent has calibrated confidence, corrects overconfidence, and evolves strategy based on outcome data.

**Validation Criteria**:
- Calibration error < 0.2 after 500 cycles (BeliefEngine tracks this)
- Overconfident domains are flagged and auto-corrected
- Strategy variants produce measurably different outcomes
- Adversarial self-critique finds at least 1 mistaken belief per 1000 cycles

---

### Phase 8: Full AGI Integration (Week 15-16)

**Goal**: All systems work together seamlessly. The agent operates with genuine autonomy — perceiving, reasoning, planning, acting, learning, and self-improving as a unified loop.

| # | Task | Effort | Impact | Status |
|---|------|--------|--------|--------|
| 8.1 | Implement goal hierarchy — goals can spawn sub-goals, prioritize across levels | 4h | HIGH | Pending |
| 8.2 | Add world model integration — maintain a structured model of platform states, market conditions, social dynamics | 6h | HIGH | Pending |
| 8.3 | Implement cross-domain strategy transfer — apply market strategies to social engagement and vice versa | 4h | MEDIUM | Pending |
| 8.4 | Add long-term memory consolidation — promote frequently-validated beliefs to "core beliefs" that resist decay | 3h | MEDIUM | Pending |
| 8.5 | Implement narrative self-model — the agent can explain its own behavior, beliefs, and goals in natural language | 4h | MEDIUM | Pending |
| 8.6 | Add risk-aware decision making — factor in downside risk, not just probability | 3h | MEDIUM | Pending |
| 8.7 | Implement graceful degradation — when LLMs fail, fall back to belief-driven heuristic actions | 4h | MEDIUM | Pending |
| 8.8 | Remove all Duat/Synergy remnant code — complete migration to cognitive architecture | 4h | HIGH | Pending |
| 8.9 | Replace all `print()` with `logging` across the entire codebase (567 instances) | 6h | MEDIUM | Pending |
| 8.10 | Achieve 50% test coverage on `src/agentic/` core modules | 16h | HIGH | Pending |
| 8.11 | Prune `world_state.db` from 99MB — add archival, indexing, and vacuuming | 4h | MEDIUM | Pending |
| 8.12 | Consolidate memory layer — eliminate JSON fallback, unified SQLite schema | 8h | MEDIUM | Pending |

**Deliverable**: Agent runs autonomously with full cognitive loop, self-directed goals, calibrated confidence, and self-improvement. No legacy Duat/Synergy code remains.

**Validation Criteria**:
- 48-hour unattended run with zero crashes
- Agent generates and completes at least 5 self-directed goals
- Calibration error < 0.15 (well-calibrated)
- Self-improvement generates at least 1 working plugin
- Belief count > 100 with < 5% seed beliefs remaining
- Coverage targets: 50% on cognitive modules, 30% on brain modules

---

## Architecture Target State

```
                    ┌─────────────────────────────────┐
                    │         AGI Agent Loop           │
                    └─────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌──────▼──────┐
              │   SENSE    │ │   THINK   │ │    LEARN    │
              │            │ │           │ │             │
              │ Platform   │ │ Belief    │ │ Belief      │
              │ Polling    │ │ Predict   │ │ Update      │
              │ Trend      │ │ Self-     │ │ Self-Model  │
              │ Detection  │ │ Assess    │ │ Record      │
              │ Observation│ │ Goal      │ │ Knowledge   │
              │            │ │ Generate  │ │ Extract     │
              └─────┬──────┘ └─────┬─────┘ └──────┬──────┘
                    │              │              │
                    │    ┌─────────▼─────────┐   │
                    │    │  COGNITIVE CORE    │   │
                    │    │                     │   │
                    │    │  BeliefEngine       │   │
                    │    │  SelfModel          │   │
                    │    │  GoalPlanner        │   │
                    │    │  KnowledgeGraph     │   │
                    │    │  CognitiveIntegr.   │   │
                    │    └─────────┬─────────┘   │
                    │              │              │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼──────┐
              │  VALIDATE  │ │    ACT    │ │  IMPROVE   │
              │            │ │           │ │             │
              │ Confidence │ │ Route     │ │ Skill Gap   │
              │ Gate       │ │ Execute   │ │ Detection   │
              │ Safety     │ │ Record    │ │ Code Gen    │
              │ HITL       │ │ Outcome   │ │ Test/Deploy │
              └────────────┘ └───────────┘ └─────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
              │ Episodic   │ │  World    │ │  Belief   │
              │ Memory     │ │  Model    │ │ Store     │
              │ (SQLite)   │ │ (SQLite)  │ │ (JSON)    │
              └────────────┘ └───────────┘ └───────────┘
```

---

## Key Metrics to Track

| Metric | Current | Phase 1 Target | Phase 8 Target | Measurement |
|--------|---------|----------------|----------------|-------------|
| Validated beliefs | 1 | 20+ | 100+ | `len([b for b in beliefs if prediction_count > 0])` |
| Calibration error | Unknown | < 0.25 | < 0.15 | `belief_engine.get_calibration_report()['mean_error']` |
| Capabilities tracked | 1 | 10+ | 50+ | `len(self_model.capabilities)` |
| Self-model samples | 1 | 50+ | 500+ | `sum(c['sample_size'] for c in capabilities)` |
| Plans completed | 0 | 5+ | 50+ | `len([p for p in plans if status == 'completed'])` |
| Auto-generated plugins | 0 | 0 | 1+ | `len(auto_skill_builder.built_skills)` |
| Curiosity goals/cycle | 0 | 0 | 0.1+ | Percentage of goals from curiosity vs. external |
| Test coverage (src/agentic) | ~1.5% | 20% | 50% | pytest --cov |
| Duat/Synergy references | 68 | 68 | 0 | `grep -r '[Ss]ynergy\|[Dd]uat' src/` |
| `print()` calls (src/agentic) | 567 | 400 | 0 | `grep -r 'print(' src/agentic/` count |
| Brain line count | 3,324 | 3,300 | < 300 | `wc -l autonomous_brain.py` |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM hallucination in goal decomposition | HIGH | MEDIUM | P14 validation gate rejects low-confidence plans |
| Belief decay too aggressive | MEDIUM | HIGH | Tunable decay rate. Start conservatively (alpha=0.15) |
| Self-improvement generates broken code | HIGH | HIGH | Docker sandbox. Test coverage gate. Revert capability. |
| Circular goal spawning (curiosity loop) | MEDIUM | MEDIUM | Max goals per cycle. Goal budget. Conflict detection. |
| Calibration never converges | LOW | HIGH | Fallback to heuristic biases if calibration error > 0.5 after 1000 cycles |
| World_state.db grows unbounded | HIGH | MEDIUM | Phase 8 archival. Monitor size. Vacuum weekly. |
| Thread safety in cognitive modules | MEDIUM | HIGH | Phase 1 adds locks. RLock for shared dicts. |
| Cold start produces poor initial predictions | HIGH | MEDIUM | Seed 30+ domain-relevant beliefs. Start with conservative confidence (0.5-0.7). |

---

## Principles

1. **Learning over heuristics** — Every bias must come from data, not hardcoded rules. The Duat numbers are gone; beliefs must earn their confidence.

2. **Calibration over confidence** — An agent that knows when it's wrong is more useful than one that's confidently wrong. Track predicted vs actual relentlessly.

3. **Self-direction over reactivity** — The agent should initiate goals from curiosity and knowledge gaps, not just respond to external events.

4. **Fail safely, learn from failure** — Every failed action is data. Record it, learn from it, adjust beliefs. Never silently swallow errors.

5. **Test everything** — Every cognitive module needs tests before Phase 2. No untested code in the AGI loop.

6. **Remove, don't add** — Phase 8 removes Duat/Synergy entirely. Phase 5 decomposes the god class. Adding functionality means removing complexity elsewhere.

7. **Cold start honestly** — Seed beliefs start at moderate confidence (0.5-0.7) with prediction_count=0. They must earn higher confidence through validated predictions. No free confidence.

---

*This plan is a living document. Update after each phase completion. The path to AGI is not a destination but a direction — each phase builds on the last, and the metrics tell us whether we're moving forward.*