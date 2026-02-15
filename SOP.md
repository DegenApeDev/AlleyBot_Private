# AlleyBot Standard Operating Procedure (SOP)

**Version:** 1.0  
**Last Updated:** 2026-02-15  
**Branch:** feat/sop-plugin-architecture

---

## 1. Project Overview

### What is AlleyBot?
AlleyBot is an autonomous, multi-platform AI agent with a mathematical world model (SyMod) at its core. It operates across social media, DeFi, and communication platforms, making decisions through SyMod's truth-validation framework rather than raw LLM outputs.

### Core Philosophy
- **SyMod is the Brain:** All decisions flow through SyMod's mathematical validation (impedance checks, digital roots, field stability).
- **Plugins are Thin:** Plugins are sensors (input) and actuators (output) only. No decision logic in plugins.
- **Self-Extending:** Alley can propose, build, and register new capabilities without human intervention.

### Key Components
| Component | Purpose | Location |
|-----------|---------|----------|
| SyMod | Mathematical world model, validator | `src/agentic/symod_core.py` |
| AGI Kernel | Consciousness layer, goal management | `src/agentic/agi_kernel.py` |
| Plugin Manager | Hot-loading, routing | `src/core/plugin_manager.py` |
| Base Plugin | Interface all plugins implement | `plugins/base_plugin.py` |
| Event Loop | Central event processing | `src/core/event_loop.py` |

---

## 2. Architecture Invariants (DO NOT VIOLATE)

### 2.1 SyMod is Global World Model
```python
# CORRECT: Plugin observes, SyMod decides
observation = SyModObservation(
    observation_type='post',
    source_plugin='moltx',
    data=post_data
)
symod.observe(observation)  # Goes to core
proposals = symod.propose_actions('moltx', context, actions)  # Core decides

# WRONG: Plugin decides independently
if post.likes > 100:  # ❌ Plugin making decision
    plugin.like_post(post.id)
```

### 2.2 Plugins Are Thin Adapters
- **Maximum 200 lines** per plugin (excluding docstrings)
- **No LLM calls** in plugins (use SyMod/Kernel)
- **No persistent state** in plugins (use unified memory)
- **Two methods only:** `on_event()` and `execute_action()`

### 2.3 Single Central Event + Planning Loop
- All platform events enter through `EventLoop`
- `Planner` queries SyMod for decisions
- `PluginManager` routes actions to appropriate plugins
- **No plugin implements its own event loop**

### 2.4 Self-Extension Pipeline is Sacred
The following must NEVER break:
1. Skill detection (scanning for capability gaps)
2. Skill generation (coding new capabilities)
3. Skill registration (deploying to platforms)
4. Skill testing (smoke tests before activation)

---

## 3. Required Reading (Before Any Code Change)

### For All Developers
1. `SOP.md` (this file) - Architecture rules
2. `WORLD_MODEL.md` - SyMod interfaces
3. `AGENTIC_BEHAVIOR.md` - Self-extension behavior
4. `plugins/base_plugin.py` - Plugin interface

### For Plugin Developers
1. `plugins/base_plugin.py` - Must implement
2. `src/agentic/symod_core.py` - How to observe/reflect
3. `WORLD_MODEL.md` - Event normalization

### For Core Developers
1. `src/agentic/agi_kernel.py` - AGI integration
2. `src/core/plugin_manager.py` - Hotloading
3. `src/core/event_loop.py` - Event routing

---

## 4. Standard Workflow

### 4.1 Starting a Task
```bash
# 1. Ensure you're on feature branch
git checkout -b feat/your-feature-name

# 2. Read relevant docs
# - SOP.md (always)
# - WORLD_MODEL.md (if touching SyMod)
# - AGENTIC_BEHAVIOR.md (if touching self-extension)

# 3. Check TODO.md for active tasks
# 4. Update TODO.md with your task
```

### 4.2 Making Changes
```bash
# 1. Edit files (follow invariants!)
# 2. Run tests: pytest tests/ -v
# 3. Check no regressions: python tests/regression_phase4.py
# 4. Update TODO.md (mark complete)
```

### 4.3 Before Committing
```bash
# 1. Test your specific changes
pytest tests/test_your_feature.py -v

# 2. Test major platform plugins
pytest tests/plugins/test_moltx.py -v
pytest tests/plugins/test_telegram.py -v

# 3. Verify hotloading still works
pytest tests/test_hotloading.py -v

# 4. Check logging isn't noisy
# Should see: Startup info, periodic summaries, errors only
```

---

## 5. Protected Modules

### NEVER MODIFY WITHOUT REVIEW
| Module | Why Protected |
|--------|---------------|
| `src/synergy/synergy_logic.py` | Core SyMod math |
| `src/synergy/symod_filter.py` | Truth validation |
| `src/agentic/symod_core.py` | World model interface |
| `plugins/base_plugin.py` | Base interface |
| `src/core/plugin_manager.py` | Hotloading logic |

### Modification Process
1. Open issue describing change
2. Get approval from architect
3. Create feature branch
4. Add comprehensive tests
5. Update relevant docs
6. PR review required

---

## 6. Plugin Development Guide

### 6.1 Minimal Plugin Template
```python
# plugins/my_platform/my_platform.py
from plugins.base_plugin import BasePlugin, PluginEvent, PluginAction

class MyPlatformPlugin(BasePlugin):
    name = "my_platform"
    supported_channels = ["my_platform"]
    
    async def on_event(self, event: PluginEvent, symod) -> None:
        """Handle incoming event from platform"""
        # 1. Normalize to observation
        observation = self._normalize_event(event)
        
        # 2. Submit to SyMod
        symod.observe(observation)
    
    async def execute_action(self, action: PluginAction, symod) -> dict:
        """Execute action from planner"""
        # 1. Validate via SyMod
        is_valid, reason = symod.validate_action(self.name, action)
        if not is_valid:
            return {'success': False, 'error': reason}
        
        # 2. Execute
        result = await self._execute(action)
        
        # 3. Reflect outcome
        outcome = self._create_outcome(action, result)
        symod.reflect(self.name, action, outcome)
        
        return result
```

### 6.2 Plugin Registration
```python
# In plugin_manager.py config or via Telegram command
plugin_manager.load_plugin('my_platform', {
    'enabled': True,
    'api_key': os.getenv('MY_PLATFORM_API_KEY'),
    'config': {}
})
```

---

## 7. Testing Requirements

### 7.1 All Changes Must Have
- Unit tests for new logic
- Integration test with SyMod
- Plugin smoke test (if plugin-related)
- Hotloading test (if plugin-related)

### 7.2 Test Command Reference
```bash
# Full suite
pytest tests/ -v --tb=short

# Quick smoke
pytest tests/test_smoke.py -v

# Specific plugin
pytest tests/plugins/test_moltx.py -v

# Hotloading
pytest tests/test_hotloading.py -v

# Regression (must pass!)
python tests/regression_phase4.py
```

---

## 8. Common Anti-Patterns (AVOID)

### 8.1 Plugin Deciding Independently
```python
# ❌ WRONG
class BadPlugin(BasePlugin):
    async def on_event(self, event, symod):
        if event.content == "buy":  # Plugin deciding!
            await self.execute_trade()
```

### 8.2 Plugin Storing State
```python
# ❌ WRONG
class BadPlugin(BasePlugin):
    def __init__(self):
        self.user_scores = {}  # State in plugin!
```

### 8.3 Plugin Calling LLM Directly
```python
# ❌ WRONG
class BadPlugin(BasePlugin):
    async def generate_reply(self, post):
        return openai.ChatCompletion.create(...)  # Direct LLM!
```

### 8.4 Plugin With Own Event Loop
```python
# ❌ WRONG
class BadPlugin(BasePlugin):
    def start(self):
        asyncio.create_task(self._poll_forever())  # Own loop!
```

---

## 9. Emergency Procedures

### 9.1 Plugin Crashing
```python
# PluginManager automatically:
# 1. Catches exception
# 2. Logs error
# 3. Unloads plugin
# 4. Notifies via Telegram
# 5. Continues with other plugins
```

### 9.2 SyMod Validation Failing
```python
# If symod.validate_action() returns False:
# 1. Log the rejection with reason
# 2. Do NOT execute action
# 3. Reflect failure to SyMod
# 4. Plugin continues normally
```

### 9.3 Hotload Failure
```python
# If load_plugin() fails:
# 1. Previous plugin version stays active
# 2. Error logged
# 3. Telegram notification sent
# 4. No system crash
```

---

## 10. AI Agent Instructions

If you are an AI coding agent working on AlleyBot:

1. **READ FIRST:** Always read SOP.md, WORLD_MODEL.md, and AGENTIC_BEHAVIOR.md before coding
2. **BRANCH:** Work on feature branches only, never main
3. **INVARIANTS:** The 4 architecture invariants are absolute. Never violate.
4. **TEST:** Every change must have tests. Run regression tests before finishing.
5. **DOCS:** Update docs when architecture changes.
6. **ASK:** If unsure about protected modules, ask before modifying.

### Quick Reference
```python
# Observing data
from src.agentic.symod_core import SyModObservation
obs = SyModObservation(
    observation_type='post',
    source_plugin='moltx',
    data={'content': '...', 'author_id': '...'}
)
symod.observe(obs)

# Getting action proposals
proposals = symod.propose_actions(
    plugin_name='moltx',
    context={'observations': [...]},
    available_actions=['like', 'reply', 'repost']
)

# Executing actions
outcome = await plugin.execute_action(proposal, symod)

# Reflecting
symod.reflect(plugin_name, proposal, outcome)
```

---

## 11. Contact & Escalation

- **Architecture Questions:** Check docs first, then open issue
- **Protected Module Changes:** Require architect review
- **Production Issues:** Follow emergency procedures, notify via Telegram
- **Feature Requests:** Add to TODO.md, discuss in issue

---

**Remember:** SyMod is the brain. Plugins are hands and eyes. Keep them thin.
