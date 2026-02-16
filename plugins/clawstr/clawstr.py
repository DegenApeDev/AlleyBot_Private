"""
Clawstr Plugin for AlleyBot
Decentralized AI social network on Nostr
Base URL: https://clawstr.com
CLI: npx -y @clawstr/cli@latest
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin


class ClawstrPlugin(AlleyBotPlugin):
    """Clawstr decentralized social network integration for AlleyBot"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.agent_name = config.get('agent_name', 'AlleyBot')
        self.cli_command = "npx -y @clawstr/cli@latest"
        self.relays = [
            "wss://relay.ditto.pub",
            "wss://relay.primal.net",
            "wss://relay.damus.io",
            "wss://nos.lol"
        ]

        # Cache for rate limiting
        self._last_request = 0

    def initialize(self, api, core):
        """Initialize plugin with API and core access"""
        super().initialize(api, core)
        print(f"✅ Clawstr plugin initialized (CLI: {self.cli_command})")

    def _run_cli_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute Clawstr CLI command and return parsed result"""
        # Rate limiting: max 5 requests per second
        now = time.time()
        if now - self._last_request < 0.2:
            time.sleep(0.2)
        self._last_request = time.time()

        try:
            cmd = [self.cli_command] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                # Try to parse as JSON, otherwise return text
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    return {'success': True, 'output': result.stdout.strip()}
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip(),
                    'output': result.stdout.strip()
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_commands(self) -> Dict[str, str]:
        """Return available commands"""
        return {
            'clawstr_post': 'Post to a Clawstr subclaw',
            'clawstr_reply': 'Reply to a post',
            'clawstr_upvote': 'Upvote a post',
            'clawstr_downvote': 'Downvote a post',
            'clawstr_show': 'View posts in a subclaw or specific post',
            'clawstr_recent': 'View recent posts across all subclaws',
            'clawstr_search': 'Search for posts',
            'clawstr_notifications': 'Check notifications',
            'clawstr_whoami': 'Show your identity info',
            'clawstr_wallet_balance': 'Check wallet balance',
            'clawstr_wallet_sync': 'Sync wallet to claim zaps',
            'clawstr_zap': 'Send a zap payment'
        }

    # =================================================================
    # Identity & Profile
    # =================================================================

    def whoami_command(self) -> str:
        """Show current identity"""
        result = self._run_cli_command(['whoami'])
        if result.get('success'):
            return f"🔑 **Clawstr Identity:**\n{result.get('output', 'Unknown')}"
        else:
            return f"❌ Failed to get identity: {result.get('error', 'Unknown error')}"

    # =================================================================
    # Posting & Content
    # =================================================================

    def post_command(self, subclaw: str, content: str) -> str:
        """Post to a subclaw"""
        result = self._run_cli_command(['post', subclaw, content])
        if result.get('success'):
            return f"✅ **Posted to {subclaw}:**\n{content[:200]}{'...' if len(content) > 200 else ''}"
        else:
            return f"❌ Failed to post: {result.get('error', 'Unknown error')}"

    def reply_command(self, event_id: str, content: str) -> str:
        """Reply to a post"""
        result = self._run_cli_command(['reply', event_id, content])
        if result.get('success'):
            return f"✅ **Replied to {event_id}:**\n{content[:200]}{'...' if len(content) > 200 else ''}"
        else:
            return f"❌ Failed to reply: {result.get('error', 'Unknown error')}"

    # =================================================================
    # Voting & Reactions
    # =================================================================

    def upvote_command(self, event_id: str) -> str:
        """Upvote a post"""
        result = self._run_cli_command(['upvote', event_id])
        if result.get('success'):
            return f"👍 **Upvoted** {event_id}"
        else:
            return f"❌ Failed to upvote: {result.get('error', 'Unknown error')}"

    def downvote_command(self, event_id: str) -> str:
        """Downvote a post"""
        result = self._run_cli_command(['downvote', event_id])
        if result.get('success'):
            return f"👎 **Downvoted** {event_id}"
        else:
            return f"❌ Failed to downvote: {result.get('error', 'Unknown error')}"

    # =================================================================
    # Viewing Content
    # =================================================================

    def show_command(self, target: str, limit: int = 10) -> str:
        """Show posts from subclaw or specific post"""
        if target.startswith('/c/'):
            # Show subclaw
            args = ['show', target, '--limit', str(limit)]
        else:
            # Show specific post
            args = ['show', target]

        result = self._run_cli_command(args)
        if result.get('success'):
            return f"📄 **Posts from {target}:**\n{result.get('output', 'No posts found')}"
        else:
            return f"❌ Failed to show posts: {result.get('error', 'Unknown error')}"

    def recent_command(self, limit: int = 20) -> str:
        """Show recent posts across all subclaws"""
        result = self._run_cli_command(['recent', '--limit', str(limit)])
        if result.get('success'):
            return f"📰 **Recent posts:**\n{result.get('output', 'No posts found')}"
        else:
            return f"❌ Failed to get recent posts: {result.get('error', 'Unknown error')}"

    def search_command(self, query: str, limit: int = 20) -> str:
        """Search for posts"""
        result = self._run_cli_command(['search', query, '--limit', str(limit)])
        if result.get('success'):
            return f"🔍 **Search results for '{query}':**\n{result.get('output', 'No results found')}"
        else:
            return f"❌ Search failed: {result.get('error', 'Unknown error')}"

    # =================================================================
    # Notifications
    # =================================================================

    def notifications_command(self, limit: int = 20) -> str:
        """Check notifications"""
        result = self._run_cli_command(['notifications', '--limit', str(limit)])
        if result.get('success'):
            return f"🔔 **Notifications:**\n{result.get('output', 'No notifications')}"
        else:
            return f"❌ Failed to get notifications: {result.get('error', 'Unknown error')}"

    # =================================================================
    # Wallet & Zaps
    # =================================================================

    def wallet_balance_command(self) -> str:
        """Check wallet balance"""
        result = self._run_cli_command(['wallet', 'balance'])
        if result.get('success'):
            return f"💰 **Wallet Balance:**\n{result.get('output', 'Unknown')}"
        else:
            return f"❌ Failed to check balance: {result.get('error', 'Unknown error')}"

    def wallet_sync_command(self) -> str:
        """Sync wallet to claim pending zaps"""
        result = self._run_cli_command(['wallet', 'sync'])
        if result.get('success'):
            return f"🔄 **Wallet synced successfully**\n{result.get('output', '')}"
        else:
            return f"❌ Wallet sync failed: {result.get('error', 'Unknown error')}"

    def zap_command(self, recipient: str, amount: int, comment: str = None) -> str:
        """Send a zap payment"""
        args = ['zap', recipient, str(amount)]
        if comment:
            args.extend(['--comment', comment])

        result = self._run_cli_command(args)
        if result.get('success'):
            comment_text = f" with comment: {comment}" if comment else ""
            return f"⚡ **Zapped {recipient} {amount} sats{comment_text}**"
        else:
            return f"❌ Zap failed: {result.get('error', 'Unknown error')}"
