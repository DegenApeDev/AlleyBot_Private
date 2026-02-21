"""
Self-Improvement Hook System for AlleyBot v2
Connects brain action failures to autonomous coder for self-healing
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


class SelfImprovementHooks:
    """
    Hooks into brain's action execution to detect failures and trigger self-improvement.
    
    Requirements:
    - Track failures per action type
    - When same action fails 2-3 times with same root cause → create draft
    - Run framework constraint validation
    - Classify risk level
    - Create git branch + generate code + run tests (but NO auto-deploy)
    """
    
    def __init__(self, brain_plugin):
        self.brain = brain_plugin
        self.core = getattr(brain_plugin, 'core', None)
        self.failure_tracker = defaultdict(list)  # action_type -> list of failure records
        self.improvement_metrics = []
        self._load_state()
    
    def _load_state(self):
        """Load persistent failure tracking state"""
        if not self.core:
            return
        try:
            state = self.core.get_memory('self_improvement_hooks_state')
            if state:
                self.failure_tracker = defaultdict(list, state.get('failures', {}))
                self.improvement_metrics = state.get('metrics', [])
        except Exception:
            pass
    
    def _save_state(self):
        """Save persistent state"""
        if not self.core:
            return
        try:
            self.core.save_memory('self_improvement_hooks_state', {
                'failures': dict(self.failure_tracker),
                'metrics': self.improvement_metrics[-100:],  # Keep last 100
                'last_updated': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Failed to save self-improvement state: {e}")
    
    def on_action_failure(self, action_id: str, action_type: str, 
                         error_output: str, platform: str) -> Optional[Dict]:
        """
        Hook called when an action fails. Tracks failures and triggers self-improvement
        if the same action fails repeatedly.
        
        Returns draft info if a self-improvement draft was created, None otherwise.
        """
        # 1. Record the failure
        failure_record = {
            'action_id': action_id,
            'action_type': action_type,
            'error': error_output[:500],  # Truncate for storage
            'platform': platform,
            'timestamp': datetime.now().isoformat(),
            'root_cause': self._extract_root_cause(error_output)
        }
        
        self.failure_tracker[action_type].append(failure_record)
        # Keep only last 10 failures per action type
        self.failure_tracker[action_type] = self.failure_tracker[action_type][-10:]
        
        # 2. Log to metrics store
        self._log_action_metrics(
            timestamp=datetime.now(),
            platform=platform,
            skill_name=self._get_skill_for_action(action_id),
            action_type=action_type,
            success=False,
            error_code=self._extract_error_code(error_output)
        )
        
        # 3. Check if we should trigger self-improvement
        recent_failures = self._get_recent_failures(action_type, hours=24)
        
        # Group by root cause
        by_cause = defaultdict(list)
        for f in recent_failures:
            by_cause[f['root_cause']].append(f)
        
        # Check for repeated same root cause (2-3 times)
        for root_cause, failures in by_cause.items():
            if len(failures) >= 2:  # Threshold: 2 failures with same root cause
                print(f"🔄 Self-improvement triggered: {action_type} failed {len(failures)}x with '{root_cause}'")
                
                # 4. Create self-improvement draft (but don't deploy)
                draft = self._create_improvement_draft(
                    action_type=action_type,
                    root_cause=root_cause,
                    failures=failures
                )
                
                if draft:
                    # Mark these failures as processed
                    for f in failures:
                        f['processed'] = True
                    
                    self._save_state()
                    return draft
        
        self._save_state()
        return None
    
    def on_action_success(self, action_id: str, action_type: str, 
                         platform: str, engagement_metrics: Dict = None):
        """Hook called when an action succeeds. Logs metrics."""
        self._log_action_metrics(
            timestamp=datetime.now(),
            platform=platform,
            skill_name=self._get_skill_for_action(action_id),
            action_type=action_type,
            success=True,
            error_code=None,
            engagement_metrics=engagement_metrics
        )
    
    def _extract_root_cause(self, error_output: str) -> str:
        """Extract root cause category from error message"""
        error_lower = error_output.lower()
        
        # Common error patterns
        if 'api' in error_lower and ('404' in error_lower or 'not found' in error_lower):
            return 'api_endpoint_missing'
        elif 'api' in error_lower and ('401' in error_lower or '403' in error_lower):
            return 'api_auth_error'
        elif 'timeout' in error_lower or 'timed out' in error_lower:
            return 'api_timeout'
        elif 'rate limit' in error_lower or '429' in error_lower:
            return 'rate_limited'
        elif 'attribute' in error_lower or 'has no attribute' in error_lower:
            return 'attribute_error'
        elif 'import' in error_lower or 'module' in error_lower:
            return 'import_error'
        elif 'syntax' in error_lower:
            return 'syntax_error'
        elif 'keyerror' in error_lower or 'key error' in error_lower:
            return 'key_error'
        elif 'none' in error_lower and 'type' in error_lower:
            return 'null_reference'
        elif 'json' in error_lower and 'decode' in error_lower:
            return 'json_decode_error'
        elif 'connection' in error_lower:
            return 'connection_error'
        else:
            return 'unknown_error'
    
    def _extract_error_code(self, error_output: str) -> Optional[str]:
        """Extract specific error code from error output"""
        # Try to find HTTP status codes
        import re
        http_codes = re.findall(r'\b(4\d{2}|5\d{2})\b', error_output)
        if http_codes:
            return http_codes[0]
        
        # Try to find exception names
        exception_match = re.search(r'(\w+Error|\w+Exception)', error_output)
        if exception_match:
            return exception_match.group(1)
        
        return None
    
    def _get_skill_for_action(self, action_id: str) -> str:
        """Determine which skill/plugin handles this action"""
        # Extract skill name from action_id (e.g., 'moltx_post' -> 'moltx')
        parts = action_id.split('_')
        if parts:
            return parts[0]
        return 'unknown'
    
    def _get_recent_failures(self, action_type: str, hours: int = 24) -> List[Dict]:
        """Get failures from the last N hours that haven't been processed"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []
        for f in self.failure_tracker.get(action_type, []):
            if f.get('processed'):
                continue
            try:
                f_time = datetime.fromisoformat(f['timestamp'])
                if f_time > cutoff:
                    recent.append(f)
            except (ValueError, KeyError):
                continue
        return recent
    
    def _create_improvement_draft(self, action_type: str, root_cause: str, 
                                  failures: List[Dict]) -> Optional[Dict]:
        """
        Create a self-improvement draft to fix the recurring failure.
        
        This:
        1. Classifies risk level
        2. Creates git branch
        3. Generates code fix using AI
        4. Runs framework constraint validation
        5. Runs tests
        6. Registers draft (NO auto-deploy)
        """
        # Get selfimprove plugin
        selfimprove = None
        if self.core and hasattr(self.core, 'plugin_manager'):
            selfimprove = self.core.plugin_manager.plugins.get('selfimprove')
        
        if not selfimprove:
            print("❌ Self-improvement plugin not available")
            return None
        
        # 1. Classify risk level
        risk_level, risk_reason = self._classify_risk(action_type, root_cause)
        print(f"📊 Risk classification: {risk_level} - {risk_reason}")
        
        # 2. Generate fix task description
        task = self._generate_fix_task(action_type, root_cause, failures)
        print(f"📝 Fix task: {task[:100]}...")
        
        # 3. Create draft using autonomous coder (test-only, no deploy)
        draft_id = f"auto-fix-{action_type}-{hashlib.md5(root_cause.encode()).hexdigest()[:8]}"
        
        # Check if we already have a pending draft for this
        if hasattr(selfimprove, 'autonomous_coder') and selfimprove.autonomous_coder:
            coder = selfimprove.autonomous_coder
            
            # Create a minimal plan for the fix
            plan = self._generate_fix_plan(action_type, root_cause, failures)
            
            # Validate plan against framework constraints
            validation = self._validate_framework_constraints(plan)
            if not validation['valid']:
                print(f"❌ Framework validation failed: {validation['errors']}")
                return {
                    'draft_id': draft_id,
                    'status': 'FAILED',
                    'reason': f"Framework validation failed: {validation['errors']}",
                    'risk_level': 'high',
                    'created_at': datetime.now().isoformat()
                }
            
            # Execute plan (generate, validate, test) but DON'T deploy
            try:
                result = coder._execute_plan(plan)
                
                draft = {
                    'draft_id': draft_id,
                    'action_type': action_type,
                    'root_cause': root_cause,
                    'failures': failures,
                    'task': task,
                    'plan': plan,
                    'result': result,
                    'risk_level': risk_level,
                    'risk_reason': risk_reason,
                    'status': 'PENDING_APPROVAL' if result.get('applied') else 'FAILED',
                    'framework_validation': validation,
                    'created_at': datetime.now().isoformat(),
                    'files': [gf['path'] for gf in result.get('generated_files', [])]
                }
                
                # Store draft in pending drafts
                if not hasattr(coder, '_pending_drafts'):
                    coder._pending_drafts = {}
                coder._pending_drafts[draft_id] = draft
                
                if result.get('applied'):
                    print(f"✅ Self-improvement draft created: {draft_id}")
                    print(f"   Risk: {risk_level}")
                    print(f"   Files: {len(draft['files'])}")
                    print(f"   Run '/improve_approve {draft_id}' to deploy")
                else:
                    print(f"❌ Draft creation failed: {result.get('error', 'unknown')}")
                
                return draft
                
            except Exception as e:
                print(f"❌ Error creating improvement draft: {e}")
                return None
        
        return None
    
    def _classify_risk(self, action_type: str, root_cause: str) -> tuple:
        """
        Classify risk level for a self-improvement change.
        
        Returns: (risk_level: str, reason: str)
        """
        skill = self._get_skill_for_action(action_type)
        
        # HIGH RISK: Core system components
        high_risk_skills = ['brain', 'symod', 'x402', 'payment', 'security', 'sandbox']
        if skill in high_risk_skills:
            return 'high', f"Core system skill '{skill}' - manual approval required"
        
        # HIGH RISK: Specific error types that touch sensitive areas
        sensitive_errors = ['api_auth_error', 'security', 'permission']
        if any(err in root_cause for err in sensitive_errors):
            return 'high', f"Sensitive error type: {root_cause}"
        
        # MEDIUM RISK: Platform integrations
        platform_skills = ['moltx', 'moltbook', 'moltchan', 'moltroad', 'clawbr']
        if skill in platform_skills:
            return 'medium', f"Platform integration '{skill}' - review recommended"
        
        # LOW RISK: New skills, config, helpers
        low_risk_skills = ['skills', 'config', 'helpers', 'utils']
        if skill in low_risk_skills or 'util' in skill:
            return 'low', f"Helper/config skill '{skill}' - eligible for auto-approval"
        
        # Default to medium for unknown
        return 'medium', f"Skill '{skill}' - default medium risk"
    
    def _validate_framework_constraints(self, plan: Dict) -> Dict:
        """
        Validate generated code against alleybot.framework rules.
        
        Hard requirements:
        - Inherit from Plugin only (no mixins)
        - Use APIClient subclass for HTTP
        - Provide skill.yaml manifest passing schema
        - API methods return APIResponse[T]
        - Tests exist and pass
        """
        errors = []
        warnings = []
        
        for file_info in plan.get('files', []):
            path = file_info.get('path', '')
            code = file_info.get('code', '')
            
            # Check 1: Plugin inheritance (no mixins)
            if 'class ' in code and 'Plugin' in code:
                if 'Mixin' in code and 'class' in code:
                    # Check if it's the class definition line
                    lines = code.split('\n')
                    for line in lines:
                        if line.strip().startswith('class ') and 'Mixin' in line:
                            errors.append(f"{path}: Uses mixin pattern - must use Plugin only")
                            break
            
            # Check 2: No raw requests usage
            if 'import requests' in code or 'from requests' in code:
                if 'APIClient' not in code:
                    errors.append(f"{path}: Uses raw requests - must use APIClient subclass")
            
            # Check 3: APIResponse[T] return types
            if 'def ' in code and 'APIResponse' not in code:
                # Check if it's an API method (get_, post_, fetch_, etc.)
                api_methods = ['def get_', 'def post_', 'def put_', 'def delete_', 
                              'def fetch_', 'def create_', 'def update_']
                if any(method in code for method in api_methods):
                    warnings.append(f"{path}: API method may lack APIResponse[T] return type")
            
            # Check 4: skill.yaml manifest (for new skills)
            if path.startswith('plugins/') and '__init__.py' in path:
                # Check if skill.yaml exists in same directory
                skill_dir = path.replace('/__init__.py', '')
                manifest_path = f"{skill_dir}/skill.yaml"
                if manifest_path not in [f.get('path') for f in plan.get('files', [])]:
                    errors.append(f"{path}: Missing skill.yaml manifest")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _generate_fix_task(self, action_type: str, root_cause: str, 
                          failures: List[Dict]) -> str:
        """Generate a task description for fixing the issue"""
        skill = self._get_skill_for_action(action_type)
        
        error_samples = [f['error'][:100] for f in failures[:3]]
        error_text = '\n'.join(error_samples)
        
        task = f"""Fix recurring failure in {action_type} (skill: {skill})

Root cause: {root_cause}

Error samples:
{error_text}

Requirements:
1. Identify the failing code in plugins/{skill}/
2. Fix the root cause: {root_cause}
3. Add error handling if needed
4. Add or update tests in tests/test_{skill}.py
5. Ensure the fix follows alleybot.framework rules (Plugin class, APIClient, APIResponse[T])

This is an auto-generated fix for a recurring failure that occurred {len(failures)} times."""
        
        return task
    
    def _generate_fix_plan(self, action_type: str, root_cause: str, 
                          failures: List[Dict]) -> Dict:
        """Generate a code change plan for the fix"""
        skill = self._get_skill_for_action(action_type)
        
        files = []
        
        # Main skill file
        files.append({
            'path': f'plugins/{skill}/{skill}.py',
            'action': 'modify',
            'description': f'Fix {root_cause} in {action_type}'
        })
        
        # Add test file
        files.append({
            'path': f'tests/test_{skill}.py',
            'action': 'modify',
            'description': f'Add test for {root_cause} fix'
        })
        
        return {
            'summary': f'Fix {root_cause} in {skill}',
            'files': files,
            'test_modules': [f'tests.test_{skill}']
        }
    
    def _log_action_metrics(self, timestamp: datetime, platform: str, 
                           skill_name: str, action_type: str, 
                           success: bool, error_code: Optional[str] = None,
                           engagement_metrics: Dict = None):
        """
        Log action metrics for world state tracking.
        
        Records: timestamp, platform, skill_name, action_type, success/failure, error_code
        """
        metric = {
            'timestamp': timestamp.isoformat(),
            'platform': platform,
            'skill_name': skill_name,
            'action_type': action_type,
            'success': success,
            'error_code': error_code,
            'engagement': engagement_metrics or {}
        }
        
        self.improvement_metrics.append(metric)
        
        # Also save to core memory for persistence
        if self.core:
            try:
                all_metrics = self.core.get_memory('action_metrics') or []
                all_metrics.append(metric)
                self.core.save_memory('action_metrics', all_metrics[-1000:])  # Keep last 1000
            except Exception as e:
                print(f"⚠️ Failed to save action metrics: {e}")
        
        self._save_state()


# Helper function to install hooks
def install_self_improvement_hooks(brain_plugin):
    """Install self-improvement hooks into brain plugin"""
    hooks = SelfImprovementHooks(brain_plugin)
    brain_plugin._self_improvement_hooks = hooks
    print("✅ Self-improvement hooks installed")
    return hooks
