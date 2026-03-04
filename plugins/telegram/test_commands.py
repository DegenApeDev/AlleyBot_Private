"""
Test Commands for Telegram
Debugging and testing utilities
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TestCommands:
    """Test command handlers for debugging"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
    
    @property
    def core(self):
        """Dynamically access core from telegram plugin"""
        return self.telegram.core
    
    async def test_mcp_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test MCP plugin status and news capability"""
        logger.info(f"test_mcp_news called by user {update.effective_user.id}")
        try:
            await update.message.reply_text("🔍 Command received, checking MCP...")
            
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            await update.message.reply_text("🔍 Checking MCP plugin status...")
            
            # Get MCP plugin
            mcp_plugin = self.core.plugin_manager.get_plugin('mcp')
            
            if not mcp_plugin:
                await update.message.reply_text(
                    "❌ MCP plugin not loaded\n\n"
                    "News fetching won't work without MCP.\n"
                    "Polymarket will use social sentiment and knowledge graph instead."
                )
                return
            
            # Show MCP status
            output = "✅ MCP Plugin Status:\n\n"
            output += f"Name: {getattr(mcp_plugin, 'name', 'unknown')}\n"
            output += f"Status: {getattr(mcp_plugin, 'status', 'unknown')}\n"
            output += f"Servers: {len(getattr(mcp_plugin, 'mcp_servers', {}))}\n"
            
            # Check for RSS news fetcher
            if hasattr(mcp_plugin, 'rss_news_fetcher') and mcp_plugin.rss_news_fetcher:
                output += f"RSS Feeds: {len(mcp_plugin.rss_news_fetcher.feeds)}\n"
            
            await update.message.reply_text(output)
            
            # Get query from args or use default
            query = " ".join(context.args) if context.args else "Bitcoin"
            
            # Test news fetching
            if hasattr(mcp_plugin, 'query_news'):
                await update.message.reply_text(f"📰 Fetching news for: '{query}'...")
                
                news_results = await mcp_plugin.query_news(query, limit=5)
                
                if news_results:
                    news_output = f"📰 Found {len(news_results)} news articles:\n\n"
                    for i, article in enumerate(news_results, 1):
                        news_output += f"{i}. {article.get('title', 'No title')}\n"
                        news_output += f"   Source: {article.get('source', 'Unknown')}\n"
                        news_output += f"   Relevance: {article.get('relevance', 0):.0%}\n"
                        news_output += f"   {article.get('summary', 'No summary')[:150]}...\n\n"
                    
                    await update.message.reply_text(news_output)
                else:
                    await update.message.reply_text(
                        "📰 No news articles found.\n"
                        "This could mean:\n"
                        "- No recent articles match the query\n"
                        "- RSS feeds are temporarily unavailable\n"
                        "- Try a different search term"
                    )
            else:
                await update.message.reply_text(
                    "⚠️ query_news method not found.\n"
                    "RSS news integration may not be loaded."
                )
            
        except Exception as e:
            logger.error(f"Error in test_mcp_news: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def test_polymarket_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test full Polymarket analysis with news"""
        logger.info(f"test_polymarket_analysis called by user {update.effective_user.id}")
        try:
            await update.message.reply_text("🔍 Command received, starting analysis...")
            
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            await update.message.reply_text("🔍 Testing Polymarket analysis flow...")
            
            # Fetch a market
            markets = await polymarket.fetch_markets(limit=1)
            
            if not markets:
                await update.message.reply_text("❌ No markets found")
                return
            
            market = markets[0]
            
            await update.message.reply_text(
                f"📊 Analyzing market:\n{market.question}\n\n"
                "This will test:\n"
                "- Social sentiment gathering\n"
                "- MCP news fetching\n"
                "- Knowledge graph queries\n"
                "- Unified reasoning\n\n"
                "Check logs for detailed output..."
            )
            
            # Analyze the market (this will trigger news fetching)
            analysis = await polymarket.analyze_market(market)
            
            # Report results
            output = f"✅ Analysis Complete!\n\n"
            output += f"Prediction: {analysis.predicted_outcome}\n"
            output += f"Confidence: {analysis.confidence:.1%}\n"
            output += f"Edge: {analysis.edge:.1%}\n"
            output += f"Sources used: {', '.join(analysis.sources)}\n\n"
            output += f"Reasoning:\n{analysis.reasoning[:200]}..."
            
            await update.message.reply_text(output)
            
        except Exception as e:
            logger.error(f"Error in test_polymarket_analysis: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Return command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('test_mcp_news', self.test_mcp_news),
            CommandHandler('test_polymarket_analysis', self.test_polymarket_analysis),
        ]
