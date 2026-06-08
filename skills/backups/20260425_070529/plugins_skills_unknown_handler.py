# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "1.0.0"
        self.plugin_aliases = {
            'clawbr_d': 'clawbr_debates',
            'deb': 'clawbr_debates',
            'd': 'clawbr_debates',
        }
        self.failure_counts = {}
        self.last_unknown = None

    def get_command_key(self, input_str: str) -> str:
        if not input_str or not input_str.strip():
            return ''
        return input_str.split(maxsplit=1)[0].strip().lower()

    def get_commands(self) -> Dict[str, callable]:
        return {
            "unknown": self.handle_unknown,
            "retry": self.retry_last,
            "correct": self.self_correct,
        }

    def handle_unknown(self, args: list) -> str:
        if not args:
            return "No input provided for unknown handler."

        full_command = args[0]
        command_name = full_command.strip().lower()
        params_str = " ".join(args[1:]) if len(args) > 1 else ""

        # Resolve aliases before treating as unknown
        if command_name in self.plugin_aliases:
            real_command = self.plugin_aliases[command_name]
            suggestion = f"!{real_command}"
            if params_str:
                suggestion += f" {params_str}"
            print(f"[UnknownHandler] Resolved alias '{full_command}' -> '{real_command}'")
            return f"'{full_command}' is an alias for '{real_command}'. Try {suggestion}."

        # Store original
        self.last_unknown = " ".join(args)

        # Track failures per command
        if command_name not in self.failure_counts:
            self.failure_counts[command_name] = 0
        self.failure_counts[command_name] += 1
        current_failures = self.failure_counts[command_name]
        print(f"[UnknownHandler] Handling unknown action: '{self.last_unknown}'. Failure count for '{command_name}': {current_failures}")

        if current_failures >= 3:
            return self._trigger_fallback(command_name)

        suggestions = self._generate_suggestions(self.last_unknown)
        return f"Sorry, '{self.last_unknown}' is unknown to me. {suggestions} Failure #{current_failures}/3 before fallback."

    def _generate_suggestions(self, unknown_input: str) -> str:
        lower_input = unknown_input.lower()
        suggestions = []

        # Check for partial alias matches
        parts = unknown_input.split()
        command_lower = parts[0].lower().strip() if parts else ''
        orig_cmd = parts[0] if parts else ''
        for alias, real in self.plugin_aliases.items():
            if (command_lower == alias or
                command_lower.startswith(alias) or
                alias.startswith(command_lower)):
                suggestions.append(f"'{orig_cmd}' might be '{real}'? Try '!{real}'.")
                break

        if "help" in lower_input:
            suggestions.append("Try '!help' for available commands.")
        if any(word in lower_input for word in ["chat", "talk"]):
            suggestions.append("Try the 'chat' skill for conversation.")

        if suggestions:
            return "Suggestions: " + "; ".join(suggestions)
        return "Try '!help' or describe what you need."

    def _trigger_fallback(self, command_key: str) -> str:
        print(f"[UnknownHandler] Repeated failures (max 3 attempts) for '{command_key}' detected. Triggering fallback to core plugin and reset.")
        self.failure_counts.pop(command_key, None)
        self.last_unknown = None
        return f"Too many unknown actions for '{command_key}' (max 3 retries exceeded). Resetting context. Fallback to core plugin. How can I assist you now? Try '!help'."

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown action to retry."
        print(f"[UnknownHandler] Retry requested for: '{self.last_unknown}'.")
        last_key = self.get_command_key(self.last_unknown)
        if last_key in self.failure_counts:
            self.failure_counts[last_key] -= 1
            if self.failure_counts[last_key] <= 0:
                self.failure_counts.pop(last_key)
        correction = self._attempt_correction(self.last_unknown)
        current = self.failure_counts.get(last_key, 0)
        if "Could not auto-correct" not in correction:
            return f"Retry with correction: {correction}"
        else:
            return f"Retry failed: still unknown. {correction} Failures now: {current}/3"

    def self_correct(self, args: list) -> str:
        print("[UnknownHandler] Self-correction mechanism activated.")
        if not self.last_unknown:
            return "No recent error to correct. Use after an 'unknown' event."
        last_key = self.get_command_key(self.last_unknown)
        if last_key in self.failure_counts:
            self.failure_counts[last_key] -= 1
            if self.failure_counts[last_key] <= 0:
                self.failure_counts.pop(last_key)
        correction = self._attempt_correction(self.last_unknown)
        return f"Self-correcting '{self.last_unknown}': {correction}"

    def _attempt_correction(self, unknown_input: str) -> str:
        # Check aliases first
        parts = unknown_input.split(maxsplit=1)
        if parts:
            command_name = parts[0].strip().lower()
            if command_name in self.plugin_aliases:
                real = self.plugin_aliases[command_name]
                params = parts[1] if len(parts) > 1 else ""
                use_cmd = f"!{real}"
                if params:
                    use_cmd += f" {params}"
                corrected = f"{real}"
                if params:
                    corrected += f" {params}"
                return f"Corrected to '{corrected}'. Try {use_cmd}."

        # Simple spell check or intent guess
        lower_input = unknown_input.lower().strip()
        corrections = {
            "helo": "hello - use '!chat hello'",
            "helllo": "hello - use '!chat hello'",
            "hi": "hello - use '!chat hi'",
            "bye": "goodbye - use '!chat bye'",
            "goodbye": "goodbye - use '!chat goodbye'",
        }
        for key, corr in corrections.items():
            if key in lower_input:
                return corr
        return "Could not auto-correct. Please rephrase your request."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "1.0.0",
    "description": "Handles unknown actions, plugin aliases (e.g., clawbr_d -> clawbr_debates), per-command retry logic (max 3 attempts per command), fallback to core plugin, self-correction, partial suggestions, and dispatching logic to prevent repeated failures across commands.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})