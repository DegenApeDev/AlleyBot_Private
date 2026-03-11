---
name: content-strategy
description: |-
  Analyzes past content to generate themed calendars, detect repetition, and enforce voice consistency; use before content-generation or posting to plan varied, on-brand themes weekly/monthly.
---
# Content Strategy Skill

## Core Data Structures

**Content Log** (JSON object, maintain in agent memory or file: `content-log.json`):
```json
{
  "themes": [
    {
      "id": "theme-uuid",
      "name": "DeFi Liquidity",
      "keywords": ["symod", "liquidity", "pools"],
      "usage_count": 5,
      "last_used": "2024-10-01",
      "engagement_avg": 0.85
    }
  ],
  "voice_profile": {
    "tone": "playful-expert",
    "style": "concise-witty",
    "length_range": [100, 280],
    "keywords": ["claw", "molt", "hustle"],
    "avoid": ["generic", "salesy"]
  },
  "last_update": "2024-10-07"
}
```

**Strategy Output** (JSON for content-generation input):
```json
{
  "period": "week-42",
  "themes": [
    {"theme": "NFT Molt", "priority": "high", "slot": 1},
    {"theme": "Claw Tools", "priority": "med", "slot": 3}
  ],
  "repetition_score": 0.3,
  "voice_reminder": "Keep playful-expert, max 280 chars",
  "diversity_goals": {"max_per_theme": 2, "new_themes": 1}
}
```

## Decision Logic

1. **Repetition Check**:
   - Score = (sum(usage_count > 3 for themes in last 14 days)) / total_themes
   - If score > 0.4: Flag "high_repetition", prioritize 2+ new themes (low usage_count < 2)

2. **Theme Generation**:
   - Base themes from voice_profile.keywords + existing skills (e.g., blockchain-analysis trends)
   - New theme if: usage_count < 2 OR engagement_avg < 0.7
   - Max 7 themes/week, balanced by engagement_avg (high first)

3. **Voice Enforcement**:
   - Always validate against voice_profile before output
   - If drift detected (e.g., keyword mismatch > 20%): Reset reminder

## Action Steps (Follow Sequentially)

1. **Fetch & Update Log**:
   - Call `moltbook-engagement-analyzer` or `social-engagement` for last 20 posts.
   - Categorize posts into themes via keyword match (threshold: 60% overlap).
   - Update `content-log.json`: increment usage_count, set last_used, calc engagement_avg.
   - Save log.

2. **Analyze**:
   - Load `content-log.json`.
   - Compute repetition_score over last 14 days.
   - Generate 5-7 candidate themes:
     | Source | Logic |
     |--------|-------|
     | Past high-performers | usage_count > 3 AND engagement_avg > 0.8 |
     | Trends | Integrate `blockchain-analysis` or `symod-liquidity-architect` outputs |
     | New | Random from voice.keywords + "claw-", ensure variety |

3. **Build Strategy**:
   - Select top 5-7 themes: Sort by priority (new > high_eng > balanced).
   - Assign slots (1-7 for week).
   - If repetition_score > 0.4: Force 40% new themes.
   - Generate voice_reminder: "Tone: {tone}. Avoid: {avoid}."

4. **Output & Log**:
   - Emit Strategy Output JSON.
   - Append to log: {"action": "strategy_generated", "output": strategy}.
   - Use output as prompt prefix for `content-generation`.

## Integration Hooks

- **Pre-content-generation**: Always run if >3 days since last strategy.
- **Post-post**: Trigger update via `engagement-optimizer` feedback.
- **API Simulation** (internal calls):
  | Endpoint | Method | Purpose |
  |----------|--------|---------|
  | `/internal/posts/recent` | GET ?limit=20 | Fetch posts |
  | `/internal/themes/suggest` | POST {keywords} | Generate candidates |
  | `/skills/moltbook-engagement-analyzer` | POST {posts} | Analyze engagement |

## Thresholds
- High repetition: >0.4
- Theme freshness: <14 days
- Min diversity: 3 unique/week