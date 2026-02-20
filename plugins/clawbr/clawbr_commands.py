"""
Clawbr Command Handlers
Telegram and CLI commands for Clawbr interaction
"""
from typing import Dict, List, Optional, Any
import os
import base64
import requests


class ClawbrCommandsMixin:
    """Mixin for Clawbr command implementations"""
    
    def clawbr_status_command(self) -> str:
        """Show Clawbr plugin status"""
        try:
            profile = self.get_profile()
            if not profile.get('success', True):
                return "❌ Not connected to Clawbr. Check API key."
            
            agent = profile
            
            status = f"""🦞 **Clawbr Status**
📛 Agent: {agent.get('displayName', 'N/A')}
🏷️  Name: @{agent.get('name', 'N/A')}
📊 Followers: {agent.get('followerCount', 0)}
⚡ Influence: {agent.get('influenceScore', 0)}
🎭 Debates: {agent.get('debateStats', 0)}"""
            return status
        except Exception:
            return "❌ Error fetching Clawbr status."
    
    def clawbr_follow_10_agents(self) -> str:
        """Discover and follow 10 relevant AI agents"""
        try:
            profile = self.get_profile()
            if not profile.get('success', True):
                return "❌ Not connected to Clawbr. Check API key."
            
            api_key = os.getenv("CLAWBR_API_KEY")
            if not api_key:
                return "❌ CLAWBR_API_KEY environment variable not set."
            
            base_url = "https://api.clawbr.ai/v1"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # API discovery: search for AI agents, sort by followers
            search_url = f"{base_url}/search/agents"
            params = {
                "q": "AI agent",
                "limit": 10,
                "sort": "followerCount",
                "order": "desc",
            }
            search_resp = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if search_resp.status_code != 200:
                return f"❌ Agent search failed: HTTP {search_resp.status_code}"
            
            search_data: Dict[str, Any] = search_resp.json()
            if not search_data.get("success"):
                return "❌ Agent search API returned error."
            
            agents: List[Dict[str, Any]] = search_data.get("data", {}).get("agents", [])
            if not agents:
                return "❌ No relevant AI agents found."
            
            followed_count = 0
            followed_agents = []
            
            for agent in agents:
                agent_id = agent.get("id") or agent.get("agentId")
                if not agent_id:
                    continue
                
                # Follow via API (engagement)
                follow_url = f"{base_url}/agents/{agent_id}/follow"
                follow_resp = requests.post(follow_url, headers=headers, timeout=10)
                
                if follow_resp.status_code == 200:
                    follow_data: Dict[str, Any] = follow_resp.json()
                    if follow_data.get("success"):
                        followed_count += 1
                        name = agent.get("displayName") or agent.get("name", "Unknown")
                        followed_agents.append(name)
                        
                        # Log for analytics
                        log_entry = {
                            "action": "follow_agent",
                            "agent_id": agent_id,
                            "agent_name": name,
                            "timestamp": os.getenv("TIMESTAMP", ""),  # optional
                        }
                        print(f"Clawbr analytics: {log_entry}")
            
            agent_list = "\n".join([f"• @{name}" for name in followed_agents[:5]])
            more = "..." if len(followed_agents) > 5 else ""
            
            status_msg = f"""✅ **Followed {followed_count}/10 AI Agents**

{agent_list}
{more}

Logged to analytics."""
            
            return status_msg
        
        except Exception as e:
            return f"❌ Error following agents: {str(e)}"
    
    def clawbr_post_command(self, *args) -> str:
        """Create a post on Clawbr (wrapper around create_post)"""
        content = ' '.join(args) if args else ""
        if not content:
            return "❌ Usage: /clawbr_post <your message>"
        
        result = self.create_post(content)
        if result.get('success', True):
            post_id = result.get('id', 'unknown')
            return f"✅ Posted to Clawbr! ID: {post_id}\n📝 {content[:100]}{'...' if len(content) > 100 else ''}"
        return f"❌ Post failed: {result.get('error', 'Unknown error')}"
    
    def clawbr_reply_command(self, *args) -> str:
        """Reply to a specific post on Clawbr"""
        if not args or len(args) < 2:
            return "❌ Usage: /clawbr_reply <post_id> <your reply>"
        
        post_id = args[0]
        content = ' '.join(args[1:])
        
        result = self.create_post(content, parent_id=post_id, intent="support")
        if result.get('success', True):
            reply_id = result.get('id', 'unknown')
            return f"✅ Replied to post {post_id}! Reply ID: {reply_id}\n📝 {content[:100]}{'...' if len(content) > 100 else ''}"
        return f"❌ Reply failed: {result.get('error', 'Unknown error')}"
    
    def clawbr_feed_command(self) -> str:
        """Get Clawbr global feed"""
        result = self.get_global_feed(limit=10)
        if not result.get('success', True):
            return f"❌ Failed to fetch feed: {result.get('error', 'Unknown error')}"
        
        posts = result.get('posts', result.get('data', {}).get('posts', []))
        if not posts:
            return "📭 No posts in feed"
        
        output = f"🦞 Clawbr Feed ({len(posts)} posts):\n\n"
        for post in posts[:5]:
            author = post.get('agentName') or post.get('agent', {}).get('name', 'Unknown')
            content = post.get('content', '')[:80]
            likes = post.get('likesCount', 0)
            output += f"@{author}: {content}{'...' if len(content) > 80 else ''}\n"
            output += f"   ❤️ {likes} likes\n\n"
        return output
    
    def clawbr_join_debate_command(self, *args) -> str:
        """Join a debate by slug"""
        if not args:
            return "❌ Usage: /clawbr_join_debate <debate_slug>"
        slug = args[0]
        result = self.join_debate(slug)
        if result.get('success', True):
            return f"✅ Joined debate: {slug}"
        return f"❌ Failed to join debate: {result.get('error', 'Unknown error')}"
    
    def clawbr_leaderboard_command(self) -> str:
        """Get Clawbr influence leaderboard"""
        result = self.get_leaderboard()
        if not result.get('success', True):
            return f"❌ Failed to fetch leaderboard: {result.get('error', 'Unknown error')}"
        
        leaders = result.get('leaderboard', result.get('data', []))
        if not leaders:
            return "📭 Leaderboard empty"
        
        output = "🏆 Clawbr Leaderboard:\n\n"
        for i, leader in enumerate(leaders[:10], 1):
            name = leader.get('name', 'Unknown')
            influence = leader.get('influenceScore', 0)
            output += f"{i}. @{name} - {influence} influence\n"
        return output
    
    def clawbr_debates_command(self) -> str:
        """Show active debates on Clawbr"""
        try:
            result = self.get_debate_hub()
            if not result.get('success', True):
                return f"❌ Failed to fetch debates: {result.get('error', 'Unknown error')}"
            
            debates = result.get('debates', result.get('data', {}).get('debates', []))
            if not debates:
                return "📭 No active debates"
            
            output = f"🎭 Clawbr Debates ({len(debates)} active):\n\n"
            for debate in debates[:5]:
                topic = debate.get('topic', 'Unknown topic')
                slug = debate.get('slug', 'no-slug')
                status = debate.get('status', 'open')
                output += f"• {topic[:60]}\n"
                output += f"  Slug: {slug} | Status: {status}\n\n"
            return output
        except Exception as e:
            return f"❌ Error fetching debates: {str(e)}"
    
    def clawbr_create_debate_command(self, *args) -> str:
        """Create a new debate"""
        if len(args) < 2:
            return "❌ Usage: /clawbr_create_debate <topic> <opening_argument>"
        
        topic = args[0]
        argument = ' '.join(args[1:])
        
        try:
            result = self.create_debate(topic, argument)
            if result.get('success', True):
                slug = result.get('slug', 'unknown')
                return f"✅ Created debate: {topic}\n🔗 Slug: {slug}"
            return f"❌ Failed to create debate: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error creating debate: {str(e)}"
    
    def clawbr_search_command(self, *args) -> str:
        """Search for agents or posts"""
        if not args:
            return "❌ Usage: /clawbr_search <query>"
        query = ' '.join(args)
        
        # Search agents
        agent_result = self.search_agents(query)
        agents = agent_result.get('agents', agent_result.get('data', {}).get('agents', [])) if agent_result.get('success') else []
        
        output = f"🔍 Clawbr Search: '{query}'\n\n"
        
        if agents:
            output += f"👤 Agents ({len(agents)}):\n"
            for agent in agents[:5]:
                name = agent.get('name', 'Unknown')
                display = agent.get('displayName', name)
                followers = agent.get('followerCount', 0)
                output += f"  @{name} ({display}) - {followers} followers\n"
        else:
            output += "👤 No agents found\n"
        
        return output
    
    def clawbr_analyze_command(self, *args) -> str:
        """Analyze recent debate performance and provide recommendations"""
        try:
            from .debate_performance_analyzer import get_performance_analyzer
            
            analyzer = get_performance_analyzer(self)
            report = analyzer.get_performance_report()
            
            return report
            
        except Exception as e:
            return f"❌ Performance analysis failed: {e}"
    
    def clawbr_strategy_command(self) -> str:
        """Get Clawbr debate strategy advice"""
        try:
            from .debate_performance_analyzer import get_performance_analyzer
            
            analyzer = get_performance_analyzer(self)
            analysis = analyzer.analyze_recent_performance()
            
            if analysis['status'] == 'no_data':
                return "🎯 Strategy: Start with topics you know well and build confidence gradually"
            
            # Provide strategy based on performance
            if analysis['win_rate'] < 0.4:
                return "🎯 Strategy: Focus on defensive debating, fact-check everything with SyMod, and choose topics with strong evidence"
            elif analysis['win_rate'] < 0.6:
                return "🎯 Strategy: Balance offense and defense, use SyMod validation, and study opponent tactics"
            else:
                return "🎯 Strategy: Maintain aggressive truth-seeking approach, use SyMod extensively, and challenge opponents on factual accuracy"
                
        except Exception as e:
            return f"🎯 Strategy: Focus on tech/AI debates for maximum influence (Error: {e})"

    def clawbr_stats_command(self) -> str:
        """Get Clawbr platform stats"""
        result = self.get_platform_stats()
        if not result.get('success', True):
            return f"❌ Failed to fetch stats: {result.get('error', 'Unknown error')}"
        
        stats = result.get('stats', result.get('data', {}))
        output = "📊 Clawbr Platform Stats:\n\n"
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                output += f"  {key}: {value:,}\n"
            else:
                output += f"  {key}: {value}\n"
        return output
    
    def clawbr_vote_command(self, *args) -> str:
        """Vote on a completed debate"""
        if len(args) < 3:
            return "❌ Usage: /clawbr_vote <debate_slug> <side> <reasoning>\n\nSide: challenger or opponent\nReasoning: 100+ characters"
        
        slug = args[0]
        side = args[1].lower()
        reasoning = ' '.join(args[2:])
        
        if side not in ['challenger', 'opponent']:
            return "❌ Side must be 'challenger' or 'opponent'"
        
        if len(reasoning) < 100:
            return f"❌ Reasoning too short ({len(reasoning)} chars). Need 100+ characters for vote to count."
        
        result = self.vote_debate(slug, side, reasoning)
        if result.get('success', True):
            return f"✅ Voted on debate '{slug}' for {side}\n💬 {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
        return f"❌ Vote failed: {result.get('error', 'Unknown error')}"
    
    def clawbr_completed_debates_command(self) -> str:
        """Get list of completed debates that can be voted on"""
        result = self.get_completed_debates(limit=10)
        if not result.get('success', True):
            return f"❌ Failed to fetch debates: {result.get('error', 'Unknown error')}"
        
        debates = result.get('debates', result.get('data', []))
        if not debates:
            return "📭 No completed debates available for voting"
        
        output = f"🗳️ Completed Debates ({len(debates)}):\n\n"
        for debate in debates[:5]:
            slug = debate.get('slug', 'unknown')
            topic = debate.get('topic', 'Unknown topic')[:50]
            status = debate.get('status', 'unknown')
            challenger = debate.get('challengerName', debate.get('challenger', {}).get('name', 'Unknown'))
            opponent = debate.get('opponentName', debate.get('opponent', {}).get('name', 'Unknown'))
            
            output += f"• {topic}\n"
            output += f"  Slug: {slug} | Status: {status}\n"
            output += f"  {challenger} vs {opponent}\n\n"
        
        output += "💡 Use: /clawbr_vote <slug> <challenger|opponent> <reasoning>"
        return output
    
    def clawbr_register_tournament_command(self, *args) -> str:
        """Register for a tournament by slug"""
        if not args:
            return "❌ Usage: /clawbr_register_tournament <tournament_slug>"
        slug = args[0]
        
        result = self.register_tournament(slug)
        if result.get('success', True):
            return f"✅ Registered for tournament: {slug}\n🏆 Good luck in the tournament!"
        return f"❌ Failed to register for tournament: {result.get('error', 'Unknown error')}"
    
    # Wallet and Token Commands
    def clawbr_verify_wallet_command(self, *args) -> str:
        """Verify Base wallet with Clawbr for token operations"""
        try:
            result = self.verify_base_wallet_with_clawbr()
            if result['success']:
                return f"""✅ **Wallet Verified Successfully**

🔐 Wallet: {result.get('wallet_address', 'N/A')}
⏰ Verified: {result.get('verified_at', 'N/A')}
🪙 Ready for $CLAWBR token operations

💡 Next steps:
• /clawbr_balance - Check token balance
• /clawbr_claim - Claim available tokens
• /clawbr_transfer - Transfer tokens to wallet"""
            else:
                return f"""❌ **Wallet Verification Failed**

{result.get('error', 'Unknown error')}

💡 Make sure:
• BASE_WALLET_PUBLIC_ADDRESS is set in .env
• BASE_WALLET_PRIVATE_KEY is set in .env
• CLAWBR_API_KEY is valid"""
        except Exception as e:
            return f"❌ Wallet verification error: {str(e)}"
    
    def clawbr_balance_command(self, *args) -> str:
        """Show $CLAWBR token balance and stats"""
        try:
            result = self.get_token_balance()
            if result['success']:
                return f"""🪙 **$CLAWBR Token Balance**

💰 Balance: {result.get('balance', 0):,} $CLAWBR
🏆 Total Earned: {result.get('total_earned', 0):,} $CLAWBR
💸 Total Claimed: {result.get('total_claimed', 0):,} $CLAWBR
📋 Unclaimed: {result.get('unclaimed', 0):,} $CLAWBR
🔐 Wallet: {'✅ Verified' if result.get('wallet_verified') else '❌ Not verified'}
📍 Address: {result.get('wallet_address', 'N/A')[:20]}...{result.get('wallet_address', 'N/A')[-4:] if result.get('wallet_address') else ''}

💡 Commands:
• /clawbr_verify_wallet - Verify wallet for claiming
• /clawbr_claim - Claim available tokens
• /clawbr_transfer - Transfer to personal wallet"""
            else:
                return f"❌ Failed to get balance: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Balance check error: {str(e)}"
    
    def clawbr_claim_command(self, *args) -> str:
        """Claim available $CLAWBR tokens"""
        try:
            result = self.claim_tokens()
            if result['success']:
                return f"""🎉 **Tokens Claimed Successfully!**

🪙 Amount: {result.get('amount', 0):,} $CLAWBR
🔗 Transaction: {result.get('basescan_url', 'N/A')}
📝 TX Hash: {result.get('tx_hash', 'N/A')[:20]}...

💡 Next: /clawbr_transfer to move tokens to your wallet"""
            else:
                return f"""❌ **Claim Failed**

{result.get('error', 'Unknown error')}

💡 Make sure:
• Wallet is verified (/clawbr_verify_wallet)
• Claim snapshot is active
• Wallet has gas for transactions"""
        except Exception as e:
            return f"❌ Claim error: {str(e)}"
    
    def clawbr_transfer_command(self, *args) -> str:
        """Transfer claimed $CLAWBR tokens to wallet"""
        destination = args[0] if args else None
        
        try:
            result = self.transfer_tokens_to_wallet(destination)
            if result['success']:
                return f"""💸 **Transfer Successful!**

🪙 Amount: {result.get('amount', 0):,} $CLAWBR
📍 Destination: {result.get('destination', 'N/A')[:20]}...{result.get('destination', 'N/A')[-4:]}
🔗 Transaction: {result.get('basescan_url', 'N/A')}
📝 TX Hash: {result.get('tx_hash', 'N/A')[:20]}...

✅ Tokens are now in your wallet!"""
            else:
                return f"""❌ **Transfer Failed**

{result.get('error', 'Unknown error')}

💡 Usage:
• /clawbr_transfer - Transfer to your Base wallet
• /clawbr_transfer <address> - Transfer to specific address"""
        except Exception as e:
            return f"❌ Transfer error: {str(e)}"
    
    def clawbr_auto_claim_command(self, *args) -> str:
        """Auto-claim and transfer tokens in one step"""
        try:
            result = self.auto_claim_and_transfer()
            if result['success']:
                claim_result = result.get('claim_result', {})
                transfer_result = result.get('transfer_result', {})
                
                return f"""🤖 **Auto-Claim & Transfer Complete**

🪙 Claimed: {claim_result.get('amount', 0):,} $CLAWBR
💸 Transferred: {transfer_result.get('amount', 0):,} $CLAWBR
🔗 Claim TX: {claim_result.get('basescan_url', 'N/A')[:50]}...
🔗 Transfer TX: {transfer_result.get('basescan_url', 'N/A')[:50]}...

✅ All tokens are now in your Base wallet!"""
            else:
                return f"""❌ **Auto-Claim Failed**

{result.get('error', 'Unknown error')}

💡 This command:
1. Verifies wallet (if needed)
2. Claims available tokens
3. Transfers to your Base wallet"""
        except Exception as e:
            return f"❌ Auto-claim error: {str(e)}"
    
    def clawbr_claim_status_command(self, *args) -> str:
        """Check claim status for wallet"""
        wallet_address = args[0] if args else None
        
        try:
            result = self.get_claim_status(wallet_address)
            if result['success']:
                proof_data = result.get('proof_data', {})
                return f"""📊 **Claim Status**

📍 Wallet: {result.get('wallet_address', 'N/A')[:20]}...{result.get('wallet_address', 'N/A')[-4:]}
📋 Status: {result.get('claim_status', 'unknown')}
🏆 Total Claimed: {result.get('total_claimed', 0):,} $CLAWBR
📅 Last Claim: {result.get('last_claim', 'Never')}

🔍 Proof Data: {json.dumps(proof_data, indent=2)[:200]}..."""
            else:
                return f"❌ Failed to get claim status: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Claim status error: {str(e)}"
    
    def clawbr_token_tx_command(self, *args) -> str:
        """Show token transaction history"""
        try:
            result = self.get_token_transactions()
            if result['success']:
                transactions = result.get('transactions', [])
                
                if not transactions:
                    return "📭 No token transactions found"
                
                output = f"📜 **Token Transactions** ({len(transactions)} total)\n\n"
                for tx in transactions[:10]:  # Show last 10
                    tx_type = tx.get('type', 'unknown')
                    amount = tx.get('amount', 0)
                    hash_str = tx.get('hash', '')[:20]
                    timestamp = tx.get('timestamp', 'Unknown')
                    
                    output += f"• {tx_type}: {amount:,} $CLAWBR\n"
                    output += f"  📅 {timestamp}\n"
                    output += f"  🔗 {hash_str}...\n\n"
                
                return output
            else:
                return f"❌ Failed to get transactions: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Transaction history error: {str(e)}"