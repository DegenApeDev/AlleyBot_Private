"""
Phase 13.5: Crisis Detection System
Pauses posting if platform issues or controversies detected
Multi-signal crisis detection with automatic pause/resume
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import asyncio


class CrisisLevel(Enum):
    """Severity levels for detected issues"""
    INFO = "info"           # FYI, no action needed
    WATCH = "watch"         # Monitor closely
    WARNING = "warning"     # Reduce posting
    CRITICAL = "critical"   # Pause all posting
    EMERGENCY = "emergency" # Immediate action required


class CrisisType(Enum):
    """Types of crises that can be detected"""
    PLATFORM_OUTAGE = "platform_outage"
    RATE_LIMITING = "rate_limiting"
    API_ERROR_SPIKE = "api_error_spike"
    CONTROVERSY = "controversy"
    NEGATIVE_SENTIMENT_SPIKE = "negative_sentiment"
    COMPETITOR_ISSUE = "competitor_issue"
    REGULATORY_NEWS = "regulatory_news"
    SECURITY_INCIDENT = "security_incident"
    COMMUNITY_BACKLASH = "community_backlash"
    TOPIC_SENSITIVITY = "topic_sensitivity"


@dataclass
class CrisisAlert:
    """A detected crisis/alert"""
    crisis_type: CrisisType
    level: CrisisLevel
    message: str
    detected_at: datetime
    expires_at: Optional[datetime] = None
    affected_platforms: List[str] = None
    recommended_action: str = ""
    metadata: Optional[Dict] = None


class CrisisDetector:
    """
    Detects platform issues and controversies
    Automatically pauses posting when needed
    """
    
    # Keywords that indicate sensitive/controversial topics
    CONTROVERSY_KEYWORDS = {
        'high': ['scam', 'rug', 'hack', 'exploit', 'stolen', 'lawsuit', 'investigation', 
                'fraud', 'collapse', 'bankruptcy', 'shutdown', 'banned'],
        'medium': ['controversy', 'criticism', 'concerns', 'allegations', 'accused',
                  'investigating', 'dispute', 'controversial', 'backlash'],
        'crypto_specific': ['ponzi', 'pump and dump', 'insider trading', 'market manipulation',
                          'liquidity crisis', 'depeg', 'withdrawals halted']
    }
    
    def __init__(self, db_path: str = 'data/crisis.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        # Current crisis state
        self.active_crises: Dict[str, CrisisAlert] = {}
        self.paused_platforms: Set[str] = set()
        self.global_pause = False
        
        # Thresholds
        self.error_rate_threshold = 0.3  # 30% error rate triggers warning
        self.negative_sentiment_threshold = -0.5
        self.controversy_mention_threshold = 5  # Mentions per hour
    
    def _init_db(self):
        """Initialize crisis database"""
        with sqlite3.connect(self.db_path) as conn:
            # Crisis history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crisis_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crisis_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    duration_minutes REAL,
                    affected_platforms TEXT,  -- JSON array
                    triggered_pause BOOLEAN DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            # Platform health metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_healthy BOOLEAN DEFAULT 1,
                    error_rate REAL DEFAULT 0,
                    response_time_ms INTEGER,
                    api_status TEXT,
                    sentiment_score REAL,
                    mention_volume INTEGER,
                    controversy_score REAL DEFAULT 0
                )
            """)
            
            # Pause history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pause_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    global_pause BOOLEAN DEFAULT 0,
                    paused_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resumed_at TIMESTAMP,
                    reason TEXT,
                    triggered_by_crisis TEXT,
                    manual BOOLEAN DEFAULT 0
                )
            """)
            
            # Sentiment tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    topic TEXT,
                    avg_sentiment REAL,
                    sample_size INTEGER,
                    negative_mentions INTEGER,
                    total_mentions INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def check_api_health(self, platform: str, error_count: int, 
                        total_requests: int,
                        avg_response_time_ms: int = None) -> Optional[CrisisAlert]:
        """Check if platform API is healthy"""
        if total_requests == 0:
            return None
        
        error_rate = error_count / total_requests
        
        # Record health metrics
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO platform_health (platform, error_rate, response_time_ms) "
                "VALUES (?, ?, ?)",
                (platform, error_rate, avg_response_time_ms)
            )
            conn.commit()
        
        # Check for issues
        if error_rate > 0.8:
            return CrisisAlert(
                crisis_type=CrisisType.API_ERROR_SPIKE,
                level=CrisisLevel.CRITICAL,
                message=f"{platform} API error rate: {error_rate:.1%} - critical failure",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="pause_posting",
                metadata={'error_rate': error_rate, 'error_count': error_count}
            )
        elif error_rate > self.error_rate_threshold:
            return CrisisAlert(
                crisis_type=CrisisType.API_ERROR_SPIKE,
                level=CrisisLevel.WARNING,
                message=f"{platform} API elevated error rate: {error_rate:.1%}",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="reduce_posting",
                metadata={'error_rate': error_rate}
            )
        elif avg_response_time_ms and avg_response_time_ms > 10000:
            return CrisisAlert(
                crisis_type=CrisisType.PLATFORM_OUTAGE,
                level=CrisisLevel.WARNING,
                message=f"{platform} API very slow ({avg_response_time_ms}ms)",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="monitor",
                metadata={'response_time': avg_response_time_ms}
            )
        
        return None
    
    def detect_controversy(self, platform: str, 
                          recent_posts: List[Dict]) -> Optional[CrisisAlert]:
        """Detect if controversial topics are trending"""
        if not recent_posts:
            return None
        
        # Count controversy keywords
        high_risk_count = 0
        medium_risk_count = 0
        crypto_risk_count = 0
        
        for post in recent_posts:
            content = post.get('content', '').lower()
            
            for keyword in self.CONTROVERSY_KEYWORDS['high']:
                if keyword in content:
                    high_risk_count += 1
            
            for keyword in self.CONTROVERSY_KEYWORDS['medium']:
                if keyword in content:
                    medium_risk_count += 1
            
            for keyword in self.CONTROVERSY_KEYWORDS['crypto_specific']:
                if keyword in content:
                    crypto_risk_count += 1
        
        # Calculate controversy score
        score = (high_risk_count * 3 + medium_risk_count * 1 + crypto_risk_count * 2)
        
        # Record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO platform_health (platform, controversy_score) VALUES (?, ?)",
                (platform, score)
            )
            conn.commit()
        
        # Check thresholds
        if high_risk_count >= 3 or score >= 10:
            return CrisisAlert(
                crisis_type=CrisisType.CONTROVERSY,
                level=CrisisLevel.CRITICAL,
                message=f"High-risk controversy detected on {platform} "
                       f"({high_risk_count} high-risk, {crypto_risk_count} crypto-risk mentions)",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="pause_posting",
                metadata={
                    'high_risk_mentions': high_risk_count,
                    'medium_risk_mentions': medium_risk_count,
                    'crypto_risk_mentions': crypto_risk_count,
                    'controversy_score': score
                }
            )
        elif medium_risk_count >= self.controversy_mention_threshold:
            return CrisisAlert(
                crisis_type=CrisisType.TOPIC_SENSITIVITY,
                level=CrisisLevel.WARNING,
                message=f"Sensitive topics trending on {platform} "
                       f"({medium_risk_count} medium-risk mentions)",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="review_content",
                metadata={'medium_risk_mentions': medium_risk_count}
            )
        
        return None
    
    def analyze_sentiment_spike(self, platform: str, 
                                sentiment_scores: List[float]) -> Optional[CrisisAlert]:
        """Detect negative sentiment spikes"""
        if len(sentiment_scores) < 10:
            return None
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        negative_count = sum(1 for s in sentiment_scores if s < -0.3)
        negative_ratio = negative_count / len(sentiment_scores)
        
        # Record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sentiment_snapshots "
                "(platform, avg_sentiment, sample_size, negative_mentions, total_mentions) "
                "VALUES (?, ?, ?, ?, ?)",
                (platform, avg_sentiment, len(sentiment_scores), 
                 negative_count, len(sentiment_scores))
            )
            conn.commit()
        
        # Check for negative spike
        if avg_sentiment < self.negative_sentiment_threshold and negative_ratio > 0.4:
            return CrisisAlert(
                crisis_type=CrisisType.NEGATIVE_SENTIMENT_SPIKE,
                level=CrisisLevel.WARNING,
                message=f"Negative sentiment spike on {platform} "
                       f"(avg: {avg_sentiment:.2f}, {negative_ratio:.0%} negative)",
                detected_at=datetime.now(),
                affected_platforms=[platform],
                recommended_action="reduce_posting",
                metadata={
                    'avg_sentiment': avg_sentiment,
                    'negative_ratio': negative_ratio,
                    'sample_size': len(sentiment_scores)
                }
            )
        
        return None
    
    def handle_crisis(self, alert: CrisisAlert) -> bool:
        """Handle a detected crisis"""
        crisis_id = f"{alert.crisis_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store crisis event
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO crisis_events "
                "(crisis_type, level, message, affected_platforms, triggered_pause, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (alert.crisis_type.value, alert.level.value, alert.message,
                 json.dumps(alert.affected_platforms),
                 alert.recommended_action in ['pause_posting', 'global_pause'],
                 json.dumps(alert.metadata) if alert.metadata else None)
            )
            conn.commit()
        
        # Take action based on level
        if alert.level in [CrisisLevel.CRITICAL, CrisisLevel.EMERGENCY]:
            if alert.recommended_action == 'global_pause':
                self.global_pause = True
                print(f"🚨 GLOBAL PAUSE ACTIVATED: {alert.message}")
            elif alert.affected_platforms:
                for platform in alert.affected_platforms:
                    self.paused_platforms.add(platform)
                print(f"🚨 PAUSED {', '.join(alert.affected_platforms)}: {alert.message}")
        
        elif alert.level == CrisisLevel.WARNING:
            print(f"⚠️  WARNING: {alert.message}")
            if alert.recommended_action == 'pause_posting':
                for platform in alert.affected_platforms or []:
                    self.paused_platforms.add(platform)
        
        self.active_crises[crisis_id] = alert
        
        return True
    
    def resolve_crisis(self, crisis_id: str) -> bool:
        """Mark a crisis as resolved"""
        if crisis_id not in self.active_crises:
            return False
        
        alert = self.active_crises.pop(crisis_id)
        
        # Resume platforms if appropriate
        if alert.level in [CrisisLevel.CRITICAL, CrisisLevel.EMERGENCY]:
            if alert.recommended_action == 'global_pause':
                self.global_pause = False
                print(f"✅ Global posting resumed (crisis resolved)")
            elif alert.affected_platforms:
                for platform in alert.affected_platforms:
                    self.paused_platforms.discard(platform)
                print(f"✅ {', '.join(alert.affected_platforms)} posting resumed")
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE crisis_events SET resolved_at = ?, duration_minutes = ? "
                "WHERE crisis_type = ? AND detected_at = ?",
                (datetime.now().isoformat(),
                 (datetime.now() - alert.detected_at).total_seconds() / 60,
                 alert.crisis_type.value,
                 alert.detected_at.isoformat())
            )
            conn.commit()
        
        return True
    
    def is_posting_allowed(self, platform: str = None) -> Tuple[bool, str]:
        """Check if posting is currently allowed"""
        if self.global_pause:
            return False, "Global pause active due to crisis"
        
        if platform and platform in self.paused_platforms:
            return False, f"Posting paused on {platform} due to crisis"
        
        return True, "Posting allowed"
    
    def manual_pause(self, platform: str = None, reason: str = "manual") -> bool:
        """Manually pause posting"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO pause_history (platform, reason, manual) VALUES (?, ?, 1)",
                (platform, reason)
            )
            conn.commit()
        
        if platform:
            self.paused_platforms.add(platform)
            print(f"⏸️  Manually paused {platform}: {reason}")
        else:
            self.global_pause = True
            print(f"⏸️  Manually paused all platforms: {reason}")
        
        return True
    
    def manual_resume(self, platform: str = None) -> bool:
        """Manually resume posting"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE pause_history SET resumed_at = ? "
                "WHERE platform = ? AND resumed_at IS NULL",
                (datetime.now().isoformat(), platform)
            )
            conn.commit()
        
        if platform:
            self.paused_platforms.discard(platform)
            print(f"▶️  Manually resumed {platform}")
        else:
            self.global_pause = False
            self.paused_platforms.clear()
            print(f"▶️  Manually resumed all platforms")
        
        return True
    
    def get_status(self) -> Dict:
        """Get current crisis and pause status"""
        return {
            'global_pause': self.global_pause,
            'paused_platforms': list(self.paused_platforms),
            'active_crises': len(self.active_crises),
            'crisis_details': [
                {
                    'type': alert.crisis_type.value,
                    'level': alert.level.value,
                    'message': alert.message,
                    'platforms': alert.affected_platforms,
                    'detected': alert.detected_at.isoformat()
                }
                for alert in self.active_crises.values()
            ]
        }
    
    def get_crisis_history(self, hours: int = 168) -> List[Dict]:
        """Get crisis history"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM crisis_events WHERE detected_at > ? "
                    "ORDER BY detected_at DESC",
                    (cutoff.isoformat(),)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting crisis history: {e}")
            return []


class CrisisMonitor:
    """Continuously monitors for crises"""
    
    def __init__(self, detector: CrisisDetector, 
                 health_check_callback=None,
                 sentiment_check_callback=None):
        self.detector = detector
        self.health_check_callback = health_check_callback
        self.sentiment_check_callback = sentiment_check_callback
        self.running = False
    
    async def run(self, check_interval: int = 60):
        """Run continuous crisis monitoring"""
        self.running = True
        print("🛡️  Crisis monitoring started")
        
        while self.running:
            try:
                # API health check
                if self.health_check_callback:
                    health_data = await self.health_check_callback()
                    for platform, data in health_data.items():
                        alert = self.detector.check_api_health(
                            platform,
                            data.get('error_count', 0),
                            data.get('total_requests', 1),
                            data.get('avg_response_time_ms')
                        )
                        if alert:
                            self.detector.handle_crisis(alert)
                
                # Sentiment check
                if self.sentiment_check_callback:
                    sentiment_data = await self.sentiment_check_callback()
                    for platform, scores in sentiment_data.items():
                        alert = self.detector.analyze_sentiment_spike(platform, scores)
                        if alert:
                            self.detector.handle_crisis(alert)
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ Crisis monitor error: {e}")
                await asyncio.sleep(check_interval)
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        print("🛡️  Crisis monitoring stopped")
