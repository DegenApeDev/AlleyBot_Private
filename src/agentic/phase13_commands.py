"""
Phase 13 CLI Commands
Command handlers for Advanced Automation features
"""
from typing import Dict, List, Any
import json
from datetime import datetime


class Phase13CommandsMixin:
    """
    CLI commands for Phase 13 features
    """
    
    # Scheduling Commands
    def schedule_command(self, *args) -> str:
        """/schedule <platform> <content> [priority] - Schedule content for optimal time"""
        if len(args) < 2:
            return "Usage: /schedule <platform> <content> [priority 1-10]"
        
        platform = args[0]
        content = args[1]
        priority = 5
        
        if len(args) > 2:
            try:
                priority = int(args[2])
            except ValueError:
                pass
        
        if not hasattr(self, 'schedule_content'):
            return "❌ Scheduling system not available"
        
        post_id = self.schedule_content(content, platform, priority=priority)
        
        if post_id:
            return f"✅ Scheduled post #{post_id} for optimal time on {platform}"
        return "❌ Failed to schedule post"
    
    def schedule_queue_command(self, *args) -> str:
        """/schedule_queue [platform] - Show scheduled content queue"""
        platform = args[0] if args else None
        
        if not hasattr(self, 'get_scheduled_queue'):
            return "❌ Scheduling system not available"
        
        posts = self.get_scheduled_queue(platform)
        
        if not posts:
            return f"📭 No scheduled posts{' for ' + platform if platform else ''}"
        
        output = f"📅 **Scheduled Posts** ({len(posts)} total)\n\n"
        
        for post in posts[:10]:
            time_str = post.get('optimal_time', 'Unknown')
            if time_str and time_str != 'Unknown':
                time_str = time_str[11:16]  # Extract HH:MM
            pred = post.get('engagement_prediction', 0)
            output += f"  [{time_str}] {post['platform']} - "
            output += f"pred: {pred:.0f} pts\n"
        
        if len(posts) > 10:
            output += f"\n... and {len(posts) - 10} more"
        
        return output
    
    def optimal_times_command(self, *args) -> str:
        """/optimal_times <platform> - Show best posting times"""
        if not args:
            return "Usage: /optimal_times <platform>"
        
        platform = args[0]
        
        if not hasattr(self, 'get_optimal_posting_times'):
            return "❌ Scheduling system not available"
        
        slots = self.get_optimal_posting_times(platform)
        
        if not slots:
            return f"📭 No data yet for {platform}. Post some content to build analytics."
        
        output = f"🕐 **Optimal Posting Times for {platform}**\n\n"
        output += f"{'Rank':<6}{'Day':<12}{'Hour':<8}{'Score':<10}{'Confidence'}\n"
        output += "-" * 50 + "\n"
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i, slot in enumerate(slots, 1):
            day = days[slot['day']]
            hour = f"{slot['hour']:02d}:00"
            score = f"{slot['engagement_score']:.1f}"
            conf = f"{slot['confidence']:.0%}"
            output += f"{i:<6}{day:<12}{hour:<8}{score:<10}{conf}\n"
        
        return output
    
    def schedule_stats_command(self, *args) -> str:
        """/schedule_stats - Show scheduling statistics"""
        if not hasattr(self, 'get_schedule_stats'):
            return "❌ Scheduling system not available"
        
        stats = self.get_schedule_stats()
        
        if 'error' in stats:
            return f"❌ {stats['error']}"
        
        output = "📊 **Scheduling Statistics**\n\n"
        
        pending = stats.get('pending_by_platform', {})
        if pending:
            output += "📅 Pending by Platform:\n"
            for platform, data in pending.items():
                output += f"  • {platform}: {data['count']} posts "
                output += f"(avg pred: {data['avg_prediction']:.1f})\n"
        
        by_status = stats.get('by_status', {})
        if by_status:
            output += f"\n📋 By Status:\n"
            for status, count in by_status.items():
                output += f"  • {status}: {count}\n"
        
        return output
    
    # Trend Commands
    def trends_command(self, *args) -> str:
        """/trends [min_confidence] - Predict trending topics"""
        min_conf = 0.5
        if args:
            try:
                min_conf = float(args[0])
            except ValueError:
                pass
        
        if not hasattr(self, 'predict_trends'):
            return "❌ Trend prediction not available"
        
        predictions = self.predict_trends(min_conf)
        
        if not predictions:
            return f"📭 No trends detected (confidence >= {min_conf:.0%})"
        
        output = f"🔥 **Predicted Trends** (confidence >= {min_conf:.0%})\n\n"
        output += f"{'Topic':<25}{'Conf':<8}{'Peak':<12}{'Action'}\n"
        output += "-" * 60 + "\n"
        
        for p in predictions[:10]:
            topic = p['topic'][:23] + ".." if len(p['topic']) > 25 else p['topic']
            conf = f"{p['confidence']:.0%}"
            peak = p['predicted_peak'][11:16] if len(p['predicted_peak']) > 16 else '?'
            action = p['action']
            output += f"{topic:<25}{conf:<8}{peak:<12}{action}\n"
        
        return output
    
    def trend_report_command(self, *args) -> str:
        """/trend_report [hours] - Comprehensive trend analysis"""
        hours = 24
        if args:
            try:
                hours = int(args[0])
            except ValueError:
                pass
        
        if not hasattr(self, 'get_trend_report'):
            return "❌ Trend prediction not available"
        
        report = self.get_trend_report(hours)
        
        output = f"📈 **Trend Report (last {hours}h)**\n\n"
        
        predictions = report.get('current_predictions', [])
        output += f"🔮 Current Predictions: {len(predictions)}\n"
        
        high_conf = report.get('high_confidence_count', 0)
        output += f"🎯 High Confidence (>70%): {high_conf}\n"
        
        detections = report.get('recent_detections', [])
        output += f"\n📊 Recent Detections: {len(detections)}\n"
        
        return output
    
    # A/B Testing Commands
    def ab_test_command(self, *args) -> str:
        """/ab_test <topic> <platform> [variant1,variant2,...] - Create A/B test"""
        if len(args) < 2:
            return "Usage: /ab_test <topic> <platform> [variants: short,detailed,question]"
        
        topic = args[0]
        platform = args[1]
        variants = None
        
        if len(args) > 2:
            variants = args[2].split(',')
        
        if not hasattr(self, 'create_ab_test'):
            return "❌ A/B testing not available"
        
        test_id = self.create_ab_test(topic, platform, variants)
        
        if test_id:
            return f"🧪 Created A/B test: {test_id}\nTopic: {topic} | Platform: {platform}"
        return "❌ Failed to create test"
    
    def ab_analyze_command(self, *args) -> str:
        """/ab_analyze <test_id> - Analyze A/B test results"""
        if not args:
            return "Usage: /ab_analyze <test_id>"
        
        test_id = args[0]
        
        if not hasattr(self, 'analyze_ab_test'):
            return "❌ A/B testing not available"
        
        result = self.analyze_ab_test(test_id)
        
        if 'error' in result:
            return f"❌ {result['error']}"
        
        if result.get('status') == 'insufficient_data':
            output = f"⏳ Test {test_id}: Insufficient data\n"
            output += f"   Samples: {result['samples_collected']}/{result['min_required']}\n"
            return output
        
        output = f"🧪 **A/B Test Results: {test_id}**\n\n"
        output += f"🏆 Winner: {result['winner']}\n"
        output += f"📊 Confidence: {result['confidence']:.0%}\n"
        output += f"📈 Win Margin: {result['win_margin_percent']:.1f}%\n"
        output += f"📝 Total Samples: {result['sample_size']}\n\n"
        
        results = result.get('results', [])
        if results:
            output += "**Variant Performance:**\n"
            for r in results:
                winner = "👑 " if r.get('winner') else "   "
                output += f"{winner}{r['variant']}: {r['avg_engagement']:.1f} avg engagement "
                output += f"({r['posts_count']} posts)\n"
        
        return output
    
    def ab_insights_command(self, *args) -> str:
        """/ab_insights [topic] [platform] - Get learned A/B test insights"""
        topic = args[0] if args else None
        platform = args[1] if len(args) > 1 else None
        
        if not hasattr(self, 'get_ab_insights'):
            return "❌ A/B testing not available"
        
        insights = self.get_ab_insights(topic, platform)
        
        if not insights:
            return "📭 No A/B test insights available yet"
        
        output = "💡 **Learned Content Insights**\n\n"
        
        for i in insight[:5]:
            output += f"🎯 **{i['topic_pattern'] or 'General'}** on {i['platform']}\n"
            output += f"   Winner: {i['winning_variant']}\n"
            output += f"   Margin: {i['win_margin']:.1f}% | Confidence: {i['confidence']:.0%}\n"
            output += f"   Samples: {i['sample_size']}\n\n"
        
        return output
    
    # Competitor Commands
    def track_competitor_command(self, *args) -> str:
        """/track_competitor <id> <platform> [handle] [category] - Add competitor"""
        if len(args) < 2:
            return "Usage: /track_competitor <id> <platform> [handle] [category]"
        
        comp_id = args[0]
        platform = args[1]
        handle = args[2] if len(args) > 2 else None
        category = args[3] if len(args) > 3 else None
        
        if not hasattr(self, 'track_competitor'):
            return "❌ Competitor tracking not available"
        
        if self.track_competitor(comp_id, platform, handle, category):
            return f"👁️  Now tracking competitor: {handle or comp_id} ({category or 'uncategorized'})"
        return "❌ Failed to add competitor"
    
    def competitors_command(self, *args) -> str:
        """/competitors - List tracked competitors"""
        if not hasattr(self, 'get_tracked_competitors'):
            return "❌ Competitor tracking not available"
        
        competitors = self.get_tracked_competitors()
        
        if not competitors:
            return "📭 No competitors tracked. Use /track_competitor to add."
        
        output = f"👁️  **Tracked Competitors** ({len(competitors)})\n\n"
        
        for c in competitors:
            name = c.get('display_name') or c.get('handle') or c['competitor_id']
            cat = c.get('category', 'uncategorized')
            platform = c['platform']
            output += f"  • {name} ({cat}) on {platform}\n"
        
        return output
    
    def competitor_activity_command(self, *args) -> str:
        """/competitor_activity [competitor_id] [hours] - Show competitor activity"""
        comp_id = args[0] if args else None
        hours = 24
        
        if len(args) > 1:
            try:
                hours = int(args[1])
            except ValueError:
                pass
        
        if not hasattr(self, 'get_competitor_activity'):
            return "❌ Competitor tracking not available"
        
        activity = self.get_competitor_activity(comp_id, hours)
        
        if not activity:
            return f"📭 No activity found{' for ' + comp_id if comp_id else ''}"
        
        output = f"📊 **Competitor Activity** (last {hours}h)\n\n"
        output += f"Total posts tracked: {len(activity)}\n\n"
        
        # Group by competitor
        by_comp = {}
        for a in activity:
            cid = a['competitor_id']
            if cid not in by_comp:
                by_comp[cid] = []
            by_comp[cid].append(a)
        
        for cid, posts in list(by_comp.items())[:3]:
            output += f"**{cid}**: {len(posts)} posts\n"
            for p in posts[:3]:
                preview = p['content'][:60] + "..." if len(p['content']) > 60 else p['content']
                eng = (p['likes'] or 0) + (p['replies'] or 0) + (p['reposts'] or 0)
                output += f"  • {preview} ({eng} engagement)\n"
            output += "\n"
        
        return output
    
    def competitive_insights_command(self, *args) -> str:
        """/competitive_insights [platform] - Get competitive intelligence"""
        platform = args[0] if args else None
        
        if not hasattr(self, 'get_competitive_insights'):
            return "❌ Competitor tracking not available"
        
        insights = self.get_competitive_insights(platform)
        
        if not insights:
            return "📭 No competitive insights available"
        
        output = "🕵️ **Competitive Insights**\n\n"
        
        high_eng = [i for i in insights if i.get('alert')]
        if high_eng:
            output += "🔥 **High Engagement Alerts:**\n"
            for i in high_eng:
                output += f"  ⚠️  {i['competitor_id']}: {i['avg_engagement_rate']:.2%}\n"
            output += "\n"
        
        output += "**Recent Activity:**\n"
        for i in insights[:10]:
            output += f"  • {i['competitor_id']}: {i['recent_posts']} posts, "
            output += f"{i['avg_engagement_rate']:.2%} avg engagement\n"
        
        return output
    
    # Crisis Commands
    def pause_command(self, *args) -> str:
        """/pause [platform] [reason] - Pause posting"""
        platform = args[0] if args else None
        reason = args[1] if len(args) > 1 else "manual"
        
        if not hasattr(self, 'pause_posting'):
            return "❌ Crisis system not available"
        
        if self.pause_posting(platform, reason):
            if platform:
                return f"⏸️  Posting paused on {platform}: {reason}"
            return f"⏸️  Posting paused on all platforms: {reason}"
        return "❌ Failed to pause"
    
    def resume_command(self, *args) -> str:
        """/resume [platform] - Resume posting"""
        platform = args[0] if args else None
        
        if not hasattr(self, 'resume_posting'):
            return "❌ Crisis system not available"
        
        if self.resume_posting(platform):
            if platform:
                return f"▶️  Posting resumed on {platform}"
            return f"▶️  Posting resumed on all platforms"
        return "❌ Failed to resume"
    
    def crisis_status_command(self, *args) -> str:
        """/crisis_status - Check crisis detection status"""
        if not hasattr(self, 'get_crisis_status'):
            return "❌ Crisis system not available"
        
        status = self.get_crisis_status()
        
        if 'error' in status:
            return f"❌ {status['error']}"
        
        output = "🛡️  **Crisis Detection Status**\n\n"
        
        if status.get('global_pause'):
            output += "🚨 **GLOBAL PAUSE ACTIVE**\n\n"
        
        if status.get('paused_platforms'):
            output += "⏸️  **Paused Platforms:**\n"
            for p in status['paused_platforms']:
                output += f"  • {p}\n"
            output += "\n"
        
        crises = status.get('crisis_details', [])
        if crises:
            output += f"⚠️  **Active Crises ({len(crises)}):**\n"
            for c in crises:
                output += f"  [{c['level'].upper()}] {c['type']}: {c['message'][:50]}\n"
        else:
            output += "✅ No active crises detected\n"
        
        return output
    
    def posting_check_command(self, *args) -> str:
        """/posting_check [platform] - Check if posting is allowed"""
        platform = args[0] if args else None
        
        if not hasattr(self, 'check_posting_allowed'):
            return "❌ Crisis system not available"
        
        allowed, reason = self.check_posting_allowed(platform)
        
        if allowed:
            return f"✅ Posting allowed{' on ' + platform if platform else ''}: {reason}"
        return f"⛔ Posting blocked{' on ' + platform if platform else ''}: {reason}"
    
    def crisis_history_command(self, *args) -> str:
        """/crisis_history [hours] - Show recent crisis events"""
        hours = 168  # 7 days
        if args:
            try:
                hours = int(args[0])
            except ValueError:
                pass
        
        if not hasattr(self, 'get_crisis_history'):
            return "❌ Crisis system not available"
        
        history = self.get_crisis_history(hours)
        
        if not history:
            return f"📭 No crisis events in last {hours}h"
        
        output = f"📜 **Crisis History (last {hours}h)**\n\n"
        output += f"Total events: {len(history)}\n\n"
        
        for h in history[:10]:
            level = h.get('level', 'unknown')
            ctype = h.get('crisis_type', 'unknown')
            detected = h.get('detected_at', '')
            if detected:
                detected = detected[11:16]  # HH:MM
            
            resolved = '✓' if h.get('resolved_at') else '○'
            output += f"[{resolved}] [{detected}] [{level}] {ctype}\n"
        
        return output
    
    # Automation Control Commands
    def automation_start_command(self, *args) -> str:
        """/automation_start - Start all automation systems"""
        if not hasattr(self, 'start_automation'):
            return "❌ Automation systems not available"
        
        import asyncio
        asyncio.create_task(self.start_automation())
        
        return "🚀 Starting all automation systems...\nUse /automation_status to check."
    
    def automation_status_command(self, *args) -> str:
        """/automation_status - Check automation system status"""
        output = "⚡ **Phase 13 Automation Status**\n\n"
        
        systems = [
            ('Scheduler', hasattr(self, 'scheduler') and self.scheduler),
            ('Trend Predictor', hasattr(self, 'trend_predictor') and self.trend_predictor),
            ('A/B Testing', hasattr(self, 'ab_test_manager') and self.ab_test_manager),
            ('Competitor Monitor', hasattr(self, 'competitor_monitor') and self.competitor_monitor),
            ('Crisis Detector', hasattr(self, 'crisis_detector') and self.crisis_detector)
        ]
        
        for name, active in systems:
            status = "🟢 Active" if active else "🔴 Not Available"
            output += f"  {name}: {status}\n"
        
        return output
