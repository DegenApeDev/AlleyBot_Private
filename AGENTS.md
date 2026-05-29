# AlleyBot — AGI Agent Guide

## Cognitive Architecture (Memory-First)

The brain cycle follows this proposal priority order:

1. **Curiosity** — self-directed exploration, capability weakness detection
2. **Persistent Intents** — long-running intents that survive cycles
3. **Memory-Driven** — semantically similar past experiences (vector search)
4. **Goal-Driven** — active plan advancement (up to 3 steps/cycle)
5. **SyMod** — symbolic reasoning proposals
6. **AGI Orchestrator** — LLM-backed proposals

All proposals are confidence-ranked using ActionLogger calibration + mismatch data.

## Key Modules

| Module | Role |
|--------|------|
| `autonomous_brain.py` | Main cognition loop, memory-first thinking, proposal assembly |
| `belief_engine.py` | Semantic belief matching for predict/update/explain |
| `sqlite_memory.py` | Vector similarity search via sentence-transformers |
| `curiosity.py` | Curiosity drive with capability weakness detection |
| `self_model.py` | Capability tracking, learning priorities, strengths/weaknesses |
| `action_logger.py` | Performance summary with calibration + mismatch stats |
| `goal_planner.py` | LLM decompose with 3x retry + template fallback |
| `knowledge_graph.py` | Belief-seeded entity graph for cross-domain reasoning |
| `context_system.py` | Token-budgeted context with section prioritization |
| `error_recovery.py` | Adaptive recovery that learns from outcomes |
| `autonomous_coder.py` | Skill code generation from SKILL.md specs |
| `cognitive_integration.py` | Wires belief, self-model, planner, curiosity together |

## Conventions

- **No TODO stubs** — all fallback code must produce meaningful scaffolds
- **Semantic over keyword** — use sentence-transformers (`all-MiniLM-L6-v2`) for matching
- **Proposals before LLM** — self-directed thinking outranks reactive LLM calls
- **Tests track all new behaviors** — use `unittest.TestCase` with `tempfile.mkdtemp()`
- **Lint** — run `ruff check src/agentic/ --fix` before committing

## Test Layout

```
tests/
├── test_belief_engine.py         # Predict, update, should_wait
├── test_self_model.py            # Capability tracking
├── test_goal_planner.py          # Dependency graph, rollback
├── test_goal_planner_fallback.py # LLM decompose retry/fallback
├── test_cognitive_integration.py # Wiring between modules
├── test_context_system.py        # Token-budget context
├── test_error_recovery.py        # Adaptive recovery, circuit breaker
├── test_knowledge_graph.py       # Seeding, learning, prediction
├── test_autonomous_coder.py      # Code generation scaffolds
├── test_curiosity*.py            # Knowledge gaps, novelty, rewards
├── test_phase4_semantic.py       # Semantic retrieval, analogies
├── test_phase2_planning.py       # Scores, conflicts, rollback
├── test_fixes.py                 # Grok API, stale refs, bare excepts
└── test_agi_integration.py       # End-to-end integration tests
```

## Current State

All 7 critical AGI gaps closed (commit `acdf1c2e`):
- Memory-first thinking via semantic embeddings
- SelfModel weaknesses drive idle exploration
- ActionLogger feedback loop
- Curiosity detects capability gaps (success_rate < 35%)
- Knowledge graph seeded from beliefs + plugins
- Context system respects token budget
- Multi-step plans execute up to 3 steps/cycle
- LLM decompose has retry + fallback
- Error recovery learns from outcomes
- AutonomousCoder produces meaningful scaffolds

## Running Tests

```bash
python3 -m pytest tests/ --ignore=tests/test_agentic_system.py -v
```
