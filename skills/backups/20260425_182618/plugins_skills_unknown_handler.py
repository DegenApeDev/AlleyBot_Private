# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict, Callable
import time
from difflib import get_close_matches
import re

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "3.0.0"
        self.plugin_aliases = {
            'clawbr_d': 'clawbr_debates',
            'clawbrd': 'clawbr_debates',
            'deb': 'clawbr_debates',
            'd': 'clawbr_debates',
            'debate': 'clawbr_debates',
            'debates': 'clawbr_debates',
            'cb': 'clawbr_debates',
            'cb_d': 'clawbr_debates',
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
            'img_gen': 'image_gen',
            'imagegen': 'image_gen',
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
        self.known_plugins_set = set(self.known_plugins)
        self.failure_counts = {}
        self.last_failure_time = {}
        self.last_unknown = None

    def get_command_key(self, input_str: str) -> str:
        if not input_str or not input_str.strip():
            return ''
        return input_str.split(maxsplit=1)[0].strip().lower()

    def get_commands(self) -> Dict[str, Callable]:
        return {
            "unknown": self.handle_unknown,
            "retry": self.retry_last,
            "correct": self.self_correct,
            "reset": self.reset_failures,
        }

    def _trigger_fallback(self, command_name: str, params_str: str) -> str:
        fallback = f"!core handle unknown '{command_name}'"
        if params_str:
            fallback += f" with params '{params_str}'"
        fallback = fallback.strip()
        return f"Fallback triggered for '{command_name}': Try {fallback} or !chat for natural handling."

    def handle_unknown(self, args: list) -> str:
        full_input = " ".join(args)
        try:
            if not full_input:
                return "No input provided for unknown handler."

            command_name = self.get_command_key(full_input)
            parts = full_input.split(maxsplit=1)
            params_str = parts[1] if len(parts) > 1 else ""

            # Prevent repeated calls
            if full_input == self.last_unknown:
                print(f"[UnknownHandler] Repeated unknown call for '{full_input}', forcing fallback.")
                return self._trigger_fallback(command_name, params_str)

            # Parse error chains, enhanced for ActionRouter
            extracted = None
            error_patterns = [
                r"plugin\s+(?:named\s+|)['\"]([^'\"]*)['\"]?\s*(?:not\s+found|doesn't\s+exist|unknown)",
                r"(?:no\s+|unknown\s+)?plugin\s+['\"]?([^'\" \t\n]+)['\"]?(?:\s+not\s+found)?",
                r"action\s+(?:['\"]([^'\"]*)['\"]\s+(?:missing|not\s+found|unknown))",
                r"(?:no\s+|unknown\s+)?action\s+['\"]?([^'\" \t\n]+)['\"]?(?:\s+missing)?",
                r"ActionRouter\[[^\]]+\]:\s*(?:No action|Action not found)\s+['\"]?([^'\" \t\n]+)['\"]?(?:\s+in\s+plugin)?",
                r"plugin\s+['\"]([^'\"]+)['\"]\s+(?:action|command)\s+['\"]([^'\"]*)['\"]",
                r"(?:Failed to find|No such)\s+(?:plugin|action)\s+['\"]([^'\"]+)['\"]",
                r"Unknown\s+action\s+['\"]([^'\"]*)['\"]?\s+(?:in|from)\s+['\"]([^'\"]*)['\"]?",
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
                    if real_command in self.known_plugins_set:
                        suggestion = f"!{real_command}"
                        if params_str:
                            suggestion += f" {params_str}"
                        return f"Error for '{extracted}': alias for '{real_command}'. Try {suggestion}."
                    else:
                        return f"Alias '{extracted}' points to unknown plugin '{real_command}'. Try !help."
                fuzzy_aliases = get_close_matches(extracted, self.alias_keys, n=1, cutoff=0.6)
                if fuzzy_aliases:
                    alias_used = fuzzy_aliases[0]
                    real_command = self.plugin_aliases[alias_used]
                    if real_command in self.known_plugins_set:
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

            # Exact alias resolution with pre-check
            if command_name in self.plugin_aliases:
                real_command = self.plugin_aliases[command_name]
                if real_command not in self.known_plugins_set:
                    return f"Alias '{command_name}' points to unknown plugin '{real_command}'. Try '!help'."
                suggestion = f"!{real_command}"
                if params_str:
                    suggestion += f" {params_str}"
                print(f"[UnknownHandler] Resolved exact alias '{command_name}' -> '{real_command}'")
                return f"'{command_name}' is an alias for '{real_command}'. Try {suggestion}."

            # Fuzzy alias resolution with pre-check
            fuzzy_aliases = get_close_matches(command_name, self.alias_keys, n=1, cutoff=0.6)
            if fuzzy_aliases:
                alias_used = fuzzy_aliases[0]
                real_command = self.plugin_aliases[alias_used]
                if real_command in self.known_plugins_set:
                    suggestion = f"!{real_command}"
                    if params_str:
                        suggestion += f" {params_str}"
                    print(f"[UnknownHandler] Fuzzy-resolved '{command_name}' ~ '{alias_used}' -> '{real_command}'")
                    return f"'{command_name}' matches alias '{alias_used}' for '{real_command}'. Try {suggestion}."

            # Store original for retry
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

            # Fallback logic based on failure count
            if current_failures >= 5:
                return self._trigger_fallback(command_name, params_str)
            elif current_failures >= 3:
                fuzzy_known = get_close_matches(command_name, self.known_plugins, n=3, cutoff=0.6)
                suggestions = ", ".join(fuzzy_known) if fuzzy_known else "none"
                return f"Persistent unknown '{command_name}' (failures: {current_failures}). Similar: {suggestions}. !retry?"
            else:
                return f"Unknown '{command_name}' (failures: {current_failures}). !help | !retry | !correct {command_name}"

        except Exception as e:
            print(f"[UnknownHandler] Error in handle_unknown: {e}")
            return "Handler error. Try !reset."

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown command to retry."
        command_name = self.get_command_key(self.last_unknown)
        params_str = self.last_unknown.split(maxsplit=1)[1] if " " in self.last_unknown else ""
        # Reset failure count for this command
        self.failure_counts.pop(command_name, None)
        self.last_failure_time.pop(command_name, None)
        print(f"[UnknownHandler] Retry setup for '{self.last_unknown}' (failures reset)")
        # Try to correct it
        if command_name in self.plugin_aliases:
            real_command = self.plugin_aliases[command_name]
            if real_command in self.known_plugins_set:
                suggestion = f"!{real_command}"
                if params_str:
                    suggestion += f" {params_str}"
                return f"Smart retry (alias): {suggestion}"
        fuzzy_aliases = get_close_matches(command_name, self.alias_keys + self.known_plugins, n=1, cutoff=0.6)
        if fuzzy_aliases:
            real_command = self.plugin_aliases.get(fuzzy_aliases[0], fuzzy_aliases[0])
            suggestion = f"!{real_command}"
            if params_str:
                suggestion += f" {params_str}"
            return f"Smart retry (fuzzy): {suggestion}"
        return f"Retry original: {self.last_unknown} (failures reset). Or {self._trigger_fallback(command_name, params_str)}"

    def self_correct(self, args: list) -> str:
        full_input = " ".join(args).strip().lower()
        if not full_input:
            return "Usage: !correct <suspected_command> [args]"
        command_name = self.get_command_key(full_input)
        params_str = full_input.split(maxsplit=1)[1] if " " in full_input else ""
        if command_name in self.plugin_aliases:
            real_command = self.plugin_aliases[command_name]
            if real_command in self.known_plugins_set:
                suggestion = f"!{real_command}"
                if params_str:
                    suggestion += f" {params_str}"
                return f"Corrected '{command_name}' -> {suggestion}"
        fuzzy_aliases = get_close_matches(command_name, self.alias_keys + self.known_plugins, n=1, cutoff=0.6)
        if fuzzy_aliases:
            matched = fuzzy_aliases[0]
            real_command = self.plugin_aliases.get(matched, matched)
            suggestion = f"!{real_command}"
            if params_str:
                suggestion += f" {params_str}"
            return f"Corrected '{command_name}' ~ '{matched}' -> {suggestion}"
        return f"No correction for '{command_name}'. Check !help."

    def reset_failures(self, args: list) -> str:
        before = len(self.failure_counts)
        self.failure_counts.clear()
        self.last_failure_time.clear()
        self.last_unknown = None
        print(f"[UnknownHandler] Reset failures (cleared {before} entries)")
        return f"Reset all failure counters and last_unknown."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "3.0.0",
    "description": "Improved unknown action/command handling with shortname/alias mappings, fuzzy matching, failure tracking, fallback logic, and retry/correct mechanisms.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})