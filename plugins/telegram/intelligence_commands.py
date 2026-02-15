"""
Telegram Commands for World State Intelligence (Phase 7)

Provides /trends, /influencers, /predict, /anomalies, /sentiment, /patterns
for owner to access world state intelligence.

Part of AGI Core - Phase 7
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime

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
                
                if hasattr(trend, 'predicted_peak') and trend.predicted_peak:
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
            
            msg = f"🚨 **Detected Anomalies (Last {hours}h)**\n\n"
            
            if not anomalies:
                msg += "No significant anomalies detected."
            else:
                for i, anomaly in enumerate(anomalies[:10], 1):
                    anomaly_emoji = getattr(anomaly, 'emoji', '🚨')
                    title = getattr(anomaly, 'title', getattr(anomaly, 'topic', 'Unknown'))
                    score = getattr(anomaly, 'score', 0.0)
                    confidence = getattr(anomaly, 'confidence', 0.0)
                    description = getattr(anomaly, 'description', '')[:150]
                    
                    msg += f"{i}. {anomaly_emoji} **{title}**\n"
                    msg += f"   Score: {score:.2f} | Confidence: {confidence:.0%}\n"
                    msg += f"   {description}...\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in anomalies: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Analyze sentiment for a topic.
        
        Usage: /sentiment <topic> [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /sentiment <topic> [hours]\n\n"
                "Example: /sentiment Bitcoin 48"
            )
            return
        
        topic = context.args[0]
        hours = 24
        if len(context.args) > 1:
            try:
                hours = int(context.args[1])
            except ValueError:
                pass
        
        try:
            ClawbrAnalytics_cls = None
            try:
                from src.analytics.clawbr_analytics import ClawbrAnalytics
                ClawbrAnalytics_cls = ClawbrAnalytics
            except ImportError:
                try:
                    from alleybot.analytics.clawbr_analytics import ClawbrAnalytics
                    ClawbrAnalytics_cls = ClawbrAnalytics
                except ImportError:
                    raise ImportError("ClawbrAnalytics not found")
            
            analytics = ClawbrAnalytics_cls()
            result = analytics.analyze_sentiment(topic, hours)
            
            score = getattr(result, 'score', 0.0)
            sentiment_emoji = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "🟡"
            sentiment_label = "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
            
            summary = getattr(result, 'summary', 'No summary available')
            examples = getattr(result, 'examples', [])
            
            msg = f"😊 **Sentiment Analysis for '{topic}' (Last {hours}h)**\n\n"
            msg += f"**Score:** {sentiment_emoji} {score:.3f} ({sentiment_label})\n\n"
            msg += f"**Summary:** {summary}\n\n"
            
            if examples:
                msg += "**Recent Examples:**\n"
                for ex in examples[:5]:
                    msg += f"• {str(ex)[:100]}...\n"
            else:
                msg += "**Examples:** None available\n"
            
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
                strength = getattr(pattern, 'strength', 0.5)
                strength_bars = '█' * int(strength * 10)
                
                msg += f"{i}. **{getattr(pattern, 'pattern_type', 'Unknown').upper()}**\n"
                msg += f"   {strength_bars} {strength:.0%}\n"
                msg += f"   {getattr(pattern, 'description', 'No description')}\n"
                platforms = getattr(pattern, 'platforms', [])
                if platforms:
                    msg += f"   Platforms: {', '.join(platforms)}\n"
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
            
            # Get various intelligence data
            trends = engine.detect_trends(hours=24, top_n=5)
            anomalies = engine.detect_anomalies(hours=24)
            
            msg = "🧠 **Intelligence Briefing**\n\n"
            
            msg += "📈 **Current Trends:**\n"
            if trends:
                for trend in trends[:5]:
                    topic = getattr(trend, 'topic', 'Unknown')
                    msg += f"• {topic}\n"
            else:
                msg += "• No major trends\n"
            
            msg += f"\n🚨 **Anomalies:** {len(anomalies) if anomalies else 0} active\n"
            msg += f"🌐 **Status:** Systems operational\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in intel: {e}")
            await update.message.reply_text(f"❌ Error: {e}")