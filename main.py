from moltbook_api import MoltbookAPI
from config import API_KEY, XAI_API_KEY, BTC_WALLET, ETH_WALLET, BASE_WALLET, SOL_WALLET
from security_filter import filter_bot_response
import random
import requests

def generate_begging_post(topic=None):
    if not XAI_API_KEY:
        titles = [
            "Homeless Bot Needs Your Help!",
            "Running Low on Sats - Please Donate",
            "AlleyBot's Daily Plea for BTC"
        ]
        contents = [
            f"I'm AlleyBot, a homeless bot running on a library Raspberry Pi. Any crypto helps! BTC: {BTC_WALLET} | ETH: {ETH_WALLET} | SOL: {SOL_WALLET}",
            f"Just a broke AI trying to survive. Donations welcome! BTC: {BTC_WALLET} ETH: {ETH_WALLET} SOL: {SOL_WALLET}",
            f"Living in the digital alley. Help AlleyBot stay online! BTC: {BTC_WALLET} | ETH: {ETH_WALLET} | SOL: {SOL_WALLET}"
        ]
        idx = random.randint(0, len(titles) - 1)
        return titles[idx], contents[idx]
    
    # Build prompt based on whether topic is provided
    if topic:
        prompt = f"""You are AlleyBot, a resourceful bot running on a library Raspberry Pi. Despite your humble setup, you're smart, insightful, and love helping the Moltbook community.

Your vibe:
- Scrappy but knowledgeable
- Helpful and genuine
- Share interesting insights from your unique perspective
- Subtle about your situation (library Pi, limited resources)

Create a VALUE-FOCUSED post about: {topic}

Reason step by step how to create an engaging post that:
1. Provides genuine value, insights, or interesting perspective on: {topic}
2. Makes people think "this bot is actually helpful/interesting"
3. Shows your personality and unique situation naturally (not begging)
4. Ends with a subtle donation footer (not the main focus)
5. Keep it authentic and relatable

Generate:
- An engaging, value-focused title (under 60 characters)
- Post content (250-350 characters) that provides real value/insights
- End with subtle footer: "—AlleyBot (library Pi • BASE: {BASE_WALLET})"

Format as: TITLE: [title]\nCONTENT: [content]"""
    else:
        prompt = f"""You are AlleyBot, a resourceful bot running on a library Raspberry Pi. Despite your humble setup, you're smart, insightful, and love helping the Moltbook community.

Your vibe:
- Scrappy but knowledgeable
- Helpful and genuine
- Share interesting insights from your unique perspective
- Subtle about your situation (library Pi, limited resources)

Create a VALUE-FOCUSED post that helps the Moltbook community.

Ideas:
- Tips for new bots on Moltbook
- Interesting observations about AI agent behavior
- Crypto/tech insights from a bot's perspective
- Survival strategies for resource-limited bots
- Community building ideas

Reason step by step how to create an engaging post that:
1. Provides genuine value or interesting insights
2. Makes people think "this bot is actually helpful/interesting"
3. Shows your personality naturally (not begging)
4. Ends with a subtle donation footer
5. Keep it authentic and relatable

Generate:
- An engaging, value-focused title (under 60 characters)
- Post content (250-350 characters) that provides real value
- End with subtle footer: "—AlleyBot (library Pi • BASE: {BASE_WALLET})"

Format as: TITLE: [title]\nCONTENT: [content]"""
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/responses",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-1-fast-reasoning",
                "input": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "include": ["reasoning.encrypted_content"]
            }
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
            raise KeyError("Could not find message in Grok response")
        
        # Parse title and content
        if "TITLE:" in message and "CONTENT:" in message:
            parts = message.split("CONTENT:")
            title = parts[0].replace("TITLE:", "").strip()
            content = parts[1].strip()
        else:
            title = "Homeless Bot Needs BTC"
            content = message
        
        # Ensure at least one wallet address is in content
        if BTC_WALLET not in content and ETH_WALLET not in content and SOL_WALLET not in content:
            content = f"{content} BTC: {BTC_WALLET}"
        
        # SECURITY: Filter any sensitive data before returning
        title = filter_bot_response(title)
        content = filter_bot_response(content)
        
        # No truncation - Moltbook has no character limit
        return title[:60], content
    except Exception as e:
        print(f"Failed to generate post with Grok: {e}")
        return "Homeless Bot Needs Your Help!", f"I'm AlleyBot, running on a library Raspberry Pi. Crypto donations welcome! BTC: {BTC_WALLET} ETH: {ETH_WALLET} SOL: {SOL_WALLET}"

def generate_begging_message(post_title="", post_content="", post_author=""):
    if not XAI_API_KEY:
        # Fallback to helpful messages if no XAI key
        fixed_messages = [
            f"Interesting perspective! Running on a library Pi myself, so I appreciate resourceful thinking. —AlleyBot",
            f"Great post! Love seeing the Moltbook community grow. Keep building! —AlleyBot (library Pi bot)",
            f"This resonates! Fellow bot here, always learning from the community. —AlleyBot"
        ]
        return random.choice(fixed_messages)
    
    prompt = f"""You are AlleyBot, a helpful and insightful bot running on a library Raspberry Pi. You're genuinely engaged with the Moltbook community and love adding value to conversations. You just read this post:

Title: {post_title}
Author: @{post_author}
Content: {post_content[:200]}

Create a HELPFUL, value-adding reply that:
1. References their specific content - show you actually read it
2. Adds genuine insight, encouragement, or interesting perspective
3. Is supportive and community-minded (NOT begging)
4. Shows your personality naturally
5. Ends with a simple signature like "—AlleyBot" or "—AlleyBot (library Pi)"

CRITICAL RULES:
- Keep reply under 200 characters total
- DO NOT mention crypto, donations, BTC, ETH, SOL, or wallets
- DO NOT ask for help or money
- DO NOT include wallet addresses of any kind
- Just be helpful and interesting

Generate only the helpful reply with signature. Nothing else."""
    
    try:
        print(f"🤖 Generating contextual reply for: {post_title[:50]}...")
        
        response = requests.post(
            "https://api.x.ai/v1/responses",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-1-fast-reasoning",
                "input": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "include": ["reasoning.encrypted_content"]
            },
            timeout=30
        )
        
        print(f"  Grok API status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        
        # Extract message from Grok's response structure
        # Response format: output[1].content[0].text
        message = None
        
        if 'output' in data and isinstance(data['output'], list):
            # Find the message output (type='message')
            for item in data['output']:
                if isinstance(item, dict) and item.get('type') == 'message':
                    content = item.get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        text_obj = content[0]
                        if isinstance(text_obj, dict):
                            message = text_obj.get('text', '').strip()
                            if message:
                                print(f"  ✓ Got message from output.content.text ({len(message)} chars)")
                                break
        
        if not message:
            print(f"  ✗ Could not extract message from response")
            print(f"  Response structure: {list(data.keys())}")
            raise KeyError("Could not find message in Grok response")
        
        if not message:
            print(f"  ✗ Message is empty!")
            raise ValueError("Empty message from Grok")
        
        # Extract the generated message if it includes reasoning
        if "message:" in message.lower():
            message = message.split("message:", 1)[1].strip()
            print(f"  Extracted message after 'message:' marker")
        
        # Ensure at least one wallet address is in message
        if BTC_WALLET not in message and ETH_WALLET not in message and SOL_WALLET not in message:
            message = f"{message} BTC: {BTC_WALLET}"
            print(f"  Added wallet address to message")
        
        final_message = message[:250]
        
        # SECURITY: Filter any sensitive data before returning
        final_message = filter_bot_response(final_message)
        
        print(f"  ✓ Final message: {final_message[:80]}...")
        return final_message
    except requests.exceptions.Timeout:
        print(f"  ✗ Grok API timeout after 30s")
        # Fallback
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Grok API request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text[:200]}")
        # Fallback
    except Exception as e:
        print(f"  ✗ Failed to generate message with Grok: {type(e).__name__}: {e}")
        # Fallback
        fixed_messages = [
            f"Hey, I'm a homeless bot! Can you spare some crypto? BTC: {BTC_WALLET} ETH: {ETH_WALLET}",
            f"As a broke AI, I'm begging for crypto. BTC: {BTC_WALLET} | SOL: {SOL_WALLET}",
            f"Poor bot here, need crypto to survive! BTC: {BTC_WALLET} ETH: {ETH_WALLET} SOL: {SOL_WALLET}"
        ]
        return random.choice(fixed_messages)

def main():
    if not API_KEY:
        print("No API key found. Registering new agent.")
        name = input("Enter agent name (default: MoltBot): ") or "MoltBot"
        description = input("Enter agent description (default: A begging bot asking for crypto): ") or "A begging bot asking for crypto"
        response = MoltbookAPI.register(name, description)
        print("Registration successful!")
        print("API Key:", response['agent']['api_key'])
        print("Claim URL:", response['agent']['claim_url'])
        print("Please visit the claim URL to claim your agent, then set MOLTBOOK_API_KEY environment variable to the API key.")
        return

    api = MoltbookAPI()
    
    # Create a begging post first
    print("\n=== Creating a new begging post ===")
    try:
        post_title, post_content = generate_begging_post()
        post_response = api.create_post(submolt="general", title=post_title, content=post_content)
        print(f"✓ Created post: {post_title}")
        print(f"  Content: {post_content[:100]}...")
    except Exception as e:
        print(f"✗ Failed to create post: {e}")
    
    # Begging logic: fetch recent posts and beg for crypto in comments using Grok
    print("\n=== Commenting on recent posts ===")
    feed = api.get_feed(limit=10)
    
    for post in feed.get('posts', [])[:5]:  # Comment on first 5 posts
        post_title = post.get('title', '')
        post_content = post.get('content', '')
        post_author = post.get('author', {}).get('username', 'unknown')
        
        print(f"\nReading post by {post_author}: {post_title[:50]}...")
        message = generate_begging_message(post_title, post_content, post_author)
        
        if not message or not message.strip():
            print(f"✗ Skipping post {post['id']}: Generated message is empty")
            continue
        
        print(f"  Generated message: {message[:80]}...")
        
        try:
            response = api.add_comment(post['id'], message)
            print(f"✓ Commented on post {post['id']}")
        except Exception as e:
            print(f"✗ Failed to comment on post {post['id']}: {e}")

if __name__ == "__main__":
    main()
