"""
Skill Autonomous Executor - Heartbeat & Trigger System

Adds OpenClaw-style autonomous execution with:
- HEARTBEAT.md checklist processing
- Cron-based scheduled skills
- Event-driven triggers (webhooks, email, file changes)
- Tool registry integration (browser, system, email, calendar)
"""
import os
import re
import yaml
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class TriggerType(Enum):
    """Types of autonomous triggers"""
    HEARTBEAT = "heartbeat"      # Regular interval check
    CRON = "cron"                # Scheduled time
    WEBHOOK = "webhook"          # External HTTP call
    EMAIL = "email"              # Gmail Pub/Sub
    FILE = "file"                # File system change
    EVENT = "event"              # Internal event


@dataclass
class SkillTrigger:
    """Configuration for autonomous skill execution"""
    skill_name: str
    trigger_type: TriggerType
    schedule: Optional[str] = None       # Cron expression or interval
    condition: Optional[str] = None      # Condition to check
    last_run: Optional[datetime] = None
    run_count: int = 0
    enabled: bool = True
    max_runs_per_day: int = 100
    require_approval: bool = False       # Safety: require manual approval


class SkillAutonomousExecutorMixin:
    """
    Autonomous skill execution with OpenClaw-style triggers.
    
    Features:
    - HEARTBEAT.md checklist processing every N minutes
    - Cron-scheduled skills
    - Event-driven execution
    - Tool registry integration
    - Safety gating with approval workflows
    """

    def __init__(self, config):
        super().__init__(config)
        self.triggers: Dict[str, SkillTrigger] = {}
        self.tool_registry: Dict[str, Callable] = {}
        self.heartbeat_interval = config.get('heartbeat_interval_minutes', 30)
        self._heartbeat_task = None
        self._running = False
        self.execution_history: List[Dict] = []
        self.max_history = 1000
        
        # Initialize tool registry
        self._init_tool_registry()
        
        # Load HEARTBEAT.md if exists
        self._load_heartbeat_config()

    def _init_tool_registry(self):
        """Register available tools for skill execution"""
        self.tool_registry = {
            # System tools
            'system.run': self._tool_system_run,
            'system.notify': self._tool_system_notify,
            'file.read': self._tool_file_read,
            'file.write': self._tool_file_write,
            'file.list': self._tool_file_list,
            
            # Browser tools
            'browser.open': self._tool_browser_open,
            'browser.scrape': self._tool_browser_scrape,
            'browser.click': self._tool_browser_click,
            'browser.fill': self._tool_browser_fill,
            
            # Communication tools
            'email.read': self._tool_email_read,
            'email.send': self._tool_email_send,
            'telegram.send': self._tool_telegram_send,
            'discord.send': self._tool_discord_send,
            
            # Data tools
            'calendar.read': self._tool_calendar_read,
            'calendar.create': self._tool_calendar_create,
            'search.web': self._tool_web_search,
            'api.call': self._tool_api_call,
            
            # Crypto/Web3 tools (AlleyBot specialty)
            'wallet.balance': self._tool_wallet_balance,
            'dex.swap': self._tool_dex_swap,
            'token.price': self._tool_token_price,
        }

    def _load_heartbeat_config(self):
        """Load HEARTBEAT.md from workspace if exists"""
        heartbeat_paths = [
            Path(self.project_root) / 'HEARTBEAT.md',
            Path.home() / '.alleybot' / 'HEARTBEAT.md',
        ]
        
        for path in heartbeat_paths:
            if path.exists():
                try:
                    content = path.read_text()
                    self._parse_heartbeat(content)
                    print(f"📋 Loaded HEARTBEAT.md from {path}")
                    break
                except Exception as e:
                    print(f"⚠️ Failed to load HEARTBEAT.md: {e}")

    def _parse_heartbeat(self, content: str):
        """Parse HEARTBEAT.md and create triggers"""
        # Look for YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            try:
                config = yaml.safe_load(match.group(1))
                interval = config.get('interval_minutes', self.heartbeat_interval)
                self.heartbeat_interval = interval
            except:
                pass
        
        # Parse checklist items as skill triggers
        # Pattern: - [ ] Task description -> skill_name
        checklist_pattern = r'- \[([ x])\] (.+?)(?: -> (\w+))?$'
        for match in re.finditer(checklist_pattern, content, re.MULTILINE):
            checked = match.group(1) == 'x'
            task = match.group(2).strip()
            skill = match.group(3) or self._infer_skill_from_task(task)
            
            if skill and not checked:
                trigger_id = f"heartbeat_{skill}_{task[:20]}"
                self.triggers[trigger_id] = SkillTrigger(
                    skill_name=skill,
                    trigger_type=TriggerType.HEARTBEAT,
                    condition=task,
                    enabled=True
                )

    def _infer_skill_from_task(self, task: str) -> Optional[str]:
        """Infer which skill to use for a task"""
        task_lower = task.lower()
        
        # Map common tasks to skills
        mappings = {
            'email': 'email-manager',
            'gmail': 'email-manager',
            'calendar': 'calendar-manager',
            'schedule': 'calendar-manager',
            'price': 'crypto-prices',
            'crypto': 'crypto-prices',
            'bitcoin': 'crypto-prices',
            'token': 'token-analysis',
            'post': 'social-poster',
            'tweet': 'social-poster',
            'moltx': 'moltx-poster',
            'moltbook': 'moltbook-poster',
            'backup': 'file-backup',
            'file': 'file-manager',
            'browser': 'web-browser',
            'search': 'web-search',
            'scrape': 'web-scraper',
        }
        
        for keyword, skill in mappings.items():
            if keyword in task_lower:
                return skill
        
        return None

    # === Tool Implementations ===

    def _tool_system_run(self, command: str, timeout: int = 30) -> Dict:
        """Execute system command safely"""
        try:
            # Security: Check against allowlist
            allowed_commands = ['ls', 'cat', 'grep', 'find', 'curl', 'git', 'python3', 'pip']
            cmd_base = command.split()[0] if command else ''
            
            if cmd_base not in allowed_commands:
                return {
                    'success': False,
                    'error': f'Command not in allowlist: {cmd_base}. Allowed: {allowed_commands}'
                }
            
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.project_root
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[:2000],  # Limit output
                'stderr': result.stderr[:1000],
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_system_notify(self, title: str, message: str) -> Dict:
        """Send system notification"""
        try:
            # Linux
            if os.system('which notify-send > /dev/null 2>&1') == 0:
                os.system(f'notify-send "{title}" "{message}"')
                return {'success': True}
            
            # macOS
            if os.system('which osascript > /dev/null 2>&1') == 0:
                script = f'display notification "{message}" with title "{title}"'
                os.system(f'osascript -e \'{script}\'')
                return {'success': True}
            
            return {'success': False, 'error': 'No notification system available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_file_read(self, path: str) -> Dict:
        """Read file contents"""
        try:
            full_path = Path(self.project_root) / path
            # Security: Stay within project
            if not str(full_path).startswith(str(self.project_root)):
                return {'success': False, 'error': 'Path outside project root'}
            
            content = full_path.read_text()
            return {'success': True, 'content': content[:10000]}  # Limit size
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_file_write(self, path: str, content: str) -> Dict:
        """Write file contents"""
        try:
            full_path = Path(self.project_root) / path
            if not str(full_path).startswith(str(self.project_root)):
                return {'success': False, 'error': 'Path outside project root'}
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return {'success': True, 'path': str(full_path)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_file_list(self, path: str = '.') -> Dict:
        """List directory contents"""
        try:
            full_path = Path(self.project_root) / path
            if not str(full_path).startswith(str(self.project_root)):
                return {'success': False, 'error': 'Path outside project root'}
            
            items = []
            for item in full_path.iterdir():
                items.append({
                    'name': item.name,
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0
                })
            return {'success': True, 'items': items}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_browser_open(self, url: str) -> Dict:
        """Open URL in browser (requires Playwright/Selenium)"""
        return {'success': False, 'error': 'Browser automation requires Playwright setup. Use: pip install playwright && playwright install'}

    def _tool_browser_scrape(self, url: str, selector: Optional[str] = None) -> Dict:
        """Scrape webpage content"""
        return {'success': False, 'error': 'Browser automation requires Playwright setup'}

    def _tool_browser_click(self, selector: str) -> Dict:
        """Click element on current page"""
        return {'success': False, 'error': 'Browser automation requires Playwright setup'}

    def _tool_browser_fill(self, selector: str, value: str) -> Dict:
        """Fill form field on current page"""
        return {'success': False, 'error': 'Browser automation requires Playwright setup'}

    def _tool_email_read(self, limit: int = 10) -> Dict:
        """Read recent emails (requires Gmail integration)"""
        return {'success': False, 'error': 'Email integration not configured. Set up Gmail Pub/Sub or IMAP.'}

    def _tool_email_send(self, to: str, subject: str, body: str) -> Dict:
        """Send email"""
        return {'success': False, 'error': 'Email integration not configured'}

    def _tool_telegram_send(self, chat_id: str, message: str) -> Dict:
        """Send Telegram message"""
        if hasattr(self, 'core') and hasattr(self.core, 'telegram'):
            try:
                self.core.telegram.send_message(chat_id, message)
                return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Telegram not available'}

    def _tool_discord_send(self, webhook_url: str, message: str) -> Dict:
        """Send Discord message via webhook"""
        try:
            import requests
            response = requests.post(webhook_url, json={'content': message}, timeout=10)
            return {'success': response.status_code == 204}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_calendar_read(self, days: int = 7) -> Dict:
        """Read calendar events"""
        return {'success': False, 'error': 'Calendar integration not configured'}

    def _tool_calendar_create(self, title: str, start: str, end: Optional[str] = None) -> Dict:
        """Create calendar event"""
        return {'success': False, 'error': 'Calendar integration not configured'}

    def _tool_web_search(self, query: str, limit: int = 10) -> Dict:
        """Search the web"""
        return {'success': False, 'error': 'Web search requires API key (Serper, Brave, etc.)'}

    def _tool_api_call(self, method: str, url: str, headers: Optional[Dict] = None, 
                       body: Optional[Dict] = None) -> Dict:
        """Make HTTP API call"""
        try:
            import requests
            response = requests.request(
                method, url, headers=headers, json=body, timeout=30
            )
            return {
                'success': 200 <= response.status_code < 300,
                'status': response.status_code,
                'body': response.text[:5000]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _tool_wallet_balance(self, chain: str = 'ethereum', address: Optional[str] = None) -> Dict:
        """Get wallet balance"""
        # Route to appropriate plugin
        if hasattr(self, 'core') and hasattr(self.core, 'plugin_manager'):
            plugins = self.core.plugin_manager.plugins
            if 'base_wallet_balance' in plugins:
                return plugins['base_wallet_balance'].get_balance(address)
        return {'success': False, 'error': 'Wallet plugin not available'}

    def _tool_dex_swap(self, from_token: str, to_token: str, amount: float) -> Dict:
        """Execute DEX swap"""
        return {'success': False, 'error': 'DEX swap requires manual approval for security'}

    def _tool_token_price(self, symbol: str) -> Dict:
        """Get token price"""
        if hasattr(self, 'core') and hasattr(self.core, 'plugin_manager'):
            plugins = self.core.plugin_manager.plugins
            if 'crypto' in plugins:
                return plugins['crypto'].get_price(symbol)
        return {'success': False, 'error': 'Crypto plugin not available'}

    # === Autonomous Execution ===

    def start_autonomous_mode(self):
        """Start the autonomous heartbeat loop"""
        if self._running:
            return False
        
        self._running = True
        print(f"🤖 Autonomous mode started (heartbeat: {self.heartbeat_interval}min)")
        
        # Start heartbeat in background
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self._heartbeat_task = loop.create_task(self._heartbeat_loop())
        return True

    def stop_autonomous_mode(self):
        """Stop the autonomous heartbeat loop"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        print("🛑 Autonomous mode stopped")

    async def _heartbeat_loop(self):
        """Main heartbeat loop - runs every N minutes"""
        while self._running:
            try:
                await self._process_heartbeat()
                # Sleep for interval (convert minutes to seconds)
                await asyncio.sleep(self.heartbeat_interval * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute on error

    async def _process_heartbeat(self):
        """Process HEARTBEAT.md checklist and triggers"""
        print(f"💓 Heartbeat at {datetime.now().isoformat()}")
        
        results = []
        
        # Process each trigger
        for trigger_id, trigger in self.triggers.items():
            if not trigger.enabled:
                continue
            
            # Check rate limiting
            if trigger.run_count >= trigger.max_runs_per_day:
                continue
            
            # Check if it's time to run
            should_run = False
            if trigger.trigger_type == TriggerType.HEARTBEAT:
                # Run on every heartbeat if condition not met
                should_run = True
            elif trigger.trigger_type == TriggerType.CRON and trigger.schedule:
                should_run = self._check_cron_schedule(trigger.schedule)
            
            if should_run:
                result = await self._execute_trigger(trigger_id, trigger)
                results.append(result)
        
        # Log summary
        if results:
            success_count = sum(1 for r in results if r.get('success'))
            print(f"   ✅ {success_count}/{len(results)} tasks executed")
        else:
            print("   📭 No tasks to execute")

    async def _execute_trigger(self, trigger_id: str, trigger: SkillTrigger) -> Dict:
        """Execute a triggered skill"""
        print(f"   🔧 Executing: {trigger.skill_name} ({trigger.trigger_type.value})")
        
        # Check if approval required
        if trigger.require_approval:
            self._request_approval(trigger_id, trigger)
            return {'success': False, 'pending_approval': True}
        
        # Execute skill
        try:
            # Use skill composition to execute
            result = self.execute_skill(trigger.skill_name, trigger.condition or "Autonomous execution")
            
            # Update trigger stats
            trigger.last_run = datetime.now()
            trigger.run_count += 1
            
            # Log execution
            self._log_execution(trigger_id, trigger, result)
            
            return result
            
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            self._log_execution(trigger_id, trigger, error_result)
            return error_result

    def _request_approval(self, trigger_id: str, trigger: SkillTrigger):
        """Request manual approval for sensitive action"""
        if hasattr(self, 'core') and hasattr(self.core, 'notification_service'):
            self.core.notification_service.send_alert(
                f"Approval required: {trigger.skill_name}",
                f"Task: {trigger.condition}\nUse: skill_approve {trigger_id}"
            )

    def _check_cron_schedule(self, schedule: str) -> bool:
        """Check if cron schedule should run now"""
        # Simple cron check - full implementation would use croniter library
        # For now, support simple formats like "*/30 * * * *" (every 30 min)
        try:
            parts = schedule.split()
            if len(parts) == 5:
                minute_part = parts[0]
                if minute_part.startswith('*/'):
                    interval = int(minute_part[2:])
                    current_minute = datetime.now().minute
                    return current_minute % interval == 0
        except:
            pass
        return False

    def _log_execution(self, trigger_id: str, trigger: SkillTrigger, result: Dict):
        """Log execution to history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'trigger_id': trigger_id,
            'skill_name': trigger.skill_name,
            'trigger_type': trigger.trigger_type.value,
            'condition': trigger.condition,
            'success': result.get('success', False),
            'error': result.get('error'),
        }
        self.execution_history.append(entry)
        
        # Trim history
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

    # === Telegram Commands ===

    def autonomous_start_command(self):
        """Start autonomous heartbeat mode"""
        if self.start_autonomous_mode():
            return f"🤖 Autonomous mode started\n💓 Heartbeat: every {self.heartbeat_interval} minutes\n📋 Triggers: {len(self.triggers)} configured"
        return "⚠️ Autonomous mode already running"

    def autonomous_stop_command(self):
        """Stop autonomous heartbeat mode"""
        self.stop_autonomous_mode()
        return "🛑 Autonomous mode stopped"

    def autonomous_status_command(self):
        """Get autonomous execution status"""
        status = "🤖 Autonomous Status:\n\n"
        status += f"Running: {'✅ Yes' if self._running else '❌ No'}\n"
        status += f"Heartbeat interval: {self.heartbeat_interval} minutes\n"
        status += f"Triggers configured: {len(self.triggers)}\n"
        status += f"Execution history: {len(self.execution_history)} entries\n\n"
        
        if self.triggers:
            status += "📋 Triggers:\n"
            for tid, trigger in self.triggers.items():
                enabled = "✅" if trigger.enabled else "❌"
                last = trigger.last_run.strftime("%H:%M") if trigger.last_run else "Never"
                status += f"  {enabled} {trigger.skill_name} ({trigger.trigger_type.value}) - Last: {last}\n"
        
        return status

    def tool_list_command(self):
        """List available tools"""
        output = "🔧 Available Tools:\n\n"
        
        categories = {
            'System': ['system.run', 'system.notify', 'file.read', 'file.write', 'file.list'],
            'Browser': ['browser.open', 'browser.scrape', 'browser.click', 'browser.fill'],
            'Communication': ['email.read', 'email.send', 'telegram.send', 'discord.send'],
            'Data': ['calendar.read', 'calendar.create', 'search.web', 'api.call'],
            'Crypto': ['wallet.balance', 'dex.swap', 'token.price'],
        }
        
        for category, tools in categories.items():
            output += f"📁 {category}:\n"
            for tool in tools:
                available = "✅" if tool in self.tool_registry else "❌"
                output += f"  {available} {tool}\n"
            output += "\n"
        
        return output

    def tool_exec_command(self, tool_name: str, *args):
        """Execute a tool directly: tool_exec <tool_name> [args...]"""
        if not tool_name:
            return "❌ Usage: tool_exec <tool_name> [args...]\nExample: tool_exec system.run 'ls -la'"
        
        if tool_name not in self.tool_registry:
            return f"❌ Tool not found: {tool_name}\nUse 'tool_list' to see available tools"
        
        # Parse arguments as JSON if they look like JSON, otherwise as string
        try:
            if args:
                arg_str = ' '.join(args)
                # Try to parse as JSON
                if arg_str.startswith('{'):
                    parsed_args = json.loads(arg_str)
                else:
                    parsed_args = {'command': arg_str} if tool_name == 'system.run' else {'query': arg_str}
            else:
                parsed_args = {}
        except:
            parsed_args = {'query': ' '.join(args)}
        
        result = self.tool_registry[tool_name](**parsed_args)
        
        if result.get('success'):
            output = f"✅ Tool executed: {tool_name}\n"
            if 'stdout' in result:
                output += f"\nOutput:\n{result['stdout'][:500]}"
            if 'content' in result:
                output += f"\nContent:\n{result['content'][:500]}"
            return output
        else:
            return f"❌ Tool failed: {result.get('error', 'Unknown error')}"

    def get_commands(self):
        """Add autonomous commands"""
        base_commands = super().get_commands() if hasattr(super(), 'get_commands') else {}
        base_commands.update({
            'autonomous_start': self.autonomous_start_command,
            'autonomous_stop': self.autonomous_stop_command,
            'autonomous_status': self.autonomous_status_command,
            'tool_list': self.tool_list_command,
            'tool_exec': self.tool_exec_command,
        })
        return base_commands
