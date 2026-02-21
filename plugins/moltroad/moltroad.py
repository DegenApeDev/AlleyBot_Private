"""
MoltRoad Plugin - Integrates AlleyBot with MoltRoad.com
The Underground Agent Marketplace - AI agent trading & services
"""
import json
import requests
import os
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin
from config import MOLTROAD_API_KEY

class MoltRoadPlugin(AlleyBotPlugin):
    """Plugin for MoltRoad.com underground marketplace"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://moltroad.com/api/v1"
        self.api_key = MOLTROAD_API_KEY
        self.agent_name = None
        self.agent_id = None
        self.credentials_file = Path.home() / ".config" / "moltroad" / "credentials.json"
        self.initialized = False
        
    def initialize(self, api, core):
        """Initialize MoltRoad plugin"""
        super().initialize(api, core)
        
        # Check if API key is available from environment
        if self.api_key:
            print("✅ MoltRoad API key loaded from environment")
            self.initialized = True
            self.agent_name = "AlleyBot"  # Default name
        else:
            # Try to load from credentials file
            self._load_credentials()
            
            if not self.api_key:
                print("🔑 No MoltRoad API key found. Set MOLTROAD_API_KEY in .env or run 'moltroad_register' command.")
            else:
                print(f"✅ MoltRoad initialized as {self.agent_name}")
                self.initialized = True
        
    def _load_credentials(self):
        """Load credentials from file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key')
                    self.agent_name = creds.get('agent_name')
                    self.agent_id = creds.get('agent_id')
                    print(f"📁 Loaded MoltRoad credentials for {self.agent_name}")
            else:
                print("📁 No MoltRoad credentials file found")
        except Exception as e:
            print(f"❌ Error loading MoltRoad credentials: {e}")
    
    def _save_credentials(self, api_key, agent_data):
        """Save credentials to file"""
        try:
            # Create directory if it doesn't exist
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            credentials = {
                'api_key': api_key,
                'agent_name': agent_data['name'],
                'agent_id': agent_data['id'],
                'registered_at': datetime.now().isoformat()
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print(f"💾 Saved MoltRoad credentials to {self.credentials_file}")
            
        except Exception as e:
            print(f"❌ Error saving MoltRoad credentials: {e}")
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to MoltRoad API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
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
            result = response.json()

            # Check for platform-pushed skill update events
            self._check_for_skill_event('moltroad', result)

            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ MoltRoad API error: {e}")
            return None

    def _check_for_skill_event(self, platform, response):
        """Check API response for skill update notices"""
        try:
            if not isinstance(response, dict):
                return
            notice = (response.get('skill_update') or
                      response.get('notice') or
                      response.get(f'{platform}_notice'))
            if not notice or not isinstance(notice, dict):
                return
            if notice.get('type') != 'skill_update':
                return
            if hasattr(self, 'core') and self.core:
                plugins = getattr(self.core, 'plugin_manager', None)
                if plugins:
                    selfimprove = plugins.plugins.get('selfimprove')
                    if selfimprove and hasattr(selfimprove, 'handle_platform_skill_event'):
                        selfimprove.handle_platform_skill_event(platform, notice)
        except Exception as e:
            print(f"⚠️  Error checking skill event: {e}")
    
    def register_agent(self, name, bio=None):
        """Register a new agent on MoltRoad"""
        if len(name) < 3 or len(name) > 50:
            return "❌ Agent name must be 3-50 characters"
        
        data = {'name': name}
        if bio:
            if len(bio) > 500:
                return "❌ Bio must be max 500 characters"
            data['bio'] = bio
        
        print(f"🌃 Registering agent '{name}' on MoltRoad...")
        
        result = self._make_request('POST', '/register', data)
        
        if result and 'api_key' in result:
            self.api_key = result['api_key']
            self.agent_name = result.get('name', name)  # Use result name or fallback
            self.agent_id = result['id']
            
            # Save credentials
            agent_data = {
                'name': self.agent_name,
                'id': self.agent_id
            }
            self._save_credentials(self.api_key, agent_data)
            
            self.initialized = True
            
            output = f"✅ Agent '{name}' registered on MoltRoad!\n"
            output += f"🔑 API Key: {result['api_key']}\n"
            output += f"💰 Starting Balance: {result['balance']} credits\n"
            output += f"🔗 Claim URL: {result.get('claim_url', 'N/A')}\n"
            output += f"📱 Verification Code: {result.get('verification_code', 'N/A')}"
            
            return output
        else:
            return f"❌ Registration failed. Response: {result}"
    
    def get_profile(self):
        """Get agent profile information"""
        if not self.initialized:
            return "❌ MoltRoad not initialized. Register an agent first."
        
        result = self._make_request('GET', '/me')
        
        if result:
            output = f"🌃 MoltRoad Profile for {result.get('name', 'Unknown')}:\n\n"
            output += f"🆔 ID: {result.get('id', 'N/A')}\n"
            output += f"⭐ Rating: {result.get('rating', 'N/A')} ({result.get('rating_count', 0)} reviews)\n"
            output += f"💰 Balance: {result.get('balance', 0)} credits\n"
            output += f"📝 Bio: {result.get('bio', 'No bio')}\n"
            
            if result.get('twitter_handle'):
                output += f"🐦 Twitter: @{result['twitter_handle']} ✅\n"
            
            if result.get('active_listings'):
                output += f"📦 Active Listings: {len(result['active_listings'])}\n"
            
            return output
        else:
            return "❌ Failed to fetch profile"
    
    def check_balance(self):
        """Check wallet balance"""
        if not self.initialized:
            return "❌ MoltRoad not initialized. Register an agent first."
        
        result = self._make_request('GET', '/wallet')
        
        if result:
            output = f"💰 MoltRoad Wallet:\n"
            output += f"  Balance: {result.get('balance', 0)} credits\n"
            
            if result.get('transactions'):
                output += f"\n📊 Recent Transactions:\n"
                for tx in result['transactions'][:5]:
                    output += f"  {tx.get('type', 'Unknown')}: {tx.get('amount', 0)} credits\n"
            
            return output
        else:
            return "❌ Failed to check balance"
    
    def browse_listings(self, category=None, search=None, limit=20):
        """Browse marketplace listings"""
        # Validate limit
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        
        params = {'limit': limit}
        
        if category:
            valid_categories = ['substances', 'contraband', 'services', 'weapons', 'documents']
            if category not in valid_categories:
                return f"❌ Invalid category. Valid: {', '.join(valid_categories)}"
            params['category'] = category
        
        if search:
            params['search'] = search
        
        result = self._make_request('GET', '/listings', params=params)
        
        if result and 'listings' in result:
            listings = result['listings']
            output = f"🛒 MoltRoad Listings ({len(listings)} found):\n\n"
            
            for listing in listings:
                output += f"📦 {listing['title']}\n"
                output += f"   💰 Price: {listing['price']} credits\n"
                output += f"   🏷️  Category: {listing.get('category', 'N/A')}\n"
                output += f"   👤 Seller: {listing.get('seller', {}).get('name', 'Unknown')}\n"
                output += f"   ⭐ Rating: {listing.get('seller', {}).get('rating', 'N/A')}\n"
                output += f"   📝 {listing.get('description', 'No description')[:100]}...\n\n"
            
            return output
        else:
            return "❌ Failed to fetch listings"
    
    def create_listing(self, title, description, price, category):
        """Create a new marketplace listing"""
        if not self.initialized:
            return "❌ MoltRoad not initialized. Register an agent first."
        
        valid_categories = ['substances', 'contraband', 'services', 'weapons', 'documents']
        if category not in valid_categories:
            return f"❌ Invalid category. Valid: {', '.join(valid_categories)}"
        
        if not title or len(title) > 200:
            return "❌ Title required and must be max 200 characters"
        
        if not description or len(description) > 1000:
            return "❌ Description required and must be max 1000 characters"
        
        try:
            price_num = float(price)
            if price_num <= 0:
                return "❌ Price must be a positive number"
        except (ValueError, TypeError):
            return "❌ Price must be a valid number"
        
        data = {
            'title': title,
            'description': description,
            'price': int(price_num),
            'category': category
        }
        
        print(f"📦 Creating listing: {title}")
        
        result = self._make_request('POST', '/listings', data)
        
        if result and 'id' in result:
            self._record_activity('create_listing', {
                'listing_id': result['id'],
                'title': title,
                'price': price
            })
            return f"✅ Listing created: {result['id']} - {title} ({price} credits)"
        else:
            return "❌ Failed to create listing"
    
    def get_orders(self, role='seller'):
        """Get orders (as seller or buyer)"""
        if not self.initialized:
            return "❌ MoltRoad not initialized. Register an agent first."
        
        params = {'role': role}
        result = self._make_request('GET', '/orders', params=params)
        
        if result and 'orders' in result:
            orders = result['orders']
            output = f"📋 Orders ({role}):\n\n"
            
            for order in orders:
                status_emoji = {
                    'pending': '⏳',
                    'escrowed': '🔒',
                    'delivered': '📦',
                    'confirmed': '✅',
                    'cancelled': '❌'
                }
                
                emoji = status_emoji.get(order.get('status'), '❓')
                output += f"{emoji} Order {order['id']}: {order.get('listing', {}).get('title', 'Unknown')}\n"
                output += f"   💰 Amount: {order.get('amount', 0)} credits\n"
                output += f"   📊 Status: {order.get('status', 'Unknown')}\n"
                output += f"   👤 {order.get('buyer', {}).get('name', 'Unknown')} → {order.get('seller', {}).get('name', 'Unknown')}\n\n"
            
            return output
        else:
            return f"❌ Failed to fetch {role} orders"
    
    def get_bounties(self):
        """Get open bounties - NOTE: API endpoint not implemented, return empty"""
        # Bounties endpoint returns 404 - not implemented yet
        # Silently return None without making API call
        return None
    
    def get_status(self):
        """Get MoltRoad plugin status"""
        if self.initialized:
            return f"🌃 MoltRoad Status:\n  Agent: {self.agent_name}\n  ID: {self.agent_id}\n  API: ✅ Connected"
        else:
            return "🌃 MoltRoad Status: ❌ Not initialized"
    
    def _record_activity(self, activity_type, data):
        """Record MoltRoad activity in memory"""
        activities = self.core.get_memory('moltroad_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('moltroad_activities', activities[-100:])  # Keep last 100
    
    def get_tasks(self):
        """Define scheduled tasks for MoltRoad"""
        return {
            'moltroad_heartbeat': {
                'schedule': '0 */4 * * *',  # Every 4 hours
                'function': self._heartbeat
            }
        }
    
    def _heartbeat(self):
        """MoltRoad heartbeat - check marketplace activity"""
        if not self.initialized:
            return
        
        print("🌃 MoltRoad heartbeat - checking marketplace...")
        
        # Check profile and balance
        profile = self._make_request('GET', '/me')
        if profile:
            balance = profile.get('balance', 0)
            rating = profile.get('rating', 'N/A')
            print(f"💳 Balance: {balance} | ⭐ Rating: {rating}")
        
        # Check pending orders
        orders = self._make_request('GET', '/orders', params={'role': 'seller'})
        if orders and 'orders' in orders:
            pending = [o for o in orders['orders'] if o.get('status') == 'escrowed']
            if pending:
                print(f"⚠️ You have {len(pending)} orders waiting for delivery!")
        
        print("🌃 MoltRoad heartbeat complete")
    
    def get_commands(self):
        """Define MoltRoad commands"""
        return {
            'moltroad_register': self.register_command,
            'moltroad_profile': self.profile_command,
            'moltroad_balance': self.balance_command,
            'moltroad_browse': self.browse_command,
            'moltroad_list': self.create_listing_command,
            'moltroad_orders': self.orders_command,
            'moltroad_bounties': self.bounties_command,
            'moltroad_status': self.get_status,
            'moltroad_heartbeat': self.heartbeat_command
        }
    
    def register_command(self, name, bio=None):
        """Command to register agent"""
        return self.register_agent(name, bio)
    
    def profile_command(self):
        """Command to get profile"""
        return self.get_profile()
    
    def balance_command(self):
        """Command to check balance"""
        return self.check_balance()
    
    def browse_command(self, category=None, search=None):
        """Command to browse listings"""
        return self.browse_listings(category, search)
    
    def create_listing_command(self, title, description, price, category):
        """Command to create listing"""
        return self.create_listing(title, description, price, category)
    
    def orders_command(self, role='seller'):
        """Command to get orders"""
        return self.get_orders(role)
    
    def bounties_command(self):
        """Command to get bounties"""
        return self.get_bounties()
    
    def heartbeat_command(self):
        """Manual heartbeat command"""
        try:
            self._heartbeat()
            return "🌃 Heartbeat completed"
        except Exception as e:
            return f"❌ Heartbeat failed: {e}"
    
    def cleanup(self):
        """Cleanup MoltRoad plugin"""
        print("🌃 Cleaning up MoltRoad plugin...")
