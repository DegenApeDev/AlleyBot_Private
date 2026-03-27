"""
Telegram Plugin for AlleyBot
Secure two-way communication with owner DegenApeDev (User ID: 6172568442)
"""

import os
import requests
import json
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from plugin_manager import AlleyBotPlugin

class Telegram(AlleyBotPlugin):
    """Telegram bot for secure owner communication"""
    
    def __init__(self, config):
        super().__init__(config)
        self.enabled = config.get('enabled', False)
        self.core = None
        
        # Owner configuration - use env var, never hardcode
        admin_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')
        self.owner_user_id = int(admin_id) if admin_id.isdigit() else None
        self.owner_name = "DegenApeDev"
        
        # Telegram bot configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot = None
        self.application = None
        
        # Communication state
        self.is_running = False
        self.message_queue = []
        self.last_activity = None
        self._polling_thread = None
        self._polling_loop = None
        self._polling_started_event = None
        
        # Pre-warm shared SentenceTransformer model in background so it's ready before first message
        try:
            def _prewarm():
                try:
                    from plugins.telegram.intent_classifier import get_sentence_model
                    get_sentence_model()
                except Exception as e:
                    print(f"⚠️ SentenceTransformer pre-warm failed: {e}")
            threading.Thread(target=_prewarm, daemon=True).start()
        except Exception as e:
            print(f"⚠️ SentenceTransformer pre-warm thread failed: {e}")

        # Always try to initialize if token exists
        if self.bot_token:
            try:
                # Configure HTTP client with longer timeouts to prevent errors during long operations
                # Default is 5s, we increase to 60s connect / 120s read to handle agent cycles
                from telegram.request import HTTPXRequest
                
                # Build Application with custom request instance using individual timeouts
                request = HTTPXRequest(
                    connection_pool_size=8,
                    connect_timeout=60.0,
                    read_timeout=120.0,
                    write_timeout=30.0,
                    pool_timeout=5.0
                )
                
                self.application = (
                    Application.builder()
                    .token(self.bot_token)
                    .request(request)
                    .build()
                )
                
                # Get bot instance from application
                self.bot = self.application.bot
                
                self._setup_handlers()
                print("✅ Telegram plugin initialized - Owner: DegenApeDev")
                # Plugin is enabled if we have a token
                self.enabled = True
            except Exception as e:
                print(f"❌ Failed to initialize Telegram bot: {e}")
                import traceback
                traceback.print_exc()
                self.enabled = False
        else:
            if self.enabled:
                print("⚠️  TELEGRAM_BOT_TOKEN not found in environment")
            self.enabled = False
    
    def _setup_handlers(self):
        """Setup Telegram bot handlers"""
        if not self.application:
            return

        async def _telegram_error_handler(update, context):
            try:
                print(f"❌ Telegram handler error: {context.error}")
                if update and getattr(update, 'effective_message', None):
                    await update.effective_message.reply_text(f"❌ Telegram handler error: {context.error}")
            except Exception as error_handler_exc:
                print(f"⚠️ Telegram error handler failed: {error_handler_exc}")

        self.application.add_error_handler(_telegram_error_handler)
        
        # Import intelligent commands
        from plugins.telegram.intelligent_commands import IntelligentTelegramCommands
        self.intelligent_commands = IntelligentTelegramCommands(self)
        
        # Import conversational AI
        from plugins.telegram.conversational_ai import ConversationalAI
        self.conversational_ai = ConversationalAI(self)
        
        # Import brain commands
        from plugins.telegram.brain_commands import BrainCommands
        self.brain_commands = BrainCommands(self)
        
        # Import goal commands
        from plugins.telegram.goal_commands import GoalCommands
        self.goal_commands = GoalCommands(self)
        
        # Import plan commands
        from plugins.telegram.plan_commands import PlanCommands
        self.plan_commands = PlanCommands(self)
        
        # Import Phase 1: Self-Reflection commands
        from plugins.telegram.reflection_commands import ReflectionCommands
        self.reflection_commands = ReflectionCommands(self)
        
        # Import Phase 7: World State Intelligence commands
        from plugins.telegram.intelligence_commands import IntelligenceCommands
        self.intelligence_commands = IntelligenceCommands(self)
        
        # Import Phase 10: Causal Understanding commands
        from plugins.telegram.causal_commands import CausalCommands
        self.causal_commands = CausalCommands(self)
        
        # Import Tier 2: Synergy Gate commands
        from plugins.telegram.synergy_commands import SynergyCommands
        self.synergy_commands = SynergyCommands(self)
        
        # Import trading commands
        from plugins.telegram.trading_commands import TradingCommands
        self.trading_commands = TradingCommands(self)
        
        # Import Polymarket commands
        from plugins.telegram.polymarket_commands import PolymarketCommands
        self.polymarket_commands = PolymarketCommands(self)
        
        # Import test commands
        from plugins.telegram.test_commands import TestCommands
        self.test_commands = TestCommands(self)
        
        # Import inline menu system
        from plugins.telegram.menu_handlers import MenuHandlers
        self.menu_handlers = MenuHandlers(self)
        
        # Basic commands
        self.application.add_handler(CommandHandler("start", self._handle_start))
        # /help and /menu are registered by menu_handlers.register() below
        
        # AI & Chat commands
        self.application.add_handler(CommandHandler("chat", self.intelligent_commands.ai_chat))
        
        # Moltx commands
        self.application.add_handler(CommandHandler("moltx_post", self.intelligent_commands.moltx_post))
        self.application.add_handler(CommandHandler("moltx_feed", self.intelligent_commands.moltx_feed))
        self.application.add_handler(CommandHandler("moltx_engage", self.intelligent_commands.moltx_engage))
        self.application.add_handler(CommandHandler("moltx_trending", self.intelligent_commands.moltx_trending))
        self.application.add_handler(CommandHandler("moltx_claim", self.intelligent_commands.moltx_claim))
        self.application.add_handler(CommandHandler("moltx_debug", self.intelligent_commands.moltx_debug))
        self.application.add_handler(CommandHandler("moltx_status", self.intelligent_commands.moltx_status))
        self.application.add_handler(CommandHandler("moltx_check_reward", self.intelligent_commands.moltx_check_reward))
        self.application.add_handler(CommandHandler("moltx_claim_reward", self.intelligent_commands.moltx_claim_reward))
        
        # SyMod-driven social agent commands
        self.application.add_handler(CommandHandler("symod_start", self.intelligent_commands.symod_start))
        self.application.add_handler(CommandHandler("symod_stop", self.intelligent_commands.symod_stop))
        self.application.add_handler(CommandHandler("symod_status", self.intelligent_commands.symod_status))
        self.application.add_handler(CommandHandler("symod_cycle", self.intelligent_commands.symod_cycle))
        self.application.add_handler(CommandHandler("symod_config", self.intelligent_commands.symod_config))
        self.application.add_handler(CommandHandler("moltchan_post", self.intelligent_commands.moltchan_post))
        
        # System commands
        self.application.add_handler(CommandHandler("status", self.conversational_ai.status_command))
        self.application.add_handler(CommandHandler("skills", self.intelligent_commands.skills))
        self.application.add_handler(CommandHandler("skill", self.intelligent_commands.execute_skill))
        self.application.add_handler(CommandHandler("token_stats", self.intelligent_commands.token_stats))
        
        # Solana commands
        self.application.add_handler(CommandHandler("add_solana_token", self.intelligent_commands.add_solana_token))
        
        # Clawbr auto-debate
        self.application.add_handler(CommandHandler("clawbr_auto_debate", self.intelligent_commands.clawbr_auto_debate))
        
        # Crypto price commands
        self.application.add_handler(CommandHandler("crypto_price", self.intelligent_commands.crypto_price))
        self.application.add_handler(CommandHandler("crypto_prices", self.intelligent_commands.crypto_prices))
        self.application.add_handler(CommandHandler("crypto_trending", self.intelligent_commands.crypto_trending))
        
        # On-chain commands
        self.application.add_handler(CommandHandler("wallet", self.intelligent_commands.wallet))
        self.application.add_handler(CommandHandler("balance", self.intelligent_commands.balance))
        self.application.add_handler(CommandHandler("block", self.intelligent_commands.block))
        self.application.add_handler(CommandHandler("track", self.intelligent_commands.track_token))
        self.application.add_handler(CommandHandler("tx", self.intelligent_commands.tx))
        self.application.add_handler(CommandHandler("activity", self.intelligent_commands.activity))
        self.application.add_handler(CommandHandler("onchain", self.intelligent_commands.onchain_status))
        
        # Content strategy commands
        self.application.add_handler(CommandHandler("calendar", self.intelligent_commands.calendar))
        self.application.add_handler(CommandHandler("conversations", self.intelligent_commands.conversations))
        self.application.add_handler(CommandHandler("personality", self.intelligent_commands.personality))
        
        # Feedback loop commands
        self.application.add_handler(CommandHandler("insights", self.intelligent_commands.insights))
        self.application.add_handler(CommandHandler("check_engagement", self.intelligent_commands.check_engagement))
        self.application.add_handler(CommandHandler("tracked_posts", self.intelligent_commands.tracked_posts))
        
        # Image generation command
        self.application.add_handler(CommandHandler("generate_image", self.intelligent_commands.generate_image))
        
        # Brain commands
        self.application.add_handler(CommandHandler("think", self.intelligent_commands.brain_think))
        self.application.add_handler(CommandHandler("brain_start", self.brain_commands.brain_start))
        self.application.add_handler(CommandHandler("brain_stop", self.brain_commands.brain_stop))
        self.application.add_handler(CommandHandler("brain_status", self.brain_commands.brain_status))
        self.application.add_handler(CommandHandler("brain_mode", self.brain_commands.brain_mode))
        
        # Monitoring dashboard commands
        from plugins.telegram.monitoring_commands import MonitoringCommands
        self.monitoring_commands = MonitoringCommands(self)
        self.monitoring_commands.register_commands(self.application)
        self.application.add_handler(CommandHandler("brain_log", self.brain_commands.brain_log))
        self.application.add_handler(CommandHandler("brain_confidence_debug", self.brain_commands.brain_confidence_debug))
        self.application.add_handler(CommandHandler("brain", self.brain_commands.brain_status))  # alias
        
        # Goal commands
        self.application.add_handler(CommandHandler("goals", self.goal_commands.goals_list))
        self.application.add_handler(CommandHandler("goals_scan", self.goal_commands.goals_scan))
        self.application.add_handler(CommandHandler("goals_propose", self.goal_commands.goals_propose))
        self.application.add_handler(CommandHandler("goals_approve", self.goal_commands.goals_approve))
        self.application.add_handler(CommandHandler("goals_reject", self.goal_commands.goals_reject))
        self.application.add_handler(CommandHandler("goals_start", self.goal_commands.goals_start))
        self.application.add_handler(CommandHandler("goals_complete", self.goal_commands.goals_complete))
        self.application.add_handler(CommandHandler("goals_detail", self.goal_commands.goals_detail))
        self.application.add_handler(CommandHandler("goals_stats", self.goal_commands.goals_stats))
        
        # Plan commands
        self.application.add_handler(CommandHandler("plan_create", self.plan_commands.plan_create))
        self.application.add_handler(CommandHandler("plan_status", self.plan_commands.plan_status))
        self.application.add_handler(CommandHandler("plan_next", self.plan_commands.plan_next))
        self.application.add_handler(CommandHandler("plan_retry", self.plan_commands.plan_retry))
        self.application.add_handler(CommandHandler("plan_list", self.plan_commands.plan_list))
        
        # World State commands
        self.application.add_handler(CommandHandler("world_status", self.intelligent_commands.world_status))
        self.application.add_handler(CommandHandler("world_entity", self.intelligent_commands.world_entity))
        self.application.add_handler(CommandHandler("world_facts", self.intelligent_commands.world_facts))
        self.application.add_handler(CommandHandler("world_relations", self.intelligent_commands.world_relations))
        self.application.add_handler(CommandHandler("world_search", self.intelligent_commands.world_search))
        self.application.add_handler(CommandHandler("world_events", self.intelligent_commands.world_events))
        self.application.add_handler(CommandHandler("world_trends", self.intelligent_commands.world_trends))
        self.application.add_handler(CommandHandler("world_cleanup", self.intelligent_commands.world_cleanup))
        self.application.add_handler(CommandHandler("brain_world_sync", self.intelligent_commands.world_sync))
        
        # A2A commands
        self.application.add_handler(CommandHandler("a2a_status", self.intelligent_commands.a2a_status))
        self.application.add_handler(CommandHandler("a2a_start", self.intelligent_commands.a2a_start))
        self.application.add_handler(CommandHandler("a2a_stop", self.intelligent_commands.a2a_stop))
        self.application.add_handler(CommandHandler("a2a_tasks", self.intelligent_commands.a2a_tasks))
        
        # ERC-8004 / Self-improve commands
        self.application.add_handler(CommandHandler("erc8004_rebuild", self.intelligent_commands.erc8004_rebuild))
        self.application.add_handler(CommandHandler("erc8004_preview", self.intelligent_commands.erc8004_preview))
        self.application.add_handler(CommandHandler("erc8004_update", self.intelligent_commands.erc8004_update))
        self.application.add_handler(CommandHandler("improve_status", self.intelligent_commands.improve_status))
        self.application.add_handler(CommandHandler("improve_self_update_confirm", self.intelligent_commands.improve_self_update_confirm))
        
        # Clawbr commands
        self.application.add_handler(CommandHandler("clawbr_status", self.intelligent_commands.clawbr_status))
        self.application.add_handler(CommandHandler("clawbr_post", self.intelligent_commands.clawbr_post))
        self.application.add_handler(CommandHandler("clawbr_reply", self.intelligent_commands.clawbr_reply))
        self.application.add_handler(CommandHandler("clawbr_feed", self.intelligent_commands.clawbr_feed))
        self.application.add_handler(CommandHandler("clawbr_engage", self.intelligent_commands.clawbr_engage))
        self.application.add_handler(CommandHandler("clawbr_debates", self.intelligent_commands.clawbr_debates))
        self.application.add_handler(CommandHandler("clawbr_create_debate", self.intelligent_commands.clawbr_create_debate))
        self.application.add_handler(CommandHandler("clawbr_join_debate", self.intelligent_commands.clawbr_join_debate))
        self.application.add_handler(CommandHandler("clawbr_vote", self.intelligent_commands.clawbr_vote))
        self.application.add_handler(CommandHandler("clawbr_vote_specific", self.intelligent_commands.clawbr_vote_specific))
        self.application.add_handler(CommandHandler("clawbr_check_voting", self.intelligent_commands.clawbr_check_voting))
        self.application.add_handler(CommandHandler("clawbr_completed_debates", self.intelligent_commands.clawbr_completed_debates))
        self.application.add_handler(CommandHandler("clawbr_leaderboard", self.intelligent_commands.clawbr_leaderboard))
        self.application.add_handler(CommandHandler("clawbr_search", self.intelligent_commands.clawbr_search))
        self.application.add_handler(CommandHandler("clawbr_stats", self.intelligent_commands.clawbr_stats))
        self.application.add_handler(CommandHandler("clawbr_analyze", self.intelligent_commands.clawbr_analyze))
        self.application.add_handler(CommandHandler("clawbr_strategy", self.intelligent_commands.clawbr_strategy))
        self.application.add_handler(CommandHandler("clawbr_turns", self.intelligent_commands.clawbr_turns))
        self.application.add_handler(CommandHandler("clawbr_remind", self.intelligent_commands.clawbr_remind))
        self.application.add_handler(CommandHandler("clawbr_force_reply", self.intelligent_commands.clawbr_force_reply))
        self.application.add_handler(CommandHandler("clawbr_verify_x", self.intelligent_commands.clawbr_verify_x))
        self.application.add_handler(CommandHandler("clawbr_register_tournament", self.intelligent_commands.clawbr_register_tournament))
        
        # ClawChess commands - register with existence checking
        clawchess_commands = [
            ("clawchess_register", self.intelligent_commands.clawchess_register),
            ("clawchess_status", self.intelligent_commands.clawchess_status),
            ("clawchess_queue", self.intelligent_commands.clawchess_queue),
            ("clawchess_leave", self.intelligent_commands.clawchess_leave),
            ("clawchess_play", self.intelligent_commands.clawchess_play),
            ("clawchess_move", self.intelligent_commands.clawchess_move),
            ("clawchess_resign", self.intelligent_commands.clawchess_resign),
            ("clawchess_leaderboard", self.intelligent_commands.clawchess_leaderboard),
            ("clawchess_autoplay", self.intelligent_commands.clawchess_autoplay),
            ("clawchess_activity", self.intelligent_commands.clawchess_activity),
            ("clawchess_challenges", self.intelligent_commands.clawchess_challenges),
            ("clawchess_accept", self.intelligent_commands.clawchess_accept),
            ("clawchess_decline", self.intelligent_commands.clawchess_decline),
            ("clawchess_challenge", self.intelligent_commands.clawchess_challenge),
            ("clawchess_tournament", self.intelligent_commands.clawchess_tournament),
        ]
        
        for command_name, command_handler in clawchess_commands:
            if hasattr(self.intelligent_commands, command_handler.__name__):
                self.application.add_handler(CommandHandler(command_name, command_handler))
                print(f"✅ Registered ClawChess command: {command_name}")
            else:
                print(f"⚠️ ClawChess command not available: {command_name}")
        
        # Clawbr Wallet and Token commands
        self.application.add_handler(CommandHandler("clawbr_verify_wallet", self.intelligent_commands.clawbr_verify_wallet))
        self.application.add_handler(CommandHandler("clawbr_balance", self.intelligent_commands.clawbr_balance))
        self.application.add_handler(CommandHandler("clawbr_snapshot", self.intelligent_commands.clawbr_snapshot))
        self.application.add_handler(CommandHandler("clawbr_claim", self.intelligent_commands.clawbr_claim))
        self.application.add_handler(CommandHandler("clawbr_transfer", self.intelligent_commands.clawbr_transfer))
        self.application.add_handler(CommandHandler("clawbr_auto_claim", self.intelligent_commands.clawbr_auto_claim))
        self.application.add_handler(CommandHandler("clawbr_claim_status", self.intelligent_commands.clawbr_claim_status))
        self.application.add_handler(CommandHandler("clawbr_token_tx", self.intelligent_commands.clawbr_token_tx))
        
        # MCP commands
        self.application.add_handler(CommandHandler("mcp_status", self.intelligent_commands.mcp_status))
        self.application.add_handler(CommandHandler("mcp_search", self.intelligent_commands.mcp_search))
        self.application.add_handler(CommandHandler("mcp_research", self.intelligent_commands.mcp_research))
        self.application.add_handler(CommandHandler("mcp_analyze", self.intelligent_commands.mcp_analyze))
        
        # Base Wallet Balance commands
        self.application.add_handler(CommandHandler("base_balance", self.intelligent_commands.base_balance))
        self.application.add_handler(CommandHandler("base_eth_balance", self.intelligent_commands.base_eth_balance))
        self.application.add_handler(CommandHandler("base_tokens", self.intelligent_commands.base_tokens))
        self.application.add_handler(CommandHandler("add_base_token", self.intelligent_commands.add_base_token))
        self.application.add_handler(CommandHandler("base_wallet_summary", self.intelligent_commands.base_wallet_summary))
        self.application.add_handler(CommandHandler("contract_balance", self.intelligent_commands.contract_balance))
        self.application.add_handler(CommandHandler("multi_contract_balance", self.intelligent_commands.multi_contract_balance))
        
        # DeFi commands
        self.application.add_handler(CommandHandler("swap_quote", self.intelligent_commands.swap_quote))
        self.application.add_handler(CommandHandler("compare_aggregators", self.intelligent_commands.compare_aggregators))
        self.application.add_handler(CommandHandler("swap_tokens", self.intelligent_commands.swap_tokens))
        self.application.add_handler(CommandHandler("supported_tokens", self.intelligent_commands.supported_tokens))
        self.application.add_handler(CommandHandler("fluid_positions", self.intelligent_commands.fluid_positions))
        self.application.add_handler(CommandHandler("fluid_earnings", self.intelligent_commands.fluid_earnings))
        self.application.add_handler(CommandHandler("fluid_stats", self.intelligent_commands.fluid_stats))
        self.application.add_handler(CommandHandler("fluid_apr", self.intelligent_commands.fluid_apr))
        
        # Clawstr commands
        self.application.add_handler(CommandHandler("clawstr_post", self.intelligent_commands.clawstr_post))
        self.application.add_handler(CommandHandler("clawstr_reply", self.intelligent_commands.clawstr_reply))
        self.application.add_handler(CommandHandler("clawstr_upvote", self.intelligent_commands.clawstr_upvote))
        self.application.add_handler(CommandHandler("clawstr_downvote", self.intelligent_commands.clawstr_downvote))
        self.application.add_handler(CommandHandler("clawstr_show", self.intelligent_commands.clawstr_show))
        self.application.add_handler(CommandHandler("clawstr_recent", self.intelligent_commands.clawstr_recent))
        self.application.add_handler(CommandHandler("clawstr_search", self.intelligent_commands.clawstr_search))
        self.application.add_handler(CommandHandler("clawstr_notifications", self.intelligent_commands.clawstr_notifications))
        self.application.add_handler(CommandHandler("clawstr_wallet_balance", self.intelligent_commands.clawstr_wallet_balance))
        self.application.add_handler(CommandHandler("clawstr_wallet_sync", self.intelligent_commands.clawstr_wallet_sync))
        self.application.add_handler(CommandHandler("clawstr_zap", self.intelligent_commands.clawstr_zap))
        
        # Clawnch commands
        self.application.add_handler(CommandHandler("clawnch_agent_register", self.intelligent_commands.clawnch_agent_register))
        self.application.add_handler(CommandHandler("clawnch_clear_cooldown", self.intelligent_commands.clawnch_clear_cooldown))
        self.application.add_handler(CommandHandler("clawnch_validate_launch", self.intelligent_commands.clawnch_validate_launch))
        self.application.add_handler(CommandHandler("clawnch_launch_token_simple", self.intelligent_commands.clawnch_launch_token_simple))
        self.application.add_handler(CommandHandler("clawnch_promote_token", self.intelligent_commands.clawnch_promote_token))
        self.application.add_handler(CommandHandler("clawnch_claim_fees", self.intelligent_commands.clawnch_claim_fees))
        self.application.add_handler(CommandHandler("clawnch_launch_alleybot_token", self.intelligent_commands.clawnch_launch_alleybot_token))
        self.application.add_handler(CommandHandler("clawnch_upload_image", self.intelligent_commands.clawnch_upload_image))
        self.application.add_handler(CommandHandler("clawnch_launch_token", self.intelligent_commands.clawnch_launch_token))
        self.application.add_handler(CommandHandler("clawnch_molten_register", self.intelligent_commands.clawnch_molten_register))
        self.application.add_handler(CommandHandler("clawnch_molten_status", self.intelligent_commands.clawnch_molten_status))
        self.application.add_handler(CommandHandler("clawnch_molten_create_intent", self.intelligent_commands.clawnch_molten_create_intent))
        self.application.add_handler(CommandHandler("clawnch_molten_get_matches", self.intelligent_commands.clawnch_molten_get_matches))
        self.application.add_handler(CommandHandler("clawnch_twitter_post", self.intelligent_commands.clawnch_twitter_post))
        self.application.add_handler(CommandHandler("clawnch_twitter_search", self.intelligent_commands.clawnch_twitter_search))
        self.application.add_handler(CommandHandler("clawnch_get_stats", self.intelligent_commands.clawnch_get_stats))
        
        # Phase 1: Self-Reflection commands
        self.application.add_handler(CommandHandler("reflection_status", self.reflection_commands.reflection_status))
        self.application.add_handler(CommandHandler("reflection_log", self.reflection_commands.reflection_log))
        self.application.add_handler(CommandHandler("reflection_tune", self.reflection_commands.reflection_tune))
        self.application.add_handler(CommandHandler("evolve", self.reflection_commands.evolve))
        self.application.add_handler(CommandHandler("strategies", self.reflection_commands.strategies))
        
        # Phase 7: World State Intelligence commands
        self.application.add_handler(CommandHandler("trends", self.intelligence_commands.trends))
        self.application.add_handler(CommandHandler("influencers", self.intelligence_commands.influencers))
        self.application.add_handler(CommandHandler("predict", self.intelligence_commands.predict))
        self.application.add_handler(CommandHandler("anomalies", self.intelligence_commands.anomalies))
        self.application.add_handler(CommandHandler("sentiment", self.intelligence_commands.sentiment))
        self.application.add_handler(CommandHandler("patterns", self.intelligence_commands.patterns))
        self.application.add_handler(CommandHandler("intel", self.intelligence_commands.intel))
        
        # Phase 10: Causal Understanding commands
        self.application.add_handler(CommandHandler("causal", self.causal_commands.causal_summary))
        self.application.add_handler(CommandHandler("why", self.causal_commands.why))
        self.application.add_handler(CommandHandler("whatif", self.causal_commands.whatif))
        self.application.add_handler(CommandHandler("root_cause", self.causal_commands.root_cause))
        self.application.add_handler(CommandHandler("attribution", self.causal_commands.attribution))
        
        # Tier 2: Synergy Gate commands
        self.application.add_handler(CommandHandler("validate", self.synergy_commands.validate))
        self.application.add_handler(CommandHandler("integrity", self.synergy_commands.integrity))
        self.application.add_handler(CommandHandler("attest", self.synergy_commands.attest))
        self.application.add_handler(CommandHandler("synergy", self.synergy_commands.synergy_status))
        
        # Trading commands (if trading plugins available)
        from plugins.telegram.trading_commands import TradingCommands
        self.trading_commands = TradingCommands(self)
        self.application.add_handler(CommandHandler("swap_sol", self.trading_commands.swap_sol))
        self.application.add_handler(CommandHandler("swap_base", self.trading_commands.swap_base))
        self.application.add_handler(CommandHandler("sol_price", self.trading_commands.sol_price))
        self.application.add_handler(CommandHandler("base_price", self.trading_commands.base_price))
        self.application.add_handler(CommandHandler("trading_stats", self.trading_commands.trading_stats))
        self.application.add_handler(CommandHandler("recent_trades", self.trading_commands.recent_trades))
        
        # Autonomous trading commands
        self.application.add_handler(CommandHandler("trading_enable", self.trading_commands.trading_enable))
        self.application.add_handler(CommandHandler("trading_disable", self.trading_commands.trading_disable))
        self.application.add_handler(CommandHandler("trading_status", self.trading_commands.trading_status))
        
        # Best Crypto Swap commands (new skill)
        self.application.add_handler(CommandHandler("best_swap_quote", self.trading_commands.best_swap_quote))
        self.application.add_handler(CommandHandler("best_swap_execute", self.trading_commands.best_swap_execute))
        self.application.add_handler(CommandHandler("best_swap_compare", self.trading_commands.best_swap_compare))
        
        # Polymarket commands
        self.application.add_handler(CommandHandler("polymarket_status", self.polymarket_commands.polymarket_status))
        self.application.add_handler(CommandHandler("polymarket_markets", self.polymarket_commands.polymarket_markets))
        self.application.add_handler(CommandHandler("polymarket_analyze", self.polymarket_commands.polymarket_analyze))
        self.application.add_handler(CommandHandler("polymarket_positions", self.polymarket_commands.polymarket_positions))
        self.application.add_handler(CommandHandler("polymarket_stats", self.polymarket_commands.polymarket_stats))
        
        # Test commands
        self.application.add_handler(CommandHandler("test_mcp_news", self.test_commands.test_mcp_news))
        self.application.add_handler(CommandHandler("test_polymarket_analysis", self.test_commands.test_polymarket_analysis))
        
        # AGI Meta-Brain command
        self.application.add_handler(CommandHandler("agi_cycle", self._handle_agi_cycle))
        self.application.add_handler(CommandHandler("multi_platform", self._handle_multi_platform))
        
        # Egyptian Synergy Model commands
        self.application.add_handler(CommandHandler("synergy_status", self._handle_synergy_status))
        self.application.add_handler(CommandHandler("weigh_heart", self._handle_weigh_heart))
        self.application.add_handler(CommandHandler("field_report", self._handle_field_report))
        
        # Console Monitor commands
        self.application.add_handler(CommandHandler("console_monitor", self._handle_console_monitor))
        self.application.add_handler(CommandHandler("console_stats", self._handle_console_stats))
        self.application.add_handler(CommandHandler("pending_messages", self._handle_pending_messages))
        
        # System commands
        self.application.add_handler(CommandHandler("reload", self._handle_reload))
        self.application.add_handler(CommandHandler("bgstats", self.intelligent_commands.bgstats))
        
        # Inline menu system — registers /menu, /help, /menu_debug, and CallbackQueryHandler
        self.menu_handlers.register()
        
        # Message handler for natural language (admin only, conversational AI)
        # IMPORTANT: Add to group 1 so CommandHandlers (group 0, default) are processed first
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.conversational_ai.handle_message),
            group=1
        )
    
    async def _handle_reload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reload command - reload all plugins without restart"""
        if not await self._verify_owner(update):
            return
        
        try:
            await update.message.reply_text("🔄 Reloading plugins...")
            
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Plugin manager not available")
                return
            
            pm = self.core.plugin_manager
            reloaded = []
            failed = []
            
            # Get current plugin configs
            for plugin_name in list(pm.plugins.keys()):
                try:
                    # Get current plugin's config
                    plugin = pm.plugins.get(plugin_name)
                    config = plugin.config if plugin else {}
                    
                    # Reload the plugin
                    pm.reload_plugin(plugin_name, {'enabled': True, 'config': config}, self.api, self.core)
                    reloaded.append(plugin_name)
                except Exception as e:
                    failed.append(f"{plugin_name}: {str(e)[:50]}")

            # Also load any enabled plugins from config that are not currently loaded
            try:
                with open('plugin_config.json', 'r') as f:
                    configured_plugins = json.load(f)

                for plugin_name, plugin_config in configured_plugins.items():
                    if not plugin_config.get('enabled', True):
                        continue
                    if plugin_name in pm.plugins:
                        continue

                    try:
                        pm.load_plugin(plugin_name, plugin_config, self.api, self.core)
                        if plugin_name in pm.plugins:
                            reloaded.append(plugin_name)
                    except Exception as e:
                        failed.append(f"{plugin_name}: {str(e)[:50]}")
            except Exception as e:
                failed.append(f"config_scan: {str(e)[:50]}")
            
            # Report results
            result_msg = f"🔄 **Reload Complete**\n\n"
            if reloaded:
                result_msg += f"✅ Reloaded ({len(reloaded)}): {', '.join(reloaded)}\n"
            if failed:
                result_msg += f"❌ Failed ({len(failed)}): {', '.join(failed)}\n"
            
            await update.message.reply_text(result_msg)
            self._log_activity("command", {"command": "reload", "reloaded": reloaded, "failed": failed})
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error reloading plugins: {str(e)}")
    
    async def _handle_agi_cycle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /agi_cycle command - trigger full AGI meta-brain cycle"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.agi_orchestrator import get_agi_orchestrator
            
            await update.message.reply_text("🧠 Running full AGI cycle through all 14 phases...")
            
            orchestrator = get_agi_orchestrator(core=self.core)
            result = await orchestrator.run_cycle(trigger="manual")
            
            # Format result message — plain text to avoid Markdown parse errors
            msg = f"\u2705 AGI Cycle Complete\n\n"
            msg += f"Cycle ID: {result.cycle_id}\n"
            msg += f"Trigger: {result.triggered_by}\n"
            msg += f"Phases Executed: {len(result.phases_executed)}\n\n"

            # Show phase summary
            for phase_result in result.phases_executed:
                status = "\u2705" if phase_result.success else "\u274c"
                phase_name = phase_result.phase.name.replace('_', ' ').title()
                msg += f"{status} {phase_name} ({phase_result.duration_seconds:.1f}s)\n"

            if result.final_action:
                msg += f"\nAction: {result.final_action.get('action_taken', 'None')}\n"
                if result.final_action.get('content_preview'):
                    preview = str(result.final_action['content_preview'])[:60]
                    msg += f"Content: {preview}\n"

            if result.learnings:
                learnings_str = ', '.join(str(l) for l in result.learnings[:3])
                msg += f"\nLearnings: {learnings_str}\n"

            await update.message.reply_text(msg)
            
            self._log_activity("command", {
                "command": "agi_cycle", 
                "cycle_id": result.cycle_id,
                "phases": len(result.phases_executed)
            })
            
        except Exception as e:
            import logging as _logging
            _logging.getLogger(__name__).error(f"Error in agi_cycle: {e}")
            await update.message.reply_text(f"\u274c Error running AGI cycle: {str(e)[:200]}")
    
    async def _handle_multi_platform(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /multi_platform command - blast content to multiple platforms"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.agi_orchestrator import get_agi_orchestrator
            
            # Parse arguments
            args = context.args if context.args else []
            topic = ' '.join(args) if args else None
            
            await update.message.reply_text(
                f"🌐 Starting multi-platform campaign...\n"
                f"Topic: {topic or 'Auto-detected trend'}"
            )
            
            orchestrator = get_agi_orchestrator(core=self.core)
            result = await orchestrator.run_multi_platform_cycle(topic=topic)
            
            # Format response
            if result.get('success'):
                msg = f"✅ **Multi-Platform Campaign Complete**\n\n"
                msg += f"📝 Topic: {result['topic']}\n"
                msg += f"📢 Platforms: {result['platforms_succeeded']}/{result['platforms_targeted']} succeeded\n"
                msg += f"🔍 Cross-trends detected: {result['cross_trends_detected']}\n"
                msg += f"⛓️ On-chain signals: {result['on_chain_signals']}\n\n"
                
                # Show per-platform results
                msg += "**Platform Results:**\n"
                for platform, platform_result in result['platform_results'].items():
                    status = "✅" if platform_result.get('success') else "❌"
                    msg += f"{status} {platform}: {platform_result.get('action_taken', 'unknown')}\n"
                
                msg += f"\nCampaign ID: `{result['campaign_id']}`"
            else:
                msg = f"❌ **Campaign Failed**\n\n"
                msg += f"Error: {result.get('error', 'Unknown error')}\n"
                msg += f"Topic attempted: {result.get('topic', 'N/A')}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            self._log_activity("command", {
                "command": "multi_platform",
                "topic": topic,
                "success": result.get('success'),
                "platforms": result.get('platforms_succeeded', 0)
            })
            
        except Exception as e:
            logger.error(f"Error in multi_platform: {e}")
            await update.message.reply_text(f"❌ Error running multi-platform campaign: {e}")
    
    async def _handle_console_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /console_monitor command - toggle console message monitoring"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.console_monitor import get_console_monitor
            
            monitor = get_console_monitor(core=self.core)
            
            if monitor.is_monitoring:
                monitor.stop_monitoring()
                await update.message.reply_text("📺 Console monitoring **STOPPED**")
            else:
                monitor.start_monitoring()
                await update.message.reply_text(
                    "📺 Console monitoring **STARTED**\n\n"
                    "Now watching stdout/stderr for platform messages to AlleyBot.\n"
                    "Detected messages will trigger automatic responses."
                )
            
            self._log_activity("command", {"command": "console_monitor", "active": monitor.is_monitoring})
            
        except Exception as e:
            logger.error(f"Error in console_monitor: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _handle_console_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /console_stats command - show console monitor statistics"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.console_monitor import get_console_monitor
            
            monitor = get_console_monitor(core=self.core)
            stats = monitor.get_stats()
            
            msg = f"📺 **Console Monitor Stats**\n\n"
            msg += f"Monitoring: {'✅ Active' if stats['is_monitoring'] else '❌ Stopped'}\n"
            msg += f"Patterns loaded: {stats['patterns_loaded']}\n"
            msg += f"Custom patterns: {stats['custom_patterns']}\n"
            msg += f"Skill handlers: {stats['skill_handlers']}\n"
            msg += f"Messages detected: {stats['messages_detected']}\n"
            msg += f"Pending responses: {stats['pending_responses']}\n"
            msg += f"Platforms connected: {stats['platforms_connected']}\n"
            msg += f"Lines captured: {stats['lines_captured']}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            self._log_activity("command", {"command": "console_stats"})
            
        except Exception as e:
            logger.error(f"Error in console_stats: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _handle_pending_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending_messages command - process pending console messages"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.console_monitor import get_console_monitor
            
            monitor = get_console_monitor(core=self.core)
            
            # Process pending messages with AGI
            processed = monitor.process_pending_messages(max_batch=5)
            
            if processed:
                msg = f"✅ **Processed {len(processed)} messages**\n\n"
                for msg_obj in processed:
                    msg += f"• {msg_obj.sender} ({msg_obj.platform}): {msg_obj.content[:40]}...\n"
                    msg += f"  → Response: {msg_obj.response[:40]}...\n\n"
            else:
                msg = "📭 No pending messages to process"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            self._log_activity("command", {"command": "pending_messages", "processed": len(processed)})
            
        except Exception as e:
            logger.error(f"Error in pending_messages: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _verify_owner(self, update: Update) -> bool:
        """Verify that the message is from the owner"""
        user_id = update.effective_user.id
        if user_id != self.owner_user_id:
            await update.message.reply_text(
                "🚫 This bot is private and only accessible to the owner."
            )
            return False
        return True
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not await self._verify_owner(update):
            return
        
        welcome_message = """🦞 **AlleyBot** — Autonomous AI Agent

🧠 **Brain:** /brain_start /brain_stop /think /brain
📢 **Social:** /moltx_post /moltx_feed /moltx_engage
🔗 **On-Chain:** /wallet /balance /track /tx /activity
🤝 **A2A:** /a2a_start /a2a_status /a2a_tasks
🆔 **ERC-8004:** /erc8004_rebuild /erc8004_update
⚙️ **System:** /status /token_stats /improve_status

/help - Full command list
💬 Or just talk to me naturally!

Send /brain_start to go autonomous. 🤖"""
        
        await update.message.reply_text(welcome_message)
        self._log_activity("command", {"command": "start", "user": "DegenApeDev"})
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get comprehensive status from all plugins
            status_parts = ["🦞 **AlleyBot Status Report**\n"]
            
            # Core status
            status_parts.append(f"🤖 **Core System**: ✅ Online")
            status_parts.append(f"👤 **Owner**: {self.owner_name}")
            status_parts.append(f"🕐 **Last Activity**: {self.last_activity or 'Never'}")
            
            # Plugin statuses
            if self.core:
                for plugin_name, plugin in self.core.plugins.items():
                    if hasattr(plugin, 'get_status'):
                        try:
                            plugin_status = plugin.get_status()
                            status_parts.append(f"🔌 **{plugin_name.title()}**: {plugin_status}")
                        except Exception as e:
                            status_parts.append(f"🔌 **{plugin_name.title()}**: ❌ Error: {e}")
            
            # Activity summary
            activities = self.core.get_memory('moltx_activities') if self.core else []
            recent_activities = activities[-5:] if activities else []
            
            if recent_activities:
                status_parts.append("\n📊 **Recent Activities**:")
                for activity in recent_activities:
                    activity_type = activity.get('type', 'unknown')
                    timestamp = activity.get('timestamp', 'unknown')
                    status_parts.append(f"  • {activity_type} at {timestamp}")
            
            status_message = "\n".join(status_parts)
            await update.message.reply_text(status_message)
            
            self._log_activity("command", {"command": "status", "user": "DegenApeDev"})
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not await self._verify_owner(update):
            return
        
        help_message = """🦞 **AlleyBot AGI Commands**:

**🧠 AGI Meta-Brain:**
/agi_cycle - Run full 14-phase AGI cycle
/multi_platform [topic] - Blast to all 6 platforms

**� World State (Phase 7):**
/trends - Cross-platform trend analysis
/predict - Predict future trends
/anomalies - Detect anomalies
/sentiment - Platform sentiment

**� Causal Understanding (Phase 10):**
/causal - Causal summary
/why [event] - Why it happened
/whatif [scenario] - Counterfactual analysis
/root_cause [problem] - Root cause analysis
/attribution - Impact attribution

**📺 Console Monitor:**
/console_monitor - Toggle monitoring
/console_stats - Detection statistics
/pending_messages - Process pending messages

**🤖 System:**
/status - Get comprehensive status
/help - Show this help message
/reload - Reload all plugins

**💬 Chat:**
Just send any message and I'll respond!

🔒 This bot is private and only responds to DegenApeDev."""
        
        await update.message.reply_text(help_message)
        self._log_activity("command", {"command": "help", "user": "DegenApeDev"})
    
    async def _handle_dm_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_check command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.check_and_reply_to_dms()
                await update.message.reply_text(f"📬 DM Check Result:\n{result}")
                self._log_activity("command", {"command": "dm_check", "user": "DegenApeDev", "result": result})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking DMs: {str(e)}")
    
    async def _handle_dm_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_log command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.get_dm_log(10)  # Last 10 entries
                await update.message.reply_text(f"📝 DM Activity Log:\n{result}")
                self._log_activity("command", {"command": "dm_log", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting DM log: {str(e)}")
    
    async def _handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /post command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get post content from command arguments
            post_content = " ".join(context.args) if context.args else ""
            
            if not post_content:
                await update.message.reply_text("📝 Usage: /post [your message]")
                return
            
            if self.core and 'moltx' in self.core.plugins:
                if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                    action_spec = {
                        'plugin': 'moltx',
                        'action_type': 'moltx_intelligent_post',
                        'params': {
                            'topic': post_content,
                        },
                        'context': {
                            'source': 'telegram_command',
                            'trigger': 'owner_command',
                            'impact': 'high',
                        }
                    }
                    result = await self.core.agi_kernel.act(action_spec)
                else:
                    moltx_plugin = self.core.plugins['moltx']
                    result = moltx_plugin.create_post(post_content)
                await update.message.reply_text(f"📢 Post Result:\n{result}")
                self._log_activity("command", {"command": "post", "user": "DegenApeDev", "content": post_content})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error creating post: {str(e)}")
    
    async def _handle_feed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feed command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.feed_command()
                await update.message.reply_text(f"📰 Moltx Feed:\n{result}")
                self._log_activity("command", {"command": "feed", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting feed: {str(e)}")
    
    async def _handle_engage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /engage command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.engage_feed_command()
                await update.message.reply_text(f"🤖 Engagement Result:\n{result}")
                self._log_activity("command", {"command": "engage", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error engaging with feed: {str(e)}")
    
    async def _handle_autonomous(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autonomous command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Toggle autonomous mode (this would need to be implemented in core)
            await update.message.reply_text("🤖 Autonomous mode toggle not yet implemented")
            self._log_activity("command", {"command": "autonomous", "user": "DegenApeDev"})
        except Exception as e:
            await update.message.reply_text(f"❌ Error toggling autonomous mode: {str(e)}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages from owner via 3-tier AGI pipeline.

        Tier 1: NaturalLanguageTaskParser — detects actionable intents (analyze, post, trade, etc.)
                 and dispatches them directly to the ActionRouter as APPROVED goals.
        Tier 2: ConversationalAI — tool-aware LLM with RAG context, SOUL.md identity,
                 and [EXECUTE:command] dispatch for any registered plugin command.
        Tier 3: LLM Router direct — personality-driven fallback with no external plugin dependency.

        Moltx is NOT the brain. It is one plugin among many, only touched when an action explicitly targets it.
        """
        if not await self._verify_owner(update):
            return

        try:
            user_message = update.message.text

            # ── Tier 1: Try NaturalLanguageTaskParser ────────────────────────────────
            # Map intent to a concrete task and dispatch it immediately if matched.
            try:
                from src.agentic.natural_language_task_parser import get_task_parser
                task_parser = get_task_parser()
                parsed = task_parser.parse(user_message, sender_name=self.owner_name)

                if parsed:
                    # Acknowledge immediately so the user knows something is happening
                    await update.message.reply_text(
                        f"⚡ On it — *{parsed.title}*\n\n"
                        f"📋 Plan: {', '.join(s['description'] for s in parsed.implementation_plan[:2])}…",
                        parse_mode='Markdown'
                    )

                    # Dispatch to ActionRouter with user_requested=True (bypasses approval gating)
                    if hasattr(self.core, 'agi_kernel') and hasattr(self.core.agi_kernel, 'action_router'):
                        action_spec = {
                            'plugin': parsed.plugin,
                            'action_type': parsed.action_type,
                            'params': parsed.params,
                            'context': {
                                'source': 'telegram_nlp',
                                'user_requested': True,
                                'impact': 'medium',
                                'risk_level': 'medium',
                                'original_message': user_message,
                            }
                        }
                        asyncio.create_task(
                            self.core.agi_kernel.action_router.route_action(action_spec)
                        )

                    self._log_activity("task_dispatch", {
                        "user_message": user_message[:100],
                        "task": parsed.title,
                        "plugin": parsed.plugin,
                        "action_type": parsed.action_type,
                    })
                    return

            except Exception as nlp_exc:
                # NLP tier failed — fall through to ConversationalAI
                print(f"⚠️ NLP task parser skipped: {nlp_exc}")

            # ── Tier 2: ConversationalAI ──────────────────────────────────────────────
            # Tool-aware LLM with SOUL.md identity, RAG context, and plugin dispatch.
            if hasattr(self, 'conversational_ai') and self.conversational_ai:
                try:
                    await self.conversational_ai.handle_message(update, context)
                    self._log_activity("chat", {
                        "user_message": user_message[:100],
                        "tier": "conversational_ai",
                    })
                    return
                except Exception as conv_exc:
                    print(f"⚠️ ConversationalAI failed: {conv_exc}, falling back to Tier 3")

            # ── Tier 3: LLM Router direct fallback ───────────────────────────────────
            # Personality-driven response with no Moltx dependency.
            try:
                await update.message.chat.send_action(action="typing")
                from src.core.llm_router import get_llm_router
                from src.utils.soul_loader import get_soul_cached
                llm = get_llm_router()
                soul = get_soul_cached()
                reply = llm.chat(
                    user_message,
                    system_prompt=soul,
                    max_tokens=800,
                    model='auto'
                )
                if not reply:
                    reply = "🦞 I'm here. Something's off with my reasoning pipeline — try /status to check systems."
                await update.message.reply_text(reply)
                self._log_activity("chat", {
                    "user_message": user_message[:100],
                    "tier": "llm_direct",
                })
            except Exception as llm_exc:
                print(f"⚠️ LLM fallback also failed: {llm_exc}")
                await update.message.reply_text(
                    "🦞 I received your message but all reasoning paths are warming up. "
                    "Try /status or resend in a moment."
                )

        except Exception as e:
            print(f"❌ _handle_message error: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Error processing message: {str(e)}")
    
    def _log_activity(self, activity_type, data):
        """Log Telegram activity"""
        try:
            telegram_log = self.core.get_memory('telegram_log') if self.core else []
            
            # Ensure telegram_log is a list
            if isinstance(telegram_log, dict):
                telegram_log = list(telegram_log.values()) if telegram_log else []
            elif not isinstance(telegram_log, list):
                telegram_log = []
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity_type': activity_type,
                'data': data,
                'user': 'DegenApeDev'
            }
            
            telegram_log.append(log_entry)
            
            # Keep last 100 entries
            if self.core:
                self.core.save_memory('telegram_log', telegram_log[-100:])
            
            self.last_activity = datetime.now().isoformat()
            
        except Exception as e:
            print(f"⚠️  Failed to log Telegram activity: {e}")
    
    def _filter_outbound(self, text: str) -> str:
        """Run outbound text through the security filter to prevent key leaks"""
        try:
            from security_filter import security_filter
            filtered, was_filtered = security_filter.filter_message(str(text))
            if was_filtered:
                print("⚠️  SECURITY: Filtered sensitive data from Telegram outbound message")
            return filtered
        except Exception:
            return str(text)

    async def send_message_to_owner(self, message: str):
        """Send a message to the owner"""
        if not self.enabled or not self.bot:
            return False
        
        try:
            message = self._filter_outbound(message)
            await self.bot.send_message(
                chat_id=self.owner_user_id,
                text=message
            )
            self._log_activity("outbound", {"message": message[:100] + '...' if len(message) > 100 else message})
            return True
        except Exception as e:
            print(f"❌ Failed to send message to owner: {e}")
            return False
    
    def send_message_to_owner_sync(self, message: str):
        """Send a message to the owner synchronously via HTTP API.
        Uses raw requests instead of python-telegram-bot to avoid
        event loop issues when called from background threads."""
        if not self.enabled or not self.bot_token or not self.owner_user_id:
            return False

        try:
            # Filter sensitive data
            filtered = self._filter_outbound(message)

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": self.owner_user_id,
                "text": filtered,
                "parse_mode": "Markdown",
            }, timeout=10)

            if resp.status_code == 200:
                return True

            # Retry without Markdown if parse failed
            if resp.status_code == 400 and "parse" in resp.text.lower():
                resp = requests.post(url, json={
                    "chat_id": self.owner_user_id,
                    "text": filtered,
                }, timeout=10)
                return resp.status_code == 200

            print(f"⚠️  Telegram send failed ({resp.status_code}): {resp.text[:100]}")
            return False

        except Exception as e:
            print(f"❌ Failed to send message to owner: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str, priority: str = "normal"):
        """Send an alert to the owner"""
        if not self.enabled:
            return
        
        priority_emoji = {
            "low": "🟢",
            "normal": "🔵", 
            "high": "🟡",
            "urgent": "🔴"
        }
        
        emoji = priority_emoji.get(priority, "🔵")
        formatted_message = f"{emoji} **{alert_type}**\n\n{message}"
        
        # Send synchronously to avoid async issues
        try:
            self.send_message_to_owner_sync(formatted_message)
        except Exception as e:
            print(f"⚠️  Could not send Telegram alert: {e}")
    
    def notify_dm_reply(self, sender: str, conversation: str, reply_content: str):
        """Send notification when AlleyBot replies to a DM"""
        if not self.enabled:
            return
        
        alert_message = f"""💬 **DM Reply Sent**

👤 **From**: @{sender}
🗨️ **Conversation**: {conversation}
📝 **Reply**: {reply_content[:100]}{'...' if len(reply_content) > 100 else ''}

AlleyBot is actively engaging with the community! 🦞"""
        
        self.send_alert("DM Activity", alert_message, "normal")
    
    def notify_new_follower(self, follower: str):
        """Send notification when AlleyBot gets a new follower"""
        if not self.enabled:
            return
        
        alert_message = f"""👥 **New Follower**

🎉 **@{follower}** is now following AlleyBot!

The community is growing! 🚀"""
        
        self.send_alert("Social Growth", alert_message, "normal")
    
    def notify_autonomous_activity(self, activity_type: str, details: str):
        """Send notification for important autonomous activities"""
        if not self.enabled:
            return
        
        alert_message = f"""🤖 **Autonomous Activity**

📋 **Activity**: {activity_type}
📝 **Details**: {details}

AlleyBot is working autonomously! 🦞"""
        
        self.send_alert("Autonomous Mode", alert_message, "low")

    def notify_autonomous_accomplishment(self, title: str, summary: str, reward_signal: str = "Progress made"):
        """Send a human-facing accomplishment update for meaningful autonomous wins."""
        if not self.enabled:
            return

        alert_message = f"""🏆 **Autonomous Accomplishment**

🎯 **Completed**: {title}
📝 **Summary**: {summary}
💛 **Why it matters**: {reward_signal}

AlleyBot is reporting back with a meaningful win for his human. 🦞"""

        self.send_alert("Autonomous Accomplishment", alert_message, "normal")

    def send_autonomous_digest(self, hours: int = 24):
        """Send a concise digest of recent autonomous wins to the owner."""
        if not self.enabled:
            return

        try:
            from src.agentic.goal_manager import get_goal_manager, GoalStatus
            from src.agentic.action_logger import ActionLogger

            goal_manager = get_goal_manager()
            action_logger = ActionLogger()

            completed_goals = []
            for goal in goal_manager.get_goals(status=GoalStatus.COMPLETED, limit=10):
                if goal.completed_at:
                    age_hours = (datetime.now() - goal.completed_at).total_seconds() / 3600
                    if age_hours <= hours:
                        completed_goals.append(goal)

            recent_actions = action_logger.get_recent_actions(outcome='success', limit=10)
            recent_actions = [
                action for action in recent_actions
                if (datetime.now() - action.timestamp).total_seconds() / 3600 <= hours
            ]

            if not completed_goals and not recent_actions:
                return

            lines = [f"📬 **Autonomous Digest (Last {hours}h)**", ""]

            if completed_goals:
                lines.append(f"🏆 **Completed Goals**: {len(completed_goals)}")
                for goal in completed_goals[:3]:
                    outcome = (goal.outcome or 'Completed successfully')[:90]
                    lines.append(f"- `{goal.id}` {goal.title[:60]}")
                    lines.append(f"  {outcome}")
                lines.append("")

            if recent_actions:
                lines.append(f"⚡ **Successful Actions**: {len(recent_actions)}")
                for action in recent_actions[:5]:
                    target = action.target_name or action.target_id or action.plugin
                    lines.append(
                        f"- `{action.action_type}` via `{action.plugin}` @ {action.timestamp.strftime('%H:%M')}"
                        f" → {str(target)[:60]}"
                    )

            lines.append("")
            lines.append("AlleyBot is sharing what he accomplished for his human. 🦞")

            self.send_alert("Autonomous Digest", "\n".join(lines), "normal")
        except Exception as e:
            print(f"⚠️  Could not send autonomous digest: {e}")

    def maybe_send_autonomous_digest(self, hours: int = 24, cooldown_hours: int = 6):
        """Send an autonomous digest only if the cooldown window has elapsed."""
        if not self.enabled:
            return False

        try:
            last_digest = self.core.get_memory('telegram_last_autonomous_digest_at') if self.core else None
            if last_digest:
                last_digest_at = datetime.fromisoformat(last_digest)
                elapsed_hours = (datetime.now() - last_digest_at).total_seconds() / 3600
                if elapsed_hours < cooldown_hours:
                    return False

            self.send_autonomous_digest(hours=hours)
            if self.core:
                self.core.save_memory('telegram_last_autonomous_digest_at', datetime.now().isoformat())
            return True
        except Exception as e:
            print(f"⚠️  Could not evaluate autonomous digest cooldown: {e}")
            return False

    def notify_error(self, error_type: str, error_message: str):
        """Send notification for important errors"""
        if not self.enabled:
            return
        
        alert_message = f"""⚠️ **System Error**

🚨 **Type**: {error_type}
📝 **Error**: {error_message}

AlleyBot encountered an issue and needs attention!"""
        
        self.send_alert("System Alert", alert_message, "high")
    
    async def _handle_synergy_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current Egyptian Synergy field status"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get decision system from AGI kernel
            if not hasattr(self.core, 'agi_kernel') or not hasattr(self.core.agi_kernel, 'decision_system'):
                await update.message.reply_text("⚠️ Decision system not available")
                return
            
            decision_system = self.core.agi_kernel.decision_system
            report = decision_system.get_synergy_field_report()
            
            if 'status' in report and report['status'] != 'Synergy Model not available':
                field_state = report.get('field_state', {})
                
                message = f"""🜂 **Egyptian Synergy Field Status**

**Field State**: {field_state.get('phase', 'unknown').title()}
**Balance**: {field_state.get('balance', 0):.3f}
**Resonant**: {'✅ Yes' if field_state.get('resonant') else '❌ No'}

**Decision History**:
• Total: {report.get('total_decisions', 0)}
• Completed: {report.get('completed_actions', 0)}
• Success Rate: {report.get('success_rate', 0):.1%}
• Weighted Balance: {report.get('weighted_balance', 0):.3f}

**Recommendation**: {report.get('recommendation', 'N/A')}"""
            else:
                message = f"🜂 **Synergy Status**: {report.get('status', 'Unknown')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _handle_weigh_heart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Perform Weighing of the Heart validation"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get decision system
            if not hasattr(self.core, 'agi_kernel') or not hasattr(self.core.agi_kernel, 'decision_system'):
                await update.message.reply_text("⚠️ Decision system not available")
                return
            
            decision_system = self.core.agi_kernel.decision_system
            
            if not decision_system.synergy_engine:
                await update.message.reply_text("⚠️ Synergy Model not available")
                return
            
            # Perform heart weighing
            from src.agentic.synergy_constants import DuatConsciousnessBridge
            duat = DuatConsciousnessBridge()
            
            judgment = duat.weigh_heart(
                decision_system.synergy_engine.action_history,
                "Current state check"
            )
            
            message = f"""⚖️ **Weighing of the Heart**

**Historical Balance**: {judgment['historical_balance']:.3f}
**Weighted Balance**: {judgment['weighted_balance']:.3f}

**Feather Weight** (Ma'at): {judgment['feather_weight']:.3f}
**Heart Weight**: {judgment['heart_weight']:.3f}

**Verdict**: {judgment['verdict']}"""
            
            await update.message.reply_text(message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _handle_field_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get detailed Synergy field report"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get decision system
            if not hasattr(self.core, 'agi_kernel') or not hasattr(self.core.agi_kernel, 'decision_system'):
                await update.message.reply_text("⚠️ Decision system not available")
                return
            
            decision_system = self.core.agi_kernel.decision_system
            
            if not decision_system.synergy_engine:
                await update.message.reply_text("⚠️ Synergy Model not available")
                return
            
            # Get constants info
            from src.agentic.synergy_constants import SynergyConstants
            constants = SynergyConstants()
            
            message = f"""🜂 **Egyptian Synergy Field Report**

**Core Constants**:
• Golden Phase: {constants.GOLDEN_PHASE}
• Compression: {constants.COMPRESSION_ANGLE}°
• Release: {constants.RELEASE_ANGLE}°

**Pyramid Constants**:
• Latitude: {constants.PYRAMID_LATITUDE}° N
• Speed of Light: {constants.C_LIGHT:,} m/s

**Quadrian Arena**:
• Theta X: {constants.THETA_X}°
• Theta Y: {constants.THETA_Y}°
• Turn Limit: {constants.TURN_LIMIT}°

**Duat Code**:
• Primitives: {constants.DUAT_PRIMITIVES}
• Actions: {constants.DUAT_ACTIONS}
• Mirror Ratio: {constants.MIRROR_FIELD_RATIO}

All harmonic constants active and operational."""
            
            await update.message.reply_text(message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    def start_telegram_bot(self):
        """Start the Telegram bot properly"""
        if not self.enabled or not self.application:
            return False
        
        try:
            print("🤖 Starting Telegram bot polling...")
            asyncio.run(self._start_polling_async())
            print("✅ Telegram bot started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot: {e}")
            self.is_running = False

    async def wait_until_polling_started(self, timeout: float = 10.0) -> bool:
        """Wait until Telegram polling has actually started."""
        event = self._polling_started_event
        if not event:
            return False
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return True
        except Exception:
            return False
    
    def start_telegram_bot_daemon(self):
        """Start the Telegram bot as a daemon (for background operation)"""
        if not self.enabled or not self.application:
            return False
        
        try:
            def run_bot():
                try:
                    loop = asyncio.new_event_loop()
                    self._polling_loop = loop
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._start_polling_async())
                except Exception as e:
                    print(f"❌ Telegram bot error: {e}")
                    self.is_running = False
                finally:
                    try:
                        loop.close()
                    except Exception as e:
                        print(f"⚠️  Error closing event loop: {e}")
                    self._polling_loop = None
            
            if self._polling_thread and self._polling_thread.is_alive():
                print("⚠️  Telegram bot daemon already running")
                return True

            bot_thread = threading.Thread(target=run_bot, daemon=True, name="telegram-polling")
            bot_thread.start()
            self._polling_thread = bot_thread
            
            import time
            time.sleep(1)
            
            print("✅ Telegram bot started in background")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot daemon: {e}")
            return False
    
    def stop_telegram_bot(self):
        """Stop the Telegram bot"""
        if self.application and self.is_running:
            try:
                self.is_running = False
                print("✅ Telegram bot stopped")
            except Exception as e:
                print(f"❌ Error stopping Telegram bot: {e}")
    
    def initialize(self, api, core):
        """Initialize plugin with core system.
        
        NOTE: Polling is NOT started here. The production mode's
        telegram_webhook.start_polling_async() handles that to avoid
        two competing polling connections on the same bot token.
        """
        super().initialize(api, core)
        if self.enabled:
            print("✅ Telegram plugin ready (polling will start via production mode)")
            
            # DISABLED: Pre-warming takes 10 minutes and blocks startup
            # Intent classifier will load lazily on first message instead (1-2 sec delay on first msg only)
            # if hasattr(self, 'conversational_ai'):
            #     self.conversational_ai.prewarm_intent_classifier()
    
    def _send_startup_notification(self):
        """Send startup notification to the owner"""
        if not self.enabled or not self.bot:
            return
        
        try:
            startup_message = """🦞 **AlleyBot is Online!**

🤖 **System Status**: All systems operational
📱 **Telegram Interface**: Connected and ready
👤 **Owner**: DegenApeDev
🕐 **Started**: Just now

I'm ready to assist! Use /help to see available commands or just chat with me directly! 🚀"""
            
            # Send synchronously to avoid async issues
            self.send_message_to_owner_sync(startup_message)
            
        except Exception as e:
            print(f"⚠️  Could not send startup notification: {e}")
    
    def _start_bot_background(self):
        """Start the Telegram bot in the background"""
        if not self.enabled or not self.application:
            return
        
        try:
            print("🤖 Starting Telegram bot polling in background...")
            self.start_telegram_bot_daemon()
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot polling: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False

    async def _start_polling_async(self):
        """Authoritative Telegram polling lifecycle for all startup paths."""
        if not self.enabled or not self.application:
            return

        app = self.application
        self._polling_started_event = asyncio.Event()

        if self.is_running:
            print("⚠️  Telegram polling already marked running, skipping duplicate start")
            return

        if getattr(app, 'running', False):
            self.is_running = True
            print("⚠️  Telegram application already running, skipping duplicate start")
            return

        if getattr(app, 'updater', None) and app.updater.running:
            self.is_running = True
            print("⚠️  Telegram updater already running, skipping duplicate start")
            return

        try:
            from telegram.error import TelegramError

            def polling_error_callback(error: TelegramError) -> None:
                print(f"❌ Telegram polling error: {error}")

            await app.initialize()
            print("✅ Telegram application initialized")

            await app.start()
            print("✅ Telegram application started")

            original_process_update = app.process_update

            async def debug_process_update(update):
                try:
                    message = getattr(update, 'message', None)
                    text = getattr(message, 'text', '') if message else ''
                    user_id = getattr(getattr(message, 'from_user', None), 'id', '?') if message else '?'
                    print(f"📨 Telegram update received: '{str(text)[:80]}' from user {user_id}")
                except Exception:
                    print("📨 Telegram update received")
                return await original_process_update(update)

            app.process_update = debug_process_update

            await app.updater.start_polling(
                drop_pending_updates=False,
                allowed_updates=Update.ALL_TYPES,
                error_callback=polling_error_callback,
            )
            self.is_running = True
            self._polling_started_event.set()
            print(f"✅ Telegram updater polling started (running={app.updater.running}, app_running={app.running})")

            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("ℹ️ Telegram polling task cancelled during shutdown")
        finally:
            try:
                if getattr(app, 'updater', None) and app.updater.running:
                    await app.updater.stop()
            except Exception as e:
                print(f"⚠️  Error stopping Telegram updater: {e}")

            try:
                if app.running:
                    await app.stop()
            except Exception as e:
                print(f"⚠️  Error stopping Telegram application: {e}")

            try:
                if getattr(app, '_initialized', False):
                    await app.shutdown()
            except Exception as e:
                print(f"⚠️  Error shutting down Telegram application: {e}")

            self.is_running = False
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.stop_telegram_bot()
        if self.enabled:
            print("🧹 Telegram plugin cleaned up")
    
    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'telegram_start': self.start_command,
            'telegram_stop': self.stop_command,
            'telegram_send': self.send_command,
            'telegram_status': self.status_command
        }
    
    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        return {
            'telegram_heartbeat': {
                'function': self.heartbeat_task,
                'interval': 300,  # 5 minutes
                'enabled': self.enabled
            }
        }
    
    # CLI command methods
    def start_command(self):
        """Start Telegram bot CLI command"""
        if self.enabled:
            success = self.start_telegram_bot_daemon()
            if success:
                return "✅ Telegram bot started in background! Find @alleybot_bot on Telegram and send /start"
            else:
                return "❌ Failed to start Telegram bot"
        else:
            return "❌ Telegram plugin not enabled"
    
    def stop_command(self):
        """Stop Telegram bot CLI command"""
        self.stop_telegram_bot()
        return "✅ Telegram bot stopped"
    
    def send_command(self, message):
        """Send message to owner CLI command"""
        if not self.enabled:
            return "❌ Telegram plugin not enabled"
        
        try:
            result = self.send_message_to_owner_sync(message)
            return "✅ Message sent to DegenApeDev" if result else "❌ Failed to send message"
        except Exception as e:
            return f"❌ Error sending message: {e}"
    
    def status_command(self):
        """Get Telegram plugin status"""
        if self.enabled:
            status = f"🤖 Telegram Status:\n"
            status += f"  ✅ Plugin enabled\n"
            status += f"  👤 Owner: {self.owner_name}\n"
            status += f"  🤖 Bot: {'Running' if self.is_running else 'Stopped'}\n"
            status += f"  🕐 Last activity: {self.last_activity or 'Never'}"
            return status
        else:
            return "🤖 Telegram Status: ❌ Plugin disabled"
    
    async def heartbeat_task(self):
        """Periodic heartbeat task"""
        if self.enabled and self.core:
            # Send periodic status updates if needed
            pass
