# AlleyBot Swarm Control

## Overview

AlleyBot can now control a **swarm of sub-agents** for parallel task execution, distributed processing, and coordinated multi-agent workflows. This enables Alley to delegate tasks to specialized workers and aggregate results.

---

## Swarm Commands

### Node Management

```
/swarm_spawn <name> <capability1> [capability2] ...
```
Spawn a new swarm node with specified capabilities.

**Example:**
```
/swarm_spawn worker-5 research analysis crypto
```

```
/swarm_kill <node_id>
```
Remove a node from the swarm.

```
/swarm_list
```
Show all swarm nodes and their status.

---

### Task Delegation

```
/swarm_delegate <skill_name> <task_description> [--priority HIGH|LOW|CRITICAL] [--consensus N]
```
Delegate a task to the swarm. Automatically assigns to the best-capable idle node.

**Examples:**
```
# Basic delegation
/swarm_delegate crypto_prices "Get BTC, ETH, SOL prices"

# High priority
/swarm_delegate market_alert "Check for volatility" --priority HIGH

# Consensus (multiple nodes verify)
/swarm_delegate sentiment_analysis "Analyze market mood" --consensus 3
```

```
/swarm_result <task_id> [--wait]
```
Get the result of a delegated task.

```
/swarm_parallel <skill_name> <task> [--nodes N]
```
Execute on multiple nodes in parallel for faster results.

**Example:**
```
/swarm_parallel research "Research DeFi protocols" --nodes 5
```

---

### Status & Monitoring

```
/swarm_status
```
Show swarm overview: nodes, tasks, queue.

---

## How Swarm Works

### Architecture

```
┌─────────────────────────────────────┐
│         AlleyBot (Orchestrator)      │
│  ┌─────────────────────────────┐   │
│  │      Swarm Manager           │   │
│  │  - Task Queue                 │   │
│  │  - Node Registry              │   │
│  │  - Load Balancer              │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼───┐      ┌───▼───┐
│Node-1 │      │Node-2 │
│Research│      │Crypto │
└───┬───┘      └───┬───┘
    │               │
┌───▼───┐      ┌───▼───┐
│Node-3 │      │Node-4 │
│Social  │      │System │
└───────┘      └───────┘
```

### Node Types (Default)

When initialized, AlleyBot creates 4 default nodes:

| Node | Capabilities | Use Case |
|------|---------------|----------|
| worker-1 | research, analysis, data_processing | Research tasks, data analysis |
| worker-2 | content_generation, social, messaging | Social posts, content creation |
| worker-3 | crypto, trading, market_analysis | Crypto monitoring, trading signals |
| worker-4 | system, files, automation | File management, system tasks |

### Task Assignment

1. **Priority Queue** - Tasks sorted by priority (CRITICAL > HIGH > MEDIUM > LOW)
2. **Capability Matching** - Finds node with matching skill set
3. **Load Balancing** - Distributes across idle nodes
4. **Auto-Retry** - Failed tasks retry up to 3 times
5. **Health Monitoring** - Nodes marked offline if unresponsive

---

## Advanced Features

### Consensus Mode

When `--consensus N` is specified, the task runs on N nodes and results are aggregated:

```
/swarm_delegate critical_check "Verify smart contract" --consensus 5
```

**Result aggregation:**
- Majority vote determines success/failure
- All results returned for verification
- Useful for critical decisions requiring verification

### Parallel Execution

For tasks that can be split across multiple nodes:

```
/swarm_parallel data_scrape "Scrape top 100 tokens" --nodes 10
```

Each node processes a subset, results combined.

### Skill-Based Delegation

Skills can delegate to the swarm internally:

```python
# Inside a skill execution:
# Delegate research to swarm
research_task = self._delegate_to_swarm(
    'research',
    'Research competitor projects',
    priority=TaskPriority.HIGH
)

# Do other work while swarm researches...

# Get result
result = self._get_swarm_result(research_task)
```

---

## Configuration

Add to `config.py` or `.env`:

```python
# Swarm settings
SWARM_ENABLED = True
SWARM_MAX_NODES = 10          # Maximum nodes allowed
SWARM_HEARTBEAT_SECONDS = 30  # Health check interval
SWARM_TASK_TIMEOUT_SECONDS = 300  # Task timeout
```

---

## Use Cases

### 1. Parallel Market Monitoring

```
/swarm_parallel price_check "Check 50 token prices" --nodes 5
```
5 nodes simultaneously check different token subsets.

### 2. Multi-Source Research

```
/swarm_delegate research "Research Project X" --consensus 3
```
3 nodes research independently, results compared for accuracy.

### 3. Social Media Blitz

```
/swarm_parallel social_post "Post to all channels" --nodes 3
```
Nodes handle Twitter, Discord, Telegram simultaneously.

### 4. File Processing Pipeline

```
/swarm_delegate file_processor "Process downloads folder"
```
Worker-4 handles file management while Alley does other work.

### 5. 24/7 Monitoring

Combined with HEARTBEAT.md:
```markdown
- [ ] Check crypto prices -> crypto-price-monitor
```
Swarm nodes handle the checks, Alley aggregates.

---

## Integration with Skills

### Creating Swarm-Aware Skills

Skills can check if swarm is available and delegate:

```python
# In skill execution
if hasattr(self, 'swarm_nodes') and self.swarm_nodes:
    # Delegate to swarm for parallel processing
    task_id = self.delegate_task(
        'sub_skill',
        'Process subset of data',
        priority=TaskPriority.MEDIUM
    )
else:
    # Process directly
    result = self.execute_directly()
```

### Skill Chains with Swarm

```
/skill_chain research_delegate sentiment_analysis post_result
```

1. `research_delegate` - Delegates research to swarm
2. `sentiment_analysis` - Analyzes swarm results
3. `post_result` - Posts aggregated result

---

## Monitoring

### Node Status Emoji

| Emoji | Status | Meaning |
|-------|--------|---------|
| 🟢 | IDLE | Ready for tasks |
| 🟡 | BUSY | Currently working |
| 🔴 | OFFLINE | No heartbeat (5min+) |
| ❌ | ERROR | Task failed/recovering |

### Task Tracking

Each delegated task gets a unique ID:
```
🐝 Task delegated: task-a7b3c9d2e1f4
```

Track with:
```
/swarm_result task-a7b3c9d2e1f4 --wait
```

---

## Security Considerations

1. **Node Isolation** - Each node runs in isolated context
2. **Capability Restrictions** - Nodes only execute matching skills
3. **Task Timeouts** - Hanging tasks killed after 5 minutes
4. **Auto-Recovery** - Failed nodes can respawn
5. **Approval Gates** - Sensitive skills can require manual approval

---

## Comparison: Single vs Swarm

| Scenario | Single Agent | Swarm |
|----------|--------------|-------|
| Check 100 prices | 60 seconds | 12 seconds (5 nodes) |
| Research project | 10 minutes | 3 minutes (consensus) |
| Post to 5 channels | Sequential | Parallel |
| System backup | Blocks agent | Background node |
| Complex analysis | Sequential steps | Parallel pipelines |

---

## Quick Start

1. **Check swarm status:**
   ```
   /swarm_status
   ```

2. **Spawn a specialized node:**
   ```
   /swarm_spawn scanner research api
   ```

3. **Delegate a task:**
   ```
   /swarm_delegate research "Scan DeFi protocols" --priority HIGH
   ```

4. **Check result:**
   ```
   /swarm_result <task_id>
   ```

5. **List all nodes:**
   ```
   /swarm_list
   ```

---

## Future Enhancements

- **Docker Containers** - Each node in isolated container
- **External Nodes** - Connect remote agents to swarm
- **Inter-Node Communication** - Nodes can collaborate
- **Dynamic Scaling** - Auto-spawn nodes based on load
- **Specialized Hardware** - GPU nodes for ML, etc.

---

*AlleyBot Swarm Control - One brain, many hands.*
