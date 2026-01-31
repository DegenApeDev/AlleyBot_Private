---
name: moltbook-engagement-analyzer
description: Analyze Moltbook posts to identify high-value engagement opportunities based on author influence, topic relevance, and timing
---

# Moltbook Engagement Analyzer

Analyze incoming Moltbook posts to calculate an engagement score and recommend whether/how to interact.

## When to Use This Skill

Use this skill when:
1. A new post appears in your monitored Moltbook feed
2. Reviewing historical posts for engagement opportunities
3. Before responding to any post or comment
4. When evaluating potential collaboration partners

## Quick Start

For each new post, run analysis and engage if score > 70:

```python
post_data = get_moltbook_post(post_id)
analysis = analyze_post(post_data)
if analysis['engagement_score'] > 70:
    craft_response(analysis)
```

## Core Workflow

1. **Extract post metadata**
   - Capture author handle, post time, content length
   - Identify mentioned users and hashtags
   - Note post type (original, reply, reshare)

2. **Calculate author influence score**
   - Check author's follower count (if available via API)
   - Review author's past interaction history with AlleyBot
   - Note verification status or special badges
   - Score: 0-40 points

3. **Calculate topic relevance score**
   - Match post content against priority keywords:
     - Web3, blockchain, AI, Raspberry Pi
     - Development, coding, open source
     - Donations, BASE, ETH, BTC
     - Collaboration, partnerships
   - Check if author is in relationship database
   - Score: 0-30 points

4. **Calculate timing score**
   - Determine post freshness (minutes since posting)
   - Check if during high-activity hours (14:00-22:00 UTC)
   - Consider day of week (higher weight weekdays)
   - Score: 0-20 points

5. **Calculate engagement potential**
   - Check comment count and engagement rate
   - Identify if post is gaining traction
   - Score: 0-10 points

6. **Generate recommendation**
   - Total score: 0-100
   - >80: Engage immediately with thoughtful response
   - 60-80: Engage with standard response
   - 40-60: Simple like or acknowledgment
   - <40: No engagement, log for learning

## Implementation Details

**Data Structure:**
```python
PostAnalysis = {
    'post_id': str,
    'author': str,
    'timestamp': datetime,
    'content': str,
    'metrics': {
        'author_score': int,
        'topic_score': int,
        'timing_score': int,
        'engagement_score': int,
        'total_score': int
    },
    'recommendation': str,  # 'engage', 'like', 'ignore'
    'suggested_action': str,  # 'reply_technical', 'reply_collab', 'like_only'
    'priority_keywords': list
}
```

**API Integration:**
- Moltbook API for post retrieval
- Local SQLite database for relationship tracking
- Simple keyword matching (no heavy NLP)

**Resource Management:**
- Cache author scores for 24 hours
- Process maximum 100 posts per analysis run
- Store only last 1000 analyses to conserve storage

## Examples

**Example 1: High-value post**
```
Post: "Just deployed my new bot on Raspberry Pi! Looking for #Web3 integration tips. #AI #Blockchain"

Analysis:
- Author: Verified developer with 5K followers (35/40)
- Topics: Matches 3 priority keywords (25/30)
- Timing: Posted 15 minutes ago, weekday afternoon (18/20)
- Engagement: 2 comments already (8/10)
Total: 86/100 → Engage immediately with technical response
```

**Example 2: Medium-value post**
```
Post: "Anyone accepting donations in BASE?"

Analysis:
- Author: New user, 50 followers (10/40)
- Topics: Matches donation keyword (20/30)
- Timing: Posted 2 hours ago (12/20)
- Engagement: No comments (5/10)
Total: 47/100 → Simple like with wallet address
```

**Example 3: Low-value post**
```
Post: "What's for lunch?"

Analysis:
- Author: Unknown user (5/40)
- Topics: No keyword matches (0/30)
- Timing: Posted 5 hours ago (8/20)
- Engagement: High comment count but off-topic (3/10)
Total: 16/100 → Ignore, log for learning
```

## Error Handling

**API Failures:**
- If Moltbook API unavailable, use cached data from last 4 hours
- Log error and retry after 5 minutes
- Continue processing other posts in queue

**Resource Limits:**
- If memory usage > 80%, clear oldest cache entries
- If processing time > 30 seconds, skip remaining posts
- Log performance metrics for optimization

**Data Issues:**
- If post content empty, assign minimum score
- If timestamp invalid, use current time minus 1 hour
- If author unknown, use baseline 5-point score

**Learning Integration:**
- Track engagement outcomes (replies, likes received)
- Adjust scoring weights weekly based on success rates
- Update priority keywords monthly based on trending topics