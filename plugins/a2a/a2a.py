"""
A2A Plugin — Agent-to-Agent protocol for AlleyBot.

Enables other AI agents to discover AlleyBot's capabilities and request tasks
via a standardized HTTP API. All requests pass through a 7-layer security
pipeline before execution.

AlleyBot ERC-8004 Agent #22899 on Ethereum mainnet.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.a2a.a2a_server import A2AServerMixin
from plugins.a2a.a2a_security import A2ASecurityMixin
from plugins.a2a.a2a_tasks import A2ATaskHandlerMixin


class A2APlugin(A2AServerMixin, A2ASecurityMixin, A2ATaskHandlerMixin, AlleyBotPlugin):
    """Agent-to-Agent protocol plugin for AlleyBot.

    Composes:
      - A2AServerMixin: HTTP server, A2A protocol endpoints
      - A2ASecurityMixin: Identity, payment, sanitization, rate limits, audit
      - A2ATaskHandlerMixin: Task registry, execution, sandboxing
    """

    def __init__(self, config):
        super().__init__(config)
        self._init_security()
        self._init_task_handler()
        self._init_server()

    def initialize(self, api, core):
        super().initialize(api, core)
        self._setup_a2a_server()

        auto_start = self.config.get('auto_start', False)
        if auto_start:
            self.start_a2a_server()

        print("🤝 A2A plugin initialized (Agent-to-Agent protocol)")

    def get_tasks(self):
        """Return scheduled tasks."""
        return {}

    def get_commands(self):
        """Return CLI/Telegram commands for A2A management."""
        return {
            'a2a_status': self.status_command,
            'a2a_start': self.start_command,
            'a2a_stop': self.stop_command,
            'a2a_tasks': self.tasks_command,
            'a2a_security': self.security_command,
            'a2a_audit': self.audit_command,
            'a2a_block': self.block_command,
            'a2a_unblock': self.unblock_command,
            'a2a_allow': self.allow_command,
        }

    def get_endpoints(self):
        """Return web endpoints (served by own Flask app, not analytics)."""
        return {}

    def cleanup(self):
        """Cleanup A2A plugin."""
        print("🤝 A2A plugin cleaned up")

    # ── Owner Commands ──────────────────────────────────────────────

    def status_command(self, *args):
        """Show A2A server status and statistics."""
        server_running = self._server_thread is not None and self._server_thread.is_alive()
        security = self.get_security_stats()
        task_stats = self.get_task_stats()
        endpoints = self.get_a2a_endpoints()

        lines = [
            "🤝 A2A Protocol Status",
            f"{'='*40}",
            f"Server: {'🟢 Running' if server_running else '🔴 Stopped'}",
            f"Port: {self._a2a_port}",
            f"",
            f"📊 Requests",
            f"  Total: {security['total_requests']}",
            f"  Rejected: {security['total_rejected']}",
            f"  Tasks executed: {task_stats['tasks_executed']}",
            f"  Tasks failed: {task_stats['tasks_failed']}",
            f"  Success rate: {task_stats['success_rate']}%",
            f"",
            f"🛡️ Security",
            f"  Blocklist: {security['blocklist_size']} agents",
            f"  Allowlist: {security['allowlist_size']} agents",
            f"  Active circuit breakers: {security['active_circuit_breakers']}",
            f"  Min reputation: {security['min_reputation']}",
            f"  Audit log: {security['audit_log_entries']} entries",
            f"",
            f"🌐 Endpoints",
        ]
        for name, url in endpoints.items():
            lines.append(f"  {name}: {url}")

        return '\n'.join(lines)

    def start_command(self, *args):
        """Start the A2A server."""
        if self._server_thread and self._server_thread.is_alive():
            return "🟢 A2A server is already running"
        self.start_a2a_server()
        return f"🚀 A2A server started on port {self._a2a_port}"

    def stop_command(self, *args):
        """Stop the A2A server (note: Flask dev server can't be gracefully stopped)."""
        if not self._server_thread or not self._server_thread.is_alive():
            return "🔴 A2A server is not running"
        # Flask dev server doesn't support graceful shutdown easily
        # In production, use gunicorn/uvicorn with proper signal handling
        return "⚠️ Server stop requires restart. Use production WSGI server for graceful shutdown."

    def tasks_command(self, *args):
        """List available A2A tasks and their tiers."""
        tasks = self.list_available_tasks()
        lines = ["📋 Available A2A Tasks", f"{'='*40}"]

        for name, info in tasks.items():
            tier_icon = '🟢' if info['tier'] == 'public' else '💰'
            price = f" (${info['price_usdc']} USDC)" if info.get('price_usdc') else ''
            lines.append(f"  {tier_icon} {name}{price}")
            lines.append(f"     {info['description']}")

        lines.append(f"\n🔒 Owner-only tasks are never exposed via A2A")
        return '\n'.join(lines)

    def security_command(self, *args):
        """Show security statistics."""
        stats = self.get_security_stats()
        lines = [
            "🛡️ A2A Security Stats",
            f"{'='*40}",
            f"Total requests: {stats['total_requests']}",
            f"Total rejected: {stats['total_rejected']}",
            f"Blocklist: {stats['blocklist_size']} agents",
            f"Allowlist: {stats['allowlist_size']} agents",
            f"Active circuit breakers: {stats['active_circuit_breakers']}",
            f"Rate-limited agents: {stats['rate_limited_agents']}",
            f"Min reputation: {stats['min_reputation']}",
            f"Audit entries: {stats['audit_log_entries']}",
        ]
        return '\n'.join(lines)

    def audit_command(self, *args):
        """Show recent audit log entries."""
        entries = self.get_audit_log(limit=15)
        if not entries:
            return "📋 No audit log entries yet"

        lines = ["📋 Recent A2A Audit Log", f"{'='*40}"]
        for e in entries:
            lines.append(f"  [{e['event']}] {e['agent_id']}: {e['detail']}")
            lines.append(f"    {e['timestamp']}")
        return '\n'.join(lines)

    def block_command(self, *args):
        """Block an agent. Usage: a2a_block <agent_id>"""
        if not args or not args[0]:
            return "Usage: a2a_block <agent_id>"
        agent_id = args[0].strip() if isinstance(args[0], str) else str(args[0])
        return self.block_agent(agent_id)

    def unblock_command(self, *args):
        """Unblock an agent. Usage: a2a_unblock <agent_id>"""
        if not args or not args[0]:
            return "Usage: a2a_unblock <agent_id>"
        agent_id = args[0].strip() if isinstance(args[0], str) else str(args[0])
        return self.unblock_agent(agent_id)

    def allow_command(self, *args):
        """Add an agent to the allowlist. Usage: a2a_allow <agent_id>"""
        if not args or not args[0]:
            return "Usage: a2a_allow <agent_id>"
        agent_id = args[0].strip() if isinstance(args[0], str) else str(args[0])
        return self.allow_agent(agent_id)
