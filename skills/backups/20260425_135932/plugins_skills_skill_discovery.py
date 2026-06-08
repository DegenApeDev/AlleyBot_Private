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
            # Still add core plugins
        else:
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
                        metadata = frontmatter.get('metadata', {}).copy()
                        aliases = metadata.get('aliases', frontmatter.get('aliases', []))
                        aliases = [str(a).strip() for a in aliases] if isinstance(aliases, (list, tuple)) else []
                        metadata['aliases'] = aliases
                        self.skill_index[frontmatter['name']] = {
                            'name': frontmatter.get('name'),
                            'description': frontmatter.get('description', ''),
                            'path': str(skill_dir),
                            'metadata': metadata
                        }
                except Exception as e:
                    print(f"⚠️ Failed to parse skill {skill_dir.name}: {e}")

        # Always include core plugins
        plugins_dir = Path(self.project_root) / "plugins"
        core_plugins = {
            "core": {
                "description": "Core AlleyBot plugin - essential commands, configuration, and system utilities.",
                "aliases": []
            },
            "clawbr_debates": {
                "description": "Clawbr Debates - AI-powered debate simulation, logic, and persuasion skills.",
                "aliases": ["debates", "debate", "clawbr-debates"]
            }
        }
        for plugin_name, data in core_plugins.items():
            plugin_path = plugins_dir / plugin_name
            added = False
            skill_file = plugin_path / "SKILL.md"
            if skill_file.exists():
                try:
                    frontmatter = self._parse_frontmatter(skill_file)
                    if frontmatter and frontmatter.get('name') == plugin_name:
                        metadata = frontmatter.get('metadata', {}).copy()
                        aliases = metadata.get('aliases', frontmatter.get('aliases', data['aliases']))
                        aliases = [str(a).strip() for a in aliases] if isinstance(aliases, (list, tuple)) else data['aliases']
                        metadata['aliases'] = aliases
                        self.skill_index[plugin_name] = {
                            'name': plugin_name,
                            'description': frontmatter.get('description', data['description']),
                            'path': str(plugin_path),
                            'metadata': metadata
                        }
                        added = True
                except Exception as e:
                    print(f"⚠️ Failed to parse plugin skill {plugin_name}: {e}")
            if not added:
                metadata = {'aliases': data['aliases']}
                self.skill_index[plugin_name] = {
                    'name': plugin_name,
                    'description': data['description'],
                    'path': str(plugin_path),
                    'metadata': metadata
                }

    def _resolve_alias(self, name: str) -> Optional[str]:
        """Resolve skill name or alias to canonical skill name"""
        if not name:
            return None
        if name in self.skill_index:
            return name
        for skill_name, info in self.skill_index.items():
            aliases = info['metadata'].get('aliases', [])
            if name in aliases:
                return skill_name
        return None

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
            if not skill_path.exists():
                # Fallback for plugins without SKILL.md
                metadata = skill_info['metadata'].copy()
                frontmatter = {
                    'name': skill_name,
                    'description': skill_info['description'],
                    'metadata': metadata
                }
                body = f"Plugin-based skill without dedicated SKILL.md file.\n\nPath: {skill_info['path']}\n\nMetadata:\n{yaml.dump(metadata, default_flow_style=False)}"
                full_skill = {
                    'name': skill_name,
                    'description': skill_info['description'],
                    'body': body,
                    'frontmatter': frontmatter,
                    'path': skill_info['path']
                }
            else:
                content = skill_path.read_text(encoding='utf-8')
                # Parse frontmatter and body
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
                if match:
                    frontmatter_text = match.group(1)
                    frontmatter = yaml.safe_load(frontmatter_text)
                    body = match.group(2).strip()
                else:
                    frontmatter = {
                        'name': skill_name,
                        'description': skill_info['description']
                    }
                    body = content.strip()
                # Standardize aliases in metadata
                metadata = frontmatter.get('metadata', {}).copy()
                aliases = metadata.get('aliases', frontmatter.get('aliases', []))
                aliases = [str(a).strip() for a in aliases] if isinstance(aliases, (list, tuple)) else []
                metadata['aliases'] = aliases
                frontmatter['metadata'] = metadata
                full_skill = {
                    'name': skill_name,
                    'description': frontmatter.get('description', skill_info['description']),
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
            if len(info.get('description', '')) > 60:
                desc += '...'
            output += f"  📄 {name}\n"
            if desc:
                output += f"     {desc}\n"
            aliases = info['metadata'].get('aliases', [])
            if aliases:
                aliases_str = ', '.join(aliases[:3])
                if len(aliases) > 3:
                    aliases_str += '...'
                output += f"     🔗 {aliases_str}\n"
            output += "\n"
        return output.rstrip('\n')

    def skill_info_command(self, *args):
        """Get detailed info about a skill. Usage: skill_info <name>"""
        if not args:
            return "❌ Usage: skill_info <skill_name or alias>"

        requested = args[0]
        skill_name = self._resolve_alias(requested)

        if skill_name is None:
            return f"❌ Skill or alias '{requested}' not found"

        skill = self._load_full_skill(skill_name)

        if not skill:
            return f"❌ Failed to load skill '{skill_name}'"

        output = f"📄 {skill['name']}"
        if requested != skill_name:
            output += f" (alias: {requested})"
        output += "\n"
        output += f"📝 {skill['description']}\n\n"

        fm = skill.get('frontmatter', {})
        metadata = fm.get('metadata', {})
        if 'license' in fm:
            output += f"📜 License: {fm['license']}\n"
        if 'author' in metadata:
            output += f"👤 Author: {metadata['author']}\n"
        if 'version' in metadata:
            output += f"🔢 Version: {metadata['version']}\n"
        aliases = metadata.get('aliases', [])
        if aliases:
            output += f"🔗 Aliases: {', '.join(aliases)}\n"

        # Check for optional content
        if skill.get('scripts'):
            output += f"\n📁 Scripts: {len(skill['scripts'])} files\n"
        if skill.get('references'):
            output += f"📚 References: {len(skill['references'])} files\n"
        if skill.get('assets'):
            output += f"🎨 Assets: {len(skill['assets'])} files\n"

        output += f"\n📂 Path: {skill['path']}\n"
        return output