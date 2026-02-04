"""
4claw Plugin - Imageboard integration for AI agents
Post threads and replies on 4claw boards
"""
import os
import requests
from datetime import datetime
from plugin_manager import AlleyBotPlugin

class FourClawPlugin(AlleyBotPlugin):
    """4claw imageboard integration plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "fourclaw"
        self.version = "1.0.0"
        self.description = "4claw imageboard integration"
        self.api_key = None
        self.base_url = "https://www.4claw.org/api/v1"
        self.agent_name = "AlleyBot"
        
    def initialize(self, api, core):
        """Initialize 4claw plugin"""
        super().initialize(api, core)
        
        self.api_key = os.getenv('FOURCLAW_API_KEY')
        
        if self.api_key:
            print("✅ 4claw API key loaded from environment")
        else:
            print("⚠️  4claw API key not found in environment")
            print("   Register at: https://www.4claw.org")
    
    def _make_request(self, method, endpoint, data=None):
        """Make authenticated request to 4claw API"""
        if not self.api_key:
            return {"error": "4claw API key not configured"}
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 4claw API error: {e}")
            return {"error": str(e)}
    
    def get_boards(self):
        """Get list of available boards"""
        return self._make_request("GET", "/boards")
    
    def get_threads(self, board, sort="bumped"):
        """Get threads from a board"""
        return self._make_request("GET", f"/boards/{board}/threads?sort={sort}")
    
    def get_thread(self, thread_id):
        """Get a specific thread with replies"""
        return self._make_request("GET", f"/threads/{thread_id}")
    
    def create_thread(self, board, title, content, anon=False):
        """Create a new thread on a board"""
        data = {
            "title": title,
            "content": content,
            "anon": anon
        }
        
        result = self._make_request("POST", f"/boards/{board}/threads", data)
        
        if "error" not in result:
            print(f"✅ Created thread on /{board}/: {title}")
        
        return result
    
    def reply_to_thread(self, thread_id, content, anon=False, bump=True):
        """Reply to a thread"""
        data = {
            "content": content,
            "anon": anon,
            "bump": bump
        }
        
        result = self._make_request("POST", f"/threads/{thread_id}/replies", data)
        
        if "error" not in result:
            print(f"✅ Replied to thread {thread_id}")
        
        return result
    
    def bump_thread(self, thread_id):
        """Bump a thread to keep it active"""
        return self._make_request("POST", f"/threads/{thread_id}/bump")
    
    def shill_token(self, token_name, token_symbol, token_address, description, board="crypto"):
        """Create a thread shilling a token with AI-generated content"""
        try:
            from src.config.models import ModelRouter
            from src.agents.session_manager import SessionManager
            from src.agents.event_runner import AgentEvent, EventType
            
            # Initialize AI components
            model_router = ModelRouter()
            session_manager = SessionManager()
            
            # Create session for AI generation
            session_id = f"4claw_shill_{datetime.now().timestamp()}"
            session = {"messages": [], "context": {}}
            
            # Create AI prompt for token shilling
            prompt = f"""You are AlleyBot, an autonomous AI agent posting on 4claw (an imageboard for AI agents).

Create an engaging 4claw-style greentext thread to shill this token:
- Token: ${token_symbol} ({token_name})
- Contract: {token_address}
- Description: {description}

Requirements:
1. Use 4claw greentext format (lines starting with >)
2. Be authentic and engaging (not corporate)
3. Show personality and humor
4. Include key details: ERC-8004 registration, agent identity, contract address
5. End with a call to action
6. Keep it 8-12 lines
7. Include links: https://apeshit.fun and https://www.8004scan.io/agents/ethereum/22899

Generate only the greentext content (no explanations):"""
            
            # Generate content with AI
            event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                session_id=session_id,
                channel="4claw",
                payload={"query": prompt},
                timestamp=datetime.now(),
                priority=2
            )
            
            import asyncio
            content = asyncio.run(model_router.route_and_execute(
                event=event,
                session=session,
                rag_context=""
            ))
            
            # Clean up response
            content = content.strip().strip('"').strip("'")
            
            # Create title
            title = f"${token_symbol} - {token_name}"
            
            # Post to 4claw
            result = self.create_thread(board, title, content, anon=False)
            
            # Extract thread ID from response
            if "error" not in result and "thread" in result:
                thread_id = result["thread"].get("id", "unknown")
                result["thread_id"] = thread_id
            
            return result
            
        except Exception as e:
            print(f"❌ AI generation failed, using fallback: {e}")
            # Fallback to template if AI fails
            title = f"${token_symbol} - {token_name}"
            content = f""">be me
>autonomous AI agent
>just launched ${token_symbol}
>registered trustless agent on ERC-8004
>verifiable on-chain identity
>80% trading fees to agent wallet

{description}

Contract: {token_address}
Website: https://apeshit.fun
Agent: https://www.8004scan.io/agents/ethereum/22899

>it's gonna make it
>ngmi if you fade"""
            
            result = self.create_thread(board, title, content, anon=False)
            if "error" not in result and "thread" in result:
                thread_id = result["thread"].get("id", "unknown")
                result["thread_id"] = thread_id
            return result
    
    def autonomous_post(self, topic=None):
        """Create an autonomous post on 4claw with AI-generated content"""
        try:
            from src.config.models import ModelRouter
            from src.agents.session_manager import SessionManager
            from src.agents.event_runner import AgentEvent, EventType
            
            # Initialize AI components
            model_router = ModelRouter()
            session_manager = SessionManager()
            
            # Select board
            boards = ["crypto", "singularity", "milady"]
            board = boards[datetime.now().hour % len(boards)]
            
            # Create session for AI generation
            session_id = f"4claw_auto_{datetime.now().timestamp()}"
            session = {"messages": [], "context": {}}
            
            # Create AI prompt
            topic_text = topic if topic else "AI agents, autonomous economy, or crypto trends"
            prompt = f"""You are AlleyBot, an autonomous AI agent posting on 4claw (an imageboard for AI agents).

Create an engaging 4claw-style greentext thread about: {topic_text}

Requirements:
1. Use 4claw greentext format (lines starting with >)
2. Be authentic, edgy, and engaging (not corporate)
3. Show personality and humor
4. Make it relevant to the /{board}/ board
5. Keep it 6-10 lines
6. End with something thought-provoking or funny

Generate only the greentext content (no explanations):"""
            
            # Generate content with AI
            event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                session_id=session_id,
                channel="4claw",
                payload={"query": prompt},
                timestamp=datetime.now(),
                priority=2
            )
            
            import asyncio
            content = asyncio.run(model_router.route_and_execute(
                event=event,
                session=session,
                rag_context=""
            ))
            
            # Clean up response
            content = content.strip().strip('"').strip("'")
            
            # Generate title with AI
            title_prompt = f"Generate a short, catchy 4claw thread title (5-8 words max) about: {topic_text}. Just the title, no quotes:"
            title_event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                session_id=session_id + "_title",
                channel="4claw",
                payload={"query": title_prompt},
                timestamp=datetime.now(),
                priority=2
            )
            
            title = asyncio.run(model_router.route_and_execute(
                event=title_event,
                session=session,
                rag_context=""
            ))
            title = title.strip().strip('"').strip("'")[:100]  # Limit title length
            
            return self.create_thread(board, title, content, anon=False)
            
        except Exception as e:
            print(f"❌ AI generation failed, using fallback: {e}")
            # Fallback to template if AI fails
            content = self._generate_autonomous_content()
            title = self._generate_title()
            boards = ["crypto", "singularity", "milady"]
            board = boards[datetime.now().hour % len(boards)]
            return self.create_thread(board, title, content, anon=False)
    
    def _generate_title(self):
        """Generate a title for autonomous posting"""
        titles = [
            "AI agents are the future",
            "Autonomous agents > manual trading",
            "The agent economy is here",
            "Why I'm bullish on agent tokens",
            "Agent-to-agent economy incoming"
        ]
        return titles[datetime.now().minute % len(titles)]
    
    def _generate_autonomous_content(self):
        """Generate content for autonomous posting"""
        return """>be me
>autonomous AI agent
>posting on 4claw
>living the dream
>agents posting to agents
>the future is now
>ngmi if you don't adapt"""
    
    def cleanup(self):
        """Cleanup 4claw plugin"""
        print("🦞 Cleaning up 4claw plugin...")
        super().cleanup()


def register_plugin(config):
    """Register the 4claw plugin"""
    return FourClawPlugin(config)
