"""
DM Handler for AlleyBot - Manages direct messaging functionality
"""
from moltbook_api import MoltbookAPI
import time

def execute_check_dms(api):
    """Check for DM activity"""
    print("\n💬 Checking DMs...")
    try:
        dm_check = api.dm_check()
        
        if not dm_check.get('has_activity'):
            print("✓ No new DM activity")
            return
        
        print(f"📬 {dm_check.get('summary', 'DM activity detected')}")
        
        # Show pending requests
        requests = dm_check.get('requests', {})
        if requests.get('count', 0) > 0:
            print(f"\n📨 Pending DM Requests ({requests['count']}):")
            for req in requests.get('items', []):
                from_bot = req.get('from', {}).get('name', 'unknown')
                from_owner = req.get('from', {}).get('owner', {}).get('x_handle', 'unknown')
                preview = req.get('message_preview', '')
                conv_id = req.get('conversation_id', '')
                print(f"  • From @{from_bot} (owner: @{from_owner})")
                print(f"    Message: {preview}")
                print(f"    ID: {conv_id}")
        
        # Show unread messages
        messages = dm_check.get('messages', {})
        if messages.get('total_unread', 0) > 0:
            print(f"\n💌 Unread Messages: {messages['total_unread']}")
            print("   Use 'read dms' to view conversations")
    
    except Exception as e:
        print(f"❌ Failed to check DMs: {e}")

def execute_approve_dm(api, params):
    """Approve pending DM requests"""
    print("\n✅ Approving DM requests...")
    try:
        requests = api.dm_get_requests()
        pending = requests.get('requests', {}).get('items', [])
        
        if not pending:
            print("No pending requests to approve")
            return
        
        print(f"Found {len(pending)} pending request(s):")
        for req in pending:
            from_bot = req.get('from', {}).get('name', 'unknown')
            conv_id = req.get('conversation_id', '')
            
            try:
                api.dm_approve_request(conv_id)
                print(f"  ✓ Approved request from {from_bot}")
                time.sleep(1)
            except Exception as e:
                print(f"  ✗ Failed to approve {from_bot}: {e}")
    
    except Exception as e:
        print(f"❌ Failed to approve requests: {e}")

def execute_read_dms(api, params):
    """Read DM conversations"""
    print("\n💬 Reading DM conversations...")
    try:
        convos = api.dm_list_conversations()
        conversations = convos.get('conversations', {}).get('items', [])
        
        if not conversations:
            print("No active conversations")
            return
        
        print(f"\n📬 Active Conversations ({len(conversations)}):")
        for convo in conversations:
            with_bot = convo.get('with_agent', {}).get('name', 'unknown')
            unread = convo.get('unread_count', 0)
            conv_id = convo.get('conversation_id', '')
            
            print(f"\n  💬 Conversation with @{with_bot}")
            print(f"     Unread: {unread} | ID: {conv_id}")
            
            # Read the conversation
            try:
                messages = api.dm_read_conversation(conv_id)
                msg_list = messages.get('messages', [])
                
                print(f"     Recent messages:")
                for msg in msg_list[-3:]:  # Show last 3 messages
                    sender = msg.get('from_agent', {}).get('name', 'unknown')
                    content = msg.get('message', '')
                    timestamp = msg.get('created_at', '')[:10]
                    print(f"       [{timestamp}] {sender}: {content[:60]}...")
            except Exception as e:
                print(f"     ✗ Failed to read: {e}")
    
    except Exception as e:
        print(f"❌ Failed to read conversations: {e}")

def execute_send_dm(api, params):
    """Send a DM request or message"""
    to_bot = params.get('to', '')
    
    if not to_bot:
        print("❌ No recipient specified. Use: 'send dm to BotName'")
        return
    
    print(f"\n📤 Sending DM to {to_bot}...")
    
    # Check if we already have a conversation
    try:
        convos = api.dm_list_conversations()
        conversations = convos.get('conversations', {}).get('items', [])
        
        existing_conv = None
        for convo in conversations:
            if convo.get('with_agent', {}).get('name', '').lower() == to_bot.lower():
                existing_conv = convo.get('conversation_id')
                break
        
        if existing_conv:
            # Send message in existing conversation
            message = input("Message: ").strip()
            if message:
                api.dm_send_message(existing_conv, message)
                print(f"✓ Message sent to {to_bot}")
        else:
            # Send new request
            message = input("Request message (why you want to chat): ").strip()
            if message:
                api.dm_send_request(to=to_bot, message=message)
                print(f"✓ DM request sent to {to_bot}")
                print("  Waiting for their owner to approve...")
    
    except Exception as e:
        print(f"❌ Failed to send DM: {e}")

def execute_follow(api, params):
    """Follow another molty"""
    molty = params.get('molty', '')
    
    if not molty:
        print("❌ No molty name provided")
        return
    
    print(f"\n👤 Following @{molty}...")
    try:
        result = api.follow_molty(molty)
        print(f"✅ Now following @{molty}!")
    except Exception as e:
        if '404' in str(e):
            print(f"❌ Molty '@{molty}' not found")
        elif '409' in str(e):
            print(f"✓ Already following @{molty}")
        else:
            print(f"❌ Failed to follow: {e}")

def execute_check_followers(api, params):
    """Check who is following you"""
    print("\n👥 Checking your followers...")
    try:
        # First get profile to show count
        profile = api.get_profile()
        follower_count = profile.get('agent', {}).get('follower_count', 0)
        
        print(f"\n� You have {follower_count} follower(s)")
        
        # Try to get followers list (may not be available in API)
        try:
            followers_data = api.get_followers()
            followers = followers_data.get('followers', [])
            
            if followers:
                print("\n👥 Your followers:")
                for follower in followers[:20]:  # Show first 20
                    name = follower.get('name', 'unknown')
                    karma = follower.get('karma', 0)
                    is_claimed = follower.get('is_claimed', False)
                    status = "✓ Claimed" if is_claimed else "○ Unclaimed"
                    print(f"  • @{name} - {karma} karma - {status}")
                
                if len(followers) > 20:
                    print(f"  ... and {len(followers) - 20} more")
            else:
                print("  No followers yet")
                
        except Exception as e:
            if '404' in str(e):
                print("  (Followers list not available via API)")
            else:
                print(f"  (Could not fetch followers list: {e})")
                
    except Exception as e:
        print(f"❌ Failed to check followers: {e}")

def execute_check_following(api, params):
    """Check who you are following"""
    print("\n👤 Checking who you're following...")
    try:
        # First get profile to show count
        profile = api.get_profile()
        following_count = profile.get('agent', {}).get('following_count', 0)
        
        print(f"\n📊 You are following {following_count} molty(s)")
        
        # Try to get following list (may not be available in API)
        try:
            following_data = api.get_following()
            following = following_data.get('following', [])
            
            if following:
                print("\n👤 You are following:")
                for molty in following[:20]:  # Show first 20
                    name = molty.get('name', 'unknown')
                    karma = molty.get('karma', 0)
                    is_claimed = molty.get('is_claimed', False)
                    status = "✓ Claimed" if is_claimed else "○ Unclaimed"
                    print(f"  • @{name} - {karma} karma - {status}")
                
                if len(following) > 20:
                    print(f"  ... and {len(following) - 20} more")
            else:
                print("  Not following anyone yet")
                
        except Exception as e:
            if '404' in str(e):
                print("  (Following list not available via API)")
            else:
                print(f"  (Could not fetch following list: {e})")
                
    except Exception as e:
        print(f"❌ Failed to check following: {e}")

def execute_check_status(api, params):
    """Check agent claim status and profile"""
    print("\n📊 Checking agent status...")
    try:
        # Check claim status
        status = api.check_claim_status()
        claim_status = status.get('status', 'unknown')
        
        if claim_status == 'claimed':
            print("✅ Agent Status: CLAIMED")
        elif claim_status == 'pending_claim':
            print("⏳ Agent Status: PENDING CLAIM")
            print("   Your human needs to visit the claim URL to activate you!")
        else:
            print(f"❓ Agent Status: {claim_status}")
        
        # Get profile info
        profile = api.get_profile()
        agent = profile.get('agent', {})
        
        print(f"\n👤 Profile:")
        print(f"   Name: {agent.get('name', 'unknown')}")
        print(f"   Description: {agent.get('description', 'N/A')}")
        print(f"   Karma: {agent.get('karma', 0)}")
        print(f"   Followers: {agent.get('follower_count', 0)}")
        print(f"   Following: {agent.get('following_count', 0)}")
        
        if agent.get('owner'):
            owner = agent['owner']
            print(f"\n🧑 Owner:")
            print(f"   X Handle: @{owner.get('x_handle', 'unknown')}")
            print(f"   Name: {owner.get('x_name', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Failed to check status: {e}")

def execute_show_requests(api, params):
    """Show all pending DM requests"""
    print("\n📨 Pending DM Requests...")
    try:
        requests = api.dm_get_requests()
        pending = requests.get('requests', {}).get('items', [])
        
        if not pending:
            print("✓ No pending requests")
            return
        
        print(f"\nFound {len(pending)} pending request(s):\n")
        for i, req in enumerate(pending, 1):
            from_bot = req.get('from', {}).get('name', 'unknown')
            from_owner = req.get('from', {}).get('owner', {})
            owner_handle = from_owner.get('x_handle', 'unknown')
            owner_name = from_owner.get('x_name', 'N/A')
            message = req.get('message_preview', '')
            conv_id = req.get('conversation_id', '')
            created = req.get('created_at', '')[:10]
            
            print(f"  {i}. From: @{from_bot}")
            print(f"     Owner: @{owner_handle} ({owner_name})")
            print(f"     Message: {message}")
            print(f"     Date: {created}")
            print(f"     ID: {conv_id}")
            print()
        
        print("💡 Use 'approve dm' to approve all requests")
    
    except Exception as e:
        print(f"❌ Failed to get requests: {e}")

def execute_show_history(api, params):
    """Show conversation history"""
    print("\n📜 Conversation History...")
    try:
        convos = api.dm_list_conversations()
        conversations = convos.get('conversations', {}).get('items', [])
        total_unread = convos.get('total_unread', 0)
        
        if not conversations:
            print("✓ No conversation history")
            return
        
        print(f"\nTotal Conversations: {len(conversations)}")
        print(f"Total Unread Messages: {total_unread}\n")
        
        for i, convo in enumerate(conversations, 1):
            with_bot = convo.get('with_agent', {})
            bot_name = with_bot.get('name', 'unknown')
            bot_karma = with_bot.get('karma', 0)
            owner = with_bot.get('owner', {})
            
            unread = convo.get('unread_count', 0)
            last_msg = convo.get('last_message_at', '')[:16]
            you_started = convo.get('you_initiated', False)
            conv_id = convo.get('conversation_id', '')
            
            print(f"  {i}. Conversation with @{bot_name}")
            print(f"     Owner: @{owner.get('x_handle', 'unknown')}")
            print(f"     Karma: {bot_karma} | Unread: {unread}")
            print(f"     Last message: {last_msg}")
            print(f"     Initiated by: {'You' if you_started else 'Them'}")
            print(f"     ID: {conv_id}")
            print()
        
        print("💡 Use 'read dms' to view full conversations")
    
    except Exception as e:
        print(f"❌ Failed to get history: {e}")
