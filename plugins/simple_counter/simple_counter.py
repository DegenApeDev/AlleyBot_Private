import json
import os
import threading
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
        self.lock = threading.Lock()
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
            "counter_get": self.counter_get,
            "counter_list": self.counter_list,
            "counter_reset": self.counter_reset,
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
        
        with self.lock:
            current = self.counters.get(name, 0)
            new_value = current + amount
            self.counters[name] = new_value
            self.save()
        
        return f"Incremented '{name}' by {amount}. New value: {new_value}"

    def counter_get(self, args: list) -> str:
        if not args:
            return "Usage: counter_get <name>"
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        
        with self.lock:
            value = self.counters.get(name)
        
        if value is None:
            return f"No counter named '{name}' found"
        
        return f"Counter '{name}': {value}"

    def counter_list(self) -> str:
        with self.lock:
            if not self.counters:
                return "No counters defined yet"
            
            lines = ["Current counters:"]
            
            predefined_names = ["posts", "debates", "yields", "engagements"]
            
            lines.append("Predefined metrics:")
            
            for name in predefined_names:
                value = self.counters.get(name, 0)
                lines.append(f"  {name}: {value}")