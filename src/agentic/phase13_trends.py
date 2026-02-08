"""
Phase 13.2: Trend Prediction System
Anticipates trending topics before they peak
Uses multi-source signal aggregation
"""
import sqlite3
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class TrendSignal:
    """A signal that a topic might be trending"""
    topic: str
    signal_type: str  # volume, velocity, cross_platform, ai_prediction
    strength: float  # 0-1
    source: str  # Where this signal came from
    timestamp: datetime
    metadata: Optional[Dict] = None


@dataclass
class PredictedTrend:
    """A trend prediction with confidence"""
    topic: str
    confidence: float  # 0-1
    predicted_peak: datetime
    current_velocity: float  # posts per hour
    signals: List[TrendSignal]
    related_topics: List[str]
    suggested_action: str


class TrendPredictor:
    """
    Predicts trending topics using multiple signals:
    - Volume spikes (sudden increase in mentions)
    - Velocity (rate of growth)
    - Cross-platform correlation
    - AI sentiment analysis
    - Historical pattern matching
    """
    
    def __init__(self, db_path: str = 'data/trends.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.min_signal_strength = 0.3
    
    def _init_db(self):
        """Initialize trends database"""
        with sqlite3.connect(self.db_path) as conn:
            # Topic mentions over time
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topic_mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    platform TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    mention_count INTEGER DEFAULT 1,
                    context TEXT,  -- sample of context
                    sentiment REAL  -- -1 to 1 if analyzed
                )
            """)
            
            # Trending topics detected
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detected_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL,
                    status TEXT DEFAULT 'emerging',  -- emerging, peaked, declining, confirmed
                    peak_timestamp TIMESTAMP,
                    actual_peak_confirmed BOOLEAN DEFAULT 0,
                    sources TEXT,  -- JSON array of sources
                    metadata TEXT
                )
            """)
            
            # Historical trends for pattern matching
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trend_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    first_seen TIMESTAMP,
                    peak_timestamp TIMESTAMP,
                    duration_hours REAL,
                    max_velocity REAL,
                    related_topics TEXT,  -- JSON array
                    category TEXT  -- tech, crypto, politics, etc.
                )
            """)
            
            # Cross-platform signals
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    source_platform TEXT NOT NULL,
                    target_platform TEXT,
                    signal_type TEXT,  -- lagged_correlation, simultaneous, leading_indicator
                    correlation_strength REAL,
                    lag_hours REAL,  -- How much target platform lags behind source
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def record_mention(self, topic: str, platform: str,
                      context: str = None, sentiment: float = None) -> bool:
        """Record a topic mention"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO topic_mentions (topic, platform, context, sentiment) "
                    "VALUES (?, ?, ?, ?)",
                    (topic.lower().strip(), platform, context, sentiment)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording mention: {e}")
            return False
    
    def record_mentions_batch(self, mentions: List[Dict]) -> bool:
        """Record multiple mentions efficiently"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for mention in mentions:
                    conn.execute(
                        "INSERT INTO topic_mentions (topic, platform, context, sentiment) "
                        "VALUES (?, ?, ?, ?)",
                        (mention['topic'].lower().strip(), mention.get('platform'),
                         mention.get('context'), mention.get('sentiment'))
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording mentions batch: {e}")
            return False
    
    def analyze_volume_spikes(self, hours: int = 6) -> List[TrendSignal]:
        """Detect topics with sudden volume spikes"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get recent mention counts
                cursor = conn.execute(
                    "SELECT topic, COUNT(*) as count, platform "
                    "FROM topic_mentions WHERE timestamp > ? "
                    "GROUP BY topic, platform ORDER BY count DESC",
                    (cutoff.isoformat(),)
                )
                recent = defaultdict(lambda: defaultdict(int))
                for row in cursor.fetchall():
                    recent[row['topic']][row['platform']] = row['count']
                
                # Get baseline (previous period)
                prev_start = cutoff - timedelta(hours=hours)
                cursor = conn.execute(
                    "SELECT topic, COUNT(*) as count "
                    "FROM topic_mentions WHERE timestamp > ? AND timestamp <= ? "
                    "GROUP BY topic",
                    (prev_start.isoformat(), cutoff.isoformat())
                )
                baseline = {row['topic']: row['count'] for row in cursor.fetchall()}
                
                signals = []
                for topic, platforms in recent.items():
                    recent_total = sum(platforms.values())
                    base_count = baseline.get(topic, 1)  # Min 1 to avoid div by zero
                    
                    # Spike ratio
                    spike_ratio = recent_total / base_count
                    
                    # Minimum threshold: at least 5 mentions and 3x increase
                    if recent_total >= 5 and spike_ratio >= 3:
                        strength = min((spike_ratio - 1) / 9, 1.0)  # Cap at 10x = 1.0
                        
                        signals.append(TrendSignal(
                            topic=topic,
                            signal_type='volume',
                            strength=strength,
                            source='volume_spike',
                            timestamp=datetime.now(),
                            metadata={
                                'recent_count': recent_total,
                                'baseline': base_count,
                                'spike_ratio': spike_ratio,
                                'by_platform': dict(platforms)
                            }
                        ))
                
                return signals
        except Exception as e:
            print(f"⚠️ Error analyzing volume: {e}")
            return []
    
    def analyze_velocity(self, window_hours: int = 3) -> List[TrendSignal]:
        """Detect topics with accelerating growth rate"""
        try:
            now = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                signals = []
                
                # Get all topics with mentions in last window_hours
                cutoff = now - timedelta(hours=window_hours)
                cursor = conn.execute(
                    "SELECT DISTINCT topic FROM topic_mentions WHERE timestamp > ?",
                    (cutoff.isoformat(),)
                )
                topics = [row['topic'] for row in cursor.fetchall()]
                
                for topic in topics:
                    # Get hourly counts
                    cursor = conn.execute(
                        "SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour, COUNT(*) as count "
                        "FROM topic_mentions WHERE topic = ? AND timestamp > ? "
                        "GROUP BY hour ORDER BY hour",
                        (topic, cutoff.isoformat())
                    )
                    hourly = [(row['hour'], row['count']) for row in cursor.fetchall()]
                    
                    if len(hourly) >= 2:
                        # Calculate velocity (change in mentions per hour)
                        counts = [c for _, c in hourly]
                        velocity = sum(counts) / len(counts)
                        
                        # Acceleration (increasing trend)
                        if len(counts) >= 3:
                            # Simple linear regression slope
                            n = len(counts)
                            x = list(range(n))
                            x_mean = sum(x) / n
                            y_mean = sum(counts) / n
                            
                            numerator = sum((x[i] - x_mean) * (counts[i] - y_mean) for i in range(n))
                            denominator = sum((xi - x_mean) ** 2 for xi in x)
                            
                            slope = numerator / denominator if denominator != 0 else 0
                            
                            # Positive slope = accelerating
                            if slope > 0 and velocity > 2:
                                strength = min(slope / 10, 1.0)  # Normalize
                                signals.append(TrendSignal(
                                    topic=topic,
                                    signal_type='velocity',
                                    strength=strength,
                                    source='velocity_analysis',
                                    timestamp=now,
                                    metadata={
                                        'velocity': velocity,
                                        'acceleration': slope,
                                        'hourly_counts': counts
                                    }
                                ))
                
                return signals
        except Exception as e:
            print(f"⚠️ Error analyzing velocity: {e}")
            return []
    
    def analyze_cross_platform(self, hours: int = 6) -> List[TrendSignal]:
        """Detect topics trending on multiple platforms"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute(
                    "SELECT topic, platform, COUNT(*) as count "
                    "FROM topic_mentions WHERE timestamp > ? "
                    "GROUP BY topic, platform",
                    (cutoff.isoformat(),)
                )
                
                topic_platforms = defaultdict(dict)
                for row in cursor.fetchall():
                    topic_platforms[row['topic']][row['platform']] = row['count']
                
                signals = []
                for topic, platforms in topic_platforms.items():
                    # Trending on 2+ platforms is significant
                    if len(platforms) >= 2:
                        total = sum(platforms.values())
                        strength = min(len(platforms) * 0.3 + (total / 50) * 0.2, 1.0)
                        
                        signals.append(TrendSignal(
                            topic=topic,
                            signal_type='cross_platform',
                            strength=strength,
                            source='cross_platform_correlation',
                            timestamp=datetime.now(),
                            metadata={
                                'platforms': platforms,
                                'platform_count': len(platforms)
                            }
                        ))
                
                return signals
        except Exception as e:
            print(f"⚠️ Error analyzing cross-platform: {e}")
            return []
    
    def predict_trends(self, min_confidence: float = 0.5) -> List[PredictedTrend]:
        """Aggregate all signals and predict trends"""
        # Gather all signals
        volume_signals = self.analyze_volume_spikes()
        velocity_signals = self.analyze_velocity()
        cross_platform_signals = self.analyze_cross_platform()
        
        all_signals = volume_signals + velocity_signals + cross_platform_signals
        
        # Group by topic
        topic_signals = defaultdict(list)
        for signal in all_signals:
            topic_signals[signal.topic].append(signal)
        
        predictions = []
        
        for topic, signals in topic_signals.items():
            # Calculate combined confidence
            # More signal types = higher confidence
            # Stronger individual signals = higher confidence
            
            signal_type_bonus = min(len(set(s.signal_type for s in signals)) * 0.1, 0.3)
            avg_strength = sum(s.strength for s in signals) / len(signals)
            
            confidence = (avg_strength * 0.7) + signal_type_bonus
            
            if confidence >= min_confidence:
                # Estimate peak time
                velocity = next((s.metadata.get('velocity', 0) for s in signals 
                                 if s.signal_type == 'velocity'), 0)
                
                # Higher velocity = sooner peak (0.5-48 hours)
                if velocity > 10:
                    hours_to_peak = 0.5
                elif velocity > 5:
                    hours_to_peak = 2
                elif velocity > 2:
                    hours_to_peak = 6
                else:
                    hours_to_peak = 24
                
                predicted_peak = datetime.now() + timedelta(hours=hours_to_peak)
                
                # Find related topics (co-occurring)
                related = self._find_related_topics(topic, signals)
                
                # Suggest action
                action = self._suggest_action(topic, confidence, signals)
                
                predictions.append(PredictedTrend(
                    topic=topic,
                    confidence=confidence,
                    predicted_peak=predicted_peak,
                    current_velocity=velocity,
                    signals=signals,
                    related_topics=related,
                    suggested_action=action
                ))
        
        # Sort by confidence
        predictions.sort(key=lambda x: x.confidence, reverse=True)
        
        return predictions
    
    def _find_related_topics(self, topic: str, signals: List[TrendSignal], 
                           max_related: int = 5) -> List[str]:
        """Find topics that co-occur with this topic"""
        try:
            # Get recent mentions of this topic
            cutoff = datetime.now() - timedelta(hours=6)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT context FROM topic_mentions "
                    "WHERE topic = ? AND timestamp > ? AND context IS NOT NULL",
                    (topic, cutoff.isoformat())
                )
                
                # Extract other topics from context
                all_words = []
                for row in cursor.fetchall():
                    if row[0]:
                        words = re.findall(r'\b[a-z]{4,}\b', row[0].lower())
                        all_words.extend(words)
                
                # Count and filter
                word_counts = Counter(all_words)
                # Remove common stop words and the topic itself
                stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they', 'their'}
                filtered = {w: c for w, c in word_counts.items() 
                           if w not in stop_words and w != topic and c >= 2}
                
                # Return top related
                top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
                return [w for w, _ in top[:max_related]]
        except Exception as e:
            print(f"⚠️ Error finding related topics: {e}")
            return []
    
    def _suggest_action(self, topic: str, confidence: float, 
                       signals: List[TrendSignal]) -> str:
        """Suggest an action based on trend characteristics"""
        has_velocity = any(s.signal_type == 'velocity' for s in signals)
        has_volume = any(s.signal_type == 'volume' for s in signals)
        has_cross = any(s.signal_type == 'cross_platform' for s in signals)
        
        if confidence > 0.8 and has_velocity and has_cross:
            return "immediate_post"  # Post now, this is hot
        elif confidence > 0.7 and has_volume:
            return "prepare_content"  # Draft content to post soon
        elif has_cross:
            return "monitor"  # Watch closely
        else:
            return "track"  # Keep tracking
    
    def record_prediction_accuracy(self, topic: str, 
                                 predicted_peak: datetime,
                                 actual_status: str) -> bool:
        """Record whether a prediction was accurate (for learning)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE detected_trends SET status = ?, actual_peak_confirmed = ? "
                    "WHERE topic = ?",
                    (actual_status, actual_status == 'peaked', topic)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording accuracy: {e}")
            return False
    
    def get_trend_report(self, hours: int = 24) -> Dict:
        """Get a comprehensive trend report"""
        predictions = self.predict_trends(min_confidence=0.4)
        
        # Get recent detections
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM detected_trends WHERE detected_at > ? "
                    "ORDER BY confidence DESC",
                    (cutoff.isoformat(),)
                )
                recent = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            recent = []
        
        return {
            'current_predictions': [
                {
                    'topic': p.topic,
                    'confidence': p.confidence,
                    'predicted_peak': p.predicted_peak.isoformat(),
                    'velocity': p.current_velocity,
                    'related_topics': p.related_topics,
                    'action': p.suggested_action,
                    'signal_count': len(p.signals)
                }
                for p in predictions[:10]
            ],
            'recent_detections': recent,
            'total_signals_analyzed': len(predictions),
            'high_confidence_count': len([p for p in predictions if p.confidence > 0.7])
        }
    
    def extract_topics_from_text(self, text: str, 
                                 min_length: int = 4) -> List[str]:
        """Extract potential topic keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{' + str(min_length) + ',}\b', text)
        
        # Filter for likely topics (nouns, hashtags, etc)
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 
                   'they', 'their', 'about', 'would', 'could', 'should'}
        
        filtered = [w.lower() for w in words if w.lower() not in stop_words]
        
        # Return unique
        return list(set(filtered))


class TrendMonitor:
    """Continuously monitors for trends and triggers alerts"""
    
    def __init__(self, predictor: TrendPredictor, alert_callback=None):
        self.predictor = predictor
        self.alert_callback = alert_callback
        self.monitored_topics: Set[str] = set()
        self.alert_threshold = 0.7
    
    async def monitor_loop(self, interval_minutes: int = 10):
        """Run continuous trend monitoring"""
        import asyncio
        
        print("📈 Trend monitoring started")
        
        while True:
            try:
                predictions = self.predictor.predict_trends(min_confidence=self.alert_threshold)
                
                for pred in predictions:
                    # Check if this is a new high-confidence prediction
                    if pred.topic not in self.monitored_topics:
                        self.monitored_topics.add(pred.topic)
                        
                        if self.alert_callback:
                            await self.alert_callback(pred)
                        
                        print(f"🔥 High-confidence trend detected: {pred.topic} "
                              f"({pred.confidence:.2f} confidence)")
                
                # Clean up old monitored topics
                cutoff = datetime.now() - timedelta(hours=48)
                with sqlite3.connect(self.predictor.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT DISTINCT topic FROM detected_trends "
                        "WHERE detected_at > ?",
                        (cutoff.isoformat(),)
                    )
                    active = {row[0] for row in cursor.fetchall()}
                    self.monitored_topics = self.monitored_topics & active
                
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"⚠️ Trend monitor error: {e}")
                await asyncio.sleep(interval_minutes * 60)
