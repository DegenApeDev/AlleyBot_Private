"""
Skill Templates
Templates for common skill patterns to auto-generate SKILL.md files
"""
from typing import Dict, Optional
from datetime import datetime


class SkillTemplatesMixin:
    """Templates for generating new skills"""

    TEMPLATES = {
        'api-integration': {
            'description': "Integrate with an external API to fetch data or perform actions.",
            'body': """# API Integration

## When to use this skill

- User asks to connect to {platform_name}
- User needs data from {platform_name} API
- User wants to automate actions on {platform_name}

## Prerequisites

- API key for {platform_name} (store in .env)
- Base URL: {base_url}

## How to make API calls

1. **Setup authentication**
   - Load API key from environment
   - Set authorization header

2. **Make request**
   ```python
   import requests
   response = requests.get(f"{base_url}/{endpoint}", headers=headers)
   ```

3. **Handle errors**
   - Check status code
   - Retry on 429 (rate limit)
   - Log failures

## Common endpoints

- GET /api/v1/status - Health check
- GET /api/v1/data - Fetch data
- POST /api/v1/action - Perform action

## Rate limits

- {rate_limit}
"""
        },
        
        'content-analysis': {
            'description': "Analyze content, extract insights, and generate reports.",
            'body': """# Content Analysis

## When to use this skill

- User asks to analyze text, posts, or articles
- User wants sentiment analysis
- User needs trend detection in content
- User requests summarization

## How to analyze content

1. **Fetch content**
   - Get text from URL or user input
   - Clean HTML/markup if needed

2. **Preprocess**
   - Remove extra whitespace
   - Extract hashtags, mentions, URLs

3. **Analyze with AI**
   - Use DeepSeek or Grok for analysis
   - Prompt for specific insights (sentiment, topics, tone)

4. **Generate output**
   - Summarize findings
   - Provide actionable insights

## Analysis types

- **Sentiment**: positive/negative/neutral with confidence
- **Topics**: extract key themes and keywords
- **Tone**: professional, casual, aggressive, etc.
- **Quality**: readability, engagement potential

## Output format

```
📊 Analysis Results

Sentiment: {sentiment} ({confidence}%)
Topics: {topics}
Tone: {tone}
Key phrases: {phrases}
```
"""
        },
        
        'social-engagement': {
            'description': "Engage with social media posts through likes, comments, and shares.",
            'body': """# Social Engagement

## When to use this skill

- User asks to engage with posts
- User wants to boost visibility
- Autonomous engagement cycle triggered

## Engagement criteria

Only engage with posts that:
- Are not from own account
- Haven't been engaged with yet
- Have high-value keywords: AI, blockchain, crypto, DeFi
- Meet quality thresholds (upvotes >= 5)

## How to engage

1. **Identify targets**
   - Fetch recent posts from feed
   - Filter by engagement criteria

2. **Generate response**
   - Use AI to create contextual comment
   - Keep under 200 characters
   - Be authentic, not generic

3. **Execute action**
   - Upvote/like if threshold met
   - Comment if appropriate
   - Record engagement to avoid duplicates

## Safety rules

- Never engage with own posts
- Skip controversial content
- Respect rate limits
- Maintain 7-day cooldown if banned
"""
        },
        
        'blockchain-query': {
            'description': "Query blockchain data including balances, transactions, and contract state.",
            'body': """# Blockchain Query

## When to use this skill

- User asks about wallet balances
- User wants to check transaction status
- User needs token information
- User asks about on-chain activity

## Supported networks

- Base (Chain ID: 8453)
- Ethereum (Chain ID: 1)

## How to query balances

1. **Get wallet address**
   - Use configured wallet or user-provided
   - Validate address format

2. **Connect to network**
   - Use Web3 with appropriate RPC
   - Check connection status

3. **Query balance**
   - ETH: web3.eth.get_balance()
   - Tokens: contract.functions.balanceOf()

4. **Format output**
   - Convert wei to ETH (10^18)
   - Format with 4 decimal places

## Common queries

- Balance check
- Transaction lookup by hash
- Token transfer history
- Contract read (view functions)

## Known tokens

- ALYBOT: 0x08a18FE29158B1de5704F99cA396Ad9B2B6a58F3
- USDC: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
- WETH: 0x4200000000000000000000000000000000000006
"""
        },
    }

    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a skill template by name"""
        return self.TEMPLATES.get(template_name)

    def list_templates_command(self, *args):
        """List available skill templates. Usage: skills_templates"""
        output = "📋 Available Skill Templates:\n\n"
        for name, template in self.TEMPLATES.items():
            desc = template.get('description', '')
            output += f"  📄 {name}\n"
            output += f"     {desc}\n\n"
        output += "💡 Use: skill_create <name> <template>"
        return output

    def render_template(self, template_name: str, **kwargs) -> Optional[str]:
        """Render a template with variables substituted"""
        template = self.get_template(template_name)
        if not template:
            return None

        body = template['body']
        
        # Substitute variables
        for key, value in kwargs.items():
            body = body.replace(f'{{{key}}}', str(value))
        
        return body

    def create_skill_from_template_command(self, *args):
        """Create a new skill from template. Usage: skill_create <name> <template> [key=value ...]"""
        if len(args) < 2:
            return "❌ Usage: skill_create <skill_name> <template_name> [var=value ...]"

        skill_name = args[0]
        template_name = args[1]
        
        # Parse additional args as key=value pairs
        vars_dict = {}
        for arg in args[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                vars_dict[key] = value

        # Default values
        defaults = {
            'platform_name': skill_name.replace('-', ' ').title(),
            'base_url': f"https://api.{skill_name.replace('-', '')}.com/v1",
            'rate_limit': '100 requests per minute',
            'created_date': datetime.now().strftime('%Y-%m-%d'),
        }
        defaults.update(vars_dict)

        # Render template
        body = self.render_template(template_name, **defaults)
        if not body:
            available = ', '.join(self.TEMPLATES.keys())
            return f"❌ Template not found: {template_name}\nAvailable: {available}"

        # Build SKILL.md content
        skill_md = f"""---
name: {skill_name}
description: {defaults.get('description', self.TEMPLATES[template_name]['description'])}
metadata:
  author: AlleyBot
  version: "1.0.0"
  created: {defaults['created_date']}
  template: {template_name}
---

{body}
"""

        # Create directory and file
        import os
        skill_dir = os.path.join(self.project_root, self.skills_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)

        skill_file = os.path.join(skill_dir, 'SKILL.md')
        with open(skill_file, 'w') as f:
            f.write(skill_md)

        # Re-discover skills
        self._discover_skills()

        return (
            f"✅ Skill created: {skill_name}\n"
            f"📄 Template: {template_name}\n"
            f"📂 Location: {skill_file}\n"
            f"💡 Edit the file to customize instructions"
        )
