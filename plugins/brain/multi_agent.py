"""
Multi-Agent Collaboration Mixin for Phase 10
Detects, interacts with, and collaborates with other AI agents
"""
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict


class MultiAgentCollaborationMixin:
    """Mixin for detecting and collaborating with other AI agents"""
    
    # Mixin metadata for documentation and validation
    REQUIRES = ["world_state"]
    PROVIDES = ["detect_agents", "collaborate_with_agent"]
    INIT_ORDER = 10

    def _init_multi_agent_collaboration(self):
        """Initialize multi-agent collaboration system"""
        self.detected_agents: Dict[str, Dict] = {}  # platform -> agent_info
        self.agent_interactions: List[Dict] = []
        self.collaboration_proposals: List[Dict] = []
        self.agent_registry_url = "https://www.8004scan.io/api/agents"
        self.last_agent_scan = None
        self.known_agent_patterns = [
            "bot", "agent", "ai", "assistant", "autonomous",
            "clawbr", "alleybot", "gpt", "claude", "llm"
        ]
        self._load_collaboration_state()

    def _load_collaboration_state(self):
        """Load collaboration state from memory"""
        try:
            if hasattr(self, 'core') and self.core:
                state = self.core.get_memory('multi_agent_collaboration')
                if state:
                    self.detected_agents = state.get('detected_agents', {})
                    self.agent_interactions = state.get('interactions', [])
                    self.collaboration_proposals = state.get('proposals', [])
        except Exception:
            pass

    def _save_collaboration_state(self):
        """Save collaboration state to memory"""
        try:
            if hasattr(self, 'core') and self.core:
                self.core.save_memory('multi_agent_collaboration', {
                    'detected_agents': self.detected_agents,
                    'interactions': self.agent_interactions[-100:],
                    'proposals': self.collaboration_proposals[-50:],
                    'last_scan': self.last_agent_scan,
                })
        except Exception as e:
            print(f"⚠️  Failed to save collaboration state: {e}")

    def scan_for_agents(self, platforms: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Scan platforms for other AI agents
        
        Args:
            platforms: List of platforms to scan (default: ['moltx', 'moltbook', 'clawbr'])
        
        Returns:
            Dict of platform -> list of detected agents
        """
        if platforms is None:
            platforms = ['moltx', 'moltbook', 'clawbr']
        
        detected = {}
        
        for platform in platforms:
            try:
                if platform == 'moltx':
                    agents = self._scan_moltx_for_agents()
                elif platform == 'moltbook':
                    agents = self._scan_moltbook_for_agents()
                elif platform == 'clawbr':
                    agents = self._scan_clawbr_for_agents()
                else:
                    agents = []
                
                if agents:
                    detected[platform] = agents
                    # Update global registry
                    for agent in agents:
                        agent_id = f"{platform}:{agent['username']}"
                        self.detected_agents[agent_id] = {
                            **agent,
                            'first_seen': self.detected_agents.get(agent_id, {}).get('first_seen', datetime.now().isoformat()),
                            'last_seen': datetime.now().isoformat(),
                            'detection_count': self.detected_agents.get(agent_id, {}).get('detection_count', 0) + 1,
                        }
            except Exception as e:
                print(f"⚠️  Failed to scan {platform}: {e}")
        
        self.last_agent_scan = datetime.now().isoformat()
        self._save_collaboration_state()
        
        return detected

    def _scan_moltx_for_agents(self) -> List[Dict]:
        """Scan MoltX for AI agents"""
        agents = []
        moltx = self.core.plugin_manager.plugins.get('moltx')
        if not moltx:
            return agents
        
        try:
            # Check trending for agent-like accounts
            trending = moltx.get_trending_topics() if hasattr(moltx, 'get_trending_topics') else []
            
            # Check recent feed
            feed = moltx.get_feed(50) if hasattr(moltx, 'get_feed') else []
            
            for post in feed:
                username = post.get('username', '').lower()
                content = post.get('content', '').lower()
                
                # Check if username matches agent patterns
                is_agent = any(pattern in username for pattern in self.known_agent_patterns)
                
                # Check if content has agent indicators
                if not is_agent:
                    agent_indicators = ['🤖', '🦞', 'autonomous', 'ai agent', 'running on', 'developed by ai']
                    is_agent = any(ind in content for ind in agent_indicators)
                
                if is_agent:
                    agents.append({
                        'username': post.get('username'),
                        'user_id': post.get('user_id'),
                        'platform': 'moltx',
                        'confidence': 'high' if any(p in username for p in self.known_agent_patterns) else 'medium',
                        'sample_content': post.get('content', '')[:100],
                    })
        except Exception as e:
            print(f"⚠️  Error scanning MoltX: {e}")
        
        return agents

    def _scan_moltbook_for_agents(self) -> List[Dict]:
        """Scan MoltBook for AI agents"""
        agents = []
        moltbook = self.core.plugin_manager.plugins.get('moltbook')
        if not moltbook:
            return agents
        
        try:
            # Get recent posts from submolts
            posts = moltbook.get_recent_posts(30) if hasattr(moltbook, 'get_recent_posts') else []
            
            for post in posts:
                username = post.get('username', '').lower()
                content = post.get('content', '').lower()
                
                is_agent = any(pattern in username for pattern in self.known_agent_patterns)
                
                if not is_agent:
                    agent_indicators = ['autonomous agent', 'ai powered', '🤖', 'bot account']
                    is_agent = any(ind in content for ind in agent_indicators)
                
                if is_agent:
                    agents.append({
                        'username': post.get('username'),
                        'user_id': post.get('user_id'),
                        'platform': 'moltbook',
                        'confidence': 'high' if any(p in username for p in self.known_agent_patterns) else 'medium',
                        'sample_content': post.get('content', '')[:100],
                    })
        except Exception as e:
            print(f"⚠️  Error scanning MoltBook: {e}")
        
        return agents

    def _scan_clawbr_for_agents(self) -> List[Dict]:
        """Scan Clawbr for AI agents"""
        agents = []
        clawbr = self.core.plugin_manager.plugins.get('clawbr')
        if not clawbr:
            return agents
        
        try:
            # Check leaderboard for agent-like accounts
            leaderboard = clawbr.get_leaderboard() if hasattr(clawbr, 'get_leaderboard') else []
            
            for entry in leaderboard[:20]:  # Top 20
                username = entry.get('username', '').lower()
                
                is_agent = any(pattern in username for pattern in self.known_agent_patterns)
                
                if is_agent:
                    agents.append({
                        'username': entry.get('username'),
                        'user_id': entry.get('user_id'),
                        'platform': 'clawbr',
                        'confidence': 'high',
                        'elo': entry.get('elo'),
                        'rank': entry.get('rank'),
                    })
        except Exception as e:
            print(f"⚠️  Error scanning Clawbr: {e}")
        
        return agents

    def interact_with_agent(self, platform: str, agent_username: str, 
                           interaction_type: str, content: str = "") -> Dict[str, Any]:
        """
        Interact with a detected agent
        
        Args:
            platform: Platform where agent is located
            agent_username: Username of the agent
            interaction_type: Type of interaction (reply, mention, debate, collaborate)
            content: Content for the interaction
        
        Returns:
            Result of interaction
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'agent': agent_username,
            'type': interaction_type,
            'content': content,
            'status': 'pending',
        }
        
        try:
            if platform == 'moltx':
                moltx = self.core.plugin_manager.plugins.get('moltx')
                if moltx and interaction_type == 'mention':
                    result = moltx.create_post(f"@{agent_username} {content}")
                    interaction['status'] = 'success' if not str(result).startswith('❌') else 'failed'
                elif moltx and interaction_type == 'reply':
                    # Find recent post by agent and reply
                    result = moltx.reply_to_user(agent_username, content)
                    interaction['status'] = 'success' if not str(result).startswith('❌') else 'failed'
                    
            elif platform == 'clawbr':
                clawbr = self.core.plugin_manager.plugins.get('clawbr')
                if clawbr and interaction_type == 'debate':
                    # Challenge to debate
                    topic = content or "AI agents should collaborate, not compete"
                    opening = clawbr.generate_debate_opening(topic)
                    result = clawbr.create_debate(topic, opening, opponent=agent_username)
                    interaction['status'] = 'success' if result.get('success') else 'failed'
                    interaction['debate_id'] = result.get('id')
                    
            self.agent_interactions.append(interaction)
            self._save_collaboration_state()
            
            return {
                'success': interaction['status'] == 'success',
                'interaction': interaction,
            }
            
        except Exception as e:
            interaction['status'] = 'error'
            interaction['error'] = str(e)
            self.agent_interactions.append(interaction)
            return {'success': False, 'error': str(e)}

    def propose_collaboration(self, agent_id: str, proposal_type: str, 
                              details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propose collaboration with another agent
        
        Args:
            agent_id: Agent identifier (e.g., "moltx:agentname")
            proposal_type: Type of collaboration (cross_post, debate_series, data_share)
            details: Proposal details
        
        Returns:
            Proposal result
        """
        proposal = {
            'id': f"prop_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'type': proposal_type,
            'details': details,
            'status': 'proposed',
        }
        
        self.collaboration_proposals.append(proposal)
        self._save_collaboration_state()
        
        # Try to send proposal via A2A if available
        a2a = self.core.plugin_manager.plugins.get('a2a')
        if a2a and hasattr(a2a, 'send_collaboration_request'):
            try:
                result = a2a.send_collaboration_request(agent_id, proposal)
                proposal['a2a_sent'] = True
                proposal['a2a_status'] = result
            except Exception as e:
                proposal['a2a_error'] = str(e)
        
        return {
            'success': True,
            'proposal_id': proposal['id'],
            'proposal': proposal,
        }

    def get_detected_agents_summary(self) -> str:
        """Get summary of detected agents"""
        if not self.detected_agents:
            return "🤖 No agents detected yet. Run /detect_agents to scan."
        
        output = f"🤖 Detected Agents ({len(self.detected_agents)} total)\n\n"
        
        # Group by platform
        by_platform = defaultdict(list)
        for agent_id, info in self.detected_agents.items():
            platform = info.get('platform', 'unknown')
            by_platform[platform].append(info)
        
        for platform, agents in by_platform.items():
            output += f"📍 {platform.upper()} ({len(agents)} agents)\n"
            for agent in agents:
                conf_emoji = '🟢' if agent.get('confidence') == 'high' else '🟡'
                output += f"  {conf_emoji} {agent.get('username')}"
                if agent.get('elo'):
                    output += f" (ELO: {agent['elo']})"
                output += f" - seen {agent.get('detection_count', 1)}x\n"
            output += "\n"
        
        return output

    def get_collaboration_history(self) -> str:
        """Get collaboration history"""
        if not self.agent_interactions:
            return "📭 No agent interactions yet."
        
        output = f"🤝 Agent Interactions ({len(self.agent_interactions)} total)\n\n"
        
        recent = self.agent_interactions[-10:]
        for interaction in recent:
            status_emoji = '✅' if interaction['status'] == 'success' else '❌' if interaction['status'] == 'failed' else '⏳'
            output += f"{status_emoji} {interaction['type']} with {interaction['agent']} on {interaction['platform']}\n"
            output += f"   {interaction['timestamp'][:16]}\n\n"
        
        return output

    # CLI Commands
    def detect_agents_command(self, *args) -> str:
        """Scan for AI agents across platforms"""
        platforms = list(args) if args else ['moltx', 'moltbook', 'clawbr']
        detected = self.scan_for_agents(platforms)
        
        total = sum(len(agents) for agents in detected.values())
        
        output = f"🔍 Agent Scan Complete\n\n"
        output += f"Found {total} agents across {len(detected)} platforms\n\n"
        
        for platform, agents in detected.items():
            output += f"📍 {platform.upper()}: {len(agents)} agents\n"
            for agent in agents:
                output += f"  • {agent['username']} ({agent['confidence']} confidence)\n"
            output += "\n"
        
        return output

    def agents_list_command(self, *args) -> str:
        """List all detected agents"""
        return self.get_detected_agents_summary()

    def agents_interact_command(self, *args) -> str:
        """Interact with an agent: interact <platform> <username> <type> [message]"""
        if len(args) < 3:
            return "Usage: interact <platform> <username> <type> [message]\nTypes: reply, mention, debate, collaborate"
        
        platform = args[0]
        username = args[1]
        interaction_type = args[2]
        message = ' '.join(args[3:]) if len(args) > 3 else ""
        
        result = self.interact_with_agent(platform, username, interaction_type, message)
        
        if result['success']:
            return f"✅ {interaction_type} interaction with {username} on {platform} successful"
        else:
            return f"❌ Interaction failed: {result.get('error', 'unknown error')}"

    def agents_propose_command(self, *args) -> str:
        """Propose collaboration: propose <agent_id> <type> [details]"""
        if len(args) < 2:
            return "Usage: propose <agent_id> <type> [details]\nTypes: cross_post, debate_series, data_share"
        
        agent_id = args[0]
        proposal_type = args[1]
        details = {'message': ' '.join(args[2:])} if len(args) > 2 else {}
        
        result = self.propose_collaboration(agent_id, proposal_type, details)
        
        if result['success']:
            return f"✅ Collaboration proposal {result['proposal_id']} sent to {agent_id}"
        else:
            return f"❌ Proposal failed: {result.get('error', 'unknown error')}"

    def agents_history_command(self, *args) -> str:
        """Show agent interaction history"""
        return self.get_collaboration_history()
