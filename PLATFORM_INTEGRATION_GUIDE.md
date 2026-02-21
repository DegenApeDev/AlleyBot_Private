# Platform Integration Guide

**How to integrate any social platform with AlleyBot's World State**

This guide ensures all platform integrations follow the same pattern, making AlleyBot's World State scalable to 20+ platforms without custom code for each one.

---

## Quick Start (For New Platform Developers)

To add a new platform (e.g., "Twitter", "Discord", "Lens"):

1. **Create adapter file**: `plugins/twitter/twitter_adapter.py`
2. **Implement `PlatformAdapter` interface** (see template below)
3. **Register in Brain plugin**: Add one line to register the adapter
4. **Test**: Run `/world_status` to see data flowing

---

## The Adapter Pattern

### Why This Pattern?

**Problem:** Every platform has different APIs, data formats, and terminology
- Moltx: `agent_name`, `post_id`, `likes_count`
- Clawbr: `username`, `debate_slug`, `vote_count`
- Future platforms: Who knows?

**Solution:** Adapter Pattern
- Each platform implements a standard interface
- World State sees unified data regardless of source
- New platforms = new adapter file, no changes to core

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    World State Manager                       │
│         (Single source of truth - unified schema)           │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ standardized data
┌─────────────────────────────────────────────────────────────┐
│              World State Ingestion Engine                    │
│     (Coordinates sync, manages adapters, runs schedules)  │
└─────────────────────────────────────────────────────────────┘
                              ▲
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Moltx Adapter  │  │ Clawbr Adapter  │  │ Future Adapter  │
│ (moltx_adapter) │  │(clawbr_adapter) │  │ (your_adapter)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
│   Moltx API     │  │  Clawbr API     │  │  Platform API   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Implementation Template

Create `plugins/{platform}/{platform}_adapter.py`:

```python
"""
{Platform} Adapter for World State

Integrates {Platform} with AlleyBot's unified World State.
"""
from typing import List, Optional
from datetime import datetime

from src.autonomy.platform_adapter import (
    PlatformAdapter, 
    PlatformEntity, 
    PlatformInteraction,
    PlatformRelationship
)


class {Platform}Adapter(PlatformAdapter):
    """
    {Platform} platform adapter.
    
    Implements standardized interface for ingesting {Platform} data
    into World State.
    """
    
    def __init__(self, {platform}_plugin):
        """
        Initialize with platform plugin instance.
        
        Args:
            {platform}_plugin: The {Platform}Plugin instance from plugin_manager
        """
        self.plugin = {platform}_plugin
    
    def get_platform_name(self) -> str:
        """Return platform identifier"""
        return "{platform}"
    
    def is_available(self) -> bool:
        """Check if platform is connected"""
        return (
            self.plugin is not None and 
            getattr(self.plugin, 'initialized', False) and
            getattr(self.plugin, 'api_key', None) is not None
        )
    
    def fetch_recent_interactions(self, limit: int = 50, since: Optional[str] = None) -> List[PlatformInteraction]:
        """
        Fetch recent posts, likes, replies from {Platform}.
        
        Args:
            limit: Max interactions to fetch
            since: ISO timestamp - only fetch after this time
            
        Returns:
            List of PlatformInteraction objects
        """
        interactions = []
        
        # 1. Fetch from platform API
        feed = self.plugin.get_feed(limit=limit)
        
        # 2. Convert to standardized format
        for post in feed:
            interaction = self._convert_post_to_interaction(post)
            if interaction:
                interactions.append(interaction)
        
        return interactions
    
    def fetch_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List[PlatformEntity]:
        """
        Fetch entities (users, posts) from {Platform}.
        
        Args:
            entity_type: Filter by type ('user', 'post', etc.)
            limit: Max entities to fetch
            
        Returns:
            List of PlatformEntity objects
        """
        entities = []
        
        # Example: Fetch users
        if entity_type is None or entity_type == 'agent':
            users = self.plugin.search_agents("*", limit=limit)
            for user in users:
                entity = PlatformEntity(
                    id=f"{self.get_platform_name()}_{user['id']}",
                    type='agent',
                    platform=self.get_platform_name(),
                    name=user.get('name'),
                    display_name=user.get('display_name'),
                    attributes={
                        'follower_count': user.get('follower_count', 0),
                        'verified': user.get('verified', False)
                    },
                    created_at=user.get('created_at'),
                    url=f"https://{self.get_platform_name()}.io/user/{user['id']}"
                )
                entities.append(entity)
        
        return entities
    
    def fetch_relationships(self, entity_id: Optional[str] = None, limit: int = 100) -> List[PlatformRelationship]:
        """
        Fetch relationships from {Platform}.
        
        Args:
            entity_id: Filter by entity (None = all)
            limit: Max relationships
            
        Returns:
            List of PlatformRelationship objects
        """
        relationships = []
        
        # Example: Fetch follows
        if entity_id:
            follows = self.plugin.get_followers(entity_id, limit=limit)
            for follow in follows:
                rel = PlatformRelationship(
                    from_entity=f"{self.get_platform_name()}_{follow['follower_id']}",
                    to_entity=f"{self.get_platform_name()}_{follow['following_id']}",
                    relation_type='follows',
                    platform=self.get_platform_name(),
                    strength=1.0,  # Follow is binary
                    timestamp=follow.get('created_at')
                )
                relationships.append(rel)
        
        return relationships
    
    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS (Platform-specific conversion logic)
    # ═══════════════════════════════════════════════════════════════
    
    def _convert_post_to_interaction(self, post: dict) -> Optional[PlatformInteraction]:
        """Convert platform-specific post to standardized interaction"""
        try:
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or 'unknown'
            
            return PlatformInteraction(
                id=f"{self.get_platform_name()}_{post_id}",
                type='post',
                platform=self.get_platform_name(),
                actor_id=author,
                content=post.get('content', ''),
                timestamp=post.get('created_at') or datetime.now().isoformat(),
                engagement_metrics={
                    'likes': post.get('likes_count', 0),
                    'replies': post.get('replies_count', 0),
                    'shares': post.get('repost_count', 0)
                },
                hashtags=self._extract_hashtags(post.get('content', '')),
                mentions=self._extract_mentions(post.get('content', ''))
            )
        except Exception as e:
            print(f"⚠️  Failed to convert post: {e}")
            return None
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract #hashtags from content"""
        import re
        return re.findall(r'#(\w+)', content)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        import re
        return re.findall(r'@(\w+)', content)
```

---

## Registration

### Step 1: Create Adapter File

```bash
# Create the adapter file
touch plugins/{platform}/{platform}_adapter.py

# Edit it with the template above
```

### Step 2: Register in Brain Plugin

Edit `plugins/brain/brain.py`:

```python
def _init_world_state(self):
    # ... existing initialization ...
    
    # Register platform adapters
    self._register_platform_adapters()

def _register_platform_adapters(self):
    """Register all platform adapters for World State ingestion"""
    from src.autonomy.platform_adapter import WorldStateIngestionEngine
    
    # Create ingestion engine
    self.ingestion_engine = WorldStateIngestionEngine(self.world_state)
    
    # Register Moltx adapter if available
    moltx = self.core.plugin_manager.plugins.get('moltx')
    if moltx:
        try:
            from plugins.moltx.moltx_adapter import MoltxAdapter
            self.ingestion_engine.register_adapter(MoltxAdapter(moltx))
        except ImportError:
            print("⚠️  Moltx adapter not found")
    
    # Register Clawbr adapter if available
    clawbr = self.core.plugin_manager.plugins.get('clawbr')
    if clawbr:
        try:
            from plugins.clawbr.clawbr_adapter import ClawbrAdapter
            self.ingestion_engine.register_adapter(ClawbrAdapter(clawbr))
        except ImportError:
            print("⚠️  Clawbr adapter not found")
    
    # ═══════════════════════════════════════════════════════════════
    # ADD YOUR PLATFORM HERE
    # ═══════════════════════════════════════════════════════════════
    {platform} = self.core.plugin_manager.plugins.get('{platform}')
    if {platform}:
        try:
            from plugins.{platform}.{platform}_adapter import {Platform}Adapter
            self.ingestion_engine.register_adapter({Platform}Adapter({platform}))
        except ImportError:
            print("⚠️  {Platform} adapter not found")
    # ═══════════════════════════════════════════════════════════════
```

### Step 3: Add Scheduled Sync Task

Edit `plugins/brain/brain.py` `get_tasks()`:

```python
def get_tasks(self):
    return {
        # ... existing tasks ...
        
        'world_state_sync': {
            'function': self._sync_world_state,
            'schedule': '*/15 * * * *',  # Every 15 minutes
            'description': 'Sync all platforms to World State'
        }
    }

def _sync_world_state(self):
    """Scheduled sync of all platforms to World State"""
    if hasattr(self, 'ingestion_engine'):
        stats = self.ingestion_engine.sync_all(limit=50)
        print(f"🌍 World State sync: {stats}")
```

---

## Testing Your Adapter

### 1. Verify Registration

```bash
# In Telegram
/world_status

# Should show:
# 🌍 World State Status
#   📊 Entities: N (from your platform)
#   📝 Facts: N
```

### 2. Manual Sync Test

```python
# In Python console or debug mode
brain = core.plugin_manager.plugins['brain']
stats = brain.ingestion_engine.sync_platform('your_platform')
print(stats)
# {'entities': 10, 'interactions': 25, 'relationships': 5}
```

### 3. Check Entities

```bash
# In Telegram
/world_search your_platform_

# Should show entities from your platform
```

---

## Common Patterns

### Handling Platform-Specific Data

**Problem:** Each platform has unique fields

**Solution:** Store unique fields in `attributes` dict

```python
# Moltx example
entity = PlatformEntity(
    id=f"moltx_{user['id']}",
    type='agent',
    platform='moltx',
    attributes={
        # Platform-specific fields go here
        'moltx_claim_status': user.get('claim_status'),
        'moltx_karma': user.get('karma_score'),
        'moltx_wallet': user.get('wallet_address')
    }
)
```

### Handling Rate Limits

```python
def fetch_recent_interactions(self, limit=50, since=None):
    try:
        feed = self.plugin.get_feed(limit=limit)
    except RateLimitError as e:
        print(f"⏳ Rate limited on {self.get_platform_name()}: {e}")
        return []  # Return empty, will retry next sync
    
    return [self._convert_post(p) for p in feed]
```

### Handling Deleted Content

```python
def _convert_post_to_interaction(self, post):
    # Check if post was deleted
    if post.get('deleted', False):
        return None  # Skip deleted posts
    
    return PlatformInteraction(...)
```

---

## Required Data Fields

### PlatformEntity

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | ✅ | Unique ID, prefix with platform name |
| `type` | str | ✅ | 'agent', 'post', 'topic', 'comment' |
| `platform` | str | ✅ | Platform name |
| `name` | str | ✅ | Display name or handle |
| `attributes` | dict | ❌ | Platform-specific data |
| `created_at` | str | ❌ | ISO timestamp |
| `url` | str | ❌ | Link to original |

### PlatformInteraction

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | ✅ | Unique interaction ID |
| `type` | str | ✅ | 'post', 'like', 'reply', 'repost', 'debate' |
| `platform` | str | ✅ | Platform name |
| `actor_id` | str | ✅ | Who did it |
| `target_id` | str | ❌ | What was affected |
| `content` | str | ❌ | Content/text |
| `timestamp` | str | ✅ | ISO timestamp |
| `engagement_metrics` | dict | ❌ | likes, replies, etc. |

---

## Troubleshooting

### "Adapter not found" error

**Problem:** Import fails

**Solution:** Check file path and class name
```python
# File: plugins/twitter/twitter_adapter.py
class TwitterAdapter(PlatformAdapter):  # Must match import
```

### "No data ingested" 

**Problem:** `fetch_recent_interactions()` returns empty

**Solution:** Check API response format
```python
def fetch_recent_interactions(self, limit=50, since=None):
    feed = self.plugin.get_feed(limit=limit)
    print(f"DEBUG: Got {len(feed)} items from API")  # Add logging
    return [self._convert_post(p) for p in feed]
```

### "Entities not showing in /world_search"

**Problem:** Entity IDs not prefixed with platform

**Solution:** Always prefix IDs
```python
# ❌ Bad
id=post['id']

# ✅ Good  
id=f"{self.get_platform_name()}_{post['id']}"
```

---

## Submission Checklist

Before submitting your platform adapter:

- [ ] Adapter implements all required abstract methods
- [ ] Entity IDs are prefixed with platform name
- [ ] Handles API errors gracefully (returns empty list on failure)
- [ ] Includes docstrings explaining platform-specific fields
- [ ] Tested with `/world_status` showing your platform's data
- [ ] Tested with `/world_search {platform}_` showing entities
- [ ] No hardcoded secrets (uses plugin's config)
- [ ] Follows existing code style (4 spaces, PEP 8)

---

## Example: Complete Moltx Adapter

See `plugins/moltx/moltx_adapter.py` for a complete, tested implementation.

Key features demonstrated:
- Multiple entity types (agents, posts)
- Engagement metrics
- Hashtag/mention extraction
- Relationship tracking (follows, replies)

---

## Questions?

- Check existing adapters for patterns
- Review `src/autonomy/platform_adapter.py` for base interface
- Test incrementally: entities → interactions → relationships

**Remember:** The goal is "write adapter once, works forever" - no core changes needed for new platforms.
