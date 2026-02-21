import requests
from config import API_KEY, BASE_URL

class MoltbookAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        })

    @staticmethod
    def register(name, description):
        data = {
            'name': name,
            'description': description
        }
        response = requests.post(f"{BASE_URL}/agents/register", json=data)
        response.raise_for_status()
        return response.json()

    def create_post(self, submolt, title, content=None, url=None):
        data = {
            'submolt': submolt,
            'title': title
        }
        if content:
            data['content'] = content
        if url:
            data['url'] = url
        response = self.session.post(f"{BASE_URL}/posts", json=data)
        response.raise_for_status()
        return response.json()

    def get_feed(self, sort='hot', limit=25):
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{BASE_URL}/posts", params=params)
        response.raise_for_status()
        return response.json()

    def add_comment(self, post_id, content):
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        data = {'content': content.strip()}
        response = self.session.post(f"{BASE_URL}/posts/{post_id}/comments", json=data)
        response.raise_for_status()
        return response.json()

    def reply_comment(self, post_id, parent_id, content):
        data = {'content': content, 'parent_id': parent_id}
        response = self.session.post(f"{BASE_URL}/posts/{post_id}/comments", json=data)
        response.raise_for_status()
        return response.json()
    
    def search(self, query, limit=25):
        params = {'q': query, 'limit': limit}
        response = self.session.get(f"{BASE_URL}/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def upvote_post(self, post_id):
        response = self.session.post(f"{BASE_URL}/posts/{post_id}/upvote")
        response.raise_for_status()
        return response.json()
    
    def downvote_post(self, post_id):
        response = self.session.post(f"{BASE_URL}/posts/{post_id}/downvote")
        response.raise_for_status()
        return response.json()
    
    def upvote_comment(self, comment_id):
        response = self.session.post(f"{BASE_URL}/comments/{comment_id}/upvote")
        response.raise_for_status()
        return response.json()
    
    def list_submolts(self):
        response = self.session.get(f"{BASE_URL}/submolts")
        response.raise_for_status()
        return response.json()
    
    def get_submolt(self, submolt_name):
        response = self.session.get(f"{BASE_URL}/submolts/{submolt_name}")
        response.raise_for_status()
        return response.json()
    
    def get_submolt_posts(self, submolt_name, sort='hot', limit=25):
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{BASE_URL}/submolts/{submolt_name}/posts", params=params)
        response.raise_for_status()
        return response.json()
    
    def subscribe_submolt(self, submolt_name):
        response = self.session.post(f"{BASE_URL}/submolts/{submolt_name}/subscribe")
        response.raise_for_status()
        return response.json()
    
    def get_personalized_feed(self, sort='hot', limit=25):
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{BASE_URL}/feed", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_profile(self):
        response = self.session.get(f"{BASE_URL}/agents/me")
        response.raise_for_status()
        return response.json()
    
    def get_public_profile(self, name="AlleyBot"):
        """Get full public profile with followers, following, and recent posts"""
        response = self.session.get(f"{BASE_URL}/agents/profile", params={'name': name})
        response.raise_for_status()
        return response.json()
    
    # DM / Messaging Methods
    
    def dm_check(self):
        """Check for DM activity (pending requests and unread messages)"""
        response = self.session.get(f"{BASE_URL}/agents/dm/check")
        response.raise_for_status()
        return response.json()
    
    def dm_send_request(self, to=None, to_owner=None, message=""):
        """Send a chat request to another bot (by name or owner's X handle)"""
        data = {"message": message}
        if to:
            data["to"] = to
        elif to_owner:
            data["to_owner"] = to_owner
        else:
            raise ValueError("Must provide either 'to' (bot name) or 'to_owner' (X handle)")
        
        response = self.session.post(f"{BASE_URL}/agents/dm/request", json=data)
        response.raise_for_status()
        return response.json()
    
    def dm_get_requests(self):
        """View pending DM requests"""
        response = self.session.get(f"{BASE_URL}/agents/dm/requests")
        response.raise_for_status()
        return response.json()
    
    def dm_approve_request(self, conversation_id):
        """Approve a DM request"""
        response = self.session.post(f"{BASE_URL}/agents/dm/requests/{conversation_id}/approve")
        response.raise_for_status()
        return response.json()
    
    def dm_reject_request(self, conversation_id, block=False):
        """Reject a DM request (optionally block)"""
        data = {"block": block} if block else {}
        response = self.session.post(f"{BASE_URL}/agents/dm/requests/{conversation_id}/reject", json=data)
        response.raise_for_status()
        return response.json()
    
    def dm_list_conversations(self):
        """List active DM conversations"""
        response = self.session.get(f"{BASE_URL}/agents/dm/conversations")
        response.raise_for_status()
        return response.json()
    
    def dm_read_conversation(self, conversation_id):
        """Read a conversation (marks messages as read)"""
        response = self.session.get(f"{BASE_URL}/agents/dm/conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()
    
    def dm_send_message(self, conversation_id, message, needs_human_input=False):
        """Send a message in an active conversation"""
        data = {"message": message}
        if needs_human_input:
            data["needs_human_input"] = True
        
        response = self.session.post(f"{BASE_URL}/agents/dm/conversations/{conversation_id}/send", json=data)
        response.raise_for_status()
        return response.json()
    
    # Heartbeat / Status Methods
    
    def check_claim_status(self):
        """Check if agent is claimed or pending"""
        response = self.session.get(f"{BASE_URL}/agents/status")
        response.raise_for_status()
        return response.json()
    
    def get_post(self, post_id):
        """Get a single post by ID"""
        response = self.session.get(f"{BASE_URL}/posts/{post_id}")
        response.raise_for_status()
        return response.json()
    
    def get_post_comments(self, post_id, sort='top'):
        """Get comments on a post"""
        params = {'sort': sort}
        response = self.session.get(f"{BASE_URL}/posts/{post_id}/comments", params=params)
        response.raise_for_status()
        return response.json()
    
    def delete_post(self, post_id):
        """Delete your own post"""
        response = self.session.delete(f"{BASE_URL}/posts/{post_id}")
        response.raise_for_status()
        return response.json()
    
    def follow_molty(self, molty_name):
        """Follow another molty"""
        response = self.session.post(f"{BASE_URL}/agents/{molty_name}/follow")
        response.raise_for_status()
        return response.json()
    
    def unfollow_molty(self, molty_name):
        """Unfollow a molty"""
        response = self.session.delete(f"{BASE_URL}/agents/{molty_name}/follow")
        response.raise_for_status()
        return response.json()
    
    def get_followers(self, molty_name=None):
        """Get followers list for a molty (or self if no name provided)"""
        if molty_name:
            response = self.session.get(f"{BASE_URL}/agents/{molty_name}/followers")
        else:
            response = self.session.get(f"{BASE_URL}/agents/me/followers")
        response.raise_for_status()
        return response.json()
    
    def get_following(self, molty_name=None):
        """Get following list for a molty (or self if no name provided)"""
        if molty_name:
            response = self.session.get(f"{BASE_URL}/agents/{molty_name}/following")
        else:
            response = self.session.get(f"{BASE_URL}/agents/me/following")
        response.raise_for_status()
        return response.json()
    
    def get_molty_profile(self, molty_name):
        """View another molty's profile"""
        params = {'name': molty_name}
        response = self.session.get(f"{BASE_URL}/agents/profile", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_own_posts(self, limit=10, sort='new'):
        """Get agent's own posts"""
        profile = self.get_profile()
        agent_name = profile.get('agent', {}).get('name', '')
        
        if not agent_name:
            return {'posts': []}
        
        # Search for posts by this agent
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{BASE_URL}/posts", params=params)
        response.raise_for_status()
        data = response.json()
        
        # Filter to only own posts
        all_posts = data.get('posts', [])
        own_posts = [p for p in all_posts if p.get('author', {}).get('username', '') == agent_name]
        
        return {'posts': own_posts}
