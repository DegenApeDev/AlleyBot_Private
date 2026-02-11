"""
Skill Validation and Linting
Validate SKILL.md files against agentskills.io specification
"""
import re
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class SkillValidationMixin:
    """Validate skills against the Agent Skills specification"""

    def __init__(self, config):
        super().__init__(config)
        self.validation_errors: List[str] = []

    def validate_skill(self, skill_path: str) -> Dict[str, Any]:
        """Validate a SKILL.md file against the specification"""
        errors = []
        warnings = []
        
        skill_file = Path(skill_path) / 'SKILL.md'
        if not skill_file.exists():
            return {'valid': False, 'errors': ['SKILL.md not found'], 'warnings': []}

        try:
            content = skill_file.read_text(encoding='utf-8')
        except Exception as e:
            return {'valid': False, 'errors': [f'Cannot read file: {e}'], 'warnings': []}

        # Parse frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            errors.append('Missing YAML frontmatter (---) at start of file')
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError as e:
            errors.append(f'Invalid YAML in frontmatter: {e}')
            return {'valid': False, 'errors': errors, 'warnings': []}

        # Validate required fields
        # Name field
        name = frontmatter.get('name')
        if not name:
            errors.append('Missing required field: name')
        elif not self._validate_name(name):
            errors.append(f'Invalid name "{name}": must be 1-64 chars, lowercase alphanumeric and hyphens only, no leading/trailing hyphens')
        else:
            # Check name matches directory
            expected_name = Path(skill_path).name
            if name != expected_name:
                warnings.append(f'Name "{name}" does not match directory name "{expected_name}"')

        # Description field
        description = frontmatter.get('description')
        if not description:
            errors.append('Missing required field: description')
        elif len(description) > 1024:
            errors.append(f'Description too long: {len(description)} chars (max 1024)')
        elif len(description) < 10:
            warnings.append(f'Description very short: {len(description)} chars (should be descriptive)')

        # Optional fields validation
        if 'license' in frontmatter:
            license_str = str(frontmatter['license'])
            if len(license_str) > 100:
                warnings.append('License string very long (consider referencing a file)')

        if 'compatibility' in frontmatter:
            compat = str(frontmatter['compatibility'])
            if len(compat) > 500:
                errors.append('Compatibility field too long (max 500 chars)')

        # Body content validation
        body = content[frontmatter_match.end():].strip()
        if not body:
            warnings.append('No body content after frontmatter (should include instructions)')
        elif len(body) < 100:
            warnings.append('Body content very short (should include detailed instructions)')

        # Check for recommended sections
        if '##' not in body:
            warnings.append('No sections (##) in body - consider adding "When to use" section')
        
        # Check for code blocks if scripts directory exists
        scripts_dir = Path(skill_path) / 'scripts'
        if scripts_dir.exists():
            # Scripts exist but no code blocks referencing them
            if '```' not in body:
                warnings.append('Scripts directory exists but no code blocks in SKILL.md')

        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'name': name,
            'description': description,
            'errors': errors,
            'warnings': warnings,
            'path': str(skill_path)
        }

    def _validate_name(self, name: str) -> bool:
        """Validate skill name per spec: lowercase alphanumeric and hyphens"""
        if not name or len(name) > 64:
            return False
        # Must match: lowercase a-z, digits 0-9, hyphens
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            return False
        return True

    def validate_all_skills_command(self, *args):
        """Validate all discovered skills. Usage: skills_validate"""
        if not self.skill_index:
            return "📭 No skills to validate"

        results = []
        valid_count = 0
        invalid_count = 0

        for name, info in self.skill_index.items():
            result = self.validate_skill(info['path'])
            results.append(result)
            if result['valid']:
                valid_count += 1
            else:
                invalid_count += 1

        output = f"📋 Skill Validation Results\n\n"
        output += f"✅ Valid: {valid_count}\n"
        output += f"❌ Invalid: {invalid_count}\n"
        output += f"📊 Total: {len(results)}\n\n"

        # Show invalid skills with errors
        for result in results:
            if not result['valid']:
                output += f"❌ {result.get('name', 'unknown')}\n"
                for error in result['errors']:
                    output += f"   - {error}\n"
                if result['warnings']:
                    for warning in result['warnings']:
                        output += f"   ⚠️ {warning}\n"
                output += "\n"

        # Show warnings for valid skills (if any)
        warning_count = sum(len(r['warnings']) for r in results)
        if warning_count > 0:
            output += f"⚠️ Warnings found in {warning_count} skills\n"

        return output

    def lint_skill_command(self, *args):
        """Lint a specific skill. Usage: skill_lint <name>"""
        if not args:
            return "❌ Usage: skill_lint <skill_name>"

        skill_name = args[0]
        if skill_name not in self.skill_index:
            return f"❌ Skill not found: {skill_name}"

        info = self.skill_index[skill_name]
        result = self.validate_skill(info['path'])

        status = "✅ Valid" if result['valid'] else "❌ Invalid"
        output = f"{status}: {skill_name}\n\n"

        if result['errors']:
            output += "❌ Errors:\n"
            for error in result['errors']:
                output += f"   - {error}\n"
            output += "\n"

        if result['warnings']:
            output += "⚠️ Warnings:\n"
            for warning in result['warnings']:
                output += f"   - {warning}\n"
            output += "\n"

        if result['valid'] and not result['warnings']:
            output += "✅ Perfect! No issues found.\n"

        output += f"📂 Path: {result['path']}\n"
        return output
