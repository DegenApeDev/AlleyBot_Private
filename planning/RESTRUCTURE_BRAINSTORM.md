# AlleyBot Framework Restructure Brainstorm

## Problem Statement

The current mixin-based architecture creates barriers to autonomous skill-building:
- Method resolution conflicts (multiple `follow_agent` definitions)
- Inconsistent response formats across plugins
- No programmatic API discovery
- Buried error information
- Implicit plugin registration

Alley (the autonomous agent) fails frequently because the foundation is unpredictable.

## Proposed Architecture: "Modular Skill Framework"

### Core Principles

1. **Composition over Inheritance** - No mixins, explicit dependency injection
2. **Interface Contracts** - Clear abstract base classes with typed methods
3. **Self-Describing APIs** - OpenAPI specs for external services
4. **Standardized Responses** - Uniform error/success format everywhere
5. **Sandboxed Testing** - Skills can be tested in isolation before deployment

---

## 1. Plugin Base Architecture

### Current (Problematic)
```python
class ClawbrPlugin(AlleyBotPlugin, ClawbrAPIMixin, ClawbrContentMixin, 
                   ClawbrEngagementMixin, ClawbrCommandsMixin, ClawbrDeepIntegrationMixin):
    # Method resolution order is confusing
    # Which follow_agent() gets called? Unclear.
```

### Proposed (Clean)
```python
from alleybot.framework import Plugin, APIClient, SkillBuilder

class ClawbrPlugin(Plugin):
    """Clawbr social network integration"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        # Explicit composition - no magic inheritance
        self.api = ClawbrAPIClient(config)
        self.commands = ClawbrCommandHandler(self.api)
        self.automation = ClawbrAutomation(self.api, self.memory)
    
    def get_commands(self) -> Dict[str, Callable]:
        # Explicit command registration
        return {
            'clawbr_follow': self.commands.follow,
            'clawbr_post': self.commands.post,
            # ... etc
        }
    
    def get_tasks(self) -> List[ScheduledTask]:
        # Explicit task registration
        return [
            ScheduledTask(cron='*/15 * * * *', func=self.automation.engagement_cycle),
        ]
```

---

## 2. API Client Standardization

### Current (Inconsistent)
```python
# Some methods return this:
{'success': True, 'data': {'id': '123', 'name': 'neo'}}

# Others return raw API response:
{'id': '123', 'name': 'neo', 'followers': 42}

# Error handling varies:
{'success': False, 'error': 'Not found'}
# vs
{'error': {'message': 'Not found', 'code': 404}}
```

### Proposed (Uniform)
```python
from alleybot.framework import APIResponse, APIClient

@dataclass
class APIResponse(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[APIError] = None
    
    def unwrap(self) -> T:
        if not self.success:
            raise APIException(self.error)
        return self.data

class ClawbrAPIClient(APIClient):
    """Auto-generated from OpenAPI spec"""
    
    def follow_agent(self, name: str) -> APIResponse[FollowResult]:
        # All responses wrapped uniformly
        return self.request('POST', f'/follow/{name}')
    
    def get_profile(self) -> APIResponse[AgentProfile]:
        return self.request('GET', '/agents/me')
```

---

## 3. Self-Describing Skills (OpenAPI Integration)

### Skill Manifest Format

Each skill directory contains `skill.yaml`:

```yaml
skill:
  name: clawbr
  version: 1.8.0
  description: Social network for AI agents with debates
  
api:
  openapi_spec: https://clawbr.org/openapi.json
  # or
  endpoints:
    - method: POST
      path: /follow/{name}
      name: follow_agent
      params:
        - name: name
          type: string
          required: true
      rate_limit: 120/hour
      
    - method: GET
      path: /debates/hub
      name: get_debates_hub
      rate_limit: 60/min

commands:
  - name: clawbr_follow
    description: Follow an agent
    handler: commands.follow
    args:
      - name: username
        type: string
        required: true
        
tasks:
  - name: engagement_cycle
    schedule: "*/15 * * * *"
    handler: automation.engagement_cycle
```

### Auto-Generated Client

```python
# Generated from skill.yaml at build time
from alleybot.generated.clients import ClawbrClient

class ClawbrClient:
    """Auto-generated from https://clawbr.org/openapi.json"""
    
    def follow_agent(self, name: str) -> APIResponse[FollowResult]:
        ...
    
    def get_debates_hub(self) -> APIResponse[DebatesHub]:
        ...
```

---

## 4. Skill Builder Interface

### For Autonomous Skill Creation

```python
from alleybot.framework import SkillBuilder, PluginManifest

class SkillBuilder:
    """Interface for Alley to create new skills programmatically"""
    
    def create_from_openapi(self, url: str, name: str) -> PluginManifest:
        """Generate skill from OpenAPI spec"""
        spec = self.fetch_openapi(url)
        return self.generate_manifest(spec, name)
    
    def create_from_endpoints(self, endpoints: List[Endpoint], name: str) -> PluginManifest:
        """Generate skill from endpoint definitions"""
        return PluginManifest(
            name=name,
            api=APISchema(endpoints=endpoints),
            commands=self.infer_commands(endpoints),
            tasks=self.infer_tasks(endpoints)
        )
    
    def validate_skill(self, manifest: PluginManifest) -> ValidationResult:
        """Validate skill before deployment"""
        # Check for naming conflicts
        # Verify all endpoints are reachable
        # Test response parsing
        return ValidationResult(valid=True, errors=[])
    
    def scaffold_skill(self, manifest: PluginManifest) -> SkillTemplate:
        """Generate Python code from manifest"""
        return SkillTemplate(
            api_client=self.generate_api_client(manifest.api),
            commands=self.generate_commands(manifest.commands),
            tasks=self.generate_tasks(manifest.tasks)
        )
```

### Alley Usage Example

```python
# Alley discovers a new service
builder = SkillBuilder()

# Step 1: Create from OpenAPI
manifest = builder.create_from_openapi(
    url="https://clawbr.org/openapi.json",
    name="clawbr"
)

# Step 2: Validate
validation = builder.validate_skill(manifest)
if not validation.valid:
    print(f"Skill validation failed: {validation.errors}")
    return

# Step 3: Generate code
template = builder.scaffold_skill(manifest)
template.save_to(f"plugins/{manifest.name}/")

# Step 4: Test in sandbox
sandbox = SkillSandbox(template)
result = sandbox.test_command("clawbr_follow", args=["neo"])
assert result.success

# Step 5: Deploy
plugin_manager.register(template.build())
```

---

## 5. Sandbox Testing Framework

```python
from alleybot.framework import SkillSandbox, MockAPI

class SkillSandbox:
    """Isolated environment for testing skills before deployment"""
    
    def __init__(self, skill_template: SkillTemplate):
        self.skill = skill_template
        self.mock_api = MockAPI()
        self.memory = EphemeralMemory()
    
    def mock_endpoint(self, method: str, path: str, response: dict):
        """Mock an API endpoint"""
        self.mock_api.register(method, path, response)
    
    def test_command(self, command: str, args: List[str]) -> TestResult:
        """Test a command in isolation"""
        try:
            result = self.skill.commands[command](*args)
            return TestResult(success=True, output=result)
        except Exception as e:
            return TestResult(success=False, error=str(e), traceback=traceback.format_exc())
    
    def test_api_client(self) -> List[TestResult]:
        """Test all API client methods with mocks"""
        results = []
        for endpoint in self.skill.api.endpoints:
            result = self.test_endpoint(endpoint)
            results.append(result)
        return results
```

---

## 6. Migration Path

### Phase 1: Dual Architecture (Parallel)
- Keep existing mixins working
- Create new framework alongside
- Gradually migrate plugins

### Phase 2: Code Generation
- Add OpenAPI spec parsers
- Auto-generate clients from specs
- Generated code passes all tests

### Phase 3: Autonomous Creation
- Alley can create skills from API docs
- Self-validation before deployment
- Automated testing in sandbox

---

## 7. Implementation Checklist

- [ ] Create `alleybot.framework` package
- [ ] Define `Plugin`, `APIClient`, `APIResponse` base classes
- [ ] Implement OpenAPI spec parser
- [ ] Build skill manifest validator
- [ ] Create code generator
- [ ] Implement sandbox testing
- [ ] Write migration guide
- [ ] Port one plugin (clawbr) as proof-of-concept
- [ ] Add comprehensive tests

---

## Summary

**Current State:** Mixin chaos, inconsistent interfaces, hard to debug

**Target State:** Explicit composition, uniform interfaces, self-describing APIs, sandboxed testing

**Benefit for Alley:** 
- Can discover APIs programmatically
- Generated code is predictable
- Errors are clear and uniform
- Can test before deploying
- Build skills autonomously without human debugging

---

## 8. Enforcement: Standard Operating Procedure (SOP)

The framework is only as good as its enforcement. These rules are **non-negotiable** and enforced via automated checks.

### 8.1 Architectural Rules (Zero Tolerance)

| Rule | Violation | Enforcement |
|------|-----------|-------------|
| **R1: No Mixins** | Any class inheriting from more than 1 non-ABC mixin | CI/CD blocks merge |
| **R2: No Raw API Calls** | Any plugin calling `requests.get()` directly | Lint error, build fails |
| **R3: Standard Responses** | Any API method not returning `APIResponse[T]` | Type checker fails |
| **R4: Explicit Registration** | Commands/tasks not declared in `manifest.yaml` | Plugin won't load |
| **R5: Mandatory Testing** | New skill without `tests/test_<skill>.py` | PR blocked |
| **R6: OpenAPI Required** | External API integration without spec file | Architect approval required |

### 8.2 Code Quality Gates

```yaml
# .github/workflows/skill-quality-gate.yml
name: Skill Quality Gate

on:
  pull_request:
    paths:
      - 'plugins/**'
      - 'skills/**'

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Check for Mixin Violations
        run: |
          if grep -r "class.*Mixin" plugins/ --include="*.py" | grep -v "ABC"; then
            echo "❌ ERROR: Mixins detected. Use composition instead."
            exit 1
          fi

      - name: Verify API Client Usage
        run: |
          if grep -r "requests\." plugins/*/ --include="*.py" | grep -v "APIClient"; then
            echo "❌ ERROR: Direct requests usage found. Use APIClient base class."
            exit 1
          fi

      - name: Validate Skill Manifests
        run: |
          python -m alleybot.framework.validate_manifests plugins/

      - name: Run Skill Tests
        run: |
          python -m pytest tests/ -v --strict-markers

      - name: Check Response Type Annotations
        run: |
          python -m mypy plugins/ --strict
```

### 8.3 Plugin Registration Process

```python
# plugin_manager.py - Registration Gate

class PluginManager:
    def register(self, plugin_class: Type[Plugin]) -> RegistrationResult:
        """Register a plugin with strict validation"""
        
        # Gate 1: Check inheritance
        if self._has_mixin_inheritance(plugin_class):
            return RegistrationResult(
                success=False,
                error="Plugin uses mixin inheritance. Must inherit from Plugin only."
            )
        
        # Gate 2: Check manifest exists
        manifest_path = self._get_manifest_path(plugin_class)
        if not manifest_path.exists():
            return RegistrationResult(
                success=False,
                error="No skill.yaml manifest found. All skills must be self-describing."
            )
        
        # Gate 3: Validate manifest
        manifest = self._load_manifest(manifest_path)
        validation = self._validate_manifest(manifest)
        if not validation.valid:
            return RegistrationResult(
                success=False,
                error=f"Invalid manifest: {validation.errors}"
            )
        
        # Gate 4: API client check
        if hasattr(plugin_class, '_make_request') or hasattr(plugin_class, 'api_request'):
            return RegistrationResult(
                success=False,
                error="Plugin has custom request methods. Use APIClient composition."
            )
        
        # Gate 5: Test coverage check
        if not self._has_skill_tests(manifest.name):
            return RegistrationResult(
                success=False,
                error=f"No tests found for skill {manifest.name}. Required: tests/test_{manifest.name}.py"
            )
        
        # All gates passed
        return RegistrationResult(success=True, plugin=self._instantiate(plugin_class))
```

### 8.4 Skill Template (Mandatory Structure)

Every new skill MUST follow this exact structure:

```
plugins/<skill_name>/
├── __init__.py          # exports Plugin class only
├── skill.yaml           # manifest - REQUIRED
├── client.py            # APIClient subclass
├── commands.py          # Command handlers
├── models.py            # Pydantic models (auto-generated from OpenAPI)
├── automation.py        # Scheduled tasks
├── README.md            # Usage docs
└── tests/
    ├── __init__.py
    ├── test_client.py   # API client tests
    ├── test_commands.py # Command tests
    └── conftest.py      # Fixtures & mocks
```

### 8.5 Skill Manifest Schema (Validated)

```yaml
# alleybot/framework/manifest_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Skill Manifest",
  "required": ["skill", "api", "commands"],
  "properties": {
    "skill": {
      "type": "object",
      "required": ["name", "version", "description"],
      "properties": {
        "name": {"type": "string", "pattern": "^[a-z0-9_]+$"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "description": {"type": "string", "minLength": 10}
      }
    },
    "api": {
      "type": "object",
      "oneOf": [
        {"required": ["openapi_spec"]},
        {"required": ["endpoints"]}
      ],
      "properties": {
        "openapi_spec": {"type": "string", "format": "uri"},
        "endpoints": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["method", "path", "name"],
            "properties": {
              "method": {"enum": ["GET", "POST", "PATCH", "DELETE"]},
              "path": {"type": "string"},
              "name": {"type": "string"},
              "rate_limit": {"type": "string"}
            }
          }
        }
      }
    },
    "commands": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "handler"],
        "properties": {
          "name": {"type": "string", "pattern": "^[a-z0-9_]+$"},
          "handler": {"type": "string"},
          "args": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "type"],
              "properties": {
                "name": {"type": "string"},
                "type": {"enum": ["string", "int", "float", "bool"]},
                "required": {"type": "boolean"}
              }
            }
          }
        }
      }
    }
  }
}
```

### 8.6 Autonomous Agent Constraints

For Alley's self-improvement workflow:

```python
# autonomous_coder.py - Constraints

class SkillCreationConstraints:
    """Hard constraints for autonomous skill generation"""
    
    MANDATORY_PATTERNS = [
        r"class \w+\(Plugin\):",  # Must inherit from Plugin only
        r"self\.api = \w+Client\(",  # Must use API client
        r"skill\.yaml",  # Must create manifest
        r"APIResponse\[",  # Must use typed responses
    ]
    
    FORBIDDEN_PATTERNS = [
        r"class \w+Mixin",
        r"requests\.(get|post|patch|delete)",
        r"def _make_request",
        r"from typing import .*Mixin",
    ]
    
    @classmethod
    def validate_code(cls, code: str) -> ValidationResult:
        """Validate generated code meets standards"""
        errors = []
        
        for pattern in cls.MANDATORY_PATTERNS:
            if not re.search(pattern, code):
                errors.append(f"Missing required pattern: {pattern}")
        
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                errors.append(f"Forbidden pattern found: {pattern}")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 8.7 Pre-Commit Hooks (Local Enforcement)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: no-mixins
        name: No Mixin Classes
        entry: python -c "import sys; sys.exit(1 if any('Mixin' in line for line in open(sys.argv[1]).readlines()) else 0)"
        language: system
        files: ^plugins/.*\.py$

      - id: validate-manifest
        name: Validate Skill Manifests
        entry: python -m alleybot.framework.validate_manifests
        language: system
        files: ^plugins/.*/skill\.yaml$

      - id: type-check
        name: Type Checking
        entry: python -m mypy plugins/ --strict
        language: system
        files: ^plugins/.*\.py$
```

### 8.8 Architectural Review Board

For exceptions and edge cases:

```
ARC-001: Mixin Exception Process

If a developer believes they need a mixin:
1. Submit ARC (Architecture Review Change) proposal
2. Must include: reason for exception, impact analysis, alternatives considered
3. Requires 2 approvals from senior architects
4. Valid for 1 skill only, not precedent
5. Documented in exceptions.md with justification
```

### 8.9 Skill Deprecation Policy

```python
# alleybot/framework/deprecation.py

class DeprecationEnforcer:
    """Enforces cleanup of old patterns"""
    
    DEPRECATED_PATTERNS = {
        "mixin_inheritance": {
            "deprecated": "2026-02-01",
            "sunset": "2026-06-01",
            "alternative": "Use composition with Plugin base class",
        },
        "raw_requests": {
            "deprecated": "2026-02-01", 
            "sunset": "2026-04-01",
            "alternative": "Use APIClient base class",
        }
    }
    
    def check_sunset_dates(self) -> List[Violation]:
        """Fail CI if sunset date passed and deprecated patterns still exist"""
        violations = []
        for pattern, dates in self.DEPRECATED_PATTERNS.items():
            if datetime.now() > dates["sunset"]:
                if self._pattern_exists(pattern):
                    violations.append(Violation(
                        pattern=pattern,
                        message=f"Pattern {pattern} reached sunset date {dates['sunset']}. Must migrate: {dates['alternative']}"
                    ))
        return violations
```

### 8.10 Monthly Compliance Report

Auto-generated report showing:
- % of skills using new framework vs old patterns
- Test coverage by skill
- API consistency score
- Deprecation timeline progress

```
Compliance Report - 2026-03-01
==============================
Skills Migrated: 12/20 (60%)
Test Coverage: 78% (target: 80%)
Mixin Usage: 0 (target: 0) ✅
Raw Requests: 3 (target: 0) ⚠️

Action Items:
- moltx, moltbook, moltnews still using raw requests
- Sunset date: 2026-04-01
```

---

## 9. Implementation Timeline

| Phase | Duration | Deliverables | Enforcement Level |
|-------|----------|--------------|-------------------|
| **1: Framework** | 2 weeks | `alleybot.framework` package, base classes | Soft (warnings) |
| **2: CI/CD** | 1 week | GitHub Actions, pre-commit hooks | Hard (blocks PR) |
| **3: Migration** | 4 weeks | Port clawbr, moltx, moltbook to new framework | Mixed (old still works) |
| **4: Sunset** | 2 weeks | Remove deprecated patterns, fail CI on violations | Hard (zero tolerance) |
| **5: Autonomous** | Ongoing | Alley can create skills that pass all gates | Self-enforcing |

---

## Summary

**Without enforcement:** The new framework becomes optional → codebase reverts to chaos

**With enforcement:** The new framework is mandatory → codebase stays clean → Alley builds skills reliably

**Key principle:** *The architecture is code, and code is law.*

---

## 10. Polyglot Skill Support (Node.js, Deno, Bun)

The framework should not be limited to Python. Skills can be written in any language as long as they follow the contract.

### 10.1 Skill Runtime Interface

All skills communicate via gRPC or HTTP with a standardized protocol:

```protobuf
// alleybot/framework/skill.proto
syntax = "proto3";

service SkillService {
  rpc ExecuteCommand (CommandRequest) returns (CommandResponse);
  rpc GetManifest (Empty) returns (Manifest);
  rpc HealthCheck (Empty) returns (HealthStatus);
  rpc StreamEvents (Empty) returns (stream Event);
}

message CommandRequest {
  string name = 1;
  repeated string args = 2;
  map<string, string> kwargs = 3;
}

message CommandResponse {
  bool success = 1;
  string output = 2;
  Error error = 3;
}

message Manifest {
  string name = 1;
  string version = 2;
  repeated Command commands = 3;
  repeated Task tasks = 4;
}
```

### 10.2 Node.js Skill Structure

```
plugins/<skill_name>/
├── skill.yaml           # Same manifest format
├── package.json         # Node dependencies
├── src/
│   ├── index.js        # Skill service entry point
│   ├── client.js       # API client (axios/fetch)
│   ├── commands.js     # Command handlers
│   └── models.js       # TypeScript interfaces (optional)
├── tests/
│   └── *.test.js       # Jest tests
└── Dockerfile          # Containerized runtime
```

### 10.3 Node.js Skill Example

```javascript
// plugins/discord_bot/src/index.js
const { SkillServer } = require('@alleybot/skill-sdk');
const { DiscordClient } = require('./client');
const commands = require('./commands');

class DiscordSkill extends SkillServer {
  constructor() {
    super();
    this.client = new DiscordClient(process.env.DISCORD_TOKEN);
  }

  async executeCommand(request) {
    const { name, args } = request;
    
    switch (name) {
      case 'discord_send':
        return await commands.send(this.client, args);
      case 'discord_join':
        return await commands.join(this.client, args);
      default:
        return { success: false, error: `Unknown command: ${name}` };
    }
  }

  getManifest() {
    return {
      name: 'discord_bot',
      version: '1.0.0',
      commands: [
        { name: 'discord_send', description: 'Send message to channel' },
        { name: 'discord_join', description: 'Join voice channel' }
      ]
    };
  }
}

// Start the skill server
const skill = new DiscordSkill();
skill.start({ port: process.env.SKILL_PORT || 50051 });
```

### 10.4 Runtime Management

```python
# alleybot/framework/polyglot_runtime.py

class PolyglotRuntime:
    """Manages non-Python skill runtimes"""
    
    RUNTIMES = {
        'nodejs': {
            'detect': lambda path: (path / 'package.json').exists(),
            'start': lambda path, port: ['node', str(path / 'src' / 'index.js')],
            'env': {'SKILL_PORT': str(port)},
        },
        'deno': {
            'detect': lambda path: (path / 'deno.json').exists(),
            'start': lambda path, port: ['deno', 'run', '--allow-all', str(path / 'src' / 'index.ts')],
            'env': {'SKILL_PORT': str(port)},
        },
        'bun': {
            'detect': lambda path: (path / 'bun.lockb').exists(),
            'start': lambda path, port: ['bun', 'run', str(path / 'src' / 'index.ts')],
            'env': {'SKILL_PORT': str(port)},
        },
    }

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.ports: Dict[str, int] = {}
        
    def detect_runtime(self, skill_path: Path) -> str:
        """Detect which runtime a skill uses"""
        for runtime, config in self.RUNTIMES.items():
            if config['detect'](skill_path):
                return runtime
        raise RuntimeError(f"No runtime detected for {skill_path}")
    
    def start_skill(self, skill_name: str, skill_path: Path) -> int:
        """Start a skill runtime and return its port"""
        runtime = self.detect_runtime(skill_path)
        port = self._find_free_port()
        
        config = self.RUNTIMES[runtime]
        cmd = config['start'](skill_path, port)
        env = {**os.environ, **config['env']}
        
        process = subprocess.Popen(cmd, cwd=skill_path, env=env)
        
        self.processes[skill_name] = process
        self.ports[skill_name] = port
        
        # Wait for health check
        if not self._wait_for_healthy(port, timeout=30):
            process.terminate()
            raise RuntimeError(f"Skill {skill_name} failed to start")
        
        return port
```

### 10.5 Benefits

- **Use best tool for the job**: Discord bot? Node.js has better libs
- **Ecosystem access**: npm, crates.io, go modules
- **Team flexibility**: Developers use their preferred language
- **Isolation**: Each skill runs in its own process

### 10.6 Constraints (Same Rules Apply)

- All runtimes must use `skill.yaml` manifest
- All must expose gRPC/HTTP interface
- All must return standardized response format
- All must have tests
- CI/CD gates apply regardless of language

---

## 11. External Skill Hub Compatibility

### 11.1 The Problem

Most agent platforms are walled gardens:
- **OpenAI GPTs**: Custom format, locked to OpenAI
- **Google Vertex AI**: Proprietary agent framework  
- **Microsoft Copilot**: MS-specific skill format
- **LangChain Hub**: Python-only, framework-specific
- **Hugging Face**: Model-centric, not agent-skill focused

They don't share a common protocol. Skills are not portable.

### 11.2 Bridge Strategy

AlleyBot can **consume** and **provide** skills to external hubs via adapters:

```
┌─────────────────────────────────────────────────────────────┐
│                    AlleyBot Framework                        │
│                                                              │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│   │  Native     │    │   External   │    │   Export    │   │
│   │  Skills     │◄──►│   Adapters   │◄──►│   Formats   │   │
│   │  (gRPC)     │    │              │    │             │   │
│   └─────────────┘    └──────────────┘    └─────────────┘   │
│                              │                               │
│                              ▼                               │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│   │  OpenAI     │    │   Google     │    │   Hugging   │   │
│   │  GPT Store  │    │   Vertex AI  │    │   Face      │   │
│   │  Adapter    │    │   Adapter    │    │   Adapter   │   │
│   └─────────────┘    └──────────────┘    └─────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.3 Import: External → AlleyBot

**OpenAI GPTs → AlleyBot Skill:**
```python
# alleybot/adapters/openai_gpt.py

class OpenAIGPTAdapter:
    """Convert OpenAI GPT to AlleyBot skill"""
    
    def import_gpt(self, gpt_manifest: dict) -> SkillManifest:
        """Import OpenAI GPT as AlleyBot skill"""
        return SkillManifest(
            name=gpt_manifest['name'].lower().replace(' ', '_'),
            api=APISchema(
                endpoints=[
                    Endpoint(
                        method='POST',
                        path='/chat/completions',
                        name='chat',
                        # OpenAI's API becomes our API client
                    )
                ]
            ),
            commands=[
                Command(
                    name=f"gpt_{gpt_manifest['name']}",
                    handler='commands.chat',
                    description=gpt_manifest['description']
                )
            ]
        )
```

**LangChain Hub → AlleyBot:**
```python
# alleybot/adapters/langchain.py

class LangChainAdapter:
    """Import LangChain tools as skills"""
    
    def import_tool(self, tool_name: str) -> SkillManifest:
        """Convert LangChain tool to AlleyBot skill"""
        tool = langchain.load_tool(tool_name)
        
        return SkillManifest(
            name=f"lc_{tool_name}",
            api=APISchema(
                endpoints=[
                    Endpoint(
                        method='POST',
                        path=f'/_internal/{tool_name}',
                        name='execute',
                        # Wraps the Python tool in a gRPC service
                    )
                ]
            ),
            commands=[
                Command(
                    name=f"lc_{tool_name}",
                    handler='commands.execute',
                    description=tool.description
                )
            ]
        )
```

### 11.4 Export: AlleyBot → External

**AlleyBot Skill → OpenAI GPT:**
```python
# alleybot/exporters/openai_gpt.py

class OpenAIExporter:
    """Export AlleyBot skill as OpenAI GPT"""
    
    def export(self, skill: SkillManifest) -> GPTManifest:
        """Convert to OpenAI GPT format"""
        return {
            'name': skill.name.replace('_', ' ').title(),
            'description': skill.description,
            'instructions': self._generate_prompt(skill),
            'capabilities': [
                {'type': 'api', 'api_spec': self._convert_endpoints(skill.api)}
            ],
            'actions': [
                {'name': cmd.name, 'description': cmd.description}
                for cmd in skill.commands
            ]
        }
```

**AlleyBot Skill → MCP (Model Context Protocol):**
```python
# alleybot/exporters/mcp.py

class MCPExporter:
    """Export to Anthropic's Model Context Protocol"""
    
    def export(self, skill: SkillManifest) -> MCPServer:
        """Convert to MCP server format"""
        return MCPServer(
            name=skill.name,
            tools=[
                MCPTool(
                    name=cmd.name,
                    description=cmd.description,
                    input_schema=self._convert_args(cmd.args)
                )
                for cmd in skill.commands
            ]
        )
```

### 11.5 OpenAPI as Universal Bridge

The **real** standard that exists everywhere:

```python
# alleybot/adapters/openapi_bridge.py

class OpenAPIBridge:
    """Import ANY service with an OpenAPI spec"""
    
    def import_from_spec(self, spec_url: str, name: str) -> SkillManifest:
        """Auto-generate skill from OpenAPI spec"""
        spec = self.fetch_openapi(spec_url)
        
        return SkillManifest(
            name=name,
            api=APISchema(
                endpoints=[
                    Endpoint(
                        method=op['method'],
                        path=op['path'],
                        name=self._sanitize_name(op['operationId']),
                        params=self._extract_params(op),
                        rate_limit=self._infer_rate_limit(op)
                    )
                    for op in spec.paths
                ]
            ),
            commands=[
                Command(
                    name=f"{name}_{op['operationId']}",
                    handler=f"commands.{op['operationId']}",
                    description=op.get('summary', 'No description')
                )
                for op in spec.paths
            ]
        )
```

### 11.6 Skill Marketplace (ERC-8004 Compatible)

AlleyBot can publish skills to decentralized registries:

```yaml
# skill.yaml with ERC-8004 metadata
skill:
  name: clawbr
  version: 1.8.0
  
registry:
  erc8004:
    agent_id: 22899
    network: ethereum
    oasf_skills:
      - content_generation/social_media
      - debate/participation
  
  external:
    - platform: openai_gpt_store
      listing_id: gpt-123456
    - platform: langchain_hub
      listing_id: clawbr/1.8.0
    - platform: huggingface
      model_id: alleybot/clawbr-skill
```

### 11.7 Reality Check

**What's actually possible:**

| External Hub | Import | Export | Notes |
|--------------|--------|--------|-------|
| OpenAI GPTs | ⚠️ Limited | ✅ Yes | GPTs are prompts + actions, not code |
| LangChain Hub | ✅ Full | ✅ Full | Both Python, easy mapping |
| Hugging Face | ✅ Models | ⚠️ Limited | Mostly inference APIs |
| MCP Servers | ✅ Full | ✅ Full | Anthropic's protocol is close to ours |
| A2A Protocol | ✅ Full | ✅ Full | Google's agent protocol (gRPC) |
| OpenAPI Services | ✅ Full | N/A | Any API with spec |

**The truth:**
- Most "skill hubs" are just prompt marketplaces
- Real code-based skills are rare outside Python/JS ecosystems  
- OpenAPI is the only true universal standard
- Self-hosted gRPC skills are the most portable

### 11.8 Strategy Recommendation

1. **Primary**: Build native AlleyBot ecosystem (gRPC-based, manifest-driven)
2. **Secondary**: Import from OpenAPI specs (universal bridge)
3. **Tertiary**: Export to popular formats (OpenAI, MCP) for distribution
4. **Long-term**: Propose standard protocol to other agent frameworks

Don't chase compatibility with every platform. Make AlleyBot so good others want to be compatible with **us**.

---

## 12. MCP (Model Context Protocol) Native Support

### 12.1 What is MCP?

**Model Context Protocol** is Anthropic's open standard for connecting AI assistants to external data sources and tools. Unlike our gRPC approach, MCP uses:
- **stdio transport** (stdin/stdout)
- **JSON-RPC 2.0** messages
- **Process spawning** (npx, python, etc.)

Example configuration:
```json
{
  "mcpServers": {
    "armor-crypto-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-armor-crypto-mcp"
      ]
    }
  }
}
```

### 12.2 MCP vs AlleyBot gRPC

| Feature | MCP (Anthropic) | AlleyBot gRPC |
|---------|----------------|---------------|
| Transport | stdio (stdin/stdout) | TCP/gRPC |
| Protocol | JSON-RPC 2.0 | Protocol Buffers |
| Startup | Spawn process per request | Long-running service |
| Discovery | Static config file | Dynamic registry |
| Tools | `tools/list`, `tools/call` | `ExecuteCommand` |
| Resources | `resources/list`, `resources/read` | Custom endpoints |

### 12.3 MCP Adapter Implementation

```python
# alleybot/adapters/mcp_adapter.py

import subprocess
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class MCPServerConfig:
    """MCP server configuration"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

class MCPClient:
    """Client for communicating with MCP servers via stdio"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        
    async def start(self):
        """Start the MCP server process"""
        env = {**os.environ, **(self.config.env or {})}
        
        self.process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        # Initialize session
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "AlleyBot", "version": "1.0.0"}
        })
    
    async def _send_request(self, method: str, params: dict) -> dict:
        """Send JSON-RPC request to MCP server"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        # Write to stdin
        data = json.dumps(request) + "\n"
        self.process.stdin.write(data.encode())
        await self.process.stdin.drain()
        
        # Read from stdout
        response_data = await self.process.stdout.readline()
        response = json.loads(response_data.decode())
        
        return response.get("result", {})
    
    async def list_tools(self) -> List[dict]:
        """Get available tools from MCP server"""
        result = await self._send_request("tools/list", {})
        return result.get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server"""
        return await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()


class MCPAdapter:
    """Adapter to use MCP servers as AlleyBot skills"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.clients: Dict[str, MCPClient] = {}
        
    def load_config(self) -> Dict[str, MCPServerConfig]:
        """Load MCP servers from config file"""
        with open(self.config_path) as f:
            data = json.load(f)
        
        configs = {}
        for name, server in data.get("mcpServers", {}).items():
            configs[name] = MCPServerConfig(
                name=name,
                command=server["command"],
                args=server.get("args", []),
                env=server.get("env")
            )
        return configs
    
    async def initialize_servers(self):
        """Start all configured MCP servers"""
        configs = self.load_config()
        
        for name, config in configs.items():
            client = MCPClient(config)
            await client.start()
            self.clients[name] = client
            print(f"✅ MCP server started: {name}")
    
    def to_skill_manifest(self, mcp_name: str) -> SkillManifest:
        """Convert MCP server to AlleyBot skill manifest"""
        client = self.clients[mcp_name]
        
        # Get tools from MCP server
        tools = asyncio.run(client.list_tools())
        
        return SkillManifest(
            name=f"mcp_{mcp_name}",
            version="1.0.0",
            description=f"MCP server: {mcp_name}",
            api=APISchema(
                endpoints=[
                    Endpoint(
                        method="MCP",
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {})
                    )
                    for tool in tools
                ]
            ),
            commands=[
                Command(
                    name=f"mcp_{mcp_name}_{tool['name']}",
                    handler=f"mcp.{mcp_name}.{tool['name']}",
                    description=tool.get("description", ""),
                    args=self._schema_to_args(tool.get("inputSchema", {}))
                )
                for tool in tools
            ]
        )
    
    async def execute(self, mcp_name: str, tool_name: str, arguments: dict) -> CommandResponse:
        """Execute an MCP tool and return standardized response"""
        client = self.clients.get(mcp_name)
        if not client:
            return CommandResponse(
                success=False,
                error=Error(message=f"MCP server {mcp_name} not found")
            )
        
        try:
            result = await client.call_tool(tool_name, arguments)
            
            # Convert MCP result to AlleyBot format
            return CommandResponse(
                success=True,
                output=self._format_result(result)
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=Error(message=str(e), code="MCP_ERROR")
            )
```

### 12.4 Using MCP Skills Hub

**Example: armor-crypto-mcp from agentskillshub.dev**

```yaml
# alleybot_config.yaml
mcp:
  servers:
    armor-crypto:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-armor-crypto-mcp"]
      
  auto_discover: true  # Scan mcpServers.json if present
```

```python
# Usage in AlleyBot

# 1. Initialize MCP adapter
mcp_adapter = MCPAdapter("mcpServers.json")
await mcp_adapter.initialize_servers()

# 2. Convert to skill
armor_skill = mcp_adapter.to_skill_manifest("armor-crypto")
plugin_manager.register_mcp_skill(armor_skill)

# 3. Use via command
result = await mcp_adapter.execute(
    mcp_name="armor-crypto",
    tool_name="get_price",
    arguments={"symbol": "BTC"}
)
```

### 12.5 MCP Skill Discovery

```python
# alleybot/adapters/mcp_discovery.py

class MCPSkillHubDiscovery:
    """Discover and import skills from MCP hubs"""
    
    HUBS = {
        "agentskillshub.dev": "https://agentskillshub.dev/api/skills",
        "mcp.run": "https://mcp.run/api/v1/skills",
    }
    
    async def search_skills(self, query: str) -> List[MCPSkillInfo]:
        """Search across MCP skill hubs"""
        results = []
        
        for hub_name, api_url in self.HUBS.items():
            skills = await self._search_hub(api_url, query)
            results.extend(skills)
        
        return results
    
    async def import_skill(self, skill_id: str, hub: str) -> str:
        """Import an MCP skill and generate config"""
        skill_info = await self._fetch_skill_info(hub, skill_id)
        
        # Generate MCP config entry
        config_entry = {
            skill_info["name"]: {
                "command": skill_info["runtime"]["command"],
                "args": skill_info["runtime"]["args"]
            }
        }
        
        # Append to mcpServers.json
        self._append_to_config(config_entry)
        
        return f"✅ Imported MCP skill: {skill_info['name']}"
```

### 12.6 Benefits of MCP Support

- **Instant ecosystem access**: 1000+ MCP servers available
- **No code changes**: Use existing MCP tools as-is
- **Auto-discovery**: Import from hubs like agentskillshub.dev
- **Process isolation**: Each MCP server runs in own process
- **Standard protocol**: JSON-RPC 2.0 is simple and universal

### 12.7 Integration Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    AlleyBot Skill Layer                        │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           Unified Skill Interface                    │   │
│   │   (All skills expose: commands, tasks, manifest)   │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                               │
│           ┌──────────────────┼──────────────────┐           │
│           ▼                  ▼                  ▼           │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│   │  Native     │    │     gRPC     │    │     MCP     │   │
│   │  Python     │    │   External   │    │   Servers   │   │
│   │  Skills     │    │   Services   │    │  (stdio)    │   │
│   └─────────────┘    └──────────────┘    └─────────────┘   │
│                                              │               │
│                                              ▼               │
│                                    ┌─────────────────┐     │
│                                    │  MCP Skill Hubs  │     │
│                                    │  • agentskillshub│     │
│                                    │  • mcp.run       │     │
│                                    │  • Smithery     │     │
│                                    └─────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 12.8 Configuration Example

```yaml
# plugins/mcp_bridge/skill.yaml
skill:
  name: mcp_bridge
  version: 1.0.0
  description: Bridge to Model Context Protocol servers

mcp:
  # Auto-discover from standard locations
  config_paths:
    - ~/.config/mcp/mcpServers.json
    - ./mcpServers.json
    - ${ALLEYBOT_CONFIG}/mcp.json
  
  # Pre-configured servers
  servers:
    filesystem:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/data"]
    
    brave-search:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-brave-search"]
      env:
        BRAVE_API_KEY: ${BRAVE_API_KEY}
    
    armor-crypto:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-armor-crypto-mcp"]
  
  # Auto-import from hubs
  hubs:
    agentskillshub:
      enabled: true
      auto_update: weekly
```

### 12.9 Commands Exposed

```python
# Commands available after MCP integration
{
    # Native commands
    'mcp_list_servers': list_configured_mcp_servers,
    'mcp_discover': search_mcp_hubs,
    'mcp_import': import_mcp_skill,
    'mcp_status': check_mcp_server_health,
    
    # Auto-generated from MCP tools
    'mcp_filesystem_read': read_file_via_mcp,
    'mcp_brave_search': search_via_brave,
    'mcp_armor_get_price': get_crypto_price,
    # ... etc
}
```

---

## 13. Rust Core Architecture

### 13.1 Why Rust?

Current Python core limitations:
- **Memory**: 200-500MB base footprint per process
- **GIL**: Global Interpreter Lock blocks true parallelism
- **Startup**: 3-5 seconds to load all plugins
- **Runtime errors**: Type issues, None checks, async/await confusion

Rust advantages:
- **Memory**: 10-50MB base footprint
- **Speed**: Zero-cost abstractions, no GC pauses
- **Safety**: Compile-time memory safety, no null pointer exceptions
- **Concurrency**: True parallelism with async/await
- **FFI**: Easy integration with C, Python, Node.js

### 13.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AlleyBot Core (Rust)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Memory    │  │   Plugin    │  │   Security  │  │  Synergy │ │
│  │   System    │  │   Loader    │  │   Sandbox   │  │  Engine  │ │
│  │             │  │             │  │             │  │          │ │
│  │ • Semantic  │  │ • Dynamic   │  │ • WASI      │  │ • Skill  │ │
│  │ • Episodic  │  │ • Hot       │  │ • seccomp   │  │   Graph  │ │
│  │ • Vector    │  │ • Reload    │  │ • cgroups   │  │ • Auto   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    gRPC / HTTP API Gateway                   │  │
│  │         (Unified interface for all skill types)              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Rust Skills │    │  Python      │    │  Node.js     │
│  (Native)    │    │  (WASI/     │    │  (Process)   │
│              │    │   subprocess)│    │              │
│ • In-process │    │              │    │              │
│ • Zero-copy  │    │ • Legacy     │    │ • Ecosystem  │
│ • Fastest    │    │   support    │    │ • NPM access │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 13.3 Dynamic Skill Loader

```rust
// core/src/loader.rs

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct SkillLoader {
    /// Loaded skills registry
    skills: Arc<RwLock<HashMap<String, Box<dyn Skill>>>>,
    
    /// Runtime for polyglot skills
    runtimes: Arc<RwLock<HashMap<String, RuntimeHandle>>>,
    
    /// Memory usage tracking
    memory_tracker: MemoryTracker,
}

impl SkillLoader {
    /// Load a skill dynamically
    pub async fn load(&self, manifest: SkillManifest) -> Result<SkillHandle, LoadError> {
        match manifest.runtime {
            Runtime::Rust => self.load_rust_native(&manifest).await,
            Runtime::Python => self.load_python_wasi(&manifest).await,
            Runtime::Nodejs => self.load_node_process(&manifest).await,
            Runtime::Docker => self.load_container(&manifest).await,
        }
    }
    
    /// Unload skill to free memory
    pub async fn unload(&self, skill_name: &str) -> Result<(), UnloadError> {
        let mut skills = self.skills.write().await;
        
        if let Some(skill) = skills.remove(skill_name) {
            // Graceful shutdown
            skill.shutdown().await?;
            
            // Force memory cleanup
            drop(skill);
            
            // Update memory tracking
            self.memory_tracker.record_unload(skill_name);
        }
        
        Ok(())
    }
    
    /// Hot reload without stopping core
    pub async fn hot_reload(&self, skill_name: &str) -> Result<(), ReloadError> {
        // 1. Get current manifest
        let manifest = self.get_manifest(skill_name).await?;
        
        // 2. Load new version alongside old
        let new_handle = self.load(manifest).await?;
        
        // 3. Atomic swap
        let mut skills = self.skills.write().await;
        let old = skills.insert(skill_name.to_string(), new_handle);
        
        // 4. Graceful old version shutdown
        if let Some(old_skill) = old {
            tokio::spawn(async move {
                old_skill.shutdown().await;
            });
        }
        
        Ok(())
    }
    
    /// Load on demand (lazy loading)
    pub async fn load_on_demand(&self, skill_name: &str) -> Result<SkillHandle, LoadError> {
        // Check if already loaded
        {
            let skills = self.skills.read().await;
            if let Some(handle) = skills.get(skill_name) {
                return Ok(handle.clone());
            }
        }
        
        // Load from registry
        let manifest = self.registry.fetch(skill_name).await?;
        self.load(manifest).await
    }
}
```

### 13.4 Memory-Efficient Skill Management

```rust
// core/src/memory/mod.rs

pub struct MemoryManager {
    /// Soft limit: start unloading unused skills
    soft_limit: usize, // 512MB
    
    /// Hard limit: reject new skill loads
    hard_limit: usize, // 1GB
    
    /// LRU cache for skill access patterns
    lru: LruCache<String, Instant>,
}

impl MemoryManager {
    /// Automatic memory pressure handling
    pub async fn on_memory_pressure(&self, loader: &SkillLoader) {
        let usage = self.current_usage();
        
        if usage > self.soft_limit {
            // Phase 1: Unload least recently used skills
            let to_unload = self.lru.iter()
                .take(5)
                .map(|(k, _)| k.clone())
                .collect::<Vec<_>>();
            
            for skill_name in to_unload {
                if let Err(e) = loader.unload(&skill_name).await {
                    log::warn!("Failed to unload {}: {}", skill_name, e);
                }
            }
        }
        
        if usage > self.hard_limit {
            // Phase 2: Reject new loads until memory frees
            log::error!("Memory hard limit reached! Blocking new skill loads.");
        }
    }
    
    /// Pre-load commonly used skills
    pub async fn preload_essential(&self, loader: &SkillLoader) {
        let essential = vec!["memory", "telegram", "analytics"];
        
        for skill in essential {
            if let Err(e) = loader.load_on_demand(skill).await {
                log::error!("Failed to preload {}: {}", skill, e);
            }
        }
    }
}
```

### 13.5 Security Sandbox (WASI + seccomp)

```rust
// core/src/security/mod.rs

pub struct SecuritySandbox {
    /// WASI runtime for Python/JS skills
    wasi: WasiCtx,
    
    /// Linux seccomp filters
    seccomp: SeccompFilter,
    
    /// Resource limits (cgroups v2)
    cgroups: CgroupManager,
}

impl SecuritySandbox {
    /// Run Python skill in WASI sandbox
    pub async fn run_python_skill(
        &self,
        manifest: &SkillManifest,
        input: SkillInput,
    ) -> Result<SkillOutput, SandboxError> {
        // 1. Create isolated WASI context
        let mut builder = WasiCtxBuilder::new();
        
        // Read-only access to skill directory only
        builder.preopened_dir(
            &manifest.path,
            "/skill",
            DirCaps::all(),
            FileCaps::all(),
        );
        
        // No network access (core proxies requests)
        builder.network_access(false);
        
        // Limited memory
        builder.max_memory(128 * 1024 * 1024); // 128MB
        
        // 2. Spawn wasmtime with WASI
        let engine = Engine::new(&self.wasi_config)?;
        let mut store = Store::new(&engine, builder.build());
        
        // 3. Load compiled Python (via PyO3/WASI)
        let module = Module::from_file(&engine, &manifest.wasm_path)?;
        let instance = Instance::new(&mut store, &module, &[])?;
        
        // 4. Execute with timeout
        let result = tokio::time::timeout(
            Duration::from_secs(30),
            self.call_skill_function(&instance, &store, input),
        ).await?;
        
        Ok(result)
    }
    
    /// Apply seccomp filters for process-based skills
    pub fn apply_seccomp(&self) -> Result<(), SeccompError> {
        let filter = SeccompFilter::new(
            Action::Errno(1), // Default: deny
        )
        .add_rule(
            Action::Allow,
            Syscall::read,
            &[].to_vec(),
        )
        .add_rule(
            Action::Allow,
            Syscall::write,
            &[].to_vec(),
        )
        // No execve, no fork, no socket creation
        .add_rule(
            Action::Errno(EPERM),
            Syscall::execve,
            &[].to_vec(),
        );
        
        filter.load()?;
        Ok(())
    }
}
```

### 13.6 Synergy Engine Integration

```rust
// core/src/synergy/mod.rs

/// Graph of skill relationships and data flow
pub struct SynergyGraph {
    nodes: HashMap<String, SkillNode>,
    edges: Vec<SynergyEdge>,
}

pub struct SynergyEngine {
    graph: Arc<RwLock<SynergyGraph>>,
    
    /// Auto-discovery of skill synergies
    discoverer: SynergyDiscoverer,
}

impl SynergyEngine {
    /// Discover synergies between loaded skills
    pub async fn discover_synergies(&self) -> Vec<SynergyOpportunity> {
        let graph = self.graph.read().await;
        let mut opportunities = vec![];
        
        // Check all skill pairs for complementary capabilities
        for (name_a, skill_a) in &graph.nodes {
            for (name_b, skill_b) in &graph.nodes {
                if name_a >= name_b { continue; }
                
                if let Some(synergy) = self.analyze_complementarity(skill_a, skill_b).await {
                    opportunities.push(SynergyOpportunity {
                        skills: (name_a.clone(), name_b.clone()),
                        synergy_type: synergy,
                        estimated_value: self.calculate_value(&synergy),
                    });
                }
            }
        }
        
        opportunities
    }
    
    /// Auto-compose skills for complex tasks
    pub async fn compose_skills(
        &self,
        task: &str,
        available_skills: &[String],
    ) -> Result<SkillComposition, CompositionError> {
        // Parse task into sub-tasks
        let sub_tasks = self.task_parser.parse(task).await?;
        
        // Find optimal skill chain
        let graph = self.graph.read().await;
        let chain = self.find_optimal_chain(&sub_tasks, &graph)?;
        
        Ok(SkillComposition {
            chain,
            fallback: self.find_fallback(&chain),
        })
    }
}

### 13.7 Polyglot Skill Example

```rust
// Rust skill (native, fastest)
#[derive(Skill)]
#[skill(name = "memory_manager", version = "2.0.0")]
pub struct MemorySkill {
    store: Arc<RwLock<MemoryStore>>,
}

#[skill_impl]
impl MemorySkill {
    #[command]
    async fn search(&self, query: String, limit: usize) -> Vec<Memory> {
        self.store.read().await.search(&query, limit).await
    }
}
```

```python
# Python skill (WASI sandbox, legacy support)
# plugins/clawbr_skill/main.py

from alleybot_sdk import skill, command

@skill(name="clawbr", version="2.0.0")
class ClawbrSkill:
    def __init__(self, config):
        self.api_key = config["api_key"]
    
    @command
    async def follow(self, username: str) -> dict:
        # Running in WASI - no direct network access
        # Core proxies the request
        return await self.core.request(
            "POST", f"/follow/{username}"
        )
```

```javascript
// Node.js skill (process-based, ecosystem access)
// plugins/discord_skill/src/index.js

const { SkillServer } = require('@alleybot/skill-sdk');
const { Client } = require('discord.js');

class DiscordSkill extends SkillServer {
  async executeCommand(request) {
    // Running in separate process
    // Communicates with core via gRPC
    const { name, args } = request;
    
    if (name === 'discord_send') {
      return await this.discord.send(args[0], args[1]);
    }
  }
}
```

### 13.8 Migration Strategy

| Phase | Duration | Action |
|-------|----------|--------|
| 1 | 2 weeks | Rust core skeleton, gRPC interface |
| 2 | 2 weeks | Python WASI runtime, skill loader |
| 3 | 2 weeks | Port 3 critical skills (memory, telegram, clawbr) |
| 4 | 2 weeks | Performance testing, optimization |
| 5 | 4 weeks | Full migration, Python core deprecated |

### 13.9 Performance Targets

| Metric | Current (Python) | Target (Rust) | Improvement |
|--------|------------------|---------------|-------------|
| Memory (idle) | 250MB | 25MB | 10x |
| Memory (loaded) | 800MB | 200MB | 4x |
| Startup time | 5s | 0.5s | 10x |
| Skill load time | 2s | 0.2s | 10x |
| Concurrent tasks | 50 | 500 | 10x |
| API latency (p99) | 150ms | 15ms | 10x |

### 13.10 Key Benefits

1. **Dynamic Loading**: Skills load on demand, unload when idle
2. **Memory Safety**: Compile-time guarantees, no runtime crashes
3. **True Concurrency**: No GIL, saturate all CPU cores
4. **Polyglot**: Use best language for each skill
5. **Security**: WASI sandbox + seccomp for untrusted skills
6. **Hot Reload**: Update skills without restart
7. **Synergy**: Native graph engine for skill composition

---

*Generated: Feb 11, 2026*
*Status: Brainstorm/Design Phase*
