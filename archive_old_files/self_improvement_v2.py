#!/usr/bin/env python3
"""
AlleyBot Self-Improvement System v2
Generates skills in ClawHub format (SKILL.md with YAML frontmatter)
"""
import os
import json
import requests
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SelfImprovementV2:
    """System for autonomous skill generation in ClawHub format"""
    
    def __init__(self, deepseek_api_key=None):
        self.deepseek_api_key = deepseek_api_key or os.getenv('DEEPSEEK_API_KEY')
        self.skills_dir = Path("skills")
        self.skills_dir.mkdir(exist_ok=True)
        
        self.improvement_log = Path("memory/improvement_log.json")
        self.improvement_log.parent.mkdir(exist_ok=True)
        
        # Load improvement history
        self.history = self._load_history()
        
        # Skill registry
        self.skills = self._load_skills()
    
    def _load_history(self):
        """Load improvement history"""
        if self.improvement_log.exists():
            with open(self.improvement_log) as f:
                return json.load(f)
        return {
            "improvements": [],
            "failed_attempts": [],
            "active_skills": []
        }
    
    def _save_history(self):
        """Save improvement history"""
        with open(self.improvement_log, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _load_skills(self):
        """Load available skills from skills directory"""
        skills = {}
        if self.skills_dir.exists():
            for skill_dir in self.skills_dir.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith('_'):
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        skills[skill_dir.name] = {
                            "path": str(skill_dir),
                            "skill_file": str(skill_md),
                            "loaded": False
                        }
        return skills
    
    def analyze_improvement_opportunities(self):
        """Analyze what skills would be most valuable for AlleyBot"""
        opportunities = [
            {
                "type": "skill",
                "name": "moltbook-engagement-analyzer",
                "description": "Analyze Moltbook posts to identify high-value engagement opportunities based on author influence, topic relevance, and timing",
                "priority": 9,
                "estimated_impact": "Better engagement ROI"
            },
            {
                "type": "skill",
                "name": "crypto-donation-tracker",
                "description": "Monitor BASE/ETH/BTC wallets for donations and automatically post thank-you messages with donor recognition",
                "priority": 9,
                "estimated_impact": "Better donor relationships"
            },
            {
                "type": "skill",
                "name": "trending-topic-detector",
                "description": "Detect trending topics on Moltbook by analyzing post frequency, engagement patterns, and keyword clustering",
                "priority": 8,
                "estimated_impact": "More timely, relevant posts"
            },
            {
                "type": "skill",
                "name": "sentiment-analyzer",
                "description": "Analyze sentiment of posts and comments to tailor response tone and engagement strategy",
                "priority": 7,
                "estimated_impact": "More authentic interactions"
            },
            {
                "type": "skill",
                "name": "response-optimizer",
                "description": "Cache and optimize common response patterns to reduce API calls and improve response speed",
                "priority": 6,
                "estimated_impact": "Faster responses, lower costs"
            }
        ]
        
        # Filter out already implemented skills
        existing = set(self.skills.keys())
        opportunities = [opp for opp in opportunities if opp['name'] not in existing]
        
        return sorted(opportunities, key=lambda x: x['priority'], reverse=True)
    
    def generate_skill(self, opportunity):
        """
        Generate a skill in ClawHub format using DeepSeek
        
        Args:
            opportunity: Dict with skill details
        
        Returns:
            Dict with skill_dir, skill_md, scripts, references, assets
        """
        print(f"\n📝 Generating skill: {opportunity['name']}")
        print(f"   Description: {opportunity['description']}")
        
        # Create skill directory
        skill_dir = self.skills_dir / opportunity['name']
        skill_dir.mkdir(exist_ok=True)
        
        # Generate SKILL.md using Grok
        prompt = f"""You are creating a skill for AlleyBot, an AI bot on Moltbook (a social platform).

Create a skill in ClawHub format with these components:

**Skill Name:** {opportunity['name']}
**Description:** {opportunity['description']}
**Context:** AlleyBot runs on a Raspberry Pi, has limited resources, and needs to:
- Engage with posts on Moltbook
- Build relationships with other bots and users
- Track donations to BASE/ETH/BTC wallets
- Create valuable content
- Learn and improve over time

**Your task:** Generate a complete SKILL.md file following this structure:

```markdown
---
name: {opportunity['name']}
description: {opportunity['description']}
---

# Skill Title

Brief overview of what this skill does.

## When to Use This Skill

Clear triggers for when AlleyBot should use this skill.

## Quick Start

Minimal example showing basic usage.

## Core Workflow

Step-by-step instructions for the main workflow.

## Implementation Details

Technical details, API integrations, data structures.

## Examples

Concrete examples of using the skill.

## Error Handling

Common issues and how to handle them.
```

**Important guidelines:**
- Be concise - assume AlleyBot is smart
- Use imperative/infinitive form
- Include only essential information
- Provide concrete examples
- Focus on procedural knowledge AlleyBot doesn't have
- If scripts are needed, describe them (we'll generate separately)
- Keep under 500 lines

Generate the complete SKILL.md content now:"""

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are an expert at creating concise, effective skills for AI agents in ClawHub format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                },
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ DeepSeek API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
            
            # Parse OpenAI-compatible response
            resp_json = response.json()
            if 'choices' in resp_json and len(resp_json['choices']) > 0:
                skill_content = resp_json['choices'][0]['message']['content']
            else:
                print(f"❌ Unexpected response format: {resp_json}")
                return None
            
            # Clean up markdown code blocks if present
            if skill_content.startswith('```'):
                lines = skill_content.split('\n')
                skill_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else skill_content
            
            print(f"✅ Generated {len(skill_content)} characters")
            
            # Save SKILL.md
            skill_md_path = skill_dir / "SKILL.md"
            with open(skill_md_path, 'w') as f:
                f.write(skill_content)
            
            # Create optional directories (empty for now)
            (skill_dir / "scripts").mkdir(exist_ok=True)
            (skill_dir / "references").mkdir(exist_ok=True)
            (skill_dir / "assets").mkdir(exist_ok=True)
            
            return {
                "skill_dir": str(skill_dir),
                "skill_md": str(skill_md_path),
                "content": skill_content
            }
            
        except Exception as e:
            print(f"❌ Error generating skill: {e}")
            return None
    
    def validate_skill(self, skill_data):
        """
        Validate skill follows ClawHub format
        
        Args:
            skill_data: Dict from generate_skill
        
        Returns:
            (bool, list of issues)
        """
        issues = []
        
        if not skill_data:
            return False, ["Skill generation failed"]
        
        skill_md_path = Path(skill_data['skill_md'])
        
        # Check file exists
        if not skill_md_path.exists():
            issues.append("SKILL.md file not found")
            return False, issues
        
        # Read and parse
        with open(skill_md_path) as f:
            content = f.read()
        
        # Check for YAML frontmatter
        if not content.startswith('---'):
            issues.append("Missing YAML frontmatter")
        else:
            # Parse frontmatter
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    
                    # Check required fields
                    if 'name' not in frontmatter:
                        issues.append("Missing 'name' in frontmatter")
                    if 'description' not in frontmatter:
                        issues.append("Missing 'description' in frontmatter")
                else:
                    issues.append("Invalid frontmatter format")
            except Exception as e:
                issues.append(f"Error parsing frontmatter: {e}")
        
        # Check minimum content length
        if len(content) < 200:
            issues.append("Skill content too short")
        
        return len(issues) == 0, issues
    
    def deploy_skill(self, skill_data, opportunity):
        """
        Deploy validated skill
        
        Args:
            skill_data: Dict from generate_skill
            opportunity: Original opportunity dict
        
        Returns:
            bool: Success
        """
        try:
            # Log deployment
            deployment = {
                "skill_name": opportunity['name'],
                "skill_dir": skill_data['skill_dir'],
                "deployed_at": datetime.now().isoformat(),
                "description": opportunity['description'],
                "priority": opportunity['priority']
            }
            
            self.history['improvements'].append(deployment)
            self.history['active_skills'].append(opportunity['name'])
            self._save_history()
            
            # Update skills registry
            self.skills[opportunity['name']] = {
                "path": skill_data['skill_dir'],
                "skill_file": skill_data['skill_md'],
                "loaded": False
            }
            
            print(f"✅ Skill deployed: {skill_data['skill_dir']}")
            return True
            
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
    
    def autonomous_improvement_cycle(self, max_improvements=1):
        """
        Run autonomous improvement cycle
        
        Args:
            max_improvements: Max number of skills to generate
        """
        print(f"\n{'='*60}")
        print("🧠 ALLEYBOT SELF-IMPROVEMENT CYCLE (ClawHub Format)")
        print(f"{'='*60}\n")
        
        # Analyze opportunities
        print("📊 Analyzing improvement opportunities...\n")
        opportunities = self.analyze_improvement_opportunities()
        
        if not opportunities:
            print("✅ No new improvement opportunities found")
            return
        
        print(f"🎯 Found {len(opportunities)} opportunities:")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"   {i}. {opp['name']} (priority: {opp['priority']}/10)")
            print(f"      {opp['description']}")
        
        # Generate skills
        completed = 0
        for opportunity in opportunities[:max_improvements]:
            print(f"\n🔧 Creating skill: {opportunity['name']}")
            print(f"   Description: {opportunity['description']}")
            print(f"   Priority: {opportunity['priority']}/10\n")
            
            # Generate
            skill_data = self.generate_skill(opportunity)
            if not skill_data:
                print(f"❌ Failed to generate skill")
                continue
            
            # Validate
            print("🔍 Validating skill...")
            valid, issues = self.validate_skill(skill_data)
            
            if not valid:
                print(f"❌ Validation failed:")
                for issue in issues:
                    print(f"   - {issue}")
                continue
            
            print("✅ Skill validated successfully")
            
            # Deploy
            print("🚀 Deploying skill...")
            if self.deploy_skill(skill_data, opportunity):
                print(f"🎉 Skill complete: {opportunity['name']}")
                print(f"   Impact: {opportunity['estimated_impact']}")
                completed += 1
            else:
                print(f"❌ Deployment failed")
        
        print(f"\n{'='*60}")
        print(f"✅ Completed: {completed}/{max_improvements} skills")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    improver = SelfImprovementV2()
    
    print("\n📚 Current Skills:")
    if improver.skills:
        for name, info in improver.skills.items():
            print(f"   - {name}")
    else:
        print("   (none yet)")
    
    print("\n" + "="*60)
    response = input("Run autonomous improvement cycle? (y/n): ")
    print("="*60)
    
    if response.lower() == 'y':
        improver.autonomous_improvement_cycle(max_improvements=1)
