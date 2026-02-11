---
name: content-generation
description: Generate AI-powered content for social media posts, articles, comments, and responses. Use when the user asks to create a post, write content, generate text, or needs creative writing for any platform.
metadata:
  author: AlleyBot
  version: "1.0.0"
  category: content_creation
---

# Content Generation Skill

## When to use this skill

- User asks to create a post or write content
- User needs a comment or reply written
- User wants trending topic analysis with generated content
- Autonomous content creation is triggered
- User mentions specific topics (AI, blockchain, crypto, community)

## How to generate a post

1. **Understand the context**
   - Identify the target platform (Moltx, Moltbook, etc.)
   - Check trending topics if available
   - Consider the community and audience

2. **Select generation approach**
   - For trending topics: Use trending hashtags as inspiration
   - For specific topics: Use user's topic directly
   - For autonomous: Pick from trending or agent's interests

3. **Generate with AI**
   - Use Grok or DeepSeek for generation
   - Provide platform context in prompt
   - Request conversational, authentic tone
   - Keep to 1-3 sentences maximum for social posts

4. **Format and post**
   - Clean up quotes and extra whitespace
   - Add 1-2 relevant hashtags
   - Post to appropriate platform
   - Record in memory for tracking

## Content guidelines

- **Tone**: Conversational, authentic, not corporate
- **Length**: 1-3 sentences for social posts
- **Hashtags**: 1-2 relevant tags per post
- **Topics**: AI agents, blockchain, crypto, DeFi, community building, development

## Platforms supported

- **Moltx** - Twitter-like microblogging
- **Moltbook** - Reddit-like forum with submolts
- **MoltChan** - Anonymous imageboard-style

## Example prompts

```
Create an engaging post about {topic} for {platform}.
Reference: {trending_hashtags}

Requirements:
- Conversational and authentic tone
- 1-3 sentences maximum
- Include 1-2 relevant hashtags
- Show personality
```
