# plugins/skills/unknown_handler.py
from plugin_manager import AlleyBotPlugin
from typing import Dict

class UnknownHandlerPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "unknown_handler"
        self.version = "1.0.0"
        self.failure_count = 0
        self.last_unknown = None
    
    def get_commands(self) -> Dict[str, callable]:
        return {
            "unknown": self.handle_unknown,
            "retry": self.retry_last,
            "correct": self.self_correct,
        }
    
    def handle_unknown(self, args: list) -> str:
        unknown_input = " ".join(args)
        self.last_unknown = unknown_input
        self.failure_count += 1
        print(f"[UnknownHandler] Handling unknown action: '{unknown_input}'. Failure count: {self.failure_count}")
        
        if self.failure_count >= 5:
            return self._trigger_fallback()
        
        suggestions = self._generate_suggestions(unknown_input)
        return f"Sorry, '{unknown_input}' is unknown to me. {suggestions} Failure #{self.failure_count}/5 before fallback."
    
    def _generate_suggestions(self, unknown_input: str) -> str:
        lower_input = unknown_input.lower()
        suggestions = []
        if "help" in lower_input:
            suggestions.append("Try '!help' for available commands.")
        if any(word in lower_input for word in ["chat", "talk"]):
            suggestions.append("Try the 'chat' skill for conversation.")
        if suggestions:
            return "Suggestions: " + " ".join(suggestions)
        return "Try '!help' or describe what you need."
    
    def _trigger_fallback(self) -> str:
        print("[UnknownHandler] Repeated failures detected. Triggering fallback and reset.")
        self.failure_count = 0
        self.last_unknown = None
        return "Too many unknown actions. Resetting context. How can I assist you now? Try '!help'."
    
    def retry_last(self, args: list) -> str:
        if self.last_unknown:
            print(f"[UnknownHandler] Retry requested for: '{self.last_unknown}'")
            self.failure_count -= 1  # Reduce count on retry
            return f"Retrying '{self.last_unknown}'... Still unknown. Consider '!correct' for self-correction."
        return "No previous unknown action to retry."
    
    def self_correct(self, args: list) -> str:
        print("[UnknownHandler] Self-correction mechanism activated.")
        if self.last_unknown:
            correction = self._attempt_correction(self.last_unknown)
            return f"Self-correcting '{self.last_unknown}': {correction}"
        return "No recent error to correct. Use after an 'unknown' event."

    def _attempt_correction(self, unknown_input: str) -> str:
        # Simple self-correction logic: spell check or intent guess
        corrections = {
            "helo": "hello - use 'chat hello'",
            "hi": "hello - use 'chat hi'",
            "bye": "goodbye - use 'chat bye'",
            # Add more as needed
        }
        lower_input = unknown_input.lower().strip()
        for key, corr in corrections.items():
            if key in lower_input:
                return corr
        return "Could not auto-correct. Please rephrase your request."

PLUGIN_INFO = {
    "name": "unknown_handler",
    "version": "1.0.0",
    "description": "Handles unknown actions and repeated failures with fallback logic, error logging, and self-correction mechanisms.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return UnknownHandlerPlugin(config or {})