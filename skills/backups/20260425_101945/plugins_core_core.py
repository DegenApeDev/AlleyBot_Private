# plugins/core/core.py
from plugin_manager import AlleyBotPlugin
from typing import Dict
import time

class CorePlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "core"
        self.version = "1.0.0"
        self.start_time = time.time()
        print("CorePlugin v1.0.0 initialized - exposing default actions for execution stages.")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "help": self.cmd_help,
            "ping": self.cmd_ping,
            "status": self.cmd_status,
        }

    def get_actions(self) -> Dict[str, callable]:
        return {
            "unknown_handler": self.cmd_unknown_handler,
            "on_startup": self.on_startup,
            "on_shutdown": self.on_shutdown,
            "before_command": self.before_command,
            "after_command": self.after_command,
            "on_error": self.on_error,
        }

    def cmd_help(self, args: list) -> str:
        return """Core plugin commands:
!help     - Show this message
!ping     - Pong!
!status   - Check core status"""

    def cmd_ping(self, args: list) -> str:
        return "Pong! 🏓"

    def cmd_status(self, args: list) -> str:
        uptime = time.time() - self.start_time
        return f"CorePlugin v{self.version} active (uptime: {uptime:.1f}s) - handling essential utilities and default actions."

    def cmd_unknown_handler(self, args: list) -> str:
        try:
            failure_count = int(args[0]) if args else 0
        except ValueError:
            failure_count = 0
        if failure_count >= 5:
            return "Repeated unknown commands detected. Try asking naturally without '!' commands, or use !help for available options."
        elif failure_count >= 3:
            return "Unknown command. Try !help for a list of commands."
        else:
            return "Unknown command."

    def on_startup(self, args: list) -> str:
        print("CorePlugin: Handling bot startup")
        return "Core startup complete"

    def on_shutdown(self, args: list) -> str:
        print("CorePlugin: Handling bot shutdown")
        return "Core shutdown complete"

    def before_command(self, args: list) -> str:
        if args:
            print(f"CorePlugin: Before command '{args[0]}'")
        return ""

    def after_command(self, args: list) -> str:
        if args:
            print(f"CorePlugin: After command '{args[0]}'")
        return ""

    def on_error(self, args: list) -> str:
        error_msg = " ".join(args) if args else "Unknown error"
        print(f"CorePlugin: Error handler - {error_msg}")
        return f"Core error handler: {error_msg[:200]}..."

PLUGIN_INFO = {
    "name": "core",
    "version": "1.0.0",
    "description": "Core plugin providing essential commands, default action handlers for execution stages (startup/shutdown, command lifecycle, errors), and unknown command fallback.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return CorePlugin(config or {})