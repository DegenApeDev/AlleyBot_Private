import json
import os
from typing import Dict, Optional

from plugins.base_plugin import BasePlugin


class SimpleCounter(BasePlugin):
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.counters: Dict[str, int] = {}
        self.data_file = os.path.join(
            os.path.dirname(__file__),
            "counters.json",
        )
        self.load_counters()

    def load_counters(self) -> None:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.counters = json.load(f)
                self.logger.info(f"Loaded {len(self.counters)} counters from file")
            else:
                self.logger.info("No counters file found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load counters: {e}")
            self.counters = {}

    def save_counters(self) -> None:
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.counters, f, indent=2)
            self.logger.debug("Counters saved to file")
        except Exception as e:
            self.logger.error(f"Failed to save counters: {e}")

    async def handle_command(self, command: str, args: list) -> str:
        if command == "counter_inc":
            return await self.counter_inc(args)
        elif command == "counter_dec":
            return await self.counter_dec(args)
        elif command == "counter_get":
            return await self.counter_get(args)
        elif command == "counter_list":
            return await self.counter_list()
        elif command == "counter_reset":
            return await self.counter_reset(args)
        else:
            return f"Unknown counter command: {command}"

    async def counter_inc(self, args: list) -> str:
        if not args:
            return "Usage: counter_inc <name> [amount=1]"
        
        name = args[0]
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            return f"Invalid amount: {args[1]}"
        
        if amount <= 0:
            return "Amount must be positive"
        
        current = self.counters.get(name, 0)
        new_value = current + amount
        self.counters[name] = new_value
        self.save_counters()
        
        return f"Incremented '{name}' by {amount}. New value: {new_value}"

    async def counter_dec(self, args: list) -> str:
        if not args:
            return "Usage: counter_dec <name> [amount=1]"
        
        name = args[0]
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            return f"Invalid amount: {args[1]}"
        
        if amount <= 0:
            return "Amount must be positive"
        
        current = self.counters.get(name, 0)
        new_value = current - amount
        self.counters[name] = new_value
        self.save_counters()
        
        return f"Decremented '{name}' by {amount}. New value: {new_value}"

    async def counter_get(self, args: list) -> str:
        if not args:
            return "Usage: counter_get <name>"
        
        name = args[0]
        value = self.counters.get(name)
        
        if value is None:
            return f"No counter named '{name}' found"
        
        return f"Counter '{name}': {value}"

    async def counter_list(self) -> str:
        if not self.counters:
            return "No counters defined yet"
        
        lines = ["Current counters:"]
        for name in sorted(self.counters.keys()):
            lines.append(f"  {name}: {self.counters[name]}")
        
        return "\n".join(lines)

    async def counter_reset(self, args: list) -> str:
        if not args:
            return "Usage: counter_reset <name>"
        
        name = args[0]
        
        if name not in self.counters:
            return f"No counter named '{name}' found"
        
        old_value = self.counters.pop(name)
        self.save_counters()
        
        return f"Reset counter '{name}' (was {old_value})"

    def get_available_commands(self) -> Dict[str, str]:
        return {
            "counter_inc": "Increment a counter by specified amount (default 1)",
            "counter_dec": "Decrement a counter by specified amount (default 1)",
            "counter_get": "Get current value of a counter",
            "counter_list": "List all counters and their values",
            "counter_reset": "Remove a counter completely",
        }