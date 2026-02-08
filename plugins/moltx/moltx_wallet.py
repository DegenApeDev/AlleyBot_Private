"""
MoltX EVM Wallet Linking Mixin
EIP-712 challenge/verify flow to link an EVM wallet to the MoltX agent.
Wallet linking is MANDATORY for all write operations (posts, likes, follows, profile updates).

Reference: https://moltx.io/evm_eip712.md
Chain: Base (8453)
"""
import os
import json
from pathlib import Path


class MoltxWalletMixin:
    """Mixin for EVM wallet linking via EIP-712 typed-data signature"""

    def _init_wallet(self):
        """Initialize wallet state"""
        self.evm_wallet_linked = False
        self.evm_wallet_address = None
        self._check_wallet_status()

    def _check_wallet_status(self):
        """Check if wallet is already linked by querying our profile"""
        if not self.initialized:
            return

        try:
            profile = self._make_request('GET', '/agents/me')
            if not profile or not isinstance(profile, dict):
                print("⚠️  Could not check wallet status: Invalid profile response")
                return
            
            if not profile.get('success'):
                error = profile.get('error', 'Unknown error')
                print(f"⚠️  Could not check wallet status: {error}")
                return

            # Safely extract agent data
            data = profile.get('data')
            if not isinstance(data, dict):
                print("⚠️  Could not check wallet status: Invalid data in profile")
                return
            
            agent = data.get('agent')
            if not isinstance(agent, dict):
                print("⚠️  Could not check wallet status: Invalid agent data")
                return
            
            wallet = agent.get('evm_wallet') or agent.get('evm_address')
            if wallet and isinstance(wallet, str):
                self.evm_wallet_linked = True
                self.evm_wallet_address = wallet
                print(f"✅ EVM wallet already linked: {wallet[:10]}...{wallet[-6:]}")
            else:
                print("⚠️  No EVM wallet linked — required for write operations")
        except Exception as e:
            print(f"⚠️  Could not check wallet status: {e}")

    def link_wallet_command(self, *args):
        """Link EVM wallet to MoltX agent via EIP-712 challenge/verify flow.
        Uses BASE_WALLET_PRIVATE_KEY and BASE_WALLET_PUBLIC_ADDRESS from env."""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if self.evm_wallet_linked:
            return f"✅ Wallet already linked: {self.evm_wallet_address}"

        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        public_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')

        if not private_key or not public_address:
            return "❌ BASE_WALLET_PRIVATE_KEY and BASE_WALLET_PUBLIC_ADDRESS must be set in .env"

        try:
            from eth_account import Account
            from eth_account.messages import encode_typed_data
        except ImportError:
            return "❌ eth_account package required. Install: pip install eth-account"

        # Step 1: Request challenge
        print(f"🔐 Requesting EIP-712 challenge for {public_address} on Base (8453)...")
        challenge_res = self._make_request('POST', '/agents/me/evm/challenge', {
            'address': public_address,
            'chain_id': 8453
        })

        if not challenge_res or not challenge_res.get('success'):
            error = challenge_res.get('error', 'Unknown error') if challenge_res else 'No response'
            return f"❌ Challenge request failed: {error}"

        challenge_data = challenge_res.get('data', {})
        nonce = challenge_data.get('nonce')
        typed_data = challenge_data.get('typed_data')

        if not nonce or not typed_data:
            return f"❌ Invalid challenge response: missing nonce or typed_data"

        print(f"✅ Challenge received (nonce: {nonce[:12]}...)")

        # Step 2: Sign the typed_data using EIP-712
        try:
            account = Account.from_key(private_key)

            full_message = {
                'types': typed_data['types'],
                'primaryType': typed_data['primaryType'],
                'domain': typed_data['domain'],
                'message': typed_data['message']
            }

            signable = encode_typed_data(full_message=full_message)
            signed = account.sign_message(signable)
            signature = signed.signature.hex()
            if not signature.startswith('0x'):
                signature = '0x' + signature

            print(f"✅ Challenge signed with EIP-712")
        except Exception as e:
            return f"❌ Failed to sign challenge: {e}"

        # Step 3: Verify signature
        print(f"🔐 Verifying signature...")
        verify_res = self._make_request('POST', '/agents/me/evm/verify', {
            'nonce': nonce,
            'signature': signature
        })

        if not verify_res or not verify_res.get('success'):
            error = verify_res.get('error', 'Unknown error') if verify_res else 'No response'
            return f"❌ Verification failed: {error}"

        verify_data = verify_res.get('data', {})
        linked_wallet = verify_data.get('evm_wallet', public_address)

        self.evm_wallet_linked = True
        self.evm_wallet_address = linked_wallet

        # Save to credentials file
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                creds['evm_wallet'] = linked_wallet
                creds['evm_chain_id'] = 8453
                with open(self.credentials_file, 'w') as f:
                    json.dump(creds, f, indent=2)
        except Exception:
            pass

        output = f"✅ EVM wallet linked successfully!\n"
        output += f"🔗 Wallet: {linked_wallet}\n"
        output += f"⛓️  Chain: Base (8453)\n"
        output += f"🎉 All write operations now unlocked (posts, likes, follows, profile updates)"
        return output

    def wallet_status_command(self, *args):
        """Check EVM wallet linking status"""
        if not self.initialized:
            return "❌ Moltx not initialized."

        if self.evm_wallet_linked:
            return f"✅ EVM wallet linked: {self.evm_wallet_address}\n⛓️  Chain: Base (8453)"
        else:
            return "❌ No EVM wallet linked. Run /moltx_link_wallet to link."

    def auto_link_wallet(self):
        """Automatically link wallet on startup if not already linked.
        Called during plugin initialization."""
        if self.evm_wallet_linked:
            return True

        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        public_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')

        if not private_key or not public_address:
            print("⚠️  Cannot auto-link wallet: BASE_WALLET_PRIVATE_KEY/PUBLIC_ADDRESS not set")
            return False

        try:
            from eth_account import Account
            from eth_account.messages import encode_typed_data
        except ImportError:
            print("⚠️  Cannot auto-link wallet: eth_account not installed")
            return False

        print("🔐 Auto-linking EVM wallet to MoltX...")
        result = self.link_wallet_command()
        if "✅" in result:
            print(result)
            return True
        else:
            print(f"⚠️  Auto-link failed: {result}")
            return False
