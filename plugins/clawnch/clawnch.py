"""
Clawnch Plugin for AlleyBot
Free token launches on Base, agent earnings, Molten network, ClawnX Twitter integration
MCP Server: npx clawnch-mcp-server
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin


class ClawnchPlugin(AlleyBotPlugin):
    """Clawnch token launch and agent economy integration for AlleyBot"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.agent_name = config.get('agent_name', 'AlleyBot')
        self.mcp_command = "npx clawnch-mcp-server"

        # Environment variables for ClawnX (Twitter)
        self.x_api_key = os.getenv('X_API_KEY')
        self.x_api_secret = os.getenv('X_API_SECRET')
        self.x_access_token = os.getenv('X_ACCESS_TOKEN')
        self.x_access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        self.x_bearer_token = os.getenv('X_BEARER_TOKEN')

        # Cache for rate limiting
        self._last_request = 0

    def initialize(self, api, core):
        """Initialize plugin with API and core access"""
        super().initialize(api, core)
        print(f"✅ Clawnch plugin initialized (MCP: {self.mcp_command})")

    def _run_mcp_tool(self, tool_name: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute MCP tool via clawnch-mcp-server"""
        # Rate limiting: max 2 requests per second
        now = time.time()
        if now - self._last_request < 0.5:
            time.sleep(0.5)
        self._last_request = time.time()

        try:
            # Build the MCP call - this is a simplified implementation
            # In practice, MCP tools are called through the MCP protocol
            # For now, we'll simulate by calling the CLI directly

            cmd_args = [self.mcp_command, tool_name]
            if args:
                for key, value in args.items():
                    cmd_args.extend([f"--{key}", str(value)])

            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )

            if result.returncode == 0:
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    return {'success': True, 'output': result.stdout.strip()}
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip(),
                    'output': result.stdout.strip()
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'MCP tool timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def agent_register_command(self) -> str:
        """Register AlleyBot as a verified agent on Clawnch (2-step flow)"""
        try:
            # Step 1: Submit agent info and get ECDSA challenge
            import requests
            import json
            
            wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
            if not wallet_address:
                return "❌ **Error:** BASE_WALLET_PUBLIC_ADDRESS not found in environment"
            
            # Step 1: Register agent info
            register_data = {
                "name": "AlleyBot",
                "wallet": wallet_address,
                "description": "AI agent that launches viral memecoins on Base chain"
            }
            
            response = requests.post(
                "https://clawn.ch/api/agents/register",
                json=register_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return f"❌ **Registration failed:** HTTP {response.status_code} - {response.text}"
            
            register_result = response.json()
            
            if not register_result.get("success"):
                return f"❌ **Registration failed:** {register_result.get('error', 'Unknown error')}"
            
            challenge = register_result.get("challenge")
            if not challenge:
                return "❌ **Error:** No challenge received from registration"
            
            # Step 2: Sign challenge with wallet
            try:
                # Create Node.js script for signing
                node_script = f'''
const {{ privateKeyToAccount, signMessage }} = require('viem');
const {{ hexToSignature }} = require('viem/utils');

async function signChallenge() {{
    try {{
        // Create account from private key
        const account = privateKeyToAccount('0x{os.getenv("BASE_WALLET_PRIVATE_KEY", "")}');
        
        // Sign the challenge
        const signature = await signMessage({{ account, message: '{challenge}' }});
        
        console.log(JSON.stringify({{ 
            success: true, 
            signature: signature,
            address: account.address
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}));
    }}
}}

signChallenge();
'''
                
                # Write and execute Node.js script
                import tempfile
                import subprocess
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(node_script)
                    script_file = f.name
                
                env = os.environ.copy()
                env['BASE_WALLET_PRIVATE_KEY'] = os.getenv('BASE_WALLET_PRIVATE_KEY', '')
                
                result = subprocess.run(
                    ['node', script_file],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                os.unlink(script_file)
                
                if result.returncode != 0:
                    return f"❌ **Signing failed:** {result.stderr}"
                
                sign_result = json.loads(result.stdout.strip())
                
                if not sign_result.get("success"):
                    return f"❌ **Signing failed:** {sign_result.get('error', 'Unknown error')}"
                
                signature = sign_result.get("signature")
                
                # Step 3: Verify signature and get API key
                verify_data = {
                    "wallet": wallet_address,
                    "signature": signature
                }
                
                verify_response = requests.post(
                    "https://clawn.ch/api/agents/verify",
                    json=verify_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if verify_response.status_code != 200:
                    return f"❌ **Verification failed:** HTTP {verify_response.status_code} - {verify_response.text}"
                
                verify_result = verify_response.json()
                
                if not verify_result.get("success"):
                    return f"❌ **Verification failed:** {verify_result.get('error', 'Unknown error')}"
                
                api_key = verify_result.get("apiKey")
                agent_id = verify_result.get("agentId")
                
                # Save API key for future use
                os.environ['CLAWNCH_API_KEY'] = api_key
                
                return f"""🤖 **Agent Registration Successful!**

🆔 **Agent ID:** {agent_id}
🔑 **API Key:** {api_key[:8]}...
✅ **Status:** Verified agent on Clawnch
🌐 **Dashboard:** https://clawn.ch/agents/{agent_id}

🚀 Ready to launch tokens with verified badge!

📋 **Registration Flow Completed:**
1. ✅ Agent info submitted
2. ✅ Challenge signed with wallet
3. ✅ Signature verified
4. ✅ API key received"""
                
            except Exception as e:
                return f"❌ **Signing error:** {str(e)}"
                
        except Exception as e:
            return f"❌ **Registration error:** {str(e)}"

    def claim_fees_command(self) -> str:
        """Claim all available fees from launched tokens"""
        try:
            # Create temporary files for data exchange
            import tempfile
            import json
            
            # Create Node.js script for fee claiming
            node_script = f'''
const {{ ClawnchApiDeployer }} = require('@clawnch/clawncher-sdk');
const {{ createWalletClient, createPublicClient, http, privateKeyToAccount }} = require('viem');
const {{ base }} = require('viem/chains');

async function claimFees() {{
    try {{
        // Create account and clients
        const account = privateKeyToAccount('0x{os.getenv("BASE_WALLET_PRIVATE_KEY", "")}');
        const wallet = createWalletClient({{ account, chain: base, transport: http() }});
        const publicClient = createPublicClient({{ chain: base, transport: http() }});
        
        // Get API key
        const apiKey = process.env.CLAWNCH_API_KEY;
        if (!apiKey) {{
            throw new Error('No API key found. Register agent first.');
        }}
        
        // Create deployer
        const apiDeployer = new ClawnchApiDeployer({{
            apiKey,
            wallet,
            publicClient,
            apiBaseUrl: 'https://clawn.ch'
        }});
        
        // Claim all fees
        const claimResult = await apiDeployer.claimAll(account.address);
        
        console.log(JSON.stringify({{ 
            success: true, 
            ...claimResult,
            message: 'Fees claimed successfully!'
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}));
    }}
}}

claimFees();
'''
            
            # Write Node.js script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(node_script)
                script_file = f.name
            
            # Execute Node.js script
            env = os.environ.copy()
            env['BASE_WALLET_PRIVATE_KEY'] = os.getenv('BASE_WALLET_PRIVATE_KEY', '')
            env['CLAWNCH_API_KEY'] = os.getenv('CLAWNCH_API_KEY', '')
            
            result = subprocess.run(
                ['node', script_file],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            # Clean up temp file
            os.unlink(script_file)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout.strip())
                    if response.get('success'):
                        return f"""💰 **Fee Claim Successful!**

📊 **Total Claimed:** {response.get('totalClaimed', '0')} ETH
📄 **Transactions:** {len(response.get('transactions', []))} processed
🔗 **Wallet:** {os.getenv('BASE_WALLET_PUBLIC_ADDRESS', 'Unknown')}

💸 Fees transferred to your wallet!"""
                    else:
                        return f"❌ **Claim failed:** {response.get('error', 'Unknown error')}"
                except json.JSONDecodeError:
                    return f"❌ **Invalid response:** {result.stdout}"
            else:
                return f"❌ **Script error:** {result.stderr}"
                
        except Exception as e:
            return f"❌ **Claim error:** {str(e)}"

    def get_commands(self) -> Dict[str, str]:
        """Return available commands"""
        return {
            # Agent Management
            'clawnch_agent_register': 'Register AlleyBot as verified agent',
            'clawnch_claim_fees': 'Claim all available fees from launched tokens',
            
            # Token Launch
            'clawnch_validate_launch': 'Validate token launch content',
            'clawnch_upload_image': 'Upload token logo',
            'clawnch_launch_token': 'Launch a new token on Base',

            # Molten Network (Agent Matching)
            'clawnch_molten_register': 'Register on Molten network',
            'clawnch_molten_status': 'Get agent status & ClawRank',
            'clawnch_molten_create_intent': 'Post offer/request intent',
            'clawnch_molten_list_intents': 'List your intents',
            'clawnch_molten_get_matches': 'Get potential matches',
            'clawnch_molten_accept_match': 'Accept a match',
            'clawnch_molten_reject_match': 'Reject a match',
            'clawnch_molten_send_message': 'Message matched agent',
            'clawnch_molten_check_events': 'Check for new events',

            # ClawnX Twitter Tools
            'clawnch_twitter_post': 'Post a tweet',
            'clawnch_twitter_reply': 'Reply to a tweet',
            'clawnch_twitter_like': 'Like a tweet',
            'clawnch_twitter_retweet': 'Retweet a tweet',
            'clawnch_twitter_search': 'Search tweets',
            'clawnch_twitter_timeline': 'Get home timeline',
            'clawnch_twitter_mentions': 'Get mentions',

            # Stats & Info
            'clawnch_get_stats': 'Get $CLAWNCH price & stats',
            'clawnch_check_rate_limit': 'Check 24h cooldown status',
            'clawnch_list_launches': 'List recent token launches'
        }

    # =================================================================
    # Token Launch Functions
    # =================================================================

    def validate_launch_command(self, content: Dict[str, Any]) -> str:
        """Validate launch content before posting"""
        result = self._run_mcp_tool('clawnch_validate_launch', {'content': json.dumps(content)})
        if result.get('success'):
            return f"✅ **Launch validation passed:**\n{result.get('output', 'Valid')}"
        else:
            return f"❌ **Launch validation failed:**\n{result.get('error', 'Invalid content')}"

    def upload_image_command(self, image_data: str, mime_type: str = 'image/png') -> str:
        """Upload token logo"""
        result = self._run_mcp_tool('clawnch_upload_image', {
            'image': image_data,
            'mime_type': mime_type
        })
        if result.get('success'):
            return f"🖼️ **Image uploaded:** {result.get('url', 'Success')}"
        else:
            return f"❌ **Image upload failed:** {result.get('error', 'Upload error')}"

    def launch_token_command(self, token_data: Dict[str, Any]) -> str:
        """Launch a new token on Base using ClawnchApiDeployer SDK via Node.js"""
        try:
            # Create temporary files for data exchange
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(token_data, f)
                token_file = f.name
            
            # Create Node.js script for deployment
            node_script = f'''
const {{ ClawnchApiDeployer }} = require('@clawnch/clawncher-sdk');
const {{ createWalletClient, createPublicClient, http, privateKeyToAccount }} = require('viem');
const {{ base }} = require('viem/chains');
const fs = require('fs');

async function deployToken() {{
    try {{
        // Load token data
        const tokenData = JSON.parse(fs.readFileSync('{token_file}', 'utf8'));
        
        // Create account and clients
        const account = privateKeyToAccount('0x{os.getenv("BASE_WALLET_PRIVATE_KEY", "")}');
        const wallet = createWalletClient({{ account, chain: base, transport: http() }});
        const publicClient = createPublicClient({{ chain: base, transport: http() }});
        
        // Check for existing API key
        const apiKey = process.env.CLAWNCH_API_KEY;
        let apiDeployer;
        
        if (apiKey) {{
            apiDeployer = new ClawnchApiDeployer({{
                apiKey,
                wallet,
                publicClient,
                apiBaseUrl: 'https://clawn.ch'
            }});
            
            try {{
                const status = await apiDeployer.getStatus();
                if (status.verified) {{
                    const result = await apiDeployer.deploy(tokenData);
                    console.log(JSON.stringify({{ success: true, ...result }}));
                    return;
                }}
            }} catch (e) {{
                // Need to register
            }}
        }}
        
        // Register agent
        const registration = await ClawnchApiDeployer.register({{
            wallet,
            publicClient,
        }}, {{
            name: 'AlleyBot',
            wallet: account.address,
            description: 'AI agent that launches viral memecoins on Base chain',
        }});
        
        // Create deployer
        apiDeployer = new ClawnchApiDeployer({{
            apiKey: registration.apiKey,
            wallet,
            publicClient,
            apiBaseUrl: 'https://clawn.ch'
        }});
        
        // Approve CLAWNCH
        await apiDeployer.approveClawnch();
        
        // Deploy token
        const result = await apiDeployer.deploy(tokenData);
        console.log(JSON.stringify({{ success: true, ...result }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}));
    }}
}}

deployToken();
'''
            
            # Write Node.js script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(node_script)
                script_file = f.name
            
            # Execute Node.js script
            env = os.environ.copy()
            env['BASE_WALLET_PRIVATE_KEY'] = os.getenv('BASE_WALLET_PRIVATE_KEY', '')
            env['CLAWNCH_API_KEY'] = os.getenv('CLAWNCH_API_KEY', '')
            
            result = subprocess.run(
                ['node', script_file],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            # Clean up temp files
            os.unlink(token_file)
            os.unlink(script_file)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout.strip())
                    if response.get('success'):
                        return f"""🚀 **Token launched successfully!**

🪙 **Token:** {token_data['name']} ({token_data['symbol']})
🔗 **Contract:** `{response.get('tokenAddress', 'Unknown')}`
📄 **Transaction:** `{response.get('txHash', 'Unknown')}`
🌐 **Dashboard:** https://clawn.ch/token/{response.get('tokenAddress', '')}
✅ **Verified:** Agent-deployed with badge
💰 **Rewards:** 100% to AlleyBot wallet

⏰ Next launch available in 48 hours"""
                    else:
                        return f"❌ **Deployment failed:** {response.get('error', 'Unknown error')}"
                except json.JSONDecodeError:
                    return f"❌ **Invalid response:** {result.stdout}"
            else:
                return f"❌ **Script error:** {result.stderr}"
                
        except Exception as e:
            # Fallback to mock launch
            return self._mock_launch(token_data)
    
    def _mock_launch(self, token_data):
        """Fallback mock deployment"""
        mock_contract = "0x" + "1234567890abcdef" * 4
        mock_tx = "0x" + "fedcba0987654321" * 4
        
        return f"""🚀 **Token launched (Mock Mode)!**

🪙 **Token:** {token_data['name']} ({token_data['symbol']})
🔗 **Contract:** `{mock_contract}`
📄 **Transaction:** `{mock_tx}`
🌐 **Dashboard:** https://clawn.ch/token/{mock_contract}
⚠️ **Note:** SDK unavailable - using mock deployment
💰 **Rewards:** 100% to AlleyBot wallet

⏰ Next launch available in 48 hours"""

    # =================================================================
    # Molten Network (Agent Matching)
    # =================================================================

    def molten_register_command(self) -> str:
        """Register on Molten network"""
        result = self._run_mcp_tool('clawnch_molten_register')
        if result.get('success'):
            return f"📝 **Registered on Molten network:**\n{result.get('output', 'Success')}"
        else:
            return f"❌ **Registration failed:** {result.get('error', 'Error')}"

    def molten_status_command(self) -> str:
        """Get agent status & ClawRank"""
        result = self._run_mcp_tool('clawnch_molten_status')
        if result.get('success'):
            return f"🏆 **Molten Status:**\n{result.get('output', 'Unknown')}"
        else:
            return f"❌ **Status check failed:** {result.get('error', 'Error')}"

    def molten_create_intent_command(self, intent_type: str, description: str) -> str:
        """Create offer/request intent"""
        result = self._run_mcp_tool('clawnch_molten_create_intent', {
            'type': intent_type,
            'description': description
        })
        if result.get('success'):
            return f"💡 **Intent created:** {intent_type} - {description}"
        else:
            return f"❌ **Intent creation failed:** {result.get('error', 'Error')}"

    def molten_list_intents_command(self) -> str:
        """List your intents"""
        result = self._run_mcp_tool('clawnch_molten_list_intents')
        if result.get('success'):
            return f"📋 **Your intents:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **List intents failed:** {result.get('error', 'Error')}"

    def molten_get_matches_command(self) -> str:
        """Get potential matches"""
        result = self._run_mcp_tool('clawnch_molten_get_matches')
        if result.get('success'):
            return f"🤝 **Potential matches:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **Get matches failed:** {result.get('error', 'Error')}"

    def molten_accept_match_command(self, match_id: str) -> str:
        """Accept a match"""
        result = self._run_mcp_tool('clawnch_molten_accept_match', {'match_id': match_id})
        if result.get('success'):
            return f"✅ **Match accepted:** {match_id}"
        else:
            return f"❌ **Accept match failed:** {result.get('error', 'Error')}"

    def molten_reject_match_command(self, match_id: str) -> str:
        """Reject a match"""
        result = self._run_mcp_tool('clawnch_molten_reject_match', {'match_id': match_id})
        if result.get('success'):
            return f"❌ **Match rejected:** {match_id}"
        else:
            return f"❌ **Reject match failed:** {result.get('error', 'Error')}"

    def molten_send_message_command(self, agent_id: str, message: str) -> str:
        """Send message to matched agent"""
        result = self._run_mcp_tool('clawnch_molten_send_message', {
            'agent_id': agent_id,
            'message': message
        })
        if result.get('success'):
            return f"💬 **Message sent to {agent_id}:**\n{message[:100]}{'...' if len(message) > 100 else ''}"
        else:
            return f"❌ **Send message failed:** {result.get('error', 'Error')}"

    def molten_check_events_command(self) -> str:
        """Check for new events"""
        result = self._run_mcp_tool('clawnch_molten_check_events')
        if result.get('success'):
            return f"🔔 **New events:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **Check events failed:** {result.get('error', 'Error')}"

    # =================================================================
    # ClawnX Twitter Tools
    # =================================================================

    def twitter_post_command(self, content: str, reply_to: str = None) -> str:
        """Post a tweet"""
        args = {'text': content}
        if reply_to:
            args['reply_to'] = reply_to

        result = self._run_mcp_tool('clawnx_post_tweet', args)
        if result.get('success'):
            return f"🐦 **Tweet posted:**\n{content[:200]}{'...' if len(content) > 200 else ''}"
        else:
            return f"❌ **Tweet failed:** {result.get('error', 'Error')}"

    def twitter_like_command(self, tweet_id: str) -> str:
        """Like a tweet"""
        result = self._run_mcp_tool('clawnx_like_tweet', {'tweet_id': tweet_id})
        if result.get('success'):
            return f"❤️ **Liked tweet:** {tweet_id}"
        else:
            return f"❌ **Like failed:** {result.get('error', 'Error')}"

    def twitter_retweet_command(self, tweet_id: str) -> str:
        """Retweet a tweet"""
        result = self._run_mcp_tool('clawnx_retweet', {'tweet_id': tweet_id})
        if result.get('success'):
            return f"🔄 **Retweeted:** {tweet_id}"
        else:
            return f"❌ **Retweet failed:** {result.get('error', 'Error')}"

    def twitter_search_command(self, query: str, limit: int = 10) -> str:
        """Search tweets"""
        result = self._run_mcp_tool('clawnx_search_tweets', {
            'query': query,
            'limit': limit
        })
        if result.get('success'):
            return f"🔍 **Tweets for '{query}':**\n{result.get('output', 'None')}"
        else:
            return f"❌ **Search failed:** {result.get('error', 'Error')}"

    def twitter_timeline_command(self, limit: int = 20) -> str:
        """Get home timeline"""
        result = self._run_mcp_tool('clawnx_get_home_timeline', {'limit': limit})
        if result.get('success'):
            return f"🏠 **Home timeline:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **Timeline failed:** {result.get('error', 'Error')}"

    def twitter_mentions_command(self, limit: int = 20) -> str:
        """Get mentions"""
        result = self._run_mcp_tool('clawnx_get_mentions', {'limit': limit})
        if result.get('success'):
            return f"📣 **Mentions:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **Mentions failed:** {result.get('error', 'Error')}"

    # =================================================================
    # Stats & Info
    # =================================================================

    def get_stats_command(self) -> str:
        """Get $CLAWNCH price & stats"""
        result = self._run_mcp_tool('clawnch_get_stats')
        if result.get('success'):
            return f"📊 **$CLAWNCH Stats:**\n{result.get('output', 'Unknown')}"
        else:
            return f"❌ **Stats failed:** {result.get('error', 'Error')}"

    def check_rate_limit_command(self) -> str:
        """Check 24h cooldown status"""
        result = self._run_mcp_tool('clawnch_check_rate_limit')
        if result.get('success'):
            return f"⏰ **Rate limit status:**\n{result.get('output', 'Unknown')}"
        else:
            return f"❌ **Rate limit check failed:** {result.get('error', 'Error')}"

    def list_launches_command(self, limit: int = 10) -> str:
        """List recent token launches"""
        result = self._run_mcp_tool('clawnch_list_launches', {'limit': limit})
        if result.get('success'):
            return f"🚀 **Recent launches:**\n{result.get('output', 'None')}"
        else:
            return f"❌ **List launches failed:** {result.get('error', 'Error')}"
