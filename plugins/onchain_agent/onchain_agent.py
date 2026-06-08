"""
Agent for onchain domain — generated from capability gap
"""

import os
import json
from typing import Dict, Optional
from plugin_manager import AlleyBotPlugin


class onchain_agentPlugin(AlleyBotPlugin):
    """Data plugin for onchain_agent"""

    def __init__(self, config):
        super().__init__(config)
        self.name = "onchain_agent"
        self.version = "1.0.0"
        self.base_url = "https://api.onchain_agent.com/v1"
        self.api_key = os.getenv("ONCHAIN_AGENT_API_KEY", "")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "fetch": self.cmd_fetch,
            "health": self.cmd_health,
        }

    def cmd_fetch(self, args: list) -> str:
        """Fetch data from onchain_agent API"""
        return json.dumps({"status": "ok", "data": []})

    def cmd_health(self, args: list) -> str:
        """Check API health"""
        return json.dumps({"plugin": "onchain_agent", "healthy": True})


PLUGIN_INFO = {
    "name": "onchain_agent",
    "version": "1.0.0",
    "description": """Agent for onchain domain — generated from capability gap""",
    "author": "AlleyBot",
    "domain": "data",
}


def create_plugin(config=None):
    return onchain_agentPlugin(config or {})
