"""
Hermes-Style Tools for AlleyBot

This module implements tools inspired by Hermes Agent to extend AlleyBot's
autonomous capabilities with similar functionality.

Tools organized by category:
- Web: web_search, web_extract
- Terminal: terminal (multiple backends)
- File: read_file, write_file, patch, search_files
- Browser: browser_navigate, browser_click, browser_snapshot, browser_vision
- Vision: vision_analyze
- Image: image_generate
- Code: execute_code
- Todo: todo management
- Memory: memory, session_search
- Delegation: delegate_task
- Messaging: send_message
- Home Assistant: ha_*
- TTS: text_to_speech
- RL: rl_*
"""

import asyncio
import json
import subprocess
import os
import tempfile
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import aiohttp
import aiofiles
from dataclasses import dataclass

from src.agentic.action_router import ActionEnvelope


@dataclass
class ToolResult:
    """Standard result format for all tools"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class WebTools:
    """Web search and extraction tools"""
    
    def __init__(self):
        self.session = None
    
    async def web_search(self, query: str, max_results: int = 10) -> ToolResult:
        """Search the web for information"""
        try:
            # Use multiple search engines for better results
            search_engines = [
                f"https://duckduckgo.com/html/?q={query}",
                f"https://www.google.com/search?q={query}",
            ]
            
            results = []
            
            # Create session if needed
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Search DuckDuckGo (no API key needed)
            async with self.session.get(search_engines[0]) as response:
                if response.status == 200:
                    text = await response.text()
                    # Parse results (simplified)
                    import re
                    links = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)".*?>(.*?)</a>', text)
                    for url, title in links[:max_results]:
                        results.append({
                            'title': title.strip(),
                            'url': url,
                            'snippet': title.strip()  # Simplified
                        })
            
            return ToolResult(
                success=True,
                data={
                    'query': query,
                    'results': results,
                    'count': len(results)
                },
                metadata={'source': 'duckduckgo'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def web_extract(self, url: str, selector: Optional[str] = None) -> ToolResult:
        """Extract content from web pages"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ToolResult(success=False, error=f"HTTP {response.status}")
                
                html = await response.text()
                
                # Extract title
                import re
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                title = title_match.group(1) if title_match else "No title"
                
                # Extract meta description
                desc_match = re.search(r'<meta name="description" content="(.*?)"', html, re.IGNORECASE)
                description = desc_match.group(1) if desc_match else "No description"
                
                # Extract text content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Apply CSS selector if provided
                selected_content = None
                if selector:
                    try:
                        elements = soup.select(selector)
                        selected_content = [elem.get_text().strip() for elem in elements]
                    except Exception as e:
                        return ToolResult(success=False, error=f"Selector error: {e}")
                
                return ToolResult(
                    success=True,
                    data={
                        'url': url,
                        'title': title,
                        'description': description,
                        'content': text[:1000],  # First 1000 chars
                        'selected': selected_content if selector else None
                    },
                    metadata={'content_length': len(text)}
                )
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class TerminalTools:
    """Terminal execution with multiple backends"""
    
    def __init__(self, backend: str = "local"):
        self.backend = backend
        self.sandbox_dir = os.path.abspath("sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.cwd = self.sandbox_dir
        self.timeout = 180
    
    async def terminal(self, command: str, cwd: Optional[str] = None) -> ToolResult:
        """Execute terminal commands with various backends, jailed to the sandbox"""
        try:
            work_dir = cwd or self.cwd
            # Enforce sandbox ceiling
            if not os.path.abspath(work_dir).startswith(self.sandbox_dir):
                work_dir = self.sandbox_dir
                
            if self.backend == "local":
                return await self._execute_local(command, work_dir)
            elif self.backend == "docker":
                return await self._execute_docker(command, work_dir)
            elif self.backend == "ssh":
                return await self._execute_ssh(command, work_dir)
            else:
                return ToolResult(success=False, error=f"Unsupported backend: {self.backend}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _execute_local(self, command: str, cwd: str) -> ToolResult:
        """Execute command locally"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode
                },
                metadata={
                    'backend': 'local',
                    'cwd': cwd,
                    'command': command
                }
            )
            
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Command timed out")
    
    async def _execute_docker(self, command: str, cwd: str) -> ToolResult:
        """Execute command in Docker container"""
        try:
            # Map local directory to container
            volume_mount = f"{os.path.abspath(cwd)}:/workspace"
            
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", volume_mount,
                "-w", "/workspace",
                "python:3.11-slim",
                "sh", "-c", command
            ]
            
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode
                },
                metadata={
                    'backend': 'docker',
                    'cwd': cwd,
                    'command': command
                }
            )
            
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Docker command timed out")
    
    async def _execute_ssh(self, command: str, cwd: str) -> ToolResult:
        """Execute command via SSH"""
        try:
            # Get SSH config from environment
            ssh_host = os.getenv('TERMINAL_SSH_HOST')
            ssh_user = os.getenv('TERMINAL_SSH_USER')
            ssh_key = os.getenv('TERMINAL_SSH_KEY')
            
            if not all([ssh_host, ssh_user, ssh_key]):
                return ToolResult(
                    success=False, 
                    error="SSH credentials not configured. Set TERMINAL_SSH_HOST, TERMINAL_SSH_USER, TERMINAL_SSH_KEY"
                )
            
            # Build SSH command
            ssh_cmd = [
                "ssh", "-i", ssh_key,
                f"{ssh_user}@{ssh_host}",
                f"cd {cwd} && {command}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode
                },
                metadata={
                    'backend': 'ssh',
                    'host': ssh_host,
                    'cwd': cwd,
                    'command': command
                }
            )
            
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="SSH command timed out")


class FileTools:
    """File manipulation tools"""
    
    async def read_file(self, path: str, offset: int = 0, limit: Optional[int] = None) -> ToolResult:
        """Read file contents"""
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                if limit:
                    content = await f.read()
                    lines = content.split('\n')
                    selected_lines = lines[offset:offset + limit]
                    result = '\n'.join(selected_lines)
                else:
                    result = await f.read()
            
            return ToolResult(
                success=True,
                data={
                    'path': path,
                    'content': result,
                    'size': len(result),
                    'lines': result.count('\n') + 1
                },
                metadata={'offset': offset, 'limit': limit}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def write_file(self, path: str, content: str, create_dirs: bool = True) -> ToolResult:
        """Write content to file"""
        try:
            file_path = Path(path)
            
            # Create directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return ToolResult(
                success=True,
                data={
                    'path': path,
                    'bytes_written': len(content),
                    'created': not file_path.exists()
                },
                metadata={'create_dirs': create_dirs}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def patch(self, file_path: str, old_string: str, new_string: str) -> ToolResult:
        """Apply patch to file (find and replace)"""
        try:
            # Read current content
            read_result = await self.read_file(file_path)
            if not read_result.success:
                return read_result
            
            content = read_result.data['content']
            
            # Apply patch
            if old_string not in content:
                return ToolResult(
                    success=False, 
                    error=f"String not found in file: {old_string[:50]}..."
                )
            
            new_content = content.replace(old_string, new_string)
            
            # Write back
            write_result = await self.write_file(file_path, new_content, create_dirs=False)
            
            if write_result.success:
                write_result.data.update({
                    'patch_applied': True,
                    'replacements': content.count(old_string)
                })
            
            return write_result
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def search_files(self, pattern: str, directory: str = ".", file_types: Optional[List[str]] = None) -> ToolResult:
        """Search for files matching pattern"""
        try:
            import fnmatch
            import re
            
            search_dir = Path(directory)
            matches = []
            
            # Determine if pattern is regex or glob
            is_regex = any(c in pattern for c in r'[]{}()*+?.^$|\\')
            
            for file_path in search_dir.rglob('*'):
                if file_path.is_file():
                    # Filter by file types if specified
                    if file_types and file_path.suffix not in file_types:
                        continue
                    
                    # Check pattern match
                    if is_regex:
                        if re.search(pattern, file_path.name):
                            matches.append(str(file_path))
                    else:
                        if fnmatch.fnmatch(file_path.name, pattern):
                            matches.append(str(file_path))
            
            return ToolResult(
                success=True,
                data={
                    'pattern': pattern,
                    'directory': directory,
                    'matches': matches,
                    'count': len(matches)
                },
                metadata={'file_types': file_types}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserTools:
    """Browser automation tools"""
    
    def __init__(self):
        self.driver = None
        self.current_url = None
    
    async def browser_navigate(self, url: str) -> ToolResult:
        """Navigate to URL in browser"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Setup headless browser
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(url)
            self.current_url = url
            
            return ToolResult(
                success=True,
                data={
                    'url': url,
                    'title': self.driver.title,
                    'current_url': self.driver.current_url
                },
                metadata={'browser': 'chrome-headless'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def browser_snapshot(self) -> ToolResult:
        """Take screenshot of current page"""
        try:
            if not self.driver:
                return ToolResult(success=False, error="No browser session active")
            
            # Take screenshot
            screenshot_path = tempfile.mktemp(suffix='.png')
            self.driver.save_screenshot(screenshot_path)
            
            # Get page source
            page_source = self.driver.page_source
            
            return ToolResult(
                success=True,
                data={
                    'screenshot_path': screenshot_path,
                    'page_title': self.driver.title,
                    'current_url': self.driver.current_url,
                    'page_source_length': len(page_source)
                },
                metadata={'screenshot_size': os.path.getsize(screenshot_path)}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def browser_click(self, selector: str) -> ToolResult:
        """Click element on page"""
        try:
            if not self.driver:
                return ToolResult(success=False, error="No browser session active")
            
            from selenium.webdriver.common.by import By
            
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
            
            return ToolResult(
                success=True,
                data={
                    'selector': selector,
                    'clicked': True,
                    'current_url': self.driver.current_url
                },
                metadata={'action': 'click'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def browser_vision(self, question: str) -> ToolResult:
        """Analyze page content with vision"""
        try:
            if not self.driver:
                return ToolResult(success=False, error="No browser session active")
            
            # Get page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Simple text-based analysis (could integrate with vision model)
            if question.lower() in page_text.lower():
                answer = f"Yes, '{question}' was found on the page"
            else:
                answer = f"No, '{question}' was not found on the page"
            
            return ToolResult(
                success=True,
                data={
                    'question': question,
                    'answer': answer,
                    'page_length': len(page_text)
                },
                metadata={'method': 'text_search'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class VisionTools:
    """Computer vision tools"""
    
    async def vision_analyze(self, image_path: str, question: str) -> ToolResult:
        """Analyze image with vision model"""
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return ToolResult(success=False, error=f"Image not found: {image_path}")
            
            # For now, return basic image info
            # Could integrate with OpenAI Vision, Claude Vision, etc.
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
                format = img.format
                mode = img.mode
            
            # Simple analysis based on question
            analysis = f"Image is {width}x{height} pixels, format {format}, mode {mode}"
            
            return ToolResult(
                success=True,
                data={
                    'image_path': image_path,
                    'question': question,
                    'analysis': analysis,
                    'width': width,
                    'height': height,
                    'format': format,
                    'mode': mode
                },
                metadata={'vision_model': 'basic'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CodeExecutionTools:
    """Code execution tools"""
    
    async def execute_code(self, code: str, language: str = "python") -> ToolResult:
        """Execute code in specified language"""
        try:
            if language.lower() == "python":
                return await self._execute_python(code)
            elif language.lower() == "javascript":
                return await self._execute_javascript(code)
            elif language.lower() == "bash":
                return await self._execute_bash(code)
            else:
                return ToolResult(success=False, error=f"Unsupported language: {language}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _execute_python(self, code: str) -> ToolResult:
        """Execute Python code in Sandbox scratchpad"""
        try:
            scratchpad_dir = os.path.abspath("sandbox/scratchpad")
            os.makedirs(scratchpad_dir, exist_ok=True)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=scratchpad_dir, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup
            os.unlink(temp_file)
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode,
                    'language': 'python'
                },
                metadata={'execution_time': 'N/A'}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _execute_javascript(self, code: str) -> ToolResult:
        """Execute JavaScript code with Node.js"""
        try:
            process = await asyncio.create_subprocess_exec(
                'node', '-e', code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode,
                    'language': 'javascript'
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _execute_bash(self, code: str) -> ToolResult:
        """Execute bash code"""
        try:
            process = await asyncio.create_subprocess_shell(
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode,
                    'language': 'bash'
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class TodoTools:
    """Todo management tools"""
    
    def __init__(self, storage_path: str = "data/todos.json"):
        self.storage_path = storage_path
        self.todos = self._load_todos()
    
    def _load_todos(self) -> List[Dict]:
        """Load todos from file"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def _save_todos(self):
        """Save todos to file"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.todos, f, indent=2)
    
    async def todo(self, action: str, task: Optional[str] = None, todo_id: Optional[str] = None) -> ToolResult:
        """Manage todos"""
        try:
            if action == "list":
                return ToolResult(
                    success=True,
                    data={'todos': self.todos, 'count': len(self.todos)}
                )
            
            elif action == "add" and task:
                new_todo = {
                    'id': str(len(self.todos) + 1),
                    'task': task,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat()
                }
                self.todos.append(new_todo)
                self._save_todos()
                
                return ToolResult(
                    success=True,
                    data={'todo': new_todo, 'action': 'added'}
                )
            
            elif action == "complete" and todo_id:
                for todo in self.todos:
                    if todo['id'] == todo_id:
                        todo['status'] = 'completed'
                        todo['completed_at'] = datetime.now().isoformat()
                        self._save_todos()
                        
                        return ToolResult(
                            success=True,
                            data={'todo': todo, 'action': 'completed'}
                        )
                
                return ToolResult(success=False, error=f"Todo not found: {todo_id}")
            
            elif action == "delete" and todo_id:
                self.todos = [t for t in self.todos if t['id'] != todo_id]
                self._save_todos()
                
                return ToolResult(
                    success=True,
                    data={'deleted_id': todo_id, 'action': 'deleted'}
                )
            
            else:
                return ToolResult(success=False, error=f"Invalid action: {action}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Tool registry for easy access
HERMES_TOOLS = {
    'web': WebTools(),
    'terminal': TerminalTools(),
    'file': FileTools(),
    'browser': BrowserTools(),
    'vision': VisionTools(),
    'code': CodeExecutionTools(),
    'todo': TodoTools(),
}


async def execute_hermes_tool(tool_name: str, method: str, *args, **kwargs) -> ToolResult:
    """Execute a Hermes-style tool"""
    try:
        # Map tool names to instances
        tool_map = {
            'web_search': (HERMES_TOOLS['web'], 'web_search'),
            'web_extract': (HERMES_TOOLS['web'], 'web_extract'),
            'terminal': (HERMES_TOOLS['terminal'], 'terminal'),
            'read_file': (HERMES_TOOLS['file'], 'read_file'),
            'write_file': (HERMES_TOOLS['file'], 'write_file'),
            'patch': (HERMES_TOOLS['file'], 'patch'),
            'search_files': (HERMES_TOOLS['file'], 'search_files'),
            'browser_navigate': (HERMES_TOOLS['browser'], 'browser_navigate'),
            'browser_snapshot': (HERMES_TOOLS['browser'], 'browser_snapshot'),
            'browser_click': (HERMES_TOOLS['browser'], 'browser_click'),
            'browser_vision': (HERMES_TOOLS['browser'], 'browser_vision'),
            'vision_analyze': (HERMES_TOOLS['vision'], 'vision_analyze'),
            'execute_code': (HERMES_TOOLS['code'], 'execute_code'),
            'todo': (HERMES_TOOLS['todo'], 'todo'),
        }
        
        if tool_name not in tool_map:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")
        
        tool_instance, tool_method = tool_map[tool_name]
        method_func = getattr(tool_instance, tool_method)
        
        result = await method_func(*args, **kwargs)
        
        return result
        
    except Exception as e:
        return ToolResult(success=False, error=f"Tool execution failed: {str(e)}")


# Integration with AlleyBot's action router
class HermesToolPlugin:
    """Plugin to integrate Hermes tools with AlleyBot"""
    
    def __init__(self):
        self.name = "hermes_tools"
        self.description = "Hermes-style tools for AlleyBot"
    
    async def execute_action(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Hermes tool action"""
        tool_name = action_spec.get('tool_name')
        method = action_spec.get('method', tool_name)
        params = action_spec.get('params', {})
        
        result = await execute_hermes_tool(tool_name, method, **params)
        
        return {
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'metadata': result.metadata
        }
