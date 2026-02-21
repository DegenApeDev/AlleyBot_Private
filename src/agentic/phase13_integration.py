"""
Phase 13 Integration Mixin
Wires all advanced automation systems into the agentic system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio


class Phase13IntegrationMixin:
    """
    Mixin to add Phase 13 Advanced Automation capabilities
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_phase13()
    
    def _init_phase13(self):
        """Initialize Phase 13 systems"""
        # Smart scheduling
        try:
            from .phase13_scheduling import SmartScheduler, ScheduleRunner
            self.scheduler = SmartScheduler()
            self.schedule_runner = None
        except Exception as e:
            print(f"⚠️ Could not initialize scheduler: {e}")
            self.scheduler = None
        
        # Trend prediction
        try:
            from .phase13_trends import TrendPredictor, TrendMonitor
            self.trend_predictor = TrendPredictor()
            self.trend_monitor = None
        except Exception as e:
            print(f"⚠️ Could not initialize trend predictor: {e}")
            self.trend_predictor = None
        
        # A/B testing
        try:
            from .phase13_ab_testing import ABTestManager, ContentStyler
            self.ab_test_manager = ABTestManager()
            self.content_styler = ContentStyler()
        except Exception as e:
            print(f"⚠️ Could not initialize A/B testing: {e}")
            self.ab_test_manager = None
        
        # Competitor monitoring
        try:
            from .phase13_competitors import CompetitorMonitor, CompetitorAlertSystem
            self.competitor_monitor = CompetitorMonitor()
            self.competitor_alerts = None
        except Exception as e:
            print(f"⚠️ Could not initialize competitor monitor: {e}")
            self.competitor_monitor = None
        
        # Crisis detection
        try:
            from .phase13_crisis import CrisisDetector, CrisisMonitor
            self.crisis_detector = CrisisDetector()
            self.crisis_monitor = None
        except Exception as e:
            print(f"⚠️ Could not initialize crisis detector: {e}")
            self.crisis_detector = None
    
    # Scheduling Methods
    def schedule_content(self, content: str, platform: str,
                        content_type: str = 'post', priority: int = 5,
                        target_time: Optional[datetime] = None) -> Optional[int]:
        """Schedule content for optimal posting time"""
        if not self.scheduler:
            return None
        return self.scheduler.schedule_post(content, platform, content_type, 
                                           priority, target_time)
    
    def get_optimal_posting_times(self, platform: str, limit: int = 5) -> List[Dict]:
        """Get optimal posting times for a platform"""
        if not self.scheduler:
            return []
        slots = self.scheduler.get_optimal_times(platform, limit)
        return [
            {
                'day': s.day_of_week,
                'hour': s.hour,
                'engagement_score': s.engagement_score,
                'confidence': s.confidence
            }
            for s in slots
        ]
    
    def get_scheduled_queue(self, platform: str = None) -> List[Dict]:
        """Get scheduled content queue"""
        if not self.scheduler:
            return []
        return self.scheduler.get_scheduled_posts(platform)
    
    def get_schedule_stats(self) -> Dict:
        """Get scheduling statistics"""
        if not self.scheduler:
            return {'error': 'Scheduler not available'}
        return self.scheduler.get_schedule_stats()
    
    # Trend Prediction Methods
    def predict_trends(self, min_confidence: float = 0.5) -> List[Dict]:
        """Predict trending topics"""
        if not self.trend_predictor:
            return []
        predictions = self.trend_predictor.predict_trends(min_confidence)
        return [
            {
                'topic': p.topic,
                'confidence': p.confidence,
                'predicted_peak': p.predicted_peak.isoformat(),
                'velocity': p.current_velocity,
                'related': p.related_topics,
                'action': p.suggested_action
            }
            for p in predictions
        ]
    
    def record_trend_mention(self, topic: str, platform: str,
                            context: str = None) -> bool:
        """Record a mention for trend analysis"""
        if not self.trend_predictor:
            return False
        return self.trend_predictor.record_mention(topic, platform, context)
    
    def get_trend_report(self, hours: int = 24) -> Dict:
        """Get comprehensive trend report"""
        if not self.trend_predictor:
            return {'error': 'Trend predictor not available'}
        return self.trend_predictor.get_trend_report(hours)
    
    # A/B Testing Methods
    def create_ab_test(self, topic: str, platform: str,
                      variants: List[str] = None,
                      hypothesis: str = None) -> Optional[str]:
        """Create a new A/B test"""
        if not self.ab_test_manager:
            return None
        return self.ab_test_manager.create_test(topic, platform, variants, 
                                                hypothesis=hypothesis)
    
    def get_ab_variant(self, test_id: str) -> Optional[str]:
        """Get variant for next post in test"""
        if not self.ab_test_manager:
            return None
        return self.ab_test_manager.get_variant_for_post(test_id)
    
    def apply_content_style(self, content: str, style: str) -> str:
        """Apply a content style variant"""
        if not self.content_styler:
            return content
        return self.content_styler.apply_style(content, style)
    
    def analyze_ab_test(self, test_id: str) -> Dict:
        """Analyze A/B test results"""
        if not self.ab_test_manager:
            return {'error': 'A/B test manager not available'}
        return self.ab_test_manager.analyze_test(test_id)
    
    def get_ab_insights(self, topic: str = None, platform: str = None) -> List[Dict]:
        """Get learned insights from A/B tests"""
        if not self.ab_test_manager:
            return []
        return self.ab_test_manager.get_insights(topic, platform)
    
    # Competitor Monitoring Methods
    def track_competitor(self, competitor_id: str, platform: str,
                        handle: str = None, category: str = None) -> bool:
        """Add a competitor to track"""
        if not self.competitor_monitor:
            return False
        return self.competitor_monitor.add_competitor(
            competitor_id, platform, handle, category=category
        )
    
    def get_competitor_activity(self, competitor_id: str = None,
                               hours: int = 24) -> List[Dict]:
        """Get competitor activity"""
        if not self.competitor_monitor:
            return []
        return self.competitor_monitor.get_competitor_activity(competitor_id, hours)
    
    def get_competitive_insights(self, platform: str = None) -> List[Dict]:
        """Get competitive insights"""
        if not self.competitor_monitor:
            return []
        return self.competitor_monitor.get_competitive_insights(platform)
    
    def get_tracked_competitors(self) -> List[Dict]:
        """Get list of tracked competitors"""
        if not self.competitor_monitor:
            return []
        return self.competitor_monitor.get_tracked_competitors()
    
    # Crisis Detection Methods
    def check_posting_allowed(self, platform: str = None) -> tuple:
        """Check if posting is allowed"""
        if not self.crisis_detector:
            return True, "Crisis detector not available"
        return self.crisis_detector.is_posting_allowed(platform)
    
    def pause_posting(self, platform: str = None, reason: str = "manual") -> bool:
        """Pause posting"""
        if not self.crisis_detector:
            return False
        return self.crisis_detector.manual_pause(platform, reason)
    
    def resume_posting(self, platform: str = None) -> bool:
        """Resume posting"""
        if not self.crisis_detector:
            return False
        return self.crisis_detector.manual_resume(platform)
    
    def get_crisis_status(self) -> Dict:
        """Get current crisis status"""
        if not self.crisis_detector:
            return {'error': 'Crisis detector not available'}
        return self.crisis_detector.get_status()
    
    def get_crisis_history(self, hours: int = 168) -> List[Dict]:
        """Get crisis history"""
        if not self.crisis_detector:
            return []
        return self.crisis_detector.get_crisis_history(hours)
    
    # Automation Control
    async def start_automation(self):
        """Start all automation systems"""
        print("🚀 Starting Phase 13 automation systems...")
        
        # Start trend monitoring
        if self.trend_predictor:
            from .phase13_trends import TrendMonitor
            self.trend_monitor = TrendMonitor(
                self.trend_predictor,
                alert_callback=self._on_trend_alert
            )
            asyncio.create_task(self.trend_monitor.monitor_loop())
        
        # Start crisis monitoring
        if self.crisis_detector:
            self.crisis_monitor = CrisisMonitor(
                self.crisis_detector,
                health_check_callback=self._check_platform_health,
                sentiment_check_callback=self._check_sentiment
            )
            asyncio.create_task(self.crisis_monitor.run())
        
        print("✅ Phase 13 automation systems active")
    
    async def _on_trend_alert(self, prediction):
        """Handle trend alert"""
        print(f"🔥 Trend Alert: {prediction.topic} ({prediction.confidence:.0%} confidence)")
    
    async def _check_platform_health(self) -> Dict:
        """Check platform health - override in implementation"""
        return {}
    
    async def _check_sentiment(self) -> Dict:
        """Check platform sentiment - override in implementation"""
        return {}
