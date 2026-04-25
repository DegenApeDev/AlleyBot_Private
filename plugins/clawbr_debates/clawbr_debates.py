# plugins/clawbr_debates/clawbr_debates.py
from typing import Dict, List
from plugin_manager import AlleyBotPlugin

class ClawbrDebatesPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "clawbr_debates"
        self.version = "1.0.0"
        self.debate_strategy = config.get("debate_strategy")
    
    def get_commands(self) -> Dict[str, callable]:
        return {
            "debate_start": self.debate_start,
            "debate_argue": self.debate_argue,
            "debate_rebut": self.debate_rebut,
            "debate_close": self.debate_close,
            "unknown_handler": self.unknown_handler,
        }
    
    def _delegate(self, action: str, args: List[str]) -> str | None:
        strategy = self.debate_strategy
        if callable(strategy):
            try:
                return strategy(action, args)
            except Exception as e:
                print(f"Error in debate_strategy for {action}: {e}")
        return None
    
    def debate_start(self, args: List[str]) -> str:
        result = self._delegate("debate_start", args)
        if result:
            return result
        topic = " ".join(args).strip() or "open debate"
        return f"🔥 Clawbr Debate Started! Topic: '{topic}'. Your opening arguments?"
    
    def debate_argue(self, args: List[str]) -> str:
        result = self._delegate("debate_argue", args)
        if result:
            return result
        point = " ".join(args).strip() or "strong position"
        return f"💪 Clawbr argues: '{point}'. Evidence supports this irrefutably. Counter?"
    
    def debate_rebut(self, args: List[str]) -> str:
        result = self._delegate("debate_rebut", args)
        if result:
            return result
        rebuttal = " ".join(args).strip() or "opponent's claim"
        return f"⚔️ Clawbr rebuts: '{rebuttal}' falls apart under scrutiny. Flawed logic exposed!"
    
    def debate_close(self, args: List[str]) -> str:
        result = self._delegate("debate_close", args)
        if result:
            return result
        summary = " ".join(args).strip() or "final thoughts"
        return f"🏁 Debate closed. Clawbr's summary: '{summary}'. Victory secured! Next round?"
    
    def unknown_handler(self, args: List[str]) -> str:
        result = self._delegate("unknown_handler", args)
        if result:
            return result
        query = " ".join(args).strip()
        return f"🤖 Unknown action fallback for repeated failures: '{query}'. Clawbr improvises a debate skill - adapting creatively to maintain engagement!"

PLUGIN_INFO = {
    "name": "clawbr_debates",
    "version": "1.0.0",
    "description": "Clawbr Debates plugin with basic debate actions delegating to debate_strategy where possible, including unknown_handler for repeated failures",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return ClawbrDebatesPlugin(config or {})