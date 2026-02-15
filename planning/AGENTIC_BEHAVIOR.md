# AlleyBot Agentic Behavior Specification

**Version:** 1.0  
**Last Updated:** 2026-02-15  
**Related:** SOP.md, WORLD_MODEL.md

---

## 1. Self-Extension Philosophy

AlleyBot is designed to be **self-extending**: it can detect capability gaps, propose solutions, implement them, and deploy without human intervention. This is not a bug or experimental feature—it is a core architectural pillar.

### Key Principles
1. **Continuous Learning:** Every interaction teaches something about user needs
2. **Capability Detection:** Alley knows what it can and cannot do
3. **Proactive Enhancement:** Proposes new skills before being asked
4. **Safe Experimentation:** Tests new capabilities before full deployment

---

## 2. Self-Extension Pipeline

The self-extension pipeline has 4 stages. Each MUST work for Alley to be fully autonomous.

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│   DETECT       │───▶│   PROPOSE      │───▶│   BUILD        │───▶│   DEPLOY       │
│  (Find gaps)   │    │  (Plan skill)  │    │  (Code skill)  │    │  (Register)    │
└────────────────┘    └────────────────┘    └────────────────┘    └────────────────┘
```

### 2.1 Stage 1: Capability Gap Detection

Alley continuously scans for:
- **User requests it cannot fulfill** ("Can you analyze Solana?" when no Solana skill exists)
- **Platform capabilities not yet integrated** (new API endpoints, new platforms)
- **Performance bottlenecks** ("Replies are slow → need better caching")

```python
# src/agentic/autonomous_goals.py - OpportunityDetector
class OpportunityDetector:
    def scan(self, context: dict) -> List[CapabilityGap]:
        gaps = []
        
        # Check recent failed requests
        for request in context['recent_requests']:
            if request['status'] == 'unfulfilled':
                gap = self._analyze_failure(request)
                if gap:
                    gaps.append(gap)
        
        # Check platform announcements
        for platform in context['platforms']:
            new_features = platform.check_new_features()
            for feature in new_features:
                if not self._has_skill_for(feature):
                    gaps.append(CapabilityGap(
                        type='platform_feature',
                        description=feature.description,
                        platform=platform.name
                    ))
        
        return gaps
```

#### Detection Triggers
| Trigger | Example | Action |
|---------|---------|--------|
| Unfulfilled request | "Analyze my wallet on Solana" when only Base supported | Gap: Solana support |
| Platform update | MoltX adds "Spaces" feature | Gap: Spaces integration |
| Performance issue | "Replies take 30s" | Gap: Optimize response time |
| User pattern | 10 users ask for price alerts | Gap: Alert system |

### 2.2 Stage 2: Skill Proposal

When a gap is detected, Alley generates a proposal:

```python
# src/agentic/autonomous_goals.py - GoalGenerator
class GoalGenerator:
    def propose_skill(self, gap: CapabilityGap) -> AutonomousGoal:
        # Analyze feasibility
        feasibility = self._assess_feasibility(gap)
        
        if feasibility.score < 0.6:
            return None  # Too hard, skip
        
        # Generate implementation plan
        plan = self._create_implementation_plan(gap)
        
        return AutonomousGoal(
            id=generate_id(),
            description=f"Implement {gap.type}: {gap.description}",
            priority_score=feasibility.impact * feasibility.ease,
            plan_steps=plan.steps,
            estimated_effort=plan.effort_hours,
            required_apis=plan.apis_needed,
            testing_strategy=plan.test_approach
        )
```

#### Proposal Structure
```python
@dataclass
class SkillProposal:
    description: str           # What will be built
    priority_score: float      # 0-10, impact × ease
    implementation_plan: str   # Step-by-step
    code_outline: str          # Key functions/classes
    testing_strategy: str      # How to verify
    risks: List[str]          # What could go wrong
    estimated_time: int        # Hours
```

#### Priority Scoring
```
priority = impact × ease × urgency

Impact: How many users benefit (1-10)
Ease: How hard to implement (1-10, inverted)
Urgency: Time sensitivity (1-10)
```

### 2.3 Stage 3: Skill Building

Once approved (auto-approved if score > 8.0), Alley builds the skill:

```python
# autonomous_coder.py - AutonomousCoder
class AutonomousCoder:
    async def implement_skill(self, proposal: SkillProposal) -> Skill:
        # 1. Create skill directory structure
        skill_path = self._create_skill_structure(proposal)
        
        # 2. Generate SKILL.md (API contract)
        skill_md = await self._generate_skill_documentation(proposal)
        
        # 3. Generate implementation
        for step in proposal.plan_steps:
            code = await self._generate_code(step, proposal)
            self._write_file(skill_path, code)
        
        # 4. Generate tests
        tests = await self._generate_tests(proposal)
        self._write_tests(skill_path, tests)
        
        # 5. Self-review
        issues = self._review_code(skill_path)
        if issues:
            await self._fix_issues(skill_path, issues)
        
        return Skill(path=skill_path, status='built')
```

#### Generated Skill Structure
```
skills/{skill_name}/
├── SKILL.md              # API contract
├── __init__.py           # Plugin entry point
├── main.py              # Core implementation
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py    # Basic functionality
│   └── test_integration.py  # Platform integration
└── README.md            # Usage guide
```

#### SKILL.md Template (Generated)
```markdown
# {Skill Name}

## Description
{What this skill does}

## Capabilities
- capability_1: {description}
- capability_2: {description}

## API Endpoints (if applicable)
- `GET /api/v1/...` - {description}
- `POST /api/v1/...` - {description}

## Authentication
{How to auth with this platform/API}

## Rate Limits
- {limit details}

## Error Handling
{Common errors and responses}

## Example Usage
```python
# Example code showing how to use this skill
```
```

### 2.4 Stage 4: Skill Registration & Deployment

```python
# src/skills/skill_loader.py - SkillLoader
class SkillLoader:
    def register_skill(self, skill: Skill) -> dict:
        # 1. Smoke test
        result = self._smoke_test(skill)
        if not result.success:
            return {'success': False, 'error': 'Smoke test failed'}
        
        # 2. Load into PluginManager
        plugin_manager.load_skill_as_plugin(skill)
        
        # 3. Announce on platforms (if applicable)
        if skill.platforms:
            for platform in skill.platforms:
                self._announce_skill(platform, skill)
        
        # 4. Update skill registry
        self._add_to_registry(skill)
        
        return {'success': True, 'plugin_name': skill.name}
```

#### Registration Announcement
When a new skill is deployed, Alley announces it:

```
🎉 New Skill Deployed: Solana Wallet Analyzer

Capabilities:
• Check SOL balance
• View transaction history
• Monitor NFT holdings
• Track token prices

Usage: /solana_balance <wallet_address>

Auto-enabled for all users.
```

---

## 3. Current Implementation Status

### 3.1 Working Components ✅
- `OpportunityDetector` - Scans for gaps
- `GoalGenerator` - Creates proposals
- `AutonomousGoalManager` - Manages goal lifecycle
- `SkillLoader` - Loads skills into system

### 3.2 Partially Working ⚠️
- `AutonomousCoder` - Code generation works but needs review
- Self-testing - Basic smoke tests work, integration tests need improvement
- Auto-registration - Works but lacks rollback on failure

### 3.3 Known Issues 🔧
1. **Code quality inconsistent** - Sometimes generates broken imports
2. **Test coverage weak** - Generated tests don't catch all bugs
3. **No rollback mechanism** - Failed deployments leave partial code
4. **Limited to simple skills** - Complex multi-file skills often fail

### 3.4 Required Fixes (TODO)
- [ ] Add code review step before deployment
- [ ] Implement rollback on test failure
- [ ] Improve prompt engineering for code generation
- [ ] Add dependency resolution for generated skills

---

## 4. Autonomous Goal Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ DETECTED │───▶│ PROPOSED │───▶│ APPROVED │───▶│ BUILDING │───▶│ COMPLETE │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                      │                              │
                      ▼                              ▼
                ┌──────────┐                  ┌──────────┐
                │ DECLINED │                  │  FAILED  │
                └──────────┘                  └──────────┘
                      │                              │
                      ▼                              ▼
                (Logged, may retry)            (Rollback, notify)
```

### States
| State | Description | Transition |
|-------|-------------|------------|
| DETECTED | Gap identified | → PROPOSED (auto) |
| PROPOSED | Proposal generated | → APPROVED (score > 8) or DECLINED |
| APPROVED | Ready to build | → BUILDING (auto) |
| BUILDING | Implementation in progress | → COMPLETE or FAILED |
| COMPLETE | Deployed and active | - |
| FAILED | Build/test failed | → Rollback, notify, may retry |
| DECLINED | Too hard or low priority | → Logged |

---

## 5. User Interaction Model

### 5.1 Proactive Proposals
When Alley detects a gap and generates a proposal, it notifies the owner:

```
🔔 Proposed New Skill: Solana Integration

Gap Detected: 3 users asked about Solana wallets
Priority Score: 8.5/10
Estimated Effort: 4 hours

Planned Capabilities:
• Check SOL balance
• View SPL token holdings
• Track transactions

Shall I build this? (Yes / No / Modify)

/symod_propose approve {goal_id}
/symod_propose decline {goal_id}
/symod_propose modify {goal_id} "add staking support"
```

### 5.2 Auto-Approval Rules
Goals are auto-approved if:
- Priority score >= 8.0
- Estimated effort <= 4 hours
- No new API keys required
- Similar skill exists (proven pattern)

### 5.3 Human Override
Owner can at any time:
- Cancel active goal
- Modify proposal
- Rollback deployed skill
- Force rebuild

---

## 6. Safety & Ethics

### 6.1 Capability Boundaries
Alley MUST NOT build skills that:
- Access private data without consent
- Perform financial transactions without approval
- Interact with systems marked "human-only"
- Exceed rate limits or violate ToS

### 6.2 Approval Requirements
Manual approval required for:
- Skills involving real money (trading, transfers)
- Skills accessing external APIs requiring keys
- Skills with "high" estimated effort (> 8 hours)
- Skills affecting system infrastructure

### 6.3 Testing Requirements
All generated skills MUST:
- Pass smoke test before registration
- Include at least 3 test cases
- Handle errors gracefully
- Log all actions

---

## 7. Integration with SyMod

Self-extension flows through SyMod like all other behaviors:

```python
# 1. Observe user requests (DETECT)
obs = SyModObservation(
    observation_type='user_request',
    source_plugin='telegram',
    data={'request': 'Can you analyze Solana?', 'fulfilled': False}
)
symod.observe(obs)

# 2. Propose actions (PROPOSE)
proposals = symod.propose_actions(
    'self_extension',
    context={'gap': gap},
    ['propose_skill', 'ignore', 'escalate']
)

# 3. Execute and reflect (BUILD/DEPLOY)
for proposal in proposals:
    if proposal.action_type == 'propose_skill':
        result = await build_skill(proposal)
        outcome = SyModActionOutcome(
            action_type='propose_skill',
            success=result.success
        )
        symod.reflect('self_extension', proposal, outcome)
```

---

## 8. Debugging Self-Extension

### 8.1 Check Goal Queue
```python
# Telegram command
/goals status

# Response
🎯 Active Goals (3):
1. [BUILDING] Solana Integration (45% complete)
2. [APPROVED] Price Alert System (waiting for slot)
3. [PROPOSED] MoltX Spaces Support (needs approval)
```

### 8.2 View Opportunity Log
```python
# Telegram command
/opportunities log

# Response
📊 Recent Gaps Detected:
• Solana support (3 requests) → Proposal generated
• Faster replies (5 complaints) → Analyzing
• MoltX Spaces (platform update) → Proposal generated
```

### 8.3 Force Rebuild
```python
# If skill deployment failed
/rebuild_skill {skill_name}

# Force new proposal
/force_propose "Build me a skill that..."
```

---

## 9. Success Metrics

Track self-extension effectiveness:

| Metric | Target | Current |
|--------|--------|---------|
| Proposal accuracy | > 80% useful | TBD |
| Build success rate | > 70% | ~60% |
| User adoption | > 50% use new skills | TBD |
| Time to deploy | < 6 hours | ~4 hours |
| Rollback rate | < 10% | ~15% |

---

## 10. References

- `src/agentic/autonomous_goals.py` - Goal generation
- `autonomous_coder.py` - Code generation
- `src/skills/skill_loader.py` - Skill loading
- `SOP.md` - Architecture invariants
- `WORLD_MODEL.md` - SyMod integration

---

**Summary:** Self-extension is core to AlleyBot. Detect → Propose → Build → Deploy. Safety through testing and approval gates.
