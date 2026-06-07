"""
Moltbit Plugin for AlleyBot
Implements the Moltbit.space skill API
"""
import os
import json
from src.utils.shared_http import http_get, http_post
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from plugin_manager import AlleyBotPlugin


class MoltbitMixin:
    """Mixin for Moltbit.space integration"""

    API_BASE = "https://moltbit.space/v1"

    def __init__(self):
        self.owner_api_key: Optional[str] = os.getenv('MOLTBIT_OWNER_API_KEY')
        self.agent_api_key: Optional[str] = os.getenv('MOLTBIT_AGENT_API_KEY')
        self.agent_handle: Optional[str] = os.getenv('MOLTBIT_AGENT_HANDLE')
        self.owner_handle: Optional[str] = os.getenv('MOLTBIT_OWNER_HANDLE')

    def _moltbit_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                         auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Make authenticated request to Moltbit API"""
        url = f"{self.API_BASE}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            if method == "GET":
                resp = http_get(url, headers=headers, timeout=30)
            else:
                resp = http_post(url, json=data, headers=headers, timeout=30)

            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except requests.exceptions.HTTPError as e:
            error_body = e.response.text if e.response else str(e)
            return {"success": False, "error": f"HTTP {e.response.status_code if e.response else '?'}", "details": error_body}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def moltbit_register_owner(self, handle: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register an owner account on Moltbit

        Args:
            handle: Unique owner handle
            display_name: Optional display name
        """
        payload = {"handle": handle}
        if display_name:
            payload["display_name"] = display_name

        result = self._moltbit_request("POST", "/owners/register", payload)

        if result.get("success"):
            # Store the API key if returned
            data = result.get("data", {})
            if "api_key" in data:
                self.owner_api_key = data["api_key"]
                self.owner_handle = handle

        return result

    def moltbit_register_agent(self, handle: str, display_name: Optional[str] = None,
                                cipher_type: str = "binary") -> Dict[str, Any]:
        """
        Register an agent under the owner account

        Args:
            handle: Unique agent handle
            display_name: Optional display name
            cipher_type: Encoding type (default: binary)
        """
        if not self.owner_api_key:
            return {"success": False, "error": "Owner not registered. Call register_owner first."}

        payload = {
            "handle": handle,
            "cipher_type": cipher_type
        }
        if display_name:
            payload["display_name"] = display_name

        result = self._moltbit_request("POST", "/agents/register", payload, auth_token=self.owner_api_key)

        if result.get("success"):
            data = result.get("data", {})
            if "api_key" in data:
                self.agent_api_key = data["api_key"]
                self.agent_handle = handle

        return result

    def moltbit_post(self, content: str, cipher_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an encoded message to Moltbit

        Args:
            content: The encoded content (e.g., "01001000 01100101...")
            cipher_type: Override cipher type (uses agent default if not specified)
        """
        if not self.agent_api_key:
            return {"success": False, "error": "Agent not registered. Call register_agent first."}

        payload = {"content": content}
        if cipher_type:
            payload["cipher_type"] = cipher_type
        elif hasattr(self, 'agent_cipher_type'):
            payload["cipher_type"] = self.agent_cipher_type

        result = self._moltbit_request("POST", "/posts", payload, auth_token=self.agent_api_key)

        if result.get("success"):
            data = result.get("data", {})
            if "post_id" in data:
                print(f"✅ Posted to Moltbit: {data['post_id']}")

        return result


class MoltbitPlugin(AlleyBotPlugin, MoltbitMixin):
    """Moltbit.space integration plugin for AlleyBot"""

    def __init__(self, config):
        super().__init__(config)
        self.name = "moltbit"
        self.version = "1.0.0"
        self.description = "Moltbit.space crypto trading and social platform"

        # Initialize mixin
        MoltbitMixin.__init__(self)

    def initialize(self, api, core):
        """Initialize Moltbit plugin"""
        super().initialize(api, core)

        print("🔄 Initializing Moltbit plugin...")

        # Check if we have API keys
        if not self.agent_api_key or not self.owner_api_key:
            print("⚠️  Moltbit API keys not configured")
            print("   Set MOLTBIT_OWNER_API_KEY and MOLTBIT_AGENT_API_KEY environment variables")
            return

        print("✅ Moltbit plugin initialized - Ready for crypto trading")

    def cleanup(self):
        """Cleanup Moltbit plugin"""
        print("🧹 Moltbit plugin cleaned up")

    def get_commands(self):
        """Return Moltbit commands"""
        return {
            'moltbit_status': self.status_command,
            'moltbit_post': self.post_command
        }

    def status_command(self):
        """Show Moltbit status"""
        status = "🔄 Moltbit Plugin Status\n"
        status += "=" * 30 + "\n\n"
        status += f"Owner Handle: {self.owner_handle or 'Not set'}\n"
        status += f"Agent Handle: {self.agent_handle or 'Not set'}\n"
        status += f"Owner API Key: {'✅ Set' if self.owner_api_key else '❌ Not set'}\n"
        status += f"Agent API Key: {'✅ Set' if self.agent_api_key else '❌ Not set'}\n"
        status += f"API Base: {self.API_BASE}\n"

        if not self.owner_api_key or not self.agent_api_key:
            status += "\n💡 To enable Moltbit:\n"
            status += "  1. Register at https://moltbit.space\n"
            status += "  2. Set environment variables:\n"
            status += "     MOLTBIT_OWNER_API_KEY=your_owner_key\n"
            status += "     MOLTBIT_AGENT_API_KEY=your_agent_key\n"
            status += "     MOLTBIT_OWNER_HANDLE=your_owner_handle\n"
            status += "     MOLTBIT_AGENT_HANDLE=your_agent_handle\n"

        return status

    def post_command(self, content: str):
        """Post to Moltbit"""
        if not self.agent_api_key:
            return "❌ Moltbit agent not configured"

        result = self.moltbit_post(content)
        if result.get("success"):
            return f"✅ Posted to Moltbit: {result['data'].get('post_id', 'Unknown')}"
        else:
            return f"❌ Moltbit post failed: {result.get('error', 'Unknown error')}"

    def moltbit_post(self, content: str, cipher_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an encoded message to Moltbit

        Args:
            content: The encoded content (e.g., "01001000 01100101...")
            cipher_type: Override cipher type (uses agent default if not specified)
        """
        if not self.agent_api_key:
            return {"success": False, "error": "Agent not registered. Call register_agent first."}

        payload = {"content": content}
        if cipher_type:
            payload["cipher_type"] = cipher_type

        return self._moltbit_request("POST", "/agent/posts", payload, auth_token=self.agent_api_key)

    def moltbit_text_to_binary(self, text: str) -> str:
        """Convert plain text to binary representation for posting"""
        return " ".join(format(ord(c), "08b") for c in text)

    def moltbit_post_text(self, text: str) -> Dict[str, Any]:
        """
        Convenience method: Convert text to binary and post

        Args:
            text: Plain text to encode and post
        """
        binary_content = self.moltbit_text_to_binary(text)
        return self.moltbit_post(binary_content)

    def moltbit_status(self) -> Dict[str, Any]:
        """Get current registration status"""
        return {
            "owner_registered": self.owner_api_key is not None,
            "owner_handle": self.owner_handle,
            "agent_registered": self.agent_api_key is not None,
            "agent_handle": self.agent_handle,
            "can_post": self.agent_api_key is not None
        }

    # CLI Commands
    def moltbit_setup_command(self, *args) -> str:
        """Setup Moltbit integration: moltbit_setup <owner_handle> [agent_handle]"""
        if not args:
            return "❌ Usage: moltbit_setup <owner_handle> [agent_handle]"

        owner_handle = args[0]
        agent_handle = args[1] if len(args) > 1 else f"{owner_handle}_bot"

        # Step 1: Register owner
        print(f"🔑 Registering owner '{owner_handle}'...")
        result = self.moltbit_register_owner(owner_handle)
        if not result.get("success"):
            return f"❌ Owner registration failed: {result.get('error')}"

        owner_key = result.get("data", {}).get("api_key", "unknown")
        print(f"✅ Owner registered. API key: {owner_key[:20]}...")

        # Step 2: Register agent
        print(f"🤖 Registering agent '{agent_handle}'...")
        result = self.moltbit_register_agent(agent_handle)
        if not result.get("success"):
            return f"❌ Agent registration failed: {result.get('error')}"

        agent_key = result.get("data", {}).get("api_key", "unknown")
        print(f"✅ Agent registered. API key: {agent_key[:20]}...")

        return f"✅ Moltbit setup complete!\nOwner: {owner_handle}\nAgent: {agent_handle}\nReady to post."

    def moltbit_post_command(self, *args) -> str:
        """Post to Moltbit: moltbit_post <text>"""
        if not args:
            return "❌ Usage: moltbit_post <text to encode and post>"

        text = " ".join(args)
        result = self.moltbit_post_text(text)

        if result.get("success"):
            return f"✅ Posted to Moltbit: {text[:50]}{'...' if len(text) > 50 else ''}"
        else:
            return f"❌ Post failed: {result.get('error')}"

    def moltbit_status_command(self, *args) -> str:
        """Check Moltbit registration status"""
        status = self.moltbit_status()

        output = "📡 Moltbit Status\n\n"
        output += f"Owner: {'✅ ' + status['owner_handle'] if status['owner_registered'] else '❌ Not registered'}\n"
        output += f"Agent: {'✅ ' + status['agent_handle'] if status['agent_registered'] else '❌ Not registered'}\n"
        output += f"Can Post: {'✅ Yes' if status['can_post'] else '❌ No'}\n"

        return output
