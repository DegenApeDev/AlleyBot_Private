"""
Transaction Registry - Track known-safe transaction hashes
Allows security filter to distinguish between tx hashes (public) and private keys (secret)
"""
import threading
from typing import Set, Optional

class TxRegistry:
    """Registry of transaction hashes that AlleyBot has sent (safe to display)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one global registry"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._known_txs: Set[str] = set()
        self._lock = threading.Lock()
    
    def register(self, tx_hash: str) -> None:
        """Register a transaction hash as known/safe"""
        if not tx_hash:
            return
        # Normalize: lowercase, strip 0x prefix for consistency
        normalized = tx_hash.lower().strip()
        if normalized.startswith('0x'):
            normalized = normalized[2:]
        
        with self._lock:
            self._known_txs.add(normalized)
            # Keep only last 1000 txs to prevent memory bloat
            if len(self._known_txs) > 1000:
                # Remove oldest (arbitrary since set is unordered, but that's fine)
                self._known_txs.pop()
    
    def is_known(self, tx_hash: str) -> bool:
        """Check if a transaction hash is in our known-safe registry"""
        if not tx_hash:
            return False
        # Normalize
        normalized = tx_hash.lower().strip()
        if normalized.startswith('0x'):
            normalized = normalized[2:]
        
        with self._lock:
            return normalized in self._known_txs
    
    def get_known_count(self) -> int:
        """Get number of known transactions"""
        with self._lock:
            return len(self._known_txs)
    
    def clear(self) -> None:
        """Clear registry (useful for testing)"""
        with self._lock:
            self._known_txs.clear()

# Global instance
tx_registry = TxRegistry()

# Convenience functions
def register_tx(tx_hash: str) -> None:
    """Register a transaction as known-safe"""
    tx_registry.register(tx_hash)

def is_known_tx(tx_hash: str) -> bool:
    """Check if transaction is known-safe"""
    return tx_registry.is_known(tx_hash)
