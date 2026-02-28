"""
Error Monitor - Autonomous error detection and self-healing for AGI Kernel

Monitors console logs for errors and triggers self-healing through the
selfimprove plugin. This is part of the AGI Kernel, not a plugin.

Key Features:
- Scans console logs for error patterns
- Classifies error types (import, API, plugin, syntax)
- Triggers AGI decision: should we auto-fix?
- Routes to selfimprove plugin for autonomous fixes
- Records outcomes to episodic memory

SOP Compliance:
- This is an AGI Kernel component (src/agentic/), not a plugin
- No decision logic - delegates to AGI Kernel's decision_system
- No persistent state - uses unified memory
- Follows existing pattern from decision_system.py
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque


class ErrorMonitor:
    """
    Monitor console logs for errors and trigger autonomous self-healing.
    
    This is part of the AGI Kernel's self-improvement loop.
    """
    
    # Error patterns to detect in console logs
    ERROR_PATTERNS = {
        'import_error': {
            'regex': r'(ImportError|ModuleNotFoundError):\s*(.+)',
            'severity': 'high',
            'auto_fix': True,
        },
        'api_error': {
            'regex': r'(404|500|502|503|ConnectionError|Timeout|HTTPError).*:\s*(.+)',
            'severity': 'medium',
            'auto_fix': True,
        },
        'plugin_error': {
            'regex': r'(Plugin.*failed|❌.*plugin|Error loading plugin).*:\s*(.+)',
            'severity': 'medium',
            'auto_fix': True,
        },
        'syntax_error': {
            'regex': r'(SyntaxError|IndentationError).*:\s*(.+)',
            'severity': 'high',
            'auto_fix': True,
        },
        'attribute_error': {
            'regex': r'AttributeError.*has no attribute\s+[\'"](\w+)[\'"]',
            'severity': 'medium',
            'auto_fix': True,
        },
        'key_error': {
            'regex': r'KeyError:\s*[\'"](\w+)[\'"]',
            'severity': 'low',
            'auto_fix': False,
        },
        'value_error': {
            'regex': r'ValueError:\s*(.+)',
            'severity': 'low',
            'auto_fix': False,
        },
    }
    
    def __init__(self, agi_kernel, max_history: int = 100):
        """
        Initialize error monitor.
        
        Args:
            agi_kernel: AGI Kernel instance for decision-making
            max_history: Maximum errors to keep in history
        """
        self.agi = agi_kernel
        self.max_history = max_history
        
        # Error tracking
        self.error_history: deque = deque(maxlen=max_history)
        self.last_check_time: Optional[datetime] = None
        self.check_interval_minutes = 5
        
        # Console log paths to monitor
        self.log_paths = [
            'data/console.log',
            'logs/alleybot.log',
            'logs/errors.log',
        ]
        
        # Track log file positions to avoid re-reading
        self.log_positions: Dict[str, int] = {}
        
        print("🔍 Error Monitor initialized")
    
    def scan_logs(self) -> List[Dict[str, Any]]:
        """
        Scan console logs for errors.
        
        Returns list of detected errors with metadata.
        """
        detected_errors = []
        
        for log_path in self.log_paths:
            if not os.path.exists(log_path):
                continue
            
            try:
                with open(log_path, 'r') as f:
                    # Seek to last position if we've read before
                    start_pos = self.log_positions.get(log_path, 0)
                    f.seek(start_pos)
                    
                    # Read new lines
                    lines = f.readlines()
                    
                    # Update position
                    self.log_positions[log_path] = f.tell()
                    
                    # Scan each line for errors
                    for line_num, line in enumerate(lines, start=start_pos):
                        error = self._detect_error(line, log_path, line_num)
                        if error:
                            detected_errors.append(error)
                            self.error_history.append(error)
            
            except Exception as e:
                print(f"⚠️ Error reading {log_path}: {e}")
        
        return detected_errors
    
    def _detect_error(self, line: str, log_path: str, line_num: int) -> Optional[Dict[str, Any]]:
        """
        Detect if a log line contains an error.
        
        Returns error dict if detected, None otherwise.
        """
        line = line.strip()
        if not line:
            return None
        
        # Try each error pattern
        for error_type, pattern_info in self.ERROR_PATTERNS.items():
            match = re.search(pattern_info['regex'], line, re.IGNORECASE)
            if match:
                return {
                    'type': error_type,
                    'message': line,
                    'match_groups': match.groups(),
                    'severity': pattern_info['severity'],
                    'auto_fix': pattern_info['auto_fix'],
                    'log_path': log_path,
                    'line_num': line_num,
                    'timestamp': datetime.now().isoformat(),
                }
        
        return None
    
    async def autonomous_health_check(self) -> Dict[str, Any]:
        """
        Run autonomous health check - called by AGI Kernel every 5 minutes.
        
        Flow:
        1. Scan logs for new errors
        2. Filter errors that should trigger auto-fix
        3. For each error, ask AGI: should we fix this?
        4. If yes, route to selfimprove plugin via action router
        5. Record outcome to episodic memory
        
        Returns summary of health check results.
        """
        # Check if enough time has passed
        if self.last_check_time:
            elapsed = datetime.now() - self.last_check_time
            if elapsed < timedelta(minutes=self.check_interval_minutes):
                return {'status': 'skipped', 'reason': 'too_soon'}
        
        self.last_check_time = datetime.now()
        
        # Scan for errors
        errors = self.scan_logs()
        
        if not errors:
            return {
                'status': 'healthy',
                'errors_found': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"🔍 Found {len(errors)} errors in logs")
        
        # Filter errors that should trigger auto-fix
        fixable_errors = [e for e in errors if e['auto_fix']]
        
        if not fixable_errors:
            return {
                'status': 'errors_found',
                'errors_found': len(errors),
                'fixable': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Process each fixable error
        fix_results = []
        for error in fixable_errors[:3]:  # Limit to 3 errors per cycle
            result = await self._attempt_fix(error)
            fix_results.append(result)
        
        return {
            'status': 'fixes_attempted',
            'errors_found': len(errors),
            'fixable': len(fixable_errors),
            'fixes_attempted': len(fix_results),
            'results': fix_results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _attempt_fix(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to fix an error autonomously.
        
        Flow:
        1. Ask AGI Kernel: should we fix this error?
        2. If yes, execute auto_fix_error action via action router
        3. Record outcome
        """
        error_type = error['type']
        error_msg = error['message']
        
        print(f"🔧 Attempting to fix {error_type}: {error_msg[:80]}...")
        
        # Check if AGI Kernel has decision system
        if not hasattr(self.agi, 'decision_system'):
            return {
                'success': False,
                'error_type': error_type,
                'reason': 'No decision system available'
            }
        
        # Let AGI decide if we should fix this error
        context = {
            'type': 'error_detected',
            'error': error,
            'autonomous': True,
            'severity': error['severity']
        }
        
        # AGI decides whether to take action
        decision = self.agi.decide(context)
        
        if not decision or decision.get('id') != 'auto_fix_error':
            return {
                'success': False,
                'error_type': error_type,
                'reason': 'AGI decided not to fix',
                'decision': decision.get('id') if decision else None
            }
        
        # Execute fix through action router
        if not hasattr(self.agi, 'action_router'):
            return {
                'success': False,
                'error_type': error_type,
                'reason': 'No action router available'
            }
        
        try:
            result = await self.agi.act({
                'plugin': 'selfimprove',
                'action_type': 'auto_fix_error',
                'params': {
                    'error_type': error_type,
                    'error_message': error_msg,
                    'error_details': error
                },
                'context': {
                    'autonomous': True,
                    'impact': 'high',
                    'triggered_by': 'error_monitor'
                }
            })
            
            return {
                'success': result.get('success', False),
                'error_type': error_type,
                'fix_result': result,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error_type': error_type,
                'reason': f'Exception during fix: {str(e)}'
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics about detected errors"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_type': {},
                'by_severity': {}
            }
        
        # Count by type
        by_type = {}
        by_severity = {}
        
        for error in self.error_history:
            error_type = error['type']
            severity = error['severity']
            
            by_type[error_type] = by_type.get(error_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'by_type': by_type,
            'by_severity': by_severity,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent errors"""
        return list(self.error_history)[-limit:]


def create_error_monitor(agi_kernel):
    """Factory function to create error monitor"""
    return ErrorMonitor(agi_kernel)
