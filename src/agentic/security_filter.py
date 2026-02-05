"""
Enhanced Security Filter with Runtime Checks
Prevents exploits and integrates with approval dashboard
"""
import re
import ast
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for actions"""
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SecurityFilter:
    """
    Enhanced security filter with:
    - Runtime exploit detection
    - Action risk assessment
    - Approval integration
    - Audit logging
    """
    
    # Dangerous patterns with risk levels
    DANGEROUS_PATTERNS = {
        # Critical risk
        r'os\.system': RiskLevel.CRITICAL,
        r'subprocess\.(?!run\(.*timeout)': RiskLevel.CRITICAL,
        r'eval\(': RiskLevel.CRITICAL,
        r'exec\(': RiskLevel.CRITICAL,
        r'__import__\(': RiskLevel.CRITICAL,
        r'compile\(': RiskLevel.CRITICAL,
        
        # High risk
        r'open\(.*[\'"]w': RiskLevel.HIGH,
        r'pickle\.': RiskLevel.HIGH,
        r'shelve\.': RiskLevel.HIGH,
        r'marshal\.': RiskLevel.HIGH,
        r'socket\.': RiskLevel.HIGH,
        r'rm\s+-rf': RiskLevel.HIGH,
        
        # Medium risk
        r'requests\.(?!get|post)': RiskLevel.MEDIUM,
        r'urllib\.request': RiskLevel.MEDIUM,
        r'globals\(\)': RiskLevel.MEDIUM,
        r'locals\(\)': RiskLevel.MEDIUM,
        r'vars\(\)': RiskLevel.MEDIUM,
        r'dir\(\)': RiskLevel.MEDIUM,
        
        # Low risk
        r'del\s+': RiskLevel.LOW,
    }
    
    # High-risk actions that always require approval
    HIGH_RISK_ACTIONS = [
        'create_post',
        'delete_post',
        'send_transaction',
        'transfer_funds',
        'execute_code',
        'modify_config',
        'update_credentials'
    ]
    
    # Allowlisted domains for network requests
    ALLOWED_DOMAINS = [
        'moltbook.com',
        'moltx.io',
        '4claw.org',
        'base.org',
        'etherscan.io',
        '8004.org',
        'api.deepseek.com',
        'api.x.ai'
    ]
    
    def __init__(self, approval_callback: Optional[Callable] = None):
        self.approval_callback = approval_callback
        self.audit_log = []
        self.blocked_actions = []
        
    def check_code_security(self, code: str) -> Dict[str, Any]:
        """
        Check code for security issues
        
        Returns:
            Dict with risk_level, issues, and safe flag
        """
        issues = []
        max_risk = RiskLevel.SAFE
        
        # Check for dangerous patterns
        for pattern, risk_level in self.DANGEROUS_PATTERNS.items():
            matches = re.findall(pattern, code)
            if matches:
                issues.append({
                    'pattern': pattern,
                    'risk_level': risk_level.name,
                    'matches': matches
                })
                
                if risk_level.value > max_risk.value:
                    max_risk = risk_level
        
        # Parse AST for deeper analysis
        try:
            tree = ast.parse(code)
            ast_issues = self._analyze_ast(tree)
            issues.extend(ast_issues)
            
            # Update max risk from AST analysis
            for issue in ast_issues:
                issue_risk = RiskLevel[issue['risk_level']]
                if issue_risk.value > max_risk.value:
                    max_risk = issue_risk
                    
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'risk_level': RiskLevel.HIGH.name,
                'error': str(e)
            })
            max_risk = RiskLevel.HIGH
        
        return {
            'safe': max_risk.value <= RiskLevel.LOW.value,
            'risk_level': max_risk.name,
            'issues': issues,
            'requires_approval': max_risk.value >= RiskLevel.MEDIUM.value
        }
    
    def _analyze_ast(self, tree: ast.AST) -> List[Dict]:
        """Analyze AST for security issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Check dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    if func_name in ['eval', 'exec', 'compile']:
                        issues.append({
                            'type': 'dangerous_function',
                            'function': func_name,
                            'risk_level': RiskLevel.CRITICAL.name
                        })
                    
                    elif func_name == 'open':
                        # Check if opening file in write mode
                        if len(node.args) > 1:
                            mode_arg = node.args[1]
                            if isinstance(mode_arg, ast.Constant):
                                if 'w' in str(mode_arg.value):
                                    issues.append({
                                        'type': 'file_write',
                                        'risk_level': RiskLevel.HIGH.name
                                    })
            
            # Check imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['os', 'subprocess', 'socket']:
                        issues.append({
                            'type': 'dangerous_import',
                            'module': alias.name,
                            'risk_level': RiskLevel.HIGH.name
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in ['os', 'subprocess', 'socket']:
                    issues.append({
                        'type': 'dangerous_import',
                        'module': node.module,
                        'risk_level': RiskLevel.HIGH.name
                    })
        
        return issues
    
    def check_action_security(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if an action is safe to execute
        
        Args:
            action: Action name
            params: Action parameters
            
        Returns:
            Dict with safe flag, risk_level, and approval_required
        """
        risk_level = RiskLevel.SAFE
        issues = []
        
        # Check if action is high-risk
        if action in self.HIGH_RISK_ACTIONS:
            risk_level = RiskLevel.HIGH
            issues.append({
                'type': 'high_risk_action',
                'action': action
            })
        
        # Check network requests
        if action in ['api_call', 'http_request', 'fetch_url']:
            url = params.get('url', '')
            if not self._is_allowed_domain(url):
                risk_level = RiskLevel.MEDIUM
                issues.append({
                    'type': 'disallowed_domain',
                    'url': url
                })
        
        # Check transaction actions
        if 'transaction' in action.lower() or 'transfer' in action.lower():
            risk_level = RiskLevel.HIGH
            issues.append({
                'type': 'financial_action',
                'action': action
            })
        
        # Check code execution
        if 'execute' in action.lower() or 'run' in action.lower():
            if 'code' in params:
                code_check = self.check_code_security(params['code'])
                if not code_check['safe']:
                    risk_level = RiskLevel.CRITICAL
                    issues.extend(code_check['issues'])
        
        return {
            'safe': risk_level.value <= RiskLevel.LOW.value,
            'risk_level': risk_level.name,
            'requires_approval': risk_level.value >= RiskLevel.MEDIUM.value,
            'issues': issues
        }
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is allowlisted"""
        for domain in self.ALLOWED_DOMAINS:
            if domain in url:
                return True
        return False
    
    def execute_with_security(self, action: str, params: Dict[str, Any],
                             executor: Callable) -> Dict[str, Any]:
        """
        Execute action with security checks
        
        Args:
            action: Action to execute
            params: Action parameters
            executor: Function to execute the action
            
        Returns:
            Execution result
        """
        # Check security
        security_check = self.check_action_security(action, params)
        
        # Log the attempt
        self._log_action_attempt(action, params, security_check)
        
        # Block if unsafe
        if not security_check['safe'] and security_check['risk_level'] == 'CRITICAL':
            result = {
                'success': False,
                'error': 'Action blocked by security filter',
                'risk_level': security_check['risk_level'],
                'issues': security_check['issues']
            }
            self.blocked_actions.append({
                'action': action,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'reason': 'critical_risk'
            })
            return result
        
        # Request approval if needed
        if security_check['requires_approval']:
            if not self._request_approval(action, params, security_check):
                result = {
                    'success': False,
                    'error': 'Action denied by approval system',
                    'risk_level': security_check['risk_level']
                }
                self.blocked_actions.append({
                    'action': action,
                    'params': params,
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'approval_denied'
                })
                return result
        
        # Execute action
        try:
            result = executor(action, params)
            
            # Handle string results
            if isinstance(result, str):
                result_dict = {
                    'success': True,
                    'result': result,
                    'security_check': security_check
                }
            else:
                # Assume result is already a dict
                result['security_check'] = security_check
                result_dict = result
            
            # Log successful execution
            self._log_action_execution(action, params, True, result_dict)
            
            return result_dict
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            
            # Log failed execution
            self._log_action_execution(action, params, False, result)
            
            return result
    
    def _request_approval(self, action: str, params: Dict[str, Any],
                         security_check: Dict[str, Any]) -> bool:
        """Request approval for action"""
        if self.approval_callback is None:
            # No approval system configured - deny by default
            return False
        
        try:
            approved = self.approval_callback(action, params, security_check)
            return approved
        except Exception as e:
            print(f"⚠️  Approval callback error: {e}")
            return False
    
    def _log_action_attempt(self, action: str, params: Dict[str, Any],
                           security_check: Dict[str, Any]):
        """Log action attempt"""
        self.audit_log.append({
            'type': 'attempt',
            'action': action,
            'params': params,
            'security_check': security_check,
            'timestamp': datetime.now().isoformat()
        })
    
    def _log_action_execution(self, action: str, params: Dict[str, Any],
                             success: bool, result: Dict[str, Any]):
        """Log action execution"""
        self.audit_log.append({
            'type': 'execution',
            'action': action,
            'params': params,
            'success': success,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        return self.audit_log[-limit:]
    
    def get_blocked_actions(self, limit: int = 50) -> List[Dict]:
        """Get recently blocked actions"""
        return self.blocked_actions[-limit:]
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_attempts = len([log for log in self.audit_log if log['type'] == 'attempt'])
        total_executions = len([log for log in self.audit_log if log['type'] == 'execution'])
        successful_executions = len([
            log for log in self.audit_log 
            if log['type'] == 'execution' and log['success']
        ])
        
        return {
            'total_attempts': total_attempts,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'blocked_actions': len(self.blocked_actions),
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0
        }
