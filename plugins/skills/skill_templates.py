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

    def skill_autocode_command(self, *args):
        """
        Autonomously code a skill from task description.
        Usage: skill_autocode <skill_name> <task_description>
        
        This uses the autonomous coder to generate a skill without templates.
        The skill is auto-generated, tested, and published.
        """
        if len(args) < 2:
            return "❌ Usage: skill_autocode <skill_name> <task_description>\nExample: skill_autocode price-tracker 'Track crypto prices and alert on significant changes'"
        
        skill_name = args[0]
        task_description = ' '.join(args[1:])
        
        print(f"🤖 Autocoding skill: {skill_name}")
        print(f"📝 Task: {task_description}")
        
        # Check if autonomous coder is available via selfimprove plugin
        selfimprove = None
        try:
            if hasattr(self, 'core') and self.core:
                selfimprove = self.core.plugin_manager.plugins.get('selfimprove')
        except Exception:
            pass
        
        if not selfimprove or not hasattr(selfimprove, 'autonomous_coder') or not selfimprove.autonomous_coder:
            # Fallback: Generate SKILL.md directly without autonomous coder
            return self._generate_skill_without_coder(skill_name, task_description)
        
        # Use autonomous coder to generate Python code
        try:
            coder = selfimprove.autonomous_coder
            
            # Create task for skill generation
            task = f"""Create a Python skill module for: {task_description}

Requirements:
1. Create a class named {skill_name.replace('-', '_').title()}Skill
2. Include an execute() method that takes **kwargs
3. Add proper error handling and logging
4. Include docstrings explaining the skill's purpose
5. Return results as a dictionary with 'success' key

The skill should be self-contained and ready to use."""
            
            # Generate code draft
            draft_result = coder.create_draft(task)
            if not draft_result.get('draft_id'):
                return f"❌ Failed to create code draft: {draft_result.get('error', 'Unknown error')}"
            
            draft_id = draft_result['draft_id']
            print(f"📋 Code draft created: {draft_id}")
            
            # Test the draft
            test_result = coder.test_code(draft_id)
            if test_result.get('status') == 'test_error':
                return f"❌ Skill code failed tests: {test_result.get('error')}"
            
            if test_result.get('tests_failed', 0) > 0:
                return f"❌ Skill has {test_result['tests_failed']} failing tests. Fix before publishing."
            
            print(f"✅ Code passed tests: {test_result.get('tests_passed', 0)} passed")
            
            # Get the code and convert to SKILL.md
            draft = coder.get_draft(draft_id)
            if not draft or 'files' not in draft:
                return "❌ Could not retrieve generated code"
            
            # Extract Python code from draft
            python_code = None
            for file_info in draft.get('files', []):
                if file_info.get('path', '').endswith('.py'):
                    python_code = file_info.get('content')
                    break
            
            if not python_code:
                return "❌ No Python code generated"
            
            # Create SKILL.md from generated code
            return self._create_skill_from_code(skill_name, task_description, python_code)
            
        except Exception as e:
            print(f"⚠️ Autonomous coder failed: {e}")
            return self._generate_skill_without_coder(skill_name, task_description)
    
    def _generate_skill_without_coder(self, skill_name: str, task_description: str) -> str:
        """Generate a skill using AI without the autonomous coder"""
        try:
            # Try Grok first
            from grok_ai import grok_ai
            if grok_ai.enabled:
                prompt = f"""Generate a complete Python skill module for this task:
{task_description}

Create:
1. A class named {skill_name.replace('-', '_').title()}Skill with execute() method
2. Proper error handling and docstrings
3. The skill should be self-contained

Return ONLY the Python code, no explanation."""

                data = {
                    "model": grok_ai.model,
                    "messages": [
                        {"role": "system", "content": "You are a Python expert. Generate clean, well-documented code."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.5,
                }
                
                response = grok_ai._make_api_request(data)
                python_code = grok_ai._extract_text(response)
                
                if python_code:
                    return self._create_skill_from_code(skill_name, task_description, python_code)
        except Exception as e:
            print(f"⚠️ Grok generation failed: {e}")
        
        # Fallback: Create a basic template-based skill
        return self._create_basic_skill(skill_name, task_description)
    
    def _create_skill_from_code(self, skill_name: str, description: str, python_code: str) -> str:
        """Convert Python code to SKILL.md format and save"""
        import os
        from datetime import datetime
        
        # Create SKILL.md content
        skill_md = f"""---
name: {skill_name}
description: {description}
metadata:
  author: AlleyBot (Autocoded)
  version: "1.0.0"
  created: {datetime.now().strftime('%Y-%m-%d')}
  autocoded: true
---

# {skill_name.replace('-', ' ').title()}

## Description

{description}

## Implementation

```python
{python_code}
```

## Usage

```python
from skills.{skill_name} import {skill_name.replace('-', '_').title()}Skill

skill = {skill_name.replace('-', '_').title()}Skill()
result = skill.execute(**kwargs)
```
"""
        
        # Create directory and file
        skill_dir = os.path.join(self.project_root, self.skills_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        
        skill_file = os.path.join(skill_dir, 'SKILL.md')
        with open(skill_file, 'w') as f:
            f.write(skill_md)
        
        # Also save the Python code for direct import
        py_file = os.path.join(skill_dir, f"{skill_name.replace('-', '_')}.py")
        with open(py_file, 'w') as f:
            f.write(python_code)
        
        # Re-discover skills
        self._discover_skills()
        
        return (
            f"✅ Autocoded skill: {skill_name}\n"
            f"📄 Description: {description[:80]}...\n"
            f"📂 SKILL.md: {skill_file}\n"
            f"🐍 Python: {py_file}\n"
            f"💡 Ready to use via skill_activate {skill_name}"
        )
    
    def _create_basic_skill(self, skill_name: str, description: str) -> str:
        """Create a basic skill template when AI generation fails"""
        import os
        from datetime import datetime
        
        python_code = f'''"""
{skill_name.replace('-', ' ').title()} Skill
{description}
"""

class {skill_name.replace('-', '_').title()}Skill:
    """Skill implementation for {description}"""
    
    def __init__(self):
        self.name = "{skill_name}"
        self.description = "{description}"
    
    def execute(self, **kwargs):
        """
        Execute the skill.
        
        Args:
            **kwargs: Variable arguments based on task needs
            
        Returns:
            dict: Result with 'success' status
        """
        try:
            # TODO: Implement skill logic here
            print(f"Executing {{self.name}}: {{self.description}}")
            
            return {{
                'success': True,
                'skill': self.name,
                'result': 'Skill executed successfully'
            }}
        except Exception as e:
            return {{
                'success': False,
                'skill': self.name,
                'error': str(e)
            }}

# Backwards compatibility
def main(**kwargs):
    skill = {skill_name.replace('-', '_').title()}Skill()
    return skill.execute(**kwargs)
'''
        
        return self._create_skill_from_code(skill_name, description, python_code)
