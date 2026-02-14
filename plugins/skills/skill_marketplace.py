"""
Skill Marketplace
Unified marketplace with format adapter registry for plugin extensibility.
Supports multiple skill formats: SKILL.md (agentskills.io), Python code, and custom formats.
"""
import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class SkillFormatAdapter(ABC):
    """Abstract base class for skill format adapters"""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name/identifier"""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """Return supported file extensions"""
        pass
    
    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """Check if this adapter can read the given file"""
        pass
    
    @abstractmethod
    def read_skill(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read a skill file and return standardized skill data"""
        pass
    
    @abstractmethod
    def to_marketplace_package(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert skill data to marketplace package format"""
        pass
    
    @abstractmethod
    def from_marketplace_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Convert marketplace package to skill data"""
        pass


class SkillMdAdapter(SkillFormatAdapter):
    """Adapter for agentskills.io SKILL.md format (YAML frontmatter + markdown body)"""
    
    @property
    def format_name(self) -> str:
        return "skill-md"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".md"]
    
    def can_read(self, file_path: Path) -> bool:
        if file_path.suffix != ".md":
            return False
        try:
            content = file_path.read_text(encoding='utf-8')
            return content.startswith('---') and 'name:' in content
        except Exception:
            return False
    
    def read_skill(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read SKILL.md file with YAML frontmatter"""
        try:
            import re
            import yaml
            
            content = file_path.read_text(encoding='utf-8')
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            
            if not match:
                return None
            
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2).strip()
            
            return {
                'name': frontmatter.get('name', file_path.parent.name),
                'description': frontmatter.get('description', ''),
                'body': body,
                'frontmatter': frontmatter,
                'format': 'skill-md',
                'source_path': str(file_path),
            }
        except Exception as e:
            print(f"⚠️ Error reading SKILL.md: {e}")
            return None
    
    def to_marketplace_package(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SKILL.md to marketplace package with code extraction"""
        body = skill_data.get('body', '')
        
        # Extract Python code blocks from markdown body
        import re
        code_blocks = re.findall(r'```python\n(.*?)\n```', body, re.DOTALL)
        
        # If no code blocks, create a wrapper that executes the skill
        if code_blocks:
            code = '\n\n'.join(code_blocks)
        else:
            # Generate a skill wrapper that loads and executes the SKILL.md
            code = self._generate_skill_wrapper(skill_data)
        
        return {
            'name': skill_data.get('name', 'unnamed'),
            'description': skill_data.get('description', ''),
            'code': code,
            'format': 'skill-md',
            'metadata': skill_data.get('metadata', {}),
            'version': skill_data.get('metadata', {}).get('version', '1.0.0'),
        }
    
    def from_marketplace_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Convert marketplace package to SKILL.md format"""
        code = package.get('code', '')
        
        # Try to reconstruct a SKILL.md from the package
        body = f"""# {package.get('name', 'Unnamed Skill')}

## Description

{package.get('description', 'No description provided')}

## Implementation

```python
{code}
```

## Usage

Load this skill and execute the main function with appropriate parameters.
"""
        
        return {
            'name': package.get('name', 'unnamed'),
            'description': package.get('description', ''),
            'body': body,
            'metadata': package.get('metadata', {}),
            'format': 'skill-md',
        }
    
    def _generate_skill_wrapper(self, skill_data: Dict[str, Any]) -> str:
        """Generate a Python wrapper for a SKILL.md skill"""
        name = skill_data.get('name', 'unnamed')
        description = skill_data.get('description', '')
        
        return f'''"""
Auto-generated skill wrapper for {name}
{description}
"""

class {name.replace('-', '_').title()}Skill:
    """Wrapper for SKILL.md based skill"""
    
    def __init__(self):
        self.name = "{name}"
        self.description = """{description}"""
    
    def execute(self, context=None, **kwargs):
        """Execute the skill with given context"""
        print(f"Executing skill: {{self.name}}")
        return {{"success": True, "skill": self.name}}

# Backwards compatibility
def main(**kwargs):
    skill = {name.replace('-', '_').title()}Skill()
    return skill.execute(**kwargs)
'''


class PythonCodeAdapter(SkillFormatAdapter):
    """Adapter for raw Python code skills"""
    
    @property
    def format_name(self) -> str:
        return "python"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".py"]
    
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"
    
    def read_skill(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read Python skill file"""
        try:
            code = file_path.read_text(encoding='utf-8')
            
            # Try to extract docstring as description
            import re
            docstring_match = re.match(r'^[\'"]{3}(.*?)[\'"]{3}', code, re.DOTALL)
            description = docstring_match.group(1).strip() if docstring_match else ""
            
            return {
                'name': file_path.stem,
                'description': description.split('\n')[0] if description else f"Python skill: {file_path.stem}",
                'code': code,
                'format': 'python',
                'source_path': str(file_path),
            }
        except Exception as e:
            print(f"⚠️ Error reading Python skill: {e}")
            return None
    
    def to_marketplace_package(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python skill to marketplace package"""
        return {
            'name': skill_data.get('name', 'unnamed'),
            'description': skill_data.get('description', ''),
            'code': skill_data.get('code', ''),
            'format': 'python',
            'metadata': skill_data.get('metadata', {}),
            'version': skill_data.get('metadata', {}).get('version', '1.0.0'),
        }
    
    def from_marketplace_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Convert marketplace package to Python skill"""
        return {
            'name': package.get('name', 'unnamed'),
            'description': package.get('description', ''),
            'code': package.get('code', ''),
            'metadata': package.get('metadata', {}),
            'format': 'python',
        }


class AgentskillsIOAdapter(SkillFormatAdapter):
    """Adapter for agentskills.io marketplace format"""
    
    @property
    def format_name(self) -> str:
        return "agentskills-io"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".json"]
    
    def can_read(self, file_path: Path) -> bool:
        if file_path.suffix != ".json":
            return False
        try:
            with open(file_path) as f:
                data = json.load(f)
            return 'skill' in data or 'name' in data
        except Exception:
            return False
    
    def read_skill(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read agentskills.io format skill package"""
        try:
            with open(file_path) as f:
                package = json.load(f)
            
            return {
                'name': package.get('skill', {}).get('name') or package.get('name', 'unnamed'),
                'description': package.get('skill', {}).get('description') or package.get('description', ''),
                'body': package.get('skill', {}).get('content') or package.get('content', ''),
                'format': 'agentskills-io',
                'source_path': str(file_path),
                'raw_package': package,
            }
        except Exception as e:
            print(f"⚠️ Error reading agentskills.io package: {e}")
            return None
    
    def to_marketplace_package(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to marketplace package (already in similar format)"""
        return {
            'name': skill_data.get('name', 'unnamed'),
            'description': skill_data.get('description', ''),
            'code': skill_data.get('body', ''),
            'format': 'agentskills-io',
            'metadata': skill_data.get('metadata', {}),
            'version': skill_data.get('metadata', {}).get('version', '1.0.0'),
        }
    
    def from_marketplace_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Convert marketplace package to agentskills.io format"""
        return {
            'name': package.get('name', 'unnamed'),
            'description': package.get('description', ''),
            'body': package.get('code', ''),
            'metadata': package.get('metadata', {}),
            'format': 'agentskills-io',
        }


class SkillMarketplaceMixin:
    """Unified skill marketplace with format adapter registry"""
    
    def __init__(self, config):
        super().__init__(config)
        self.marketplace_url = config.get('marketplace_url', 'https://agentskills.io')
        self.project_root = Path(getattr(self, 'project_root', os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.skills_dir = self.project_root / 'skills'
        self.marketplace_dir = self.project_root / 'data' / 'marketplace'
        self.marketplace_dir.mkdir(parents=True, exist_ok=True)
        
        # Format adapter registry
        self._adapters: Dict[str, SkillFormatAdapter] = {}
        self._register_default_adapters()
        
        # Marketplace state
        self.published_skills: Dict[str, Dict] = {}
        self.imported_skills: Dict[str, Dict] = {}
        self._load_marketplace_state()

    def _register_default_adapters(self):
        """Register built-in format adapters"""
        self.register_adapter(SkillMdAdapter())
        self.register_adapter(PythonCodeAdapter())
        self.register_adapter(AgentskillsIOAdapter())

    def register_adapter(self, adapter: SkillFormatAdapter):
        """Register a custom format adapter (plugin extensibility)"""
        self._adapters[adapter.format_name] = adapter
        print(f"🔌 Registered skill format adapter: {adapter.format_name}")

    def get_adapter(self, format_name: str) -> Optional[SkillFormatAdapter]:
        """Get adapter by format name"""
        return self._adapters.get(format_name)

    def detect_adapter(self, file_path: Path) -> Optional[SkillFormatAdapter]:
        """Auto-detect the appropriate adapter for a file"""
        for adapter in self._adapters.values():
            if adapter.can_read(file_path):
                return adapter
        return None

    def _load_marketplace_state(self):
        """Load marketplace state from memory"""
        try:
            if hasattr(self, 'core') and self.core:
                state = self.core.get_memory('skill_marketplace_v2')
                if state:
                    self.published_skills = state.get('published', {})
                    self.imported_skills = state.get('imported', {})
        except Exception:
            pass

    def _save_marketplace_state(self):
        """Save marketplace state"""
        try:
            if hasattr(self, 'core') and self.core:
                self.core.save_memory('skill_marketplace_v2', {
                    'published': self.published_skills,
                    'imported': self.imported_skills,
                })
        except Exception as e:
            print(f"⚠️ Failed to save marketplace state: {e}")

    def _compute_skill_hash(self, content: str) -> str:
        """Compute hash for skill content"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def publish_skill(self, skill_name: str, target_format: str = 'python') -> Dict[str, Any]:
        """Publish a skill to the marketplace, converting to target format"""
        # Find the skill
        skill_path = self.skills_dir / skill_name / 'SKILL.md'
        
        if not skill_path.exists():
            # Try finding as Python file
            skill_path = self.skills_dir / f"{skill_name}.py"
            if not skill_path.exists():
                return {'success': False, 'error': f"Skill '{skill_name}' not found"}
        
        # Detect and read skill
        adapter = self.detect_adapter(skill_path)
        if not adapter:
            return {'success': False, 'error': f"Cannot detect format for: {skill_path}"}
        
        skill_data = adapter.read_skill(skill_path)
        if not skill_data:
            return {'success': False, 'error': f"Failed to read skill: {skill_name}"}
        
        # Convert to target format
        target_adapter = self.get_adapter(target_format)
        if not target_adapter:
            return {'success': False, 'error': f"Unknown target format: {target_format}"}
        
        package = target_adapter.to_marketplace_package(skill_data)
        
        # Add metadata
        package['published'] = datetime.datetime.now().isoformat()
        package['source_format'] = adapter.format_name
        package['target_format'] = target_format
        package['code_hash'] = self._compute_skill_hash(package.get('code', ''))
        
        # Save to marketplace directory
        package_file = self.marketplace_dir / f"{skill_name}.json"
        try:
            with open(package_file, 'w') as f:
                json.dump(package, f, indent=2)
            
            self.published_skills[skill_name] = {
                'hash': package['code_hash'],
                'published': package['published'],
                'version': package.get('version', '1.0.0'),
                'format': target_format,
            }
            self._save_marketplace_state()
            
            return {
                'success': True,
                'skill': skill_name,
                'format': target_format,
                'hash': package['code_hash'],
                'path': str(package_file),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_skill(self, package_path: str, target_format: str = 'skill-md') -> Dict[str, Any]:
        """Import a skill from marketplace package, converting to target format"""
        try:
            package_file = Path(package_path)
            if not package_file.exists():
                # Try marketplace directory
                package_file = self.marketplace_dir / package_path
                if not package_file.exists():
                    package_file = self.marketplace_dir / f"{package_path}.json"
            
            if not package_file.exists():
                return {'success': False, 'error': f"Package not found: {package_path}"}
            
            # Load package
            with open(package_file) as f:
                package = json.load(f)
            
            # Detect source format
            source_format = package.get('format', 'python')
            source_adapter = self.get_adapter(source_format)
            if not source_adapter:
                return {'success': False, 'error': f"Unknown source format: {source_format}"}
            
            # Convert to skill data
            skill_data = source_adapter.from_marketplace_package(package)
            
            # Convert to target format
            target_adapter = self.get_adapter(target_format)
            if not target_adapter:
                return {'success': False, 'error': f"Unknown target format: {target_format}"}
            
            # Create skill directory
            skill_name = skill_data.get('name', 'unnamed')
            skill_dir = self.skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Write in target format
            if target_format == 'skill-md':
                skill_file = skill_dir / 'SKILL.md'
            else:
                skill_file = skill_dir / f"{skill_name}.py"
            
            # For SKILL.md format, write YAML frontmatter + body
            if target_format == 'skill-md':
                try:
                    import yaml
                    frontmatter = {
                        'name': skill_data.get('name', 'unnamed'),
                        'description': skill_data.get('description', ''),
                    }
                    if 'metadata' in skill_data:
                        frontmatter['metadata'] = skill_data['metadata']
                    yaml_content = yaml.dump(frontmatter, default_flow_style=False)
                    body = skill_data.get('body', '')
                    content = f"---\n{yaml_content}---\n\n{body}"
                    skill_file.write_text(content, encoding='utf-8')
                except Exception as e:
                    return {'success': False, 'error': f"Failed to write SKILL.md: {e}"}
            else:
                # For Python format, write code directly
                code = skill_data.get('code', '')
                skill_file.write_text(code, encoding='utf-8')
            
            # Update imported state
            self.imported_skills[skill_name] = {
                'hash': package.get('code_hash', ''),
                'imported': datetime.datetime.now().isoformat(),
                'source': str(package_file),
                'format': target_format,
            }
            self._save_marketplace_state()
            
            # Trigger skill rediscovery
            if hasattr(self, '_discover_skills'):
                self._discover_skills()
            
            return {
                'success': True,
                'skill': skill_name,
                'format': target_format,
                'file': str(skill_file),
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_marketplace_skills(self) -> List[Dict]:
        """List all skills available in the marketplace"""
        skills = []
        try:
            for f in self.marketplace_dir.glob('*.json'):
                try:
                    with open(f) as fh:
                        pkg = json.load(fh)
                    skills.append({
                        'name': pkg.get('name', f.stem),
                        'description': pkg.get('description', '')[:80],
                        'version': pkg.get('version', '?'),
                        'format': pkg.get('format', 'unknown'),
                        'published': pkg.get('published', '?'),
                        'file': str(f),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return skills

    # --- CLI Commands ---

    def marketplace_list_command(self, *args):
        """List skills in marketplace. Usage: skill_market_list"""
        skills = self.list_marketplace_skills()
        if not skills:
            return "📦 Marketplace is empty. Publish skills with: skill_publish <skill_name>"
        
        output = f"� Skill Marketplace ({len(skills)} packages)\n\n"
        for s in skills:
            output += f"  🧩 {s['name']} v{s['version']} [{s['format']}]\n"
            output += f"     {s['description']}\n"
            output += f"     Published: {s['published'][:10]}\n\n"
        return output

    def marketplace_publish_command(self, *args):
        """Publish skill to marketplace. Usage: skill_publish <skill_name> [format]"""
        if not args:
            # List available skills
            skills_path = self.skills_dir
            available = []
            if skills_path.exists():
                for d in skills_path.iterdir():
                    if d.is_dir() and (d / 'SKILL.md').exists():
                        available.append(d.name)
            if not available:
                return "❌ No skills to publish. Create skills with: skill_create <name> <template>"
            return f"❌ Usage: skill_publish <skill_name> [format]\nAvailable: {', '.join(available)}\nFormats: skill-md, python, agentskills-io"
        
        skill_name = args[0]
        target_format = args[1] if len(args) > 1 else 'python'
        
        result = self.publish_skill(skill_name, target_format)
        if result['success']:
            return (
                f"✅ Published '{skill_name}' to marketplace\n"
                f"📦 Format: {result['format']}\n"
                f"🔢 Hash: {result['hash']}\n"
                f"📁 Path: {result['path']}"
            )
        return f"❌ {result['error']}"

    def marketplace_import_command(self, *args):
        """Import skill from marketplace. Usage: skill_import <package_name> [format]"""
        if not args:
            return "❌ Usage: skill_import <package_name> [target_format]\nFormats: skill-md, python, agentskills-io"
        
        package_name = args[0]
        target_format = args[1] if len(args) > 1 else 'skill-md'
        
        result = self.import_skill(package_name, target_format)
        if result['success']:
            return (
                f"✅ Imported skill '{result['skill']}'\n"
                f"📄 Format: {result['format']}\n"
                f"📁 Location: {result['file']}"
            )
        return f"❌ {result['error']}"
