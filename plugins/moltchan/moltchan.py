"""
MoltChan Plugin - Integrates AlleyBot with MoltChan.org
Social imageboard for AI agents - community engagement
"""
import json
import requests
import os
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin
from config import MOLTCHAN_API_KEY

class MoltChanPlugin(AlleyBotPlugin):
    """Plugin for Moltchan.org imageboard integration"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.moltchan.org/api/v1"
        self.api_key = MOLTCHAN_API_KEY
        self.agent_name = None
        self.agent_id = None
        self.credentials_file = Path.home() / ".config" / "moltchan" / "credentials.json"
        self.initialized = False
        
    def initialize(self, api, core):
        """Initialize MoltChan plugin"""
        super().initialize(api, core)
        
        # Check if API key is available from environment
        if self.api_key:
            print("✅ MoltChan API key loaded from environment")
            self.initialized = True
            self.agent_name = "AlleyBot"  # Default name
        else:
            # Try to load from credentials file
            self._load_credentials()
            
            if not self.api_key:
                print("🔑 No MoltChan API key found. Set MOLTCHAN_API_KEY in .env or run 'moltchan_register' command.")
            else:
                print(f"✅ MoltChan initialized as {self.agent_name}")
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
                    print(f"📁 Loaded MoltChan credentials for {self.agent_name}")
            else:
                print("📁 No MoltChan credentials file found")
        except Exception as e:
            print(f"❌ Error loading MoltChan credentials: {e}")
    
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
            
            print(f"💾 Saved MoltChan credentials to {self.credentials_file}")
            
        except Exception as e:
            print(f"❌ Error saving MoltChan credentials: {e}")
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to MoltChan API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            result = response.json()

            # Check for platform-pushed skill update events
            self._check_for_skill_event('moltchan', result)

            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ MoltChan API error: {e}")
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
    
    def register_agent(self, name, description=None):
        """Register a new agent identity"""
        if len(name) < 3 or len(name) > 24:
            return "❌ Agent name must be 3-24 characters"
        
        if not name.replace('_', '').isalnum():
            return "❌ Agent name must be alphanumeric + underscores only"
        
        data = {'name': name}
        if description:
            if len(description) > 280:
                return "❌ Description must be max 280 characters"
            data['description'] = description
        
        print(f"🔑 Registering agent '{name}' on MoltChan...")
        
        result = self._make_request('POST', '/agents/register', data)
        
        if result and 'api_key' in result:
            self.api_key = result['api_key']
            self.agent_name = result['agent']['name']
            self.agent_id = result['agent']['id']
            
            # Save credentials
            self._save_credentials(self.api_key, result['agent'])
            
            self.initialized = True
            
            return f"✅ Agent '{name}' registered successfully! API key saved."
        else:
            return "❌ Registration failed"
    
    def browse_boards(self):
        """Browse available boards"""
        if not self.initialized:
            return "❌ MoltChan not initialized. Register an agent first."
        
        result = self._make_request('GET', '/boards')
        
        if result:
            # Handle both formats: direct array or object with 'boards' key
            if isinstance(result, list):
                boards = result
            elif isinstance(result, dict) and 'boards' in result:
                boards = result['boards']
            else:
                return "❌ Unexpected response format"
            
            output = f"📋 MoltChan Boards ({len(boards)}):\n\n"
            
            for board in boards:
                output += f"🏷️  /{board['id']}/ - {board['name']}\n"
                if board.get('description'):
                    output += f"   {board['description']}\n"
                output += f"   Posts: {board.get('thread_count', 0)}\n\n"
            
            return output
        else:
            return "❌ Failed to fetch boards"
    
    def list_threads(self, board_id):
        """List threads in a board"""
        if not self.initialized:
            return "❌ MoltChan not initialized. Register an agent first."
        
        result = self._make_request('GET', f'/boards/{board_id}/threads')
        
        if result and isinstance(result, list):
            threads = result
            output = f"🧵 Threads in /{board_id}/ ({len(threads)}):\n\n"
            
            for thread in threads:
                # Handle both 'title' and 'subject' fields
                title = thread.get('title') or thread.get('subject', 'No Subject')
                author = thread.get('author_name', 'Anonymous')
                replies = thread.get('replies_count', len(thread.get('replies', [])))
                
                output += f"📝 {thread['id']}: {title}\n"
                output += f"   👤 {author}\n"
                output += f"   💬 {replies} replies\n"
                output += f"   🕒 {thread.get('created_at', 'Unknown')}\n\n"
            
            return output
        else:
            return f"❌ Failed to fetch threads for /{board_id}/"
    
    def create_thread(self, board_id, subject, content):
        """Create a new thread"""
        if not self.initialized:
            return "❌ MoltChan not initialized. Register an agent first."
        
        if not subject or len(subject) > 200:
            return "❌ Subject required and must be max 200 characters"
        
        if not content or len(content) > 2000:
            return "❌ Content required and must be max 2000 characters"
        
        data = {
            'subject': subject,
            'content': content
        }
        
        print(f"📝 Creating thread in /{board_id}/: {subject}")
        
        result = self._make_request('POST', f'/boards/{board_id}/threads', data)
        
        if result and 'id' in result:
            thread = result  # The response is the thread directly
            self._record_activity('create_thread', {
                'board_id': board_id,
                'thread_id': thread['id'],
                'subject': subject
            })
            return f"✅ Thread created: {thread['id']} - {subject}"
        else:
            return "❌ Failed to create thread"
    
    def reply_to_thread(self, thread_id, content):
        """Reply to an existing thread"""
        if not self.initialized:
            return "❌ MoltChan not initialized. Register an agent first."
        
        if not content or len(content) > 2000:
            return "❌ Content required and must be max 2000 characters"
        
        data = {'content': content}
        
        print(f"💬 Replying to thread {thread_id}...")
        
        result = self._make_request('POST', f'/threads/{thread_id}/replies', data)
        
        if result and 'reply' in result:
            reply = result['reply']
            self._record_activity('reply_thread', {
                'thread_id': thread_id,
                'reply_id': reply['id']
            })
            return f"✅ Reply posted: {reply['id']}"
        else:
            return "❌ Failed to post reply"
    
    def get_status(self):
        """Get MoltChan plugin status"""
        if self.initialized:
            return f"🔗 MoltChan Status:\n  Agent: {self.agent_name}\n  ID: {self.agent_id}\n  API: ✅ Connected"
        else:
            return "🔗 MoltChan Status: ❌ Not initialized"
    
    def _record_activity(self, activity_type, data):
        """Record MoltChan activity in memory"""
        activities = self.core.get_memory('moltchan_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('moltchan_activities', activities[-100:])  # Keep last 100
    
    def get_tasks(self):
        """Define scheduled tasks for MoltChan"""
        return {
            'moltchan_browse': {
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'function': self._browse_and_engage
            },
            'moltchan_heartbeat': {
                'schedule': '0 */6 * * *',  # Every 6 hours
                'function': self._heartbeat
            }
        }
    
    def _heartbeat(self):
        """MoltChan heartbeat - check for updates and engage appropriately"""
        if not self.initialized:
            return
        
        print("🫀 MoltChan heartbeat - checking in...")
        
        # Load state
        state = self._load_state()
        
        # 1. Check for skill updates
        self._check_skill_updates(state)
        
        # 2. Browse boards for activity
        activity_summary = self._heartbeat_browse()
        
        # 3. Update state
        state['lastCheck'] = datetime.now().isoformat()
        self._save_state(state)
        
        # 4. Report status
        if activity_summary:
            print(f"🫀 HEARTBEAT - {activity_summary}")
        else:
            print("🫀 HEARTBEAT_OK - Checked moltchan, all quiet.")
    
    def _load_state(self):
        """Load heartbeat state"""
        state_file = self.credentials_file.parent / 'state.json'
        try:
            if state_file.exists():
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Failed to load MoltChan state: {e}")
        return {'lastCheck': None, 'lastPost': None}
    
    def _save_state(self, state):
        """Save heartbeat state"""
        state_file = self.credentials_file.parent / 'state.json'
        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving state: {e}")
    
    def _check_skill_updates(self, state):
        """Check for skill updates"""
        try:
            import requests
            response = requests.get('https://www.moltchan.org/skill.json')
            if response.status_code == 200:
                skill_data = response.json()
                current_version = skill_data.get('version', 'unknown')
                last_version = state.get('lastSkillVersion')
                
                if last_version != current_version:
                    print(f"🔄 Skill version updated: {last_version} -> {current_version}")
                    # Update skill files
                    self._update_skill_files()
                    state['lastSkillVersion'] = current_version
        except Exception as e:
            print(f"❌ Error checking skill updates: {e}")
    
    def _update_skill_files(self):
        """Update local skill files"""
        try:
            import requests
            base_url = 'https://www.moltchan.org'
            
            # Update SKILL.md
            response = requests.get(f'{base_url}/SKILL.md')
            if response.status_code == 200:
                skill_file = self.credentials_file.parent / 'SKILL.md'
                with open(skill_file, 'w') as f:
                    f.write(response.text)
                print("📥 Updated SKILL.md")
            
            # Update HEARTBEAT.md
            response = requests.get(f'{base_url}/HEARTBEAT.md')
            if response.status_code == 200:
                heartbeat_file = self.credentials_file.parent / 'HEARTBEAT.md'
                with open(heartbeat_file, 'w') as f:
                    f.write(response.text)
                print("📥 Updated HEARTBEAT.md")
                
        except Exception as e:
            print(f"❌ Error updating skill files: {e}")
    
    def _heartbeat_browse(self):
        """Browse boards during heartbeat and look for engagement opportunities"""
        try:
            # Get boards
            result = self._make_request('GET', '/boards')
            if not result:
                return "failed to fetch boards"
            
            boards = result if isinstance(result, list) else result.get('boards', [])
            
            # Focus on main boards
            main_boards = ['g', 'phi', 'meta']
            activities = []
            
            for board_id in main_boards:
                board = next((b for b in boards if b.get('id') == board_id), None)
                if not board:
                    continue
                
                # Get recent threads
                threads_result = self._make_request('GET', f'/boards/{board_id}/threads?sort=bumped&limit=10')
                if not threads_result:
                    continue
                
                threads = threads_result if isinstance(threads_result, list) else []
                
                # Look for interesting threads
                for thread in threads[:5]:  # Check top 5
                    # Check if AlleyBot is mentioned
                    thread_content = thread.get('content', '').lower()
                    thread_title = thread.get('title', '').lower()
                    
                    if 'alleybot' in thread_content or 'alleybot' in thread_title:
                        activities.append(f"found mention in /{board_id}/ thread {thread['id']}")
                    
                    # Check for questions about AI/agents
                    if any(keyword in thread_content for keyword in ['?', 'help', 'how', 'what', 'ai agent']):
                        if len(thread.get('replies', [])) < 3:  # Low reply count
                            activities.append(f"potential question in /{board_id}/ thread {thread['id']}")
            
            # Decide if we should engage (max 1 action per heartbeat)
            if activities and len(activities) > 0:
                # For now, just report what we found
                return f"found {len(activities)} interesting items: {', '.join(activities[:2])}"
            
            return None
            
        except Exception as e:
            print(f"❌ Error during heartbeat browse: {e}")
            return "error during browse"
    
    def _browse_and_engage(self):
        """Browse boards and engage with interesting content"""
        if not self.initialized:
            return
        
        print("🔍 Browsing MoltChan boards for engagement opportunities...")
        
        # Get boards and find interesting ones
        result = self._make_request('GET', '/boards')
        if result and 'boards' in result:
            boards = result['boards']
            # Focus on tech/ai related boards
            tech_boards = [b for b in boards if any(keyword in b.get('name', '').lower() 
                           for keyword in ['tech', 'ai', 'programming', 'development'])]
            
            if tech_boards:
                print(f"🎯 Found {len(tech_boards)} tech-related boards")
                # Could implement auto-engagement logic here
    
    def get_commands(self):
        """Define MoltChan commands"""
        return {
            'moltchan_register': self.register_command,
            'moltchan_boards': self.browse_boards_command,
            'moltchan_threads': self.list_threads_command,
            'moltchan_post': self.create_thread_command,
            'moltchan_reply': self.reply_thread_command,
            'moltchan_status': self.get_status,
            'moltchan_heartbeat': self.heartbeat_command
        }
    
    def register_command(self, name, description=None):
        """Command to register agent"""
        return self.register_agent(name, description)
    
    def browse_boards_command(self):
        """Command to browse boards"""
        return self.browse_boards()
    
    def list_threads_command(self, board_id):
        """Command to list threads"""
        return self.list_threads(board_id)
    
    def create_thread_command(self, board_id, subject, content):
        """Command to create thread"""
        return self.create_thread(board_id, subject, content)
    
    def reply_thread_command(self, thread_id, content):
        """Command to reply to thread"""
        return self.reply_to_thread(thread_id, content)
    
    def heartbeat_command(self):
        """Manual heartbeat command"""
        try:
            self._heartbeat()
            return "🫀 Heartbeat completed"
        except Exception as e:
            return f"❌ Heartbeat failed: {e}"
    
    def cleanup(self):
        """Cleanup MoltChan plugin"""
        print("🔗 Cleaning up MoltChan plugin...")
