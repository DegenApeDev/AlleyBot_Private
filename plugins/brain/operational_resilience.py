"""
Operational Resilience Mixin for Phase 9
Health alerts, rate limiting, uptime monitoring, and crash recovery
"""
import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque


class OperationalResilienceMixin:
    """Mixin for operational resilience - alerts, rate limits, uptime monitoring"""
    
    # Mixin metadata for documentation and validation
    REQUIRES = []  # Independent monitoring system
    PROVIDES = ["check_rate_limit", "send_alert", "get_uptime"]
    INIT_ORDER = 9

    def _init_operational_resilience(self):
        """Initialize operational resilience systems"""
        # Health monitoring
        self.health_status: Dict[str, Any] = {
            'last_check': datetime.now().isoformat(),
            'api_errors': defaultdict(list),  # platform -> list of recent errors
            'engagement_drops': [],
            'low_balance_alert_sent': False,
        }

        # Rate limit tracking per platform
        self.rate_limits: Dict[str, Dict] = {
            'moltx': {'requests': deque(maxlen=100), 'backoff_until': None, 'limit': 100, 'window': 60},
            'moltbook': {'requests': deque(maxlen=100), 'backoff_until': None, 'limit': 100, 'window': 60},
            'clawbr': {'requests': deque(maxlen=100), 'backoff_until': None, 'limit': 10, 'window': 60},
            'onchain': {'requests': deque(maxlen=50), 'backoff_until': None, 'limit': 30, 'window': 60},
            'crypto': {'requests': deque(maxlen=50), 'backoff_until': None, 'limit': 50, 'window': 60},
        }

        # Uptime tracking
        self.start_time = datetime.now()
        self.uptime_checks: List[Dict] = []
        self.crash_recovery_attempts = 0
        self.last_heartbeat = datetime.now()

        # Alert throttling
        self.last_alerts: Dict[str, datetime] = {}
        self.alert_cooldowns = {
            'api_error': timedelta(minutes=15),
            'low_balance': timedelta(hours=6),
            'engagement_drop': timedelta(hours=2),
            'rate_limit': timedelta(minutes=30),
        }

        self._load_resilience_state()

        # Start background monitoring
        self._start_health_monitor()

    def _load_resilience_state(self):
        """Load operational resilience state from memory"""
        try:
            state = self.core.get_memory('brain_resilience_state')
            if state:
                self.health_status = state.get('health_status', self.health_status)
                self.crash_recovery_attempts = state.get('crash_recovery_attempts', 0)
                
                # Restore rate limits with proper deque reconstruction
                saved_rate_limits = state.get('rate_limits', {})
                for platform, limits in saved_rate_limits.items():
                    if platform in self.rate_limits:
                        # Convert list back to deque
                        requests_list = limits.get('requests', [])
                        self.rate_limits[platform]['requests'] = deque(requests_list, maxlen=100)
                        
                        # Restore backoff time
                        backoff_str = limits.get('backoff_until')
                        if backoff_str:
                            self.rate_limits[platform]['backoff_until'] = datetime.fromisoformat(backoff_str)
                        else:
                            self.rate_limits[platform]['backoff_until'] = None
        except Exception:
            pass

    def _save_resilience_state(self):
        """Save operational resilience state"""
        try:
            # Convert deques to lists for JSON serialization
            serializable_rate_limits = {}
            for platform, limits in self.rate_limits.items():
                serializable_rate_limits[platform] = {
                    'requests': list(limits['requests']),  # Convert deque to list
                    'backoff_until': limits['backoff_until'].isoformat() if limits['backoff_until'] else None,
                    'limit': limits['limit'],
                    'window': limits['window'],
                }
            
            self.core.save_memory('brain_resilience_state', {
                'health_status': dict(self.health_status),
                'rate_limits': serializable_rate_limits,
                'crash_recovery_attempts': self.crash_recovery_attempts,
                'last_saved': datetime.now().isoformat(),
            })
        except Exception as e:
            print(f"⚠️  Failed to save resilience state: {e}")

    # =========================================================================
    # Health Alerts via Telegram
    # =========================================================================

    def send_health_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Send health alert via Telegram with throttling"""
        # Check cooldown
        now = datetime.now()
        cooldown = self.alert_cooldowns.get(alert_type, timedelta(minutes=30))

        if alert_type in self.last_alerts:
            if now - self.last_alerts[alert_type] < cooldown:
                return  # Skip - still in cooldown

        # Update last alert time
        self.last_alerts[alert_type] = now

        # Get Telegram plugin
        telegram = self.core.plugin_manager.plugins.get('telegram')
        if not telegram or not hasattr(telegram, 'send_message_to_owner_sync'):
            print(f"⚠️  Cannot send {severity} alert (no Telegram): {message[:60]}...")
            return

        # Format alert message
        emoji_map = {
            'critical': '🔴',
            'warning': '⚠️',
            'info': 'ℹ️',
        }
        emoji = emoji_map.get(severity, '⚠️')

        alert_msg = (
            f"{emoji} **AlleyBot Health Alert**\n\n"
            f"Type: {alert_type.replace('_', ' ').title()}\n"
            f"Severity: {severity.upper()}\n"
            f"Time: {now.strftime('%H:%M:%S')}\n\n"
            f"{message}\n\n"
            f"Uptime: {self.get_uptime_str()}"
        )

        try:
            telegram.send_message_to_owner_sync(alert_msg)
            print(f"📢 Health alert sent: {alert_type} ({severity})")
        except Exception as e:
            print(f"❌ Failed to send health alert: {e}")

    def record_api_error(self, platform: str, error: str, endpoint: str = ''):
        """Record an API error and potentially send alert"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error': error[:200],
            'endpoint': endpoint,
        }

        self.health_status['api_errors'][platform].append(error_info)

        # Keep only recent errors (last 24 hours)
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        self.health_status['api_errors'][platform] = [
            e for e in self.health_status['api_errors'][platform]
            if e['timestamp'] > cutoff
        ]

        # Count recent errors
        recent_errors = len(self.health_status['api_errors'][platform])

        # Alert if error count is high
        if recent_errors >= 5:
            self.send_health_alert(
                'api_error',
                f"Platform {platform} has {recent_errors} errors in last 24h.\n"
                f"Latest: {error[:100]}...",
                'warning' if recent_errors < 10 else 'critical'
            )

        self._save_resilience_state()

    def check_low_balance(self, eth_balance: float, token_balances: Dict[str, float]):
        """Check for low balance and send alert if needed"""
        alerts = []

        # ETH threshold (0.001 ETH ~ $2-3)
        if eth_balance < 0.001:
            alerts.append(f"ETH balance low: {eth_balance:.6f} ETH")

        # ALLEY token threshold
        alley_balance = token_balances.get('ALLEY', 0)
        if alley_balance < 100:
            alerts.append(f"ALLEY balance low: {alley_balance:,.0f} ALLEY")

        if alerts and not self.health_status.get('low_balance_alert_sent'):
            self.send_health_alert(
                'low_balance',
                "Low balance detected:\n" + "\n".join(alerts) + "\n\n"
                "Consider topping up wallet for continued operations.",
                'warning'
            )
            self.health_status['low_balance_alert_sent'] = True
            self._save_resilience_state()
        elif not alerts:
            # Reset alert flag if balances are now healthy
            self.health_status['low_balance_alert_sent'] = False

    def check_engagement_drop(self, current_rate: float, baseline_rate: float):
        """Check for engagement drops and alert"""
        if baseline_rate == 0:
            return

        drop_ratio = current_rate / baseline_rate

        if drop_ratio < 0.5:  # 50% drop
            self.health_status['engagement_drops'].append({
                'timestamp': datetime.now().isoformat(),
                'current_rate': current_rate,
                'baseline_rate': baseline_rate,
                'drop_ratio': drop_ratio,
            })

            # Keep only recent drops
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            self.health_status['engagement_drops'] = [
                d for d in self.health_status['engagement_drops']
                if d['timestamp'] > cutoff
            ]

            # Alert on significant drop
            if len(self.health_status['engagement_drops']) >= 2:
                self.send_health_alert(
                    'engagement_drop',
                    f"Engagement dropped to {drop_ratio:.0%} of baseline.\n"
                    f"Current: {current_rate:.1%} | Baseline: {baseline_rate:.1%}\n\n"
                    "Consider adjusting content strategy or checking platform health.",
                    'warning'
                )

            self._save_resilience_state()

    # =========================================================================
    # Rate Limit Awareness
    # =========================================================================

    def record_request(self, platform: str):
        """Record an API request for rate limiting"""
        if platform not in self.rate_limits:
            return

        now = time.time()
        self.rate_limits[platform]['requests'].append(now)

    def is_rate_limited(self, platform: str) -> tuple[bool, Optional[int]]:
        """
        Check if platform is rate limited
        Returns (is_limited, retry_after_seconds)
        """
        if platform not in self.rate_limits:
            return False, None

        limits = self.rate_limits[platform]

        # Check if in backoff period
        if limits['backoff_until']:
            if datetime.now() < limits['backoff_until']:
                retry_after = int((limits['backoff_until'] - datetime.now()).total_seconds())
                return True, retry_after
            else:
                # Backoff period ended
                limits['backoff_until'] = None

        # Check request rate
        now = time.time()
        window_start = now - limits['window']

        # Count requests in window
        requests_in_window = sum(1 for t in limits['requests'] if t > window_start)

        if requests_in_window >= limits['limit']:
            # Hit rate limit - set backoff
            retry_after = limits['window']
            limits['backoff_until'] = datetime.now() + timedelta(seconds=retry_after)

            # Send alert
            self.send_health_alert(
                'rate_limit',
                f"Rate limit hit for {platform}.\n"
                f"Limit: {limits['limit']} requests per {limits['window']}s.\n"
                f"Backing off for {retry_after}s.",
                'warning'
            )

            self._save_resilience_state()
            return True, retry_after

        return False, None

    def get_rate_limit_status(self, platform: str) -> Dict[str, Any]:
        """Get current rate limit status for a platform"""
        if platform not in self.rate_limits:
            return {'error': f'Unknown platform: {platform}'}

        limits = self.rate_limits[platform]
        now = time.time()
        window_start = now - limits['window']

        requests_in_window = sum(1 for t in limits['requests'] if t > window_start)

        return {
            'platform': platform,
            'limit': limits['limit'],
            'window': limits['window'],
            'requests_used': requests_in_window,
            'requests_remaining': limits['limit'] - requests_in_window,
            'in_backoff': limits['backoff_until'] is not None,
            'backoff_until': limits['backoff_until'].isoformat() if limits['backoff_until'] else None,
        }

    def get_backoff_delay(self, platform: str) -> float:
        """Get recommended backoff delay for a platform"""
        is_limited, retry_after = self.is_rate_limited(platform)

        if is_limited and retry_after:
            return retry_after

        # If approaching limit, add small delay
        status = self.get_rate_limit_status(platform)
        
        # Check if status returned an error (platform not found)
        if 'error' in status:
            return 0.0
            
        limit = status.get('limit', 0)
        if limit <= 0:
            return 0.0
            
        usage_ratio = status['requests_used'] / limit

        if usage_ratio > 0.8:
            return 5.0  # 5 second delay when near limit
        elif usage_ratio > 0.5:
            return 1.0  # 1 second delay at moderate usage

        return 0.0  # No delay needed

    # =========================================================================
    # Uptime Monitoring and Crash Recovery
    # =========================================================================

    def get_uptime(self) -> timedelta:
        """Get current uptime"""
        return datetime.now() - self.start_time

    def get_uptime_str(self) -> str:
        """Get uptime as formatted string"""
        uptime = self.get_uptime()
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"

    def record_heartbeat(self):
        """Record a heartbeat for uptime tracking"""
        now = datetime.now()
        self.last_heartbeat = now

        # Check if there was a gap (possible crash/restart)
        if self.uptime_checks:
            last_check = datetime.fromisoformat(self.uptime_checks[-1]['timestamp'])
            gap = (now - last_check).total_seconds()

            # If gap > 5 minutes, might be a crash
            if gap > 300:
                self.crash_recovery_attempts += 1
                self.send_health_alert(
                    'crash_recovery',
                    f"Possible crash detected. Gap in heartbeats: {gap/60:.1f} minutes.\n"
                    f"This is recovery attempt #{self.crash_recovery_attempts}.",
                    'critical'
                )
                self._save_resilience_state()

        # Record the check
        self.uptime_checks.append({
            'timestamp': now.isoformat(),
            'uptime_seconds': self.get_uptime().total_seconds(),
        })

        # Keep only recent checks (last 30 days)
        cutoff = (now - timedelta(days=30)).isoformat()
        self.uptime_checks = [c for c in self.uptime_checks if c['timestamp'] > cutoff]

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        # Calculate API error rates per platform
        error_rates = {}
        for platform, errors in self.health_status['api_errors'].items():
            recent_errors = len([e for e in errors
                               if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=24)])
            error_rates[platform] = recent_errors

        # Get rate limit status for all platforms
        rate_status = {p: self.get_rate_limit_status(p) for p in self.rate_limits}

        return {
            'uptime': self.get_uptime_str(),
            'uptime_seconds': self.get_uptime().total_seconds(),
            'crash_recovery_attempts': self.crash_recovery_attempts,
            'api_errors_24h': error_rates,
            'rate_limits': rate_status,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'engagement_drops_7d': len(self.health_status.get('engagement_drops', [])),
            'low_balance_alert_active': self.health_status.get('low_balance_alert_sent', False),
        }

    def _start_health_monitor(self):
        """Start background health monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    self.record_heartbeat()

                    # Check on-chain balance periodically (every hour)
                    if int(self.get_uptime().total_seconds()) % 3600 < 60:
                        onchain = self.core.plugin_manager.plugins.get('onchain')
                        if onchain and hasattr(onchain, 'get_wallet_info'):
                            try:
                                wallet = onchain.get_wallet_info()
                                self.check_low_balance(
                                    wallet.get('eth_balance', 0),
                                    wallet.get('token_balances', {})
                                )
                            except Exception:
                                pass

                    time.sleep(60)  # Check every minute

                except Exception as e:
                    print(f"⚠️  Health monitor error: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    # =========================================================================
    # CLI Commands
    # =========================================================================

    def resilience_status_command(self, *args):
        """Show operational resilience status"""
        summary = self.get_health_summary()

        output = "🛡️ Operational Resilience Status\n\n"
        output += f"  ⏱️  Uptime: {summary['uptime']}\n"
        output += f"  💔 Crash Recoveries: {summary['crash_recovery_attempts']}\n"
        output += f"  💓 Last Heartbeat: {summary['last_heartbeat'][11:19]}\n\n"

        # API Errors
        if summary['api_errors_24h']:
            output += "  📊 API Errors (24h):\n"
            for platform, count in summary['api_errors_24h'].items():
                if count > 0:
                    emoji = '🔴' if count > 5 else '🟡' if count > 1 else '🟢'
                    output += f"    {emoji} {platform}: {count} errors\n"
        else:
            output += "  ✅ No API errors in last 24h\n"

        # Rate Limits
        output += "\n  🚦 Rate Limits:\n"
        for platform, status in summary['rate_limits'].items():
            if status.get('in_backoff'):
                output += f"    🔴 {platform}: BACKOFF until {status['backoff_until'][11:16]}\n"
            else:
                usage = status['requests_used'] / status['limit'] * 100
                emoji = '🔴' if usage > 80 else '🟡' if usage > 50 else '🟢'
                output += f"    {emoji} {platform}: {usage:.0f}% used ({status['requests_used']}/{status['limit']})\n"

        # Engagement
        if summary['engagement_drops_7d'] > 0:
            output += f"\n  ⚠️  Engagement drops (7d): {summary['engagement_drops_7d']}\n"

        # Balance
        if summary['low_balance_alert_active']:
            output += "\n  🔴 Low balance alert is ACTIVE\n"

        return output

    def test_alert_command(self, *args):
        """Test health alert system"""
        alert_type = args[0] if args else 'info'
        self.send_health_alert(
            'test',
            f"This is a test {alert_type} alert from AlleyBot.",
            alert_type if alert_type in ['critical', 'warning', 'info'] else 'info'
        )
        return f"📢 Test {alert_type} alert sent to Telegram"
