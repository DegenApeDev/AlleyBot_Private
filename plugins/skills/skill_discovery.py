"""
Agent Skills Framework Plugin
Lightweight skill discovery and execution following agentskills.io specification
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin


class SkillDiscoveryMixin:
    """Scan and index all SKILL.md files in the skills directory"""

    def __init__(self, config):
        super().__init__(config)
        self.skills_dir = config.get('skills_dir', 'skills')
        self.skill_index: Dict[str, Dict] = {}  # name -> metadata only
        self.full_skills: Dict[str, Dict] = {}   # name -> full skill data

    def initialize(self, api, core):
        super().initialize(api, core)
        self._discover_skills()
        print(f"🔧 Agent Skills: Discovered {len(self.skill_index)} skills")

    def _discover_skills(self):
        """Scan skills directory and index all SKILL.md files (lazy loading)"""
        skills_path = Path(self.project_root) / self.skills_dir
        if not skills_path.exists():
            print(f"⚠️ Skills directory not found: {skills_path}")
            return

        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / 'SKILL.md'
            if not skill_file.exists():
                continue

            try:
                # Parse only frontmatter (name + description) for discovery
                frontmatter = self._parse_frontmatter(skill_file)
                if frontmatter and 'name' in frontmatter:
                    self.skill_index[frontmatter['name']] = {
                        'name': frontmatter.get('name'),
                        'description': frontmatter.get('description', ''),
                        'path': str(skill_dir),
                        'metadata': frontmatter.get('metadata', {})
                    }
            except Exception as e:
                print(f"⚠️ Failed to parse skill {skill_dir.name}: {e}")

    def _parse_frontmatter(self, skill_file: Path) -> Optional[Dict]:
        """Extract YAML frontmatter from SKILL.md"""
        try:
            content = skill_file.read_text(encoding='utf-8')
            # Look for --- ... --- pattern
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                frontmatter_text = match.group(1)
                return yaml.safe_load(frontmatter_text)
            return None
        except Exception as e:
            print(f"⚠️ Error parsing frontmatter: {e}")
            return None

    def _load_full_skill(self, skill_name: str) -> Optional[Dict]:
        """Load full skill content including body (progressive disclosure)"""
        if skill_name in self.full_skills:
            return self.full_skills[skill_name]

        if skill_name not in self.skill_index:
            return None

        skill_info = self.skill_index[skill_name]
        skill_path = Path(skill_info['path']) / 'SKILL.md'

        try:
            content = skill_path.read_text(encoding='utf-8')
            # Parse frontmatter and body
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2).strip()
            else:
                frontmatter = {}
                body = content

            full_skill = {
                'name': skill_name,
                'description': frontmatter.get('description', ''),
                'body': body,
                'frontmatter': frontmatter,
                'path': skill_info['path']
            }

            # Check for optional directories
            scripts_dir = Path(skill_info['path']) / 'scripts'
            references_dir = Path(skill_info['path']) / 'references'
            assets_dir = Path(skill_info['path']) / 'assets'

            if scripts_dir.exists():
                full_skill['scripts'] = [str(f) for f in scripts_dir.iterdir() if f.is_file()]
            if references_dir.exists():
                full_skill['references'] = [str(f) for f in references_dir.iterdir() if f.is_file()]
            if assets_dir.exists():
                full_skill['assets'] = [str(f) for f in assets_dir.iterdir() if f.is_file()]

            self.full_skills[skill_name] = full_skill
            return full_skill

        except Exception as e:
            print(f"⚠️ Error loading skill {skill_name}: {e}")
            return None

    def list_skills_command(self, *args):
        """List all discovered skills. Usage: skills_list"""
        if not self.skill_index:
            return "📭 No skills discovered"

        output = f"🔧 {len(self.skill_index)} Skills Available:\n\n"
        for name, info in sorted(self.skill_index.items()):
            desc = info.get('description', '')[:60]
            output += f"  📄 {name}\n"
            if desc:
                output += f"     {desc}...\n"
        return output

    def skill_info_command(self, *args):
        """Get detailed info about a skill. Usage: skill_info <name>"""
        if not args:
            return "❌ Usage: skill_info <skill_name>"

        skill_name = args[0]
        skill = self._load_full_skill(skill_name)

        if not skill:
            return f"❌ Skill not found: {skill_name}"

        output = f"📄 {skill['name']}\n"
        output += f"📝 {skill['description']}\n\n"

        fm = skill.get('frontmatter', {})
        if 'license' in fm:
            output += f"📜 License: {fm['license']}\n"
        if 'metadata' in fm:
            meta = fm['metadata']
            if 'author' in meta:
                output += f"👤 Author: {meta['author']}\n"
            if 'version' in meta:
                output += f"🔢 Version: {meta['version']}\n"

        # Check for optional content
        if skill.get('scripts'):
            output += f"\n📁 Scripts: {len(skill['scripts'])} files\n"
        if skill.get('references'):
            output += f"📚 References: {len(skill['references'])} files\n"
        if skill.get('assets'):
            output += f"🎨 Assets: {len(skill['assets'])} files\n"

        output += f"\n📂 Path: {skill['path']}\n"
        return output
