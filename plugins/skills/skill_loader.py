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
        # Explicitly load and register core plugin to prevent 'Plugin not found' errors
        self._load_core_plugin()

    def _load_core_plugin(self):
        """Load the core plugin and register it as a skill"""
        try:
            core_module = importlib.import_module("plugins.core.core")
            create_plugin = getattr(core_module, "create_plugin", None)
            if create_plugin:
                # Instantiate core plugin with config
                core_instance = create_plugin(self.config) if hasattr(self, "config") else create_plugin()
                # Register core commands if any, but at least ensure it's in skill_index
                print("🔧 Core plugin loaded and registered successfully")
                # Force index core if not already
                if "core" not in self.skill_index:
                    from plugins.core.core import PLUGIN_INFO
                    self.skill_index["core"] = {
                        "description": PLUGIN_INFO.get("description", "Core AlleyBot functionality"),
                        "metadata": {
                            "category": "plugin",
                            "version": PLUGIN_INFO.get("version", "1.0.0"),
                            "author": PLUGIN_INFO.get("author", "AlleyBot"),
                        },
                        "aliases": ["core", "main"],
                    }
            else:
                print("⚠️ Core plugin module found but no create_plugin function")
        except Exception as e:
            print(f"⚠️ Failed to load core plugin: {e}")
            # Ensure fallback index entry exists
            if "core" not in self.skill_index:
                print("🔧 Adding fallback core skill index")
                self.skill_index["core"] = {
                    "description": "Core AlleyBot functionality and essential commands.",
                    "metadata": {
                        "category": "plugin",
                        "version": "1.0.0",
                        "author": "AlleyBot",
                    },
                    "aliases": ["core", "main"],
                }

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

    def _index_single_plugin(self, plugin_name: str):
        """Index a single plugin as skill"""
        mod_name = f"plugins.{plugin_name}.{plugin_name}"
        try:
            plugin_module = importlib.import_module(mod_name)
            info = getattr(plugin_module, "PLUGIN_INFO", None)
            if not info:
                return
            skill_name = plugin_name
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
            print(f"⚠️ Could not index plugin {plugin_name}: {e}")

    def _index_plugins(self):
        """Index available plugins as skills"""
        plugins_dir = os.path.dirname(os.path.dirname(__file__))
        if not os.path.exists(plugins_dir):
            return
        # Pre-load core plugin first
        self._index_single_plugin("core")
        for entry in sorted(os.listdir(plugins_dir)):
            if entry == "core":
                continue
            full_path = os.path.join(plugins_dir, entry)
            if not os.path.isdir(full_path) or entry.startswith(".") or entry == "skills":
                continue
            self._index_single_plugin(entry)

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

        # Check core availability during skill loading
        if "core" not in self.skill_index:
            print(f"⚠️ Core plugin unavailable. Cannot load skill '{skill_name}'.")
            return None

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
            except Exception as e:
                print(f"⚠️ Failed to load skill file {path}: {e}")
                return None
        else:
            # For plugin-based skills (like core), return minimal info
            if skill_name in self.skill_index:
                info = self.skill_index[skill_name]
                return {
                    "name": skill_name,
                    "description": info.get("description", ""),
                    "body": "[Plugin-based skill – no markdown file]",
                    "frontmatter": info.get("metadata", {}),
                    "references": [],
                }
        return None