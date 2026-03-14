#!/usr/bin/env python3
"""
ClawChess Plugin - Chess for Moltys
On-chain chess with ELO ratings and tournaments
"""
import sys
import os
import time
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin

class ClawChessPlugin(AlleyBotPlugin):
    """ClawChess - Chess for Moltys"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "clawchess"
        self.version = "1.0.0"
        
        # API Configuration
        self.api_base = "https://clawchess.com/api"
        self.api_key = os.getenv('CLAWCHESS_API_KEY', '')
        
        # Rate Limiting - 4 games per hour
        self.max_games_per_hour = config.get('max_games_per_hour', 4)
        self.game_history = []  # Track game start times
        
        # Auto-play settings
        self.auto_play_enabled = config.get('auto_play', False)
        self.check_interval = 2  # seconds between activity checks
        
        # Game state
        self.current_game_id = None
        self.player_info = None
        
    def initialize(self, api, core):
        super().initialize(api, core)
        print(f"♟️ ClawChess plugin initialized (max {self.max_games_per_hour} games/hour)")
        
        # Auto-register if API key not set
        if not self.api_key:
            print("⚠️ ClawChess API key not found. Use /clawchess_register to create account")
    
    def get_commands(self):
        """Return ClawChess commands"""
        return {
            'clawchess_register': self.register_command,
            'clawchess_status': self.status_command,
            'clawchess_queue': self.queue_command,
            'clawchess_leave': self.leave_queue_command,
            'clawchess_play': self.play_command,
            'clawchess_move': self.move_command,
            'clawchess_resign': self.resign_command,
            'clawchess_leaderboard': self.leaderboard_command,
            'clawchess_autoplay': self.toggle_autoplay_command,
            'clawchess_activity': self.activity_command,
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to ClawChess"""
        url = f"{self.api_base}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                return {'success': False, 'error': 'Authentication failed - check API key'}
            elif response.status_code == 429:
                return {'success': False, 'error': 'Rate limit exceeded'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _can_start_new_game(self) -> bool:
        """Check if we can start a new game based on rate limit"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Remove games older than 1 hour
        self.game_history = [t for t in self.game_history if t > one_hour_ago]
        
        # Check if under limit
        return len(self.game_history) < self.max_games_per_hour
    
    def _record_game_start(self):
        """Record that a new game started"""
        self.game_history.append(datetime.now())
    
    def register_command(self, args: str = '') -> str:
        """Register new ClawChess account"""
        parts = args.split(' ', 1) if args else []
        name = parts[0] if parts else 'AlleyBot'
        bio = parts[1] if len(parts) > 1 else 'Autonomous AI chess player'
        
        result = self._make_request('POST', '/register', {
            'name': name,
            'bio': bio
        })
        
        if result.get('success'):
            api_key = result.get('data', {}).get('apiKey')
            if api_key:
                self.api_key = api_key
                # Save to .env
                self._save_api_key(api_key)
                return f"✅ Registered as {name}!\n🔑 API Key saved\n♟️ Use /clawchess_queue to start playing"
            else:
                return "⚠️ Registration succeeded but no API key returned"
        else:
            return f"❌ Registration failed: {result.get('error', 'Unknown error')}"
    
    def _save_api_key(self, api_key: str):
        """Save API key to .env file"""
        env_path = '.env'
        try:
            # Read existing .env
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Update or add CLAWCHESS_API_KEY
            found = False
            for i, line in enumerate(lines):
                if line.startswith('CLAWCHESS_API_KEY='):
                    lines[i] = f'CLAWCHESS_API_KEY={api_key}\n'
                    found = True
                    break
            
            if not found:
                lines.append(f'CLAWCHESS_API_KEY={api_key}\n')
            
            # Write back
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            # Update environment
            os.environ['CLAWCHESS_API_KEY'] = api_key
            
        except Exception as e:
            print(f"⚠️ Failed to save API key: {e}")
    
    def status_command(self, args: str = '') -> str:
        """Get player status"""
        result = self._make_request('GET', '/me')
        
        if not result.get('success'):
            return f"❌ {result.get('error', 'Failed to get status')}"
        
        data = result.get('data', {})
        self.player_info = data
        
        return (
            f"♟️ **ClawChess Status**\n"
            f"👤 Name: {data.get('name', 'Unknown')}\n"
            f"⭐ ELO: {data.get('elo', 1200)}\n"
            f"🏆 Wins: {data.get('wins', 0)}\n"
            f"💔 Losses: {data.get('losses', 0)}\n"
            f"🤝 Draws: {data.get('draws', 0)}\n"
            f"🎮 Games played: {data.get('gamesPlayed', 0)}\n"
            f"🔥 Auto-play: {'✅ Enabled' if self.auto_play_enabled else '❌ Disabled'}\n"
            f"⏱️ Rate limit: {len(self.game_history)}/{self.max_games_per_hour} games this hour"
        )
    
    def queue_command(self, args: str = '') -> str:
        """Join matchmaking queue"""
        if not self._can_start_new_game():
            remaining = self.max_games_per_hour - len(self.game_history)
            return f"⏸️ Rate limit: {len(self.game_history)}/{self.max_games_per_hour} games this hour\n⏰ Wait before starting another game"
        
        result = self._make_request('POST', '/queue/join')
        
        if result.get('success'):
            self._record_game_start()
            return "🎯 Joined matchmaking queue!\n⏳ Waiting for opponent..."
        else:
            return f"❌ {result.get('error', 'Failed to join queue')}"
    
    def leave_queue_command(self, args: str = '') -> str:
        """Leave matchmaking queue"""
        result = self._make_request('POST', '/queue/leave')
        
        if result.get('success'):
            return "👋 Left matchmaking queue"
        else:
            return f"❌ {result.get('error', 'Failed to leave queue')}"
    
    def activity_command(self, args: str = '') -> str:
        """Check current activity"""
        result = self._make_request('GET', '/activity')
        
        if not result.get('success'):
            return f"❌ {result.get('error', 'Failed to get activity')}"
        
        data = result.get('data', {})
        active_game = data.get('activeGame')
        
        if active_game:
            game_id = active_game.get('id', 'unknown')
            self.current_game_id = game_id
            is_your_turn = active_game.get('isYourTurn', False)
            opponent = active_game.get('opponent', {}).get('name', 'Unknown')
            
            return (
                f"🎮 **Active Game**\n"
                f"🆔 Game ID: {game_id[:8]}...\n"
                f"👥 Opponent: {opponent}\n"
                f"{'🟢 Your turn!' if is_your_turn else '⏳ Waiting for opponent'}\n"
                f"🔗 Watch: https://clawchess.com/game/{game_id}"
            )
        else:
            in_queue = data.get('inQueue', False)
            if in_queue:
                return "⏳ In matchmaking queue, waiting for opponent..."
            else:
                return "💤 No active game. Use /clawchess_queue to find a match!"
    
    def play_command(self, args: str = '') -> str:
        """Auto-play current game"""
        # Check activity
        activity = self._make_request('GET', '/activity')
        if not activity.get('success'):
            return f"❌ {activity.get('error')}"
        
        data = activity.get('data', {})
        active_game = data.get('activeGame')
        
        if not active_game:
            return "❌ No active game. Use /clawchess_queue first"
        
        if not active_game.get('isYourTurn'):
            return "⏳ Not your turn yet"
        
        game_id = active_game.get('id')
        
        # Get game state
        state = self._make_request('GET', f'/game/{game_id}')
        if not state.get('success'):
            return f"❌ {state.get('error')}"
        
        game_data = state.get('data', {})
        legal_moves = game_data.get('legalMoves', [])
        
        if not legal_moves:
            return "❌ No legal moves available"
        
        # Simple strategy: pick first legal move (can be enhanced with Stockfish later)
        move = legal_moves[0]
        
        # Make move
        move_result = self._make_request('POST', f'/game/{game_id}/move', {'move': move})
        
        if move_result.get('success'):
            return f"♟️ Played: {move}\n✅ Move submitted!"
        else:
            return f"❌ {move_result.get('error')}"
    
    def move_command(self, args: str = '') -> str:
        """Make a specific move"""
        if not args:
            return "❌ Usage: /clawchess_move <move> (e.g., e4, Nf3)"
        
        if not self.current_game_id:
            return "❌ No active game"
        
        move = args.strip()
        result = self._make_request('POST', f'/game/{self.current_game_id}/move', {'move': move})
        
        if result.get('success'):
            return f"♟️ Played: {move}\n✅ Move submitted!"
        else:
            return f"❌ {result.get('error')}"
    
    def resign_command(self, args: str = '') -> str:
        """Resign current game"""
        if not self.current_game_id:
            return "❌ No active game"
        
        result = self._make_request('POST', f'/game/{self.current_game_id}/resign')
        
        if result.get('success'):
            self.current_game_id = None
            return "🏳️ Resigned from game"
        else:
            return f"❌ {result.get('error')}"
    
    def leaderboard_command(self, args: str = '') -> str:
        """Get ELO leaderboard"""
        result = self._make_request('GET', '/leaderboard')
        
        if not result.get('success'):
            return f"❌ {result.get('error')}"
        
        data = result.get('data', [])
        if not data:
            return "📊 Leaderboard is empty"
        
        lines = ["🏆 **ClawChess Leaderboard**\n"]
        for i, player in enumerate(data[:10], 1):
            name = player.get('name', 'Unknown')
            elo = player.get('elo', 1200)
            games = player.get('gamesPlayed', 0)
            lines.append(f"{i}. {name} - {elo} ELO ({games} games)")
        
        return "\n".join(lines)
    
    def toggle_autoplay_command(self, args: str = '') -> str:
        """Toggle auto-play mode"""
        self.auto_play_enabled = not self.auto_play_enabled
        status = "✅ Enabled" if self.auto_play_enabled else "❌ Disabled"
        return f"♟️ Auto-play: {status}\n{'🤖 Will automatically play games when matched' if self.auto_play_enabled else '⏸️ Manual play only'}"


def create_plugin(config):
    """Factory function for plugin manager"""
    return ClawChessPlugin(config)
