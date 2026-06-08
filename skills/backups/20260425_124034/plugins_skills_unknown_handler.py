# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict
import time
from difflib import get_close_matches

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "1.5.0"
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
        self.alias_keys = list(self.plugin_aliases.keys())
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
        self.last_failure_time = {}
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
        try:
            if not args:
                return "No input provided for unknown handler."

            full_command = args[0]
            command_name = full_command.strip().lower()
            params_str = " ".join(args[1:]) if len(args) > 1 else ""
            unknown_input = " ".join(args)

            # Exact alias resolution
            if command_name in self.plugin_aliases:
                real_command = self.plugin_aliases[command_name]
                if real_command not in self.known_plugins:
                    return f"Alias '{full_command}' points to unknown plugin '{real_command}'. Try '!help'."
                suggestion = f"!{real_command}"
                if params_str:
                    suggestion += f" {params_str}"
                print(f"[UnknownHandler] Resolved exact alias '{full_command}' -> '{real_command}'")
                return f"'{full_command}' is an alias for '{real_command}'. Try {suggestion}."

            # Fuzzy alias resolution
            fuzzy_aliases = get_close_matches(command_name, self.alias_keys, n=1, cutoff=0.6)
            if fuzzy_aliases:
                alias_used = fuzzy_aliases[0]
                real_command = self.plugin_aliases[alias_used]
                if real_command in self.known_plugins:
                    suggestion = f"!{real_command}"
                    if params_str:
                        suggestion += f" {params_str}"
                    print(f"[UnknownHandler] Fuzzy-resolved '{command_name}' ~ '{alias_used}' -> '{real_command}'")
                    return f"'{full_command}' closely matches alias '{alias_used}' for '{real_command}'. Try {suggestion}."

            # Store original
            self.last_unknown = unknown_input

            # Track failures per command with decay
            now = time.time()
            if command_name in self.failure_counts:
                if now - self.last_failure_time.get(command_name, 0) > 3600:  # 1 hour decay
                    print(f"[UnknownHandler] Decaying old failure count for '{command_name}'")
                    self.failure_counts[command_name] = 0
                    self.last_failure_time.pop(command_name, None)
            self.failure_counts[command_name] = self.failure_counts.get(command_name, 0) + 1
            current_failures = self.failure_counts[command_name]
            self.last_failure_time[command_name] = now
            print(f"[UnknownHandler] Handling unknown action: '{unknown_input}'. Failure count for '{command_name}': {current_failures}")

            if current_failures >= 5:
                return self._trigger_fallback(command_name)

            suggestions = self._generate_suggestions(unknown_input)
            return f"Sorry, '{unknown_input}' is unknown. {suggestions} Failure #{current_failures}/5 before fallback."
        except Exception as e:
            print(f"[UnknownHandler] Unexpected error in handle_unknown: {e}")
            self.last_unknown = None
            return "An error occurred handling unknown. Try !help or !reset."

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
        command_lower = self.get_command_key(unknown_input)
        matches = get_close_matches(command_lower, self.known_plugins, n=3, cutoff=0.6)
        if matches:
            sugg = ", ".join(f"!{m}" for m in matches)
            suggestions.append(f"Similar: {sugg}")

        if suggestions:
            return "Suggestions: " + "; ".join(suggestions[:5])  # Limit to 5
        return "Try '!help' or describe what you need."

    def _trigger_fallback(self, command_key: str) -> str:
        print(f"[UnknownHandler] Repeated failures (max 5) for '{command_key}'. Triggering core fallback.")
        self.failure_counts.pop(command_key, None)
        self.last_failure_time.pop(command_key, None)
        fallback = f"!core {command_key}"
        return f"Max retries (5) exceeded for '{command_key}'. Counters reset. Fallback to core: {fallback}, or '!chat {command_key}', or '!help'."

    def _attempt_correction(self, input_str: str) -> str:
        parts = input_str.split(maxsplit=1)
        command_key = parts[0].strip().lower() if parts else ""
        params_str = parts[1] if len(parts) > 1 else ""
        if not command_key:
            return "Could not auto-correct: empty input."

        # Fuzzy match on known plugins/commands
        matches = get_close_matches(command_key, self.known_plugins, n=1, cutoff=0.8)
        if matches:
            real_plugin = matches[0]
            suggestion = f"!{real_plugin}"
            if params_str:
                suggestion += f" {params_str}"
            return f"Auto-corrected '{input_str}' to '{suggestion}' (matched '{real_plugin}')."

        # Fuzzy match on aliases
        alias_matches = get_close_matches(command_key, self.alias_keys, n=1, cutoff=0.75)
        if alias_matches:
            alias = alias_matches[0]
            real_plugin = self.plugin_aliases[alias]
            if real_plugin in self.known_plugins:
                suggestion = f"!{real_plugin}"
                if params_str:
                    suggestion += f" {params_str}"
                return f"Auto-corrected '{input_str}' via alias '{alias}' to '{suggestion}'."

        return "Could not auto-correct: no confident matches found."

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown to retry. Use !unknown <cmd> first."
        print(f"[UnknownHandler] Re-suggesting for last unknown: '{self.last_unknown}'")
        suggestions = self._generate_suggestions(self.last_unknown)
        command_name = self.get_command_key(self.last_unknown)
        current_failures = self.failure_counts.get(command_name, 0)
        return f"Last unknown: '{self.last_unknown}' (failures: {current_failures}). {suggestions}"

    def self_correct(self, args: list) -> str:
        target = self.last_unknown or (" ".join(args) if args else None)
        if not target:
            return "Nothing to correct. Provide input or use after !unknown."
        correction = self._attempt_correction(target)
        print(f"[UnknownHandler] Self-correction for '{target}': {correction}")
        return correction

    def reset_failures(self, args: list) -> str:
        before = len(self.failure_counts)
        self.failure_counts.clear()
        self.last_failure_time.clear()
        self.last_unknown = None
        print(f"[UnknownHandler] Reset {before} failure counters.")
        return f"Reset {before} failure trackers and last unknown."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "1.5.0",
    "description": "Handles unknown commands with aliases, fuzzy matching, failure tracking with decay, suggestions, auto-correction, and fallback to core.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})