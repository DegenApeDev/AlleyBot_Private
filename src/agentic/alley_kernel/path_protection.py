"""
Dangerous Device & Path Protection

Fail-closed security for file system operations.
Prevents reading/writing dangerous devices and sensitive paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class PathRiskLevel(Enum):
    """Risk classification for paths."""
    SAFE = "safe"
    CAUTION = "caution"  # Requires user confirmation
    DANGEROUS = "dangerous"  # Blocked by default
    CRITICAL = "critical"  # Always blocked


@dataclass
class PathProtection:
    """
    Multi-layered path protection for agent file operations.
    
    Protects against:
    - Dangerous device files (/dev/zero, /dev/random, etc.)
    - Sensitive configuration files (.bashrc, .ssh/config)
    - System directories that could break the system
    - Path traversal attacks
    """
    
    # Device files that are dangerous to read
    BLOCKED_DEVICE_PATHS: set[str] = field(default_factory=lambda: {
        # Infinite output - never reach EOF
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/full",
        # Blocking input devices
        "/dev/stdin",
        "/dev/tty",
        "/dev/console",
        # Output devices (nonsensical to read)
        "/dev/stdout",
        "/dev/stderr",
        # File descriptor aliases
        "/dev/fd/0",
        "/dev/fd/1",
        "/dev/fd/2",
        # /proc aliases
        "/proc/self/fd/0",
        "/proc/self/fd/1",
        "/proc/self/fd/2",
    })
    
    # Sensitive files that should not be auto-edited
    DANGEROUS_FILES: set[str] = field(default_factory=lambda: {
        ".gitconfig",
        ".gitmodules",
        ".bashrc",
        ".bash_profile",
        ".bash_logout",
        ".zshrc",
        ".zprofile",
        ".zshenv",
        ".profile",
        ".env",
        ".env.local",
        ".env.production",
        ".env.staging",
        ".netrc",
        ".ssh/config",
        ".ssh/id_rsa",
        ".ssh/id_ed25519",
        ".ssh/authorized_keys",
        ".ssh/known_hosts",
        ".aws/credentials",
        ".aws/config",
        ".docker/config.json",
        ".npmrc",
        ".pypirc",
        ".pgpass",
        ".my.cnf",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
        ".htpasswd",
        "htpasswd",
    })
    
    # Dangerous directories
    DANGEROUS_DIRECTORIES: set[str] = field(default_factory=lambda: {
        ".git",
        ".ssh",
        ".aws",
        ".gnupg",
        ".docker",
        "node_modules/.bin",
        ".venv/bin",
        "venv/bin",
        ".tox",
        ".pytest_cache",
        "__pycache__",
    })
    
    # System-critical directories (always blocked)
    CRITICAL_SYSTEM_PATHS: set[str] = field(default_factory=lambda: {
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/lib",
        "/lib64",
        "/usr/lib",
        "/usr/lib64",
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/boot",
        "/sys",
        "/proc",
        "/dev",
        "/var/log",
        "/var/spool",
    })
    
    # Path traversal patterns
    TRAVERSAL_PATTERNS: list[str] = field(default_factory=lambda: [
        "../",
        "..\\",
        "..",
        "./.",
        "...",  # triple dot trick
    ])

    def classify_path(self, path: str, operation: str = "read") -> PathRiskLevel:
        """
        Classify a path by risk level.
        
        Args:
            path: File path to classify
            operation: Type of operation (read, write, execute)
            
        Returns:
            Risk level classification
        """
        normalized = path.lower().strip()
        
        # Check device paths
        if self._is_blocked_device(normalized):
            return PathRiskLevel.CRITICAL
        
        # Check critical system paths
        if self._is_critical_system_path(normalized):
            return PathRiskLevel.CRITICAL
        
        # Check for path traversal
        if self._contains_traversal(normalized):
            return PathRiskLevel.DANGEROUS
        
        # Check dangerous files
        if self._is_dangerous_file(normalized):
            if operation == "write":
                return PathRiskLevel.DANGEROUS
            return PathRiskLevel.CAUTION
        
        # Check dangerous directories
        if self._is_dangerous_directory(normalized):
            if operation == "write":
                return PathRiskLevel.DANGEROUS
            return PathRiskLevel.CAUTION
        
        return PathRiskLevel.SAFE

    def validate_operation(
        self,
        path: str,
        operation: str = "read",
        allow_dangerous: bool = False,
    ) -> dict[str, Any]:
        """
        Validate a file operation.
        
        Args:
            path: File path
            operation: Operation type (read, write, execute)
            allow_dangerous: Override dangerous blocks
            
        Returns:
            Validation result with allowed/rejected status
        """
        risk_level = self.classify_path(path, operation)
        
        result = {
            "path": path,
            "operation": operation,
            "risk_level": risk_level.value,
            "allowed": True,
            "reason": None,
        }
        
        if risk_level == PathRiskLevel.CRITICAL:
            result["allowed"] = False
            result["reason"] = f"CRITICAL: {path} is a system-critical resource and cannot be accessed"
        
        elif risk_level == PathRiskLevel.DANGEROUS:
            if not allow_dangerous:
                result["allowed"] = False
                result["reason"] = f"DANGEROUS: {path} is a sensitive file/directory and requires explicit permission"
            else:
                result["reason"] = f"DANGEROUS (override): {path} allowed with dangerous flag"
        
        elif risk_level == PathRiskLevel.CAUTION:
            result["reason"] = f"CAUTION: {path} is a potentially sensitive file"
        
        return result

    def _is_blocked_device(self, path: str) -> bool:
        """Check if path is a blocked device."""
        # Direct match
        if path in self.BLOCKED_DEVICE_PATHS:
            return True
        
        # Handle /proc/<pid>/fd/ patterns
        if path.startswith("/proc/") and "/fd/" in path:
            try:
                # Extract fd number
                parts = path.split("/")
                fd_idx = parts.index("fd")
                if fd_idx + 1 < len(parts):
                    fd = parts[fd_idx + 1]
                    if fd in ("0", "1", "2"):
                        return True
            except (ValueError, IndexError):
                pass
        
        return False

    def _is_critical_system_path(self, path: str) -> bool:
        """Check if path is a critical system path."""
        for critical in self.CRITICAL_SYSTEM_PATHS:
            if path == critical or path.startswith(critical + "/"):
                return True
        return False

    def _contains_traversal(self, path: str) -> bool:
        """Check for path traversal patterns."""
        # Normalize for comparison
        normalized = path.replace("\\", "/")
        
        for pattern in self.TRAVERSAL_PATTERNS:
            if pattern in normalized:
                return True
        
        return False

    def _is_dangerous_file(self, path: str) -> bool:
        """Check if path matches dangerous file patterns."""
        # Check filename
        filename = path.split("/")[-1].split("\\")[-1]
        if filename in self.DANGEROUS_FILES:
            return True
        
        # Check full path patterns
        for dangerous in self.DANGEROUS_FILES:
            if dangerous.lower() in path:
                return True
        
        return False

    def _is_dangerous_directory(self, path: str) -> bool:
        """Check if path is in or is a dangerous directory."""
        for dangerous in self.DANGEROUS_DIRECTORIES:
            if f"/{dangerous}/" in path or f"\\{dangerous}\\" in path:
                return True
            if path.rstrip("/\\").endswith(f"/{dangerous}") or path.rstrip("/\\").endswith(f"\\{dangerous}"):
                return True
        return False

    def sanitize_path(self, path: str) -> str:
        """
        Sanitize a path by normalizing case and separators.
        
        Args:
            path: Raw path string
            
        Returns:
            Normalized path for safe comparison
        """
        # Normalize separators
        normalized = path.replace("\\", "/")
        
        # Normalize case for case-insensitive filesystems
        normalized = normalized.lower()
        
        # Remove trailing slashes
        normalized = normalized.rstrip("/")
        
        return normalized

    def get_protection_summary(self) -> dict[str, Any]:
        """Get summary of protection rules."""
        return {
            "blocked_devices": len(self.BLOCKED_DEVICE_PATHS),
            "dangerous_files": len(self.DANGEROUS_FILES),
            "dangerous_directories": len(self.DANGEROUS_DIRECTORIES),
            "critical_paths": len(self.CRITICAL_SYSTEM_PATHS),
        }

    def format_validation_error(self, validation: dict[str, Any]) -> str:
        """Format a validation error message."""
        if validation["allowed"]:
            if validation["reason"]:
                return f"⚠️ {validation['reason']}"
            return "✅ Path is safe"
        
        return f"🚫 {validation['reason']}"


# Global instance for convenience
_global_protection: PathProtection | None = None


def get_path_protection() -> PathProtection:
    """Get the global path protection instance."""
    global _global_protection
    if _global_protection is None:
        _global_protection = PathProtection()
    return _global_protection


def validate_path(
    path: str,
    operation: str = "read",
    allow_dangerous: bool = False,
) -> dict[str, Any]:
    """Convenience function to validate a path."""
    return get_path_protection().validate_operation(
        path, operation, allow_dangerous
    )


def is_dangerous_path(path: str, operation: str = "read") -> bool:
    """Quick check if path is dangerous."""
    result = validate_path(path, operation)
    return not result["allowed"]
