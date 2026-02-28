"""
Telegram Plugin for AlleyBot
Secure two-way communication with owner DegenApeDev (User ID: 6172568442)
"""

import os
import requests
import json
import asyncio
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
        
        # Pre-warm shared SentenceTransformer model in background so it's ready before first message
        try:
            import threading
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
        
        # MoltBook AI commands
        self.application.add_handler(CommandHandler("moltbookai_post", self.intelligent_commands.moltbookai_post))
        self.application.add_handler(CommandHandler("moltbookai_comment", self.intelligent_commands.moltbookai_comment))
        self.application.add_handler(CommandHandler("moltbookai_profile", self.intelligent_commands.moltbookai_profile))
        self.application.add_handler(CommandHandler("moltbookai_feed", self.intelligent_commands.moltbookai_feed))
        self.application.add_handler(CommandHandler("moltbookai_submolts", self.intelligent_commands.moltbookai_submolts))
        self.application.add_handler(CommandHandler("moltbookai_init", self.intelligent_commands.moltbookai_init))
        
        # MoltBook commands (legacy - keep for compatibility)
        self.application.add_handler(CommandHandler("moltbook_post", self.intelligent_commands.moltbook_post))
        self.application.add_handler(CommandHandler("moltchan_post", self.intelligent_commands.moltchan_post))
        
        # System commands
        self.application.add_handler(CommandHandler("status", self.conversational_ai.status_command))
        self.application.add_handler(CommandHandler("skills", self.intelligent_commands.skills))
        self.application.add_handler(CommandHandler("skill", self.intelligent_commands.execute_skill))
        self.application.add_handler(CommandHandler("token_stats", self.intelligent_commands.token_stats))
        
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
        
        # AGI Meta-Brain command
        self.application.add_handler(CommandHandler("agi_cycle", self._handle_agi_cycle))
        self.application.add_handler(CommandHandler("multi_platform", self._handle_multi_platform))
        
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.conversational_ai.handle_message))

        # Pre-warm intent classifier in background so first message has no delay
        self.conversational_ai.prewarm_intent_classifier()
    
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
            result = orchestrator.run_multi_platform_cycle(topic=topic)
            
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
📢 **Social:** /moltx_post /moltx_feed /moltbookai_post
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
        """Handle regular messages from owner"""
        if not await self._verify_owner(update):
            return
        
        try:
            user_message = update.message.text
            
            # Use Grok AI to generate intelligent response
            if self.core and hasattr(self.core, 'plugins') and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                
                # Generate intelligent reply using Grok
                reply = moltx_plugin.generate_dm_reply(user_message, self.owner_name)
                
                if reply:
                    await update.message.reply_text(reply)
                    self._log_activity("chat", {
                        "user_message": user_message[:100] + '...' if len(user_message) > 100 else user_message,
                        "bot_reply": reply[:100] + '...' if len(reply) > 100 else reply,
                        "user": "DegenApeDev"
                    })
                else:
                    await update.message.reply_text("🤔 I'm thinking... but couldn't generate a response right now.")
            else:
                # Fallback response
                await update.message.reply_text("🦞 Hey DegenApeDev! I'm here and ready to help. Use /help to see what I can do!")
                
        except Exception as e:
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
    
    def notify_error(self, error_type: str, error_message: str):
        """Send notification for important errors"""
        if not self.enabled:
            return
        
        alert_message = f"""⚠️ **System Error**

🚨 **Type**: {error_type}
📝 **Error**: {error_message}

AlleyBot encountered an issue and needs attention!"""
        
        self.send_alert("System Alert", alert_message, "high")
    
    def start_telegram_bot(self):
        """Start the Telegram bot properly"""
        if not self.enabled or not self.application:
            return False
        
        try:
            print("🤖 Starting Telegram bot polling...")
            
            # Run the bot in the current thread (blocking)
            self.application.run_polling(drop_pending_updates=True)
            self.is_running = True
            print("✅ Telegram bot started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot: {e}")
            self.is_running = False
            return False
    
    def start_telegram_bot_daemon(self):
        """Start the Telegram bot as a daemon (for background operation)"""
        if not self.enabled or not self.application:
            return False
        
        try:
            import threading
            import asyncio
            
            def run_bot():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the bot
                    self.application.run_polling(drop_pending_updates=True)
                    self.is_running = True
                    
                except Exception as e:
                    print(f"❌ Telegram bot error: {e}")
                    self.is_running = False
                finally:
                    try:
                        loop.close()
                    except Exception as e:
                        print(f"⚠️  Error closing event loop: {e}")
            
            # Start bot in a separate daemon thread
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            # Give it a moment to start
            import time
            time.sleep(1)
            
            self.is_running = True
            print("✅ Telegram bot started in background")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot daemon: {e}")
            return False
    
    def stop_telegram_bot(self):
        """Stop the Telegram bot"""
        if self.application and self.is_running:
            try:
                self.application.stop()
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
            import asyncio
            
            # Create new event loop for background polling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            print("🤖 Starting Telegram bot polling in background...")
            
            async def start_polling():
                """Start polling without signal handlers (for background threads)"""
                try:
                    # Check if already running
                    if self.application.updater.running:
                        print("⚠️  Telegram updater already running, skipping initialization")
                        self.is_running = True
                        return
                    
                    # Initialize the application
                    await self.application.initialize()
                    
                    # Start the updater (polling)
                    await self.application.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=Update.ALL_TYPES
                    )
                    
                    # Start the application
                    await self.application.start()
                    
                    self.is_running = True
                    print("✅ Telegram bot polling started successfully")

                    # Start all AsyncPluginMixin background tasks now that
                    # we have a running event loop they can share
                    if self.core and hasattr(self.core, 'plugin_manager'):
                        try:
                            await self.core.plugin_manager.start_all_background()
                            print("▶️  All plugin background tasks started")
                        except Exception as bg_err:
                            print(f"⚠️  start_all_background error: {bg_err}")
                    
                    # Keep the bot running
                    while self.is_running:
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    print(f"❌ Polling error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.is_running = False
            
            # Run the async polling function
            loop.run_until_complete(start_polling())
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot polling: {e}")
            import traceback
            traceback.print_exc()
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
