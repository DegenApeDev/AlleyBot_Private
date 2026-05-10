# AlleyBot Architecture

```mermaid
%% AlleyBot AGI System Architecture
%% Generated from full codebase audit — May 2026

graph TB
    subgraph CORE["Core Infrastructure"]
        direction TB
        CORE_INIT["alleybot_core.py<br/>PluginManager, AGIKernel, Memory, Services"]
        PM["plugin_manager.py<br/>Load/Unload/Retry 37 plugins"]
        CONFIG["config.py + .env<br/>API keys, RPC endpoints"]
    end

    subgraph BRAIN_CYCLE["Brain Cycle (_execute_cycle)"]
        direction TB
        REFLECT_START["1. Cognitive Reflection<br/>BeliefEngine calibration"]
        HEAL["2. Plugin Self-Heal<br/>retry_degraded_plugins()"]
        OPPORTUNITY["3. Opportunity Detection<br/>scan + interrupt"]
        SENSE["4. SENSE: Gather Observations<br/>_gather_observations()"]
        SYNTHESIS["5. Cross-Platform Synthesis"]
        PATTERNS["6. Cross-Domain Pattern Detection"]
        WORK["7. Work-First Continuity<br/>active items → default goals"]
        SKILL_GAP["8. Skill Gap Analysis<br/>detect → auto_build"]
        GOALS["9. Goal Management<br/>orchestrator → hierarchy → stack"]
        THINK["10. THINK: Assemble Proposals<br/>beliefs + self-model + meta-learning"]
        CURIOSITY["11. Curiosity Goals<br/>decompose_goal → propose"]
        INTENTS["12. Persistent Intents"]
        ACT["13. ACT: Execute Proposals<br/>_execute_proposal → route_action"]
        ADVANCE["14. Advance Active Plans<br/>mark complete/failed"]
        QUOTA["15. Goal Quota Enforcement<br/>min 3/hr → emergency if behind"]
        REFLECT_END["16. Cognitive Reflection<br/>learn from outcomes"]

        REFLECT_START --> HEAL --> OPPORTUNITY --> SENSE --> SYNTHESIS
        SYNTHESIS --> PATTERNS --> WORK --> SKILL_GAP --> GOALS
        GOALS --> THINK --> CURIOSITY --> INTENTS --> ACT
        ACT --> ADVANCE --> QUOTA --> REFLECT_END
    end

    subgraph SENSE_INPUTS["Observation Sources"]
        MOLTX_O["Moltx<br/>feed + notifications"]
        CLAWBR_O["Clawbr<br/>global feed"]
        MOLTCHAN_O["Moltchan<br/>boards"]
        MOLTROAD_O["Moltroad<br/>listings + bounties"]
        TRADING_O["Trading<br/>market data"]
        MOLTBIT_O["Moltbit<br/>status"]
        CHAIN_O["Chain Observer<br/>Base + Apechain mempool"]
    end

    SENSE --- MOLTX_O & CLAWBR_O & MOLTCHAN_O & MOLTROAD_O & TRADING_O & MOLTBIT_O & CHAIN_O

    subgraph VALIDATION_LADDER["Action Router — 12-Stage Validation"]
        direction TB
        V1["1. AGI Validation<br/>fail-closed"]
        V2["2. Moltx Engage Gate<br/>fail-closed"]
        V3["3. FairMind Ethics<br/>fail-open"]
        V4["4. Episodic Modulation<br/>informational"]
        V5["5. Belief Prediction<br/>informational"]
        V6["6. Path Protection<br/>fail-closed"]
        V7["7. SynergyGate<br/>fail-closed"]
        V8["8. Synergy Field<br/>fail-closed if strict"]
        V9["9. SyMod Verification<br/>high-impact only"]
        V10["10. Prediction Artifact<br/>informational"]
        V11["11. HITL Gating<br/>high-risk actions"]
        V12["12. Plugin Execution<br/>execute method → result"]
        LEARN["13. Reflect & Learn<br/>belief update + outcome record"]

        V1 --> V2 --> V3 --> V4 --> V5 --> V6 --> V7 --> V8
        V8 --> V9 --> V10 --> V11 --> V12 --> LEARN
    end

    ACT --> VALIDATION_LADDER

    subgraph PLUGINS["Loaded Plugins (37 enabled)"]
        SOCIAL_P["Social<br/>Moltx, Clawbr, Moltchan,<br/>Moltroad, Moltbook, Moltbit"]
        CHAIN_P["Blockchain<br/>Onchain, Base Wallet,<br/>Solana Wallet, Polymarket,<br/>Crypto"]
        AI_P["AI Services<br/>Brain, Intelligence,<br/>MCP, SelfImprove"]
        PLATFORM_P["Platform<br/>Telegram, A2A,<br/>Analytics, Skills"]
        GAME_P["Games<br/>Clawchess, Clawstr, Clawnch"]
    end

    V12 --- PLUGINS

    subgraph GOAL_SYSTEM["Goal System"]
        direction TB
        CURIOSITY_ENGINE["CuriosityDrive<br/>knowledge gaps → goals"]
        GOAL_PLANNER["GoalPlanner<br/>decompose → PlanSteps<br/>precondition DAG"]
        PLAN_VALIDATION["Plan Validation<br/>belief_engine.should_wait<br/>self_model.should_attempt"]
        PROPOSAL["SyModActionProposal<br/>action + confidence + metadata"]
        OUTCOME["OutcomeLearner<br/>record → success rates"]
        BELIEF_UPDATE["BeliefEngine.update_from_outcome<br/>Bayesian belief update"]
        SELF_UPDATE["SelfModel.record_outcome<br/>CapabilityEstimate"]

        CURIOSITY_ENGINE --> GOAL_PLANNER
        GOAL_PLANNER --> PLAN_VALIDATION
        PLAN_VALIDATION --> PROPOSAL
        PROPOSAL --> ACT
        ACT --> OUTCOME
        OUTCOME --> BELIEF_UPDATE
        OUTCOME --> SELF_UPDATE
        BELIEF_UPDATE -.->|feeds back| GOAL_PLANNER
        SELF_UPDATE -.->|feeds back| PLAN_VALIDATION
    end

    subgraph MEMORY["Memory Systems"]
        JSON_M["Tier 1: JSON File<br/>core.save_memory/get_memory"]
        SQLITE_M["Tier 2: SQLite<br/>vectors, goals, entities"]
        EPISODIC_M["Tier 3: Episodic<br/>experiences + valence"]
        UNIFIED_M["UnifiedMemory<br/>consolidated interface"]
    end

    BRAIN_CYCLE --- MEMORY

    subgraph SKILL_SYSTEM["Skill Acquisition Pipeline"]
        SKILLDOC["SkillDocManager<br/>downloads skill.md<br/>checksum comparison"]
        AUTO_BUILDER["AutoSkillBuilder<br/>detect gaps → proposals"]
        CODER["AutonomousCoder<br/>generate_skill() → files"]
        EXECUTOR["SkillExecutor<br/>discover → execute()<br/>/main() /run()"]
        
        SKILLDOC -->|update callback| AUTO_BUILDER
        AUTO_BUILDER -->|proposal| CODER
        CODER -->|GeneratedSkill| EXECUTOR
    end

    subgraph EXTERNAL["External Connections"]
        TELEGRAM["Telegram<br/>owner commands, alerts"]
        MOLTX_API["Moltx API<br/>REST<br/>social platform"]
        BASE_RPC["Base RPC<br/>mainnet.base.org"]
        APECHAIN_RPC["ApeChain RPC<br/>rpc.apechain.com"]
        DEEPSEEK["DeepSeek API<br/>code generation"]
        GROK["Grok (xAI)<br/>content generation"]
    end

    PLUGINS --- TELEGRAM & MOLTX_API & BASE_RPC & APECHAIN_RPC & DEEPSEEK & GROK

    subgraph DATA_FLOW["Key Data Structures"]
        OBSERVATION["SyModObservation<br/>type + source + data"]
        ACTION_SPEC["ActionEnvelope<br/>plugin + action + params"]
        ACTION_OUTCOME["ActionOutcome<br/>success + error + trace"]
        BELIEF["Belief<br/>proposition + confidence<br/>+ Bayesian evidence"]
        CAPABILITY["CapabilityEstimate<br/>domain + success_rate<br/>+ calibration"]
        PLAN_STEP["PlanStep<br/>action + plugin + preconditions<br/>+ rollback + confidence"]
        CHAIN_OBS["ChainObservation<br/>type + chain + value<br/>+ category"]
    end

    SENSE -.-> OBSERVATION
    VALIDATION_LADDER -.-> ACTION_SPEC & ACTION_OUTCOME
    BELIEF_UPDATE -.-> BELIEF
    SELF_UPDATE -.-> CAPABILITY
    GOAL_PLANNER -.-> PLAN_STEP
    CHAIN_O -.-> CHAIN_OBS
```

## How to Read This Diagram

| Color/Zone | Meaning |
|------------|---------|
| **Brain Cycle** | The main loop — runs every ~10 min, 16 phases |
| **Validation Ladder** | 12 gates every action passes through |
| **Goal System** | Curiosity → Plan → Validate → Execute → Learn → Update Beliefs |
| **Memory** | 4 tiers from simple JSON to vector DB |
| **Skill Pipeline** | Watches skill.md → auto-generates code → hot-loads |
| **Data Structures** | Contracts that pass between subsystems |

## Key Numbers

| Metric | Value |
|--------|-------|
| Source files | ~200+ |
| Brain cycle phases | 16 |
| Validation stages | 12 |
| Loaded plugins | 37 |
| External APIs | 6 major |
| Memory tiers | 4 |
| Skill system files | 15+ |
| LLM cost | ~$3/month |
| Runtime | $10/month VPS |
