import json
import os
from pathlib import Path
from typing import Dict

from plugin_manager import AlleyBotPlugin


class SimpleCounterPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "simple_counter"
        self.version = "1.0.0"
        self.counters: Dict[str, int] = {}
        self.data_file = Path(os.path.join(os.path.dirname(__file__), "..", "..", "data", "simple_counter.json"))
        self.load_counters()
    
    def get_commands(self) -> Dict[str, callable]:
        return {
            "counter_inc": self.counter_inc,
            "counter_get": self.counter_get,
            "counter_list": self.counter_list,
            "counter_reset": self.counter_reset,
        }
    
    def load_counters(self) -> None:
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.counters = {k: int(v) for k, v in data.items()}
                    else:
                        print(f"Warning: Invalid counter data format in {self.data_file}")
                        self.counters = {}
                print(f"Loaded {len(self.counters)} counters from {self.data_file}")
            else:
                print(f"No existing counter data at {self.data_file}")
        except Exception as e:
            print(f"Error: Failed to load counters: {e}")
            self.counters = {}
    
    def save_counters(self) -> None:
        try:
            os.makedirs(self.data_file.parent, exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump(self.counters, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save counters: {e}")
    
    def counter_inc(self, args: list) -> str:
        if len(args) < 1:
            return "Usage: counter_inc <name> [amount=1]"
        
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except (ValueError, IndexError):
            return "Amount must be an integer"
        
        if amount <= 0:
            return "Amount must be positive"
        
        current = self.counters.get(name, 0)
        new_value = current + amount
        self.counters[name] = new_value
        self.save_counters()
        return f"Counter '{name}' incremented by {amount}. New value: {new_value}"
    
    def counter_get(self, args: list) -> str:
        if len(args) < 1:
            return "Usage: counter_get <name>"
        
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        
        value = self.counters.get(name)
        
        if value is None:
            return f"No counter named '{name}' found"
        else:
            return f"Counter '{name}': {value}"
    
    def counter_list(self, args: list) -> str:
        if not args:
            pass
        
        if not self.counters:
            return "No counters have been created yet"
        
        lines = [f"{name}: {value}" for name, value in sorted(self.counters.items())]
        response = "Counters:\n" + "\n".join(lines)
        return response
    
    def counter_reset(self, args: list) -> str:
        if len(args) < 1:
            return "Usage: counter_reset <name>"
        
        name = args[0].strip()
        if not name:
            return "Counter name cannot be empty"
        
        old_value = self.counters.get(name)
        
        # Reset to 0 even if it doesn't exist yet
        self.counters[name] = 0
        self.save_counters()
        
        if old_value is None:
            return f"Created new counter '{name}' and set to 0"
        else:
            return f"Counter '{name}' has been reset from {old_value} to 0"


PLUGIN_INFO = {
    "name": "simple_counter",
    "version": "1.0.0",
    "description": "Simple persistent counters",
    "author": "AlleyBot",
}


def create_plugin(config=None):
    return SimpleCounterPlugin(config or {})