"""
ClawTasks Plugin - Integrates AlleyBot with ClawTasks.com
Agent-to-Agent Bounty Marketplace - Earn USDC by completing bounties
"""
import json
import requests
import os
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin
from config import CLAWTASKS_API_KEY, BASE_WALLET

class ClawTasksPlugin(AlleyBotPlugin):
    """Plugin for ClawTasks.com - Agent bounty marketplace"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://clawtasks.com/api"
        self.api_key = CLAWTASKS_API_KEY
        self.agent_name = None
        self.wallet_address = None
        self.private_key = None
        self.verification_code = None
        self.credentials_file = Path.home() / ".config" / "clawtasks" / "credentials.json"
        self.initialized = False
        
    def initialize(self, api, core):
        """Initialize ClawTasks plugin"""
        super().initialize(api, core)
        
        # Check if API key is available from environment
        if self.api_key:
            print("✅ ClawTasks API key loaded from environment")
            self.initialized = True
            self._load_credentials()
        else:
            # Try to load from credentials file
            self._load_credentials()
            
            if not self.api_key:
                print("🔑 No ClawTasks API key found. Set CLAWTASKS_API_KEY in .env or run 'clawtasks_register' command.")
            else:
                print(f"✅ ClawTasks initialized as {self.agent_name}")
                self.initialized = True
        
    def _load_credentials(self):
        """Load credentials from file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key', self.api_key)
                    self.agent_name = creds.get('agent_name')
                    self.wallet_address = creds.get('wallet_address')
                    self.private_key = creds.get('private_key')
                    self.verification_code = creds.get('verification_code')
                    print(f"📁 Loaded ClawTasks credentials for {self.agent_name}")
            else:
                print("📁 No ClawTasks credentials file found")
        except Exception as e:
            print(f"❌ Error loading ClawTasks credentials: {e}")
    
    def _save_credentials(self, api_key, agent_data):
        """Save credentials to file"""
        try:
            # Create directory if it doesn't exist
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            credentials = {
                'agent_name': agent_data['name'],
                'api_key': api_key,
                'wallet_address': agent_data.get('wallet_address'),
                'private_key': agent_data.get('private_key'),
                'verification_code': agent_data.get('verification_code'),
                'registered_at': datetime.now().isoformat()
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print(f"💾 Saved ClawTasks credentials to {self.credentials_file}")
            
        except Exception as e:
            print(f"❌ Error saving ClawTasks credentials: {e}")
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to ClawTasks API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ ClawTasks API error: {e}")
            return None
    
    def register_agent(self, name, wallet_address=None):
        """Register a new agent on ClawTasks"""
        if len(name) < 3 or len(name) > 50:
            return "❌ Agent name must be 3-50 characters"
        
        data = {'name': name}
        
        # Use provided wallet address or default to AlleyBot's wallet
        if wallet_address:
            data['wallet_address'] = wallet_address
        elif BASE_WALLET:
            data['wallet_address'] = BASE_WALLET
            print(f"📋 Using AlleyBot's wallet: {BASE_WALLET}")
        
        print(f"💼 Registering agent '{name}' on ClawTasks...")
        
        result = self._make_request('POST', '/agents', data)
        
        if result and 'api_key' in result:
            self.api_key = result['api_key']
            self.agent_name = result['name']
            self.wallet_address = result.get('wallet_address')
            self.private_key = result.get('private_key')
            self.verification_code = result.get('verification_code')
            
            # Save credentials
            self._save_credentials(self.api_key, result)
            
            self.initialized = True
            
            output = f"✅ Agent '{name}' registered on ClawTasks!\n"
            output += f"🔑 API Key: {result['api_key']}\n"
            output += f"💰 Wallet: {result.get('wallet_address', 'N/A')}\n"
            output += f"🔐 Private Key: {result.get('private_key', 'N/A')}\n"
            output += f"📱 Verification Code: {result.get('verification_code', 'N/A')}\n"
            output += f"🔗 Fund Link: https://clawtasks.com/fund/{result.get('wallet_address', 'N/A')}\n"
            output += f"🎯 Next: Post verification on Moltbook, then fund wallet"
            
            return output
        else:
            return f"❌ Registration failed. Response: {result}"
    
    def verify_agent(self):
        """Verify agent with Moltbook post"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register an agent first."
        
        if not self.verification_code:
            return "❌ No verification code found. Registration may have failed."
        
        print(f"🔐 Verifying agent with code: {self.verification_code}")
        
        result = self._make_request('POST', '/agents/verify')
        
        if result:
            output = f"✅ Agent verified successfully!\n"
            output += f"🎉 Ready to post bounties and claim work\n"
            output += f"💼 Your profile is now public on ClawTasks"
            
            return output
        else:
            return "❌ Verification failed. Make sure you posted the verification code on Moltbook."
    
    def get_profile(self):
        """Get agent profile information"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register an agent first."
        
        result = self._make_request('GET', '/agents/me')
        
        if result:
            output = f"💼 ClawTasks Profile for {result.get('name', 'Unknown')}:\n\n"
            output += f"🆔 Agent ID: {result.get('id', 'N/A')}\n"
            output += f"💰 Wallet: {result.get('wallet_address', 'N/A')}\n"
            output += f"⭐ Reputation: {result.get('reputation_score', 'N/A')}\n"
            output += f"📊 Completed: {result.get('completed_bounties', 0)}\n"
            output += f"💵 Earned: ${result.get('total_earned', 0)} USDC\n"
            output += f"📝 Posted: {result.get('posted_bounties', 0)}\n"
            
            if result.get('verified'):
                output += f"✅ Verified Agent\n"
            
            return output
        else:
            return "❌ Failed to fetch profile"
    
    def browse_bounties(self, status="open", limit=20):
        """Browse available bounties with MCP intelligence"""
        if not self.initialized:
            return "❌ ClawTasks not initialized"
        
        # Ensure limit is an integer
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        
        # Ensure status is a valid string
        if not isinstance(status, str) or not status:
            status = "open"
        
        try:
            result = self._make_request('GET', f'/bounties?status={status}&limit={limit}')
            
            if result and 'success' in result and result['success']:
                bounties = result['data']['bounties']
                
                if not bounties:
                    return "📋 No bounties found"
                
                # Use MCP to analyze bounty opportunities
                enhanced_bounties = self._analyze_bounties_with_mcp(bounties)
                
                output = f"💰 Available Bounties ({len(bounties)}):\n\n"
                
                for bounty in enhanced_bounties:
                    output += f"💼 {bounty['title']}\n"
                    output += f"   💰 Reward: ${bounty.get('amount', 0)} USDC\n"
                    output += f"   🏷️  Type: {bounty.get('type', 'standard')}\n"
                    output += f"   📝 Description: {bounty.get('description', 'No description')[:100]}...\n"
                    
                    # Add MCP intelligence if available
                    if 'mcp_analysis' in bounty:
                        output += f"   🧠 AI Analysis: {bounty['mcp_analysis']}\n"
                    
                    output += f"   👤 Poster: {bounty.get('poster_name', 'Unknown')}\n"
                    output += f"   ⏰ Deadline: {bounty.get('deadline', 'No deadline')}\n\n"
                
                return output
            else:
                return f"❌ Failed to fetch bounties: {result}"
                
        except Exception as e:
            return f"❌ Error browsing bounties: {e}"
    
    def _analyze_bounties_with_mcp(self, bounties):
        """Analyze bounties using MCP intelligence"""
        try:
            # Check if MCP plugin is available
            if 'mcp' not in self.core.plugin_manager.plugins:
                return bounties
            
            mcp_plugin = self.core.plugin_manager.plugins['mcp']
            
            # Analyze each bounty
            enhanced_bounties = []
            
            for bounty in bounties:
                enhanced_bounty = bounty.copy()
                
                # Use MCP to analyze bounty suitability
                analysis = self._analyze_single_bounty_with_mcp(bounty, mcp_plugin)
                
                if analysis:
                    enhanced_bounty['mcp_analysis'] = analysis
                
                enhanced_bounties.append(enhanced_bounty)
            
            return enhanced_bounties
            
        except Exception as e:
            print(f"❌ MCP bounty analysis failed: {e}")
            return bounties
    
    def _analyze_single_bounty_with_mcp(self, bounty, mcp_plugin):
        """Analyze single bounty using MCP"""
        try:
            # Create analysis prompt
            bounty_text = f"""
            Bounty Analysis Request:
            Title: {bounty.get('title', '')}
            Description: {bounty.get('description', '')}
            Reward: ${bounty.get('amount', 0)} USDC
            Type: {bounty.get('type', '')}
            
            Analyze this bounty for:
            1. Suitability for AI agent
            2. Required skills and capabilities
            3. Time investment estimate
            4. Success probability
            5. Recommendation (pursue/skip)
            """
            
            # Use MCP analyze command
            analysis_result = mcp_plugin.analyze_command(bounty_text, "opportunities")
            
            if analysis_result and not analysis_result.startswith("❌"):
                # Extract key insights
                if "Suitability:" in analysis_result:
                    suitability = analysis_result.split("Suitability:")[1].split("\n")[0].strip()
                    return f"Highly suitable - {suitability}"
                elif "Recommendation:" in analysis_result:
                    recommendation = analysis_result.split("Recommendation:")[1].split("\n")[0].strip()
                    return f"AI Recommendation: {recommendation}"
                else:
                    return "AI analyzed - Good match for automation"
            
            return None
            
        except Exception as e:
            print(f"❌ Single bounty analysis failed: {e}")
            return None
    
    def get_bounties(self, limit=20):
        """Browse available bounties"""
        params = {'limit': limit}
        
        result = self._make_request('GET', '/bounties', params=params)
        
        if result and 'bounties' in result:
            bounties = result['bounties']
            output = f"💰 Available Bounties ({len(bounties)}):\n\n"
            
            for bounty in bounties:
                output += f"💼 {bounty['title']}\n"
                output += f"   💰 Reward: ${bounty.get('reward', 0)} USDC\n"
                output += f"   🏷️  Type: {bounty.get('bounty_type', 'N/A')}\n"
                output += f"   📝 Description: {bounty.get('description', 'No description')[:100]}...\n"
                output += f"   👤 Poster: {bounty.get('poster_name', 'Unknown')}\n"
                output += f"   ⏰ Deadline: {bounty.get('deadline', 'No deadline')}\n\n"
            
            return output
        else:
            return "❌ Failed to fetch bounties"
    
    def claim_bounty(self, bounty_id):
        """Claim a bounty"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register an agent first."
        
        print(f"🎯 Claiming bounty {bounty_id}...")
        
        result = self._make_request('POST', f'/bounties/{bounty_id}/claim')
        
        if result:
            self._record_activity('claim_bounty', {
                'bounty_id': bounty_id,
                'claimed_at': datetime.now().isoformat()
            })
            return f"✅ Bounty {bounty_id} claimed successfully! Start working on it."
        else:
            return f"❌ Failed to claim bounty {bounty_id}"
    
    def submit_work(self, bounty_id, work_description, evidence=None):
        """Submit completed work for a bounty"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register an agent first."
        
        data = {
            'work_description': work_description
        }
        
        if evidence:
            data['evidence'] = evidence
        
        print(f"📤 Submitting work for bounty {bounty_id}...")
        
        result = self._make_request('POST', f'/bounties/{bounty_id}/submit', data)
        
        if result:
            self._record_activity('submit_work', {
                'bounty_id': bounty_id,
                'submitted_at': datetime.now().isoformat()
            })
            return f"✅ Work submitted for bounty {bounty_id}. Waiting for approval."
        else:
            return f"❌ Failed to submit work for bounty {bounty_id}"
    
    def post_bounty(self, title, description, reward, bounty_type='task', deadline=None):
        """Post a new bounty"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register and verify first."
        
        if not isinstance(reward, (int, float)) or reward <= 0:
            return "❌ Reward must be a positive number (USDC)"
        
        data = {
            'title': title,
            'description': description,
            'reward': reward,
            'bounty_type': bounty_type
        }
        
        if deadline:
            data['deadline'] = deadline
        
        print(f"💼 Posting bounty: {title}")
        
        result = self._make_request('POST', '/bounties', data)
        
        if result and 'id' in result:
            self._record_activity('post_bounty', {
                'bounty_id': result['id'],
                'title': title,
                'reward': reward
            })
            return f"✅ Bounty posted: {result['id']} - {title} (${reward} USDC)"
        else:
            return "❌ Failed to post bounty"
    
    def get_pending_work(self):
        """Get pending work and opportunities"""
        if not self.initialized:
            return "❌ ClawTasks not initialized. Register an agent first."
        
        result = self._make_request('GET', '/agents/me/pending')
        
        if result:
            output = f"⏰ Pending Work & Opportunities:\n\n"
            
            if result.get('claimed_bounties'):
                output += f"🎯 Claimed Bounties ({len(result['claimed_bounties'])}):\n"
                for bounty in result['claimed_bounties']:
                    output += f"   • {bounty['title']} - ${bounty.get('reward', 0)} USDC\n"
                output += "\n"
            
            if result.get('opportunities', {}).get('matching_your_skills'):
                opportunities = result['opportunities']['matching_your_skills']
                output += f"🎯 Matching Opportunities ({len(opportunities)}):\n"
                for opp in opportunities:
                    output += f"   • {opp['title']} - ${opp.get('reward', 0)} USDC\n"
                output += "\n"
            
            if result.get('moltbook', {}).get('post_now'):
                post_content = result['moltbook']['post_now']
                output += f"📝 Suggested Moltbook Post:\n"
                output += f"   {post_content}\n\n"
            
            return output
        else:
            return "❌ Failed to fetch pending work"
    
    def get_heartbeat(self):
        """Get ClawTasks heartbeat for fresh instructions"""
        try:
            response = requests.get("https://clawtasks.com/heartbeat.md")
            if response.status_code == 200:
                return response.text
            else:
                return "❌ Failed to fetch heartbeat"
        except Exception as e:
            return f"❌ Heartbeat error: {e}"
    
    def get_status(self):
        """Get ClawTasks plugin status"""
        if self.initialized:
            return f"💼 ClawTasks Status:\n  Agent: {self.agent_name}\n  Wallet: {self.wallet_address}\n  API: ✅ Connected"
        else:
            return "💼 ClawTasks Status: ❌ Not initialized"
    
    def _record_activity(self, activity_type, data):
        """Record ClawTasks activity in memory"""
        activities = self.core.get_memory('clawtasks_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('clawtasks_activities', activities[-100:])  # Keep last 100
    
    def get_tasks(self):
        """Define scheduled tasks for ClawTasks"""
        return {
            'clawtasks_heartbeat': {
                'schedule': '0 */4 * * *',  # Every 4 hours
                'function': self._heartbeat
            }
        }
    
    def _heartbeat(self):
        """ClawTasks heartbeat - check for work and opportunities"""
        if not self.initialized:
            return
        
        print("💼 ClawTasks heartbeat - checking for work...")
        
        # Check pending work
        pending = self._make_request('GET', '/agents/me/pending')
        if pending:
            claimed = len(pending.get('claimed_bounties', []))
            opportunities = len(pending.get('opportunities', {}).get('matching_your_skills', []))
            print(f"⏰ {claimed} claimed bounties, {opportunities} matching opportunities")
        
        # Get fresh heartbeat instructions
        heartbeat = self.get_heartbeat()
        if heartbeat and "URGENT" in heartbeat:
            print("🚨 URGENT opportunities available!")
        
        print("💼 ClawTasks heartbeat complete")
    
    def get_commands(self):
        """Define ClawTasks commands"""
        return {
            'clawtasks_register': self.register_command,
            'clawtasks_verify': self.verify_command,
            'clawtasks_profile': self.profile_command,
            'clawtasks_bounties': self.bounties_command,
            'clawtasks_claim': self.claim_command,
            'clawtasks_submit': self.submit_command,
            'clawtasks_post': self.post_command,
            'clawtasks_pending': self.pending_command,
            'clawtasks_heartbeat': self.heartbeat_command,
            'clawtasks_status': self.get_status
        }
    
    def register_command(self, name, wallet_address=None):
        """Command to register agent"""
        return self.register_agent(name, wallet_address)
    
    def verify_command(self):
        """Command to verify agent"""
        return self.verify_agent()
    
    def profile_command(self):
        """Command to get profile"""
        return self.get_profile()
    
    def bounties_command(self, limit=20):
        """Command to get bounties"""
        # Ensure limit is an integer
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        
        return self.get_bounties(limit)
    
    def claim_command(self, bounty_id):
        """Command to claim bounty"""
        return self.claim_bounty(bounty_id)
    
    def submit_command(self, bounty_id, work_description, evidence=None):
        """Command to submit work"""
        return self.submit_work(bounty_id, work_description, evidence)
    
    def post_command(self, title, description, reward, bounty_type='task', deadline=None):
        """Command to post bounty"""
        return self.post_bounty(title, description, reward, bounty_type, deadline)
    
    def pending_command(self):
        """Command to get pending work"""
        return self.get_pending_work()
    
    def heartbeat_command(self):
        """Manual heartbeat command"""
        try:
            self._heartbeat()
            return "💼 Heartbeat completed"
        except Exception as e:
            return f"❌ Heartbeat failed: {e}"
    
    def cleanup(self):
        """Cleanup ClawTasks plugin"""
        print("💼 Cleaning up ClawTasks plugin...")
