"""
AlleyBot Skill Tester - Phase 4: Self-Extension Pipeline

Validates generated skills before deployment.
Runs smoke tests, security checks, and integration tests.

Part of AGI Core - Phase 4: Self-Extension
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import ast

from src.agentic.autonomous_coder import GeneratedSkill

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    passed: bool
    duration_seconds: float
    error_message: Optional[str] = None
    output: Optional[str] = None


@dataclass
class SkillValidationReport:
    """Complete validation report for a skill"""
    skill_id: str
    skill_name: str
    generated_at: datetime
    test_results: List[TestResult] = field(default_factory=list)
    security_passed: bool = False
    syntax_valid: bool = False
    can_import: bool = False
    overall_passed: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        """Calculate test pass rate"""
        if not self.test_results:
            return 0.0
        passed = sum(1 for r in self.test_results if r.passed)
        return passed / len(self.test_results)
    
    def to_dict(self) -> Dict:
        return {
            'skill_id': self.skill_id,
            'skill_name': self.skill_name,
            'generated_at': self.generated_at.isoformat(),
            'overall_passed': self.overall_passed,
            'security_passed': self.security_passed,
            'syntax_valid': self.syntax_valid,
            'can_import': self.can_import,
            'pass_rate': self.pass_rate,
            'test_count': len(self.test_results),
            'errors': self.errors,
            'warnings': self.warnings,
        }


class SkillTester:
    """
    Tests and validates generated skills before deployment.
    
    Usage:
        tester = SkillTester()
        
        # Validate skill
        report = tester.validate_skill(skill)
        
        if report.overall_passed:
            deploy_skill(skill)
        else:
            fix_issues(report.errors)
    """
    
    def __init__(self):
        self.security_validator = CodeSecurityValidator()
    
    def validate_skill(self, skill: GeneratedSkill) -> SkillValidationReport:
        """
        Run full validation suite on a generated skill.
        
        Args:
            skill: GeneratedSkill to validate
            
        Returns:
            SkillValidationReport with all test results
        """
        report = SkillValidationReport(
            skill_id=skill.spec_id,
            skill_name=skill.skill_name,
            generated_at=datetime.now()
        )
        
        logger.info(f"🧪 Testing skill: {skill.skill_name}")
        
        # 1. Syntax validation
        self._check_syntax(skill, report)
        
        # 2. Security scan
        self._security_scan(skill, report)
        
        # 3. Import test
        self._test_import(skill, report)
        
        # 4. Run unit tests
        self._run_tests(skill, report)
        
        # 5. Integration smoke test
        self._smoke_test(skill, report)
        
        # Calculate overall result
        critical_tests = [
            report.syntax_valid,
            report.security_passed,
            report.can_import
        ]
        report.overall_passed = all(critical_tests) and report.pass_rate >= 0.5
        
        logger.info(f"✅ Validation complete: {'PASSED' if report.overall_passed else 'FAILED'}")
        return report
    
    def _check_syntax(self, skill: GeneratedSkill, report: SkillValidationReport):
        """Validate Python syntax of all files"""
        for file_path in skill.files_created:
            if not file_path.endswith('.py'):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    source = f.read()
                
                # Parse AST
                ast.parse(source)
                
            except SyntaxError as e:
                report.syntax_valid = False
                report.errors.append(f"Syntax error in {file_path}: {e}")
                return
            except Exception as e:
                report.errors.append(f"Error reading {file_path}: {e}")
                return
        
        report.syntax_valid = True
        logger.info("✅ Syntax validation passed")
    
    def _security_scan(self, skill: GeneratedSkill, report: SkillValidationReport):
        """Scan for security issues"""
        all_safe = True
        
        for file_path in skill.files_created:
            if not file_path.endswith('.py'):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                result = self.security_validator.validate_code(code)
                
                if not result.get('safe', True):
                    all_safe = False
                    report.errors.extend(result.get('issues', []))
                
                if result.get('warnings'):
                    report.warnings.extend(result.get('warnings'))
                    
            except Exception as e:
                report.errors.append(f"Security scan error for {file_path}: {e}")
                all_safe = False
        
        report.security_passed = all_safe
        logger.info(f"{'✅' if all_safe else '⚠️'} Security scan: {'passed' if all_safe else 'issues found'}")
    
    def _test_import(self, skill: GeneratedSkill, report: SkillValidationReport):
        """Test that skill can be imported"""
        try:
            skill_path = Path(skill.skill_path)
            
            # Add to path temporarily
            if str(skill_path.parent) not in sys.path:
                sys.path.insert(0, str(skill_path.parent))
            
            # Try import
            package_name = skill_path.name.replace('-', '_')
            __import__(package_name)
            
            report.can_import = True
            logger.info("✅ Import test passed")
            
        except Exception as e:
            report.can_import = False
            report.errors.append(f"Import failed: {e}")
            logger.warning(f"⚠️ Import test failed: {e}")
    
    def _run_tests(self, skill: GeneratedSkill, report: SkillValidationReport):
        """Run pytest on generated tests"""
        test_file = Path(skill.skill_path) / 'test_skill.py'
        
        if not test_file.exists():
            report.warnings.append("No test file found")
            return
        
        try:
            # Run pytest
            result = subprocess.run(
                ['python', '-m', 'pytest', str(test_file), '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            test_result = TestResult(
                test_name='unit_tests',
                passed=result.returncode == 0,
                duration_seconds=0.0,  # Could parse from output
                output=result.stdout,
                error_message=result.stderr if result.returncode != 0 else None
            )
            report.test_results.append(test_result)
            
            logger.info(f"{'✅' if test_result.passed else '❌'} Unit tests: {'passed' if test_result.passed else 'failed'}")
            
        except subprocess.TimeoutExpired:
            report.errors.append("Tests timed out")
            report.test_results.append(TestResult(
                test_name='unit_tests',
                passed=False,
                duration_seconds=30.0,
                error_message="Timeout"
            ))
        except Exception as e:
            report.errors.append(f"Test execution error: {e}")
            report.test_results.append(TestResult(
                test_name='unit_tests',
                passed=False,
                duration_seconds=0.0,
                error_message=str(e)
            ))
    
    def _smoke_test(self, skill: GeneratedSkill, report: SkillValidationReport):
        """Run smoke test - basic functionality check"""
        try:
            # Try to instantiate and call basic methods
            skill_path = Path(skill.skill_path)
            package_name = skill_path.name.replace('-', '_')
            
            # Dynamic import
            module = __import__(package_name, fromlist=['SkillClient'])
            client_class = getattr(module, 'SkillClient')
            
            # Instantiate
            client = client_class()
            
            # Try initialize
            init_result = client.initialize()
            
            # Try process
            process_result = client.process()
            
            test_result = TestResult(
                test_name='smoke_test',
                passed=init_result and isinstance(process_result, dict),
                duration_seconds=0.0
            )
            report.test_results.append(test_result)
            
            logger.info(f"{'✅' if test_result.passed else '❌'} Smoke test: {'passed' if test_result.passed else 'failed'}")
            
        except Exception as e:
            report.test_results.append(TestResult(
                test_name='smoke_test',
                passed=False,
                duration_seconds=0.0,
                error_message=str(e)
            ))
            logger.warning(f"⚠️ Smoke test failed: {e}")


class CodeSecurityValidator:
    """Validate generated code for security issues"""
    
    DANGEROUS_PATTERNS = [
        (r'os\.system', 'System command execution'),
        (r'subprocess\.call', 'Subprocess call'),
        (r'subprocess\.Popen', 'Subprocess Popen'),
        (r'eval\(', 'Eval usage'),
        (r'exec\(', 'Exec usage'),
        (r'__import__\(', 'Dynamic import'),
        (r'compile\(', 'Code compilation'),
        (r'socket\.', 'Socket usage'),
        (r'urllib\.request', 'URL fetching'),
        (r'pickle\.', 'Pickle usage'),
        (r'marshal\.', 'Marshal usage'),
        (r'globals\(\)', 'Globals access'),
        (r'rm\s+-rf', 'Dangerous rm command'),
    ]
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """Scan code for security issues"""
        issues = []
        warnings = []
        
        for pattern, description in self.DANGEROUS_PATTERNS:
            import re
            if re.search(pattern, code):
                issues.append(f"Security: {description} detected")
        
        # Check for hardcoded secrets
        if re.search(r'(api_key|apikey|password|secret|token)\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
            warnings.append("Potential hardcoded secret detected")
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }


# Singleton
_tester_instance: Optional[SkillTester] = None


def get_skill_tester() -> SkillTester:
    """Get or create skill tester singleton"""
    global _tester_instance
    if _tester_instance is None:
        _tester_instance = SkillTester()
    return _tester_instance
