# AlleyBot Super High-Level Tool Use System

## Overview

AlleyBot now has **super high-level tool use capabilities** with:
- ✅ Native function calling (DeepSeek & Grok compatible)
- ✅ Autonomous tool creation at runtime
- ✅ Dynamic tool discovery from plugins & MCP servers
- ✅ Parallel tool execution
- ✅ AI-powered tool selection

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Tool Orchestrator                       │
│  (Unified interface for all tool capabilities)          │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Function    │  │  Autonomous  │  │   Plugin     │
│  Calling     │  │     Tool     │  │   Tools      │
│  Engine      │  │   Creator    │  │   + MCP      │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Components

### 1. **Function Calling Engine** (`function_calling.py`)
Native OpenAI-compatible function calling for DeepSeek & Grok.

**Features:**
- Automatic schema generation from Python functions
- Type hint inference
- Parallel tool execution
- Tool result validation

**Example:**
```python
from src.tools.function_calling import FunctionCallingEngine, FunctionTool

# Create engine
engine = FunctionCallingEngine(llm_client, model="deepseek-chat")

# Register a tool from function
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text"""
    # ... implementation
    return "positive"

engine.register_from_function(analyze_sentiment)

# Use with LLM
result = engine.call_with_tools(
    messages=[{"role": "user", "content": "Analyze: This is great!"}],
    max_iterations=5,
    parallel=True
)
```

### 2. **Autonomous Tool Creator** (`autonomous_tool_creator.py`)
Creates tools on-the-fly when capabilities are missing.

**Flow:**
1. Detect capability gap
2. Generate tool specification (AI)
3. Generate Python code (AI)
4. Validate safety
5. Test in sandbox
6. Register dynamically
7. Use immediately

**Example:**
```python
from src.tools.autonomous_tool_creator import AutonomousToolCreator

creator = AutonomousToolCreator(llm_client, fc_engine, core)

# Detect gap
gap = creator.detect_capability_gap(
    task="Calculate fibonacci numbers",
    available_tools=["add", "multiply"]
)

# Create tool
if gap:
    tool_name = creator.create_tool(gap)
    # Tool is now available!
```

### 3. **Tool Orchestrator** (`tool_orchestrator.py`)
High-level coordinator for all tool capabilities.

**Features:**
- Unified tool interface
- Automatic tool discovery
- AI-powered task execution
- Tool suggestion system

**Example:**
```python
from src.tools.tool_orchestrator import ToolOrchestrator

orchestrator = ToolOrchestrator(core, llm_client)

# Execute complex task
result = orchestrator.execute_task_with_tools(
    task="Check crypto prices and post summary to Moltx",
    auto_create_tools=True
)
```

---

## Usage via Commands

AlleyBot provides intuitive commands for tool use:

### List Tools
```
/tools_list [type]
```
Types: `all`, `function`, `plugin`, `mcp`, `created`

### Get Tool Info
```
/tools_info <tool_name>
```

### Create Tool
```
/tools_create <capability_description>
```
Example: `/tools_create analyze sentiment of text`

### Call Tool
```
/tools_call <tool_name> <arg1=value1> <arg2=value2>
```
Example: `/tools_call analyze_sentiment text="This is great!"`

### Execute Task (AI-Powered)
```
/tools_execute <task_description>
```
Example: `/tools_execute Check crypto prices and post summary to Moltx`

### Suggest Tools
```
/tools_suggest <task_description>
```

### Tool Statistics
```
/tools_stats
```

### Refresh Discovery
```
/tools_refresh
```

---

## How It Works

### 1. **Tool Discovery**
On initialization, the orchestrator:
- Scans all plugins for commands
- Discovers MCP server capabilities
- Registers function calling tools
- Loads previously created tools

### 2. **Capability Gap Detection**
When executing a task:
```python
# AI analyzes task vs available tools
gap = detect_capability_gap(task, available_tools)

if gap:
    # AI generates tool specification
    spec = generate_tool_spec(gap)
    
    # AI generates Python code
    code = generate_tool_code(spec)
    
    # Safety validation
    if validate_code_safety(code):
        # Test in sandbox
        if test_tool_in_sandbox(code):
            # Register and use
            register_tool_from_code(code)
```

### 3. **Function Calling**
Native function calling with DeepSeek/Grok:
```python
# LLM decides which tools to call
response = llm.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tool_schemas,
    tool_choice="auto",
    parallel_tool_calls=True
)

# Execute tool calls
for tool_call in response.tool_calls:
    result = execute_tool(tool_call)
    # Add result to conversation
```

### 4. **Safety Mechanisms**
All generated tools are validated:
- ✅ No `eval()`, `exec()`, `os.system()`
- ✅ Valid Python syntax
- ✅ Sandbox testing with dummy inputs
- ✅ Type checking
- ✅ Error handling

---

## Integration with Autonomous Brain

The tool system integrates seamlessly with AlleyBot's autonomous brain:

```python
# Brain detects it needs a capability
if capability_missing:
    # Create tool automatically
    tool_name = orchestrator.create_tool_on_demand(capability)
    
    # Use tool immediately
    result = orchestrator.call_tool_by_name(tool_name, **args)
    
    # Continue autonomous operation
```

---

## Examples

### Example 1: Analyze Sentiment
```python
# User: "Analyze sentiment of recent posts"

# 1. Brain detects missing sentiment analysis tool
# 2. Tool creator generates sentiment analyzer
# 3. Tool is tested and registered
# 4. Brain uses tool to analyze posts
# 5. Results inform next actions
```

### Example 2: Complex Multi-Tool Task
```python
# User: "Check crypto prices, analyze trends, and post summary"

# AI orchestrator:
# 1. Calls crypto_prices tool
# 2. Calls analyze_trends tool (or creates it)
# 3. Calls moltx_post tool with summary
# All in one execution flow!
```

### Example 3: On-Demand Tool Creation
```
User: /tools_create calculate fibonacci sequence

AlleyBot:
🔨 Creating tool for: calculate fibonacci sequence
✅ Tool created and registered: calculate_fibonacci

You can now use it with:
/tools_call calculate_fibonacci n=10
```

---

## Performance

- **Tool Discovery:** ~100ms (cached after first run)
- **Tool Creation:** ~3-5 seconds (AI generation + testing)
- **Function Calling:** ~500ms per iteration
- **Parallel Execution:** 2-3x faster for independent tools

---

## Limitations

1. **Generated Code Quality:** AI-generated tools may need refinement
2. **Sandbox Limitations:** Some operations can't be tested in sandbox
3. **Token Limits:** Very complex tools may exceed generation limits
4. **Safety Trade-offs:** Strict validation may block some valid code

---

## Future Enhancements

- [ ] Tool versioning and rollback
- [ ] Tool performance monitoring
- [ ] Tool recommendation learning
- [ ] Cross-tool composition
- [ ] Tool marketplace (share tools between agents)
- [ ] Advanced sandbox with resource limits
- [ ] Tool documentation generation
- [ ] Tool testing suite generation

---

## Configuration

Add to `.env`:
```bash
# Enable tool orchestrator
ENABLE_TOOL_ORCHESTRATOR=true

# Auto-create tools when missing
AUTO_CREATE_TOOLS=true

# Tool creation model (grok-code-fast-1 or deepseek-chat)
TOOL_CREATION_MODEL=grok-code-fast-1
```

---

## Troubleshooting

### Tool creation fails
- Check LLM API keys (XAI_API_KEY or DEEPSEEK_API_KEY)
- Verify capability description is clear
- Check logs for safety validation errors

### Tool not found
- Run `/tools_refresh` to re-discover
- Check tool name spelling
- Verify plugin is loaded

### Function calling not working
- Ensure using DeepSeek or Grok (OpenAI-compatible)
- Check model supports function calling
- Verify tool schemas are valid

---

## API Reference

See individual module docstrings:
- `function_calling.py` - Function calling engine
- `autonomous_tool_creator.py` - Tool creation system
- `tool_orchestrator.py` - High-level orchestration
- `tool_commands.py` - Command interface
