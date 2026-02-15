"""
Telegram Commands for World State Intelligence (Phase 7)

Provides /trends, /influencers, /predict, /anomalies, /sentiment, /patterns
for owner to access world state intelligence.

Part of AGI Core - Phase 7
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.autonomy.inference_engine import get_inference_engine, InferenceEngine

logger = logging.getLogger(__name__)


class IntelligenceCommands:
    """Telegram commands for world state intelligence"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._inference_engine = None
    
    def _get_inference_engine(self):
        if self._inference_engine is None:
            self._inference_engine = get_inference_engine()
        return self._inference_engine
    
    def _is_owner(self, update: Update) -> bool:
        user_id = str(update.effective_user.id)
        owner_id = None
        
        core = getattr(self.telegram, 'core', None)
        if core and hasattr(core, 'config'):
            owner_id = core.config.get('TELEGRAM_ADMIN_CHAT_ID')
        
        if not owner_id:
            import os
            owner_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        return user_id == str(owner_id)
    
    async def trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show current trending topics.
        
        Usage: /trends [hours] [limit]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 24
        limit = 10
        
        if context.args:
            try:
                hours = int(context.args[0])
                if len(context.args) > 1:
                    limit = int(context.args[1])
            except ValueError:
                pass
        
        try:
            engine = self._get_inference_engine()
            trends = engine.detect_trends(hours=hours, top_n=limit)
            
            if not trends:
                await update.message.reply_text("📊 No significant trends detected")
                return
            
            msg = f"📈 **Trending Topics (Last {hours}h)**\n\n"
            
            for i, trend in enumerate(trends, 1):
                # Direction emoji
                direction_emoji = {
                    'rising': '🚀',
                    'falling': '📉',
                    'stable': '➡️',
                    'volatile': '📊'
                }.get(trend.direction, '📊')
                
                # Strength bars
                bars = '█' * int(trend.strength * 10)
                
                msg += f"{i}. {direction_emoji} **{trend.topic}**\n"
                msg += f"   {bars} {trend.strength:.0%}\n"
                msg += f"   Direction: {trend.direction} | Velocity: {trend.velocity:.2f}/h\n"
                
                if trend.predicted_peak:
                    time_to_peak = (trend.predicted_peak - datetime.now()).total_seconds() / 3600
                    if time_to_peak > 0:
                        msg += f"   ⏰ Peak predicted in {time_to_peak:.1f}h\n"
                
                msg += f"   Data points: {trend.data_points} | Confidence: {trend.confidence:.0%}\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in trends: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def influencers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show top influencers and relationship insights.
        
        Usage: /influencers
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        try:
            engine = self._get_inference_engine()
            graph = engine.analyze_relationships()
            
            msg = "🌟 **Network Analysis**\n\n"
            
            # Influencers
            if graph.influencers:
                msg += "**Top Influencers:**\n"
                for i, inf in enumerate(graph.influencers[:10], 1):
                    msg += f"{i}. `{inf['entity_id'][:20]}...`\n"
                    msg += f"   Centrality: {inf['centrality']:.2f} | "
                    msg += f"Connections: {inf['connections']}\n"
                msg += "\n"
            
            # Clusters
            msg += f"**Network Structure:**\n"
            msg += f"• Clusters detected: {len(graph.clusters)}\n"
            msg += f"• Echo chambers: {len(graph.echo_chambers)}\n"
            msg += f"• Bridge entities: {len(graph.bridges)}\n\n"
            
            if graph.echo_chambers:
                msg += "**Echo Chambers (High Isolation):**\n"
                for chamber in graph.echo_chambers[:3]:
                    msg += f"• {chamber['id']}: {chamber['size']} entities\n"
                    msg += f"  Density: {chamber['density']:.0%} | Isolation: {chamber['isolation']:.0%}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in influencers: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Predict engagement for content.
        
        Usage: /predict <content>
        Example: /predict Check out this amazing new feature!
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /predict <content>\n\n"
                "Example: /predict This is my post content!"
            )
            return
        
        content = ' '.join(context.args)
        
        try:
            engine = self._get_inference_engine()
            prediction = engine.predict_engagement(content)
            
            msg = "🎯 **Engagement Prediction**\n\n"
            msg += f"**Content:** _{content[:100]}..._\n\n"
            
            msg += f"📊 **Predictions:**\n"
            msg += f"• Likes: ~{prediction.predicted_likes}\n"
            msg += f"• Replies: ~{prediction.predicted_replies}\n"
            msg += f"• Reposts: ~{prediction.predicted_reposts}\n"
            msg += f"• Total Engagement: ~{prediction.predicted_likes + prediction.predicted_replies + prediction.predicted_reposts}\n\n"
            
            msg += f"🎯 Confidence: {prediction.confidence:.0%}\n\n"
            
            if prediction.factors:
                msg += "**Factors:**\n"
                for factor in prediction.factors:
                    emoji = {
                        'optimal_length': '✅',
                        'good_hashtag_count': '🏷️',
                        'asks_question': '❓',
                        'author_history': '👤'
                    }.get(factor, '•')
                    msg += f"{emoji} {factor.replace('_', ' ').title()}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def anomalies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show detected anomalies.
        
        Usage: /anomalies [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 24
        if context.args:
            try:
                hours = int(context.args[0])
            except ValueError:
                pass
        
        try:
            engine = self._get_inference_engine()
            anomalies = engine.detect_anomalies(hours=hours)
            
            if not anomalies:
                await update.message.reply_text(f"✅ No anomalies detected in last {hours}h")
                return
            
            msg = f"🚨 **Anomalies Detected (Last {hours}h)**\n\n"
            
            for anomaly in anomalies:
                # Severity emoji
                severity_emoji = {
                    'critical': '🔴',
                    'warning': '🟡',
                    'info': '🟢'
                }.get(anomaly.severity, '⚪')
                
                msg += f"{severity_emoji} **{anomaly.anomaly_type.replace('_', ' ').title()}**\n"
                msg += f"Severity: {anomaly.severity.upper()}\n"
                msg += f"Description: {anomaly.description}\n"
                
                if anomaly.entities_involved:
                    msg += f"Entities: {', '.join(anomaly.entities_involved[:3])}\n"
                
                if anomaly.metrics:
                    msg += "Metrics:\n"
                    for key, value in anomaly.metrics.items():
                        msg += f"  • {key}: {value:.2f}\n"
                
                if anomaly.recommended_action:
                    msg += f"💡 Action: {anomaly.recommended_action}\n"
                
                msg += "\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in anomalies: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Track sentiment for a topic.
        
        Usage: /sentiment <topic> [hours]
        Example: /sentiment #AlleyBot 168
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /sentiment <topic> [hours]\n\n"
                "Examples:\n"
                "/sentiment #AlleyBot\n"
                "/sentiment crypto 72"
            )
            return
        
        topic = context.args[0]
        hours = 168  # 1 week default
        
        if len(context.args) > 1:
            try:
                hours = int(context.args[1])
            except ValueError:
                pass
        
        try:
            engine = self._get_inference_engine()
            evolution = engine.track_sentiment(topic, hours=hours)
            
            msg = f"💭 **Sentiment Analysis: {topic}**\n"
            msg += f"Time window: {hours}h\n\n"
            
            # Trend direction emoji
            direction_emoji = {
                'improving': '📈',
                'worsening': '📉',
                'stable': '➡️'
            }.get(evolution.trend_direction, '➡️')
            
            msg += f"{direction_emoji} **Trend: {evolution.trend_direction.upper()}**\n"
            msg += f"Volatility: {evolution.volatility:.2f}\n"
            msg += f"Data points: {len(evolution.timeline)}\n\n"
            
            if evolution.key_events:
                msg += "**Key Events (Sentiment Shifts):**\n"
                for event in evolution.key_events[:5]:
                    direction = '📈' if event['direction'] == 'positive' else '📉'
                    msg += f"{direction} {event['time'][:16]}\n"
                    msg += f"   Shift: {event['shift']:.0%} | Volume: {event['volume']}\n"
            else:
                msg += "No major sentiment shifts detected\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in sentiment: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def patterns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show cross-platform patterns.
        
        Usage: /patterns [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 48
        if context.args:
            try:
                hours = int(context.args[0])
            except ValueError:
                pass
        
        try:
            engine = self._get_inference_engine()
            patterns = engine.find_cross_platform_patterns(hours=hours)
            
            if not patterns:
                await update.message.reply_text(
                    f"🌐 No cross-platform patterns detected in last {hours}h\n\n"
                    "Need data from multiple platforms to detect patterns."
                )
                return
            
            msg = f"🌐 **Cross-Platform Patterns (Last {hours}h)**\n\n"
            
            for i, pattern in enumerate(patterns[:10], 1):
                strength_bars = '█' * int(pattern.strength * 10)
                
                msg += f"{i}. **{pattern.pattern_type.upper()}**\n"
                msg += f"   {strength_bars} {pattern.strength:.0%}\n"
                msg += f"   {pattern.description}\n"
                msg += f"   Platforms: {', '.join(pattern.platforms)}\n"
                
                if pattern.entities_involved:
                    msg += f"   Key entities: {len(pattern.entities_involved)}\n"
                
                msg += "\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in patterns: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def intel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Quick intelligence briefing.
        
        Usage: /intel
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        try:
            engine = self._get_inference_engine()
            summary = engine.get_intelligence_summary()
            
            msg = "🧠 **Intelligence Briefing**\n\n"
            
            msg += "📈 **Current Trends:**\n"
            if summary.get('trends'):
                for trend in summary['trends'][:5]:
                    msg += f"• {trend}\n"
            else:
                msg += "• No major trends\n"
            
            msg += f"\n🌟 **Network:** {summary.get('influencers', 0)} influencers\n"
            msg += f"🌐 **Patterns:** {summary.get('cross_platform_patterns', 0)} cross-platform\n"
            msg += f"🚨 **Anomalies:** {summary.get('active_anomalies', 0)} active\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in intel: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Return command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('trends', self.trends),
            CommandHandler('influencers', self.influencers),
            CommandHandler('predict', self.predict),
            CommandHandler('anomalies', self.anomalies),
            CommandHandler('sentiment', self.sentiment),
            CommandHandler('patterns', self.patterns),
            CommandHandler('intel', self.intel),
        ]


# Fix import
from datetime import datetime

# Singleton
_intelligence_commands_instance = None


def get_intelligence_commands(telegram_plugin=None):
    """Get or create IntelligenceCommands singleton"""
    global _intelligence_commands_instance
    if _intelligence_commands_instance is None and telegram_plugin is not None:
        _intelligence_commands_instance = IntelligenceCommands(telegram_plugin)
    return _intelligence_commands_instance
