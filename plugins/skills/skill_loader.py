"""
Skill Loader and Activation
Progressive disclosure: load full skill only when needed
"""
import re
import os
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Any


class SkillLoaderMixin:
    """Load and activate skills on demand"""

    def __init__(self, config):
        super().__init__(config)
        self.skill_dir: str = os.path.join(os.path.dirname(__file__), "skills")
        self.skill_index: Dict[str, Dict[str, Any]] = {}
        self.active_skill: Optional[str] = None
        self.skill_context: Optional[str] = None
        self.skill_history: List[Dict[str, Any]] = []
        self._build_skill_index()

    def _build_skill_index(self):
        """Build lightweight skill index by scanning skills directory"""
        try:
            if not os.path.exists(self.skill_dir):
                os.makedirs(self.skill_dir, exist_ok=True)
        except Exception:
            pass

        self._index_plugins()

        if os.path.exists(self.skill_dir):
            for filename in sorted(os.listdir(self.skill_dir)):
                if filename.endswith(".md") and not filename.startswith("."):
                    name = filename[:-3]
                    path = os.path.join(self.skill_dir, filename)
                    info = self._parse_skill_frontmatter(path)
                    if info:
                        self.skill_index[name] = info

    def _index_plugins(self):
        """Index available plugins as skills"""
        plugins_dir = os.path.dirname(os.path.dirname(__file__))
        if not os.path.exists(plugins_dir):
            return
        for entry in sorted(os.listdir(plugins_dir)):
            full_path = os.path.join(plugins_dir, entry)
            if not os.path.isdir(full_path) or entry.startswith(".") or entry == "skills":
                continue
            mod_name = f"plugins.{entry}.{entry}"
            try:
                plugin_module = importlib.import_module(mod_name)
                info = getattr(plugin_module, "PLUGIN_INFO", None)
                if not info:
                    continue
                skill_name = entry
                desc = info.get("description", f"{skill_name} plugin")
                metadata = {
                    "category": "plugin",
                    "version": info.get("version", "1.0.0"),
                    "author": info.get("author", "AlleyBot"),
                }
                aliases = [skill_name]
                name = info.get("name", "")
                if name and name != skill_name:
                    aliases.append(name)
                aliases.extend(info.get("aliases", []))
                self.skill_index[skill_name] = {
                    "description": desc,
                    "metadata": metadata,
                    "aliases": aliases,
                }
                print(f"🔧 Indexed plugin skill: {skill_name}")
            except Exception as e:
                print(f"⚠️ Could not index plugin {entry}: {e}")

    def _parse_skill_frontmatter(self, path: str) -> Optional[Dict[str, Any]]:
        """Parse frontmatter for skill index (lightweight)"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL | re.MULTILINE)
            if not match:
                return None
            fm_str = match.group(1)
            frontmatter: Dict[str, Any] = {}
            try:
                import yaml
                frontmatter = yaml.safe_load(fm_str) or {}
            except (ImportError, Exception):
                # Fallback simple parser
                for line in fm_str.splitlines():
                    if ":" in line and not line.strip().startswith("#"):
                        parts = [x.strip() for x in line.split(":", 1)]
                        if len(parts) == 2:
                            frontmatter[parts[0]] = parts[1]
            description = frontmatter.get("description", "")
            metadata = dict(frontmatter)
            metadata.pop("description", None)
            # Normalize aliases to list
            aliases_raw = frontmatter.get("aliases", [])
            if isinstance(aliases_raw, str):
                aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
            elif isinstance(aliases_raw, list):
                aliases = aliases_raw
            else:
                aliases = []
            return {
                "description": description,
                "metadata": metadata,
                "aliases": aliases,
            }
        except Exception:
            return None

    def _resolve_alias(self, query: str) -> Optional[str]:
        """Resolve skill name or alias to canonical skill name"""
        query_lower = query.lower().strip()
        # Exact match
        if query in self.skill_index:
            return query
        # Case-insensitive name match
        for name in self.skill_index:
            if name.lower() == query_lower:
                return name
        # Alias match
        for name, info in self.skill_index.items():
            aliases = info.get("aliases", [])
            for alias in aliases:
                if str(alias).lower() == query_lower:
                    return name
        return None

    def _load_full_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Load full skill details on demand"""
        resolved = self._resolve_alias(skill_name)
        if not resolved:
            return None
        skill_name = resolved

        # Load from file
        path = os.path.join(self.skill_dir, f"{skill_name}.md")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL | re.MULTILINE)
                if not match:
                    return None
                fm_str = match.group(1)
                body = match.group(2).strip()
                frontmatter: Dict[str, Any] = {}
                try:
                    import yaml
                    frontmatter = yaml.safe_load(fm_str) or {}
                except (ImportError, Exception):
                    # Fallback parser
                    for line in fm_str.splitlines():
                        if ":" in line and not line.strip().startswith("#"):
                            parts = [x.strip() for x in line.split(":", 1)]
                            if len(parts) == 2:
                                frontmatter[parts[0]] = parts[1]
                desc = frontmatter.get("description", self.skill_index.get(skill_name, {}).get("description", ""))
                return {
                    "name": skill_name,
                    "description": desc,
                    "body": body,
                    "frontmatter": frontmatter,
                    "references": frontmatter.get("references", []),
                }
            except Exception:
                return None

        # Try plugin
        mod_name = f"plugins.{skill_name}.{skill_name}"
        try:
            plugin_module = importlib.import_module(mod_name)
            info = getattr(plugin_module, "PLUGIN_INFO", None)
            if not info:
                return None
            desc = info.get("description", "")
            body = f"""## {skill_name.replace('_', ' ').replace('-', ' ').title()} Skill Instructions

You have access to the {skill_name} plugin.

Plugin Description: {desc}

Use commands from this plugin as needed.
For available commands: !help {skill_name}"""
            return {
                "name": skill_name,
                "description": desc,
                "body": body,
                "frontmatter": {"category": "plugin", "plugin": skill_name},
                "references": info.get("references", []),
            }
        except (ImportError, AttributeError):
            return None

    def find_skill_for_task(self, task_description: str) -> Optional[str]:
        """Find the most relevant skill for a given task"""
        if not self.skill_index:
            return None

        # Direct alias resolution
        resolved = self._resolve_alias(task_description.strip())
        if resolved:
            return resolved

        task_lower = task_description.lower()
        task_words = set(task_lower.split())
        best_match = None
        best_score = 0

        for name, info in self.skill_index.items():
            desc_lower = info.get("description", "").lower()
            desc_words = set(desc_lower.split())
            score = len(task_words & desc_words)

            # Bonus for name matches
            name_check = name.replace("-", " ").replace("_", " ")
            name_words = set(name_check.lower().split())
            score += len(task_words & name_words) * 2

            name_lower = name.lower()
            if name_lower in task_lower:
                score += 3

            # Prioritize core and plugins
            category = info.get("metadata", {}).get("category", "")
            if category == "core":
                score += 5
            elif category == "plugin":
                score += 2

            if score > best_score:
                best_score = score
                best_match = name

        return best_match