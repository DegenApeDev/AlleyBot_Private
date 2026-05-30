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
                # SO_REUSEADDR must be set BEFORE bind to reuse TIME_WAIT sockets
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
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
    def ensure_port_free(port: int, max_retries: int = 3) -> None:
        """Kill process on port and wait for OS to release it.

        Retries up to *max_retries* times (0.5 s between attempts).
        Raises RuntimeError if port cannot be freed.
        """
        import subprocess
        import time
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    ['lsof', '-ti', f'tcp:{port}'],
                    capture_output=True, text=True, timeout=5
                )
                if not result.stdout.strip():
                    return
                pids = result.stdout.strip().split()
                for pid in pids:
                    try:
                        os.kill(int(pid), 9)
                        print(f"  🔫 Killed stale process {pid} on port {port}")
                    except ProcessLookupError:
                        pass
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)
        raise RuntimeError(f"Port {port} still occupied after {max_retries} kill attempts")

    @staticmethod
    def write_pid_file(name: str) -> str:
        """Write a PID lock file for the given service name to /tmp/.

        Returns the lock file path.
        """
        path = f"/tmp/alleybot-{name}.pid"
        with open(path, 'w') as f:
            f.write(str(os.getpid()))
        return path

    @staticmethod
    def kill_stale_pid(name: str) -> bool:
        """If a PID file for *name* exists and the PID is alive, kill it.

        Returns True if a stale process was killed.
        """
        path = f"/tmp/alleybot-{name}.pid"
        try:
            with open(path) as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)  # check if alive
                os.kill(old_pid, 9)
                print(f"  🔫 Killed stale {name} instance (PID {old_pid})")
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return False
        except (FileNotFoundError, ValueError):
            return False
        finally:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


# Global singleton
_boot_logger: Optional[BootLogger] = None


def get_boot_logger() -> BootLogger:
    global _boot_logger
    if _boot_logger is None:
        _boot_logger = BootLogger()
    return _boot_logger
