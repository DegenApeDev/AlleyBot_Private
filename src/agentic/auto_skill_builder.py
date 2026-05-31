"""
Autonomous Skill Building System

Enables AlleyBot to build new skills and integrations automatically based on:
- Observations from platforms
- Gaps in capabilities
- New platform features detected
- Learning from outcomes

Part of 100% autonomous operation.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from src.agentic.autonomous_coder import SkillSpecification

logger = logging.getLogger(__name__)


@dataclass
class SkillProposal:
    """Proposal for a new skill to build"""
    name: str
    description: str
    platform: str
    reason: str  # Why this skill is needed
    priority: int  # 1-10
    estimated_complexity: str  # 'simple', 'medium', 'complex'
    required_apis: List[str]
    example_use_case: str


class AutoSkillBuilder:
    """
    Automatically builds new skills and integrations.
    
    Features:
    - Detects capability gaps from observations
    - Monitors platform skill.md updates
    - Generates skill proposals
    - Auto-codes simple skills
    - Learns from skill usage patterns
    """
    
    def __init__(self, core, plugin_manager):
        self.core = core
        self.plugin_manager = plugin_manager
        self.skill_proposals: List[SkillProposal] = []
        self.built_skills: List[str] = []
        self.skill_usage: Dict[str, int] = {}
        
        # Get autonomous coder using unified pattern (same as autonomous_brain.py)
        from src.agentic.autonomous_coder import get_best_coder
        self.autonomous_coder = get_best_coder(plugin_manager)
        
        # Get skilldoc manager
        from src.agentic.skilldoc_manager import get_skilldoc_manager
        self.skilldoc_manager = get_skilldoc_manager()
        
        # Register callback for skill.md updates
        self.skilldoc_manager.register_update_callback(self._on_skill_doc_updated)
    
    def _on_skill_doc_updated(self, platform: str, content: str):
        """Called when a platform's skill.md is updated"""
        logger.info(f"📚 Skill.md updated for {platform}, analyzing for new capabilities...")
        
        # Parse new capabilities
        new_capabilities = self._parse_skill_doc_capabilities(content)
        
        # Check which ones we don't have yet
        for capability in new_capabilities:
            if not self._has_capability(capability):
                # Propose building this skill
                proposal = SkillProposal(
                    name=f"{platform}_{capability['name']}",
                    description=capability['description'],
                    platform=platform,
                    reason=f"New capability detected in {platform} skill.md update",
                    priority=7,
                    estimated_complexity='medium',
                    required_apis=[capability.get('endpoint', '')],
                    example_use_case=capability.get('example', '')
                )
                self.skill_proposals.append(proposal)
                logger.info(f"💡 Proposed new skill: {proposal.name}")
    
    def _parse_skill_doc_capabilities(self, content: str) -> List[Dict]:
        """Parse capabilities from skill.md content"""
        capabilities = []
        
        # Look for endpoint definitions
        import re
        endpoint_pattern = r'(?:POST|GET|PUT|DELETE)\s+([/\w\-]+)'
        endpoints = re.findall(endpoint_pattern, content)
        
        # Look for capability descriptions
        capability_pattern = r'##\s+([^\n]+)\n([^\n]+)'
        matches = re.findall(capability_pattern, content)
        
        for i, endpoint in enumerate(endpoints[:10]):  # Limit to 10
            description = matches[i][1] if i < len(matches) else "New capability"
            capabilities.append({
                'name': endpoint.replace('/', '_').strip('_'),
                'description': description,
                'endpoint': endpoint
            })
        
        return capabilities
    
    def _has_capability(self, capability: Dict) -> bool:
        """Check if we already have this capability"""
        # Check if skill exists
        skill_name = capability['name']
        
        # Check in skills directory
        from pathlib import Path
        skills_dir = Path(self.core.config_dir) / '..' / 'skills'
        if skills_dir.exists():
            for skill_file in skills_dir.glob('**/*.md'):
                if skill_name.lower() in skill_file.stem.lower():
                    return True
        
        return False
    
    async def detect_capability_gaps(self, observations: List[Any]) -> List[SkillProposal]:
        """Detect capability gaps from observations"""
        proposals = []
        
        # Analyze observations for patterns we can't handle
        for obs in observations:
            if hasattr(obs, 'metadata'):
                metadata = obs.metadata
                
                # Check for API errors (might indicate missing capability)
                if metadata.get('error') and 'not found' in str(metadata.get('error')).lower():
                    # Propose skill to handle this
                    proposal = SkillProposal(
                        name=f"handle_{metadata.get('action', 'unknown')}",
                        description=f"Handle {metadata.get('action')} action",
                        platform=metadata.get('plugin', 'unknown'),
                        reason="Detected error indicating missing capability",
                        priority=6,
                        estimated_complexity='simple',
                        required_apis=[],
                        example_use_case=str(metadata.get('error', ''))[:100]
                    )
                    proposals.append(proposal)
        
        return proposals
    
    async def auto_build_simple_skills(self, max_skills: int = 1):
        """Automatically build simple skills from proposals"""
        if not self.autonomous_coder:
            logger.warning("⚠️ Autonomous coder not available, cannot auto-build skills")
            return
        
        # Sort proposals by priority
        sorted_proposals = sorted(
            [p for p in self.skill_proposals if p.estimated_complexity == 'simple'],
            key=lambda x: x.priority,
            reverse=True
        )
        
        built_count = 0
        for proposal in sorted_proposals[:max_skills]:
            try:
                logger.info(f"🔨 Auto-building skill: {proposal.name}")
                
                # Generate skill specification
                spec = self._generate_skill_spec(proposal)
                
                # Use autonomous coder to generate code
                result = await self._build_skill_with_ai(proposal, spec)
                
                if result.get('success'):
                    self.built_skills.append(proposal.name)
                    self.skill_proposals.remove(proposal)
                    built_count += 1
                    logger.info(f"✅ Successfully built skill: {proposal.name}")
                else:
                    logger.warning(f"⚠️ Failed to build skill: {proposal.name}")
            
            except Exception as e:
                logger.error(f"❌ Error building skill {proposal.name}: {e}")
        
        return built_count
    
    def _generate_skill_spec(self, proposal: SkillProposal) -> Dict:
        """Generate skill specification from proposal"""
        return {
            'name': proposal.name,
            'description': proposal.description,
            'platform': proposal.platform,
            'capabilities': [
                {
                    'name': proposal.name,
                    'description': proposal.description,
                    'parameters': [],
                    'returns': 'Dict'
                }
            ],
            'dependencies': proposal.required_apis,
            'example': proposal.example_use_case
        }
    
    async def _build_skill_with_ai(self, proposal: SkillProposal, spec: Dict) -> Dict:
        """Build skill using AutonomousCoder's structured generation pipeline."""
        try:
            # Convert proposal to SkillSpecification
            specification = SkillSpecification(
                id=f"{proposal.platform}_{proposal.name}_{int(datetime.now().timestamp())}",
                name=proposal.name,
                description=proposal.description,
                category=proposal.platform,
                file_structure={
                    '__init__.py': f'Plugin entry point for {proposal.name}',
                    'client.py': f'Client for {proposal.description}',
                    'actions.py': f'Action handlers for {proposal.name}',
                    'models.py': f'Data models for {proposal.name}',
                },
                dependencies=proposal.required_apis,
                evidence=[proposal.reason, f"Example: {proposal.example_use_case}"]
            )

            # Generate skill code
            skill = self.autonomous_coder.generate_skill(specification)
            if skill.status == 'failed':
                return {'success': False, 'error': f"Generation failed: {skill.errors}"}

            logger.info(f"✅ Skill code generated: {skill.skill_name} ({len(skill.files_created)} files)")

            # Deploy to hot-load into the system
            deployed = self.autonomous_coder.deploy_skill(skill)
            if not deployed:
                return {'success': False, 'error': 'Skill generated but deployment failed'}

            return {
                'success': True,
                'skill_name': skill.skill_name,
                'files': skill.files_created,
                'path': skill.skill_path,
            }

        except Exception as e:
            logger.error(f"❌ AI skill building error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_skill_file(self, name: str, code: str, spec: Dict) -> str:
        """Save generated skill file"""
        from pathlib import Path
        
        # Create auto_acquired directory
        skills_dir = Path(self.core.config_dir) / '..' / 'skills' / 'auto_acquired'
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Python file
        py_file = skills_dir / f"{name}.py"
        with open(py_file, 'w') as f:
            f.write(code)
        
        # Save SKILL.md
        md_file = skills_dir / f"{name}.md"
        with open(md_file, 'w') as f:
            f.write(self._generate_skill_md(name, spec))
        
        logger.info(f"💾 Saved skill files: {py_file}, {md_file}")
        return str(py_file)
    
    def _generate_skill_md(self, name: str, spec: Dict) -> str:
        """Generate SKILL.md content"""
        return f"""# {name}

**Auto-generated skill**

## Description
{spec['description']}

## Platform
{spec['platform']}

## Capabilities
{chr(10).join(f"- {cap['name']}: {cap['description']}" for cap in spec['capabilities'])}

## Dependencies
{chr(10).join(f"- {dep}" for dep in spec.get('dependencies', []))}

## Generated
{datetime.now().isoformat()}

## Status
Active - Auto-built by AlleyBot
"""
    
    def track_skill_usage(self, skill_name: str):
        """Track skill usage for learning"""
        if skill_name not in self.skill_usage:
            self.skill_usage[skill_name] = 0
        self.skill_usage[skill_name] += 1
        
        # Log popular skills
        if self.skill_usage[skill_name] % 10 == 0:
            logger.info(f"📊 Skill {skill_name} used {self.skill_usage[skill_name]} times")
    
    def get_status(self) -> Dict:
        """Get auto skill builder status"""
        return {
            'proposals_pending': len(self.skill_proposals),
            'skills_built': len(self.built_skills),
            'top_skills': sorted(
                self.skill_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'recent_builds': self.built_skills[-5:]
        }


# Singleton instance
_auto_skill_builder = None


def get_auto_skill_builder(core=None, plugin_manager=None):
    """Get or create auto skill builder singleton"""
    global _auto_skill_builder
    if _auto_skill_builder is None and core and plugin_manager:
        _auto_skill_builder = AutoSkillBuilder(core, plugin_manager)
    return _auto_skill_builder
