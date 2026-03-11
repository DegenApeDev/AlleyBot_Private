"""
Skill Format Adapters

Converts between different skill formats:
- OpenClaw format (SKILL.md with YAML frontmatter + natural language instructions)
- ElizaOS format (character.json + actions)
- AlleyBot native format

Enables skill portability across agent platforms.
"""
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SkillFormat:
    """Universal skill representation"""
    name: str
    description: str
    instructions: str
    tools: List[str]
    metadata: Dict[str, Any]
    source_format: str  # 'openclaw', 'elizaos', 'alleybot'


class SkillFormatAdapterMixin:
    """
    Convert skills between OpenClaw, ElizaOS, and AlleyBot formats.
    
    Enables skill portability:
    - Import OpenClaw skills from ClawHub
    - Import ElizaOS characters/actions
    - Export AlleyBot skills to other formats
    """

    def __init__(self, config):
        super().__init__(config)
        self.imported_skills_dir = Path(self.project_root) / 'skills' / 'imported'
        self.imported_skills_dir.mkdir(parents=True, exist_ok=True)

    # === OpenClaw Format ===

    def import_openclaw_skill(self, skill_path: str) -> Dict[str, Any]:
        """
        Import an OpenClaw SKILL.md file.
        
        OpenClaw format:
        ```markdown
        ---
        name: skill-name
        description: What this skill does and when to use it
        ---
        
        ## Instructions
        Natural language instructions for the AI...
        
        ### Tools
        - tool.name: description
        ```
        """
        path = Path(skill_path)
        if not path.exists():
            return {'success': False, 'error': f'Skill not found: {skill_path}'}
        
        try:
            content = path.read_text()
            
            # Parse YAML frontmatter
            frontmatter = {}
            body = content
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2).strip()
            
            # Extract tools from body
            tools = self._extract_tools_from_openclaw(body)
            
            # Convert to AlleyBot format
            skill_name = frontmatter.get('name', path.parent.name)
            skill = SkillFormat(
                name=skill_name,
                description=frontmatter.get('description', ''),
                instructions=body,
                tools=tools,
                metadata={
                    'source': 'openclaw',
                    'original_path': str(path),
                    'imported_at': str(datetime.now())
                },
                source_format='openclaw'
            )
            
            # Save as AlleyBot skill
            result = self._save_as_alleybot_skill(skill)
            
            return {
                'success': True,
                'skill': skill_name,
                'tools': tools,
                'path': result.get('path')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _extract_tools_from_openclaw(self, body: str) -> List[str]:
        """Extract tool references from OpenClaw skill body"""
        tools = []
        
        # Pattern: - tool.name or tool.name: description
        tool_patterns = [
            r'[-*]\s*(\w+\.\w+):?',  # bullet list with tool.name
            r'`(\w+\.\w+)`',  # inline code with tool.name
            r'Use\s+(\w+\.\w+)',  # "Use tool.name"
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, body)
            for match in matches:
                if '.' in match and match not in tools:
                    tools.append(match)
        
        return tools

    def export_to_openclaw(self, skill_name: str, output_dir: str) -> Dict[str, Any]:
        """Export an AlleyBot skill to OpenClaw format"""
        skill = self._load_full_skill(skill_name)
        if not skill:
            return {'success': False, 'error': f'Skill not found: {skill_name}'}
        
        try:
            output_path = Path(output_dir) / skill_name
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create OpenClaw SKILL.md
            frontmatter = {
                'name': skill['name'],
                'description': skill['description']
            }
            
            # Add OpenClaw-specific metadata
            if 'metadata' in skill.get('frontmatter', {}):
                frontmatter.update(skill['frontmatter']['metadata'])
            
            skill_md = f"""---
{name}: {frontmatter['name']}
{description}: {frontmatter['description']}
---

# {skill['name']}

{skill['description']}

## Instructions

{skill['body']}

## Tools

This skill uses the following tools:
"""
            
            # Add tool references
            for tool in self._extract_tools_from_openclaw(skill['body']):
                skill_md += f"- `{tool}`\n"
            
            # Write SKILL.md
            skill_file = output_path / 'SKILL.md'
            skill_file.write_text(skill_md)
            
            # Copy scripts if any
            if skill.get('scripts'):
                scripts_dir = output_path / 'scripts'
                scripts_dir.mkdir(exist_ok=True)
                for script_path in skill['scripts']:
                    src = Path(script_path)
                    if src.exists():
                        dst = scripts_dir / src.name
                        dst.write_text(src.read_text())
            
            return {
                'success': True,
                'path': str(output_path),
                'format': 'openclaw'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === ElizaOS Format ===

    def import_elizaos_character(self, character_json_path: str) -> Dict[str, Any]:
        """
        Import an ElizaOS character.json as a skill.
        
        ElizaOS format:
        ```json
        {
          "name": "CharacterName",
          "clients": ["discord", "telegram"],
          "modelProvider": "anthropic",
          "settings": {...},
          "bio": ["Description..."],
          "lore": ["Backstory..."],
          "messageExamples": [...],
          "postExamples": [...],
          "topics": ["topic1", "topic2"],
          "style": {...},
          "adjectives": ["adjective1"]
        }
        ```
        """
        path = Path(character_json_path)
        if not path.exists():
            return {'success': False, 'error': f'Character not found: {character_json_path}'}
        
        try:
            char_data = json.loads(path.read_text())
            
            # Extract name and description
            name = char_data.get('name', 'unnamed-character')
            bio = char_data.get('bio', [])
            description = bio[0] if bio else f"ElizaOS character: {name}"
            
            # Build instructions from character data
            instructions = self._build_instructions_from_elizaos(char_data)
            
            # Extract capabilities (clients = channels)
            tools = []
            clients = char_data.get('clients', [])
            for client in clients:
                if client == 'discord':
                    tools.append('discord.send')
                elif client == 'telegram':
                    tools.append('telegram.send')
                elif client == 'twitter':
                    tools.append('social.post')
            
            skill = SkillFormat(
                name=name.lower().replace(' ', '-'),
                description=description,
                instructions=instructions,
                tools=tools,
                metadata={
                    'source': 'elizaos',
                    'original_path': str(path),
                    'topics': char_data.get('topics', []),
                    'adjectives': char_data.get('adjectives', [])
                },
                source_format='elizaos'
            )
            
            result = self._save_as_alleybot_skill(skill)
            
            return {
                'success': True,
                'skill': skill.name,
                'description': skill.description,
                'path': result.get('path')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_elizaos_action(self, action_path: str) -> Dict[str, Any]:
        """
        Import an ElizaOS action as a skill.
        
        ElizaOS actions are TypeScript files with:
        - name: Action name
        - description: What the action does
        - handler: The function that executes
        - examples: Example invocations
        """
        path = Path(action_path)
        if not path.exists():
            return {'success': False, 'error': f'Action not found: {action_path}'}
        
        try:
            # Read TypeScript file
            content = path.read_text()
            
            # Extract action metadata from TypeScript
            # Pattern: export const actionName = { ... }
            name_match = re.search(r'export\s+const\s+(\w+)\s*=', content)
            name = name_match.group(1) if name_match else path.stem
            
            # Extract description
            desc_match = re.search(r'description:[\s]*["\'](.+?)["\']', content)
            description = desc_match.group(1) if desc_match else f"ElizaOS action: {name}"
            
            # Extract handler logic (simplified)
            handler_match = re.search(r'handler:\s*async\s*\([^)]*\)\s*=>\s*\{([^}]+)\}', content)
            handler_code = handler_match.group(1) if handler_match else ""
            
            # Build instructions
            instructions = f"""# {name}

This is an imported ElizaOS action.

## Description
{description}

## Original Handler Logic
```typescript
{handler_code[:500]}
```

## Instructions
When this skill is activated, execute the equivalent of the original ElizaOS action.
Analyze the handler code above and implement similar functionality using AlleyBot tools.
"""
            
            skill = SkillFormat(
                name=name.lower().replace('_', '-'),
                description=description,
                instructions=instructions,
                tools=[],
                metadata={
                    'source': 'elizaos-action',
                    'original_path': str(path),
                    'original_code': content[:2000]
                },
                source_format='elizaos'
            )
            
            result = self._save_as_alleybot_skill(skill)
            
            return {
                'success': True,
                'skill': skill.name,
                'path': result.get('path')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _build_instructions_from_elizaos(self, char_data: Dict) -> str:
        """Convert ElizaOS character data to skill instructions"""
        instructions = []
        
        # Bio
        if char_data.get('bio'):
            instructions.append("## Character Bio")
            for item in char_data['bio']:
                instructions.append(f"- {item}")
        
        # Lore
        if char_data.get('lore'):
            instructions.append("\n## Background")
            for item in char_data['lore']:
                instructions.append(f"- {item}")
        
        # Style
        style = char_data.get('style', {})
        if style:
            instructions.append("\n## Communication Style")
            if style.get('all'):
                instructions.append(f"General: {', '.join(style['all'])}")
            if style.get('chat'):
                instructions.append(f"Chat: {', '.join(style['chat'])}")
            if style.get('post'):
                instructions.append(f"Posts: {', '.join(style['post'])}")
        
        # Topics
        if char_data.get('topics'):
            instructions.append(f"\n## Topics\n{', '.join(char_data['topics'])}")
        
        # Message examples as guidance
        if char_data.get('messageExamples'):
            instructions.append("\n## Example Conversations")
            for example in char_data['messageExamples'][:3]:  # Limit to 3
                if isinstance(example, list):
                    for msg in example:
                        user = msg.get('user', 'user')
                        content = msg.get('content', {}).get('text', '')
                        instructions.append(f"{user}: {content}")
                instructions.append("---")
        
        return '\n'.join(instructions)

    def _save_as_alleybot_skill(self, skill: SkillFormat) -> Dict[str, Any]:
        """Save a skill in AlleyBot format"""
        skill_dir = self.imported_skills_dir / skill.name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Create SKILL.md with YAML frontmatter
        frontmatter = {
            'name': skill.name,
            'description': skill.description,
            'metadata': skill.metadata
        }
        
        if skill.tools:
            frontmatter['tools'] = skill.tools
        
        yaml_fm = yaml.dump(frontmatter, default_flow_style=False)
        
        skill_md = f"""---
{yaml_fm}---

# {skill.name}

{skill.description}

## Instructions

{skill.instructions}
"""
        
        skill_file = skill_dir / 'SKILL.md'
        skill_file.write_text(skill_md)
        
        return {'success': True, 'path': str(skill_dir)}

    # === Commands ===

    def skill_import_openclaw_command(self, *args):
        """Import OpenClaw skill: skill_import_openclaw <path/to/SKILL.md>"""
        if not args:
            return "❌ Usage: skill_import_openclaw <path/to/SKILL.md>"
        
        path = ' '.join(args)
        result = self.import_openclaw_skill(path)
        
        if result['success']:
            return f"✅ Imported OpenClaw skill: {result['skill']}\n📁 Saved to: {result['path']}\n🔧 Tools: {', '.join(result.get('tools', []))}"
        return f"❌ Import failed: {result.get('error', 'Unknown error')}"

    def skill_import_elizaos_command(self, *args):
        """Import ElizaOS character: skill_import_elizaos <path/to/character.json>"""
        if not args:
            return "❌ Usage: skill_import_elizaos <path/to/character.json>"
        
        path = ' '.join(args)
        result = self.import_elizaos_character(path)
        
        if result['success']:
            return f"✅ Imported ElizaOS character: {result['skill']}\n📝 {result['description']}\n📁 Saved to: {result['path']}"
        return f"❌ Import failed: {result.get('error', 'Unknown error')}"

    def skill_export_openclaw_command(self, *args):
        """Export skill to OpenClaw format: skill_export_openclaw <skill_name> [output_dir]"""
        if not args:
            return "❌ Usage: skill_export_openclaw <skill_name> [output_dir]"
        
        skill_name = args[0]
        output_dir = args[1] if len(args) > 1 else './exported-skills'
        
        result = self.export_to_openclaw(skill_name, output_dir)
        
        if result['success']:
            return f"✅ Exported to OpenClaw format: {result['path']}"
        return f"❌ Export failed: {result.get('error', 'Unknown error')}"

    def get_commands(self):
        """Add format adapter commands"""
        base_commands = super().get_commands() if hasattr(super(), 'get_commands') else {}
        base_commands.update({
            'skill_import_openclaw': self.skill_import_openclaw_command,
            'skill_import_elizaos': self.skill_import_elizaos_command,
            'skill_export_openclaw': self.skill_export_openclaw_command,
        })
        return base_commands


# Import datetime for metadata
from datetime import datetime
