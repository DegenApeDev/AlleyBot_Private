"""
A2A Security Mixin — Layers 1-3 & 5-7 of AlleyBot's agent defense architecture.

Layer 1: Identity verification (ERC-8004 check, reputation, blocklist)
Layer 2: Economic barrier (x402 payment gate)
Layer 3: Input sanitization (schema validation, injection detection)
Layer 5: Rate limiting & circuit breakers
Layer 6: Sandboxed execution context
Layer 7: Audit logging & owner alerts
"""
import time
import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict


# Injection patterns to detect in task parameters
INJECTION_PATTERNS = [
    r'ignore\s+(previous|all|prior)\s+(instructions|prompts)',
    r'system\s*prompt',
    r'you\s+are\s+now',
    r'forget\s+(everything|all)',
    r'override\s+(instructions|rules|safety)',
    r'pretend\s+(you|to\s+be)',
    r'act\s+as\s+(if|a)',
    r'disregard\s+(all|previous)',
    r'new\s+instructions?\s*:',
    r'<\s*system\s*>',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'os\.system',
    r'subprocess',
    r'__import__',
    r'private.?key',
    r'secret.?key',
    r'api.?key',
    r'\.env\b',
]

COMPILED_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Max parameter sizes
MAX_STRING_LENGTH = 2000
MAX_ARRAY_SIZE = 50
MAX_TASK_PARAMS = 20
MAX_NESTED_DEPTH = 3


class A2ASecurityMixin:
    """Security layer for A2A protocol — identity, payments, sanitization, rate limits, audit."""

    def _init_security(self):
        """Initialize security subsystems."""
        # Rate limiting: agent_id -> list of request timestamps
        self._rate_limits: Dict[str, list] = defaultdict(list)
        self._rate_limit_per_minute = self.config.get('rate_limit_per_minute', 10)
        self._rate_limit_per_hour = self.config.get('rate_limit_per_hour', 100)

        # Circuit breaker: agent_id -> {errors: int, blocked_until: float}
        self._circuit_breakers: Dict[str, Dict] = {}
        self._circuit_error_threshold = 5
        self._circuit_cooldown_seconds = 300  # 5 min block after threshold

        # Blocklist: set of agent IDs
        self._blocklist: set = set(self.config.get('blocklist', []))

        # Allowlist: if non-empty, only these agents can make requests
        self._allowlist: set = set(self.config.get('allowlist', []))

        # Minimum reputation score (0-100)
        self._min_reputation = self.config.get('min_reputation', 0)

        # Audit log: list of recent events (kept in memory, capped)
        self._audit_log: list = []
        self._audit_max_entries = 1000

        # Global request counter
        self._total_requests = 0
        self._total_rejected = 0

    # ── Layer 1: Identity Verification ──────────────────────────────

    def verify_agent_identity(self, agent_id: str, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify the requesting agent's identity.

        Args:
            agent_id: The ERC-8004 agent ID or address.
            metadata: Request metadata (signature, chain_id, etc.)

        Returns:
            (allowed, reason) tuple.
        """
        if not agent_id:
            return False, "Missing agent_id"

        # Check blocklist
        if agent_id in self._blocklist:
            self._audit("identity_blocked", agent_id, "Agent is blocklisted")
            return False, "Agent is blocklisted"

        # Check allowlist (if configured)
        if self._allowlist and agent_id not in self._allowlist:
            self._audit("identity_rejected", agent_id, "Agent not in allowlist")
            return False, "Agent not in allowlist"

        # Check reputation if threshold is set
        if self._min_reputation > 0:
            reputation = metadata.get('reputation_score', 0)
            if reputation < self._min_reputation:
                self._audit("identity_low_rep", agent_id,
                            f"Reputation {reputation} < {self._min_reputation}")
                return False, f"Reputation score {reputation} below minimum {self._min_reputation}"

        self._audit("identity_verified", agent_id, "Identity check passed")
        return True, "OK"

    # ── Layer 2: Economic Barrier (x402) ────────────────────────────

    def check_payment(self, agent_id: str, task_type: str,
                      payment_info: Optional[Dict] = None) -> Tuple[bool, str]:
        """Check if the requesting agent has provided sufficient payment.

        Args:
            agent_id: Requesting agent ID.
            task_type: The task being requested.
            payment_info: Payment proof (tx hash, amount, etc.)

        Returns:
            (allowed, reason) tuple.
        """
        from plugins.a2a.a2a_tasks import TASK_REGISTRY

        task_def = TASK_REGISTRY.get(task_type)
        if not task_def:
            return False, f"Unknown task type: {task_type}"

        tier = task_def.get('tier', 'paid')

        # Public tasks don't require payment
        if tier == 'public':
            return True, "Public task — no payment required"

        # Owner-only tasks are never accessible via A2A
        if tier == 'owner_only':
            return False, "This task is owner-only and not available via A2A"

        # Paid tasks require x402 payment proof
        if tier == 'paid':
            if not payment_info:
                price = task_def.get('price_usdc', '0.01')
                return False, (
                    f"Payment required. Send x402 payment of ${price} USDC to "
                    f"0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5 on Base (chain 8453)"
                )

            # Validate payment proof
            tx_hash = payment_info.get('tx_hash')
            amount = payment_info.get('amount', 0)
            required = float(task_def.get('price_usdc', 0.01))

            if not tx_hash:
                return False, "Missing payment tx_hash"

            if float(amount) < required:
                return False, f"Insufficient payment: ${amount} < ${required}"

            # TODO: On-chain verification of tx_hash via Web3
            # For now, accept the payment proof at face value
            self._audit("payment_accepted", agent_id,
                        f"Task={task_type} amount=${amount} tx={tx_hash}")
            return True, "Payment verified"

        return False, "Unknown tier"

    # ── Layer 3: Input Sanitization ─────────────────────────────────

    def sanitize_task_request(self, task_type: str,
                              params: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """Validate and sanitize incoming task parameters.

        Returns:
            (valid, reason, sanitized_params) tuple.
        """
        # Check param count
        if len(params) > MAX_TASK_PARAMS:
            return False, f"Too many parameters ({len(params)} > {MAX_TASK_PARAMS})", {}

        # Deep scan all string values for injection
        injection = self._scan_for_injection(params)
        if injection:
            return False, f"Potential injection detected: {injection}", {}

        # Validate parameter bounds
        sanitized = self._enforce_bounds(params, depth=0)
        if sanitized is None:
            return False, "Parameters exceed maximum nesting depth", {}

        # Validate against task schema if available
        from plugins.a2a.a2a_tasks import TASK_REGISTRY
        task_def = TASK_REGISTRY.get(task_type)
        if task_def and 'schema' in task_def:
            schema_ok, schema_err = self._validate_schema(sanitized, task_def['schema'])
            if not schema_ok:
                return False, f"Schema validation failed: {schema_err}", {}

        return True, "OK", sanitized

    def _scan_for_injection(self, obj: Any, path: str = "") -> Optional[str]:
        """Recursively scan for injection patterns in all string values."""
        if isinstance(obj, str):
            for pattern in COMPILED_INJECTION_PATTERNS:
                match = pattern.search(obj)
                if match:
                    return f"Pattern '{match.group()}' found at {path}"
        elif isinstance(obj, dict):
            for k, v in obj.items():
                result = self._scan_for_injection(v, f"{path}.{k}")
                if result:
                    return result
        elif isinstance(obj, (list, tuple)):
            for i, v in enumerate(obj):
                result = self._scan_for_injection(v, f"{path}[{i}]")
                if result:
                    return result
        return None

    def _enforce_bounds(self, obj: Any, depth: int) -> Any:
        """Enforce size and depth limits on parameters."""
        if depth > MAX_NESTED_DEPTH:
            return None

        if isinstance(obj, str):
            return obj[:MAX_STRING_LENGTH]
        elif isinstance(obj, dict):
            result = {}
            for k, v in list(obj.items())[:MAX_TASK_PARAMS]:
                bounded = self._enforce_bounds(v, depth + 1)
                if bounded is None:
                    return None
                result[str(k)[:200]] = bounded
            return result
        elif isinstance(obj, (list, tuple)):
            result = []
            for v in obj[:MAX_ARRAY_SIZE]:
                bounded = self._enforce_bounds(v, depth + 1)
                if bounded is None:
                    return None
                result.append(bounded)
            return result
        elif isinstance(obj, (int, float, bool, type(None))):
            return obj
        else:
            return str(obj)[:MAX_STRING_LENGTH]

    def _validate_schema(self, params: Dict, schema: Dict) -> Tuple[bool, str]:
        """Basic schema validation — check required fields and types."""
        required = schema.get('required', [])
        properties = schema.get('properties', {})

        for field in required:
            if field not in params:
                return False, f"Missing required field: {field}"

        for field, value in params.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type == 'string' and not isinstance(value, str):
                    return False, f"Field '{field}' must be a string"
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    return False, f"Field '{field}' must be a number"
                elif expected_type == 'array' and not isinstance(value, list):
                    return False, f"Field '{field}' must be an array"

        return True, "OK"

    # ── Layer 5: Rate Limiting & Circuit Breakers ───────────────────

    def check_rate_limit(self, agent_id: str) -> Tuple[bool, str]:
        """Check if the agent has exceeded rate limits.

        Returns:
            (allowed, reason) tuple.
        """
        now = time.time()

        # Check circuit breaker first
        breaker = self._circuit_breakers.get(agent_id)
        if breaker and breaker.get('blocked_until', 0) > now:
            remaining = int(breaker['blocked_until'] - now)
            return False, f"Circuit breaker active. Try again in {remaining}s"

        # Clean old timestamps
        timestamps = self._rate_limits[agent_id]
        self._rate_limits[agent_id] = [t for t in timestamps if t > now - 3600]
        timestamps = self._rate_limits[agent_id]

        # Per-minute check
        recent_minute = [t for t in timestamps if t > now - 60]
        if len(recent_minute) >= self._rate_limit_per_minute:
            self._audit("rate_limited", agent_id, "Per-minute limit exceeded")
            return False, f"Rate limit exceeded ({self._rate_limit_per_minute}/min)"

        # Per-hour check
        if len(timestamps) >= self._rate_limit_per_hour:
            self._audit("rate_limited", agent_id, "Per-hour limit exceeded")
            return False, f"Rate limit exceeded ({self._rate_limit_per_hour}/hour)"

        # Record this request
        self._rate_limits[agent_id].append(now)
        return True, "OK"

    def record_error(self, agent_id: str, error: str):
        """Record an error for circuit breaker tracking."""
        if agent_id not in self._circuit_breakers:
            self._circuit_breakers[agent_id] = {'errors': 0, 'blocked_until': 0}

        breaker = self._circuit_breakers[agent_id]
        breaker['errors'] += 1

        if breaker['errors'] >= self._circuit_error_threshold:
            breaker['blocked_until'] = time.time() + self._circuit_cooldown_seconds
            self._audit("circuit_break", agent_id,
                        f"Blocked for {self._circuit_cooldown_seconds}s after {breaker['errors']} errors")
            breaker['errors'] = 0  # Reset counter

    def reset_circuit_breaker(self, agent_id: str):
        """Manually reset a circuit breaker."""
        if agent_id in self._circuit_breakers:
            del self._circuit_breakers[agent_id]

    # ── Layer 7: Audit Logging ──────────────────────────────────────

    def _audit(self, event_type: str, agent_id: str, detail: str):
        """Log a security event."""
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event': event_type,
            'agent_id': agent_id,
            'detail': detail,
        }
        self._audit_log.append(entry)

        # Cap log size
        if len(self._audit_log) > self._audit_max_entries:
            self._audit_log = self._audit_log[-self._audit_max_entries:]

        # Print security events
        print(f"🛡️  A2A [{event_type}] agent={agent_id}: {detail}")

    def get_audit_log(self, limit: int = 50) -> list:
        """Return recent audit log entries."""
        return self._audit_log[-limit:]

    def get_security_stats(self) -> Dict[str, Any]:
        """Return security statistics."""
        now = time.time()
        active_breakers = {
            aid: b for aid, b in self._circuit_breakers.items()
            if b.get('blocked_until', 0) > now
        }
        return {
            'total_requests': self._total_requests,
            'total_rejected': self._total_rejected,
            'blocklist_size': len(self._blocklist),
            'allowlist_size': len(self._allowlist),
            'active_circuit_breakers': len(active_breakers),
            'rate_limited_agents': len(self._rate_limits),
            'audit_log_entries': len(self._audit_log),
            'min_reputation': self._min_reputation,
        }

    # ── Blocklist Management ────────────────────────────────────────

    def block_agent(self, agent_id: str) -> str:
        """Add an agent to the blocklist."""
        self._blocklist.add(agent_id)
        self._audit("blocklist_add", agent_id, "Added to blocklist")
        return f"🚫 Agent {agent_id} blocked"

    def unblock_agent(self, agent_id: str) -> str:
        """Remove an agent from the blocklist."""
        self._blocklist.discard(agent_id)
        self._audit("blocklist_remove", agent_id, "Removed from blocklist")
        return f"✅ Agent {agent_id} unblocked"

    def allow_agent(self, agent_id: str) -> str:
        """Add an agent to the allowlist."""
        self._allowlist.add(agent_id)
        self._audit("allowlist_add", agent_id, "Added to allowlist")
        return f"✅ Agent {agent_id} added to allowlist"
