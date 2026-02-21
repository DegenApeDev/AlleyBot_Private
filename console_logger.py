#!/usr/bin/env python3
"""
Console Logger - Captures complete terminal output with rotation
Keeps 7 days of logs, automatically trims older logs
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

class ConsoleLogger:
    """Captures complete console output (stdout/stderr) to daily rotating logs"""

    def __init__(self, log_dir='logs/console', max_days=7):
        self.log_dir = Path(log_dir)
        self.max_days = max_days
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logger()

        # Clean old logs on startup
        self._cleanup_old_logs()

    def _setup_logger(self):
        """Setup the logger with daily rotation"""
        # Create logger
        logger = logging.getLogger('console_output')
        logger.setLevel(logging.INFO)

        # Clear any existing handlers
        logger.handlers.clear()

        # Get today's date for filename
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'console_{today}.log'

        # Create rotating file handler (10MB per file, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)
        
        # CRITICAL: Prevent logger from propagating to root logger (which writes to stderr)
        logger.propagate = False

        return logger

    def _cleanup_old_logs(self):
        """Remove log files older than max_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_days)

            for log_file in self.log_dir.glob('console_*.log*'):
                try:
                    # Extract date from filename (console_YYYY-MM-DD.log)
                    filename = log_file.name
                    if 'console_' in filename:
                        date_str = filename.split('console_')[1].split('.log')[0]
                        # Handle backup files (.log.1, .log.2, etc.)
                        date_str = date_str.split('.log')[0]

                        try:
                            file_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if file_date < cutoff_date:
                                log_file.unlink()
                                print(f"🗑️ Cleaned up old log: {log_file.name}")
                        except ValueError:
                            # Skip files with invalid date format
                            pass
                except Exception as e:
                    print(f"⚠️ Error cleaning log file {log_file}: {e}")

        except Exception as e:
            print(f"⚠️ Error during log cleanup: {e}")

    class _StreamCapture:
        """Custom stream that writes to both console and log file"""

        def __init__(self, stream, logger, level):
            self.stream = stream
            self.logger = logger
            self.level = level
            self._in_write = False  # Prevent recursion

        def write(self, message):
            # Prevent infinite recursion
            if self._in_write:
                # Emergency fallback - write directly without logging
                try:
                    if isinstance(message, bytes):
                        message = message.decode('utf-8', errors='replace')
                    self.stream.write(message)
                    self.stream.flush()
                except:
                    pass
                return
                
            self._in_write = True
            try:
                # Handle both string and bytes input (Flask sends bytes, others send strings)
                if isinstance(message, bytes):
                    message = message.decode('utf-8', errors='replace')
                
                # Write to original stream (console)
                self.stream.write(message)
                self.stream.flush()

                # Write to log only if not empty and not prompts, and handle carefully
                if message and message.strip() and not message.startswith('AlleyBot> '):
                    try:
                        if self.level == 'info':
                            self.logger.info(message.rstrip())
                        elif self.level == 'error':
                            self.logger.error(message.rstrip())
                    except Exception:
                        # If logging fails, don't crash - just continue
                        pass
            finally:
                self._in_write = False

        def flush(self):
            try:
                self.stream.flush()
            except:
                pass

        def isatty(self):
            """Return whether this is an 'interactive' stream (always False for logging)"""
            return False

    def start_capture(self):
        """Start capturing stdout and stderr"""
        # Replace stdout and stderr
        sys.stdout = self._StreamCapture(self.original_stdout, self.logger, 'info')
        sys.stderr = self._StreamCapture(self.original_stderr, self.logger, 'error')

        print("📝 Console logging started - capturing all output to daily logs")
        print(f"📁 Log directory: {self.log_dir}")
        print(f"🗂️  Retention: {self.max_days} days (auto-cleanup enabled)")

    def stop_capture(self):
        """Stop capturing and restore original streams"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        print("🛑 Console logging stopped")

    def get_log_stats(self):
        """Get statistics about current logs"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'oldest_date': None,
            'newest_date': None,
            'files': []
        }

        try:
            for log_file in self.log_dir.glob('console_*.log*'):
                stats['total_files'] += 1

                # Get file size
                size_mb = log_file.stat().st_size / (1024 * 1024)
                stats['total_size_mb'] += size_mb

                # Extract date from filename
                filename = log_file.name
                if 'console_' in filename:
                    date_str = filename.split('console_')[1].split('.log')[0]
                    try:
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')

                        if stats['oldest_date'] is None or file_date < stats['oldest_date']:
                            stats['oldest_date'] = file_date
                        if stats['newest_date'] is None or file_date > stats['newest_date']:
                            stats['newest_date'] = file_date

                        stats['files'].append({
                            'name': filename,
                            'date': file_date.strftime('%Y-%m-%d'),
                            'size_mb': round(size_mb, 2)
                        })
                    except ValueError:
                        pass

            # Sort files by date
            stats['files'].sort(key=lambda x: x['date'], reverse=True)

        except Exception as e:
            stats['error'] = str(e)

        return stats

# Global logger instance
_console_logger = None

def init_console_logging(log_dir='logs/console', max_days=7):
    """Initialize console logging globally"""
    global _console_logger
    _console_logger = ConsoleLogger(log_dir, max_days)
    _console_logger.start_capture()
    return _console_logger

def stop_console_logging():
    """Stop console logging globally"""
    global _console_logger
    if _console_logger:
        _console_logger.stop_capture()
        _console_logger = None

def get_console_logger():
    """Get the current console logger instance"""
    return _console_logger

if __name__ == "__main__":
    # Test the logger
    logger = ConsoleLogger()
    logger.start_capture()

    print("🧪 Testing console logger...")
    print("This message should appear in both console and log file")

    import time
    time.sleep(1)

    stats = logger.get_log_stats()
    print(f"📊 Log stats: {stats}")

    logger.stop_capture()
    print("✅ Console logger test complete")
