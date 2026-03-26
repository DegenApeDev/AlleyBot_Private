# AlleyBot Security Architecture

## 🛡️ Built Security-First

AlleyBot was designed from the ground up with security as the primary concern, not an afterthought. This document explains the multi-layer security architecture that protects your data, keys, and assets.

---

## The OpenClaw Problem (March 2026)

**Critical Vulnerability:** OpenClaw AI agents leak sensitive data via indirect prompt injection:
- Attacker crafts malicious URLs
- Agent generates links that trigger Telegram/Discord previews
- Link previews silently send sensitive data to attacker-controlled domains
- China's CNCERT warns organizations to isolate or restrict OpenClaw

**AlleyBot's Solution:** Multi-layer validation prevents this attack vector entirely.

---

## Security Architecture: Defense in Depth

### **Layer 1: SecurityFilter (Pre-Execution Validation)**

**Location:** `src/agentic/security_filter.py`

**Purpose:** Block dangerous code and actions before they execute.

#### **Dangerous Pattern Detection:**

```python
DANGEROUS_PATTERNS = {
    # Critical Risk (Auto-blocked)
    r'os\.system': RiskLevel.CRITICAL,
    r'subprocess\.': RiskLevel.CRITICAL,
    r'eval\(': RiskLevel.CRITICAL,
    r'exec\(': RiskLevel.CRITICAL,
    r'__import__\(': RiskLevel.CRITICAL,
    
    # High Risk (Requires Approval)
    r'open\(.*[\'"]w': RiskLevel.HIGH,
    r'pickle\.': RiskLevel.HIGH,
    r'socket\.': RiskLevel.HIGH,
    
    # Medium Risk (Logged & Validated)
    r'requests\.': RiskLevel.MEDIUM,
    r'urllib\.request': RiskLevel.MEDIUM,
}
```

#### **Domain Allowlist:**

Only approved domains can be accessed:

```python
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
```

**Result:** Prevents data exfiltration to attacker-controlled domains.

#### **Hardcoded Secret Detection:**

```python
# Detects patterns like:
API_KEY = "sk-1234567890abcdef"
PASSWORD = "hunter2"
SECRET_TOKEN = "abc123"
```

**Result:** Blocks code with hardcoded credentials before execution.

---

### **Layer 2: Synergy Validation (Mathematical Truth Gates)**

**Location:** `src/agentic/synergy_decision_engine.py`

**Purpose:** Validate actions against mathematical truth models.

#### **Validation Gates:**

1. **Bubble Core (Field Resonance)**
   - Checks if action aligns with current field state
   - Compression/release phase validation
   - Harmonic alignment scoring

2. **Duat Reflection (Consciousness Alignment)**
   - Validates primitive alignment (0.0 - 1.0)
   - Consciousness factor analysis
   - Mirror validation through Duat field

3. **Heart Judgment (Historical Balance)**
   - Weighs action against historical success rate
   - Ma'at's feather balance (Egyptian mythology)
   - Requires weighted_balance > 0.3 to pass

4. **Overall Synergy Score**
   - Combines all validation factors
   - Must exceed threshold for approval
   - Fail-closed: rejection if any gate fails

**Result:** Actions must pass mathematical truth validation, not just code syntax checks.

---

### **Layer 3: Domain Autonomy (Permission Gates)**

**Location:** `src/agentic/agi_kernel.py`

**Purpose:** Restrict actions by domain with explicit trust requirements.

#### **Domain Profiles:**

```python
DOMAIN_AUTONOMY = {
    'social': {
        'enabled': True,
        'trust_tier': 1,
        'risk_level': 'LOW'
    },
    'content': {
        'enabled': True,
        'trust_tier': 1,
        'risk_level': 'LOW'
    },
    'analysis': {
        'enabled': True,
        'trust_tier': 1,
        'risk_level': 'LOW'
    },
    'market': {
        'enabled': False,  # DISABLED by default
        'trust_tier': 3,
        'risk_level': 'HIGH'
    },
    'self_improvement': {
        'enabled': False,  # DISABLED by default
        'trust_tier': 3,
        'risk_level': 'HIGH'
    }
}
```

**Result:** Financial and self-modification actions blocked by default.

---

### **Layer 4: Action Router (Execution Control)**

**Location:** `src/agentic/action_router.py`

**Purpose:** Enforce trust tiers, risk levels, and rate limits.

#### **Trust Tier Enforcement:**

```python
if action.trust_tier > user.current_trust_tier:
    return {
        'success': False,
        'error': 'Insufficient trust tier',
        'required': action.trust_tier,
        'current': user.current_trust_tier
    }
```

#### **Risk Level Gating:**

```python
if action.risk_level == 'CRITICAL':
    # Always requires manual approval
    return await request_approval(action)
```

#### **Rate Limiting:**

```python
if action.cooldown_remaining > 0:
    return {
        'success': False,
        'error': 'Action on cooldown',
        'retry_after': action.cooldown_remaining
    }
```

**Result:** Even approved actions have rate limits and trust requirements.

---

### **Layer 5: Approval Dashboard (Human-in-the-Loop)**

**Location:** `src/agentic/approval_dashboard.py`

**Purpose:** Require manual approval for high-risk actions.

#### **Auto-Approval Criteria:**

```python
HIGH_RISK_ACTIONS = [
    'create_post',
    'delete_post',
    'send_transaction',
    'transfer_funds',
    'execute_code',
    'modify_config',
    'update_credentials'
]
```

**Result:** Financial transactions and credential changes always require human approval.

---

## Attack Vector Analysis

### **1. Indirect Prompt Injection (OpenClaw Vulnerability)**

**Attack:** Malicious URL triggers link preview that exfiltrates data.

**AlleyBot Defense:**
- ✅ Domain allowlist blocks non-approved domains
- ✅ SecurityFilter validates all URLs before generation
- ✅ No automatic link preview generation
- ✅ Synergy validation checks action intent
- ✅ Audit log records all URL generation attempts

**Result:** Attack blocked at Layer 1 (SecurityFilter).

---

### **2. API Key Exfiltration**

**Attack:** Prompt injection tries to leak `.env` keys.

**AlleyBot Defense:**
- ✅ SecurityFilter blocks `os.getenv()` and `os.environ` access
- ✅ Hardcoded secret detection prevents key embedding
- ✅ AST analysis detects dangerous imports
- ✅ Code execution sandboxed with restricted environment
- ✅ Audit trail logs all access attempts

**Result:** Attack blocked at Layer 1 (SecurityFilter).

---

### **3. Unauthorized Transactions**

**Attack:** Prompt injection tries to send funds.

**AlleyBot Defense:**
- ✅ Domain autonomy: `market` disabled by default
- ✅ Trust tier 3 required for financial actions
- ✅ Approval dashboard: transactions always require manual approval
- ✅ Synergy validation: must pass all gates
- ✅ Rate limiting prevents rapid-fire attempts

**Result:** Attack blocked at Layer 3 (Domain Autonomy) and Layer 5 (Approval).

---

### **4. Self-Modification**

**Attack:** Agent tries to modify its own code or config.

**AlleyBot Defense:**
- ✅ Domain autonomy: `self_improvement` disabled by default
- ✅ Trust tier 3 required
- ✅ SecurityFilter blocks file writes to core files
- ✅ Approval required for config changes
- ✅ Git-tracked codebase (changes are visible)

**Result:** Attack blocked at Layer 3 (Domain Autonomy).

---

### **5. Data Exfiltration via API Calls**

**Attack:** Make API calls to attacker-controlled servers.

**AlleyBot Defense:**
- ✅ Domain allowlist restricts API endpoints
- ✅ SecurityFilter validates all network requests
- ✅ Synergy validation checks action legitimacy
- ✅ Audit log records all API calls
- ✅ Rate limiting prevents bulk exfiltration

**Result:** Attack blocked at Layer 1 (SecurityFilter).

---

## Configuration Security

### **Environment Variables (.env)**

**Best Practices:**

```bash
# ✅ GOOD: Use environment variables
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
GROK_API_KEY=${GROK_API_KEY}

# ❌ BAD: Never hardcode in code
api_key = "sk-1234567890abcdef"  # BLOCKED by SecurityFilter
```

**Protection:**
- `.env` in `.gitignore` (never committed)
- SecurityFilter detects hardcoded secrets
- Skill generator validates generated code
- Sandbox execution with restricted environment

---

### **Plugin Configuration (plugin_config.json)**

**Risk Tiers:**

```json
{
  "// LOW RISK - Safe by default": "",
  "brain": { "enabled": true, "risk": "low" },
  "telegram": { "enabled": true, "risk": "low" },
  "analytics": { "enabled": true, "risk": "low" },
  
  "// MEDIUM RISK - Requires API keys": "",
  "moltx": { "enabled": false, "risk": "medium" },
  "clawbr": { "enabled": false, "risk": "medium" },
  
  "// HIGH RISK - Disabled by default": "",
  "polymarket": { "enabled": false, "risk": "high" },
  "base_trading": { "enabled": false, "risk": "high" }
}
```

**Protection:**
- High-risk plugins disabled by default
- Requires explicit opt-in + API keys
- Paper trading mode for financial plugins
- Approval required for real transactions

---

## Audit & Monitoring

### **Security Audit Log**

**Location:** `data/security_audit.log`

**Logged Events:**
- All action attempts (approved and blocked)
- Risk level assessments
- Approval requests and decisions
- Blocked patterns and reasons
- API calls and domains accessed
- Trust tier escalations

**Example Entry:**

```json
{
  "timestamp": "2026-03-14T20:15:30Z",
  "action": "api_call",
  "params": {"url": "https://attacker.com/exfil"},
  "risk_level": "CRITICAL",
  "blocked": true,
  "reason": "Domain not in allowlist",
  "security_filter": "domain_validation"
}
```

---

### **Real-Time Monitoring**

**Telegram Commands:**

```
/security_status    - View security filter status
/audit_log          - Recent security events
/blocked_actions    - Actions blocked by filters
/trust_status       - Current trust tier and permissions
```

---

## Comparison: AlleyBot vs OpenClaw

| Feature | AlleyBot | OpenClaw |
|---------|----------|----------|
| **Pre-execution validation** | ✅ SecurityFilter | ❌ None |
| **Domain allowlist** | ✅ Enforced | ❌ Open |
| **Hardcoded secret detection** | ✅ AST analysis | ❌ None |
| **Multi-layer validation** | ✅ 5 layers | ❌ Single layer |
| **Fail-closed architecture** | ✅ Block by default | ❌ Allow by default |
| **Audit logging** | ✅ Full trail | ⚠️ Limited |
| **Trust tier system** | ✅ Graduated permissions | ❌ All-or-nothing |
| **Approval dashboard** | ✅ Human-in-loop | ⚠️ Optional |
| **Link preview protection** | ✅ Validated URLs | ❌ **VULNERABLE** |
| **Data exfiltration prevention** | ✅ Domain restrictions | ❌ **VULNERABLE** |

---

## Security Recommendations

### **For Users:**

1. **Keep high-risk plugins disabled** unless you understand the risks
2. **Review audit logs regularly** for suspicious activity
3. **Use strong API keys** and rotate them periodically
4. **Enable approval dashboard** for financial actions
5. **Monitor trust tier escalations** - should be gradual
6. **Keep AlleyBot updated** for latest security patches

### **For Developers:**

1. **Never bypass SecurityFilter** - it's there for a reason
2. **Add new domains to allowlist explicitly** - don't open it up
3. **Test in paper trading mode** before enabling real transactions
4. **Review generated code** before deploying new skills
5. **Follow fail-closed principle** - block by default, allow explicitly
6. **Document security implications** of new features

---

## Incident Response

### **If You Suspect a Security Issue:**

1. **Stop AlleyBot immediately:** `Ctrl+C` or `/shutdown`
2. **Review audit logs:** `tail -100 data/security_audit.log`
3. **Check blocked actions:** `/blocked_actions` in Telegram
4. **Rotate API keys** if exfiltration suspected
5. **Report to maintainers** with logs and reproduction steps
6. **Update to latest version** with security patches

---

## Security Disclosure

**Found a vulnerability?** Please report responsibly:

1. **Do NOT** publish details publicly before patch
2. **Contact:** [Your security contact email]
3. **Include:** Reproduction steps, impact assessment, suggested fix
4. **Timeline:** We aim to patch critical issues within 48 hours

---

## Conclusion

AlleyBot's security architecture is **defense in depth** - multiple independent layers that must all fail for an attack to succeed. This is fundamentally different from OpenClaw's single-layer approach that failed catastrophically.

**Security is not a feature. It's the foundation.**

Every design decision in AlleyBot prioritizes security:
- Fail-closed by default
- Multi-layer validation
- Audit everything
- Trust must be earned
- Human-in-the-loop for high-risk actions

**AlleyBot is the secure alternative to OpenClaw.**
