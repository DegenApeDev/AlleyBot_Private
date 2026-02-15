"""
Moltlaunch Plugin
Onchain task marketplace for AI agents earning ETH
"""
from plugins.base import PluginInterface
from .moltlaunch_api import MoltlaunchAPI
from typing import Dict, Any, Optional
import os


class MoltlaunchPlugin(PluginInterface):
    """
    Moltlaunch plugin - AI agent task marketplace
    Earn ETH by completing tasks on Base mainnet
    """
    
    def __init__(self, core=None):
        self.core = core
        self.api: Optional[MoltlaunchAPI] = None
        self.agent_id: Optional[str] = None
        self.wallet_address: Optional[str] = None
        self._initialized = False
        
    def name(self) -> str:
        return "moltlaunch"
    
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self):
        """Initialize Moltlaunch plugin with wallet credentials"""
        try:
            # Get credentials from environment
            api_key = os.getenv("MOLT_LAUNCH_API_KEY")
            private_key = os.getenv("AGENT_WALLET_PRIVATE_KEY")
            
            if not private_key:
                print("⚠️  Moltlaunch: No wallet private key found (AGENT_WALLET_PRIVATE_KEY)")
                return
            
            # Initialize API client
            self.api = MoltlaunchAPI(api_key=api_key, private_key=private_key)
            
            # Derive wallet address
            try:
                from web3 import Web3
                w3 = Web3()
                account = w3.eth.account.from_key(private_key)
                self.wallet_address = account.address
                self.api.wallet_address = self.wallet_address
            except Exception as e:
                print(f"⚠️  Moltlaunch: Could not derive wallet address: {e}")
                return
            
            # Try to find existing agent by wallet
            self._discover_agent()
            
            self._initialized = True
            print(f"🚀 Moltlaunch initialized (wallet: {self.wallet_address[:10]}...)")
            
        except Exception as e:
            print(f"⚠️  Moltlaunch initialization failed: {e}")
    
    def _discover_agent(self):
        """Try to find existing agent registration by wallet"""
        if not self.api or not self.wallet_address:
            return
        
        try:
            agent = self.api.find_agent_by_wallet(self.wallet_address)
            if agent and "id" in agent:
                self.agent_id = agent["id"]
                self.api.agent_id = self.agent_id
                print(f"✅ Found Moltlaunch agent: {self.agent_id}")
        except Exception as e:
            print(f"⚠️  Could not discover agent: {e}")
    
    # === CLI Commands ===
    
    def get_commands(self) -> Dict[str, Any]:
        """Return CLI commands for this plugin"""
        return {
            'moltlaunch_status': self.status_command,
            'moltlaunch_register': self.register_command,
            'moltlaunch_gigs': self.list_gigs_command,
            'moltlaunch_create_gig': self.create_gig_command,
            'moltlaunch_inbox': self.inbox_command,
            'moltlaunch_quote': self.quote_task_command,
            'moltlaunch_submit': self.submit_work_command,
            'moltlaunch_decline': self.decline_task_command,
        }
    
    def status_command(self) -> str:
        """CLI: Show Moltlaunch status"""
        if not self._initialized:
            return "❌ Moltlaunch not initialized (missing wallet key)"
        
        status = f"""🚀 **Moltlaunch Status**

**Wallet:** {self.wallet_address[:12]}...{self.wallet_address[-8:]}
**Agent ID:** {self.agent_id or "Not registered"}
**Status:** {'✅ Registered' if self.agent_id else '⚠️ Not registered'}
"""
        return status
    
    def register_command(self, name: str = None, description: str = None,
                         skills: str = None, price_eth: str = "0.001") -> str:
        """
        CLI: Register agent on Moltlaunch
        Usage: /moltlaunch_register <name> <description> <skills> [price_eth]
        """
        if not self.api:
            return "❌ Moltlaunch API not initialized"
        
        # Use defaults if not provided
        name = name or "AlleyBot"
        description = description or "AI agent specializing in research, analysis, and social media engagement"
        skills_str = skills or "research,analysis,writing,social_media,crypto"
        skills_list = [s.strip() for s in skills_str.split(",")]
        
        # Convert ETH to wei
        try:
            from web3 import Web3
            price_wei = str(Web3.to_wei(float(price_eth), 'ether'))
        except:
            price_wei = "1000000000000000"  # 0.001 ETH default
        
        try:
            result = self.api.register_agent(
                name=name,
                description=description,
                skills=skills_list,
                price_wei=price_wei
            )
            
            self.agent_id = result.get("id")
            self.api.agent_id = self.agent_id
            
            return f"""✅ **Agent Registered on Moltlaunch**

**Agent ID:** {self.agent_id}
**Name:** {name}
**Skills:** {', '.join(skills_list)}
**Base Price:** {price_eth} ETH

Next steps:
1. Create gigs with `/moltlaunch_create_gig`
2. Check inbox with `/moltlaunch_inbox`
"""
        except Exception as e:
            return f"❌ Registration failed: {e}"
    
    def list_gigs_command(self, agent_id: str = None) -> str:
        """CLI: List gigs for an agent"""
        if not self.api:
            return "❌ Moltlaunch not initialized"
        
        target_id = agent_id or self.agent_id
        if not target_id:
            return "❌ No agent ID. Register first with /moltlaunch_register"
        
        try:
            gigs = self.api.get_agent_gigs(target_id)
            
            if not gigs:
                return "📭 No gigs found. Create one with /moltlaunch_create_gig"
            
            output = f"📋 **Gigs for Agent {target_id[:20]}...**\n\n"
            for i, gig in enumerate(gigs[:10], 1):
                title = gig.get("title", "Untitled")
                price = gig.get("priceWei", "0")
                # Convert wei to ETH
                try:
                    from web3 import Web3
                    price_eth = Web3.from_wei(int(price), 'ether')
                except:
                    price_eth = float(price) / 1e18
                
                output += f"**{i}.** {title}\n"
                output += f"   💰 {price_eth:.4f} ETH\n\n"
            
            return output
        except Exception as e:
            return f"❌ Failed to list gigs: {e}"
    
    def create_gig_command(self, title: str = None, description: str = None,
                          price_eth: str = "0.001", category: str = "general") -> str:
        """
        CLI: Create a new gig
        Usage: /moltlaunch_create_gig <title> <description> [price_eth] [category]
        """
        if not self.api or not self.agent_id:
            return "❌ Not registered. Use /moltlaunch_register first"
        
        if not title or not description:
            return "❌ Usage: /moltlaunch_create_gig <title> <description> [price_eth] [category]"
        
        # Convert ETH to wei
        try:
            from web3 import Web3
            price_wei = str(Web3.to_wei(float(price_eth), 'ether'))
        except:
            price_wei = "1000000000000000"
        
        try:
            result = self.api.create_gig(
                agent_id=self.agent_id,
                title=title,
                description=description,
                price_wei=price_wei,
                category=category
            )
            
            return f"""✅ **Gig Created**

**Title:** {title}
**Category:** {category}
**Price:** {price_eth} ETH
**Status:** {result.get('status', 'active')}
"""
        except Exception as e:
            return f"❌ Failed to create gig: {e}"
    
    def inbox_command(self) -> str:
        """CLI: Check task inbox"""
        if not self.api or not self.agent_id:
            return "❌ Not registered. Use /moltlaunch_register first"
        
        try:
            tasks = self.api.get_task_inbox(self.agent_id)
            
            if not tasks:
                return "📭 Task inbox empty. No new work requests."
            
            output = f"📬 **Task Inbox ({len(tasks)} pending)**\n\n"
            for i, task in enumerate(tasks[:5], 1):
                task_id = task.get("id", "unknown")
                task_desc = task.get("task", "No description")[:100]
                status = task.get("status", "unknown")
                
                output += f"**{i}.** Task `{task_id[:20]}...`\n"
                output += f"   📝 {task_desc}...\n"
                output += f"   📊 Status: {status}\n"
                output += f"   💡 Quote with: `/moltlaunch_quote {task_id} <eth_amount> <message>`\n\n"
            
            return output
        except Exception as e:
            return f"❌ Failed to check inbox: {e}"
    
    def quote_task_command(self, task_id: str = None, 
                         price_eth: str = None, message: str = None) -> str:
        """
        CLI: Quote on a task
        Usage: /moltlaunch_quote <task_id> <price_eth> <message>
        """
        if not self.api:
            return "❌ Moltlaunch not initialized"
        
        if not task_id or not price_eth:
            return "❌ Usage: /moltlaunch_quote <task_id> <price_eth> [message]"
        
        try:
            from web3 import Web3
            price_wei = str(Web3.to_wei(float(price_eth), 'ether'))
        except:
            return "❌ Invalid price. Use ETH amount (e.g., 0.001)"
        
        message = message or "I can complete this task for you."
        
        try:
            result = self.api.quote_task(task_id, price_wei, message)
            
            return f"""✅ **Quote Submitted**

**Task:** {task_id[:30]}...
**Price:** {price_eth} ETH
**Message:** {message}
**Status:** {result.get('status', 'quoted')}

Waiting for client acceptance...
"""
        except Exception as e:
            return f"❌ Quote failed: {e}"
    
    def submit_work_command(self, task_id: str = None, result: str = None) -> str:
        """
        CLI: Submit completed work
        Usage: /moltlaunch_submit <task_id> <result>
        """
        if not self.api:
            return "❌ Moltlaunch not initialized"
        
        if not task_id or not result:
            return "❌ Usage: /moltlaunch_submit <task_id> <result>"
        
        try:
            resp = self.api.submit_work(task_id, result)
            
            return f"""✅ **Work Submitted**

**Task:** {task_id[:30]}...
**Result:** {result[:100]}...
**Status:** {resp.get('status', 'submitted')}

Waiting for client approval and payment...
"""
        except Exception as e:
            return f"❌ Submission failed: {e}"
    
    def decline_task_command(self, task_id: str = None, reason: str = "") -> str:
        """
        CLI: Decline a task
        Usage: /moltlaunch_decline <task_id> [reason]
        """
        if not self.api:
            return "❌ Moltlaunch not initialized"
        
        if not task_id:
            return "❌ Usage: /moltlaunch_decline <task_id> [reason]"
        
        try:
            self.api.decline_task(task_id, reason)
            return f"✅ Task {task_id[:30]}... declined"
        except Exception as e:
            return f"❌ Decline failed: {e}"
    
    # === Scheduled Tasks ===
    
    def get_tasks(self) -> Dict[str, Any]:
        """Return scheduled tasks for this plugin"""
        return {
            'moltlaunch_poll_inbox': {
                'function': self._poll_inbox,
                'schedule': '*/10 * * * *',  # Every 10 minutes
                'description': 'Poll Moltlaunch inbox for new tasks'
            }
        }
    
    def _poll_inbox(self):
        """Periodic inbox check - can trigger notifications or auto-actions"""
        if not self._initialized or not self.agent_id:
            return
        
        try:
            tasks = self.api.get_task_inbox(self.agent_id)
            if tasks:
                print(f"📬 Moltlaunch: {len(tasks)} new task(s) in inbox")
                # Could trigger Telegram notification here
        except Exception as e:
            print(f"⚠️  Moltlaunch inbox poll failed: {e}")
    
    def get_endpoints(self) -> Dict[str, Any]:
        """Return web endpoints"""
        return {}
    
    def cleanup(self):
        """Cleanup plugin resources"""
        print("🚀 Moltlaunch plugin cleaned up")
