import json
import os
from typing import Dict

from plugin_manager import AlleyBotPlugin


class SimpleCounterPlugin(AlleyBotPlugin):
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.plugin_manager = plugin_manager
        self.name = "simple_counter"
        self.version = "1.0.0"
        self.counters: Dict[str, int] = {}
        self.data_file = os.path.join(
            os.path.dirname(__file__),
            "counters.json",
        )
        self.load()
        self.ensure_predefined()
        self.save()

    def ensure_predefined(self) -> None:
        predefined = ["posts", "debates", "yields", "engagements"]
        for name in predefined:
            self.counters.setdefault(name, 0)

    def load(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.counters = {k: int(v) for k, v in data.items()}
                    else:
                        self.plugin_manager.logger.warning("Invalid counters file format, starting fresh")
                        self.counters = {}
                self.plugin_manager.logger.info(f"Loaded {len(self.counters)} counters from file")
            else:
                self.plugin_manager.logger.info("No counters file found, starting fresh")
        except Exception as e:
            self.plugin_manager.logger.error(f"Failed to load counters: {e}")
            self.counters = {}

    def save(self) -> None:
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.counters, f, indent=2)
            self.plugin_manager.logger.debug("Counters saved to file")
        except Exception as e:
            self.plugin_manager.logger.error(f"Failed to save counters: {e}")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "counter_inc": self.counter_inc,
            "counter_dec": self.counter_dec,
            "counter_show": self.counter_show,
            "counter_list": self.counter_list,
            "counter_stats": self.counter_stats,
        }

    def counter_inc(self, args: list) -> str:
        if not args:
            return "Usage: counter_inc <name> [amount=1]"
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except (ValueError, IndexError):
            return f"Invalid amount: {args[1] if len(args) > 1 else 'N/A'}"
        if amount <= 0:
            return "Amount must be positive"
        current = self.counters.get(name, 0)
        new_value = current + amount
        self.counters[name] = new_value
        self.save()
        return f"Incremented '{name}' by {amount}. New value: {new_value}"

    def counter_dec(self, args: list) -> str:
        if not args:
            return "Usage: counter_dec <name> [amount=1]"
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except (ValueError, IndexError):
            return f"Invalid amount: {args[1] if len(args) > 1 else 'N/A'}"
        if amount <= 0:
            return "Amount must be positive"
        current = self.counters.get(name, 0)
        new_value = max(0, current - amount)
        self.counters[name] = new_value
        self.save()
        if new_value < current:
            return f"Decremented '{name}' by {amount}. New value: {new_value}"
        else:
            return f"Counter '{name}' was already 0, no change."

    def counter_show(self, args: list) -> str:
        if not args:
            return "Usage: counter_show <name>"
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        value = self.counters.get(name)
        if value is None:
            return f"No counter named '{name}' found"
        return f"Counter '{name}': {value}"

    def counter_list(self) -> str:
        if not self.counters:
            return "No counters defined yet"
        lines = ["Current counters:"]
        for name in sorted(self.counters.keys()):
            lines.append(f"  {name}: {self.counters[name]}")
        return "\n".join(lines)

    def counter_stats(self, args: list) -> str:
        counters = self.counters
        if not counters:
            return "No counters defined."
        num = len(counters)
        total = sum(counters.values())
        avg = total / num if num > 0 else 0
        lines = [
            f"Statistics:",
            f"  Number of counters: {num}",
            f"  Total count: {total}",
            f"  Average: {avg:.1f}",
            "Predefined counters:",
        ]
        predefined = ["posts", "debates", "yields", "engagements"]
        for name in predefined:
            v = counters.get(name, 0)
            lines.append(f"  {name}: {v}")
        return "\n".join(lines)


PLUGIN_INFO = {
    "name": "simple_counter",
    "version": "1.0.0",
    "description": "Simple counter plugin for tracking posts, debates, yields, engagements and custom counters.",
    "author": "AlleyBot"
}


def create_plugin():
    return SimpleCounterPlugin