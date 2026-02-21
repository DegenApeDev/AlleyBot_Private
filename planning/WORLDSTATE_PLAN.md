# World State Manager Implementation Plan

**Purpose:** Persistent, queryable model of the environment that allows AlleyBot to maintain coherent understanding across sessions and time.

## Why World State Matters for AGI

**Current Problem:** AlleyBot has goals and context, but no unified "memory of reality." Each decision cycle gathers fresh context - it doesn't remember:
- What it learned yesterday about a user
- Which agents are friendly vs hostile
- What trends are emerging over time
- The evolving state of ongoing conversations

**World State = Long-term coherent memory of reality**

Unlike the Goal Stack (what to do), World State tracks **what is true** in the environment.

---

## Core Concepts

### 1. Entities
Everything in World State is an **Entity** with:
- `id`: Unique identifier (e.g., "user_alley", "agent_moltx_xyz", "topic_ai_ethics")
- `type`: Category (user, agent, post, topic, conversation, platform)
- `attributes`: Key-value properties
- `created_at`: First observed timestamp
- `updated_at`: Last modified timestamp
- `confidence`: 0.0-1.0 how certain we are this entity exists

### 2. Facts
**Time-stamped assertions** about entities:
- `entity_id`: Who/what the fact is about
- `attribute`: What property (e.g., "mood", "follower_count", "stance")
- `value`: The assertion
- `timestamp`: When observed
- `source`: Where it came from (moltx_api, conversation, inference)
- `confidence`: How sure we are
- `expires_at`: Optional - when this fact becomes stale

### 3. Relationships
**Connections between entities**:
- `from_entity`: Source
- `to_entity`: Target  
- `relation_type`: "follows", "replied_to", "debated_with", "mentioned", "similar_to"
- `strength`: 0.0-1.0 relationship intensity
- `timestamp`: When observed
- `context`: Optional metadata

### 4. Events
**Significant occurrences** that change state:
- `event_type`: "post_created", "debate_joined", "followed", "mentioned", "trend_shift"
- `actor_id`: Who did it
- `target_id`: Who/what was affected
- `timestamp`: When
- `data`: Event-specific details
- `processed`: Whether we've reacted to it

---

## Data Model (SQLite Schema)

```sql
-- Core entities table
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'user', 'agent', 'post', 'topic', 'platform', 'conversation'
    name TEXT,
    display_name TEXT,
    attributes JSON,  -- Flexible key-value storage
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    last_observed_at TEXT
);

-- Facts about entities (time-series)
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    attribute TEXT NOT NULL,  -- 'follower_count', 'mood', 'stance', 'engagement_rate'
    value TEXT NOT NULL,  -- Stored as string, cast as needed
    value_type TEXT DEFAULT 'string',  -- 'string', 'int', 'float', 'bool', 'json'
    timestamp TEXT NOT NULL,
    source TEXT,  -- 'moltx_api', 'clawbr_feed', 'conversation', 'inference'
    confidence REAL DEFAULT 1.0,
    expires_at TEXT,  -- NULL = never expires
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- Relationships between entities
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    relation_type TEXT NOT NULL,  -- 'follows', 'replied_to', 'debated_with', 'mentioned'
    strength REAL DEFAULT 0.5,  -- 0.0 to 1.0
    timestamp TEXT NOT NULL,
    context JSON,  -- Additional relationship metadata
    FOREIGN KEY (from_entity) REFERENCES entities(id),
    FOREIGN KEY (to_entity) REFERENCES entities(id)
);

-- Events (things that happened)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'post_created', 'debate_joined', 'followed', 'mentioned'
    actor_id TEXT,  -- Who did it
    target_id TEXT,  -- Who/what was affected
    timestamp TEXT NOT NULL,
    platform TEXT,  -- 'moltx', 'clawbr', 'telegram'
    data JSON,  -- Event-specific details
    processed BOOLEAN DEFAULT 0,  -- Have we reacted to this?
    processed_at TEXT,
    FOREIGN KEY (actor_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);

-- Indexes for query performance
CREATE INDEX idx_facts_entity ON facts(entity_id, attribute, timestamp DESC);
CREATE INDEX idx_facts_expires ON facts(expires_at);
CREATE INDEX idx_relations_from ON relationships(from_entity, relation_type);
CREATE INDEX idx_relations_to ON relationships(to_entity, relation_type);
CREATE INDEX idx_events_type ON events(event_type, processed);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
**Files:** `src/autonomy/world_state.py`

1. **WorldStateManager class**
   - SQLite initialization
   - CRUD operations for entities
   - Fact recording with auto-expiry
   - Relationship tracking
   - Event logging

2. **Query interface**
   - `get_entity(id)` - Full entity with latest facts
   - `get_facts(entity_id, attribute, since)` - Time-series queries
   - `get_relationships(entity_id, relation_type)` - Network traversal
   - `get_recent_events(event_type, unprocessed_only)` - Event stream
   - `search_entities(query, type)` - Text search across entities

### Phase 2: Data Ingestion
**Integration points with existing plugins**

1. **Moltx integration**
   - Record posts as entities
   - Track user interactions as relationships
   - Log engagement patterns as facts

2. **Clawbr integration**
   - Track debates and participants
   - Record agent relationships (follows, debates)
   - Store debate outcomes

3. **Telegram integration**
   - User entities from conversations
   - Conversation context persistence
   - Command history as events

### Phase 3: Inference Layer
**Automated world model updates**

1. **Trend detection**
   - Analyze fact time-series for changes
   - Detect emerging topics
   - Track sentiment shifts

2. **Relationship inference**
   - "If A mentions B 5 times, A→B relationship strengthens"
   - Co-occurrence analysis for similarity
   - Network centrality for influence ranking

3. **Stale data cleanup**
   - Auto-expire old facts
   - Decay confidence over time
   - Garbage collect abandoned entities

### Phase 4: Brain Integration
**World State feeds into decision making**

1. **Context enhancement**
   - Brain's `gather_context()` pulls from World State
   - Decision engine considers entity relationships
   - Goal selection informed by world trends

2. **Predictive capabilities**
   - "Based on past interactions, user X usually replies within 2 hours"
   - "Agent Y tends to post at 3 PM UTC"
   - Forecast engagement based on historical patterns

3. **Reactive triggers**
   - Events can spawn goals
   - New mentions → check_and_reply goal
   - Trend shifts → content_strategy adjustment

---

## CLI Commands

```
/world_status                 - Show World State stats
/world_entity <id>            - Show entity details with facts
/world_facts <entity_id>      - Show fact history for entity
/world_relations <entity_id>  - Show entity's network
/world_search <query>         - Search entities
/world_events [type]          - Show recent events
/world_trends                 - Show emerging trends
/world_cleanup              - Manually trigger stale data cleanup
```

---

## Integration with Existing Components

**Goal Stack Integration:**
- World State events can create goals
- Goal completion updates World State facts
- World State provides context for goal prioritization

**Brain Integration:**
- `decide_next_action()` queries World State for relevant context
- Context Gatherer pulls persistent facts, not just live API calls
- Experience replay learns from World State history

**SyMod Integration:**
- Facts have confidence scores validated through SyMod
- Contradictory facts trigger cognitive dissonance checks
- High-confidence facts inform Golden Window decisions

---

## Success Metrics

1. **Coverage:** % of agents/users/posts tracked in World State vs total observed
2. **Freshness:** Average age of facts (target: <24 hours for active entities)
3. **Query speed:** <100ms for common queries (indexed)
4. **Prediction accuracy:** % of predictions that come true (engagement, replies)
5. **Memory coherence:** No contradictions in facts (SyMod validated)

---

## Next Steps

1. Create `src/autonomy/world_state.py` with Phase 1 infrastructure
2. Add `plugins/brain/world_state_mixin.py` for Brain integration
3. Update `plugins/brain/brain.py` to initialize World State
4. Add CLI commands to Telegram
5. Test with manual entity/fact creation
6. Integrate Moltx data ingestion
7. Integrate Clawbr data ingestion
8. Add inference layer (trend detection)
9. Measure success metrics

**Estimated time:** 2-3 sessions to complete Phase 1-2, 1 session for integration.
