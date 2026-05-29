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
        """Generate generic file with meaningful scaffold based on description keywords."""
        desc_lower = description.lower()

        if 'api' in desc_lower or 'endpoint' in desc_lower or 'client' in desc_lower:
            return f'''"""
{description}

Part of {spec.name}
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ApiConfig:
    base_url: str = ""
    api_key: Optional[str] = None
    timeout: int = 30


class ApiClient:
    """API client for {spec.name}"""

    def __init__(self, config: Optional[ApiConfig] = None):
        self.config = config or ApiConfig()

    async def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make API request"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{{self.config.base_url}}{{path}}"
                async with session.request(method, url, **kwargs) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"API request failed: {{e}}")
            return {{"success": False, "error": str(e)}}

    async def health_check(self) -> bool:
        """Check if API is reachable"""
        try:
            result = await self.request("GET", "/health")
            return result.get("status") == "ok"
        except Exception:
            return False
'''

        if 'handler' in desc_lower or 'command' in desc_lower or 'processor' in desc_lower:
            return f'''"""
{description}

Part of {spec.name}
"""

import logging
from typing import Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class Command(Enum):
    """Available commands for this handler"""
    PROCESS = "process"
    VALIDATE = "validate"
    ANALYZE = "analyze"


class CommandHandler:
    """Command handler for {spec.name}"""

    def __init__(self):
        self._handlers: Dict[Command, Callable] = {{
            Command.PROCESS: self._handle_process,
            Command.VALIDATE: self._handle_validate,
            Command.ANALYZE: self._handle_analyze,
        }}

    def execute(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command by name"""
        try:
            cmd = Command(command)
            handler = self._handlers.get(cmd)
            if not handler:
                return {{"success": False, "error": f"Unknown command: {{command}}"}}
            return handler(params)
        except (ValueError, KeyError):
            return {{"success": False, "error": f"Invalid command: {{command}}"}}

    def _handle_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {{"success": True, "action": "processed"}}

    def _handle_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {{"success": True, "valid": True}}

    def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {{"success": True, "insights": []}}
'''

        # Default: generate a data processing scaffold
        return f'''"""
{description}

Part of {spec.name}
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30


class DataProcessor:
    """Main processor for {spec.name}"""

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()

    def process(self, data: Any, **options) -> Dict[str, Any]:
        """Process input data with given options"""
        try:
            result = self._transform(data, options)
            return {{"success": True, "result": result}}
        except Exception as e:
            logger.error(f"Processing failed: {{e}}")
            return {{"success": False, "error": str(e)}}

    def validate(self, data: Any) -> bool:
        """Validate input data"""
        return data is not None

    def _transform(self, data: Any, options: Dict) -> Any:
        """Apply transformations based on options"""
        return data
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
    
    MIN_COVERAGE_PERCENT = 80

    def deploy_skill(self, skill: GeneratedSkill, test_results: Optional[Dict] = None) -> bool:
        """
        Deploy a generated skill to production with fall-safe rollback.
        
        Args:
            skill: GeneratedSkill to deploy
            test_results: Optional dict with 'passed', 'total', 'coverage' keys
            
        Returns:
            True if deployment successful
        """
        try:
            if skill.status != 'generated':
                logger.warning(f"Cannot deploy skill {skill.skill_name} - status is {skill.status}")
                return False
            
            # 6.3: Check test coverage requirement
            if test_results:
                coverage = test_results.get('coverage', 0)
                if coverage < self.MIN_COVERAGE_PERCENT:
                    logger.warning(f"⚠️ Coverage {coverage}% < {self.MIN_COVERAGE_PERCENT}%, blocking deployment")
                    skill.errors.append(f"Coverage requirement not met: {coverage}% < {self.MIN_COVERAGE_PERCENT}%")
                    return False
                
                passed = test_results.get('passed', 0)
                total = test_results.get('total', 0)
                if total > 0 and (passed / total) < 0.8:
                    logger.warning(f"⚠️ Test pass rate {passed/total:.0%} < 80%, blocking deployment")
                    skill.errors.append(f"Test pass rate requirement not met")
                    return False
            
            # 6.4: Fall-safe - backup existing files before deployment
            backup_dir = None
            try:
                skill_dir = Path(skill.skill_path)
                if skill_dir.exists():
                    backup_parent = Path('.sandbox/backups')
                    backup_parent.mkdir(parents=True, exist_ok=True)
                    backup_dir = backup_parent / f"{skill.spec_id}_{int(datetime.now().timestamp())}"
                    backup_dir.mkdir(exist_ok=True)
                    # Backup existing files
                    for f in skill_dir.glob('*'):
                        if f.is_file():
                            import shutil
                            shutil.copy2(f, backup_dir / f.name)
                    logger.info(f"📦 Backed up existing skill to {backup_dir}")
            except Exception as be:
                logger.warning(f"⚠️ Backup failed, proceeding anyway: {be}")
                backup_dir = None
            
            # Update skill status
            skill.status = 'deployed'
            self.generated_skills[skill.spec_id] = skill
            
            # Hot-reload the skill into the plugin system
            try:
                skill_dir = Path(skill.skill_path)
                if skill_dir.exists() and skill.files_created:
                    from src.core.plugin_manager import get_plugin_manager
                    pm = get_plugin_manager()
                    if pm and hasattr(pm, 'reload_plugin'):
                        pm.reload_plugin(skill.spec_id)
                        logger.info(f"🔀 Hot-reloaded skill plugin: {skill.skill_name}")
            except Exception as re:
                # 6.4: Rollback on hot-load failure
                if backup_dir and backup_dir.exists():
                    logger.warning(f"⚠️ Hot-reload failed, rolling back from {backup_dir}")
                    try:
                        import shutil
                        for f in backup_dir.glob('*'):
                            if f.is_file():
                                target = skill_dir / f.name
                                shutil.copy2(f, target)
                        logger.info("✅ Rollback complete")
                    except Exception as rb:
                        logger.error(f"❌ Rollback failed: {rb}")
                logger.warning(f"⚠️ Hot-reload failed (skill available on restart): {re}")
            
            logger.info(f"🚀 Deployed skill: {skill.skill_name} at {skill.skill_path}")
            logger.info(f"   Files: {len(skill.files_created)}")
            
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
    """Get or create autonomous coder singleton (template-based fallback)"""
    global _coder_instance
    if _coder_instance is None:
        _coder_instance = AutonomousCoder()
    return _coder_instance


def get_best_coder(plugin_manager) -> Optional[Any]:
    """
    Get the best available autonomous coder.
    
    Priority:
    1. selfimprove plugin's AI-powered coder (full pipeline with validation + sandbox)
    2. Template-based fallback coder
    
    This provides the same pattern used in autonomous_brain.py for skill gap fixes.
    """
    if plugin_manager is None:
        return get_autonomous_coder()
    
    selfimprove = plugin_manager.get_plugin('selfimprove')
    if selfimprove and hasattr(selfimprove, '_generate_code_with_ai'):
        return selfimprove
    
    return get_autonomous_coder()


def generate_skill_with_fallback(plugin_manager, spec: SkillSpecification) -> GeneratedSkill:
    """
    Generate skill using best available coder (AI or template fallback).
    
    This is the unified entry point for autonomous code generation,
    matching the pattern in autonomous_brain.py for skill gap fixes.
    """
    coder = get_best_coder(plugin_manager)
    
    # If using selfimprove, call its AI method
    if hasattr(coder, '_generate_code_with_ai'):
        task = f"Create skill: {spec.name}\n\nDescription: {spec.description}\nEvidence: {spec.evidence}"
        code = coder._generate_code_with_ai(task)
        if code:
            # Save to draft_skills and return success
            from pathlib import Path
            skill_path = Path('sandbox/draft_skills') / spec.id
            skill_path.mkdir(parents=True, exist_ok=True)
            (skill_path / 'skill.py').write_text(code)
            return GeneratedSkill(
                spec_id=spec.id,
                skill_name=spec.name,
                files_created=[str(skill_path / 'skill.py')],
                skill_path=str(skill_path),
                generated_at=datetime.now(),
                status='generated',
                errors=[]
            )
    
    # Fallback to template-based coder
    return coder.generate_skill(spec)
