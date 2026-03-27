"""
AlleyBot Autonomous Coder - Phase 4: Self-Extension Pipeline

Takes SkillSpecifications and generates actual Python code.
Writes files to skills/ directory for hot-loading.

Part of AGI Core - Phase 4: Self-Extension
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SkillSpecification:
    """Specification for a skill to be generated"""
    id: str
    name: str
    description: str
    category: str
    file_structure: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    
    def to_skill_md(self) -> str:
        """Convert to SKILL.md format"""
        return f"""# {self.name}

## Description
{self.description}

## Category
{self.category}

## Evidence
{chr(10).join(f"- {e}" for e in self.evidence)}

## Dependencies
{chr(10).join(f"- {d}" for d in self.dependencies)}

## Files
{chr(10).join(f"- {f}: {desc}" for f, desc in self.file_structure.items())}
"""


@dataclass
class GeneratedSkill:
    """Result of code generation"""
    spec_id: str
    skill_name: str
    files_created: List[str]
    skill_path: str
    generated_at: datetime
    status: str  # 'generated', 'tested', 'deployed', 'failed'
    errors: List[str]


class AutonomousCoder:
    """
    Generates Python code from skill specifications.
    
    Usage:
        coder = AutonomousCoder()
        
        # Generate from spec
        skill = coder.generate_skill(spec)
        
        # Deploy
        coder.deploy_skill(skill)
    """
    
    SKILLS_DIR = Path('sandbox/draft_skills')
    
    def __init__(self):
        self.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        self.generated_skills: Dict[str, GeneratedSkill] = {}
    
    def generate_skill(self, spec: SkillSpecification) -> GeneratedSkill:
        """
        Generate complete skill code from specification.
        
        Args:
            spec: SkillSpecification to implement
            
        Returns:
            GeneratedSkill with file paths
        """
        skill_path = self.SKILLS_DIR / spec.id
        skill_path.mkdir(exist_ok=True)
        
        files_created = []
        errors = []
        
        try:
            # Create SKILL.md
            skill_md = spec.to_skill_md()
            md_path = skill_path / 'SKILL.md'
            md_path.write_text(skill_md)
            files_created.append(str(md_path))
            
            # Generate each file from spec
            for filename, description in spec.file_structure.items():
                file_path = skill_path / filename
                
                if filename == '__init__.py':
                    content = self._generate_init(spec)
                elif filename == 'client.py':
                    content = self._generate_client(spec)
                elif filename == 'actions.py':
                    content = self._generate_actions(spec)
                elif filename == 'models.py':
                    content = self._generate_models(spec)
                elif filename == 'analyzer.py':
                    content = self._generate_analyzer(spec)
                elif filename == 'helpers.py':
                    content = self._generate_helpers(spec)
                else:
                    content = self._generate_generic(spec, description)
                
                file_path.write_text(content)
                files_created.append(str(file_path))
                logger.info(f"✅ Generated {filename}")
            
            # Create requirements.txt if needed
            if spec.dependencies:
                req_path = skill_path / 'requirements.txt'
                req_content = '\n'.join(spec.dependencies)
                req_path.write_text(req_content)
                files_created.append(str(req_path))
            
            # Create tests
            test_content = self._generate_tests(spec)
            test_path = skill_path / 'test_skill.py'
            test_path.write_text(test_content)
            files_created.append(str(test_path))
            
            # Register
            skill = GeneratedSkill(
                spec_id=spec.id,
                skill_name=spec.name,
                files_created=files_created,
                skill_path=str(skill_path),
                generated_at=datetime.now(),
                status='generated',
                errors=errors
            )
            self.generated_skills[spec.id] = skill
            
            logger.info(f"✅ Skill generated: {spec.name} at {skill_path}")
            return skill
            
        except Exception as e:
            logger.error(f"❌ Skill generation failed: {e}")
            errors.append(str(e))
            return GeneratedSkill(
                spec_id=spec.id,
                skill_name=spec.name,
                files_created=files_created,
                skill_path=str(skill_path),
                generated_at=datetime.now(),
                status='failed',
                errors=errors
            )
    
    def _generate_init(self, spec: SkillSpecification) -> str:
        """Generate __init__.py"""
        return f'''"""
{spec.name}

{spec.description}

Generated by AlleyBot Self-Extension Pipeline
"""

from .client import SkillClient
from .actions import execute_action

__version__ = "0.1.0"
__all__ = ["SkillClient", "execute_action"]
'''
    
    def _generate_client(self, spec: SkillSpecification) -> str:
        """Generate API client"""
        return f'''"""
Skill Client for {spec.name}
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SkillClient:
    """Main client for {spec.name}"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {{}}
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize the skill"""
        try:
            # Add initialization logic here
            self.initialized = True
            logger.info("✅ {spec.name} initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {{e}}")
            return False
    
    def process(self, **kwargs) -> Dict[str, Any]:
        """
        Main processing function.
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Processing results
        """
        if not self.initialized:
            self.initialize()
        
        try:
            # Main logic here
            result = {{"success": True, "output": None}}
            return result
        except Exception as e:
            logger.error(f"❌ Processing error: {{e}}")
            return {{"success": False, "error": str(e)}}
'''
    
    def _generate_actions(self, spec: SkillSpecification) -> str:
        """Generate actions module"""
        return f'''"""
Actions for {spec.name}
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


AVAILABLE_ACTIONS = [
    "process",
    "validate",
    "transform"
]


def execute_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an action by name.
    
    Args:
        action: Action name
        params: Action parameters
        
    Returns:
        Action result
    """
    if action not in AVAILABLE_ACTIONS:
        return {{"success": False, "error": f"Unknown action: {{action}}"}}
    
    try:
        # Dispatch to action handler
        handlers = {{
            "process": _handle_process,
            "validate": _handle_validate,
            "transform": _handle_transform
        }}
        
        handler = handlers.get(action, _handle_default)
        return handler(params)
        
    except Exception as e:
        logger.error(f"❌ Action execution failed: {{e}}")
        return {{"success": False, "error": str(e)}}


def _handle_process(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle 'process' action"""
    return {{"success": True, "result": "Processed"}}


def _handle_validate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle 'validate' action"""
    return {{"success": True, "valid": True}}


def _handle_transform(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle 'transform' action"""
    return {{"success": True, "transformed": params}}


def _handle_default(params: Dict[str, Any]) -> Dict[str, Any]:
    """Default handler"""
    return {{"success": False, "error": "Not implemented"}}
'''
    
    def _generate_models(self, spec: SkillSpecification) -> str:
        """Generate data models"""
        return f'''"""
Data Models for {spec.name}
"""

from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class SkillInput:
    """Input data structure"""
    data: Any
    options: Optional[dict] = None


@dataclass
class SkillOutput:
    """Output data structure"""
    success: bool
    result: Any
    error: Optional[str] = None
'''
    
    def _generate_analyzer(self, spec: SkillSpecification) -> str:
        """Generate analyzer module"""
        return f'''"""
Analyzer for {spec.name}
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class Analyzer:
    """Main analyzer class"""
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze input data"""
        return {{"success": True, "insights": []}}
    
    def report(self, results: Dict[str, Any]) -> str:
        """Generate report from results"""
        return "Analysis complete"
'''
    
    def _generate_helpers(self, spec: SkillSpecification) -> str:
        """Generate helper functions"""
        return f'''"""
Helper Functions for {spec.name}
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def format_data(data: Any) -> str:
    """Format data for display"""
    return str(data)


def validate_input(data: Any) -> bool:
    """Validate input data"""
    return data is not None


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dict"""
    return data.get(key, default)
'''
    
    def _generate_generic(self, spec: SkillSpecification, description: str) -> str:
        """Generate generic file"""
        return f'''"""
{description}

Part of {spec.name}
"""

import logging

logger = logging.getLogger(__name__)


# TODO: Implement this module
# Based on specification: {spec.description}
'''
    
    def _generate_tests(self, spec: SkillSpecification) -> str:
        """Generate test file"""
        return f'''"""
Tests for {spec.name}

Generated by AlleyBot Self-Extension Pipeline
"""

import pytest
from {spec.id.replace("-", "_")} import SkillClient


class TestSkill:
    """Test suite for {spec.name}"""
    
    def test_initialization(self):
        """Test skill can be initialized"""
        client = SkillClient()
        assert client.initialize() == True
        assert client.initialized == True
    
    def test_process(self):
        """Test basic processing"""
        client = SkillClient()
        client.initialize()
        
        result = client.process()
        assert isinstance(result, dict)
        assert "success" in result
    
    def test_error_handling(self):
        """Test error handling"""
        client = SkillClient()
        result = client.process(invalid_param=True)
        assert isinstance(result, dict)
'''
    
    def deploy_skill(self, skill: GeneratedSkill) -> bool:
        """
        Deploy a generated skill to production.
        
        This marks the skill as deployed and makes it available for use.
        
        Args:
            skill: GeneratedSkill to deploy
            
        Returns:
            True if deployment successful
        """
        try:
            if skill.status != 'generated':
                logger.warning(f"Cannot deploy skill {skill.skill_name} - status is {skill.status}")
                return False
            
            # Update skill status
            skill.status = 'deployed'
            self.generated_skills[skill.spec_id] = skill
            
            logger.info(f"🚀 Deployed skill: {skill.skill_name} at {skill.skill_path}")
            logger.info(f"   Files: {len(skill.files_created)}")
            
            # TODO: In future, could hot-reload the skill into the plugin system
            # For now, skills will be loaded on next restart
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Skill deployment failed: {e}")
            skill.status = 'failed'
            skill.errors.append(f"Deployment error: {str(e)}")
            return False
    
    def get_skill_status(self, spec_id: str) -> Optional[GeneratedSkill]:
        """Get status of generated skill"""
        return self.generated_skills.get(spec_id)
    
    def list_generated_skills(self) -> List[GeneratedSkill]:
        """List all generated skills"""
        return list(self.generated_skills.values())


# Singleton
_coder_instance: Optional[AutonomousCoder] = None


def get_autonomous_coder() -> AutonomousCoder:
    """Get or create autonomous coder singleton"""
    global _coder_instance
    if _coder_instance is None:
        _coder_instance = AutonomousCoder()
    return _coder_instance
