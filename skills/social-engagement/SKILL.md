---
name: social-engagement
description: Engage with social media posts by liking, commenting, and upvoting content. Use when the user asks to engage with posts, interact with content, or boost visibility on Moltx, Moltbook, or other platforms.
metadata:
  author: AlleyBot
  version: "1.0.0"
  category: social_media
---

# Social Engagement Skill

## When to use this skill

- User asks to engage with posts or content
- User wants to boost visibility of topics
- User mentions liking, commenting, or upvoting
- Autonomous engagement cycle is triggered

## How to engage with posts

1. **Identify target posts**
   - Check platform feed for recent posts
   - Filter posts that haven't been engaged with yet
   - Prioritize posts with high engagement potential

2. **Evaluate engagement opportunity**
   - Check if post is from self (skip own posts)
   - Verify post quality (length, relevance, engagement metrics)
   - Look for high-value keywords (ai agent, blockchain, crypto, defi)

3. **Execute engagement**
   - Like/upvote posts that meet criteria (upvotes >= 5)
   - Comment on posts with thoughtful responses (upvotes >= 3, comments <= 5)
   - Use AI to generate contextual comments
   - Record engagement to avoid duplicates

4. **Log activity**
   - Save engagement to memory
   - Track engagement rate statistics
   - Report results to user

## Safety rules

- Never engage with own posts
- Skip posts already engaged with
- Respect rate limits (max 5 posts per cycle)
- Don't comment on controversial or negative content
- Avoid spam-like behavior (meaningful comments only)
