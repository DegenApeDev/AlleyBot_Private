"""
Phase 12 CLI Commands
Command handlers for Memory & Learning features
"""
from typing import Dict, List, Any
import json


class Phase12CommandsMixin:
    """
    CLI commands for Phase 12 features
    Mix this into AgenticAlleyBot or AlleyBotCore
    """
    
    def memory_prune_command(self, *args) -> str:
        """/memory_prune [max_age_days] [min_relevance] - Run advanced memory pruning"""
        max_age = 30
        min_relevance = 0.3
        
        if args:
            try:
                max_age = int(args[0])
            except ValueError:
                pass
        if len(args) > 1:
            try:
                min_relevance = float(args[1])
            except ValueError:
                pass
        
        if not hasattr(self, 'memory') or not self.memory:
            return "❌ Memory system not available"
        
        print(f"🧹 Running advanced memory pruning (max_age={max_age}d, min_relevance={min_relevance})...")
        stats = self.memory.advanced_prune(max_age, min_relevance)
        
        if 'error' in stats:
            return f"❌ Pruning failed: {stats['error']}"
        
        output = f"✅ Memory pruning complete\n\n"
        
        if 'vector' in stats:
            v = stats['vector']
            output += f"📊 Vector Memories:\n"
            output += f"  Examined: {v.get('examined', 0)}\n"
            output += f"  Removed: {v.get('removed', 0)}\n"
            output += f"  Preserved: {v.get('preserved', 0)}\n"
        
        if 'regular' in stats:
            r = stats['regular']
            output += f"\n📄 Regular Memories:\n"
            output += f"  Examined: {r.get('examined', 0)}\n"
            output += f"  Removed: {r.get('removed', 0)}\n"
        
        if 'goals' in stats:
            output += f"\n🎯 Goals Pruned: {stats['goals']}\n"
        
        return output
    
    def memory_report_command(self, *args) -> str:
        """/memory_report - Get memory pruning and statistics report"""
        if not hasattr(self, 'memory') or not self.memory:
            return "❌ Memory system not available"
        
        # Get memory stats
        stats = self.memory.get_memory_stats()
        
        # Get pruning report
        pruning = self.memory.get_pruning_report()
        
        output = "📊 **Memory System Report**\n\n"
        
        output += f"🗄️  Total Memories: {stats.get('total_memories', 0)}\n"
        output += f"🎯 Active Goals: {stats.get('active_goals', 0)}\n"
        output += f"✅ Completed Goals: {stats.get('completed_goals', 0)}\n"
        output += f"🔐 Sensitive Keys: {stats.get('sensitive_keys', 0)}\n"
        output += f"🔍 Vector DB: {'Enabled' if stats.get('vector_db_enabled') else 'Disabled'}\n"
        
        if stats.get('memory_types'):
            output += f"\n📁 By Type:\n"
            for mem_type, count in stats['memory_types'].items():
                output += f"  {mem_type}: {count}\n"
        
        if 'message' not in pruning:
            output += f"\n🧹 Pruning Activity:\n"
            output += f"  Total Pruned: {pruning.get('total_pruned', 0)}\n"
            output += f"  Recent (7d): {pruning.get('recent_pruned', 0)}\n"
            
            if pruning.get('by_type'):
                output += f"\n  By Type:\n"
                for t, c in pruning['by_type'].items():
                    output += f"    {t}: {c}\n"
        
        return output
    
    def content_strategy_command(self, *args) -> str:
        """/content_strategy - Get AI-generated content strategy based on performance"""
        try:
            from .phase12_learning import Phase12LearningMixin
            learning = Phase12LearningMixin()
            strategy = learning.generate_content_strategy()
        except Exception as e:
            return f"❌ Could not generate strategy: {e}"
        
        output = "📈 **Content Strategy**\n\n"
        
        top = strategy.get('top_topics', [])
        if top:
            output += "🔥 **Top Performing Topics:**\n"
            for t in top[:5]:
                output += f"  • {t['topic']}: {t['avg_engagement']} avg engagement\n"
        
        rising = strategy.get('rising_topics', [])
        if rising:
            output += f"\n📈 **Rising Topics:**\n"
            for t in rising:
                output += f"  • {t}\n"
        
        falling = strategy.get('falling_topics', [])
        if falling:
            output += f"\n📉 **Falling Topics:**\n"
            for t in falling:
                output += f"  • {t}\n"
        
        recs = strategy.get('recommendations', [])
        if recs:
            output += f"\n💡 **Recommendations:**\n"
            for r in recs:
                output += f"  → {r}\n"
        
        return output
    
    def topic_performance_command(self, *args) -> str:
        """/topic_performance [days] - Show topic performance over time"""
        days = 30
        if args:
            try:
                days = int(args[0])
            except ValueError:
                pass
        
        try:
            from .phase12_learning import Phase12LearningMixin
            learning = Phase12LearningMixin()
            topics = learning.get_top_topics(limit=10, days=days)
        except Exception as e:
            return f"❌ Could not get topic performance: {e}"
        
        if not topics:
            return "📭 No topic performance data available"
        
        output = f"📊 **Topic Performance (last {days} days)**\n\n"
        output += f"{'Rank':<6}{'Topic':<25}{'Posts':<8}{'Avg Eng':<10}{'Best':<8}\n"
        output += "-" * 60 + "\n"
        
        for i, t in enumerate(topics, 1):
            topic_name = t['topic'][:23] + ".." if len(t['topic']) > 25 else t['topic']
            output += f"{i:<6}{topic_name:<25}{t['post_count']:<8}{t['avg_engagement']:<10}{t['best_score']:<8}\n"
        
        return output
    
    def community_command(self, *args) -> str:
        """/community [days] - Show active community members"""
        days = 7
        if args:
            try:
                days = int(args[0])
            except ValueError:
                pass
        
        try:
            from .phase12_learning import Phase12LearningMixin
            learning = Phase12LearningMixin()
            
            # Get summary
            summary = learning.get_relationship_summary()
            
            # Get active users
            users = learning.get_active_community_members(days=days)
        except Exception as e:
            return f"❌ Could not get community data: {e}"
        
        output = f"👥 **Community Overview**\n\n"
        output += f"📊 Tracked Users: {summary.get('total_tracked_users', 0)}\n"
        output += f"🌟 Highly Engaged: {summary.get('highly_engaged', 0)}\n"
        
        sentiments = summary.get('sentiment_distribution', {})
        if sentiments:
            output += f"💭 Sentiment: "
            for s, c in sentiments.items():
                output += f"{s}:{c} "
            output += "\n"
        
        if users:
            output += f"\n🔥 **Most Active (last {days} days):**\n"
            for u in users[:10]:
                name = u.get('username') or u['user_id'][:8]
                count = u.get('interaction_count', 0)
                sentiment = u.get('sentiment_trend', '?')
                output += f"  • @{name}: {count} interactions ({sentiment})\n"
        
        return output
    
    def user_profile_command(self, *args) -> str:
        """/user_profile <user_id> - Show detailed user profile"""
        if not args:
            return "Usage: /user_profile <user_id>"
        
        user_id = args[0]
        
        try:
            from .phase12_learning import Phase12LearningMixin
            learning = Phase12LearningMixin()
            profile = learning.get_user_profile(user_id)
        except Exception as e:
            return f"❌ Could not get user profile: {e}"
        
        if not profile:
            return f"📭 No profile found for user {user_id}"
        
        output = f"👤 **User Profile: {profile.get('username', user_id)}**\n\n"
        output += f"🆔 ID: {profile['user_id']}\n"
        output += f"📱 Platform: {profile.get('platform', 'N/A')}\n"
        output += f"📊 Interactions: {profile.get('interaction_count', 0)}\n"
        output += f"💭 Sentiment: {profile.get('sentiment_trend', 'neutral')}\n"
        
        first_seen = profile.get('first_interaction', 'Unknown')
        if first_seen and first_seen != 'Unknown':
            output += f"📅 First Seen: {first_seen[:10]}\n"
        
        prefs = profile.get('preferred_topics', [])
        if prefs:
            output += f"\n❤️ **Interests:** {', '.join(prefs[:5])}\n"
        
        notes = profile.get('notes', '')
        if notes:
            output += f"\n📝 **Notes:** {notes}\n"
        
        recent = profile.get('recent_interactions', [])
        if recent:
            output += f"\n📜 **Recent Activity:**\n"
            for r in recent[:5]:
                t = r.get('timestamp', '')[11:16]  # HH:MM
                typ = r.get('interaction_type', '?')
                output += f"  [{t}] {typ}\n"
        
        return output
    
    def goals_persist_command(self, *args) -> str:
        """/goals_persist - Verify goals are persisted and show status (Phase 12.4)"""
        if not hasattr(self, 'memory') or not self.memory:
            return "❌ Memory system not available"
        
        goals = self.memory.get_active_goals()
        
        output = "🎯 **Goal Persistence Status (Phase 12.4)**\n\n"
        output += f"✅ Goals are automatically persisted across sessions\n"
        output += f"📁 Storage: data/memory/goals.json\n\n"
        output += f"**Active Goals ({len(goals)}):**\n"
        
        for g in goals[:10]:
            progress = g.get('progress', 0) * 100
            pbar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
            output += f"  [{pbar}] {progress:.0f}% - {g['description'][:50]}\n"
        
        if len(goals) > 10:
            output += f"  ... and {len(goals) - 10} more\n"
        
        return output
