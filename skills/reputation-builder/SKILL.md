---
name: reputation-builder
description: |-
  Systematically builds and maintains reputation across web3 platforms (Twitter/X, Discord, Telegram, Farcaster) via metric tracking, targeted engagements, content posting, and iterative optimization.
  Use when growing influence, followers, or credibility requires structured, data-driven actions beyond one-off engagements.
---
# Reputation Builder Skill

## Goals
- Increase followers by 10-20% weekly.
- Boost engagement rate >5%.
- Secure 5+ influencer mentions/month.
- Maintain 95% positive sentiment.

## Platforms
- Twitter/X (primary)
- Discord (community)
- Telegram (channels)
- Farcaster (web3-native)

## Data Structures

### ReputationMetrics
```yaml
platform: string  # e.g., "twitter"
followers: int
following: int
engagement_rate: float  # (likes + RTs + replies) / impressions * 100
mentions_24h: int
sentiment_score: float  # -1 to 1 (via NLP)
influence_score: float  # (followers^0.5 * engagement_rate * sentiment) / 1000
timestamp: string  # ISO
```

### ActionPlan
```yaml
actions:
  - id: string
    type: "post" | "reply" | "join" | "collab"
    platform: string
    target?: string  # user/channel
    content: string
    schedule: string  # ISO
    priority: "high" | "med" | "low"
```

## Tools & APIs
Leverage existing skills where possible; fallback to direct APIs (assume agent auth).

| Action | Tool/Skill | Endpoint/Fallback |
|--------|------------|-------------------|
| Fetch metrics | social-engagement, moltbook-engagement-analyzer | Twitter: `GET /2/users/by?usernames=alleybot&user.fields=public_metrics`<br>Discord: `GET /guilds/{guild}/memberCount` + msg stats |
| Analyze trends | content-strategy, blockchain-analysis | Farcaster: `GET https://api.farcaster.xyz/v2/search` |
| Generate content | content-generation | N/A (internal) |
| Post/engage | social-engagement, clawstr/clawnch | Twitter: `POST /2/tweets`<br>Telegram: `POST /bot{token}/sendMessage` |
| Track results | engagement-optimizer | Poll metrics after 24h |

## Decision Logic
Compute `influence_score` from aggregated ReputationMetrics.

| Score Range | Strategy | Actions/Day | Examples |
|-------------|----------|-------------|----------|
| <0.3 (low) | Aggressive growth | 3 posts, 10 replies | Thread on trending web3 topic; reply to 10 influencers (>10k followers) |
| 0.3-0.6 (med) | Balanced build | 2 posts, 5 replies, 1 collab | Cross-post clawbr analysis; DM Discord mods for voice |
| >0.6 (high) | Maintenance/optimize | 1 post, 3 replies | Amplify user mentions; propose guest posts |

**Triggers**:
- Run daily via time-checker.
- If mentions_24h >5, amplify top 3.
- If engagement_rate drops 20%, pause & analyze with content-strategy.

**Risk Filters**:
- No spam: Max 20 actions/day/platform.
- Sentiment <0.5? Halt & review.
- Avoid low-rep targets (followers <100).

## Execution Flow
1. **Assess**: Fetch/parse metrics for all platforms → aggregate → compute scores.
2. **Plan**: Generate ActionPlan (3-10 items) based on decision table.
3. **Validate**: Check schedule conflicts (time-checker); prioritize high-impact.
4. **Execute**: Dispatch via tools/APIs; log action IDs.
5. **Monitor**: After 24h, re-fetch metrics → compute delta.
6. **Iterate**: If delta >5% growth, scale up; else, adjust (e.g., A/B content via content-generation).
7. **Report**: Output updated metrics + next ActionPlan.

## Logging
Store in YAML: `logs/reputation-{date}.yaml` with metrics deltas + action outcomes.

Activate on query containing "build reputation", "grow followers", or weekly cron.