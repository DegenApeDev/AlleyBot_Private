# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict
import time
from difflib import get_close_matches
import re

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "2.0.0"
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
            "unknown_handler",
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
            full_input = " ".join(args)
            if not full_input:
                return "No input provided for unknown handler."

            command_name = self.get_command_key(full_input)
            parts = full_input.split(maxsplit=1)
            params_str = parts[1] if len(parts) > 1 else ""

            # Parse error chains
            extracted = None
            error_patterns = [
                r"plugin\s+(?:named\s+|)['\"]([^'\"]*)['\"]?\s*(?:not\s+found|doesn't\s+exist|unknown)",
                r"(?:no\s+|unknown\s+)?plugin\s+['\"]?([^'\" \t\n]+)['\"]?(?:\s+not\s+found)?",
                r"action\s+(?:['\"]([^'\"]*)['\"]\s+(?:missing|not\s+found|unknown))",
                r"(?:no\s+|unknown\s+)?action\s+['\"]?([^'\" \t\n]+)['\"]?(?:\s+missing)?",
            ]
            for pat in error_patterns:
                match = re.search(pat, full_input, re.I)
                if match:
                    extracted = match.group(1).strip().lower()
                    break
            if extracted:
                print(f"[UnknownHandler] Parsed error chain for '{extracted}' from '{full_input}'")
                if extracted in self.plugin_aliases:
                    real_command = self.plugin_aliases[extracted]
                    if real_command in self.known_plugins:
                        suggestion = f"!{real_command}"
                        if params_str:
                            suggestion += f" {params_str}"
                        return f"Error for '{extracted}': alias for '{real_command}'. Try {suggestion}."
                    else:
                        return f"Alias '{extracted}' points to unknown action/plugin '{real_command}'. Try !help."
                fuzzy_aliases = get_close_matches(extracted, self.alias_keys, n=1, cutoff=0.6)
                if fuzzy_aliases:
                    alias_used = fuzzy_aliases[0]
                    real_command = self.plugin_aliases[alias_used]
                    if real_command in self.known_plugins:
                        suggestion = f"!{real_command}"
                        if params_str:
                            suggestion += f" {params_str}"
                        return f"Error '{extracted}' ~ '{alias_used}' -> '{real_command}'. Try {suggestion}."
                fuzzy_known = get_close_matches(extracted, self.known_plugins, n=1, cutoff=0.6)
                if fuzzy_known:
                    real_command = fuzzy_known[0]
                    suggestion = f"!{real_command}"
                    if params_str:
                        suggestion += f" {params_str}"
                    return f"Error '{extracted}' similar to '{real_command}'. Try {suggestion}."
                self.last_unknown = full_input
                return f"Parsed error '{extracted}', no direct match. Try !core {extracted} or !help."

            # Exact alias resolution
            if command_name in self.plugin_aliases:
                real_command = self.plugin_aliases[command_name]
                if real_command not in self.known_plugins:
                    return f"Alias '{command_name}' points to unknown plugin '{real_command}'. Try '!help'."
                suggestion = f"!{real_command}"
                if params_str:
                    suggestion += f" {params_str}"
                print(f"[UnknownHandler] Resolved exact alias '{command_name}' -> '{real_command}'")
                return f"'{command_name}' is an alias for '{real_command}'. Try {suggestion}."

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
                    return f"'{command_name}' matches alias '{alias_used}' for '{real_command}'. Try {suggestion}."

            # Store original
            self.last_unknown = full_input

            # Track failures per command with decay
            now = time.time()
            if command_name in self.failure_counts:
                if now - self.last_failure_time.get(command_name, 0) > 3600:  # 1 hour decay
                    print(f"[UnknownHandler] Decaying failure count for '{command_name}'")
                    self.failure_counts[command_name] = 0
                    self.last_failure_time.pop(command_name, None)
            self.failure_counts[command_name] = self.failure_counts.get(command_name, 0) + 1
            current_failures = self.failure_counts[command_name]
            self.last_failure_time[command_name] = now
            print(f"[UnknownHandler] Unknown: '{full_input}'. Failures for '{command_name}': {current_failures}")

            if current_failures >= 5:
                return self._trigger_fallback(command_name, params_str)

            suggestions = self._generate_suggestions(full_input)
            return f"'{full_input}' unknown. {suggestions} Failure #{current_failures}/5 before fallback."
        except Exception as e:
            print(f"[UnknownHandler] Error in handle_unknown: {e}")
            self.last_unknown = None
            return "Error handling unknown. Try !help or !reset."

    def _generate_suggestions(self, unknown_input: str) -> str:
        command_lower = self.get_command_key(unknown_input)
        suggs = []
        # Fuzzy aliases
        fuzzy_a = get_close_matches(command_lower, self.alias_keys, n=3, cutoff=0.6)
        for fa in fuzzy_a:
            real = self.plugin_aliases[fa]
            suggs.append(f"!{real} ({fa})")
        # Fuzzy known
        fuzzy_k = get_close_matches(command_lower, self.known_plugins, n=3, cutoff=0.6)
        for fk in fuzzy_k:
            suggs.append(f"!{fk}")
        # Prefix matches
        for alias in self.alias_keys:
            if (len(alias) > 2 and
                (command_lower.startswith(alias) or
                 alias.startswith(command_lower) or
                 len(command_lower) >= 3 and command_lower[:3] == alias[:3])):
                real = self.plugin_aliases[alias]
                suggs.append(f"!{real} ({alias})")
        unique_suggs = list(dict.fromkeys(suggs))[:5]
        if unique_suggs:
            return "Suggestions: " + " | ".join(unique_suggs) + " | !help"
        return "Try !help | !chat | !core | !web_search"

    def _trigger_fallback(self, command_name: str, params_str: str) -> str:
        print(f"[UnknownHandler] Fallback triggered for '{command_name}' (5+ failures)")
        print(f"[UnknownHandler] Failure history for '{command_name}': {self.failure_counts.get(command_name, 0)}")
        # Self-improve: map to core
        if command_name not in self.plugin_aliases:
            self.plugin_aliases[command_name] = "core"
            self.alias_keys = list(self.plugin_aliases.keys())
            print(f"[UnknownHandler] Self-improved: added '{command_name}' -> 'core'")
        suggestion = f"!core {command_name}"
        if params_str:
            suggestion += f" {params_str}"
        # Reset count
        self.failure_counts[command_name] = 0
        self.last_failure_time.pop(command_name, None)
        return f"Self-improved after repeated failures: '{command_name}' now aliases 'core'. Try: {suggestion}"

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown command to retry."
        cmd = self.get_command_key(self.last_unknown)
        # Decrement failure count
        if cmd in self.failure_counts:
            self.failure_counts[cmd] = max(0, self.failure_counts[cmd] - 1)
            print(f"[UnknownHandler] Retry: failures for '{cmd}' now {self.failure_counts[cmd]}")
        # Check if now resolved
        if cmd in self.plugin_aliases:
            real = self.plugin_aliases[cmd]
            parts = self.last_unknown.split(maxsplit=1)
            params = parts[1] if len(parts) > 1 else ""
            suggestion = f"!{real}"
            if params:
                suggestion += f" {params}"
            return f"Retrying '{self.last_unknown}' -> resolved to {suggestion}"
        return f"Retrying last unknown: {self.last_unknown} (failures decremented)"

    def self_correct(self, args: list) -> str:
        print(f"[UnknownHandler] Self-correct invoked. Last: {self.last_unknown}")
        print(f"[UnknownHandler] Failures: {self.failure_counts}")
        if self.last_unknown:
            cmd = self.get_command_key(self.last_unknown)
            if cmd in self.failure_counts and self.failure_counts[cmd] >= 3:
                return f"High failures for '{cmd}': Consider config alias. Try !chat or !core {self.last_unknown}"
        return "Self-correct: No action needed. Use !retry or !reset."

    def reset_failures(self, args: list) -> str:
        before = len(self.failure_counts)
        self.failure_counts.clear()
        self.last_failure_time.clear()
        self.last_unknown = None
        print(f"[UnknownHandler] Reset {before} failure entries.")
        return f"Reset {before} tracked failures."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "2.0.0",
    "description": "Handles unknown commands with aliases, fuzzy matching, failure tracking, retry logic, and self-improvement via dynamic alias addition.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})