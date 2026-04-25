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
        }
        self.failure_count = 0
        self.last_unknown = None
    
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
        self.failure_count += 1
        print(f"[UnknownHandler] Handling unknown action: '{self.last_unknown}'. Failure count: {self.failure_count}")
        
        if self.failure_count >= 3:
            return self._trigger_fallback()
        
        suggestions = self._generate_suggestions(self.last_unknown)
        return f"Sorry, '{self.last_unknown}' is unknown to me. {suggestions} Failure #{self.failure_count}/3 before fallback."
    
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
    
    def _trigger_fallback(self) -> str:
        print("[UnknownHandler] Repeated failures (max 3 attempts) detected. Triggering fallback and reset.")
        self.failure_count = 0
        self.last_unknown = None
        return "Too many unknown actions (max 3 retries exceeded). Resetting context. How can I assist you now? Try '!help'."
    
    def retry_last(self, args: list) -> str:
        if self.last_unknown:
            print(f"[UnknownHandler] Retry requested for: '{self.last_unknown}'. Current failures: {self.failure_count}")
            correction = self._attempt_correction(self.last_unknown)
            self.failure_count = max(0, self.failure_count - 1)
            if "Could not auto-correct" not in correction:
                return f"Retry with correction: {correction}"
            else:
                return f"Retry failed: still unknown. {correction} Failures now: {self.failure_count}/3"
        return "No previous unknown action to retry."
    
    def self_correct(self, args: list) -> str:
        print("[UnknownHandler] Self-correction mechanism activated.")
        if self.last_unknown:
            correction = self._attempt_correction(self.last_unknown)
            self.failure_count = max(0, self.failure_count - 1)
            return f"Self-correcting '{self.last_unknown}': {correction}"
        return "No recent error to correct. Use after an 'unknown' event."

    def _attempt_correction(self, unknown_input: str) -> str:
        # Check aliases first
        args = unknown_input.split()
        if args:
            command_name = args[0].strip().lower()
            if command_name in self.plugin_aliases:
                real = self.plugin_aliases[command_name]
                params = " ".join(args[1:])
                return f"Corrected to '{real}'{f' {params}' if params else ''} - use '!{real}'"
        
        # Simple spell check or intent guess
        corrections = {
            "helo": "hello - use 'chat hello'",
            "hi": "hello - use 'chat hi'",
            "bye": "goodbye - use 'chat bye'",
        }
        lower_input = unknown_input.lower().strip()
        for key, corr in corrections.items():
            if key in lower_input:
                return corr
        return "Could not auto-correct. Please rephrase your request."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "1.0.0",
    "description": "Handles unknown actions, plugin aliases, retry logic (max 3 attempts), fallback responses, logging for repeated failures, and self-correction mechanisms.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})