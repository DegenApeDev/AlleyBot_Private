"""
Skill Generator
Auto-generate SKILL.md files from platform skill.md files
Converts existing platform skills to Agent Skills format
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List


class SkillGeneratorMixin:
    """Generate Agent Skills from existing platform skill files"""

    def __init__(self, config):
        super().__init__(config)
        self.generated_skills: List[str] = []

    def generate_skill_from_platform(self, platform: str) -> Optional[str]:
        """Convert a platform skill.md to Agent Skills SKILL.md format"""
        skill_file = os.path.join(self.project_root, 'skills', f'{platform}_skill.md')
        
        if not os.path.exists(skill_file):
            return None

        try:
            with open(skill_file, 'r') as f:
                content = f.read()

            # Parse existing skill content
            skill_name = platform.lower().replace('_', '-')
            description = self._extract_description(content)
            
            # Extract key sections
            capabilities = self._extract_capabilities(content)
            endpoints = self._extract_endpoints(content)
            
            # Build SKILL.md content
            skill_md = f"""---
name: {skill_name}
description: {description}
metadata:
  author: AlleyBot
  version: "1.0.0"
  generated_from: {platform}_skill.md
  generated_at: {datetime.now().isoformat()}
---

# {platform.title()} Platform Skill

## When to use this skill

{description}

## Capabilities

"""
            # Add capabilities as steps
            for cap in capabilities:
                skill_md += f"- {cap}\n"
            
            skill_md += "\n## How to use\n\n"
            
            # Add endpoints as steps
            if endpoints:
                skill_md += "### API Endpoints\n\n"
                for endpoint in endpoints:
                    skill_md += f"- {endpoint}\n"
                skill_md += "\n"
            
            # Add execution steps
            skill_md += """### Execution steps

1. **Initialize connection**
   - Load API credentials
   - Validate connectivity

2. **Perform action**
   - Select appropriate endpoint
   - Format request parameters
   - Handle errors gracefully

3. **Log results**
   - Record activity to memory
   - Update metrics

## Error handling

- Retry on transient failures (3 attempts)
- Log errors with context
- Notify on critical failures
"""

            # Create skill directory and save
            skill_dir = os.path.join(self.project_root, 'skills', skill_name)
            os.makedirs(skill_dir, exist_ok=True)
            
            output_file = os.path.join(skill_dir, 'SKILL.md')
            with open(output_file, 'w') as f:
                f.write(skill_md)
            
            self.generated_skills.append(skill_name)
            
            return output_file
            
        except Exception as e:
            print(f"❌ Failed to generate skill for {platform}: {e}")
            return None

    def _extract_description(self, content: str) -> str:
        """Extract description from skill.md content"""
        # Look for first paragraph after title
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# ') and i + 1 < len(lines):
                # Return next non-empty line
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        return lines[j].strip()[:200]
        return f"Interact with platform using AI-powered capabilities"

    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities from skill.md content"""
        capabilities = []
        
        # Look for feature/capability lists
        lines = content.split('\n')
        in_list = False
        
        for line in lines:
            # Check for bullet points
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                cap = line.strip()[2:].strip()
                if cap and len(cap) < 100:
                    capabilities.append(cap)
                in_list = True
            elif in_list and not line.strip():
                in_list = False
        
        return capabilities[:10]  # Limit to 10

    def _extract_endpoints(self, content: str) -> List[str]:
        """Extract API endpoints from skill.md content"""
        endpoints = []
        
        # Look for URL patterns
        url_pattern = r'https?://[^\s\)\]\>]+'
        matches = re.findall(url_pattern, content)
        
        for url in matches:
            # Clean up the URL
            url = url.rstrip('.,;')
            if url not in endpoints and len(url) < 200:
                endpoints.append(url)
        
        return endpoints[:5]  # Limit to 5

    def generate_all_platform_skills_command(self, *args):
        """Generate Agent Skills from all platform skill files. Usage: skills_generate_all"""
        skills_dir = os.path.join(self.project_root, 'skills')
        if not os.path.exists(skills_dir):
            return "❌ Skills directory not found"

        # Find all *_skill.md files
        platform_skills = []
        for f in os.listdir(skills_dir):
            if f.endswith('_skill.md'):
                platform = f.replace('_skill.md', '')
                platform_skills.append(platform)

        if not platform_skills:
            return "📭 No platform skill files found (*.md)"

        output = f"🔧 Generating Agent Skills from {len(platform_skills)} platforms:\n\n"
        generated = []
        failed = []

        for platform in platform_skills:
            result = self.generate_skill_from_platform(platform)
            if result:
                output += f"  ✅ {platform} -> {result}\n"
                generated.append(platform)
            else:
                output += f"  ❌ {platform} failed\n"
                failed.append(platform)

        # Re-discover skills
        self._discover_skills()

        output += f"\n📊 Results: {len(generated)} generated, {len(failed)} failed"
        return output

    def generate_skill_command(self, *args):
        """Generate Agent Skill from a platform. Usage: skill_generate <platform>"""
        if not args:
            return "❌ Usage: skill_generate <platform_name>"

        platform = args[0]
        result = self.generate_skill_from_platform(platform)

        if result:
            # Re-discover
            self._discover_skills()
            return (
                f"✅ Skill generated: {platform}\n"
                f"📄 Output: {result}\n"
                f"💡 Use 'skill_activate {platform.lower().replace('_', '-')}' to load"
            )
        else:
            return f"❌ Failed to generate skill for {platform}"
