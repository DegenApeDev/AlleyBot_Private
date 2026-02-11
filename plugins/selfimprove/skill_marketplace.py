"""
Skill Marketplace Mixin
Share, import, and discover skills from a local registry and remote sources.
"""
import os
import json
import hashlib
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class SkillMarketplaceMixin:
    """Mixin for skill sharing and importing"""

    def _init_marketplace(self):
        """Initialize skill marketplace state"""
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.skills_dir = self.project_root / 'dynamic_skills'
        self.marketplace_dir = self.project_root / 'data' / 'marketplace'
        self.marketplace_dir.mkdir(parents=True, exist_ok=True)
        self.published_skills: Dict[str, Dict] = {}
        self.imported_skills: Dict[str, Dict] = {}
        self._load_marketplace_state()

    def _load_marketplace_state(self):
        """Load marketplace state from memory"""
        try:
            state = self.core.get_memory('selfimprove_marketplace')
            if state:
                self.published_skills = state.get('published', {})
                self.imported_skills = state.get('imported', {})
        except Exception:
            pass

    def _save_marketplace_state(self):
        """Save marketplace state"""
        try:
            self.core.save_memory('selfimprove_marketplace', {
                'published': self.published_skills,
                'imported': self.imported_skills,
            })
        except Exception as e:
            print(f"⚠️  Failed to save marketplace state: {e}")

    def _get_skill_registry(self) -> Dict:
        """Load the dynamic skills registry"""
        registry_file = self.skills_dir / 'registry.json'
        if registry_file.exists():
            try:
                with open(registry_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _compute_skill_hash(self, code: str) -> str:
        """Compute a hash for skill code to detect changes"""
        return hashlib.sha256(code.encode()).hexdigest()[:16]

    def publish_skill(self, skill_name: str) -> Dict[str, Any]:
        """Publish a skill to the local marketplace for sharing"""
        registry = self._get_skill_registry()

        if skill_name not in registry:
            return {'success': False, 'error': f"Skill '{skill_name}' not found in registry"}

        skill_info = registry[skill_name]
        skill_file = Path(skill_info.get('file', ''))

        if not skill_file.exists():
            return {'success': False, 'error': f"Skill file not found: {skill_file}"}

        try:
            code = skill_file.read_text()
            code_hash = self._compute_skill_hash(code)

            # Create marketplace package
            package = {
                'name': skill_name,
                'description': skill_info.get('description', ''),
                'code': code,
                'code_hash': code_hash,
                'metadata': skill_info.get('metadata', {}),
                'published': datetime.datetime.now().isoformat(),
                'version': '1.0.0',
                'author': 'AlleyBot',
            }

            # Save to marketplace directory
            package_file = self.marketplace_dir / f"{skill_name}.json"
            with open(package_file, 'w') as f:
                json.dump(package, f, indent=2)

            self.published_skills[skill_name] = {
                'hash': code_hash,
                'published': package['published'],
                'version': package['version'],
            }
            self._save_marketplace_state()

            return {
                'success': True,
                'skill': skill_name,
                'hash': code_hash,
                'path': str(package_file),
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_skill(self, package_path: str) -> Dict[str, Any]:
        """Import a skill from a marketplace package file"""
        try:
            package_file = Path(package_path)
            if not package_file.exists():
                # Try marketplace directory
                package_file = self.marketplace_dir / package_path
                if not package_file.exists():
                    package_file = self.marketplace_dir / f"{package_path}.json"

            if not package_file.exists():
                return {'success': False, 'error': f"Package not found: {package_path}"}

            with open(package_file) as f:
                package = json.load(f)

            skill_name = package['name']
            code = package['code']

            # Safety check
            safety = self.validate_code_safety(code)
            if not safety['safe']:
                return {
                    'success': False,
                    'error': 'Imported skill failed safety validation',
                    'issues': safety['issues'],
                }

            # Write skill file
            self.skills_dir.mkdir(exist_ok=True)
            skill_file = self.skills_dir / f"{skill_name}.py"
            with open(skill_file, 'w') as f:
                f.write(code)

            # Update registry
            registry = self._get_skill_registry()
            registry[skill_name] = {
                'file': str(skill_file),
                'description': package.get('description', ''),
                'metadata': package.get('metadata', {}),
                'imported': datetime.datetime.now().isoformat(),
                'source': str(package_file),
            }
            registry_file = self.skills_dir / 'registry.json'
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)

            self.imported_skills[skill_name] = {
                'hash': package.get('code_hash', ''),
                'imported': datetime.datetime.now().isoformat(),
                'source': str(package_file),
            }
            self._save_marketplace_state()

            return {
                'success': True,
                'skill': skill_name,
                'file': str(skill_file),
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_marketplace_skills(self) -> List[Dict]:
        """List all skills available in the local marketplace"""
        skills = []
        try:
            for f in self.marketplace_dir.glob('*.json'):
                try:
                    with open(f) as fh:
                        pkg = json.load(fh)
                    skills.append({
                        'name': pkg.get('name', f.stem),
                        'description': pkg.get('description', ''),
                        'version': pkg.get('version', '?'),
                        'author': pkg.get('author', '?'),
                        'published': pkg.get('published', '?'),
                        'file': str(f),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return skills

    def marketplace_list_command(self, *args):
        """List skills in the marketplace"""
        skills = self.list_marketplace_skills()
        if not skills:
            return "📦 Marketplace is empty. Publish skills with: improve_publish <skill_name>"

        output = f"📦 Skill Marketplace ({len(skills)} skills)\n\n"
        for s in skills:
            output += f"  🧩 {s['name']} v{s['version']}\n"
            output += f"     {s['description'][:60]}\n"
            output += f"     By: {s['author']} | {s['published'][:10]}\n\n"
        return output

    def marketplace_publish_command(self, *args):
        """Publish a skill to marketplace. Usage: improve_publish <skill_name>"""
        if not args:
            # List available skills
            registry = self._get_skill_registry()
            if not registry:
                return "❌ No dynamic skills to publish. Generate skills first."
            return "❌ Usage: improve_publish <skill_name>\nAvailable: " + ", ".join(registry.keys())

        skill_name = args[0]
        result = self.publish_skill(skill_name)
        if result['success']:
            return f"✅ Published '{skill_name}' to marketplace\n📦 Hash: {result['hash']}"
        return f"❌ {result['error']}"

    def marketplace_import_command(self, *args):
        """Import a skill from marketplace. Usage: improve_import <skill_name_or_path>"""
        if not args:
            return "❌ Usage: improve_import <skill_name_or_path>"

        result = self.import_skill(args[0])
        if result['success']:
            return f"✅ Imported skill '{result['skill']}'\n📁 {result['file']}"
        return f"❌ {result['error']}"

    def marketplace_status_command(self, *args):
        """Show marketplace status"""
        available = self.list_marketplace_skills()
        registry = self._get_skill_registry()

        output = "📦 Marketplace Status\n\n"
        output += f"  🧩 Dynamic Skills: {len(registry)}\n"
        output += f"  📤 Published: {len(self.published_skills)}\n"
        output += f"  📥 Imported: {len(self.imported_skills)}\n"
        output += f"  📦 Available in Marketplace: {len(available)}\n"

        if registry:
            output += "\n  🔧 Registered Skills:\n"
            for name in registry:
                pub = "📤" if name in self.published_skills else "  "
                imp = "📥" if name in self.imported_skills else "  "
                output += f"    {pub}{imp} {name}\n"

        return output
