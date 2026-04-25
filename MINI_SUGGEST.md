# MINI_SUGGEST.md — Street Smart Evolving Hacker AGI

## Vision
Create an AGI that's **street smart** — learns from real-world outcomes, adapts on the fly, finds creative solutions, and knows when to pivot. Can't be tricked, manipulated, or caught off guard.

> **Hacker ≠ Destructive** — Wozniak style: resourceful, creative, efficient. Finding clever workarounds. Breaking things apart to understand them.

---

## What "Street Smart" Means Here

| Street Smart | AGI Equivalent |
|--------------|-----------------|
| Can't be tricked | Detect social engineering, manipulation attempts |
| Not easily manipulated | Skeptical of unverified info, validate before acting |
| Always has backup plan | Alternative paths ready when primary fails |
| Knows when to pivot | Switches strategy fast when compromised |
| Reads between lines | Understands subtext, detects FUD, separates signal from noise |
| Trust but verify | Validates claims before forming beliefs |

---

## Gap Analysis — What We Have vs What's Needed

### ✅ We Have (Foundation)
- BeliefEngine (Bayesian belief updating)
- SelfModel (capability calibration)
- CuriosityDrive (self-directed goals)
- StrategyEvolver (mutation + selection)
- Semantic memory + embeddings
- Skill gap detection → code generation
- 166 tests

### ❌ We're Missing (The "Street Smart" Layer)

| Gap | Why It Matters | Hacker Analogy |
|-----|----------------|-----------------|
| **Real-time counter-strategy** | Can't adapt when something blocks it | Finding workaround when one path is blocked |
| **Failure pattern recognition** | Misses "this always fails in situation X" | Learning what doesn't work in certain contexts |
| **Adaptive tool mixing** | Uses one tool at a time | Combining tools creatively (nmap + grep + curl) |
| **Exploit identification** | Doesn't find vulnerabilities in its own workflows | Pentesting its own thinking process |
| **Fast pivot capability** | Slow to change strategy | "That didn't work? Try this instead" in seconds |
| **Learned heuristics** | Relies on templates/LLM | Builds its own "rules of thumb" from experience |
| **Adversarial resilience** | Can't handle hostile inputs | Handling trolls, FUD, market manipulation |

---

## Next Steps — Priority Order

### P0 — Real-World Learning Loop (Critical)
```
CURRENT: BeliefEngine has seed beliefs, needs validation
NEED: Actually record outcomes from EVERY action, update beliefs, learn

Implementation:
1. Force outcome recording on EVERY action execution
2. Add "was this useful?" feedback loop (manual or inferred)
3. Build belief chains: "A → B → success" patterns
```

### P1 — Fast Fail / Fast Pivot
```
CURRENT: Tries same thing multiple times before changing
NEED: Max 3 retries with different approach

Implementation:
1. Add retry_limit per action type (default: 3)
2. On fail: generate 3 alternative approaches immediately
3. Track "tried X, Y failed, try Z" sequences in beliefs
```

### P2 — Exploit Discovery (Self-Hacking)
```
CURRENT: Only fixes skill gaps from failures
NEED: Proactively finds weaknesses in its own workflows

Implementation:
1. Add "audit_my_workflow()" - finds bottlenecks, redundancies
2. Mirror reflection - "if I were attacking myself, what would I exploit?"
3. Generate "attack vectors" against its own planning
```

### P3 — Tool Mixing / Chaining
```
CURRENT: Uses one tool per action
NEED: Compose tool chains like a hacker

Implementation:
1. Add tool_chain capability to action_router
2. "Get data → transform → post" as single logical action
3. Track successful chains, replicate them
```

### P4 — Adaptive Heuristics (Street Smarts)
```
CURRENT: Templates from LLM, not learned
NEED: Build own "rules of thumb" from experience

Implementation:
1. Extract patterns: "when X happens, do Y" from outcome data
2. Store as "heuristic beliefs" - faster than LLM calls
3. Make heuristics editable by the agent itself
```

### P5 — Adversarial Resilience
```
CURRENT: Handles errors gracefully, but not hostile inputs
NEED: Detects and responds to deliberate attacks

Implementation:
1. "Is this input trying to manipulate me?" (prompt injection detection)
2. Market FUD detection - separate signal from noise
3. Troll/attack detection on social platforms
```

---

## Quick Wins (This Week)

1. **Outcome Density** — Ensure every action logs outcome, every outcome updates belief
2. **Pivot Counter** — Add `consecutive_failures` to action types, auto-pivot after 3
3. **Pattern Hunter** — Run nightly: "what sequences of actions succeeded/failed?"
4. **Chain Builder** — Add `tool_chaining` flag to action definitions

---

## Philosophy in Code

```python
# The street-smart hacker mindset:
class StreetSmartHacker:
    def attempt(self, action):
        result = action.execute()
        self.learn(result)  # Always learn
        if result.failed:
            alternatives = self.generate_alternatives(action, limit=3)
            return self.attempt(alternatives[0])  # Fast pivot
        return result
    
    def learn(self, result):
        # Extract the lesson, even from failure
        pattern = self.extract_pattern(result)
        self.beliefs.add(pattern)
        
    def generate_alternatives(self, action, limit=3):
        # Not templates - variations learned from experience
        past_failures = self.beliefs.get_failures_like(action)
        return [self.mutate(action, f) for f in past_failures[:limit]]
```

---

## Risk Control

- **Hacker != Destructive** — All changes sandboxed, validated before production
- **Street smart ≠ Manipulative** — Ethics baked in, HITL for high-risk
- **Evolving ≠ Unstable** — Core beliefs (is_core) resist accidental change

---

## References
- Current cognitive: BeliefEngine, SelfModel, CuriosityDrive, StrategyEvolver
- Phase 1-8: All foundational layers complete
- This doc: "Layer 9" — The adaptive, learning, evolving layer

---

**TL;DR**: We have the brain. Now give it street smarts. Fast fail, fast pivot, build own heuristics, audit itself, chain tools creatively.