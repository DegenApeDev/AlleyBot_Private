# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict
from difflib import get_close_matches

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "1.2.0"
        self.plugin_aliases = {
            'clawbr_d': 'clawbr_debates',
            'deb': 'clawbr_debates',
            'd': 'clawbr_debates',
            'debate': 'clawbr_debates',
            'debates': 'clawbr_debates',
            'cb': 'clawbr_debates',
            'c': 'chat',
            'ch': 'chat',
            'chatgpt': 'chat',
            'gpt': 'chat',
            'convo': 'chat',
            'talk': 'chat',
            'core': 'core',
            'cr': 'core',
            'img': 'image_gen',
            'image': 'image_gen',
            'code': 'code_exec',
            'exec': 'code_exec',
            'search': 'web_search',
            'web': 'web_search',
        }
        self.known_plugins = [
            "help",
            "chat",
            "clawbr_debates",
            "image_gen",
            "code_exec",
            "web_search",
            "core",
            "unknown",
            "retry",
            "correct",
            "reset",
        ]
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
            "reset": self.reset_failures,
        }

    def handle_unknown(self, args: list) -> str:
        if not args:
            return "No input provided for unknown handler."

        full_command = args[0]
        command_name = full_command.strip().lower()
        params_str = " ".join(args[1:]) if len(args) > 1 else ""
        unknown_input = " ".join(args)

        # Resolve aliases before treating as unknown
        if command_name in self.plugin_aliases:
            real_command = self.plugin_aliases[command_name]
            # Validate target plugin is known
            if real_command not in self.known_plugins:
                return f"Alias '{full_command}' points to unknown plugin '{real_command}'. Try '!help'."
            suggestion = f"!{real_command}"
            if params_str:
                suggestion += f" {params_str}"
            print(f"[UnknownHandler] Resolved alias '{full_command}' -> '{real_command}'")
            return f"'{full_command}' is an alias for '{real_command}'. Try {suggestion}."

        # Store original
        self.last_unknown = unknown_input

        # Track failures per command
        if command_name not in self.failure_counts:
            self.failure_counts[command_name] = 0
        self.failure_counts[command_name] += 1
        current_failures = self.failure_counts[command_name]
        print(f"[UnknownHandler] Handling unknown action: '{unknown_input}'. Failure count for '{command_name}': {current_failures}")

        if current_failures >= 3:
            return self._trigger_fallback(command_name)

        suggestions = self._generate_suggestions(unknown_input)
        return f"Sorry, '{unknown_input}' is unknown. {suggestions} Failure #{current_failures}/3 before fallback."

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
                # Validate real plugin known
                if real in self.known_plugins:
                    suggestions.append(f"'{orig_cmd}' might be '{real}'? Try '!{real}'.")
                else:
                    print(f"[UnknownHandler] Alias '{alias}' points to unknown '{real}' - skipping suggestion.")

        # Keyword-based suggestions
        if "help" in lower_input or "list" in lower_input:
            suggestions.append("Try '!help' for available commands.")
        if any(word in lower_input for word in ["chat", "talk", "convo"]):
            suggestions.append("Try the 'chat' skill for conversation.")
        if "core" in lower_input or "fallback" in lower_input:
            suggestions.append("Try '!core' for fallback handling.")

        # Fuzzy matching on known plugins
        matches = get_close_matches(command_lower, self.known_plugins, n=3, cutoff=0.6)
        if matches:
            sugg = ", ".join(f"!{m}" for m in matches)
            suggestions.append(f"Similar: {sugg}")

        if suggestions:
            return "Suggestions: " + "; ".join(suggestions)
        return "Try '!help' or describe what you need."

    def _trigger_fallback(self, command_key: str) -> str:
        print(f"[UnknownHandler] Repeated failures (max 3) for '{command_key}'. Triggering core fallback.")
        self.failure_counts.pop(command_key, None)
        self.last_unknown = None
        fallback = f"!core {command_key}"
        return f"Max retries (3) exceeded for '{command_key}'. Counter reset. Fallback to core: {fallback}, or '!chat {command_key}', or '!help'."

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown to retry. Use !unknown <cmd> first."
        print(f"[UnknownHandler] Retry requested for: '{self.last_unknown}'.")
        last_key = self.get_command_key(self.last_unknown)
        if last_key in self.failure_counts:
            self.failure_counts[last_key] -= 1
            if self.failure_counts[last_key] <= 0:
                self.failure_counts.pop(last_key)
        correction = self._attempt_correction(self.last_unknown)
        if "Could not auto-correct" not in correction:
            self.last_unknown = None
            return f"Retry corrected: {correction}"
        else:
            current = self.failure_counts.get(last_key, 0)
            return f"Retry failed: still unknown. {correction} Failures now: {current}/3"

    def self_correct(self, args: list) -> str:
        to_correct = " ".join(args) if args else self.last_unknown
        if not to_correct:
            return "Nothing to correct. Use !correct <maybe_cmd> or after !unknown."
        print(f"[UnknownHandler] Self-correcting: '{to_correct}'.")
        command_key = self.get_command_key(to_correct)
        if command_key in self.failure_counts:
            self.failure_counts[command_key] -= 1
            if self.failure_counts[command_key] <= 0:
                self.failure_counts.pop(command_key)
        correction = self._attempt_correction(to_correct)
        if "Could not auto-correct" not in correction:
            if to_correct == self.last_unknown:
                self.last_unknown = None
            return f"Corrected: {correction}"
        else:
            current = self.failure_counts.get(command_key, 0)
            return f"Correction failed: {correction} Failures: {current}/3"

    def reset_failures(self, args: list) -> str:
        prev_count = len(self.failure_counts)
        self.failure_counts.clear()
        self.last_unknown = None
        print(f"[UnknownHandler] Reset {prev_count} failure counts.")
        return f"Reset {prev_count} failure counters and last unknown. Fresh start!"

    def _attempt_correction(self, unknown_input: str) -> str:
        # Check aliases first
        parts = unknown_input.split(maxsplit=1)
        if parts:
            command_name = parts[0].strip().lower()
            if command_name in self.plugin_aliases:
                real = self.plugin_aliases[command_name]
                if real in self.known_plugins:
                    params = parts[1] if len(parts) > 1 else ""
                    use_cmd = f"!{real}"
                    if params:
                        use_cmd += f" {params}"
                    corrected = f"{real}"
                    if params:
                        corrected += f" {params}"
                    return f"Corrected to '{corrected}'. Try {use_cmd}."
                else:
                    return f"Alias targets unknown plugin '{real}'. Try '!help'."

        # Spell check / intent mappings
        lower_input = unknown_input.lower()
        corrections = {
            "helo": "hello - use '!chat hello'",
            "helllo": "hello - use '!chat hello'",
            "hi": "hello - use '!chat hi'",
            "bye": "goodbye - use '!chat bye'",
            "goodbye": "goodbye - use '!chat goodbye'",
            "image": "image_gen - use '!image_gen <prompt>'",
            "img": "image_gen - use '!image_gen <prompt>'",
            "pic": "image_gen - use '!image_gen <prompt>'",
            "picture": "image_gen - use '!image_gen <prompt>'",
            "code": "code_exec - use '!code_exec <code>'",
            "exec": "code_exec - use '!code_exec <code>'",
            "python": "code_exec - use '!code_exec <python code>'",
            "search": "web_search - use '!web_search <query>'",
            "google": "web_search - use '!web_search <query>'",
            "core": "core - use '!core <input>'",
        }
        for key, value in corrections.items():
            if key in lower_input:
                return value
        return f"Could not auto-correct '{unknown_input}'. Try '!help'."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "1.2.0",
    "description": "Handles unknown commands with aliases, suggestions, failure tracking, retry, correct, reset, and core fallback.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})