# AlleyBot Security Audit Report

**Audit Date:** February 11, 2026  
**Auditor:** Senior Cybersecurity Engineer  
**Scope:** Complete codebase review - plugins/, src/, config files  
**Files Analyzed:** 50+ Python modules, configuration files, dependencies

---

## Executive Summary

AlleyBot is an autonomous AI agent with social media integration (Moltx, MoltBook), blockchain analytics (Base network), A2A protocol compliance, and self-improvement capabilities. The codebase demonstrates **strong security awareness** in several areas but contains **critical vulnerabilities** that require immediate attention.

**Overall Security Posture Rating: 6/10**
- **Strengths:** Security filtering for outbound messages, input validation in A2A server, encrypted storage for sensitive data, sandboxed code execution
- **Weaknesses:** Critical use of `eval()` in secret manager, subprocess calls in autonomous coder, insufficient input sanitization in some areas

---

## Critical Vulnerabilities (Immediate Action Required)

### 1. **CRITICAL: Arbitrary Code Execution via `eval()` in Secret Manager**

**Location:** `src/security/secret_manager.py`

**Lines:** 230, 281, 345, 371

**Vulnerability:** The SecretManager uses `eval()` to deserialize metadata strings:

```python
# Line 230
metadata = eval(old_metadata) if old_metadata else {}

# Line 281  
metadata = eval(metadata_str)

# Line 345
all_logs = eval(existing)

# Line 371
metadata = eval(metadata_str)
```

**Impact:** If an attacker can manipulate the vault storage (via file system access, memory corruption, or compromised vault client), they can inject malicious Python code that executes with the same privileges as the AlleyBot process.

**Attack Vector:**
1. Attacker gains access to vault data or compromises the vault client
2. Injects malicious metadata: `{"rotated_at": "2024-01-01", "previous_version": "__import__('os').system('rm -rf /')"}`
3. SecretManager calls `eval()` on this data during rotation check
4. Arbitrary code execution achieved

**Remediation:**
```python
# Replace eval() with json.loads()
import json

# Line 230 fix:
metadata = json.loads(old_metadata) if old_metadata else {}

# Ensure all metadata is stored as JSON, not Python literals
```

**Priority:** P0 - Fix immediately

---

### 2. **CRITICAL: Unrestricted Subprocess Execution in Autonomous Coder**

**Location:** `plugins/selfimprove/autonomous_coder.py`

**Lines:** 124-126, 144-149, 729-733, 753-770

**Vulnerability:** Multiple subprocess calls without proper input validation:

```python
# Lines 124-126 - User-controlled path in compile check
result = subprocess.run(
    [python_cmd, '-c', f"import py_compile; py_compile.compile(r'{tmp_path}', doraise=True)"],
    capture_output=True, text=True, timeout=15, env=env,
)

# Lines 729-733 - Git checkout with user-controlled paths
subprocess.run(
    ['git', 'checkout', '--', gf['path']],
    cwd=self.project_root,
    capture_output=True, timeout=10,
)
```

**Impact:** Path traversal and command injection. If an attacker controls the `path` field in a generated file object, they can execute arbitrary commands:

**Attack Example:**
```python
# Attacker submits plan with malicious path
gf = {
    'path': '../../../../../etc/passwd; rm -rf / #',
    'action': 'modify'
}
# This causes: git checkout -- ../../../etc/passwd; rm -rf / #
```

**Remediation:**
```python
from pathlib import Path
import re

def sanitize_path(path: str, project_root: str) -> str:
    """Ensure path stays within project root"""
    # Normalize the path
    full_path = Path(project_root) / path
    
    # Resolve to absolute path
    try:
        resolved = full_path.resolve()
        root_resolved = Path(project_root).resolve()
        
        # Ensure path is within project root
        if not str(resolved).startswith(str(root_resolved)):
            raise ValueError(f"Path {path} is outside project root")
            
        # Block dangerous characters
        if any(c in path for c in [';', '&', '|', '$', '`', '\\0']):
            raise ValueError(f"Path contains dangerous characters")
            
        return str(resolved)
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

# Use in subprocess calls
safe_path = sanitize_path(gf['path'], self.project_root)
subprocess.run(['git', 'checkout', '--', safe_path], ...)
```

**Priority:** P0 - Fix immediately

---

### 3. **HIGH: Pickle Deserialization in Vector Memory Store**

**Location:** `src/agentic/enhanced_memory.py`

**Lines:** 206-209, 217-220

**Vulnerability:** Loading pickled data without validation:

```python
# Line 217-220
def load(self, filepath: str):
    with open(f"{filepath}.pkl", 'rb') as f:
        data = pickle.load(f)  # Dangerous!
        self.memories = data['memories']
```

**Impact:** Pickle deserialization can execute arbitrary code during unpickling. If an attacker can write to the memory files (e.g., via path traversal, file upload vulnerability, or compromised backup), they achieve RCE.

**Remediation:**
```python
# Option 1: Use JSON instead of pickle for non-binary data
import json

def save(self, filepath: str):
    # Convert memories to serializable dicts
    serializable = {
        'memories': [m.to_dict() for m in self.memories],
        'id_to_index': self.id_to_index
    }
    with open(f"{filepath}.json", 'w') as f:
        json.dump(serializable, f)

def load(self, filepath: str):
    with open(f"{filepath}.json", 'r') as f:
        data = json.load(f)
        # Reconstruct Memory objects with validation
        self.memories = []
        for m_data in data['memories']:
            # Validate required fields
            required = ['id', 'content', 'memory_type', 'timestamp']
            if not all(k in m_data for k in required):
                raise ValueError("Invalid memory data structure")
            self.memories.append(Memory(**m_data))

# Option 2: If pickle is required, add HMAC signature verification
import hmac
import hashlib

def save_secure(self, filepath: str, key: bytes):
    data = pickle.dumps({
        'memories': self.memories,
        'id_to_index': self.id_to_index
    })
    signature = hmac.new(key, data, hashlib.sha256).digest()
    with open(f"{filepath}.pkl", 'wb') as f:
        f.write(signature + data)

def load_secure(self, filepath: str, key: bytes):
    with open(f"{filepath}.pkl", 'rb') as f:
        content = f.read()
    signature = content[:32]
    data = content[32:]
    expected = hmac.new(key, data, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Data integrity check failed - possible tampering")
    data = pickle.loads(data)
```

**Priority:** P1 - Fix within 1 week

---

## High Severity Issues

### 4. **HIGH: Insufficient Input Validation in A2A Task Routing**

**Location:** `plugins/a2a/a2a_server.py`

**Lines:** 310-313, 562-601

**Vulnerability:** User-supplied metadata fields are used to route tasks without proper validation:

```python
# Lines 310-313
agent_id = request.headers.get('Authorization', 'anonymous')
metadata = body.get('metadata', {})

# Lines 570-573
task_type, task_params = self._route_message(user_text, body)
# ...
result = self.execute_task(task_type, sanitized_params, agent_id)
```

**Impact:** While basic sanitization exists, the task routing logic may allow unintended task types to be executed if an attacker crafts specific metadata.

**Remediation:**
```python
# Add strict allowlist for task types
ALLOWED_TASK_TYPES = {
    'agent.health', 'agent.capabilities', 'agent.stats', 'agent.skills',
    'content.generate_post', 'content.analyze_trend',
    'blockchain.check_balance', 'blockchain.lookup_tx'
}

def _route_message(self, text: str, body: Dict) -> tuple:
    # ... existing routing logic ...
    
    # Validate task_type is allowed
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError(f"Task type '{task_type}' not in allowlist")
    
    # Validate task_params types
    validated_params = {}
    for key, value in task_params.items():
        if not isinstance(key, str) or not key.isidentifier():
            raise ValueError(f"Invalid parameter key: {key}")
        # Only allow primitive types
        if not isinstance(value, (str, int, float, bool, list, dict)):
            raise ValueError(f"Invalid parameter type for {key}")
        validated_params[key] = value
    
    return task_type, validated_params
```

**Priority:** P1 - Fix within 1 week

---

### 5. **HIGH: CORS Misconfiguration in A2A Server**

**Location:** `plugins/a2a/a2a_server.py`

**Lines:** 158-163

**Vulnerability:** Overly permissive CORS configuration:

```python
@self._a2a_app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'  # Allows ANY origin
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, A2A-Version, A2A-Extensions'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response
```

**Impact:** Any website can make cross-origin requests to the A2A server, potentially enabling:
- CSRF attacks if authentication relies on cookies
- Information leakage through timing attacks
- Abuse of paid endpoints from unauthorized domains

**Remediation:**
```python
# Define allowed origins based on configuration
ALLOWED_ORIGINS = os.getenv('A2A_ALLOWED_ORIGINS', '').split(',')

@self._a2a_app.after_request
def add_cors(response):
    origin = request.headers.get('Origin')
    
    # Only allow configured origins
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'  # Important for caching
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, A2A-Version, A2A-Extensions'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response
```

**Priority:** P1 - Fix within 1 week

---

### 6. **HIGH: Sensitive Data Exposure in Telegram Error Messages**

**Location:** `plugins/telegram/telegram.py`

**Lines:** 224, 272, 311, 386

**Vulnerability:** Error messages sent to Telegram may contain sensitive information:

```python
# Line 224
await update.message.reply_text(f"❌ Error getting status: {str(e)}")

# Line 272
await update.message.reply_text(f"❌ Error checking DMs: {str(e)}")
```

**Impact:** Exception messages may include:
- File paths (`/home/user/project/secrets.py`)
- Database connection strings
- API keys in error traces
- Internal system architecture details

**Remediation:**
```python
from security_filter import security_filter

async def _handle_dm_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await self._verify_owner(update):
        return
    
    try:
        # ... logic ...
    except Exception as e:
        # Log full error internally
        import logging
        logging.error(f"DM check failed: {e}", exc_info=True)
        
        # Send sanitized message to user
        safe_error = security_filter.sanitize_error_message(str(e))
        await update.message.reply_text(f"❌ Error checking DMs. Reference: {self._error_ref()}")
        
        # Optionally send detailed error to owner via secure channel
        self.send_alert("System Error", f"DM check failed: {safe_error}", "high")

def _error_ref(self) -> str:
    """Generate unique error reference for support"""
    import uuid
    return str(uuid.uuid4())[:8]
```

**Priority:** P2 - Fix within 2 weeks

---

## Medium Severity Issues

### 7. **MEDIUM: Hardcoded Payment Address in Agent Card**

**Location:** `plugins/a2a/a2a_server.py`

**Line:** 217

**Issue:**
```python
"paymentAddress": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",
```

**Impact:** While not a direct security vulnerability, hardcoding payment addresses makes it difficult to:
- Rotate addresses if compromised
- Support multiple payment recipients
- Test in different environments

**Remediation:**
```python
# In config.py or .env
A2A_PAYMENT_ADDRESS = os.getenv('A2A_PAYMENT_ADDRESS', '0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5')

# In a2a_server.py
"paymentAddress": os.getenv('A2A_PAYMENT_ADDRESS'),
```

**Priority:** P2 - Fix within 2 weeks

---

### 8. **MEDIUM: Missing Rate Limit on A2A Streaming Endpoint**

**Location:** `plugins/a2a/a2a_server.py`

**Lines:** 390-500

**Issue:** The streaming endpoint (`/message:stream`) doesn't have explicit rate limiting, unlike the standard `/message:send` endpoint.

**Impact:** Attackers could abuse the streaming endpoint for:
- Resource exhaustion (keeping connections open)
- Denial of service
- Unpaid task execution

**Remediation:**
```python
def _handle_message_stream(self) -> Response:
    # Add rate limiting check
    agent_id = request.headers.get('Authorization', 'anonymous')
    rate_ok, rate_reason = self.check_rate_limit(agent_id)
    if not rate_ok:
        return _a2a_error("RATE_LIMITED", rate_reason, 429)
    
    # Add connection timeout for streaming
    def generate():
        start_time = time.time()
        max_duration = 60  # 60 second max stream
        
        # ... existing generate logic ...
        
        # Check timeout periodically
        if time.time() - start_time > max_duration:
            yield f"data: {json.dumps({'error': 'Stream timeout'})}\n\n"
            return
```

**Priority:** P2 - Fix within 2 weeks

---

### 9. **MEDIUM: Environment Variable Fallback in Secret Manager**

**Location:** `src/security/secret_manager.py`

**Lines:** 60, 118-122

**Issue:**
```python
self._fallback_to_env = True  # Allow fallback to os.getenv during migration

# Lines 118-122
if value is None and self._fallback_to_env:
    value = os.getenv(key.upper())
    if value:
        source_type = "env_fallback"
        print(f"⚠️  Secret '{key}' loaded from environment (migrate to vault!)")
```

**Impact:** Secrets may be unintentionally exposed through:
- Process listings (`ps e`)
- `/proc/*/environ` on Linux
- Core dumps
- Container inspection

**Remediation:**
```python
class SecretManager:
    def __init__(self, vault: Optional[VaultClient] = None):
        # Default to False - require explicit opt-in
        self._fallback_to_env = os.getenv('SECRET_MANAGER_FALLBACK', 'false').lower() == 'true'
        
        if self._fallback_to_env:
            import warnings
            warnings.warn(
                "SecretManager is configured to fallback to environment variables. "
                "This is insecure and should only be used during initial migration.",
                SecurityWarning
            )
    
    def disable_env_fallback(self):
        """Disable environment variable fallback (call after full migration)"""
        self._fallback_to_env = False
        # Clear any secrets from os.environ that were copied
        for key in list(os.environ.keys()):
            if any(s in key.upper() for s in ['API_KEY', 'SECRET', 'TOKEN', 'PRIVATE_KEY']):
                del os.environ[key]
        print("🔐 Environment variable fallback disabled - vault only mode")
```

**Priority:** P2 - Fix within 2 weeks

---

### 10. **MEDIUM: Insecure Temporary File Creation in Sandbox**

**Location:** `plugins/selfimprove/autonomous_coder.py`

**Lines:** 113-115, 138-139

**Issue:**
```python
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
    tmp.write(code)
    tmp_path = tmp.name
```

**Impact:** 
- `delete=False` requires manual cleanup (done in finally block, but risky)
- Files are created with default permissions (readable by other users on shared systems)
- Predictable naming could allow symlink attacks on some systems

**Remediation:**
```python
import tempfile
import os

def _sandbox_check_file(self, code: str, filepath: str) -> Dict[str, Any]:
    # Create temp file with restrictive permissions
    fd, tmp_path = tempfile.mkstemp(suffix='.py', prefix='alleybot_sandbox_')
    try:
        # Set permissions before writing (owner only)
        os.fchmod(fd, 0o600)
        
        # Write and close
        with os.fdopen(fd, 'w') as f:
            f.write(code)
        fd = None  # Mark as closed
        
        # ... rest of checks ...
        
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
```

**Priority:** P3 - Fix within 1 month

---

## Low Severity / Best Practice Issues

### 11. **LOW: Debug Mode Enabled in Flask (A2A Server)**

**Location:** `plugins/a2a/a2a_server.py`

**Line:** 173-178

**Current:**
```python
self._a2a_app.run(
    host=self._a2a_host,
    port=self._a2a_port,
    debug=False,  # Correctly disabled
    use_reloader=False,  # Correctly disabled
)
```

**Status:** ✅ **Already correct** - Debug mode is properly disabled.

**Recommendation:** Add explicit environment check to prevent accidental enable:
```python
# At startup
if os.getenv('FLASK_DEBUG') == '1':
    raise RuntimeError(
        "FLASK_DEBUG=1 is not allowed for A2A server security. "
        "Remove this environment variable."
    )
```

**Priority:** P3 - Informational

---

### 12. **LOW: Missing Content Security Policy Headers**

**Location:** `plugins/a2a/a2a_server.py`

**Issue:** No CSP headers are set on HTTP responses.

**Remediation:**
```python
@self._a2a_app.after_request
def add_security_headers(response):
    # Existing CORS headers...
    
    # Add security headers
    response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response
```

**Priority:** P3 - Informational

---

### 13. **LOW: Dependency Version Pinning**

**Location:** `requirements.txt`

**Issue:** Several dependencies lack strict version pinning:

```
requests
python-dotenv
flask
schedule
python-telegram-bot
aiohttp
web3
PyYAML
```

**Impact:** Supply chain attacks via dependency confusion or malicious updates.

**Remediation:**
```
requests>=2.31.0,<3.0.0
python-dotenv>=1.0.0,<2.0.0
flask>=2.3.0,<3.0.0
schedule>=1.2.0,<2.0.0
python-telegram-bot>=20.0,<21.0
aiohttp>=3.8.0,<4.0.0
web3>=6.0.0,<7.0.0
PyYAML>=6.0.0,<7.0.0
```

**Priority:** P3 - Fix at next maintenance window

---

### 14. **LOW: Encryption Key Storage**

**Location:** `src/agentic/enhanced_memory.py`

**Lines:** 93-103

**Issue:**
```python
def _load_or_create_key(self) -> Fernet:
    if self.key_file.exists():
        with open(self.key_file, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        os.chmod(self.key_file, 0o600)
```

**Impact:** 
- Key file is created if missing (transparent recreation)
- No detection of missing key (potential data loss scenario)
- No HSM or external key management integration

**Remediation:**
```python
def _load_or_create_key(self) -> Fernet:
    if self.key_file.exists():
        with open(self.key_file, 'rb') as f:
            key = f.read()
        
        # Validate key format
        try:
            return Fernet(key)
        except ValueError as e:
            raise RuntimeError(
                f"Invalid encryption key in {self.key_file}: {e}. "
                "This may indicate tampering or corruption."
            ) from e
    else:
        # In production, fail instead of auto-creating
        if os.getenv('ENVIRONMENT') == 'production':
            raise RuntimeError(
                f"Encryption key not found at {self.key_file}. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; "
                "open('{self.key_file}', 'wb').write(Fernet.generate_key())\""
            )
        
        # In development, auto-create with warning
        import warnings
        warnings.warn(
            f"Auto-creating encryption key at {self.key_file}. "
            "This is fine for development but NOT for production!",
            UserWarning
        )
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        os.chmod(self.key_file, 0o600)
        return Fernet(key)
```

**Priority:** P3 - Informational

---

## Security Best Practices Assessment

### ✅ Strengths

1. **Security Filter Implementation** (`security_filter.py`)
   - Comprehensive pattern matching for API keys
   - Automatic redaction of sensitive values
   - Pattern detection for Telegram tokens, Ethereum keys, etc.

2. **Telegram Authentication** (`plugins/telegram/telegram.py`)
   - Owner-only access enforcement via `_verify_owner()`
   - Hardcoded owner ID check prevents unauthorized access

3. **Code Safety Validation** (`plugins/selfimprove/test_gate.py`)
   - Blocks `eval()`, `exec()`, `os.system()`, `shell=True`
   - AST parsing for syntax validation
   - Sandboxed execution in temporary directories

4. **A2A Security Pipeline** (`plugins/a2a/a2a_server.py`)
   - Identity verification
   - Rate limiting (on most endpoints)
   - Task sanitization before execution
   - Security filter on all outputs

5. **Encrypted Storage** (`src/agentic/enhanced_memory.py`)
   - Fernet symmetric encryption for sensitive data
   - Proper file permissions (0o600) on key files

6. **Web3 Provider Security** (`plugins/onchain/web3_provider.py`)
   - No private key storage (read-only operations)
   - Address checksum validation
   - No transaction signing capability

---

### ❌ Areas for Improvement

1. **Logging Inconsistency**
   - Mix of `print()` statements and proper logging
   - No centralized log format
   - Some errors may leak to stdout in production

2. **Error Handling**
   - Bare `except:` blocks in several places
   - Some error messages not sanitized before display

3. **Configuration Management**
   - No validation of required environment variables at startup
   - Missing config schema validation

4. **Session Management**
   - No formal session concept for Telegram interactions
   - State persistence relies on in-memory structures

---

## Remediation Roadmap

### Week 1 (Critical Fixes)
- [ ] Replace `eval()` with `json.loads()` in `secret_manager.py`
- [ ] Add path sanitization to `autonomous_coder.py` subprocess calls
- [ ] Add HMAC verification to pickle operations or migrate to JSON

### Week 2 (High Priority)
- [ ] Implement strict task type allowlist in A2A server
- [ ] Fix CORS configuration with explicit origin list
- [ ] Sanitize all Telegram error messages through security filter
- [ ] Add rate limiting to streaming endpoint

### Week 3-4 (Medium Priority)
- [ ] Externalize hardcoded payment address
- [ ] Disable environment variable fallback by default
- [ ] Secure temporary file creation with proper permissions
- [ ] Pin all dependency versions

### Month 2 (Low Priority / Best Practices)
- [ ] Add comprehensive security headers
- [ ] Implement proper logging framework
- [ ] Add CSP headers
- [ ] Production-mode key management

---

## Compliance Notes

### GDPR / Data Privacy
- ✅ No PII storage identified in core functionality
- ⚠️ Memory system stores conversation history (needs data retention policy)
- ⚠️ Audit logs may contain agent identifiers (review retention period)

### SOC 2 Considerations
- ⚠️ Need formal access control policy documentation
- ⚠️ Encryption key management needs HSM consideration
- ✅ Audit logging present but needs formal retention policy

### Blockchain / Web3 Security
- ✅ No private key exposure in code
- ✅ Read-only blockchain operations
- ✅ Address validation before queries
- ⚠️ Consider rate limiting on blockchain endpoints to prevent RPC abuse

---

## Appendix: Tools Used

- **Static Analysis:** grep-based pattern matching, manual code review
- **Dependencies:** requirements.txt analysis (recommend `safety` or `pip-audit` for automated CVE checking)
- **Test Coverage:** 160 tests identified (good coverage)

---

## Sign-off

**Auditor:** Cascade (AI Security Engineer)  
**Date:** February 11, 2026  
**Classification:** Internal - Development Team  
**Next Audit Recommended:** After critical fixes implemented (30 days)

---

*This audit was generated using automated analysis tools and manual code review. While every effort was made to identify security issues, this report should not be considered exhaustive. Penetration testing and dynamic analysis are recommended for production deployments.*
