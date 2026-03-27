"""
Approval Dashboard for High-Risk Actions
Telegram integration for human-in-the-loop approval
"""
import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """Approval request structure"""
    id: str
    action: str
    params: Dict[str, Any]
    security_check: Dict[str, Any]
    timestamp: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    response_time: Optional[datetime] = None
    approver: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'params': self.params,
            'security_check': self.security_check,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'response_time': self.response_time.isoformat() if self.response_time else None,
            'approver': self.approver,
            'notes': self.notes
        }


class ApprovalDashboard:
    """
    Approval dashboard for high-risk actions
    Integrates with Telegram for real-time approval requests
    """
    
    def __init__(self, telegram_bot=None, admin_chat_id: Optional[str] = None,
                 timeout_seconds: int = 300):
        self.telegram_bot = telegram_bot
        self.admin_chat_id = admin_chat_id or os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        self.timeout_seconds = timeout_seconds
        
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.request_history: List[ApprovalRequest] = []
        
        self.auto_approve_patterns = []
        self.auto_deny_patterns = []
        
    async def request_approval(self, action: str, params: Dict[str, Any],
                        security_check: Dict[str, Any]) -> bool:
        """
        Request approval for an action
        
        Args:
            action: Action name
            params: Action parameters
            security_check: Security check results
            
        Returns:
            True if approved, False if denied
        """
        # Create approval request
        request_id = f"approval_{datetime.now().timestamp()}"
        request = ApprovalRequest(
            id=request_id,
            action=action,
            params=params,
            security_check=security_check,
            timestamp=datetime.now()
        )
        
        # Check auto-approve patterns
        if self._check_auto_approve(action, params):
            request.status = ApprovalStatus.APPROVED
            request.response_time = datetime.now()
            request.approver = "auto"
            request.notes = "Auto-approved based on pattern"
            self.request_history.append(request)
            return True
        
        # Check auto-deny patterns
        if self._check_auto_deny(action, params):
            request.status = ApprovalStatus.DENIED
            request.response_time = datetime.now()
            request.approver = "auto"
            request.notes = "Auto-denied based on pattern"
            self.request_history.append(request)
            return False
        
        # Add to pending
        self.pending_requests[request_id] = request
        
        # Send Telegram notification
        if self.telegram_bot and self.admin_chat_id:
            self._send_telegram_approval_request(request)
        else:
            print("⚠️  No Telegram bot configured - approval request logged only")
        
        # Wait for approval with timeout
        approved = await self._wait_for_approval(request_id)
        
        # Move to history
        request = self.pending_requests.pop(request_id)
        self.request_history.append(request)
        
        # Keep only last 100 requests
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
        
        return approved
    
    def _send_telegram_approval_request(self, request: ApprovalRequest):
        """Send approval request via Telegram"""
        try:
            risk_emoji = {
                'SAFE': '✅',
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🟠',
                'CRITICAL': '🔴'
            }
            
            risk_level = request.security_check.get('risk_level', 'UNKNOWN')
            emoji = risk_emoji.get(risk_level, '⚠️')
            
            message = f"""
{emoji} **APPROVAL REQUIRED** {emoji}

**Action:** `{request.action}`
**Risk Level:** {risk_level}
**Request ID:** `{request.id}`

**Parameters:**
```json
{json.dumps(request.params, indent=2)}
```

**Security Issues:**
{self._format_security_issues(request.security_check.get('issues', []))}

**Commands:**
• `/approve {request.id}` - Approve this action
• `/deny {request.id} [reason]` - Deny this action
• `/details {request.id}` - View full details

⏰ Timeout: {self.timeout_seconds}s
"""
            
            self.telegram_bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"⚠️  Failed to send Telegram approval request: {e}")
    
    def _format_security_issues(self, issues: List[Dict]) -> str:
        """Format security issues for display"""
        if not issues:
            return "None"
        
        formatted = []
        for issue in issues[:5]:  # Show max 5 issues
            issue_type = issue.get('type', 'unknown')
            risk = issue.get('risk_level', 'UNKNOWN')
            formatted.append(f"• [{risk}] {issue_type}")
        
        if len(issues) > 5:
            formatted.append(f"• ... and {len(issues) - 5} more")
        
        return '\n'.join(formatted)
    
    async def _wait_for_approval(self, request_id: str) -> bool:
        """Wait for approval with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout_seconds:
            request = self.pending_requests.get(request_id)
            
            if not request:
                return False
            
            if request.status == ApprovalStatus.APPROVED:
                return True
            elif request.status == ApprovalStatus.DENIED:
                return False
            
            await asyncio.sleep(1)
        
        # Timeout
        request = self.pending_requests.get(request_id)
        if request:
            request.status = ApprovalStatus.TIMEOUT
            request.response_time = datetime.now()
            request.notes = "Request timed out"
        
        return False
    
    def approve_request(self, request_id: str, approver: str = "admin",
                       notes: Optional[str] = None) -> bool:
        """Approve a pending request"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.status = ApprovalStatus.APPROVED
            request.response_time = datetime.now()
            request.approver = approver
            request.notes = notes
            
            print(f"✅ Request approved: {request_id}")
            return True
        
        return False
    
    def deny_request(self, request_id: str, approver: str = "admin",
                    notes: Optional[str] = None) -> bool:
        """Deny a pending request"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.status = ApprovalStatus.DENIED
            request.response_time = datetime.now()
            request.approver = approver
            request.notes = notes or "Denied by admin"
            
            print(f"❌ Request denied: {request_id}")
            return True
        
        return False
    
    def add_auto_approve_pattern(self, pattern: Dict[str, Any]):
        """Add pattern for auto-approval"""
        self.auto_approve_patterns.append(pattern)
    
    def add_auto_deny_pattern(self, pattern: Dict[str, Any]):
        """Add pattern for auto-denial"""
        self.auto_deny_patterns.append(pattern)
    
    def _check_auto_approve(self, action: str, params: Dict[str, Any]) -> bool:
        """Check if action matches auto-approve patterns"""
        for pattern in self.auto_approve_patterns:
            if self._matches_pattern(action, params, pattern):
                return True
        return False
    
    def _check_auto_deny(self, action: str, params: Dict[str, Any]) -> bool:
        """Check if action matches auto-deny patterns"""
        for pattern in self.auto_deny_patterns:
            if self._matches_pattern(action, params, pattern):
                return True
        return False
    
    def _matches_pattern(self, action: str, params: Dict[str, Any],
                        pattern: Dict[str, Any]) -> bool:
        """Check if action matches a pattern"""
        # Check action name
        if 'action' in pattern:
            if pattern['action'] != action:
                return False
        
        # Check params
        if 'params' in pattern:
            for key, value in pattern['params'].items():
                if key not in params or params[key] != value:
                    return False
        
        return True
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending approval requests"""
        return [req.to_dict() for req in self.pending_requests.values()]
    
    def get_request_history(self, limit: int = 50) -> List[Dict]:
        """Get approval request history"""
        return [req.to_dict() for req in self.request_history[-limit:]]
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        total = len(self.request_history)
        approved = len([r for r in self.request_history if r.status == ApprovalStatus.APPROVED])
        denied = len([r for r in self.request_history if r.status == ApprovalStatus.DENIED])
        timeout = len([r for r in self.request_history if r.status == ApprovalStatus.TIMEOUT])
        
        # Calculate average response time
        response_times = [
            (r.response_time - r.timestamp).total_seconds()
            for r in self.request_history
            if r.response_time
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_requests': total,
            'approved': approved,
            'denied': denied,
            'timeout': timeout,
            'pending': len(self.pending_requests),
            'approval_rate': approved / total if total > 0 else 0,
            'avg_response_time_seconds': avg_response_time,
            'auto_approve_patterns': len(self.auto_approve_patterns),
            'auto_deny_patterns': len(self.auto_deny_patterns)
        }


class TelegramApprovalHandler:
    """Handler for Telegram approval commands"""
    
    def __init__(self, approval_dashboard: ApprovalDashboard):
        self.dashboard = approval_dashboard
    
    def handle_approve_command(self, request_id: str, user_id: str) -> str:
        """Handle /approve command"""
        if self.dashboard.approve_request(request_id, approver=user_id):
            return f"✅ Request {request_id} approved"
        else:
            return f"❌ Request {request_id} not found or already processed"
    
    def handle_deny_command(self, request_id: str, user_id: str,
                           reason: Optional[str] = None) -> str:
        """Handle /deny command"""
        if self.dashboard.deny_request(request_id, approver=user_id, notes=reason):
            return f"❌ Request {request_id} denied"
        else:
            return f"❌ Request {request_id} not found or already processed"
    
    def handle_details_command(self, request_id: str) -> str:
        """Handle /details command"""
        # Check pending
        if request_id in self.dashboard.pending_requests:
            request = self.dashboard.pending_requests[request_id]
            return self._format_request_details(request)
        
        # Check history
        for request in self.dashboard.request_history:
            if request.id == request_id:
                return self._format_request_details(request)
        
        return f"❌ Request {request_id} not found"
    
    def handle_pending_command(self) -> str:
        """Handle /pending command"""
        pending = self.dashboard.get_pending_requests()
        
        if not pending:
            return "✅ No pending approval requests"
        
        message = f"⏳ **Pending Approvals ({len(pending)})**\n\n"
        
        for req in pending:
            message += f"• `{req['id']}` - {req['action']} [{req['security_check']['risk_level']}]\n"
        
        return message
    
    def handle_stats_command(self) -> str:
        """Handle /stats command"""
        stats = self.dashboard.get_approval_stats()
        
        message = f"""
📊 **Approval Statistics**

Total Requests: {stats['total_requests']}
✅ Approved: {stats['approved']}
❌ Denied: {stats['denied']}
⏰ Timeout: {stats['timeout']}
⏳ Pending: {stats['pending']}

Approval Rate: {stats['approval_rate']:.1%}
Avg Response Time: {stats['avg_response_time_seconds']:.1f}s

Auto-Approve Patterns: {stats['auto_approve_patterns']}
Auto-Deny Patterns: {stats['auto_deny_patterns']}
"""
        
        return message
    
    def _format_request_details(self, request: ApprovalRequest) -> str:
        """Format request details for display"""
        message = f"""
📋 **Request Details**

**ID:** `{request.id}`
**Action:** `{request.action}`
**Status:** {request.status.value.upper()}
**Risk Level:** {request.security_check.get('risk_level', 'UNKNOWN')}

**Timestamp:** {request.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Response Time:** {request.response_time.strftime('%Y-%m-%d %H:%M:%S') if request.response_time else 'N/A'}
**Approver:** {request.approver or 'N/A'}

**Parameters:**
```json
{json.dumps(request.params, indent=2)}
```

**Security Issues:**
{len(request.security_check.get('issues', []))} issues detected

**Notes:** {request.notes or 'None'}
"""
        
        return message
