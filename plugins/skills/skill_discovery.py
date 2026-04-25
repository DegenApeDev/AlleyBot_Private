"""
Agent Skills Framework Plugin
Lightweight skill discovery and execution following agentskills.io specification
"""
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin


class SkillDiscoveryPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "skill_discovery"
        self.version = "1.0.0"
        self.skills_dir = config.get('skills_dir', 'skills')
        self.skill_index: Dict[str, Dict[str, Any]] = {}
        self.full_skills: Dict[str, Dict[str, Any]] = {}
        self.skill_by_alias: Dict[str, str] = {}

    def initialize(self, api, core):
        super().initialize(api, core)
        self._discover_skills()
        print(f"🔧 Agent Skills: Discovered {len(self.skill_index)} skills")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "skills": self.skills_cmd,
            "skill": self.skill_cmd,
        }

    def skills_cmd(self, args: List[str]) -> str:
        lines = []
        for name, info in self.skill_index.items():
            aliases_str = f" ({', '.join(info['metadata'].get('aliases', []))})" if info['metadata'].get('aliases') else ""
            desc = info['description'][:100] + "..." if len(info['description']) > 100 else info['description']
            lines.append(f"• **{name}**{aliases_str}: {desc}")
        header = f"**Available Skills** ({len(lines)} total):"
        return f"{header}\n" + "\n".join(lines)

    def skill_cmd(self, args: List[str]) -> str:
        if not args:
            return self.skills_cmd([])
        query = " ".join(args).strip()
        canonical = self.resolve_skill(query)
        if canonical is None:
            return f"No skill or alias '{query}' found."
        full_skill = self.get_full_skill(canonical)
        if full_skill is None:
            return f"Failed to load skill '{canonical}'."
        aliases = full_skill['frontmatter'].get('metadata', {}).get('aliases', [])
        aliases_str = f"\n**Aliases:** {', '.join(aliases)}" if aliases else ""
        body_preview = full_skill['body'][:1000]
        if len(full_skill['body']) > 1000:
            body_preview += "\n[... truncated ...]"
        return (f"**{full_skill['name']}**{aliases_str}\n\n"
                f"**Description:** {full_skill['description']}\n\n"
                f"**Preview:**\n{body_preview}\n\n"
                f"**Path:** {full_skill['path']}")

    def resolve_skill(self, name: str) -> Optional[str]:
        if not name:
            return None
        if name in self.skill_index:
            return name
        return self.skill_by_alias.get(name)

    def get_full_skill(self, name: str) -> Optional[Dict[str, Any]]:
        canonical = self.resolve_skill(name)
        if canonical is None:
            return None
        if canonical in self.full_skills:
            return self.full_skills[canonical]
        return self._load_full_skill(canonical)

    def _discover_skills(self):
        """Scan skills directory and index all SKILL.md files (lazy loading)"""
        self.skill_index.clear()
        self.full_skills.clear()
        self.skill_by_alias.clear()

        # Prioritize core and debate plugins first
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

        # Then scan skills directory
        skills_path = Path(self.project_root) / self.skills_dir
        if not skills_path.exists():
            print(f"⚠️ Skills directory not found: {skills_path}")
        else:
            for skill_dir in skills_path.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / 'SKILL.md'
                if not skill_file.exists():
                    continue
                try:
                    frontmatter = self._parse_frontmatter(skill_file)
                    if frontmatter and 'name' in frontmatter:
                        name = frontmatter['name']
                        if name in self.skill_index:
                            print(f"⚠️ Duplicate skill name {name}, skipping {skill_dir.name}")
                            continue
                        metadata = frontmatter.get('metadata', {}).copy()
                        aliases = metadata.get('aliases', frontmatter.get('aliases', []))
                        aliases = [str(a).strip() for a in aliases] if isinstance(aliases, (list, tuple)) else []
                        metadata['aliases'] = aliases
                        self.skill_index[name] = {
                            'name': name,
                            'description': frontmatter.get('description', ''),
                            'path': str(skill_dir),
                            'metadata': metadata
                        }
                except Exception as e:
                    print(f"⚠️ Failed to parse skill {skill_dir.name}: {e}")

        # Build alias resolution map
        for skill_name, info in self.skill_index.items():
            aliases = info['metadata'].get('aliases', [])
            for alias in aliases:
                if alias in self.skill_by_alias:
                    print(f"⚠️ Alias conflict: '{alias}' already maps to {self.skill_by_alias[alias]}, now {skill_name}")
                self.skill_by_alias[alias] = skill_name

    def _parse_frontmatter(self, skill_file: Path) -> Optional[Dict]:
        """Extract YAML frontmatter from SKILL.md"""
        try:
            content = skill_file.read_text(encoding='utf-8')
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                frontmatter_text = match.group(1)
                return yaml.safe_load(frontmatter_text)
            return None
        except Exception as e:
            print(f"⚠️ Error parsing frontmatter: {e}")
            return None

    def _load_full_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Load full skill content including body (progressive disclosure)"""
        if skill_name in self.full_skills:
            return self.full_skills[skill_name]

        if skill_name not in self.skill_index:
            return None

        skill_info = self.skill_index[skill_name]
        skill_path = Path(skill_info['path']) / 'SKILL.md'

        try:
            if not skill_path.exists():
                # Fallback for plugins without dedicated SKILL.md file
                metadata = skill_info['metadata'].copy()
                frontmatter = {
                    'name': skill_name,
                    'description': skill_info['description'],
                    'metadata': metadata
                }
                body = (f"Plugin-based skill without dedicated SKILL.md file.\n\n"
                        f"Path: {skill_info['path']}\n\n"
                        f"Metadata:\n{yaml.dump(metadata, default_flow_style=False)}")
                full_skill = {
                    'name': skill_name,
                    'description': skill_info['description'],
                    'body': body,
                    'frontmatter': frontmatter,
                    'path': skill_info['path']
                }
            else:
                content = skill_path.read_text(encoding='utf-8')
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
            self.full_skills[skill_name] = full_skill
            return full_skill
        except Exception as e:
            print(f"⚠️ Failed to load full skill {skill_name}: {e}")
            return None


PLUGIN_INFO = {
    "name": "skill_discovery",
    "version": "1.0.0",
    "description": "Agent Skills Framework Plugin - Lightweight skill discovery and execution following agentskills.io specification",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return SkillDiscoveryPlugin(config or {})