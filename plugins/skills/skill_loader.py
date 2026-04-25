"""
Skill Loader and Activation
Progressive disclosure: load full skill only when needed
"""
import re
import os
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

        if os.path.exists(self.skill_dir):
            for filename in os.listdir(self.skill_dir):
                if filename.endswith(".md") and not filename.startswith("."):
                    name = filename[:-3]
                    path = os.path.join(self.skill_dir, filename)
                    info = self._parse_skill_frontmatter(path)
                    if info:
                        self.skill_index[name] = info

        self._add_core_if_missing()

    def _add_core_if_missing(self):
        """Dynamically load 'core' plugin if not found"""
        if "core" in self.skill_index:
            return
        try:
            from plugins.core.core import PLUGIN_INFO
            info: Dict[str, Any] = {
                "description": PLUGIN_INFO.get("description", "Core plugin provides essential functionality."),
                "metadata": {
                    "category": "core",
                    "version": PLUGIN_INFO.get("version", "1.0.0"),
                    "author": PLUGIN_INFO.get("author", "AlleyBot"),
                },
                "aliases": ["core", "base", "system", "main"],
            }
            self.skill_index["core"] = info
            print("🔧 Dynamically loaded core plugin into skill index")
        except ImportError:
            print("⚠️ Core plugin not found - basic core skill not available")

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
        query_lower = query.lower()
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
                if alias.lower() == query_lower:
                    return name
        return None

    def _load_full_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Load full skill details on demand"""
        resolved = self._resolve_alias(skill_name)
        if not resolved:
            return None
        skill_name = resolved

        # Special handling for core
        if skill_name == "core":
            try:
                from plugins.core.core import PLUGIN_INFO
                desc = PLUGIN_INFO.get("description", "Core plugin provides essential commands and functionality.")
                body = """## Core Skill Instructions
You have access to core plugin commands and utilities.
Use commands like !help, !status, and other base functions.
For specific core commands, refer to plugin documentation."""
                return {
                    "name": "core",
                    "description": desc,
                    "body": body,
                    "frontmatter": {"category": "core"},
                    "references": [],
                }
            except ImportError:
                return None

        # Load from file
        path = os.path.join(self.skill_dir, f"{skill_name}.md")
        if not os.path.exists(path):
            return None
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

    def find_skill_for_task(self, task_description: str) -> Optional[str]:
        """Find the most relevant skill for a given task"""
        if not self.skill_index:
            return None

        # Direct alias resolution
        resolved = self._resolve_alias(task_description.strip())
        if resolved:
            return resolved

        task_lower = task_description.lower()
        best_match = None
        best_score = 0

        task_words = set(task_lower.split())

        for name, info in self.skill_index.items():
            desc = info.get("description", "").lower()
            score = 0

            # Keyword matches in description
            desc_words = set(desc.split())
            overlap = task_words & desc_words
            score += len(overlap)

            # Bonus for name matches
            name_check = name.replace("-", " ")
            if name_check.lower() in task_lower:
                score += 5

            # Category match
            meta = info.get("metadata", {})
            category = meta.get("category", "").lower()
            if category in task_lower:
                score += 3

            # Alias matches
            aliases = info.get("aliases", [])
            for alias in aliases:
                alias_lower = alias.lower()
                if alias_lower in task_lower:
                    score += 6

            if score > best_score:
                best_score = score
                best_match = name

        return best_match if best_score > 0 else None