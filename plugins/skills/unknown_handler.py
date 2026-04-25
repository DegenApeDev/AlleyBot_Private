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
        self.known_plugins_set = set(self.known_plugins)
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
                    if real_command in self.known_plugins_set:
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

            # Exact alias resolution
            if command_name in self.plugin_aliases:
                real_command = self.plugin_aliases[command_name]
                if real_command not in self.known_plugins_set:
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
                if real_command in self.known_plugins_set:
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
        if suggs:
            return f"Suggestions: {', '.join(set(suggs[:5]))}. "
        return "No suggestions. "

    def _trigger_fallback(self, command_name: str, params_str: str) -> str:
        fallback = f"!core {command_name}"
        if params_str:
            fallback += f" {params_str}"
        print(f"[UnknownHandler] Fallback triggered for '{command_name}': {fallback}")
        # Reset count after fallback
        self.failure_counts.pop(command_name, None)
        self.last_failure_time.pop(command_name, None)
        return f"After 5 failures of '{command_name}', fallback: {fallback} or !chat {command_name} {params_str} or !help."

    def retry_last(self, args: list) -> str:
        if not self.last_unknown:
            return "No previous unknown command to retry. Use !unknown <cmd> first."
        print(f"[UnknownHandler] Retrying last unknown: {self.last_unknown}")
        return f"Last unknown: {self.last_unknown}\nPaste/try it, !correct <fix>, or !core {self.last_unknown}."

    def self_correct(self, args: list) -> str:
        if not args:
            return "Usage: !correct <correct_command> [args] - overrides last unknown."
        correction = " ".join(args)
        self.last_unknown = correction
        print(f"[UnknownHandler] Self-corrected to: {correction}")
        cmd_key = self.get_command_key(correction)
        parts = correction.split(maxsplit=1)
        params = parts[1] if len(parts) > 1 else ""
        if cmd_key in self.plugin_aliases:
            real = self.plugin_aliases[cmd_key]
            return f"Corrected '{cmd_key}' to '{real}'. Try: !{real} {params}."
        fuzzy_a = get_close_matches(cmd_key, self.alias_keys, n=1, cutoff=0.6)
        if fuzzy_a:
            alias = fuzzy_a[0]
            real = self.plugin_aliases[alias]
            return f"Corrected '{cmd_key}' ~ '{alias}' -> '{real}'. Try: !{real} {params}."
        fuzzy_k = get_close_matches(cmd_key, self.known_plugins, n=1, cutoff=0.6)
        if fuzzy_k:
            real = fuzzy_k[0]
            return f"Corrected '{cmd_key}' ~ '{real}'. Try: !{real} {params}."
        return f"Set last to '{correction}', but unknown. Suggestions: {self._generate_suggestions(correction)}!help."

    def reset_failures(self, args: list) -> str:
        cleared = len(self.failure_counts)
        self.failure_counts.clear()
        self.last_failure_time.clear()
        self.last_unknown = None
        print(f"[UnknownHandler] Reset {cleared} failure counters.")
        return f"Reset {cleared} failure trackers and cleared last unknown."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "2.0.0",
    "description": "Handles unknown commands with robust aliases, fuzzy matching, repeated failure tracking, fallbacks, retry/correct/reset.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})