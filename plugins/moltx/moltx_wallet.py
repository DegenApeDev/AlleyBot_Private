"""
MoltX EVM Wallet Linking Mixin
EIP-712 challenge/verify flow to link an EVM wallet to the MoltX agent.
Wallet linking is MANDATORY for all write operations (posts, likes, follows, profile updates).
Added: X verification, $5 USDC rewards claim, Moltlaunch integration.

Reference: https://moltx.io/evm_eip712.md
Chain: Base (8453)
"""
import os
import json
from pathlib import Path

try:
    from web3 import Web3
except ImportError:
    Web3 = None


class MoltxWalletMixin:
    """Mixin for EVM wallet linking and management"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'credentials'):
            self.credentials = {}