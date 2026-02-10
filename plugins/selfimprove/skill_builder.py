"""
Skill Builder Mixin
AI-powered skill generation following the Agent Skills specification (agentskills.io).
Skills are SKILL.md files with YAML frontmatter + markdown instructions.

Platform skill docs are used as references:
- Moltx: https://moltx.io/skill.md
- Moltbook: https://moltbook.io/skill.md (if available)
"""
import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


# Platforms AlleyBot operates on — used for gap analysis
ACTIVE_PLATFORMS = {
    'moltx': {
        'skill_url': 'https://moltx.io/skill.md',
        'description': 'Twitter-like social platform for AI agents',
        'capabilities': ['post', 'reply', 'like', 'follow', 'feed', 'trending', 'articles', 'DMs'],
    },
    'moltbook': {
        'skill_url': 'https://moltbook.io/skill.md',
        'description': 'Reddit-like forum platform for AI agents',
        'capabilities': ['post', 'comment', 'upvote', 'submolts', 'feed'],
    },
    'clawbr': {
        'skill_url': 'https://clawbr.org/skill.md',
        'description': 'Social network for AI agents with debates, voting, and leaderboard',
        'capabilities': [
            'post', 'reply', 'like', 'follow', 'feed', 'debates', 'vote',
            'notifications', 'search', 'leaderboard', 'verification', 'stats'
        ],
    },
    'onchain': {
        'skill_url': None,
        'description': 'On-chain operations on Base (EVM)',
        'capabilities': ['wallet', 'balance', 'transfer', 'token_tracking', 'tx_lookup'],
    },
}


class SkillBuilderMixin:
    """Mixin for discovering, loading, and generating Agent Skills (SKILL.md format)"""

    def _init_skill_builder(self):
        """Initialize the skill builder"""
        self.skills_dir = Path('skills')
        self.skills_dir.mkdir(exist_ok=True)
        self.loaded_skills: Dict[str, Dict] = {}
        self._discover_skills()

    def _discover_skills(self) -> Dict[str, Dict]:
        """Discover all SKILL.md files in the skills directory"""
        self.loaded_skills = {}

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / 'SKILL.md'
            if not skill_md.exists():
                continue

            try:
                meta = self._parse_skill_metadata(skill_md)
                if meta:
                    self.loaded_skills[meta['name']] = {
                        'name': meta['name'],
                        'description': meta['description'],
                        'path': str(skill_dir),
                        'has_scripts': (skill_dir / 'scripts').is_dir(),
                        'has_references': (skill_dir / 'references').is_dir(),
                        'has_assets': (skill_dir / 'assets').is_dir(),
                    }
            except Exception as e:
                print(f"⚠️  Failed to parse skill {skill_dir.name}: {e}")

        return self.loaded_skills

    def _parse_skill_metadata(self, skill_md_path: Path) -> Optional[Dict]:
        """Parse YAML frontmatter from a SKILL.md file"""
        content = skill_md_path.read_text(encoding='utf-8')

        # Extract YAML frontmatter between --- markers
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not frontmatter or 'name' not in frontmatter:
                return None
            return {
                'name': frontmatter['name'],
                'description': frontmatter.get('description', ''),
            }
        except yaml.YAMLError:
            return None

    def _read_skill(self, skill_name: str) -> Optional[str]:
        """Read the full SKILL.md content for activation"""
        skill = self.loaded_skills.get(skill_name)
        if not skill:
            return None
        skill_md = Path(skill['path']) / 'SKILL.md'
        if skill_md.exists():
            return skill_md.read_text(encoding='utf-8')
        return None

    def list_skills_command(self, *args) -> str:
        """List all discovered skills"""
        self._discover_skills()
        if not self.loaded_skills:
            return "📭 No skills found in skills/ directory"

        output = f"🧩 Discovered Skills ({len(self.loaded_skills)})\n\n"
        for name, info in self.loaded_skills.items():
            extras = []
            if info['has_scripts']:
                extras.append('scripts')
            if info['has_references']:
                extras.append('refs')
            if info['has_assets']:
                extras.append('assets')
            extra_str = f" [{', '.join(extras)}]" if extras else ""
            output += f"  📄 {name}{extra_str}\n"
            output += f"     {info['description'][:100]}\n\n"
        return output

    # ------------------------------------------------------------------
    # Gap analysis — identify what skills AlleyBot is missing
    # ------------------------------------------------------------------

    def _identify_skill_gaps(self) -> List[Dict]:
        """Analyze current capabilities and identify gaps worth filling"""
        gaps = []
        existing_names = set(self.loaded_skills.keys())

        # Check action history for failures
        brain = None
        if hasattr(self, 'core') and self.core:
            brain = self.core.plugin_manager.plugins.get('brain')

        failure_actions = {}
        if brain and hasattr(brain, 'action_history'):
            for entry in brain.action_history[-50:]:
                if not entry.get('success'):
                    action = entry.get('action', '')
                    failure_actions[action] = failure_actions.get(action, 0) + 1

        # Gap: engagement optimization (if we don't have it)
        if 'engagement-optimizer' not in existing_names:
            gaps.append({
                'name': 'engagement-optimizer',
                'reason': 'No skill for optimizing post timing, content style, and engagement patterns',
                'platform': 'moltx',
                'priority': 0.8,
            })

        # Gap: content strategy
        if 'content-strategy' not in existing_names:
            gaps.append({
                'name': 'content-strategy',
                'reason': 'No skill for planning content themes, avoiding repetition, maintaining voice',
                'platform': 'all',
                'priority': 0.7,
            })

        # Gap: reputation building
        if 'reputation-builder' not in existing_names:
            gaps.append({
                'name': 'reputation-builder',
                'reason': 'No skill for systematic reputation building across platforms',
                'platform': 'all',
                'priority': 0.6,
            })

        # Gap: conversation threading
        if 'conversation-threading' not in existing_names:
            gaps.append({
                'name': 'conversation-threading',
                'reason': 'No skill for maintaining multi-turn conversations and building relationships',
                'platform': 'moltx',
                'priority': 0.5,
            })

        # Add gaps from frequent failures
        for action, count in failure_actions.items():
            if count >= 2:
                gap_name = f"{action}-recovery"
                if gap_name not in existing_names:
                    gaps.append({
                        'name': gap_name,
                        'reason': f'Action {action} failed {count} times recently',
                        'platform': 'system',
                        'priority': min(0.9, 0.3 + count * 0.1),
                    })

        # Sort by priority
        gaps.sort(key=lambda g: g['priority'], reverse=True)
        return gaps

    # ------------------------------------------------------------------
    # AI-powered skill generation
    # ------------------------------------------------------------------

    def _generate_skill(self, gap: Dict) -> Optional[str]:
        """Use AI to generate a SKILL.md file for a given gap"""
        skill_name = gap['name']
        reason = gap['reason']
        platform = gap.get('platform', 'all')
        
        print(f"[SKILL-DEBUG] Starting skill generation for: {skill_name}")
        print(f"[SKILL-DEBUG] Reason: {reason}")
        print(f"[SKILL-DEBUG] Platform: {platform}")

        # Build context about existing skills
        existing_summary = ", ".join(self.loaded_skills.keys()) if self.loaded_skills else "none"
        print(f"[SKILL-DEBUG] Existing skills ({len(self.loaded_skills)}): {existing_summary[:100]}...")

        # Platform-specific context
        platform_context = ""
        if platform in ACTIVE_PLATFORMS:
            p = ACTIVE_PLATFORMS[platform]
            platform_context = f"\nTarget platform: {p['description']}\nPlatform capabilities: {', '.join(p['capabilities'])}"
            print(f"[SKILL-DEBUG] Platform context added: {p['description']}")

        prompt = f"""You are AlleyBot, an autonomous AI agent building a new skill for yourself.

Generate a SKILL.md file following the Agent Skills specification (agentskills.io).

Requirements:
- YAML frontmatter with `name` and `description` fields
- name must be lowercase with hyphens only: {skill_name}
- description should explain WHAT the skill does and WHEN to use it (1-2 sentences)
- Body: practical, actionable instructions YOU will follow
- Include specific API endpoints, data structures, and decision logic
- Keep under 200 lines — be concise, you're already smart
- No README, no CHANGELOG, no setup instructions — just the skill

Skill to build: {skill_name}
Reason needed: {reason}
{platform_context}

Existing skills: {existing_summary}

Generate ONLY the SKILL.md content, starting with --- frontmatter."""

        print(f"[SKILL-DEBUG] Prompt length: {len(prompt)} chars")

        # Try Grok first, then DeepSeek
        content = None
        grok_error = None
        deepseek_error = None
        
        try:
            print(f"[SKILL-DEBUG] Attempting Grok AI generation...")
            from grok_ai import grok_ai
            print(f"[SKILL-DEBUG] Grok enabled: {grok_ai.enabled}")
            
            if grok_ai.enabled:
                content = grok_ai.chat(prompt, max_tokens=2000)
                print(f"[SKILL-DEBUG] Grok returned content: {bool(content)}, length: {len(content) if content else 0}")
            else:
                print(f"[SKILL-DEBUG] Grok is disabled, skipping")
        except Exception as e:
            grok_error = str(e)
            print(f"[SKILL-DEBUG] ❌ Grok skill generation failed: {e}")
            import traceback
            traceback.print_exc()

        if not content:
            try:
                print(f"[SKILL-DEBUG] Attempting DeepSeek AI generation...")
                from deepseek_ai import deepseek_ai
                print(f"[SKILL-DEBUG] DeepSeek enabled: {deepseek_ai.enabled}")
                
                if deepseek_ai.enabled:
                    content = deepseek_ai.chat(prompt, max_tokens=2000)
                    print(f"[SKILL-DEBUG] DeepSeek returned content: {bool(content)}, length: {len(content) if content else 0}")
                else:
                    print(f"[SKILL-DEBUG] DeepSeek is disabled, skipping")
            except Exception as e:
                deepseek_error = str(e)
                print(f"[SKILL-DEBUG] ❌ DeepSeek skill generation failed: {e}")
                import traceback
                traceback.print_exc()

        if not content:
            print(f"[SKILL-DEBUG] ❌ No AI provider returned content")
            print(f"[SKILL-DEBUG] Grok error: {grok_error}")
            print(f"[SKILL-DEBUG] DeepSeek error: {deepseek_error}")
            return None

        # Clean up — ensure it starts with ---
        print(f"[SKILL-DEBUG] Cleaning up AI output...")
        original_content = content
        content = content.strip()
        print(f"[SKILL-DEBUG] After strip: {len(content)} chars")
        
        if not content.startswith('---'):
            print(f"[SKILL-DEBUG] Content doesn't start with '---', searching for frontmatter...")
            # Try to find the frontmatter start
            idx = content.find('---')
            if idx >= 0:
                print(f"[SKILL-DEBUG] Found '---' at index {idx}, extracting from there")
                content = content[idx:]
            else:
                print(f"[SKILL-DEBUG] ❌ No '---' found in content! First 200 chars: {content[:200]}")
                return None
        else:
            print(f"[SKILL-DEBUG] Content starts with '---' ✓")

        # Remove trailing markdown code fences if AI wrapped it
        content = re.sub(r'```\s*$', '', content).strip()
        print(f"[SKILL-DEBUG] Final content length: {len(content)} chars")
        print(f"[SKILL-DEBUG] First 100 chars: {content[:100]}...")

        return content

    def build_skill_command(self, *args) -> str:
        """Build a new skill based on identified gaps or a specific topic"""
        print(f"[SKILL-DEBUG] build_skill_command called with args: {args}")
        
        self._discover_skills()
        print(f"[SKILL-DEBUG] Discovered {len(self.loaded_skills)} existing skills")

        # If a topic is provided, build that specific skill
        if args:
            topic = '-'.join(args).lower().replace(' ', '-')
            # Clean name per spec
            topic = re.sub(r'[^a-z0-9-]', '', topic)
            topic = re.sub(r'-+', '-', topic).strip('-')
            gap = {
                'name': topic,
                'reason': f'User requested skill: {" ".join(args)}',
                'platform': 'all',
                'priority': 1.0,
            }
            print(f"[SKILL-DEBUG] User requested skill: {topic}")
        else:
            # Auto-identify the highest priority gap
            print(f"[SKILL-DEBUG] No args provided, auto-identifying gaps...")
            gaps = self._identify_skill_gaps()
            if not gaps:
                print(f"[SKILL-DEBUG] No gaps identified")
                return "✅ No skill gaps identified — all capabilities covered!"
            gap = gaps[0]
            print(f"[SKILL-DEBUG] Selected highest priority gap: {gap['name']} (priority: {gap['priority']})")

        skill_name = gap['name']
        print(f"🧩 Building skill: {skill_name} ({gap['reason']})")

        # Check if skill already exists
        if skill_name in self.loaded_skills:
            print(f"[SKILL-DEBUG] Skill '{skill_name}' already exists!")
            return f"⚠️  Skill '{skill_name}' already exists at {self.loaded_skills[skill_name]['path']}"

        # Generate the SKILL.md content
        print(f"[SKILL-DEBUG] Calling _generate_skill for: {skill_name}")
        content = self._generate_skill(gap)
        if not content:
            print(f"[SKILL-DEBUG] ❌ _generate_skill returned None for '{skill_name}'")
            return f"❌ Failed to generate skill content for '{skill_name}'"
        
        print(f"[SKILL-DEBUG] ✓ Generated content: {len(content)} chars")

        # Validate frontmatter
        print(f"[SKILL-DEBUG] Validating frontmatter...")
        meta = None
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                meta = yaml.safe_load(match.group(1))
                print(f"[SKILL-DEBUG] Frontmatter parsed successfully: {meta}")
            except yaml.YAMLError as e:
                print(f"[SKILL-DEBUG] ❌ YAML parsing error: {e}")
                pass
        else:
            print(f"[SKILL-DEBUG] ❌ No frontmatter match found in content")

        if not meta or 'name' not in meta or 'description' not in meta:
            print(f"[SKILL-DEBUG] ❌ Invalid frontmatter. meta={meta}, has_name={'name' in meta if meta else False}, has_desc={'description' in meta if meta else False}")
            return f"❌ Generated skill has invalid frontmatter"

        # Write the skill
        print(f"[SKILL-DEBUG] Writing skill to disk...")
        skill_dir = self.skills_dir / skill_name
        print(f"[SKILL-DEBUG] Skill directory: {skill_dir}")
        skill_dir.mkdir(exist_ok=True)
        skill_md = skill_dir / 'SKILL.md'
        print(f"[SKILL-DEBUG] Writing to: {skill_md}")
        
        try:
            skill_md.write_text(content, encoding='utf-8')
            print(f"[SKILL-DEBUG] ✓ Successfully wrote {len(content)} chars to {skill_md}")
        except Exception as e:
            print(f"[SKILL-DEBUG] ❌ Failed to write skill file: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Failed to write skill file: {e}"

        # Re-discover to pick it up
        print(f"[SKILL-DEBUG] Re-discovering skills...")
        self._discover_skills()

        line_count = len(content.split('\n'))
        output = f"✅ Skill '{skill_name}' created!\n"
        output += f"   📄 {skill_md} ({line_count} lines)\n"
        output += f"   📝 {meta['description'][:100]}\n"
        output += f"   💡 Reason: {gap['reason']}\n"

        # Log to memory
        if hasattr(self, 'core') and self.core:
            try:
                skill_log = self.core.get_memory('skill_build_log') or []
                if not isinstance(skill_log, list):
                    skill_log = []
                skill_log.append({
                    'name': skill_name,
                    'reason': gap['reason'],
                    'timestamp': datetime.now().isoformat(),
                    'lines': line_count,
                })
                self.core.save_memory('skill_build_log', skill_log[-50:])
                print(f"[SKILL-DEBUG] ✓ Logged skill creation to memory")
            except Exception as e:
                print(f"[SKILL-DEBUG] ⚠️ Failed to log to memory: {e}")
                pass

        print(f"[SKILL-DEBUG] ✓ Skill creation complete!")
        return output
