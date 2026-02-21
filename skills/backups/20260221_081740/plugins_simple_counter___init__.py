import json
import os
from pathlib import Path
from typing import Dict, Optional

from alleybot import BasePlugin, Message


class SimpleCounter(BasePlugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.counters: Dict[str, int] = {}
        self.data_file = Path("data/simple_counter.json")
        self.load_counters()

    def load_counters(self) -> None:
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    self.counters = json.load(f)
                self.logger.info(f"Loaded {len(self.counters)} counters from {self.data_file}")
            else:
                self.logger.info(f"No existing counter data at {self.data_file}")
        except Exception as e:
            self.logger.error(f"Failed to load counters: {e}")
            self.counters = {}

    def save_counters(self) -> None:
        try:
            os.makedirs(self.data_file.parent, exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump(self.counters, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save counters: {e}")

    async def handle_message(self, message: Message) -> None:
        if not message.text.startswith("counter_"):
            return

        parts = message.text.split()
        command = parts[0]

        if command == "counter_inc":
            await self.counter_inc(message, parts[1:])
        elif command == "counter_dec":
            await self.counter_dec(message, parts[1:])
        elif command == "counter_get":
            await self.counter_get(message, parts[1:])
        elif command == "counter_list":
            await self.counter_list(message)
        elif command == "counter_reset":
            await self.counter_reset(message, parts[1:])

    async def counter_inc(self, message: Message, args: list) -> None:
        if len(args) < 1:
            await message.reply("Usage: counter_inc <name> [amount=1]")
            return

        name = args[0]
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            await message.reply("Amount must be an integer")
            return

        if amount <= 0:
            await message.reply("Amount must be positive")
            return

        current = self.counters.get(name, 0)
        new_value = current + amount
        self.counters[name] = new_value
        self.save_counters()
        await message.reply(f"Counter '{name}' incremented by {amount}. New value: {new_value}")

    async def counter_dec(self, message: Message, args: list) -> None:
        if len(args) < 1:
            await message.reply("Usage: counter_dec <name> [amount=1]")
            return

        name = args[0]
        try:
            amount = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            await message.reply("Amount must be an integer")
            return

        if amount <= 0:
            await message.reply("Amount must be positive")
            return

        current = self.counters.get(name, 0)
        new_value = current - amount
        self.counters[name] = new_value
        self.save_counters()
        await message.reply(f"Counter '{name}' decremented by {amount}. New value: {new_value}")

    async def counter_get(self, message: Message, args: list) -> None:
        if len(args) < 1:
            await message.reply("Usage: counter_get <name>")
            return

        name = args[0]
        value = self.counters.get(name)
        
        if value is None:
            await message.reply(f"No counter named '{name}' found")
        else:
            await message.reply(f"Counter '{name}': {value}")

    async def counter_list(self, message: Message) -> None:
        if not self.counters:
            await message.reply("No counters have been created yet")
            return

        lines = [f"{name}: {value}" for name, value in sorted(self.counters.items())]
        
        if len(lines) <= 10:
            response = "Counters:\n" + "\n".join(lines)