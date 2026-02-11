"""
Secret Manager for AlleyBot
High-level abstraction for secret operations with automatic rotation and audit logging.
"""
import os
import time
import hashlib
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

from src.security.vault_client import vault_client, VaultClient


class SecretType(Enum):
    """Types of secrets with different rotation policies"""
    API_KEY = "api_key"           # Rotate every 90 days
    ACCESS_TOKEN = "access_token"  # Rotate every 30 days
    PRIVATE_KEY = "private_key"    # Rotate every 180 days
    PASSWORD = "password"          # Rotate every 90 days
    ENCRYPTION_KEY = "encryption_key"  # Rotate every 365 days
    WEBHOOK_SECRET = "webhook_secret"  # Rotate every 180 days


@dataclass
class AuditLogEntry:
    """Audit log entry for secret access"""
    timestamp: str
    action: str  # 'get', 'set', 'delete', 'rotate'
    key: str
    source: str  # Plugin name or 'manual'
    success: bool
    details: Optional[str] = None


class SecretManager:
    """
    High-level secret manager providing:
    - Unified interface for all secret operations
    - Automatic rotation scheduling
    - Audit logging
    - Fallback to environment variables during migration
    """
    
    # Rotation intervals in days by secret type
    ROTATION_INTERVALS = {
        SecretType.API_KEY: 90,
        SecretType.ACCESS_TOKEN: 30,
        SecretType.PRIVATE_KEY: 180,
        SecretType.PASSWORD: 90,
        SecretType.ENCRYPTION_KEY: 365,
        SecretType.WEBHOOK_SECRET: 180,
    }
    
    def __init__(self, vault: Optional[VaultClient] = None):
        self.vault = vault or vault_client
        self._audit_log: List[AuditLogEntry] = []
        self._rotation_callbacks: Dict[str, Callable[[], str]] = {}
        self._fallback_to_env = True  # Allow fallback to os.getenv during migration
        self._last_rotation_check: Optional[datetime] = None
        
    def initialize(self, vault_url: Optional[str] = None, 
                   token: Optional[str] = None,
                   local_path: Optional[str] = None,
                   master_key: Optional[str] = None,
                   fallback_to_env: bool = True) -> bool:
        """
        Initialize the secret manager
        
        Args:
            vault_url: HashiCorp Vault URL
            token: Vault token
            local_path: Path for local vault
            master_key: Master key for local vault
            fallback_to_env: Allow fallback to environment variables
        """
        self._fallback_to_env = fallback_to_env
        
        # Initialize vault client
        success = self.vault.initialize(
            vault_url=vault_url,
            token=token,
            local_path=local_path,
            master_key=master_key
        )
        
        if success:
            print(f"🔐 SecretManager initialized (vault mode: {self.vault._mode})")
            if fallback_to_env:
                print("   ℹ️  Fallback to environment variables enabled during migration")
        else:
            print("⚠️  SecretManager: Vault initialization failed")
            if fallback_to_env:
                print("   ℹ️  Will use environment variables as fallback")
        
        return success or fallback_to_env
    
    def get_secret(self, key: str, source: str = "unknown") -> Optional[str]:
        """
        Get a secret value
        
        Args:
            key: Secret key
            source: Source plugin or component (for audit logging)
        
        Returns:
            Secret value or None if not found
        """
        value = None
        source_type = "vault"
        
        # Try vault first
        if self.vault.is_enabled():
            value = self.vault.get(key)
        
        # Fallback to environment variable
        if value is None and self._fallback_to_env:
            value = os.getenv(key.upper())
            if value:
                source_type = "env_fallback"
                print(f"⚠️  Secret '{key}' loaded from environment (migrate to vault!)")
        
        # Log the access
        self._log_audit(
            action='get',
            key=key,
            source=source,
            success=value is not None,
            details=source_type
        )
        
        return value
    
    def set_secret(self, key: str, value: str, secret_type: SecretType = SecretType.API_KEY,
                   source: str = "unknown", ttl_days: Optional[int] = None) -> bool:
        """
        Store a secret
        
        Args:
            key: Secret key
            value: Secret value
            secret_type: Type of secret (affects rotation policy)
            source: Source of the change
            ttl_days: Optional time-to-live in days
        
        Returns:
            True if successful
        """
        if not self.vault.is_enabled():
            print(f"❌ Cannot store secret '{key}': vault not initialized")
            return False
        
        success = self.vault.set(key, value, ttl_days)
        
        if success:
            # Store metadata about secret type for rotation
            metadata_key = f"_meta_{key}"
            metadata = {
                'type': secret_type.value,
                'created_at': datetime.now().isoformat(),
                'source': source
            }
            self.vault.set(metadata_key, json.dumps(metadata))
        
        self._log_audit(
            action='set',
            key=key,
            source=source,
            success=success
        )
        
        return success
    
    def delete_secret(self, key: str, source: str = "unknown") -> bool:
        """Delete a secret"""
        if not self.vault.is_enabled():
            return False
        
        success = self.vault.delete(key)
        
        # Also delete metadata
        if success:
            self.vault.delete(f"_meta_{key}")
        
        self._log_audit(
            action='delete',
            key=key,
            source=source,
            success=success
        )
        
        return success
    
    def rotate_secret(self, key: str, new_value: Optional[str] = None,
                      source: str = "manual") -> bool:
        """
        Rotate a secret to a new value
        
        Args:
            key: Secret key
            new_value: New value (if None, uses registered callback)
            source: Source of rotation
        
        Returns:
            True if successful
        """
        if not self.vault.is_enabled():
            return False
        
        # Get new value from callback if not provided
        if new_value is None:
            callback = self._rotation_callbacks.get(key)
            if callback:
                new_value = callback()
            else:
                print(f"❌ No rotation callback registered for {key}")
                return False
        
        # Store old value for potential rollback
        old_value = self.vault.get(key)
        
        # Set new value
        success = self.vault.set(key, new_value)
        
        if success:
            # Update metadata
            metadata_key = f"_meta_{key}"
            old_metadata = self.vault.get(metadata_key)
            metadata = json.loads(old_metadata) if old_metadata else {}
            metadata['rotated_at'] = datetime.now().isoformat()
            metadata['previous_version'] = hashlib.sha256(
                (old_value or '').encode()
            ).hexdigest()[:16] if old_value else None
            self.vault.set(metadata_key, json.dumps(metadata))
            
            print(f"🔐 Rotated secret '{key}' (source: {source})")
        
        self._log_audit(
            action='rotate',
            key=key,
            source=source,
            success=success
        )
        
        return success
    
    def register_rotation_callback(self, key: str, callback: Callable[[], str]):
        """
        Register a callback function for automatic secret rotation
        
        The callback should return the new secret value
        """
        self._rotation_callbacks[key] = callback
        print(f"🔐 Registered rotation callback for '{key}'")
    
    def check_rotations(self) -> List[str]:
        """
        Check which secrets need rotation based on their type
        
        Returns:
            List of keys that need rotation
        """
        if not self.vault.is_enabled():
            return []
        
        need_rotation = []
        now = datetime.now()
        
        for key in self.vault.list_keys():
            if key.startswith('_meta_'):
                continue
            
            metadata_key = f"_meta_{key}"
            metadata_str = self.vault.get(metadata_key)
            
            if not metadata_str:
                continue
            
            try:
                metadata = json.loads(metadata_str)
                secret_type = SecretType(metadata.get('type', 'api_key'))
                created_at = datetime.fromisoformat(metadata.get('created_at', '2000-01-01'))
                rotated_at = metadata.get('rotated_at')
                
                if rotated_at:
                    last_change = datetime.fromisoformat(rotated_at)
                else:
                    last_change = created_at
                
                interval = self.ROTATION_INTERVALS.get(secret_type, 90)
                days_since_rotation = (now - last_change).days
                
                if days_since_rotation >= interval:
                    need_rotation.append(key)
                    print(f"⚠️  Secret '{key}' needs rotation ({days_since_rotation} days old)")
                    
            except Exception as e:
                print(f"⚠️  Error checking rotation for {key}: {e}")
        
        self._last_rotation_check = now
        return need_rotation
    
    def auto_rotate(self) -> Dict[str, bool]:
        """
        Automatically rotate all secrets that need rotation
        
        Returns:
            Dict mapping keys to rotation success status
        """
        results = {}
        
        for key in self.check_rotations():
            if key in self._rotation_callbacks:
                results[key] = self.rotate_secret(key, source="auto_rotation")
            else:
                print(f"⚠️  Cannot auto-rotate '{key}': no callback registered")
                results[key] = False
        
        return results
    
    def _log_audit(self, action: str, key: str, source: str, 
                   success: bool, details: Optional[str] = None):
        """Log a secret access to audit trail"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            key=key,
            source=source,
            success=success,
            details=details
        )
        
        self._audit_log.append(entry)
        
        # Keep only last 1000 entries in memory
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        # Persist to vault if available
        if self.vault.is_enabled():
            try:
                existing = self.vault.get('_audit_log')
                if existing:
                    all_logs = json.loads(existing)
                else:
                    all_logs = []
                
                all_logs.append(asdict(entry))
                
                # Keep last 5000 entries in vault
                all_logs = all_logs[-5000:]
                self.vault.set('_audit_log', json.dumps(all_logs))
            except Exception:
                pass  # Don't fail if audit logging fails
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        return [asdict(entry) for entry in self._audit_log[-limit:]]
    
    def get_secret_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get information about a secret (metadata, not the value)"""
        if not self.vault.is_enabled():
            return None
        
        metadata_key = f"_meta_{key}"
        metadata_str = self.vault.get(metadata_key)
        
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
                return {
                    'key': key,
                    'exists': self.vault.get(key) is not None,
                    **metadata
                }
            except Exception:
                pass
        
        return {'key': key, 'exists': self.vault.get(key) is not None}
    
    def list_secrets(self) -> List[str]:
        """List all secret keys (excluding metadata)"""
        if not self.vault.is_enabled():
            return []
        
        return [
            key for key in self.vault.list_keys()
            if not key.startswith('_')
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Check secret manager health"""
        vault_health = self.vault.health_check()
        
        return {
            **vault_health,
            'fallback_to_env': self._fallback_to_env,
            'rotation_callbacks_registered': len(self._rotation_callbacks),
            'audit_log_entries': len(self._audit_log),
            'last_rotation_check': self._last_rotation_check.isoformat() if self._last_rotation_check else None
        }
    
    def disable_env_fallback(self):
        """Disable environment variable fallback (call after full migration)"""
        self._fallback_to_env = False
        print("🔐 Environment variable fallback disabled - vault only mode")


# Global secret manager instance
secret_manager = SecretManager()


def get_secret_manager() -> SecretManager:
    """Get the global secret manager instance"""
    return secret_manager


def get_secret(key: str, source: str = "unknown") -> Optional[str]:
    """Convenience function to get a secret"""
    return secret_manager.get_secret(key, source)
