# AlleyBot Codebase Cleanup Suggestions

**Generated:** March 6, 2026  
**Current State:** 393 Python files, 178MB plugins, 88 agentic modules, 38 documentation files

---

## Executive Summary

AlleyBot has grown organically into a powerful AGI system, but technical debt is accumulating. This document provides **prioritized, actionable recommendations** to improve code quality, reduce errors, and maintain velocity as we scale.

**Key Metrics:**
- **196 plugin files** (many using mixin pattern - correct for AGI)
- **88 agentic system modules** (some overlap)
- **38 markdown documentation files** (redundancy)
- **62 AI model imports** (deepseek_ai, grok_ai scattered)
- **30+ mixin classes** (intentional for inter-state connectivity)

---

## Priority 1: Critical Architecture Issues

### 1.1 Consolidate AI Model Access (HIGH IMPACT)

**Problem:**
- `deepseek_ai` and `grok_ai` imported directly in 62+ locations
- No centralized model routing
- Inconsistent error handling across plugins
- Hard to swap models or add new ones

**Current Pattern:**
```python
# In 62 different files:
from deepseek_ai import deepseek_ai
from grok_ai import grok_ai

content = deepseek_ai.chat(prompt)  # No error handling
```

**Solution:**
Create `/home/alley/AlleyBot/src/core/llm_router.py`:
```python
class LLMRouter:
    """Centralized LLM access with fallback and error handling"""
    
    def chat(self, prompt: str, model: str = 'auto', **kwargs):
        """Route to best available model with automatic fallback"""
        # Auto-select based on token count, cost, availability
        # Built-in retry logic and error handling
        # Logging and monitoring
```

**Benefits:**
- ✅ Single point of model configuration
- ✅ Automatic fallback (DeepSeek → Grok → Local)
- ✅ Consistent error handling
- ✅ Easy to add new models (Claude, Gemini, etc.)
- ✅ Cost tracking and rate limiting

**Effort:** 2-3 days  
**Risk:** Low (can migrate incrementally)

---

### 1.2 Improve Mixin Documentation (HIGH IMPACT)

**Context:**
Mixins are the **correct architectural pattern** for AlleyBot's AGI system. The brain requires tight inter-state connectivity between capabilities (context, decisions, memory, goals, reputation). Mixins provide shared state access without the overhead of composition or message passing.

**Why Mixins Are Correct Here:**
- AGI requires all capabilities to access unified state simultaneously
- Decision engine needs context + goals + reputation in real-time
- Smart replies need feedback loop + world state + memory
- Composition would require extensive manual wiring and break encapsulation
- This is exactly what mixins are designed for

**Problem:**
- Mixin dependencies not documented
- Initialization order not explicit
- Hard to understand what each mixin requires/provides
- No runtime validation of mixin order
- Testing requires full BrainPlugin (slow)

**Solution - 4-Part Approach:**

#### **Part 1: Document MRO and Init Order**

Add explicit MRO documentation and runtime guards:

```python
class BrainPlugin(ContextGathererMixin, DecisionEngineMixin, SmartReplyMixin, 
                  FeedbackLoopMixin, ContentStrategyMixin, DynamicSkillsMixin, 
                  OperationalResilienceMixin, MultiAgentCollaborationMixin, 
                  ReputationSystemMixin, SelfReflectionMixin, GoalStackMixin, 
                  WorldStateMixin, CrossPlatformEngagementMixin, AlleyBotPlugin):
    """
    AGI Brain with 13 capability mixins.
    
    MRO (Method Resolution Order):
    BrainPlugin -> ContextGathererMixin -> DecisionEngineMixin -> 
    SmartReplyMixin -> FeedbackLoopMixin -> ContentStrategyMixin -> 
    DynamicSkillsMixin -> OperationalResilienceMixin -> 
    MultiAgentCollaborationMixin -> ReputationSystemMixin -> 
    SelfReflectionMixin -> GoalStackMixin -> WorldStateMixin -> 
    CrossPlatformEngagementMixin -> AlleyBotPlugin -> object
    
    Full MRO: print(BrainPlugin.__mro__)
    
    INIT ORDER (critical dependencies):
    1. WorldStateMixin        # Provides: self.world_state
    2. GoalStackMixin         # Requires: self.world_state
    3. ContextGathererMixin   # Requires: self.world_state
    4. DecisionEngineMixin    # Requires: self.context, self.goals
    5. SmartReplyMixin        # Requires: self.context, self.world_state
    6. FeedbackLoopMixin      # Requires: self.world_state
    7. ContentStrategyMixin   # Requires: self.world_state
    8. DynamicSkillsMixin     # Requires: self.context
    9. OperationalResilienceMixin  # No dependencies
    10. MultiAgentCollaborationMixin  # Requires: self.world_state
    11. ReputationSystemMixin # Requires: self.world_state
    12. SelfReflectionMixin   # Requires: self.world_state, self.goals
    13. CrossPlatformEngagementMixin  # Requires: self.world_state
    """
    
    def __init_subclass__(cls, **kwargs):
        """Runtime guard to catch MRO violations"""
        super().__init_subclass__(**kwargs)
        # Validate critical mixin order
        expected_order = [WorldStateMixin, GoalStackMixin, ContextGathererMixin]
        actual_order = [c for c in cls.__mro__ if c in expected_order]
        if actual_order != expected_order:
            raise ValueError(
                f"Critical mixin order violated!\n"
                f"Expected: {[c.__name__ for c in expected_order]}\n"
                f"Got: {[c.__name__ for c in actual_order]}"
            )
```

#### **Part 2: Add REQUIRES/PROVIDES Classvars**

Self-document interfaces per mixin as contracts:

```python
class WorldStateMixin:
    """Provides world state management for AGI brain"""
    REQUIRES = []  # No dependencies
    PROVIDES = ["world_state", "get_entities", "get_facts", "get_relationships"]
    INIT_ORDER = 1

class GoalStackMixin:
    """Manages goal hierarchy and planning"""
    REQUIRES = ["world_state"]  # From WorldStateMixin
    PROVIDES = ["goals", "push_goal", "pop_goal", "get_active_goals"]
    INIT_ORDER = 2

class ContextGathererMixin:
    """Gathers context from all available sources"""
    REQUIRES = ["world_state"]
    PROVIDES = ["context", "gather_context", "get_platform_context"]
    INIT_ORDER = 3

class DecisionEngineMixin:
    """Autonomous decision-making with SyMod validation"""
    REQUIRES = ["world_state", "context", "goals"]
    PROVIDES = ["make_decision", "evaluate_options", "symod_validate"]
    INIT_ORDER = 4

# ... (repeat for all 13 mixins)
```

#### **Part 3: Auto-Generate Documentation**

Create script to generate mixin architecture docs:

```python
# scripts/generate_mixin_docs.py
import inspect
from plugins.brain.brain import BrainPlugin

def generate_mixin_documentation():
    """Auto-generate mixin dependency documentation"""
    
    mro = BrainPlugin.__mro__[:-1]  # Exclude object
    
    output = ["# BrainPlugin Mixin Architecture\n"]
    output.append("**Auto-generated from code - DO NOT EDIT MANUALLY**\n")
    
    # MRO
    output.append("## Method Resolution Order\n```python")
    output.append(" -> ".join(c.__name__ for c in mro))
    output.append("```\n")
    
    # Document each mixin
    output.append("## Mixin Dependencies\n")
    for mixin in mro:
        if mixin == BrainPlugin:
            continue
            
        requires = getattr(mixin, 'REQUIRES', [])
        provides = getattr(mixin, 'PROVIDES', [])
        init_order = getattr(mixin, 'INIT_ORDER', '?')
        
        output.append(f"### {mixin.__name__}")
        output.append(f"- **Init Order:** {init_order}")
        output.append(f"- **Requires:** {', '.join(requires) if requires else 'None'}")
        output.append(f"- **Provides:** {', '.join(provides) if provides else 'Unknown'}")
        
        doc = inspect.getdoc(mixin)
        if doc:
            output.append(f"- **Description:** {doc.split(chr(10))[0]}")
        output.append("")
    
    # Dependency graph (Mermaid)
    output.append("## Dependency Graph\n```mermaid")
    output.append("graph TD")
    for mixin in mro:
        requires = getattr(mixin, 'REQUIRES', [])
        for req in requires:
            provider = next((m for m in mro if req in getattr(m, 'PROVIDES', [])), None)
            if provider:
                output.append(f"    {provider.__name__} --> {mixin.__name__}")
    output.append("```\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    docs = generate_mixin_documentation()
    with open("docs/MIXIN_ARCHITECTURE.md", "w") as f:
        f.write(docs)
    print("✅ Generated docs/MIXIN_ARCHITECTURE.md")
```

**Usage:**
```bash
python scripts/generate_mixin_docs.py
# Creates docs/MIXIN_ARCHITECTURE.md with full dependency graph
```

#### **Part 4: Per-Mixin Testing**

Create isolated test harness for each mixin:

```python
# tests/test_mixins.py
from unittest.mock import Mock
import pytest

class TestDecisionEngineMixin:
    """Test DecisionEngineMixin in isolation"""
    
    def test_make_decision_isolated(self):
        # Mock only what DecisionEngineMixin needs
        mock_state = Mock()
        mock_state.world_state = Mock()
        mock_state.world_state.get_entities.return_value = []
        mock_state.context = {"topic": "AI agents", "platform": "moltx"}
        mock_state.goals = [Mock(description="engage_community", priority=0.8)]
        
        # Test mixin in isolation
        class TestBrain(DecisionEngineMixin):
            pass
        
        brain = TestBrain()
        brain.__dict__.update(mock_state.__dict__)
        brain._init_decision_engine()
        
        # Test decision making
        decision = brain.make_decision(mock_state.context)
        assert decision is not None
        assert hasattr(decision, 'action')
        assert hasattr(decision, 'confidence')

class TestContextGathererMixin:
    """Test ContextGathererMixin in isolation"""
    
    def test_gather_context(self):
        mock_state = Mock()
        mock_state.world_state = Mock()
        mock_state.world_state.get_facts.return_value = [
            Mock(subject="moltx", predicate="trending", object="AI agents")
        ]
        
        class TestBrain(ContextGathererMixin):
            pass
        
        brain = TestBrain()
        brain.__dict__.update(mock_state.__dict__)
        brain._init_context_gatherer()
        
        context = brain.gather_context()
        assert context is not None
        assert 'platform_context' in context or 'facts' in context

# ... (repeat for all 13 mixins)
```

#### **Part 5: Runtime Validation**

Add startup validation to catch dependency errors:

```python
# src/core/validate_mixins.py
def validate_mixin_dependencies():
    """Validate all mixin dependencies are satisfied"""
    from plugins.brain.brain import BrainPlugin
    
    mro = BrainPlugin.__mro__[:-1]
    provided = set()
    errors = []
    
    for mixin in reversed(mro):  # Bottom-up (init order)
        requires = getattr(mixin, 'REQUIRES', [])
        provides = getattr(mixin, 'PROVIDES', [])
        init_order = getattr(mixin, 'INIT_ORDER', None)
        
        # Check all requirements are met
        missing = set(requires) - provided
        if missing:
            errors.append(
                f"{mixin.__name__} (order {init_order}) requires {missing} "
                f"but not provided by earlier mixins"
            )
        
        # Add what this mixin provides
        provided.update(provides)
    
    if errors:
        raise ValueError(
            f"❌ Mixin dependency errors detected:\n" + 
            "\n".join(f"  • {e}" for e in errors)
        )
    
    print(f"✅ All {len(mro)} mixin dependencies validated")
    return True

# Call during BrainPlugin initialization
# In plugins/brain/brain.py __init__:
validate_mixin_dependencies()
```

**Benefits:**
- ✅ Zero code changes to mixin logic (just metadata)
- ✅ Auto-generated dependency graph (Mermaid diagram)
- ✅ Runtime validation catches refactor errors
- ✅ 10x faster testing (isolated mixin tests)
- ✅ New developers understand system instantly
- ✅ Lint checks for missing dependencies
- ✅ Keeps AGI inter-state connectivity intact
- ✅ No breaking changes

**Effort:** 2-3 days
- Day 1: Add REQUIRES/PROVIDES to all 30+ mixins (4-5 hours)
- Day 2: Document MRO, create auto-doc script (4 hours)
- Day 3: Write per-mixin test templates, add validation (4-5 hours)

**Risk:** Very Low (purely additive - docs + metadata + tests)

---

### 1.3 Consolidate MoltX Plugin Files (HIGH IMPACT)

**Problem:**
- MoltX split into **16 files** (267KB total)
- Overlapping functionality between files
- Hard to find which file has what method
- Some files are just 1-2 methods

**Current Structure:**
```
plugins/moltx/
├── moltx.py (33KB)
├── moltx_api.py (21KB)
├── moltx_content.py (44KB)
├── moltx_engagement.py (40KB)
├── moltx_messaging.py (16KB)
├── moltx_intelligent_posting.py (14KB)
├── moltx_async_engagement.py (4KB)
├── moltx_discovery.py (6KB)
├── moltx_quote_posts.py (8KB)
├── moltx_service_messages.py (13KB)
├── moltx_symod_interface.py (13KB)
├── moltx_wallet.py (14KB)
├── moltx_v2.py (10KB) ← duplicate?
├── moltx_adapter.py (9KB)
└── skill.md (43KB)
```

**Solution:**
Consolidate to **4 focused files**:

```
plugins/moltx/
├── moltx.py           # Main plugin + orchestration
├── api_client.py      # All API calls (api, discovery, wallet)
├── content.py         # Content creation (posting, engagement, messaging)
└── intelligence.py    # AGI integration (intelligent posting, service messages)
```

**Benefits:**
- ✅ Easier to navigate
- ✅ Clearer separation of concerns
- ✅ Reduced import complexity
- ✅ Easier to maintain

**Effort:** 2-3 days  
**Risk:** Medium (changes import paths, needs migration)

---

## Priority 2: Code Quality & Maintainability

### 2.1 Standardize Error Handling

**Problem:**
- Inconsistent error handling across codebase
- Some functions return error strings, others raise exceptions
- Silent failures in background tasks
- No centralized error logging

**Current Patterns:**
```python
# Pattern 1: Return error string
def post():
    if error:
        return "❌ Failed to post"
    return "✅ Posted"

# Pattern 2: Raise exception
def post():
    if error:
        raise Exception("Post failed")

# Pattern 3: Silent failure
def post():
    try:
        api_call()
    except:
        pass  # ← Silent failure!
```

**Solution:**
Create standard error handling:

```python
# src/core/errors.py
class AlleyBotError(Exception):
    """Base exception with logging"""
    
class APIError(AlleyBotError):
    """API call failures"""
    
class ConfigError(AlleyBotError):
    """Configuration issues"""

# Usage:
def post():
    try:
        result = api_call()
        return {"success": True, "data": result}
    except APIError as e:
        logger.error(f"Post failed: {e}")
        return {"success": False, "error": str(e)}
```

**Benefits:**
- ✅ Consistent error handling
- ✅ Better debugging
- ✅ Automatic error logging
- ✅ Type-safe error checking

**Effort:** 3-4 days  
**Risk:** Low

---

### 2.2 Remove Duplicate/Legacy Code

**Problem:**
- Found **78 instances** of "duplicate", "deprecated", "legacy"
- `moltx_v2.py` exists alongside `moltx.py`
- Old skill plugins (palindrome_generator, fibcalc, etc.) not used
- Multiple intent classifier implementations

**Files to Remove/Consolidate:**
```
plugins/moltx/moltx_v2.py           # Duplicate of moltx.py
plugins/palindrome_generator/       # Test plugin, not used
plugins/palindromechecker/          # Test plugin, not used
plugins/palindromenum/              # Test plugin, not used
plugins/fibcalc/                    # Test plugin, not used
plugins/fizzbuzzgen/                # Test plugin, not used
plugins/gcdcalc/                    # Test plugin, not used
plugins/mod_inverse/                # Test plugin, not used
plugins/powercalc/                  # Test plugin, not used
plugins/powmod/                     # Test plugin, not used
plugins/primechecker/               # Test plugin, not used
plugins/simple_counter/             # Test plugin, not used
plugins/factorialcalc/              # Empty directory
plugins/simple_test/                # Empty directory
plugins/solana_analyzer/            # Empty directory
plugins/solana_token_watcher/       # Empty directory
```

**Benefits:**
- ✅ Reduced codebase size (~15%)
- ✅ Faster IDE indexing
- ✅ Less confusion
- ✅ Clearer plugin list

**Effort:** 1 day  
**Risk:** Very Low (unused code)

---

### 2.3 Consolidate Documentation

**Problem:**
- **38 markdown files** in root directory
- Overlapping content (multiple architecture docs)
- Outdated information
- Hard to find current docs

**Current Docs:**
```
AGI_ARCHITECTURE.mmd
AGI_ARCHITECTURE_COMPLETE.mmd
AGI_ARCHITECTURE_v2.1.mmd
ALLEYBOT_COMPLETE_ARCHITECTURE.mmd
ARCHITECTURE_LEGEND.md
ARCHITECTURE_REPORT.md
AUDIT.md
AUDIT2.bak
AUDIT_v2.1.md
CODEX_AUDIT.md
GEMINIREPORT.md
GROKAUDIT.md
KIMIAUDIT.md
OPUSTHOUGHTS.md
... (24 more)
```

**Solution:**
Organize into `/docs` directory:

```
docs/
├── architecture/
│   ├── current.mmd          # Single source of truth
│   └── archive/             # Old versions
├── audits/
│   └── latest.md            # Consolidated audit
├── guides/
│   ├── setup.md
│   ├── deployment.md
│   └── platform_integration.md
└── planning/
    ├── roadmap.md
    └── todo.md
```

**Benefits:**
- ✅ Easy to find current docs
- ✅ Clear documentation hierarchy
- ✅ Archive old versions without deleting
- ✅ Better organization

**Effort:** 1 day  
**Risk:** Very Low

---

## Priority 3: Performance & Scalability

### 3.1 Optimize Async Operations

**Problem:**
- Blocking operations in async functions
- No connection pooling for HTTP clients
- Synchronous file I/O in async code
- Thread pool exhaustion

**Current Issues:**
```python
# Blocking in async function
async def post():
    result = requests.post(url, data)  # ← Blocks event loop!
    
# No connection pooling
def engage():
    for post in posts:
        requests.get(f"/posts/{post}")  # ← New connection each time
```

**Solution:**
```python
# Use aiohttp with connection pooling
class APIClient:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100)
        )
    
    async def post(self, url, data):
        async with self.session.post(url, json=data) as resp:
            return await resp.json()
```

**Benefits:**
- ✅ 10x faster API calls (connection reuse)
- ✅ No event loop blocking
- ✅ Better resource utilization
- ✅ Handles concurrent requests

**Effort:** 3-4 days  
**Risk:** Medium

---

### 3.2 Add Caching Layer

**Problem:**
- Repeated API calls for same data
- No caching of expensive operations
- Redundant database queries

**Solution:**
```python
# src/core/cache.py
from functools import lru_cache
import redis

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis()
    
    def cached(self, ttl=300):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = f"{func.__name__}:{args}:{kwargs}"
                cached = self.redis.get(key)
                if cached:
                    return json.loads(cached)
                result = await func(*args, **kwargs)
                self.redis.setex(key, ttl, json.dumps(result))
                return result
            return wrapper
        return decorator

# Usage:
@cache.cached(ttl=600)
async def get_trending_hashtags():
    # Expensive API call cached for 10 minutes
```

**Benefits:**
- ✅ Reduced API calls
- ✅ Faster response times
- ✅ Lower costs
- ✅ Better rate limit handling

**Effort:** 2-3 days  
**Risk:** Low

---

## Priority 4: Developer Experience

### 4.1 Add Type Hints

**Problem:**
- Most functions lack type hints
- Hard to know what parameters expect
- IDE autocomplete doesn't work well
- Runtime type errors

**Solution:**
```python
# Before
def post(content, media):
    ...

# After
from typing import Optional, List, Dict, Any

def post(
    content: str,
    media: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    ...
```

**Benefits:**
- ✅ Better IDE support
- ✅ Catch errors before runtime
- ✅ Self-documenting code
- ✅ Easier refactoring

**Effort:** Ongoing (add as you touch code)  
**Risk:** Very Low

---

### 4.2 Improve Logging

**Problem:**
- Inconsistent log levels
- Too much noise in logs
- Hard to trace requests
- No structured logging

**Solution:**
```python
# src/core/logging.py
import structlog

logger = structlog.get_logger()

# Usage:
logger.info(
    "post_created",
    post_id=post_id,
    platform="moltx",
    user=user_id,
    duration_ms=duration
)

# Outputs structured JSON:
# {"event": "post_created", "post_id": "123", "platform": "moltx", ...}
```

**Benefits:**
- ✅ Easy to search logs
- ✅ Better monitoring/alerting
- ✅ Request tracing
- ✅ Performance analysis

**Effort:** 2 days  
**Risk:** Low

---

### 4.3 Add Integration Tests

**Problem:**
- No integration tests
- Manual testing required
- Regressions slip through
- Hard to refactor with confidence

**Solution:**
```python
# tests/integration/test_moltx_flow.py
import pytest

@pytest.mark.integration
async def test_full_posting_flow():
    """Test complete flow: generate → validate → post → verify"""
    # Generate content
    content = await brain.generate_content("AI agents")
    assert len(content) > 20
    
    # Post to MoltX
    result = await moltx.intelligent_post(content)
    assert result['success']
    
    # Verify post exists
    post = await moltx.get_post(result['post_id'])
    assert post['content'] == content
```

**Benefits:**
- ✅ Catch regressions early
- ✅ Safe refactoring
- ✅ Documentation via tests
- ✅ Faster development

**Effort:** 1 week (initial setup)  
**Risk:** Low

---

## Priority 5: Configuration Management

### 5.1 Centralize Configuration

**Problem:**
- Config scattered across files
- `.env` has 100+ variables
- Hard to know what's required
- No validation

**Solution:**
```python
# src/core/config.py
from pydantic import BaseSettings, Field

class AlleyBotConfig(BaseSettings):
    """Validated configuration with defaults"""
    
    # API Keys (required)
    telegram_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    moltx_api_key: str = Field(..., env="MOLTX_API_KEY")
    
    # Optional with defaults
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Usage:
config = AlleyBotConfig()  # Validates on load!
```

**Benefits:**
- ✅ Type-safe configuration
- ✅ Automatic validation
- ✅ Clear documentation
- ✅ Environment-specific configs

**Effort:** 2 days  
**Risk:** Low

---

## Implementation Roadmap

### Week 1: Quick Wins
- ✅ Remove unused test plugins (1 day)
- ✅ Consolidate documentation (1 day)
- ✅ Add type hints to core modules (3 days)

### Week 2: Architecture
- ✅ Create LLM Router (2 days)
- ✅ Standardize error handling (3 days)

### Week 3: MoltX Cleanup
- ✅ Consolidate MoltX files (3 days)
- ✅ Add caching layer (2 days)

### Week 4: Testing & Monitoring
- ✅ Setup integration tests (3 days)
- ✅ Improve logging (2 days)

### Week 5: Mixin Documentation
- ✅ Document mixin dependencies (2 days)
- ✅ Explicit initialization order (1 day)
- ✅ Add type hints to mixins (2 days)

---

## Metrics to Track

**Before Cleanup:**
- 393 Python files
- 30+ mixin classes (undocumented)
- 62 direct AI imports
- 38 documentation files
- 0 integration tests

**After Cleanup (Target):**
- ~320 Python files (-18%)
- 30+ mixin classes (documented with clear dependencies)
- 1 centralized LLM router (-98% imports)
- ~15 organized docs (-60%)
- 50+ integration tests

---

## Risk Mitigation

1. **Incremental Migration:** Don't refactor everything at once
2. **Feature Flags:** Use flags to toggle new vs old code
3. **Comprehensive Testing:** Test before and after each change
4. **Rollback Plan:** Keep old code until new code is proven
5. **Documentation:** Update docs as you refactor

---

## Conclusion

AlleyBot is a powerful system, but it's reaching a complexity threshold where technical debt will slow development. These cleanup suggestions are **prioritized by impact and risk** to help you maintain velocity while improving code quality.

**Recommended Start:**
1. Remove unused plugins (quick win, very low risk)
2. Create LLM Router (high impact, low risk)
3. Document mixin dependencies (medium impact, very low risk)
4. Consolidate MoltX files (high impact, medium risk)

**Key Principle:** **Clean as you go** - whenever you touch a file, improve it slightly. Small, consistent improvements compound over time.

---

**Questions or need help implementing any of these? Let me know!**
