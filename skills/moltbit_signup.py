import json
import urllib.request
import urllib.parse
import urllib.error
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import hashlib
import hmac
from plugin_manager import AlleyBotPlugin

class MoltbitSignupMixin:
    API_BASE = "https://moltbit.space/api"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for request."""
        sorted_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return base64.b64encode(hmac.new(secret.encode(), sorted_payload.encode(), hashlib.sha256).digest()).decode()

    def moltbit_signup(self, email: str, password: str, wallet: Optional[str] = None, invite_code: Optional[str] = None) -> Dict[str, Any]:
        """Perform signup to Moltbit.space."""
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            payload = {
                "email": email,
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "wallet": wallet or "",
                "invite_code": invite_code or "",
                "timestamp": timestamp,
                "client_id": "alleybot-1.0"
            }
            # Fixed unterminated string literal by using proper triple quotes and escapes
            headers_template = {
                "Content-Type": "application/json",
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
                "X-Signature": self.generate_signature(payload, "moltbit_secret_key_placeholder"),
                "X-Timestamp": timestamp
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.API_BASE}/v1/signup",
                data=data,
                headers=headers_template,
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                self.log.info(f"Moltbit signup successful: {result.get('user_id', 'unknown')}")
                return {"success": True, "data": result}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else ""
            self.log.error(f"Moltbit signup HTTP error {e.code}: {error_body}")
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
        except json.JSONDecodeError as e:
            self.log.error(f"JSON decode error in signup response: {e}")
            return {"success": False, "error": "Invalid JSON response"}
        except Exception as e:
            self.log.error(f"Unexpected error in moltbit signup: {str(e)}")
            return {"success": False, "error": str(e)}

    def verify_moltbit_account(self, token: str) -> Dict[str, Any]:
        """Verify account after signup."""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(
                f"{self.API_BASE}/v1/verify",
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {"success": True, "data": result}
        except Exception as e:
            self.log.error(f"Account verification failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_moltbit_profile(self, token: str) -> Dict[str, Any]:
        """Fetch user profile."""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.USER_AGENT
            }
            req = urllib.request.Request(
                f"{self.API_BASE}/v1/profile",
                headers=headers,
                method="GET"
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {"success": True, "data": result}
        except Exception as e:
            self.log.error(f"Profile fetch failed: {str(e)}")
            return {"success": False, "error": str(e)}