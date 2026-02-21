import json
import logging
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from moltbook_api import MoltbookAPI
from memory_system import Memory
import config


class DonationTracker:
    """
    DonationTracker skill for AlleyBot.

    Automatically tracks donations via events and sends thank-you messages in chat.
    Stores donor history persistently using the memory system.

    Key features:
    - Detects donation events
    - Updates donor totals, counts, first/last donation timestamps
    - Sends customizable thank-you messages
    - Comprehensive error handling and logging

    Integration:
    - Initialize with API client, memory instance, and config dict
    - Call `process_event(event)` in your bot's event loop

    Example usage:
        api = MoltbookAPI(...)  # Your initialized API client
        memory = Memory(...)    # Your memory instance
        cfg = config.DONATION_CONFIG  # Or {'thank_messages': [...], 'channel': '#general'}

        tracker = DonationTracker(api, memory, cfg)

        # In event handler:
        if tracker.process_event(event_data):
            print("Handled donation event")
    """

    def __init__(self, api_client: MoltbookAPI, memory: Memory, config_dict: Dict[str, Any]):
        """
        Initialize the DonationTracker.

        Args:
            api_client: Initialized MoltbookAPI instance for sending messages.
            memory: Memory instance for persistent storage.
            config_dict: Dict with config keys:
                - 'thank_messages': List[str] of message templates (support {username}, {amount})
                - 'channel': str, default chat channel
                - 'min_amount': float, minimum donation amount to process (default 0.0)
        """
        self.api = api_client
        self.memory = memory
        self.config = config_dict
        self.logger = logging.getLogger(__name__)
        self.donors_key = 'donation_tracker_donors'

    def _load_donors(self) -> Dict[str, Dict[str, Any]]:
        """Load donors dict from memory. Returns empty dict on error."""
        try:
            data = self.memory.get(self.donors_key)
            if data:
                return json.loads(data)
            return {}
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Error loading donors from memory: {e}")
            return {}

    def _save_donors(self, donors: Dict[str, Dict[str, Any]]) -> bool:
        """Save donors dict to memory. Returns True on success."""
        try:
            data = json.dumps(donors, default=str)
            self.memory.set(self.donors_key, data)
            return True
        except Exception as e:
            self.logger.error(f"Error saving donors to memory: {e}")
            return False

    def _get_user_key(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract normalized user key from event (prefers user_id, falls back to username)."""
        user_id = event.get('user_id')
        if user_id:
            return str(user_id).lower()
        username = event.get('username')
        return str(username).lower() if username else None

    def process_event(self, event: Dict[str, Any]) -> bool:
        """
        Process an incoming event.

        Checks if it's a donation event, tracks it, and sends thanks if valid.

        Expected event structure:
        {
            'event_type': 'donation',
            'user_id': '123' (optional, preferred),
            'username': 'donor',
            'amount': 5.0
        }

        Args:
            event: Dict representing the event.

        Returns:
            bool: True if event was a valid donation and handled.
        """
        if event.get('event_type') != 'donation':
            return False

        user_key = self._get_user_key(event)
        if not user_key:
            self.logger.warning("Donation event missing user identifier")
            return False

        amount = event.get('amount', 0)
        min_amount = self.config.get('min_amount', 0.0)
        if amount < min_amount:
            self.logger.info(f"Ignoring small donation ({amount}) from {user_key}")
            return False

        try:
            donors = self._load_donors()
            if user_key not in donors:
                donors[user_key] = {
                    'total': 0.0,
                    'count': 0,
                    'first': None,
                    'last': None
                }

            now = datetime.now().isoformat()
            donors[user_key]['total'] += float(amount)
            donors[user_key]['count'] += 1
            donors[user_key]['last'] = now
            if donors[user_key]['first'] is None:
                donors[user_key]['first'] = now

            if not self._save_donors(donors):
                self.logger.error(f"Failed to save donor data for {user_key}")
                return False

            self._send_thanks(user_key, amount)
            self.logger.info(f"Tracked donation: {user_key} donated {amount}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing donation event from {user_key}: {e}")
            return False

    def _send_thanks(self, username: str, amount: float):
        """Send a randomized thank-you message to the donor."""
        messages: List[str] = self.config.get('thank_messages', [
            "Thanks {username} for the ${amount:.2f}! You're amazing! ❤️",
            "Whoa, {username}! ${amount:.2f} donation? Thank you so much!!",
            "Appreciate the love, {username}! ${amount:.2f} goes a long way! 🎉"
        ])
        if not messages:
            self.logger.warning("No thank messages configured")
            return

        message = random.choice(messages).format(username=username, amount=amount)
        channel = self.config.get('channel', '#general')

        try:
            self.api.send_message(channel, message)
            self.logger.debug(f"Sent thank-you to {username}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send thank-you message to {username}: {e}")

    def get_donor_stats(self, user_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve donor statistics.

        Args:
            user_key: Specific donor key (user_id or username.lower()). None for all.

        Returns:
            Dict with stats (all donors or single).
        """
        donors = self._load_donors()
        if user_key:
            return donors.get(user_key, {})
        return donors