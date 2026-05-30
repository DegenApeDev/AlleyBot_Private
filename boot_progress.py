"""
Boot Progress — Clean ANSI boot display for AlleyBot startup.
Consolidates verbose logging into structured progress lines,
redirects third-party chatter to logs/boot.log.
"""
import os
import logging
from pathlib import Path
from typing import Optional


class BootLogger:
    """Clean boot progress display with redirect of third-party chatter."""

    def __init__(self):
        self._boot_log = self._setup_boot_log()

    def _setup_boot_log(self) -> logging.Logger:
        log = logging.getLogger('boot')
        log.setLevel(logging.DEBUG)
        log.handlers.clear()
        log.propagate = False
        Path('logs').mkdir(exist_ok=True)
        handler = logging.FileHandler('logs/boot.log', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
        log.addHandler(handler)
        return log

    # ── Public display API ─────────────────────────────────────────

    def header(self, title: str):
        self._boot_log.info(f"=== {title} ===")
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}")

    def step(self, label: str, status: str = "..."):
        """Show an in-progress step. Call .ok() or .fail() to finish."""
        self._boot_log.info(f"[{status}] {label}")
        print(f"  ⏳ {label}...", end="", flush=True)

    def ok(self, detail: str = ""):
        detail = f" — {detail}" if detail else ""
        self._boot_log.info(f"[OK] {detail}")
        print(f"\r{' ' * 80}\r  ✅{detail}", flush=True)

    def warn(self, message: str):
        self._boot_log.warning(message)
        print(f"\r{' ' * 80}\r  ⚠️  {message}", flush=True)

    def fail(self, message: str):
        self._boot_log.error(message)
        print(f"\r{' ' * 80}\r  ❌ {message}", flush=True)

    def info(self, message: str):
        self._boot_log.info(message)
        print(f"  {message}")

    def debug(self, message: str):
        self._boot_log.debug(message)

    def blank(self):
        print()

    # ── Silence third-party loggers ────────────────────────────────

    def silence(self, name: str, level: int = logging.WARNING):
        """Redirect a noisy third-party logger to boot.log at WARNING+ level."""
        log = logging.getLogger(name)
        log.setLevel(level)
        log.propagate = False
        handler = logging.FileHandler('logs/boot.log', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(message)s'))
        log.addHandler(handler)

    def silence_flask(self):
        """Silence Flask development server warnings to boot.log."""
        for name in ('werkzeug', 'flask', 'flask.app'):
            self.silence(name)

    # ── Port utilities ─────────────────────────────────────────────

    @staticmethod
    def check_port(host: str, port: int) -> bool:
        """Return True if port is available."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return True
            except OSError:
                return False

    @staticmethod
    def find_available_port(host: str, preferred: int, max_attempts: int = 10) -> int:
        """Try preferred port, then increment until one is free."""
        for offset in range(max_attempts):
            candidate = preferred + offset
            if BootLogger.check_port(host, candidate):
                return candidate
        return preferred  # give up, let the caller handle

    @staticmethod
    def kill_process_on_port(port: int):
        """Try to kill whatever is holding a port (Linux/macOS)."""
        import subprocess
        try:
            result = subprocess.run(
                ['lsof', '-ti', f'tcp:{port}'],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split()
                for pid in pids:
                    os.kill(int(pid), 9)
                    print(f"  🔫 Killed stale process {pid} on port {port}")
        except Exception:
            pass  # best-effort


# Global singleton
_boot_logger: Optional[BootLogger] = None


def get_boot_logger() -> BootLogger:
    global _boot_logger
    if _boot_logger is None:
        _boot_logger = BootLogger()
    return _boot_logger
