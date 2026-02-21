"""
Phase 13.3: Automated A/B Testing System
Tries different content styles and measures performance
"""
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import random


class ContentVariant(Enum):
    """Different content style variants to test"""
    SHORT_CONCISE = "short_concise"  # Brief, punchy
    DETAILED = "detailed"  # Longer, more context
    QUESTION = "question"  # Ends with question
    HOOK = "hook"  # Attention-grabbing opening
    STORY = "story"  # Narrative style
    DATA_DRIVEN = "data_driven"  # Statistics/facts
    EMOTIONAL = "emotional"  # Appeals to emotion
    PROFESSIONAL = "professional"  # Formal tone


@dataclass
class TestResult:
    """Results from an A/B test"""
    variant: str
    posts_count: int
    avg_engagement: float
    avg_likes: float
    avg_replies: float
    avg_reposts: float
    click_through_rate: Optional[float] = None
    conversion_rate: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    winner: bool = False


class ABTestManager:
    """
    Manages automated A/B testing of content
    Tests different styles and measures performance
    """
    
    def __init__(self, db_path: str = 'data/ab_tests.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.active_tests: Dict[str, 'ABTest'] = {}
    
    def _init_db(self):
        """Initialize A/B testing database"""
        with sqlite3.connect(self.db_path) as conn:
            # Active and completed tests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE NOT NULL,
                    test_name TEXT,
                    topic TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT DEFAULT 'running',  -- running, paused, completed
                    hypothesis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    winner_variant TEXT,
                    confidence_level REAL,
                    sample_size INTEGER DEFAULT 0,
                    variants TEXT  -- JSON array of variant names
                )
            """)
            
            # Individual posts in tests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    content_hash TEXT,  -- For deduplication
                    content_preview TEXT,
                    posted_at TIMESTAMP,
                    platform_post_id TEXT,  -- External ID
                    status TEXT DEFAULT 'pending',  -- pending, posted, measuring, complete
                    engagement_data TEXT  -- JSON
                )
            """)
            
            # Variant performance metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS variant_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    posts_count INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_replies INTEGER DEFAULT 0,
                    total_reposts INTEGER DEFAULT 0,
                    total_impressions INTEGER DEFAULT 0,
                    total_clicks INTEGER DEFAULT 0,
                    avg_engagement_score REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(test_id, variant)
                )
            """)
            
            # Learned insights from tests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_pattern TEXT,  -- e.g., "crypto", "tech", "general"
                    platform TEXT,
                    winning_variant TEXT,
                    win_margin REAL,  -- How much better (%)
                    confidence REAL,
                    sample_size INTEGER,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    times_applied INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def create_test(self, topic: str, platform: str,
                   variants: List[str] = None,
                   test_name: str = None,
                   hypothesis: str = None) -> Optional[str]:
        """Create a new A/B test"""
        try:
            test_id = hashlib.md5(f"{topic}_{platform}_{datetime.now()}".encode()).hexdigest()[:12]
            
            # Default variants if not specified
            if variants is None:
                variants = [ContentVariant.SHORT_CONCISE.value, 
                          ContentVariant.DETAILED.value,
                          ContentVariant.QUESTION.value]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO ab_tests (test_id, test_name, topic, platform, "
                    "hypothesis, variants, started_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (test_id, test_name or f"Test: {topic}", topic, platform,
                     hypothesis, json.dumps(variants), datetime.now().isoformat())
                )
                conn.commit()
            
            print(f"🧪 Created A/B test {test_id}: {topic} on {platform}")
            print(f"   Variants: {', '.join(variants)}")
            
            return test_id
        except Exception as e:
            print(f"⚠️ Error creating test: {e}")
            return None
    
    def get_variant_for_post(self, test_id: str) -> Optional[str]:
        """Get which variant to use for the next post"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get test info
                cursor = conn.execute(
                    "SELECT variants FROM ab_tests WHERE test_id = ? AND status = 'running'",
                    (test_id,)
                )
                result = cursor.fetchone()
                if not result:
                    return None
                
                variants = json.loads(result[0])
                
                # Get current distribution
                cursor = conn.execute(
                    "SELECT variant, COUNT(*) as count FROM test_posts "
                    "WHERE test_id = ? GROUP BY variant",
                    (test_id,)
                )
                counts = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Find least used variant for balanced test
                min_count = min(counts.get(v, 0) for v in variants)
                candidates = [v for v in variants if counts.get(v, 0) == min_count]
                
                return random.choice(candidates)
        except Exception as e:
            print(f"⚠️ Error getting variant: {e}")
            return None
    
    def record_post(self, test_id: str, variant: str, content: str,
                   platform_post_id: str = None) -> bool:
        """Record a post as part of a test"""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
            preview = content[:100] + "..." if len(content) > 100 else content
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO test_posts (test_id, variant, content_hash, "
                    "content_preview, posted_at, platform_post_id, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (test_id, variant, content_hash, preview,
                     datetime.now().isoformat(), platform_post_id, 'posted')
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording post: {e}")
            return False
    
    def record_engagement(self, test_id: str, platform_post_id: str,
                         engagement: Dict[str, int]) -> bool:
        """Record engagement for a test post"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get variant for this post
                cursor = conn.execute(
                    "SELECT variant FROM test_posts WHERE test_id = ? AND platform_post_id = ?",
                    (test_id, platform_post_id)
                )
                result = cursor.fetchone()
                if not result:
                    return False
                
                variant = result[0]
                
                # Update test post
                conn.execute(
                    "UPDATE test_posts SET engagement_data = ?, status = 'complete' "
                    "WHERE test_id = ? AND platform_post_id = ?",
                    (json.dumps(engagement), test_id, platform_post_id)
                )
                
                # Update aggregate performance
                likes = engagement.get('likes', 0)
                replies = engagement.get('replies', 0)
                reposts = engagement.get('reposts', 0)
                impressions = engagement.get('impressions', 0)
                clicks = engagement.get('clicks', 0)
                
                # Calculate engagement score (weighted sum)
                score = likes + (replies * 2) + (reposts * 3)
                
                cursor = conn.execute(
                    "SELECT * FROM variant_performance WHERE test_id = ? AND variant = ?",
                    (test_id, variant)
                )
                if cursor.fetchone():
                    conn.execute(
                        "UPDATE variant_performance SET "
                        "posts_count = posts_count + 1, "
                        "total_likes = total_likes + ?, "
                        "total_replies = total_replies + ?, "
                        "total_reposts = total_reposts + ?, "
                        "total_impressions = total_impressions + ?, "
                        "total_clicks = total_clicks + ?, "
                        "avg_engagement_score = (avg_engagement_score * posts_count + ?) / (posts_count + 1), "
                        "last_updated = ? "
                        "WHERE test_id = ? AND variant = ?",
                        (likes, replies, reposts, impressions, clicks, score,
                         datetime.now().isoformat(), test_id, variant)
                    )
                else:
                    conn.execute(
                        "INSERT INTO variant_performance "
                        "(test_id, variant, posts_count, total_likes, total_replies, "
                        "total_reposts, total_impressions, total_clicks, avg_engagement_score) "
                        "VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)",
                        (test_id, variant, likes, replies, reposts, impressions, clicks, score)
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording engagement: {e}")
            return False
    
    def analyze_test(self, test_id: str, min_samples: int = 10) -> Dict:
        """Analyze test results and determine winner"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get variant performance
                cursor = conn.execute(
                    "SELECT * FROM variant_performance WHERE test_id = ?",
                    (test_id,)
                )
                variants = [dict(row) for row in cursor.fetchall()]
                
                if len(variants) < 2:
                    return {'error': 'Need at least 2 variants with data'}
                
                # Check sample size
                total_samples = sum(v['posts_count'] for v in variants)
                if total_samples < min_samples:
                    return {
                        'status': 'insufficient_data',
                        'samples_collected': total_samples,
                        'min_required': min_samples,
                        'progress': variants
                    }
                
                # Find best performer
                best = max(variants, key=lambda x: x['avg_engagement_score'])
                baseline = min(variants, key=lambda x: x['avg_engagement_score'])
                
                # Calculate margin
                if baseline['avg_engagement_score'] > 0:
                    margin = ((best['avg_engagement_score'] - baseline['avg_engagement_score']) 
                             / baseline['avg_engagement_score'] * 100)
                else:
                    margin = 100  # Can't calculate %, but best is clearly better
                
                # Simple confidence calculation (would use proper statistical test in production)
                confidence = min(best['posts_count'] / 30, 1.0) * 0.8 + 0.2
                
                results = []
                for v in variants:
                    ctr = (v['total_clicks'] / v['total_impressions'] * 100) if v['total_impressions'] > 0 else 0
                    
                    results.append(TestResult(
                        variant=v['variant'],
                        posts_count=v['posts_count'],
                        avg_engagement=v['avg_engagement_score'],
                        avg_likes=v['total_likes'] / v['posts_count'],
                        avg_replies=v['total_replies'] / v['posts_count'],
                        avg_reposts=v['total_reposts'] / v['posts_count'],
                        click_through_rate=ctr,
                        winner=(v['variant'] == best['variant'])
                    ))
                
                # Update test status
                conn.execute(
                    "UPDATE ab_tests SET status = 'completed', ended_at = ?, "
                    "winner_variant = ?, confidence_level = ?, sample_size = ? "
                    "WHERE test_id = ?",
                    (datetime.now().isoformat(), best['variant'], confidence,
                     total_samples, test_id)
                )
                conn.commit()
                
                return {
                    'status': 'completed',
                    'winner': best['variant'],
                    'confidence': confidence,
                    'win_margin_percent': margin,
                    'sample_size': total_samples,
                    'results': [asdict(r) for r in results]
                }
        except Exception as e:
            print(f"⚠️ Error analyzing test: {e}")
            return {'error': str(e)}
    
    def get_insights(self, topic_pattern: str = None, 
                    platform: str = None) -> List[Dict]:
        """Get learned insights from completed tests"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if topic_pattern and platform:
                    cursor = conn.execute(
                        "SELECT * FROM ab_insights WHERE topic_pattern = ? AND platform = ? "
                        "ORDER BY confidence DESC, discovered_at DESC",
                        (topic_pattern, platform)
                    )
                elif topic_pattern:
                    cursor = conn.execute(
                        "SELECT * FROM ab_insights WHERE topic_pattern = ? "
                        "ORDER BY confidence DESC, discovered_at DESC",
                        (topic_pattern,)
                    )
                elif platform:
                    cursor = conn.execute(
                        "SELECT * FROM ab_insights WHERE platform = ? "
                        "ORDER BY confidence DESC, discovered_at DESC",
                        (platform,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM ab_insights ORDER BY confidence DESC, discovered_at DESC"
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting insights: {e}")
            return []
    
    def apply_learned_style(self, topic: str, platform: str,
                           content_generator_fn) -> str:
        """
        Use learned insights to generate optimally-styled content
        content_generator_fn should accept a style parameter
        """
        insights = self.get_insights(topic, platform)
        
        if insights:
            best = insights[0]
            winning_variant = best['winning_variant']
            print(f"🎯 Using learned style '{winning_variant}' for {topic} on {platform} "
                  f"({best['confidence']:.0%} confidence)")
            
            return content_generator_fn(winning_variant)
        
        # No insights, use default
        return content_generator_fn(ContentVariant.SHORT_CONCISE.value)
    
    def get_active_tests(self) -> List[Dict]:
        """Get all active tests"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM ab_tests WHERE status = 'running' "
                    "ORDER BY started_at DESC"
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting active tests: {e}")
            return []
    
    def get_test_report(self, test_id: str = None) -> Dict:
        """Get comprehensive test report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if test_id:
                    cursor = conn.execute(
                        "SELECT * FROM ab_tests WHERE test_id = ?", (test_id,)
                    )
                    test = dict(cursor.fetchone())
                    
                    cursor = conn.execute(
                        "SELECT * FROM variant_performance WHERE test_id = ?",
                        (test_id,)
                    )
                    variants = [dict(row) for row in cursor.fetchall()]
                    
                    return {'test': test, 'variants': variants}
                else:
                    # Summary report
                    cursor = conn.execute(
                        "SELECT status, COUNT(*) as count FROM ab_tests GROUP BY status"
                    )
                    by_status = {row['status']: row['count'] for row in cursor.fetchall()}
                    
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM ab_insights"
                    )
                    insights_count = cursor.fetchone()[0]
                    
                    return {
                        'tests_by_status': by_status,
                        'total_insights': insights_count,
                        'recent_insights': self.get_insights()[:5]
                    }
        except Exception as e:
            print(f"⚠️ Error getting report: {e}")
            return {'error': str(e)}


class ContentStyler:
    """Applies different content styles for A/B testing"""
    
    @staticmethod
    def apply_style(content: str, style: str) -> str:
        """Apply a style variant to content"""
        
        if style == ContentVariant.SHORT_CONCISE.value:
            # Truncate to 2-3 sentences, punchy
            sentences = content.split('. ')
            if len(sentences) > 3:
                return '. '.join(sentences[:3]) + '.'
            return content
        
        elif style == ContentVariant.QUESTION.value:
            # Add engaging question at end
            questions = [
                "What do you think?",
                "Agree or disagree?",
                "Have you seen this before?",
                "What's your take?",
                "Thoughts?"
            ]
            return content + f"\n\n{random.choice(questions)}"
        
        elif style == ContentVariant.HOOK.value:
            # Add attention-grabbing opener
            hooks = [
                "🔥 Hot take: ",
                "🚨 Important: ",
                "💡 Did you know? ",
                "⚡ Breaking: ",
                "🎯 Key insight: "
            ]
            return random.choice(hooks) + content
        
        elif style == ContentVariant.DATA_DRIVEN.value:
            # Add data framing
            return "📊 Based on the data:\n\n" + content
        
        elif style == ContentVariant.EMOTIONAL.value:
            # Add emotional framing
            return "This matters because it affects all of us.\n\n" + content
        
        # Default: return as-is
        return content
    
    @staticmethod
    def get_available_styles() -> List[str]:
        """Get list of available style variants"""
        return [v.value for v in ContentVariant]
