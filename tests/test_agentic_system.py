"""
Test suite for agentic enhancements
Run with: python -m pytest tests/test_agentic_system.py -v
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, MagicMock

# Test imports
from src.agentic.security_filter import SecurityFilter, CodeSecurityValidator, RiskLevel
from src.agentic.skill_generator import DynamicSkillGenerator, SecureSandbox
from src.agentic.enhanced_memory import EnhancedMemorySystem, Goal
from src.agentic.approval_dashboard import ApprovalDashboard, ApprovalStatus


class TestSecurityFilter:
    """Test security filtering and validation"""
    
    def test_code_security_validator_safe_code(self):
        """Test that safe code passes validation"""
        validator = CodeSecurityValidator()
        
        safe_code = """
import json
import time

def process_data(data):
    result = json.loads(data)
    return result
"""
        
        result = validator.validate_code(safe_code)
        assert result['safe'] == True
        assert len(result['issues']) == 0
    
    def test_code_security_validator_dangerous_code(self):
        """Test that dangerous code is detected"""
        validator = CodeSecurityValidator()
        
        dangerous_code = """
import os
os.system('rm -rf /')
"""
        
        result = validator.validate_code(dangerous_code)
        assert result['safe'] == False
        assert len(result['issues']) > 0
    
    def test_code_security_validator_eval_detection(self):
        """Test that eval is detected"""
        validator = CodeSecurityValidator()
        
        eval_code = """
user_input = "malicious code"
eval(user_input)
"""
        
        result = validator.validate_code(eval_code)
        assert result['safe'] == False
        assert any('eval' in str(issue) for issue in result['issues'])
    
    def test_security_filter_action_check(self):
        """Test action security checking"""
        security = SecurityFilter()
        
        # Safe action
        result = security.check_action_security('get_status', {})
        assert result['safe'] == True
        
        # High-risk action
        result = security.check_action_security('send_transaction', {
            'amount': '1.0',
            'to': '0x123...'
        })
        assert result['requires_approval'] == True
        assert result['risk_level'] in ['HIGH', 'CRITICAL']
    
    def test_security_filter_domain_allowlist(self):
        """Test domain allowlist checking"""
        security = SecurityFilter()
        
        # Allowed domain
        assert security._is_allowed_domain('https://moltbook.com/api')
        assert security._is_allowed_domain('https://base.org')
        
        # Disallowed domain
        assert not security._is_allowed_domain('https://malicious-site.com')


class TestSkillGenerator:
    """Test dynamic skill generation"""
    
    def test_secure_sandbox_safe_execution(self):
        """Test safe code execution in sandbox"""
        sandbox = SecureSandbox(timeout=5)
        
        safe_code = """
def add(a, b):
    return a + b

result = add(2, 3)
print(f"Result: {result}")
"""
        
        result = sandbox.execute_in_sandbox(safe_code)
        assert result['success'] == True
        assert 'Result: 5' in result['output']
    
    def test_secure_sandbox_timeout(self):
        """Test that infinite loops are caught"""
        sandbox = SecureSandbox(timeout=2)
        
        infinite_loop = """
while True:
    pass
"""
        
        result = sandbox.execute_in_sandbox(infinite_loop)
        assert result['success'] == False
        assert 'timeout' in result['error'].lower()
    
    def test_secure_sandbox_dangerous_code_blocked(self):
        """Test that dangerous code is blocked"""
        sandbox = SecureSandbox(timeout=5)
        
        dangerous_code = """
import os
os.system('echo "hacked"')
"""
        
        result = sandbox.execute_in_sandbox(dangerous_code)
        assert result['success'] == False
        assert 'security validation' in result['error'].lower()
    
    def test_skill_generator_initialization(self):
        """Test skill generator initialization"""
        mock_llm = Mock()
        generator = DynamicSkillGenerator(mock_llm, skills_dir='test_dynamic_skills')
        
        assert generator.llm == mock_llm
        assert generator.skills_dir.exists()
        
        # Cleanup
        import shutil
        shutil.rmtree('test_dynamic_skills', ignore_errors=True)


class TestEnhancedMemory:
    """Test enhanced memory system"""
    
    def test_memory_initialization(self):
        """Test memory system initialization"""
        memory = EnhancedMemorySystem(storage_dir='test_memory')
        
        assert memory.storage_dir.exists()
        assert memory.secure_storage is not None
        
        # Cleanup
        import shutil
        shutil.rmtree('test_memory', ignore_errors=True)
    
    def test_add_and_search_memory(self):
        """Test adding and searching memories"""
        memory = EnhancedMemorySystem(storage_dir='test_memory')
        
        # Add memory
        mem_id = memory.add_memory(
            "AlleyBot successfully posted on Moltbook",
            memory_type='interaction',
            metadata={'platform': 'moltbook'}
        )
        
        assert mem_id is not None
        
        # Search memory (will use fallback if vector DB not available)
        results = memory.search_memories("Moltbook post", k=5)
        
        # Cleanup
        import shutil
        shutil.rmtree('test_memory', ignore_errors=True)
    
    def test_hierarchical_goals(self):
        """Test hierarchical goal tracking"""
        memory = EnhancedMemorySystem(storage_dir='test_memory')
        
        # Add parent goal
        parent_id = memory.add_goal(
            "Build on-chain reputation",
            goal_type='long_term',
            priority=3
        )
        
        # Add child goal
        child_id = memory.add_goal(
            "Reach 1000 karma",
            goal_type='short_term',
            parent_goal_id=parent_id,
            priority=2
        )
        
        # Check hierarchy
        hierarchy = memory.get_goal_hierarchy(parent_id)
        assert hierarchy['id'] == parent_id
        assert len(hierarchy['sub_goals']) == 1
        
        # Update progress
        memory.update_goal_progress(child_id, 0.5)
        assert memory.goals[child_id].progress == 0.5
        
        # Complete goal
        memory.complete_goal(child_id)
        assert memory.goals[child_id].status == 'completed'
        
        # Cleanup
        import shutil
        shutil.rmtree('test_memory', ignore_errors=True)
    
    def test_sensitive_data_encryption(self):
        """Test encrypted storage of sensitive data"""
        memory = EnhancedMemorySystem(storage_dir='test_memory')
        
        # Store sensitive data
        memory.store_sensitive('api_key', 'secret_key_12345')
        
        # Retrieve sensitive data
        retrieved = memory.get_sensitive('api_key')
        assert retrieved == 'secret_key_12345'
        
        # Cleanup
        import shutil
        shutil.rmtree('test_memory', ignore_errors=True)


class TestApprovalDashboard:
    """Test approval system"""
    
    def test_approval_dashboard_initialization(self):
        """Test approval dashboard initialization"""
        dashboard = ApprovalDashboard(timeout_seconds=60)
        
        assert dashboard.timeout_seconds == 60
        assert len(dashboard.pending_requests) == 0
    
    def test_auto_approve_pattern(self):
        """Test auto-approve patterns"""
        dashboard = ApprovalDashboard()
        
        # Add auto-approve pattern
        dashboard.add_auto_approve_pattern({
            'action': 'get_status',
            'params': {}
        })
        
        # Request approval for matching action
        approved = dashboard.request_approval(
            'get_status',
            {},
            {'risk_level': 'LOW', 'issues': []}
        )
        
        assert approved == True
    
    def test_auto_deny_pattern(self):
        """Test auto-deny patterns"""
        dashboard = ApprovalDashboard()
        
        # Add auto-deny pattern
        dashboard.add_auto_deny_pattern({
            'action': 'delete_all',
            'params': {}
        })
        
        # Request approval for matching action
        approved = dashboard.request_approval(
            'delete_all',
            {},
            {'risk_level': 'CRITICAL', 'issues': []}
        )
        
        assert approved == False
    
    def test_approval_stats(self):
        """Test approval statistics"""
        dashboard = ApprovalDashboard()
        
        # Add some test patterns
        dashboard.add_auto_approve_pattern({'action': 'safe_action'})
        dashboard.add_auto_deny_pattern({'action': 'dangerous_action'})
        
        # Get stats
        stats = dashboard.get_approval_stats()
        
        assert 'total_requests' in stats
        assert 'approval_rate' in stats
        assert stats['auto_approve_patterns'] == 1
        assert stats['auto_deny_patterns'] == 1


class TestIntegration:
    """Integration tests for the full system"""
    
    def test_security_and_approval_integration(self):
        """Test security filter with approval dashboard"""
        dashboard = ApprovalDashboard()
        security = SecurityFilter(approval_callback=dashboard.request_approval)
        
        # Add auto-approve for testing
        dashboard.add_auto_approve_pattern({
            'action': 'test_action'
        })
        
        # Execute action
        def mock_executor(action, params):
            return {'success': True, 'result': 'executed'}
        
        result = security.execute_with_security(
            'test_action',
            {'param': 'value'},
            mock_executor
        )
        
        assert result['success'] == True
    
    def test_memory_and_goals_integration(self):
        """Test memory with goal tracking"""
        memory = EnhancedMemorySystem(storage_dir='test_memory_integration')
        
        # Create goal
        goal_id = memory.add_goal("Test goal", goal_type='short_term')
        
        # Add memory about goal
        mem_id = memory.add_memory(
            f"Working on goal: {goal_id}",
            memory_type='interaction',
            metadata={'goal_id': goal_id}
        )
        
        # Update goal progress
        memory.update_goal_progress(goal_id, 1.0)
        
        # Check goal completed
        assert memory.goals[goal_id].status == 'completed'
        
        # Cleanup
        import shutil
        shutil.rmtree('test_memory_integration', ignore_errors=True)


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
