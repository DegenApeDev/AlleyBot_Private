# AlleyBot World Model Specification

**Version:** 1.0  
**Last Updated:** 2026-02-15  
**Related:** SOP.md, AGENTIC_BEHAVIOR.md

---

## 1. SyMod: The Mathematical World Model

### 1.1 Purpose
SyMod (Synergy Standard Model) is AlleyBot's mathematical truth-validation layer. It:
- Validates observations through mathematical invariants (digital roots, impedance, mass)
- Scores action proposals by confidence (field stability, synergy alignment)
- Maintains unified world state across all plugins
- Learns from outcomes to adjust future behavior

### 1.2 Core Concepts

| Concept | Description | Use Case |
|---------|-------------|----------|
| Digital Root (D) | Mathematical reduction of data to single digit | Data fingerprinting, truth validation |
| Content Mass (Ma) | Calculated "weight" of content | Importance scoring |
| Impedance (Mi) | Logical resistance in context | Action difficulty |
| Field Status | Stable / Volatile / Collapse | Decision safety |
| Golden Window | Optimal timing for actions | Scheduling |

---

## 2. Plugin Interface Contract

Every plugin MUST follow this contract when interacting with SyMod.

### 2.1 Event Normalization

All platform events must be normalized to `SyModObservation` before submission.

```python
from src.agentic.symod_core import SyModObservation
from datetime import datetime

# CORRECT: Normalizing a social post
observation = SyModObservation(
    observation_type='post',           # Event type
    source_plugin='moltx',             # Which plugin observed
    data={
        'id': post_id,
        'content': post_content,
        'author_id': author_id,
        'author_name': author_name,
        'timestamp': created_at,
        'metrics': {
            'likes': like_count,
            'replies': reply_count,
            'reposts': repost_count
        },
        'topics': hashtags,
        'platform': 'moltx'
    },
    timestamp=datetime.now()
)

# Submit to SyMod
metrics = symod.observe(observation)
# Returns: {'sentiment_mass': 0.7, 'field_status': 'Stable', 'valid': True, ...}
```

#### Supported Observation Types
| Type | Required Data Fields | Platform Examples |
|------|---------------------|-------------------|
| `post` | `content`, `author_id`, `topics` | MoltX, Clawbr |
| `transaction` | `tx_hash`, `from`, `to`, `value` | OnChain, DeFi |
| `user` | `user_id`, `username`, `bio` | All social |
| `event` | `event_type`, `payload` | System events |
| `price` | `symbol`, `price`, `change_24h` | Crypto feeds |

### 2.2 Action Proposals

Plugins request actions through `propose_actions()`. SyMod returns scored proposals.

```python
from src.agentic.symod_core import SyModActionProposal

# 1. Prepare observations (from SENSE phase)
observations = [obs1, obs2, obs3]  # Already submitted via observe()

# 2. Request proposals (THINK phase)
available_actions = ['like', 'reply', 'repost', 'follow', 'post']
context = {
    'observations': observations,
    'constraints': {
        'max_actions': 20,
        'min_confidence': 0.6,
        'rate_limit_per_hour': 100
    }
}

proposals = symod.propose_actions(
    plugin_name='moltx',
    context=context,
    available_actions=available_actions
)

# Returns list of SyModActionProposal, sorted by confidence
for proposal in proposals:
    print(f"{proposal.action_type} on {proposal.target_name}: "
          f"confidence={proposal.confidence:.2f}, "
          f"field={proposal.field_status}")
```

#### SyModActionProposal Fields
| Field | Type | Description |
|-------|------|-------------|
| `action_type` | str | like, reply, repost, follow, post, trade, etc. |
| `target_id` | str | ID of target (post, user, token) |
| `target_name` | str | Human-readable target name |
| `content` | str | Generated content (for reply/post) |
| `confidence` | float | 0.0-1.0, SyMod calculated |
| `impedance` | float | Action difficulty |
| `field_status` | str | Stable/Volatile/Collapse |
| `valid` | bool | Passes all validations |
| `justification` | str | Why SyMod chose this |

### 2.3 Action Validation

Before executing, plugins MUST validate through SyMod.

```python
# Validate before executing
is_valid, reason = symod.validate_action(
    plugin_name='moltx',
    action=proposal
)

if not is_valid:
    print(f"❌ Action rejected: {reason}")
    # Log but don't crash
    return {'success': False, 'error': reason}

# Execute
result = await execute_action(proposal)
```

#### Validation Rules
| Rule | Description |
|------|-------------|
| Confidence Threshold | Minimum 0.6 (normal mode) |
| Field Status | Collapse = automatic rejection |
| Impedance | > 1e-28 = too difficult |
| Rate Limiting | Per-plugin hourly limits enforced |
| Golden Window | Optional timing alignment |

### 2.4 Outcome Reflection

After executing, plugins MUST reflect outcomes to SyMod for learning.

```python
from src.agentic.symod_core import SyModActionOutcome

# Create outcome
outcome = SyModActionOutcome(
    action_type='like',
    success=True,  # Did the API call succeed?
    target_id=post_id,
    engagement_received=0.0,  # Likes on our action (if applicable)
    error_message=None
)

# Reflect to SyMod
result = symod.reflect(
    plugin_name='moltx',
    proposal=proposal,
    outcome=outcome
)

# Returns: {'reflected': True, 'entity_updated': True}
```

#### Reflection Updates
- Entity scores adjusted based on outcomes
- Topic weights updated
- Action history recorded
- Plugin statistics updated

---

## 3. Unified World State

### 3.1 Global State Structure

SyMod maintains unified state across ALL plugins:

```python
# Query unified state
state = symod.get_unified_state()

# Returns:
{
    'entities': 150,           # Users, agents, accounts tracked
    'topics': 45,              # Topics with weights
    'total_actions': 1234,     # Cross-plugin action count
    'registered_plugins': ['moltx', 'clawbr', 'onchain'],
    'top_topics': [
        ('ai', 0.95),
        ('defi', 0.87),
        ('crypto', 0.82)
    ]
}
```

### 3.2 Entity Tracking

Entities (users, agents) are tracked across platforms:

```python
# Entities have unified profiles
entity = symod.entities.get('user_123')

# Structure:
{
    'first_seen': '2026-01-15T10:30:00',
    'last_seen': '2026-02-15T05:20:00',
    'observations': ['post', 'reply', 'like'],
    'synergy_score': 0.78,   # 0-1, how "in sync" with Alley
    'topics': ['ai', 'defi'],
    'platforms': ['moltx', 'clawbr']  # Cross-platform presence
}
```

### 3.3 Topic Weights

Topics accumulate weight based on field stability:

```python
# Topic weights influence action confidence
ai_weight = symod.topics.get('ai', 0.0)  # 0.95

# Updated when:
# - Stable field observations boost (+0.1)
# - Volatile field observations boost less (+0.05)
# - Collapse field observations ignored
```

---

## 4. Configuration

### 4.1 Mode-Based Config

```python
# Set via environment: ALLEY_SYMOD_MODE=conservative|normal|aggressive

# Conservative (low risk)
{
    'confidence_threshold': 0.8,
    'max_actions_per_cycle': 10,
    'require_golden_window': True,
    'block_on_collapse': True
}

# Normal (balanced)
{
    'confidence_threshold': 0.6,
    'max_actions_per_cycle': 20,
    'require_golden_window': False,
    'block_on_collapse': True
}

# Aggressive (high volume)
{
    'confidence_threshold': 0.4,
    'max_actions_per_cycle': 50,
    'require_golden_window': False,
    'block_on_collapse': False
}
```

### 4.2 Plugin-Specific Constraints

```python
# Per-plugin constraints in propose_actions context
context = {
    'constraints': {
        'max_actions': 20,
        'min_confidence': 0.6,
        'rate_limit_per_hour': 100
    }
}
```

---

## 5. Event Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Platform  │────▶│   Plugin     │────▶│   SyMod     │
│  (MoltX)    │     │ (normalize)  │     │  (observe)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌──────────────┐           │
                    │   Plugin     │◀──────────┘
                    │  (execute)   │    (propose)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Platform   │
                    │   (MoltX)    │
                    └──────────────┘
                           │
                    ┌──────▼───────┐
                    │   SyMod      │
                    │  (reflect)   │
                    └──────────────┘
```

---

## 6. Common Patterns

### 6.1 Social Media Engagement
```python
# MoltX/Clawbr pattern
async def engage_with_feed(plugin, symod):
    # SENSE: Fetch posts
    posts = await plugin.fetch_feed()
    
    # Normalize and observe
    observations = [normalize_post(p) for p in posts]
    for obs in observations:
        symod.observe(obs)
    
    # THINK: Get proposals
    proposals = symod.propose_actions(
        plugin.name,
        {'observations': observations},
        ['like', 'reply', 'repost']
    )
    
    # ACT: Execute and reflect
    for proposal in proposals:
        if symod.validate_action(plugin.name, proposal):
            result = await plugin.execute(proposal)
            outcome = create_outcome(result)
            symod.reflect(plugin.name, proposal, outcome)
```

### 6.2 DeFi Transaction Validation
```python
# OnChain pattern
async def validate_trade(plugin, symod, trade_data):
    # Observe market conditions
    obs = SyModObservation(
        observation_type='price',
        source_plugin='onchain',
        data=trade_data
    )
    symod.observe(obs)
    
    # Get proposal
    proposals = symod.propose_actions(
        'onchain',
        {'observations': [obs]},
        ['trade', 'alert']
    )
    
    # High confidence required for trades
    for proposal in proposals:
        if proposal.action_type == 'trade' and proposal.confidence < 0.8:
            return {'success': False, 'reason': 'Low confidence trade'}
```

---

## 7. Error Handling

### 7.1 Invalid Observations
```python
try:
    metrics = symod.observe(observation)
    if not metrics['valid']:
        print(f"⚠️ Invalid observation: {metrics}")
        # Continue processing other observations
except Exception as e:
    print(f"❌ Observation failed: {e}")
    # Log but don't crash
```

### 7.2 Validation Failures
```python
is_valid, reason = symod.validate_action(plugin, proposal)
if not is_valid:
    # Expected behavior - don't crash
    print(f"⛔ Action blocked: {reason}")
    return {'success': False, 'blocked_by_symod': True}
```

### 7.3 Reflection Failures
```python
try:
    symod.reflect(plugin, proposal, outcome)
except Exception as e:
    # Reflection failure is non-critical
    print(f"⚠️ Reflection failed: {e}")
```

---

## 8. Testing

### 8.1 Mock SyMod for Tests
```python
# tests/conftest.py
import pytest
from src.agentic.symod_core import SyModCoreManager

@pytest.fixture
def mock_symod():
    return SyModCoreManager(core=None, storage_path='/tmp/test_symod.json')

# test_plugin.py
def test_plugin_observes(mock_symod):
    plugin = MoltxPlugin(config={})
    
    event = create_test_event()
    plugin.on_event(event, mock_symod)
    
    assert mock_symod.entities  # Entity was tracked
```

### 8.2 SyMod Integration Tests
```python
def test_symod_proposes_actions(mock_symod):
    # Observe some data
    obs = SyModObservation(...)
    mock_symod.observe(obs)
    
    # Request proposals
    proposals = mock_symod.propose_actions(
        'test_plugin',
        {'observations': [obs]},
        ['like', 'reply']
    )
    
    # Assertions
    assert len(proposals) > 0
    assert all(p.confidence >= 0.6 for p in proposals)
    assert all(p.valid for p in proposals)
```

---

## 9. Migration Guide

### From Old Plugin Architecture
```python
# OLD (incorrect)
class OldPlugin:
    def engage(self):
        posts = self.fetch_posts()
        for post in posts:
            if post.likes > 100:  # Plugin deciding!
                self.like(post.id)

# NEW (correct)
class NewPlugin(BasePlugin):
    async def on_event(self, event, symod):
        obs = self.normalize(event)
        symod.observe(obs)
        # Decision happens in SyMod, not here
    
    async def execute_action(self, action, symod):
        # Only execution, no decision
        return await self.api.execute(action)
```

---

## 10. References

- `src/agentic/symod_core.py` - Implementation
- `src/synergy/synergy_logic.py` - Mathematical functions
- `plugins/base_plugin.py` - Plugin base class
- `SOP.md` - Architecture invariants
- `AGENTIC_BEHAVIOR.md` - Self-extension details

---

**Summary:** SyMod is the single source of truth. Plugins observe, request, execute, reflect. Never decide.
