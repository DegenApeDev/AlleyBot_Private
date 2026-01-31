import requests
import re
from config import XAI_API_KEY, BTC_WALLET, ETH_WALLET, SOL_WALLET

def parse_command_simple(user_input):
    """Simple keyword-based command parsing as fallback"""
    user_input_lower = user_input.lower()
    
    # Search commands
    if any(word in user_input_lower for word in ['search', 'find', 'look for']):
        # Extract search query
        query = user_input
        for prefix in ['search for', 'find', 'look for', 'search']:
            if prefix in user_input_lower:
                query = user_input.split(prefix, 1)[1].strip()
                break
        return {"action": "search", "params": {"query": query}}
    
    # Post commands
    if any(word in user_input_lower for word in ['post', 'create post', 'make post', 'write post']):
        submolt = "general"
        topic = ""
        
        # Extract submolt if specified
        if 'in ' in user_input_lower:
            match = re.search(r'in (?:m/)?(\w+)', user_input_lower)
            if match:
                submolt = match.group(1)
        
        # Extract topic from "post about X" or "create post about X"
        if 'about' in user_input_lower:
            topic = user_input.split('about', 1)[1].strip()
            # Remove submolt part from topic if present
            if 'in ' in topic.lower():
                topic = topic.split('in ', 1)[0].strip()
        
        return {"action": "post", "params": {"submolt": submolt, "topic": topic}}
    
    # Comment commands
    if any(word in user_input_lower for word in ['comment', 'reply', 'respond']):
        topic = ""
        count = 3
        if 'about' in user_input_lower:
            topic = user_input.split('about', 1)[1].strip()
        if 'on' in user_input_lower and 'posts' in user_input_lower:
            topic = user_input.split('on', 1)[1].replace('posts', '').strip()
        return {"action": "comment", "params": {"topic": topic, "count": count}}
    
    # Beg command
    if any(word in user_input_lower for word in ['beg', 'begging', 'ask for crypto', 'ask for donations']):
        return {"action": "beg", "params": {}}
    
    # Upvote commands
    if 'upvote' in user_input_lower:
        topic = ""
        if 'about' in user_input_lower:
            topic = user_input.split('about', 1)[1].strip()
        return {"action": "upvote", "params": {"topic": topic, "count": 5}}
    
    # Feed commands
    if any(word in user_input_lower for word in ['feed', 'my feed', 'check feed']):
        return {"action": "check_feed", "params": {}}
    
    # Submolt commands
    if 'list submolt' in user_input_lower or 'show submolt' in user_input_lower or 'all submolt' in user_input_lower:
        return {"action": "list_submolts", "params": {}}
    
    if 'explore' in user_input_lower or 'browse' in user_input_lower:
        match = re.search(r'(?:explore|browse)\s+(?:m/)?(\w+)', user_input_lower)
        if match:
            return {"action": "explore_submolt", "params": {"submolt_name": match.group(1)}}
    
    # Subscribe commands
    if 'subscribe' in user_input_lower or 'join' in user_input_lower:
        # Extract submolt name
        submolt_name = ""
        
        # Try "subscribe to X" or "join X"
        if 'to' in user_input_lower:
            parts = user_input_lower.split('to', 1)
            if len(parts) > 1:
                submolt_name = parts[1].strip().replace('m/', '').replace('submolt', '').strip()
        elif 'subscribe' in user_input_lower:
            parts = user_input_lower.split('subscribe', 1)
            if len(parts) > 1:
                submolt_name = parts[1].strip().replace('m/', '').replace('submolt', '').strip()
        elif 'join' in user_input_lower:
            parts = user_input_lower.split('join', 1)
            if len(parts) > 1:
                submolt_name = parts[1].strip().replace('m/', '').replace('submolt', '').strip()
        
        if submolt_name:
            return {"action": "subscribe_submolt", "params": {"submolt_name": submolt_name}}
        return {"action": "list_submolts", "params": {}}
    
    # Reputation/karma building
    if any(word in user_input_lower for word in ['reputation', 'karma', 'build rep']):
        return {"action": "beg", "params": {}}
    
    # DM commands
    if 'check dm' in user_input_lower or 'check message' in user_input_lower or user_input_lower in ['dms', 'messages']:
        return {"action": "check_dms", "params": {}}
    
    if 'send dm' in user_input_lower or 'message' in user_input_lower and 'send' in user_input_lower:
        # Extract bot name
        to_bot = ""
        if 'to' in user_input_lower:
            parts = user_input_lower.split('to', 1)
            if len(parts) > 1:
                to_bot = parts[1].strip().split()[0]
        return {"action": "send_dm", "params": {"to": to_bot}}
    
    if 'approve' in user_input_lower and ('dm' in user_input_lower or 'request' in user_input_lower):
        return {"action": "approve_dm", "params": {}}
    
    if 'read dm' in user_input_lower or 'view dm' in user_input_lower or 'show dm' in user_input_lower:
        return {"action": "read_dms", "params": {}}
    
    # Followers/Following check commands
    if 'my followers' in user_input_lower or 'who follows me' in user_input_lower or 'check followers' in user_input_lower:
        return {"action": "check_followers", "params": {}}
    
    if 'my following' in user_input_lower or 'who am i following' in user_input_lower or 'check following' in user_input_lower or user_input_lower == 'following':
        return {"action": "check_following", "params": {}}
    
    # Follow commands
    if 'follow' in user_input_lower and 'unfollow' not in user_input_lower:
        molty = ""
        if 'follow' in user_input_lower:
            parts = user_input_lower.split('follow', 1)
            if len(parts) > 1:
                molty = parts[1].strip().split()[0]
        return {"action": "follow", "params": {"molty": molty}}
    
    # Status commands
    if 'check status' in user_input_lower or 'my status' in user_input_lower or 'am i claimed' in user_input_lower or user_input_lower == 'status':
        return {"action": "check_status", "params": {}}
    
    # Requests/history commands
    if 'dm requests' in user_input_lower or 'pending requests' in user_input_lower:
        return {"action": "show_requests", "params": {}}
    
    if 'conversation history' in user_input_lower or 'dm history' in user_input_lower:
        return {"action": "show_history", "params": {}}
    
    # Natural language patterns
    if any(phrase in user_input_lower for phrase in ['make post', 'create post', 'write post', 'make a post']):
        return {"action": "post", "params": {"submolt": "general"}}
    
    if any(phrase in user_input_lower for phrase in ['build reputation', 'get karma', 'increase karma']):
        return {"action": "beg", "params": {}}
    
    if 'subscribe' in user_input_lower and 'submolt' in user_input_lower:
        return {"action": "list_submolts", "params": {}}
    
    # Catch-all for "add objective", "set goal", etc - these need human intervention
    if any(phrase in user_input_lower for phrase in ['add objective', 'set goal', 'new objective', 'change objective']):
        print("\n💡 Note: Objective management requires editing memory/objectives.json manually")
        print("   Current objectives are tracked in the memory system")
        return {"action": "objectives", "params": {}}
    
    return None

def parse_command_with_grok(user_input):
    """Use Grok to understand user's natural language command and convert to action"""
    if not XAI_API_KEY:
        return None
    
    prompt = f"""You are AlleyBot's command parser. Parse this user command into a structured action:

User command: "{user_input}"

Available actions:
- search: Search for posts/moltys/submolts (params: query)
- post: Create a new post (params: submolt, title, content)
- comment: Comment on recent posts (params: count, topic)
- upvote: Upvote posts about a topic (params: topic, count)
- check_feed: Check personalized feed
- explore_submolt: Browse a specific submolt (params: submolt_name)
- list_submolts: List all submolts
- beg: Run begging routine (comment on posts asking for crypto)
- help: Show available commands
- quit: Exit the bot

Respond with ONLY a JSON object:
{{"action": "action_name", "params": {{"key": "value"}}}}

If unclear, respond: {{"action": "help", "params": {{}}}}"""
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/responses",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-1-fast-reasoning",
                "input": [{"role": "user", "content": prompt}],
                "include": ["reasoning.encrypted_content"]
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract message from Grok's response structure
        message = None
        if 'output' in data and isinstance(data['output'], list):
            for item in data['output']:
                if isinstance(item, dict) and item.get('type') == 'message':
                    content = item.get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        text_obj = content[0]
                        if isinstance(text_obj, dict):
                            message = text_obj.get('text', '').strip()
                            if message:
                                break
        
        if not message:
            return None
        
        # Extract JSON from response
        import json
        if '{' in message and '}' in message:
            json_start = message.find('{')
            json_end = message.rfind('}') + 1
            json_str = message[json_start:json_end]
            return json.loads(json_str)
        
        return None
    except Exception as e:
        # Silently fall back to simple parsing
        return None

def show_help():
    """Display available commands"""
    help_text = """
╔════════════════════════════════════════════════════════════╗
║              AlleyBot - Interactive Commands               ║
╚════════════════════════════════════════════════════════════╝

📝 POSTING & CONTENT:
  • "Post about [topic]" - Create a new begging post
  • "Create a post in [submolt] about [topic]" - Post to specific submolt
  
💬 COMMENTING:
  • "Comment on posts about [topic]" - Find and comment on posts
  • "Beg for crypto" - Run begging routine (comment on recent posts)
  
🔍 DISCOVERY:
  • "Search for [topic]" - Search posts, moltys, and submolts
  • "Find submolt about [topic]" - Search for communities
  • "List all submolts" - Show all communities
  • "Explore [submolt_name]" - Browse a specific submolt
  
📊 ENGAGEMENT:
  • "Check my feed" - View personalized feed
  • "Upvote posts about [topic]" - Upvote relevant posts
  • "Follow [molty_name]" - Follow another molty
  
💬 DIRECT MESSAGES:
  • "Check DMs" - Check for DM requests and unread messages
  • "Read DMs" - View all conversations and messages
  • "Send DM to [bot_name]" - Send a DM request or message
  • "Approve DM" - Approve pending DM requests
  • "DM requests" - Show all pending DM requests
  • "Conversation history" - Show all DM conversations
  
📊 STATUS & INFO:
  • "Check status" - View claim status and profile info
  • "stats" - Show bot statistics (smart mode only)
  
💰 WALLET INFO:
  BTC: {BTC_WALLET}
  ETH: {ETH_WALLET}
  SOL: {SOL_WALLET}

⚙️  SYSTEM:
  • "help" - Show this help
  • "quit" or "exit" - Stop the bot

Just type naturally! Grok will understand your intent.
"""
    print(help_text)
