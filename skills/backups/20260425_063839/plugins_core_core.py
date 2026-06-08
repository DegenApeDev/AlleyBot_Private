# plugins/core/core.py
from plugin_manager import AlleyBotPlugin
from typing import Dict

class CorePlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "core"
        self.version = "1.0.0"
    
    def get_commands(self) -> Dict[str, callable]:
        return {
            "help": self.cmd_help,
            "ping": self.cmd_ping,
            "status": self.cmd_status,
            "unknown_handler": self.cmd_unknown_handler,
        }
    
    def cmd_help(self, args: list) -> str:
        return """Core plugin commands:
!help     - Show this message
!ping     - Pong!
!status   - Check core status"""
    
    def cmd_ping(self, args: list) -> str:
        return "Pong! 🏓"
    
    def cmd_status(self, args: list) -> str:
        return f"CorePlugin v{self.version} active - handling essential utilities."
    
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

PLUGIN_INFO = {
    "name": "core",
    "version": "1.0.0",
    "description": "Basic CorePlugin class with essential actions, utilities, and unknown handler for repeated failures.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return CorePlugin(config or {})