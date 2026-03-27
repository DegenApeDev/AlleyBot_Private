# Hermes-Style Tools for AlleyBot

This directory contains Hermes Agent-inspired tools that extend AlleyBot's autonomous capabilities with a comprehensive tool ecosystem similar to Hermes Agent.

## 🛠️ Available Tools

### Web Tools
- **web_search**: Search the web for information using DuckDuckGo (no API key required)
- **web_extract**: Extract content from web pages with CSS selectors

### Terminal Tools
- **terminal**: Execute commands with multiple backends
  - Local execution
  - Docker containers
  - SSH remote execution
  - Singularity/Apptainer
  - Modal (serverless)

### File Tools
- **read_file**: Read file contents with offset/limit support
- **write_file**: Write content to files with directory creation
- **patch**: Find and replace in files
- **search_files**: Search for files with patterns

### Browser Automation
- **browser_navigate**: Navigate to URLs
- **browser_snapshot**: Take screenshots
- **browser_click**: Click elements by CSS selector
- **browser_vision**: Analyze page content

### Vision Tools
- **vision_analyze**: Analyze images with vision models

### Code Execution
- **execute_code**: Execute Python, JavaScript, and Bash code

### Todo Management
- **todo**: Manage todo items (list, add, complete, delete)

## 🚀 Usage Examples

### Web Search
```python
# Search for information
result = await execute_tool_action(
    tool_name="web_search",
    query="Python async programming",
    max_results=10
)

# Extract content from webpage
result = await execute_tool_action(
    tool_name="web_extract",
    url="https://example.com",
    selector=".content"
)
```

### Terminal Commands
```python
# Execute local command
result = await execute_tool_action(
    tool_name="terminal",
    command="ls -la",
    cwd="/home/user"
)

# Execute in Docker
result = await execute_tool_action(
    tool_name="terminal",
    command="python --version",
    backend="docker"
)

# Execute via SSH
result = await execute_tool_action(
    tool_name="terminal",
    command="uptime",
    backend="ssh"
)
```

### File Operations
```python
# Read file
result = await execute_tool_action(
    tool_name="read_file",
    path="config.json",
    offset=0,
    limit=100
)

# Write file
result = await execute_tool_action(
    tool_name="write_file",
    path="output.txt",
    content="Hello World!",
    create_dirs=True
)

# Patch file
result = await execute_tool_action(
    tool_name="patch",
    file_path="app.py",
    old_string="old_value",
    new_string="new_value"
)
```

### Browser Automation
```python
# Navigate to page
result = await execute_tool_action(
    tool_name="browser_navigate",
    url="https://example.com"
)

# Take screenshot
result = await execute_tool_action(
    tool_name="browser_snapshot"
)

# Click element
result = await execute_tool_action(
    tool_name="browser_click",
    selector="#submit-button"
)

# Analyze page
result = await execute_tool_action(
    tool_name="browser_vision",
    question="Is there a login form?"
)
```

### Code Execution
```python
# Execute Python code
result = await execute_tool_action(
    tool_name="execute_code",
    code="print('Hello from Python!')",
    language="python"
)

# Execute JavaScript
result = await execute_tool_action(
    tool_name="execute_code",
    code="console.log('Hello from Node.js!')",
    language="javascript"
)

# Execute Bash
result = await execute_tool_action(
    tool_name="execute_code",
    code="echo 'Hello from Bash!'",
    language="bash"
)
```

### Todo Management
```python
# List todos
result = await execute_tool_action(
    tool_name="todo",
    action="list"
)

# Add todo
result = await execute_tool_action(
    tool_name="todo",
    action="add",
    task="Build new feature"
)

# Complete todo
result = await execute_tool_action(
    tool_name="todo",
    action="complete",
    todo_id="1"
)
```

## 🔧 Configuration

Create `config/hermes_tools_config.yaml`:

```yaml
# Terminal backend
terminal:
  backend: local  # local, docker, ssh, singularity, modal
  timeout: 180
  
  # Docker settings
  docker:
    image: "python:3.11-slim"
    cpu: 1
    memory: 5120  # MB
  
  # SSH settings
  ssh:
    host: ${TERMINAL_SSH_HOST}
    user: ${TERMINAL_SSH_USER}
    key: ${TERMINAL_SSH_KEY}

# Browser automation
browser:
  driver: "chrome"
  headless: true
  window_size: [1920, 1080]

# Web search
web_search:
  engines: [duckduckgo, google, bing]
  max_results: 10
  requests_per_minute: 60

# Vision analysis
vision:
  model: "basic"  # basic, openai, claude, gemini
  max_image_size: 10485760  # 10MB

# Code execution
code_execution:
  sandbox: true
  timeout: 30
  max_memory: 512  # MB
```

## 🔌 Integration with AlleyBot

### Automatic Integration
The tools are automatically integrated with AlleyBot's action router:

```python
# Tools are available as actions:
action_spec = {
    'action_type': 'tool_web_search',
    'params': {
        'query': 'async programming',
        'max_results': 5
    }
}
result = await agi_kernel.act(action_spec)
```

### Tool Discovery
AlleyBot can automatically discover relevant tools for tasks:

```python
from src.tools.tool_registry import discover_tools_for_task

# Find tools for a task
tools = discover_tools_for_task("search the web for Python tutorials")
# Returns list of relevant tools with confidence scores
```

### AI-Driven Tool Selection
The AGI Kernel can automatically select the best tool:

```python
# When processing a goal, AlleyBot will:
# 1. Analyze the goal requirements
# 2. Discover relevant tools
# 3. Select the best tool based on confidence
# 4. Execute the tool with appropriate parameters
# 5. Verify results and adjust if needed
```

## 📊 Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| Web | web_search, web_extract | Web search and content extraction |
| Terminal | terminal | Command execution with multiple backends |
| File | read_file, write_file, patch, search_files | File manipulation |
| Browser | browser_navigate, browser_snapshot, browser_click, browser_vision | Browser automation |
| Vision | vision_analyze | Image analysis |
| Code | execute_code | Code execution in multiple languages |
| Todo | todo | Task management |

## 🔒 Security Features

### Terminal Security
- Container isolation for Docker backend
- PID limits (256 processes)
- Read-only root filesystem
- All capabilities dropped
- Namespace isolation

### File Security
- Allowed path restrictions
- Forbidden path protection
- File size limits
- Content filtering

### Rate Limiting
- Per-tool rate limits
- Global request limits
- Abuse detection

## 📈 Monitoring

### Execution Logging
All tool executions are logged to `logs/tool_executions.json`:

```json
{
  "timestamp": "2026-03-26T22:00:00",
  "tool_name": "web_search",
  "method": "web_search",
  "params": {"query": "Python"},
  "success": true,
  "execution_time": 1.23,
  "metadata": {"results_count": 10}
}
```

### Performance Metrics
- Execution time tracking
- Success rate monitoring
- Error logging
- Usage statistics

## 🚀 Advanced Features

### Custom Tools
Create custom tools by extending the base classes:

```python
from src.tools.hermes_style_tools import ToolResult

class CustomTool:
    async def custom_action(self, param1: str) -> ToolResult:
        try:
            # Your logic here
            result = process(param1)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### Tool Composition
Combine multiple tools for complex workflows:

```python
# Example: Research and summarize
async def research_and_summarize(topic: str):
    # Search for information
    search_result = await execute_tool_action(
        tool_name="web_search",
        query=topic
    )
    
    # Extract content from top results
    for result in search_result['data']['results'][:3]:
        content = await execute_tool_action(
            tool_name="web_extract",
            url=result['url']
        )
        # Process content...
    
    # Generate summary
    summary = await execute_tool_action(
        tool_name="execute_code",
        code="generate_summary(content)",
        language="python"
    )
    
    return summary
```

## 🔗 Dependencies

Install required dependencies:

```bash
# Web tools
pip install aiohttp beautifulsoup4 aiofiles

# Browser automation
pip install selenium webdriver-manager

# Vision tools
pip install pillow

# Terminal tools (Docker backend)
# Requires Docker installation

# SSH backend
# Requires SSH client setup
```

## 📝 Examples in Action

### Example 1: Research Assistant
```python
# User asks: "Research async programming in Python"
# AlleyBot automatically:
# 1. Uses web_search to find tutorials
# 2. Uses web_extract to get content
# 3. Uses execute_code to process information
# 4. Uses write_file to save summary
```

### Example 2: Code Analysis
```python
# User asks: "Analyze this Python file for bugs"
# AlleyBot automatically:
# 1. Uses read_file to get code
# 2. Uses execute_code to run static analysis
# 3. Uses patch to fix issues
# 4. Uses write_file to save fixed code
```

### Example 3: Web Automation
```python
# User asks: "Check my website for errors"
# AlleyBot automatically:
# 1. Uses browser_navigate to visit site
# 2. Uses browser_snapshot to capture page
# 3. Uses browser_vision to analyze content
# 4. Uses todo to add tasks for fixes
```

## 🎯 Best Practices

1. **Tool Selection**: Let AlleyBot automatically select tools based on task requirements
2. **Error Handling**: Always check tool execution results for errors
3. **Rate Limiting**: Respect rate limits when making web requests
4. **Security**: Use appropriate backends for sensitive operations
5. **Monitoring**: Check execution logs for performance optimization

## 🤝 Contributing

To add new tools:

1. Create tool class in `hermes_style_tools.py`
2. Register tool in `tool_registry.py`
3. Add configuration options in `hermes_tools_config.yaml`
4. Update documentation

## 📄 License

These tools are part of AlleyBot and follow the same license terms.
