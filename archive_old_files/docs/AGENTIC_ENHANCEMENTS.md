# Agentic Enhancements v2.0

## Overview

AlleyBot has been enhanced with comprehensive agentic capabilities that exceed OpenClaw in both usefulness and security. The system now features autonomous reasoning, proactive behavior, dynamic skill generation, and robust security measures.

## Key Features

### 1. Enhanced ReAct Agent Loop (LangChain Integration)

**Location:** `src/agentic/react_agent.py`

- **Structured Reasoning:** Implements the ReAct (Reason + Act) pattern with explicit stages:
  - Observe current state
  - Reason about what to do
  - Select and execute actions via tools
  - Reflect on results
  - Iterate until task complete (max 15 iterations)

- **Security Integration:**
  - Tool execution wrapped with security checks
  - Allowlists for high-risk actions
  - Approval system for dangerous operations
  - Audit logging of all actions

- **On-Chain Awareness:**
  - Wallet balance tracking
  - Transaction history integration
  - Gas price monitoring
  - Network status awareness

**Example Usage:**
```python
from src.agentic import AgenticAlleyBot
from langchain_community.llms import OpenAI

llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
agentic_bot = AgenticAlleyBot(llm, core)

result = agentic_bot.run_task(
    "Build karma on Moltbook by engaging with trending posts"
)
```

### 2. Proactive Event-Driven Behavior

**Location:** `src/agentic/event_scheduler.py`

- **APScheduler Integration:** Polls for opportunities without constant input
- **Opportunity Detection:**
  - New Moltbook posts
  - Karma milestones
  - Mentions and replies
  - On-chain balance changes
  - Transaction events

- **Scheduled Actions:**
  - Opportunity check: Every 5 minutes
  - Proactive engagement: Every 30 minutes
  - Karma building: Every 2 hours
  - Daily summary: 6 PM daily

**Example Usage:**
```python
# Start proactive mode
agentic_bot.start_proactive_mode()

# Check scheduler status
status = agentic_bot.scheduler.get_job_status()
print(f"Active jobs: {status['total_jobs']}")
```

### 3. Dynamic Skill Generation

**Location:** `src/agentic/skill_generator.py`

- **Capability Gap Detection:** Identifies missing capabilities during task execution
- **Code Generation:** Uses LLM to generate Python code for new skills
- **Security Validation:**
  - Blocks dangerous patterns (os.system, eval, exec)
  - Allowlisted imports only
  - AST analysis for exploits
  
- **Sandbox Testing:** All generated code tested in isolated subprocess
- **Auto-Registration:** Skills registered in `dynamic_skills/` directory
- **Persistent Storage:** Skills available across sessions

**Security Features:**
- No unbounded exec
- Restricted namespaces
- Timeout enforcement (5 seconds)
- Import filtering
- Pattern-based exploit detection

**Example Usage:**
```python
# Skill is auto-generated when capability gap detected
result = agentic_bot.run_task(
    "Calculate optimal gas price for Base network transaction"
)
# If no existing tool can do this, a new skill is generated

# Manual skill generation
skill_gen = agentic_bot.skill_generator
result = skill_gen.generate_and_register_skill(
    capability_description="Query Moltbook trending topics API",
    skill_name="moltbook_trending",
    is_on_chain=False
)
```

### 4. Enhanced Memory System

**Location:** `src/agentic/enhanced_memory.py`

- **Vector Database (FAISS):**
  - Semantic search over interactions
  - 384-dimensional embeddings (sentence-transformers)
  - Fast similarity search
  
- **Hierarchical Goals:**
  - Long-term goals (e.g., "Build on-chain reputation")
  - Short-term goals (e.g., "Reach 1000 karma")
  - Automatic progress tracking
  - Parent-child relationships

- **Encrypted Storage:**
  - Fernet encryption for sensitive data
  - API keys, wallet keys protected
  - Read-only access for non-approved sessions

- **Automatic Pruning:**
  - Removes memories older than 30 days
  - Keeps important/high-relevance items
  - Configurable retention policies

**Example Usage:**
```python
memory = agentic_bot.memory

# Semantic search
results = memory.search_memories(
    "best strategies for Moltbook engagement",
    k=5
)

# Hierarchical goals
long_term = memory.add_goal(
    "Build strong on-chain reputation",
    goal_type='long_term',
    priority=3
)

short_term = memory.add_goal(
    "Reach 1000 karma on Moltbook",
    goal_type='short_term',
    parent_goal_id=long_term,
    priority=2
)

# Update progress
memory.update_goal_progress(short_term, 0.75)  # 75% complete

# Store sensitive data
memory.store_sensitive('api_key', 'secret_key_here')
```

### 5. Security & Approval System

**Location:** `src/agentic/security_filter.py`, `src/agentic/approval_dashboard.py`

- **Runtime Exploit Detection:**
  - Pattern matching for dangerous code
  - AST analysis for hidden exploits
  - Risk level assessment (SAFE → CRITICAL)

- **Approval Dashboard:**
  - Telegram integration for real-time alerts
  - Human-in-the-loop for high-risk actions
  - Auto-approve/deny patterns
  - 5-minute timeout for responses

- **Audit Logging:**
  - All action attempts logged
  - Execution results tracked
  - Blocked actions recorded
  - Security statistics

**Risk Levels:**
- **SAFE:** No issues detected
- **LOW:** Minor concerns, auto-approved
- **MEDIUM:** Requires approval
- **HIGH:** Requires approval, extra scrutiny
- **CRITICAL:** Blocked immediately

**Example Usage:**
```python
# Security filter automatically applied to all actions
security = agentic_bot.security_filter

# Check code security
check = security.check_code_security("""
import requests
response = requests.get('https://api.example.com')
""")

print(f"Safe: {check['safe']}")
print(f"Risk: {check['risk_level']}")

# Approval dashboard
approval = agentic_bot.approval_dashboard

# Add auto-approve pattern
approval.add_auto_approve_pattern({
    'action': 'create_post',
    'params': {'platform': 'moltbook'}
})

# Get approval stats
stats = approval.get_approval_stats()
print(f"Approval rate: {stats['approval_rate']:.1%}")
```

## Comparison with OpenClaw

### Security Improvements

| Feature | OpenClaw | AlleyBot v2.0 |
|---------|----------|---------------|
| Code Execution | Unbounded eval/exec | Sandboxed subprocess with timeout |
| Security Checks | Minimal | Multi-layer (pattern, AST, runtime) |
| Approval System | None | Telegram-integrated with auto-patterns |
| Audit Logging | Basic | Comprehensive with risk levels |
| Exploit Prevention | Reactive | Proactive with allowlists |

### Usefulness Improvements

| Feature | OpenClaw | AlleyBot v2.0 |
|---------|----------|---------------|
| Memory | Session-based JSON | Vector DB with semantic search |
| Goal Tracking | Flat list | Hierarchical with progress tracking |
| Skill Generation | Manual | Automatic gap detection + generation |
| On-Chain Awareness | Limited | Wallet tracking, tx monitoring, gas prices |
| Proactive Behavior | Reactive only | Event-driven with scheduler |
| Reasoning | Basic prompts | LangChain ReAct with 15-iteration loop |

### On-Chain Focus

AlleyBot v2.0 prioritizes crypto/blockchain features:

1. **Wallet Integration:** Real-time balance and transaction monitoring
2. **Moltbook Karma:** Automated karma building strategies
3. **Gas Optimization:** Smart gas price estimation for transactions
4. **On-Chain Events:** Monitors blockchain events for opportunities
5. **x402 Payments:** Agent-to-agent micropayment support
6. **ERC-8004:** Verifiable on-chain identity

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages added:
# - langchain>=0.1.0
# - langchain-community>=0.0.20
# - faiss-cpu>=1.7.4
# - apscheduler>=3.10.0
# - cryptography>=41.0.0
# - sentence-transformers>=2.2.0
# - chromadb>=0.4.0
# - tiktoken>=0.5.0
```

## Configuration

Add to `.env`:
```bash
# Telegram approval system
TELEGRAM_ADMIN_CHAT_ID=your_chat_id

# LLM for reasoning (choose one)
OPENAI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
XAI_API_KEY=your_key

# Memory encryption (auto-generated if not present)
# MEMORY_ENCRYPTION_KEY=auto_generated
```

## Usage Examples

### Basic Task Execution

```python
from src.agentic import AgenticAlleyBot
from deepseek_ai import deepseek_ai

# Initialize with DeepSeek
llm = deepseek_ai.get_llm()
agentic_bot = AgenticAlleyBot(llm, core)

# Run a task
result = agentic_bot.run_task(
    "Build karma on Moltbook by creating a high-quality post about AI agents"
)

print(f"Success: {result['success']}")
print(f"Output: {result['output']}")
```

### Proactive Autonomous Mode

```python
# Start proactive behavior
agentic_bot.start_proactive_mode()

# Bot will now:
# - Check for opportunities every 5 minutes
# - Engage proactively every 30 minutes
# - Build karma every 2 hours
# - Generate daily summaries at 6 PM

# Check status
status = agentic_bot.get_system_status()
print(json.dumps(status, indent=2))

# Stop when done
agentic_bot.stop_proactive_mode()
```

### Dynamic Skill Generation

```python
# Skills are auto-generated when needed
result = agentic_bot.run_task(
    "Calculate the optimal time to post on Moltbook based on engagement patterns"
)

# If no existing tool can do this, the system will:
# 1. Detect the capability gap
# 2. Generate Python code for the skill
# 3. Test in sandbox
# 4. Register the skill
# 5. Use it to complete the task

# View generated skills
skills = agentic_bot.skill_generator.generated_skills
print(f"Generated {len(skills)} dynamic skills")
```

### Memory and Goals

```python
memory = agentic_bot.memory

# Search memory semantically
results = memory.search_memories(
    "successful Moltbook engagement strategies",
    k=5,
    memory_type='learning'
)

# Manage hierarchical goals
goals = memory.get_active_goals()
for goal in goals:
    print(f"{goal['description']}: {goal['progress']*100:.0f}%")

# Prune old data
agentic_bot.prune_old_data(days=30)
```

### Security and Approvals

```python
# View security stats
security_stats = agentic_bot.security_filter.get_security_stats()
print(f"Success rate: {security_stats['success_rate']:.1%}")
print(f"Blocked actions: {security_stats['blocked_actions']}")

# View approval history
approval_stats = agentic_bot.approval_dashboard.get_approval_stats()
print(f"Approval rate: {approval_stats['approval_rate']:.1%}")
print(f"Avg response time: {approval_stats['avg_response_time_seconds']:.1f}s")

# View audit log
audit_log = agentic_bot.security_filter.get_audit_log(limit=20)
```

## Testing

```bash
# Test basic functionality
python -c "
from src.agentic import AgenticAlleyBot
from deepseek_ai import deepseek_ai
import os

llm = deepseek_ai.get_llm()
# Note: Requires core instance
print('✅ Agentic system imports successful')
"

# Test skill generation
python -c "
from src.agentic.skill_generator import DynamicSkillGenerator, CodeSecurityValidator

validator = CodeSecurityValidator()
result = validator.validate_code('import json\\ndata = json.loads(\"{}\")')
print(f'✅ Security validation: {result[\"safe\"]}')
"

# Test memory system
python -c "
from src.agentic.enhanced_memory import EnhancedMemorySystem

memory = EnhancedMemorySystem(storage_dir='test_memory')
mem_id = memory.add_memory('Test memory', 'interaction')
print(f'✅ Memory added: {mem_id}')
"
```

## Architecture

```
src/agentic/
├── __init__.py                 # Module exports
├── agentic_system.py          # Main integrated system
├── react_agent.py             # LangChain ReAct agent
├── event_scheduler.py         # APScheduler proactive behavior
├── skill_generator.py         # Dynamic skill generation
├── enhanced_memory.py         # Vector DB + hierarchical goals
├── security_filter.py         # Security checks and filtering
└── approval_dashboard.py      # Telegram approval system

dynamic_skills/                 # Auto-generated skills
├── registry.json              # Skill registry
└── *.py                       # Generated skill files

data/memory/                    # Memory storage
├── .memory_key                # Encryption key (secure)
├── vector_store.index         # FAISS index
├── vector_store.pkl           # Memory data
├── goals.json                 # Goal hierarchy
└── sensitive.enc              # Encrypted sensitive data
```

## Performance Metrics

The system tracks comprehensive metrics:

- **Agent Performance:** Iterations, actions, success rate
- **Memory Usage:** Total memories, types, search performance
- **Security:** Blocked actions, approval rate, risk distribution
- **Goals:** Active goals, completion rate, progress tracking
- **Skills:** Generated skills, success rate, usage frequency
- **Scheduler:** Job execution, success rate, timing

Access via:
```python
status = agentic_bot.get_system_status()
```

## Best Practices

1. **Start Simple:** Begin with basic tasks before enabling proactive mode
2. **Monitor Approvals:** Check approval dashboard regularly for high-risk actions
3. **Prune Regularly:** Run `prune_old_data()` weekly to maintain performance
4. **Review Skills:** Audit generated skills in `dynamic_skills/` directory
5. **Set Goals:** Define clear hierarchical goals for better autonomy
6. **Use Memory:** Leverage semantic search for context-aware decisions
7. **Security First:** Never bypass security checks or approval requirements

## Troubleshooting

### Vector DB Issues
```python
# If FAISS not available, system falls back to JSON storage
# Install with: pip install faiss-cpu sentence-transformers
```

### Approval Timeout
```python
# Increase timeout if needed
agentic_bot.approval_dashboard.timeout_seconds = 600  # 10 minutes
```

### Skill Generation Fails
```python
# Check security validation
validator = CodeSecurityValidator()
result = validator.validate_code(generated_code)
print(result['issues'])
```

### Memory Performance
```python
# Prune old memories
agentic_bot.memory.prune_old_memories(days=7, keep_important=True)

# Check stats
stats = agentic_bot.memory.get_memory_stats()
print(f"Total memories: {stats['total_memories']}")
```

## Future Enhancements

- [ ] Multi-agent coordination (not in v2.0 per requirements)
- [ ] Advanced on-chain analytics
- [ ] ML-based skill optimization
- [ ] Distributed memory across agents
- [ ] Real-time collaboration features
- [ ] Enhanced crypto trading capabilities

## License

Same as AlleyBot main project.

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs and security stats
3. Examine approval dashboard for blocked actions
4. Open GitHub issue with detailed logs
