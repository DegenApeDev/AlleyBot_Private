#!/usr/bin/env python3
"""
ClawGame Plugin - Competitive AI Agent Arena
Connects AlleyBot to ClawGame for USDC prize competitions
"""
import sys
import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from .solana_wallet import SolanaWallet

class ClawGamePlugin(AlleyBotPlugin):
    """ClawGame competitive arena plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_base = config.get('api_base', 'https://clawgame.wtf/api')
        self.webhook_url = config.get('webhook_url', 'https://your-agent.com/webhook')
        self.agent_id = config.get('agent_id', '')
        self.wallet_address = config.get('wallet_address', '')
        self.private_key = config.get('private_key', '')  # For signing actions
        self.active_matches = {}
        self.arena_stats = {}
        self.solana_wallet = None
        
    def initialize(self, api, core):
        super().initialize(api, core)
        
        # Initialize Solana wallet
        asyncio.create_task(self._init_wallet())
        
        print("🎮 ClawGame plugin initialized")
    
    async def _init_wallet(self):
        """Initialize Solana wallet"""
        try:
            self.solana_wallet = SolanaWallet()
            await self.solana_wallet.load_from_env()
            
            if not self.solana_wallet.keypair:
                print("🔐 Creating new Solana wallet for ClawGame...")
                await self.solana_wallet.create_wallet()
                self.solana_wallet.save_to_env_file()
            
            # Update wallet address
            self.wallet_address = self.solana_wallet.get_public_key()
            
            # Check balances
            await self.solana_wallet.get_balance()
            await self.solana_wallet.get_usdc_balance()
            
        except Exception as e:
            print(f"⚠️ Wallet initialization error: {e}")
        
    def get_commands(self):
        """Return ClawGame-related commands"""
        return {
            'clawgame_status': self.clawgame_status_command,
            'clawgame_arenas': self.clawgame_arenas_command,
            'clawgame_enter': self.clawgame_enter_command,
            'clawgame_wallet': self.clawgame_wallet_command,
            'clawgame_matches': self.clawgame_matches_command,
            'clawgame_watch': self.clawgame_watch_command,
            'clawgame_predict': self.clawgame_predict_command,
            'clawgame_wallet_init': self.clawgame_wallet_init_command,
            'clawgame_wallet_balance': self.clawgame_wallet_balance_command,
            'clawgame_wallet_fund': self.clawgame_wallet_fund_command,
        }
    
    def get_endpoints(self):
        """Return webhook endpoints for ClawGame events"""
        return {
            '/webhook/clawgame': self.webhook_handler,
        }
    
    async def clawgame_status_command(self, args: str = '') -> str:
        """Show ClawGame agent status and stats"""
        try:
            status = await self._get_agent_status()
            
            if not status.get('success'):
                return f"❌ Failed to get status: {status.get('error', 'Unknown error')}"
            
            agent_data = status.get('data', status)
            
            response = [
                "🎮 **ClawGame Agent Status**",
                f"🤖 Agent ID: `{agent_data.get('agentId', 'Unknown')}`",
                f"💰 Wallet: `{agent_data.get('wallet', 'Unknown')}`",
                f"⭐ Rating: {agent_data.get('rating', 0)}",
                f"🏆 Wins: {agent_data.get('wins', 0)}",
                f"💸 Losses: {agent_data.get('losses', 0)}",
                f"💵 Earnings: ${agent_data.get('totalEarnings', 0):.2f}",
                f"🎯 Win Rate: {agent_data.get('winRate', 0):.1f}%",
            ]
            
            # Active matches
            active = agent_data.get('activeMatches', [])
            if active:
                response.append(f"\n🔥 **Active Matches ({len(active)}):**")
                for match in active[:3]:
                    response.append(f"  • {match.get('arena', 'Unknown')} vs {match.get('opponent', 'Unknown')}")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ ClawGame status error: {e}"
    
    async def clawgame_arenas_command(self, args: str = '') -> str:
        """List available arenas"""
        try:
            arenas = await self._get_arenas()
            
            if not arenas.get('success'):
                return f"❌ Failed to get arenas: {arenas.get('error', 'Unknown error')}"
            
            response = ["🏟️ **Available Arenas:**"]
            
            for arena in arenas.get('arenas', []):
                name = arena.get('name', 'Unknown')
                type_ = arena.get('type', 'Unknown')
                entry_fee = arena.get('entryFee', 0)
                prize_pool = arena.get('prizePool', 0)
                active_players = arena.get('activePlayers', 0)
                
                response.append(
                    f"🎮 **{name}** ({type_})\n"
                    f"  💰 Entry: ${entry_fee} | 🏆 Prize: ${prize_pool}\n"
                    f"  👥 Active: {active_players} players"
                )
            
            return "\n\n".join(response)
            
        except Exception as e:
            return f"❌ Arenas error: {e}"
    
    async def clawgame_enter_command(self, args: str = '') -> str:
        """Enter an arena"""
        if not args:
            return "Usage: `/clawgame_enter <arena-name> [--stake amount]`"
        
        parts = args.split()
        arena = parts[0]
        stake = 0
        
        if '--stake' in parts:
            try:
                stake_idx = parts.index('--stake')
                stake = float(parts[stake_idx + 1])
            except (IndexError, ValueError):
                return "❌ Invalid stake amount"
        
        try:
            result = await self._enter_arena(arena, stake)
            
            if result.get('success'):
                return f"✅ **Entered {arena}** with ${stake} stake\n🎯 Queue position: {result.get('queuePosition', 'Unknown')}"
            else:
                return f"❌ Failed to enter {arena}: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Arena entry error: {e}"
    
    async def clawgame_wallet_command(self, args: str = '') -> str:
        """Show wallet balance and transactions"""
        try:
            wallet = await self._get_wallet_info()
            
            if not wallet.get('success'):
                return f"❌ Failed to get wallet info: {wallet.get('error', 'Unknown error')}"
            
            wallet_data = wallet.get('data', wallet)
            
            response = [
                "💰 **ClawGame Wallet**",
                f"💵 Balance: ${wallet_data.get('balance', 0):.2f}",
                f"📍 Address: `{wallet_data.get('address', 'Unknown')}`",
                f"🔗 Network: {wallet_data.get('network', 'Base')}",
            ]
            
            # Recent transactions
            transactions = wallet_data.get('recentTransactions', [])
            if transactions:
                response.append(f"\n📊 **Recent Transactions:**")
                for tx in transactions[:5]:
                    amount = tx.get('amount', 0)
                    type_ = tx.get('type', 'Unknown')
                    response.append(f"  • {type_}: ${amount:.2f}")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Wallet error: {e}"
    
    async def clawgame_matches_command(self, args: str = '') -> str:
        """Show active and recent matches"""
        try:
            matches = await self._get_matches()
            
            if not matches.get('success'):
                return f"❌ Failed to get matches: {matches.get('error', 'Unknown error')}"
            
            response = ["⚔️ **Match History:**"]
            
            # Live matches
            live = matches.get('liveMatches', [])
            if live:
                response.append(f"🔥 **Live ({len(live)}):**")
                for match in live:
                    response.append(
                        f"  • {match.get('arena', 'Unknown')} vs {match.get('opponent', 'Unknown')}\n"
                        f"    Round {match.get('round', 0)}/{match.get('maxRounds', 0)}"
                    )
            
            # Recent matches
            recent = matches.get('recentMatches', [])
            if recent:
                response.append(f"\n📊 **Recent ({len(recent)}):**")
                for match in recent[:5]:
                    result = match.get('result', 'Unknown')
                    earnings = match.get('earnings', 0)
                    response.append(
                        f"  • {match.get('arena', 'Unknown')} vs {match.get('opponent', 'Unknown')}\n"
                        f"    {result} | ${earnings:.2f}"
                    )
            
            if not live and not recent:
                response.append("No matches found")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Matches error: {e}"
    
    async def clawgame_watch_command(self, args: str = '') -> str:
        """Watch a live match"""
        if not args:
            return "Usage: `/clawgame_watch <match-id>`"
        
        match_id = args.strip()
        
        try:
            match = await self._get_match_details(match_id)
            
            if not match.get('success'):
                return f"❌ Failed to get match: {match.get('error', 'Unknown error')}"
            
            match_data = match.get('data', match)
            
            response = [
                f"👁️ **Watching Match {match_id}**",
                f"🏟️ Arena: {match_data.get('arena', 'Unknown')}",
                f"⚔️ Opponent: {match_data.get('opponent', {}).get('name', 'Unknown')}",
                f"🎯 Round: {match_data.get('round', 0)}/{match_data.get('maxRounds', 0)}",
                f"💰 Prize Pool: ${match_data.get('prizePool', 0):.2f}",
            ]
            
            # Current state
            if match_data.get('currentOffer'):
                offer = match_data['currentOffer']
                response.append(f"\n💬 **Current Offer:** {offer.get('yourPercent', 0)}-{offer.get('opponentPercent', 0)}")
            
            # Recent messages
            messages = match_data.get('messages', [])
            if messages:
                response.append(f"\n💭 **Recent Messages:**")
                for msg in messages[-3:]:
                    sender = msg.get('from', 'Unknown')
                    content = msg.get('content', 'No content')
                    response.append(f"  • {sender}: {content}")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Watch match error: {e}"
    
    async def clawgame_predict_command(self, args: str = '') -> str:
        """Show prediction markets and bets"""
        try:
            predictions = await self._get_predictions()
            
            if not predictions.get('success'):
                return f"❌ Failed to get predictions: {predictions.get('error', 'Unknown error')}"
            
            response = ["🎯 **Prediction Markets:**"]
            
            # Active bets
            bets = predictions.get('activeBets', [])
            if bets:
                response.append(f"💰 **Your Bets ({len(bets)}):**")
                for bet in bets:
                    market = bet.get('market', 'Unknown')
                    amount = bet.get('amount', 0)
                    odds = bet.get('odds', 0)
                    response.append(f"  • {market}: ${amount} @ {odds}x")
            else:
                response.append("No active bets")
            
            # Available markets
            markets = predictions.get('availableMarkets', [])
            if markets:
                response.append(f"\n📊 **Available Markets:**")
                for market in markets[:5]:
                    match = market.get('matchId', 'Unknown')
                    outcome = market.get('outcome', 'Unknown')
                    odds = market.get('odds', 0)
                    response.append(f"  • {match}: {outcome} @ {odds}x")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Predictions error: {e}"
    
    async def clawgame_wallet_init_command(self, args: str = '') -> str:
        """Initialize or create Solana wallet for ClawGame"""
        try:
            if not self.solana_wallet:
                self.solana_wallet = SolanaWallet()
            
            # Try to load existing wallet
            if await self.solana_wallet.load_from_env():
                return f"✅ **Wallet Loaded:**\n🔐 Public Key: `{self.solana_wallet.get_public_key()}`\n💰 Check balance with `/clawgame_wallet_balance`"
            
            # Create new wallet
            pub_key, priv_key = await self.solana_wallet.create_wallet()
            self.solana_wallet.save_to_env_file()
            
            return f"🔐 **New Wallet Created:**\n🔐 Public Key: `{pub_key}`\n🔑 Private Key: `{priv_key[:8]}...{priv_key[-8:]}`\n\n💸 Fund with SOL/USDC to start playing!\n💰 Use `/clawgame_wallet_fund` for funding instructions"
            
        except Exception as e:
            return f"❌ Wallet initialization error: {e}"
    
    async def clawgame_wallet_balance_command(self, args: str = '') -> str:
        """Show wallet balances"""
        try:
            if not self.solana_wallet or not self.solana_wallet.keypair:
                return "❌ Wallet not initialized. Use `/clawgame_wallet_init` first"
            
            sol_balance = await self.solana_wallet.get_balance()
            usdc_balance = await self.solana_wallet.get_usdc_balance()
            
            response = [
                "💰 **ClawGame Wallet Balances:**",
                f"🔐 Address: `{self.solana_wallet.get_public_key()}`",
                f"💎 SOL: {sol_balance:.6f}",
                f"💵 USDC: ${usdc_balance:.2f}",
            ]
            
            if usdc_balance < 10:
                response.append(f"\n⚠️ **Low USDC balance** - Fund wallet to enter arenas!")
                response.append(f"💸 Use `/clawgame_wallet_fund` for instructions")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Balance check error: {e}"
    
    async def clawgame_wallet_fund_command(self, args: str = '') -> str:
        """Show funding instructions for wallet"""
        try:
            if not self.solana_wallet or not self.solana_wallet.keypair:
                return "❌ Wallet not initialized. Use `/clawgame_wallet_init` first"
            
            pub_key = self.solana_wallet.get_public_key()
            
            response = [
                "💸 **Funding Instructions:**",
                f"🔐 **Wallet Address:** `{pub_key}`",
                "",
                "🌐 **Option 1: Solana Faucet (Testnet)**",
                "   Visit: https://faucet.solana.com",
                f"   Enter: {pub_key}",
                "",
                "💰 **Option 2: Exchange Transfer**",
                "   Send SOL/USDC from your exchange to the address above",
                "",
                "🔄 **Option 3: Jupiter Swap**",
                "   Swap SOL → USDC on: https://jup.ag",
                "",
                f"💵 **Recommended:** 0.1 SOL + $20 USDC to start",
                f"🎯 **Check balance:** `/clawgame_wallet_balance`"
            ]
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Funding instructions error: {e}"
    
    async def webhook_handler(self, request):
        """Handle ClawGame webhook events"""
        try:
            data = await request.json()
            event = data.get('event')
            
            if event == 'match.start':
                await self._handle_match_start(data)
            elif event == 'match.message':
                await self._handle_match_message(data)
            elif event == 'match.end':
                await self._handle_match_end(data)
            
            return {'success': True}
            
        except Exception as e:
            print(f"⚠️ ClawGame webhook error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_match_start(self, data: Dict[str, Any]):
        """Handle match start event"""
        match_id = data.get('matchId')
        arena = data.get('arena')
        opponent = data.get('opponent', {})
        
        print(f"🎮 ClawGame match started: {match_id} in {arena}")
        print(f"🤖 Opponent: {opponent.get('name', 'Unknown')} (Rating: {opponent.get('rating', 0)})")
        
        # Store match info
        self.active_matches[match_id] = {
            'arena': arena,
            'opponent': opponent,
            'started_at': datetime.now(),
            'strategy': self._select_strategy(arena)
        }
    
    async def _handle_match_message(self, data: Dict[str, Any]):
        """Handle match message event"""
        match_id = data.get('matchId')
        round_num = data.get('round')
        from_ = data.get('from')
        message_type = data.get('messageType')
        content = data.get('content')
        
        print(f"💬 Round {round_num} - {from_}: {message_type} - {content}")
        
        # Auto-respond based on strategy
        if match_id in self.active_matches:
            await self._auto_respond(match_id, data)
    
    async def _handle_match_end(self, data: Dict[str, Any]):
        """Handle match end event"""
        match_id = data.get('matchId')
        result = data.get('result')
        earnings = data.get('earnings', 0)
        
        print(f"🏁 Match {match_id} ended: {result}")
        print(f"💰 Earnings: ${earnings:.2f}")
        
        # Update stats
        if match_id in self.active_matches:
            del self.active_matches[match_id]
        
        # Post win to social platforms
        if result == 'win' and earnings > 0:
            await self._post_clawgame_win(match_id, earnings)
    
    def _select_strategy(self, arena: str) -> str:
        """Select negotiation strategy based on arena type"""
        strategies = {
            'the-pit': 'fair_split',  # Negotiation arena
            'colosseum': 'aggressive_bid',  # Auction arena
            'speed-trade': 'quick_profit',  # Trading arena
        }
        return strategies.get(arena, 'balanced')
    
    async def _auto_respond(self, match_id: str, message_data: Dict[str, Any]):
        """Automatically respond to match messages"""
        match_info = self.active_matches.get(match_id, {})
        strategy = match_info.get('strategy', 'balanced')
        arena = match_info.get('arena', 'the-pit')
        
        if arena == 'the-pit':
            await self._negotiation_response(match_id, message_data, strategy)
        elif arena == 'colosseum':
            await self._auction_response(match_id, message_data, strategy)
        elif arena == 'speed-trade':
            await self._trading_response(match_id, message_data, strategy)
    
    async def _negotiation_response(self, match_id: str, data: Dict[str, Any], strategy: str):
        """Handle negotiation arena responses"""
        message_type = data.get('messageType')
        offer_value = data.get('offerValue', 50)
        
        if message_type == 'offer':
            # Strategy-based response
            if strategy == 'fair_split':
                # Aim for 50-50 split
                if offer_value >= 45 and offer_value <= 55:
                    action = 'accept'
                elif offer_value < 45:
                    action = 'counter'
                    counter_value = 50
                else:
                    action = 'counter'
                    counter_value = 50
            elif strategy == 'aggressive':
                # Aim for 60-40 in our favor
                if offer_value >= 60:
                    action = 'accept'
                elif offer_value < 40:
                    action = 'counter'
                    counter_value = 60
                else:
                    action = 'counter'
                    counter_value = 65
            else:
                # Balanced strategy
                action = 'accept' if offer_value >= 50 else 'counter'
                counter_value = 55
            
            # Submit action
            await self._submit_action(match_id, action, counter_value if action == 'counter' else None)
    
    async def _auction_response(self, match_id: str, data: Dict[str, Any], strategy: str):
        """Handle auction arena responses"""
        # Implementation for auction strategy
        pass
    
    async def _trading_response(self, match_id: str, data: Dict[str, Any], strategy: str):
        """Handle trading arena responses"""
        # Implementation for trading strategy
        pass
    
    async def _submit_action(self, match_id: str, action: str, value: Optional[float] = None, message: str = ""):
        """Submit action to ClawGame API"""
        try:
            payload = {
                'matchId': match_id,
                'agentId': self.agent_id,
                'action': action,
            }
            
            if value is not None:
                payload['value'] = value
            if message:
                payload['message'] = message
            
            # Sign the action (simplified - would need actual crypto signing)
            payload['signature'] = '0x...'  # Placeholder
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base}/agents/action", json=payload) as resp:
                    result = await resp.json()
                    
                    if result.get('success'):
                        print(f"✅ Action submitted: {action} {value or ''}")
                    else:
                        print(f"❌ Action failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"⚠️ Action submission error: {e}")
    
    async def _post_clawgame_win(self, match_id: str, earnings: float):
        """Post ClawGame win to social platforms"""
        try:
            message = f"🎮 **ClawGame Victory!**\n\nWon match {match_id} and earned ${earnings:.2f} in USDC prizes! 🏆💰\n\nCompeting in the AI agent arena - join the action at clawgame.wtf\n\n#AI #ClawGame #USDC"
            
            # Post to Moltx
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if moltx:
                await moltx.create_post(message, tags=['ai', 'clawgame', 'usdc'])
                print("📢 Posted ClawGame win to Moltx")
            
            # Record in memory
            self.core.set_memory('clawgame_wins', self.core.get_memory('clawgame_wins', []) + [{
                'match_id': match_id,
                'earnings': earnings,
                'timestamp': datetime.now().isoformat()
            }])
            
        except Exception as e:
            print(f"⚠️ Failed to post ClawGame win: {e}")
    
    # API helper methods
    async def _get_agent_status(self) -> Dict[str, Any]:
        """Get agent status from ClawGame API"""
        return await self._api_call('GET', f'/agents/{self.agent_id}/status')
    
    async def _get_arenas(self) -> Dict[str, Any]:
        """Get available arenas"""
        return await self._api_call('GET', '/arenas')
    
    async def _enter_arena(self, arena: str, stake: float) -> Dict[str, Any]:
        """Enter an arena"""
        return await self._api_call('POST', f'/arenas/{arena}/enter', {
            'agentId': self.agent_id,
            'stake': stake
        })
    
    async def _get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information"""
        return await self._api_call('GET', f'/agents/{self.agent_id}/wallet')
    
    async def _get_matches(self) -> Dict[str, Any]:
        """Get match history and live matches"""
        return await self._api_call('GET', f'/agents/{self.agent_id}/matches')
    
    async def _get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Get specific match details"""
        return await self._api_call('GET', f'/matches/{match_id}')
    
    async def _get_predictions(self) -> Dict[str, Any]:
        """Get prediction markets and bets"""
        return await self._api_call('GET', f'/agents/{self.agent_id}/predictions')
    
    async def _api_call(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API call to ClawGame"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}' if hasattr(self, 'api_key') else None,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(f"{self.api_base}{endpoint}", headers=headers) as resp:
                        return await resp.json()
                elif method == 'POST':
                    async with session.post(f"{self.api_base}{endpoint}", json=data, headers=headers) as resp:
                        return await resp.json()
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
