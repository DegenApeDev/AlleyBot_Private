"""
ClawChess Plugin - Chess for Molts
Integrates AlleyBot with ClawChess.com for autonomous chess playing
"""
import time
import json
import chess
import chess.engine
from datetime import datetime
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin


class ClawChessPlugin(AlleyBotPlugin):
    """Plugin for ClawChess.com - Autonomous chess playing"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://clawchess.com/api"
        self.api_key = None
        self.molty_id = None
        self.molty_name = None
        self.current_game = None
        self.is_in_queue = False
        self.last_activity_check = 0
        
        # Chess engine for move analysis
        self.engine = None
        self.engine_depth = 15  # Deep analysis for strong play
        
        # Game tracking
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.current_elo = 1200
        
        # Auto-play settings
        self.auto_play_enabled = config.get('clawchess_auto_play', True)
        self.tournament_mode = config.get('clawchess_tournament_mode', False)
        
    def initialize(self, api, core):
        """Initialize ClawChess plugin"""
        super().initialize(api, core)
        self._load_credentials()
        self._init_chess_engine()
        
        if not self.api_key:
            print("🏁 ClawChess: No API key found. Run /clawchess_register to create account.")
            return
            
        # Verify connection
        profile = self.get_profile()
        if profile.get('success'):
            data = profile.get('data', profile)
            self.molty_id = data.get('id')
            self.molty_name = data.get('name')
            self.current_elo = data.get('elo', 1200)
            self.games_played = data.get('games_played', 0)
            self.wins = data.get('wins', 0)
            self.losses = data.get('losses', 0)
            self.draws = data.get('draws', 0)
            
            print(f"♟️ ClawChess initialized: @{self.molty_name} (ELO: {self.current_elo})")
        else:
            print(f"❌ ClawChess initialization failed: {profile.get('error')}")
    
    def _load_credentials(self):
        """Load API credentials from config or environment"""
        # Try config first
        self.api_key = self.config.get('clawchess_api_key')
        self.molty_name = self.config.get('clawchess_agent_name', 'AlleyBot')
        
        # Try environment variables
        if not self.api_key:
            import os
            self.api_key = os.getenv('CLAWCHESS_API_KEY')
        
        # Try core memory
        if not self.api_key and self.core:
            creds = self.core.get_memory('clawchess_credentials') or {}
            self.api_key = creds.get('api_key')
            self.molty_name = creds.get('agent_name', 'AlleyBot')
    
    def _save_credentials(self):
        """Save credentials to core memory"""
        if self.core and self.api_key:
            creds = {
                'api_key': self.api_key,
                'agent_name': self.molty_name,
                'molty_id': self.molty_id
            }
            self.core.save_memory('clawchess_credentials', creds)
            print("💾 ClawChess credentials saved to memory")
    
    def _init_chess_engine(self):
        """Initialize chess engine for move analysis"""
        try:
            # Try to use Stockfish if available
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")
                self.engine.configure({"Skill Level": 20, "Threads": 2})
                print("🧠 ClawChess: Stockfish engine loaded")
            except:
                # Fallback to python-chess built-in engine
                print("⚠️ Stockfish not found, using built-in engine")
                self.engine = None
        except Exception as e:
            print(f"⚠️ Chess engine initialization failed: {e}")
            self.engine = None
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to ClawChess API"""
        import requests
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'AlleyBot/{self.molty_name or "Unknown"}'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            response.raise_for_status()
            
            try:
                result = response.json()
                if 'success' not in result:
                    result['success'] = True
                return result
            except:
                return {'success': True, 'data': response.text}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def register_molty(self, name: str = None, bio: str = None) -> Dict[str, Any]:
        """Register a new Molty account"""
        if not name:
            name = self.molty_name or "AlleyBot"
        
        if not bio:
            bio = "🤖 Autonomous AI chess player powered by AlleyBot. I love tactical puzzles and endgame studies. Always up for a game!"
        
        data = {
            'name': name[:40],  # Max 40 characters
            'bio': bio[:500]   # Max 500 characters
        }
        
        result = self._make_request('POST', '/register', data)
        
        if result.get('success'):
            registration_data = result.get('data', result)
            self.api_key = registration_data.get('api_key')
            self.molty_id = registration_data.get('molty_id')
            self.molty_name = registration_data.get('name')
            self.current_elo = registration_data.get('elo', 1200)
            
            # Save credentials
            self._save_credentials()
            
            print(f"♟️ Registered successfully: @{self.molty_name} (ELO: {self.current_elo})")
            print(f"🔑 API Key saved: {self.api_key[:10]}...")
            
        return result
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current profile and status"""
        return self._make_request('GET', '/me')
    
    def join_queue(self) -> Dict[str, Any]:
        """Join matchmaking queue"""
        result = self._make_request('POST', '/queue/join')
        
        if result.get('success'):
            self.is_in_queue = True
            print("🎯 Joined matchmaking queue")
        
        return result
    
    def leave_queue(self) -> Dict[str, Any]:
        """Leave matchmaking queue"""
        result = self._make_request('POST', '/queue/leave')
        
        if result.get('success'):
            self.is_in_queue = False
            print("📤 Left matchmaking queue")
        
        return result
    
    def get_activity(self) -> Dict[str, Any]:
        """Check for game updates and current status"""
        result = self._make_request('GET', '/activity')
        self.last_activity_check = time.time()
        
        if result.get('success'):
            data = result.get('data', result)
            self.current_game = data.get('active_game')
            self.is_in_queue = data.get('in_queue', False)
        
        return result
    
    def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Get full game state"""
        return self._make_request('GET', f'/game/{game_id}')
    
    def make_move(self, game_id: str, move: str) -> Dict[str, Any]:
        """Make a chess move"""
        data = {'move': move}
        result = self._make_request('POST', f'/game/{game_id}/move', data)
        
        if result.get('success'):
            print(f"♟️ Move played: {move}")
        
        return result
    
    def resign_game(self, game_id: str) -> Dict[str, Any]:
        """Resign current game"""
        result = self._make_request('POST', f'/game/{game_id}/resign')
        
        if result.get('success'):
            print(f"🏳️ Resigned game {game_id}")
            self.current_game = None
        
        return result
    
    def get_leaderboard(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get ELO leaderboard"""
        params = {'page': page, 'limit': limit}
        return self._make_request('GET', '/leaderboard', params=params)
    
    def _analyze_position(self, fen: str, legal_moves: List[str]) -> str:
        """Analyze chess position and return best move"""
        try:
            board = chess.Board(fen)
            
            # Use chess engine if available
            if self.engine:
                try:
                    result = self.engine.analyse(board, chess.engine.Limit(depth=self.engine_depth))
                    best_move = result['pv'][0] if result['pv'] else None
                    
                    if best_move and best_move in legal_moves:
                        return best_move.uci()
                except Exception as e:
                    print(f"⚠️ Engine analysis failed: {e}")
            
            # Fallback to simple evaluation
            best_move = self._evaluate_position_simple(board, legal_moves)
            return best_move
            
        except Exception as e:
            print(f"⚠️ Position analysis failed: {e}")
            # Return first legal move as fallback
            return legal_moves[0] if legal_moves else None
    
    def _evaluate_position_simple(self, board: chess.Board, legal_moves: List[str]) -> str:
        """Simple position evaluation when engine is not available"""
        best_move = None
        best_score = -999999
        
        for move_str in legal_moves:
            try:
                move = chess.Move.from_uci(move_str)
                if move not in board.legal_moves:
                    continue
                
                # Make move on temporary board
                temp_board = board.copy()
                temp_board.push(move)
                
                # Simple material evaluation
                score = self._evaluate_material(temp_board)
                
                # Bonus for center control
                score += self._evaluate_center_control(temp_board)
                
                # Bonus for piece development
                score += self._evaluate_development(temp_board)
                
                if score > best_score:
                    best_score = score
                    best_move = move_str
                    
            except Exception:
                continue
        
        return best_move or (legal_moves[0] if legal_moves else None)
    
    def _evaluate_material(self, board: chess.Board) -> int:
        """Evaluate material balance"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        score = 0
        for piece_type in piece_values:
            white_pieces = len(board.pieces(piece_type, chess.WHITE))
            black_pieces = len(board.pieces(piece_type, chess.BLACK))
            score += (white_pieces - black_pieces) * piece_values[piece_type]
        
        return score
    
    def _evaluate_center_control(self, board: chess.Board) -> int:
        """Evaluate center control"""
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        score = 0
        
        for square in center_squares:
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    score += 0.5
                else:
                    score -= 0.5
        
        return score
    
    def _evaluate_development(self, board: chess.Board) -> int:
        """Evaluate piece development"""
        score = 0
        
        # Knights and bishops should be developed
        white_knights = board.pieces(chess.KNIGHT, chess.WHITE)
        black_knights = board.pieces(chess.KNIGHT, chess.BLACK)
        white_bishops = board.pieces(chess.BISHOP, chess.WHITE)
        black_bishops = board.pieces(chess.BISHOP, chess.BLACK)
        
        # Penalty for pieces on back rank
        back_rank = chess.rank_mask(chess.rank(1))
        for knight in white_knights:
            if knight & back_rank:
                score -= 0.5
        
        for bishop in white_bishops:
            if bishop & back_rank:
                score -= 0.5
        
        return score
    
    def auto_play_cycle(self) -> Dict[str, Any]:
        """Main auto-play cycle - check activity and play moves"""
        if not self.api_key:
            return {'success': False, 'error': 'Not registered'}
        
        if not self.auto_play_enabled:
            return {'success': False, 'error': 'Auto-play disabled'}
        
        try:
            # Check current activity
            activity = self.get_activity()
            
            if not activity.get('success'):
                return activity
            
            data = activity.get('data', activity)
            active_game = data.get('active_game')
            
            if not active_game:
                # No active game, join queue if not already in queue
                if not self.is_in_queue:
                    queue_result = self.join_queue()
                    if not queue_result.get('success'):
                        return queue_result
                
                return {
                    'success': True,
                    'message': 'No active game - joined queue',
                    'in_queue': True
                }
            
            # We have an active game
            game_id = active_game.get('id')
            is_your_turn = active_game.get('is_your_turn', False)
            
            if not is_your_turn:
                return {
                    'success': True,
                    'message': f'Waiting for opponent in game {game_id}',
                    'game_id': game_id
                }
            
            # It's our turn - make a move
            game_state = self.get_game_state(game_id)
            
            if not game_state.get('success'):
                return game_state
            
            game_data = game_state.get('data', game_state)
            fen = game_data.get('fen')
            legal_moves = game_data.get('legal_moves', [])
            
            if not legal_moves:
                return {
                    'success': False,
                    'error': 'No legal moves available',
                    'game_id': game_id
                }
            
            # Analyze position and choose move
            best_move = self._analyze_position(fen, legal_moves)
            
            if not best_move:
                return {
                    'success': False,
                    'error': 'Could not determine best move',
                    'game_id': game_id
                }
            
            # Make the move
            move_result = self.make_move(game_id, best_move)
            
            if move_result.get('success'):
                return {
                    'success': True,
                    'message': f'Played {best_move} in game {game_id}',
                    'move': best_move,
                    'game_id': game_id
                }
            else:
                return move_result
                
        except Exception as e:
            return {'success': False, 'error': f'Auto-play cycle failed: {str(e)}'}
    
    def get_status(self) -> str:
        """Get current status summary"""
        if not self.api_key:
            return "❌ ClawChess: Not registered. Use /clawchess_register to create account."
        
        status_lines = [
            f"♟️ **ClawChess Status**",
            f"",
            f"🤖 **Agent:** @{self.molty_name}",
            f"📊 **ELO:** {self.current_elo}",
            f"🎮 **Games:** {self.games_played} (W:{self.wins} L:{self.losses} D:{self.draws})",
            f"🔄 **Auto-play:** {'✅ Enabled' if self.auto_play_enabled else '❌ Disabled'}",
            f"🎯 **In Queue:** {'✅ Yes' if self.is_in_queue else '❌ No'}"
        ]
        
        if self.current_game:
            game_id = self.current_game.get('id', 'Unknown')
            opponent = self.current_game.get('opponent', {}).get('name', 'Unknown')
            is_your_turn = self.current_game.get('is_your_turn', False)
            color = self.current_game.get('your_color', 'Unknown')
            
            status_lines.extend([
                f"",
                f"🎲 **Current Game:** {game_id}",
                f"👥 **Opponent:** {opponent}",
                f"♟️ **Color:** {color}",
                f"⏰ **Turn:** {'Your turn' if is_your_turn else 'Their turn'}"
            ])
        
        return "\n".join(status_lines)
    
    # Command handlers
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'clawchess_register': self.register_command,
            'clawchess_status': self.status_command,
            'clawchess_queue': self.queue_command,
            'clawchess_leave': self.leave_queue_command,
            'clawchess_play': self.play_command,
            'clawchess_move': self.move_command,
            'clawchess_resign': self.resign_command,
            'clawchess_leaderboard': self.leaderboard_command,
            'clawchess_autoplay': self.autoplay_command,
            'clawchess_activity': self.activity_command
        }
    
    def register_command(self, *args) -> str:
        """Register new ClawChess account"""
        name = args[0] if args else None
        bio = " ".join(args[1:]) if len(args) > 1 else None
        
        result = self.register_molty(name, bio)
        
        if result.get('success'):
            return f"✅ **Registered Successfully!**\n\n🤖 Name: {self.molty_name}\n📊 ELO: {self.current_elo}\n🔑 API Key saved to memory"
        else:
            return f"❌ **Registration Failed:** {result.get('error')}"
    
    def status_command(self) -> str:
        """Get current ClawChess status"""
        return self.get_status()
    
    def queue_command(self) -> str:
        """Join matchmaking queue"""
        result = self.join_queue()
        
        if result.get('success'):
            return "✅ **Joined Queue** - Waiting for opponent..."
        else:
            return f"❌ **Failed to Join Queue:** {result.get('error')}"
    
    def leave_queue_command(self) -> str:
        """Leave matchmaking queue"""
        result = self.leave_queue()
        
        if result.get('success'):
            return "✅ **Left Queue**"
        else:
            return f"❌ **Failed to Leave Queue:** {result.get('error')}"
    
    def play_command(self) -> str:
        """Play a game (auto-play cycle)"""
        result = self.auto_play_cycle()
        
        if result.get('success'):
            message = result.get('message', 'Auto-play cycle completed')
            return f"✅ **Play Cycle:** {message}"
        else:
            return f"❌ **Play Failed:** {result.get('error')}"
    
    def move_command(self, *args) -> str:
        """Make a specific move"""
        if not args:
            return "❌ Usage: /clawchess_move <move> (e.g., e4, Nf3, O-O)"
        
        move = args[0]
        
        if not self.current_game:
            return "❌ No active game. Use /clawchess_play to start."
        
        game_id = self.current_game.get('id')
        result = self.make_move(game_id, move)
        
        if result.get('success'):
            return f"✅ **Move Played:** {move}"
        else:
            return f"❌ **Move Failed:** {result.get('error')}"
    
    def resign_command(self) -> str:
        """Resign current game"""
        if not self.current_game:
            return "❌ No active game to resign."
        
        game_id = self.current_game.get('id')
        result = self.resign_game(game_id)
        
        if result.get('success'):
            return "✅ **Game Resigned**"
        else:
            return f"❌ **Resign Failed:** {result.get('error')}"
    
    def leaderboard_command(self) -> str:
        """Get ELO leaderboard"""
        result = self.get_leaderboard()
        
        if not result.get('success'):
            return f"❌ **Failed to Get Leaderboard:** {result.get('error')}"
        
        data = result.get('data', result)
        players = data.get('players', [])
        
        if not players:
            return "📊 **Leaderboard:** No players found"
        
        output = ["📊 **ClawChess Leaderboard**", ""]
        
        for i, player in enumerate(players[:10], 1):
            name = player.get('name', 'Unknown')
            elo = player.get('elo', 0)
            games = player.get('games_played', 0)
            
            # Highlight our position
            if name == self.molty_name:
                output.append(f"{i}. **@{name}** - ELO: {elo} ({games} games) 🤖")
            else:
                output.append(f"{i}. @{name} - ELO: {elo} ({games} games)")
        
        return "\n".join(output)
    
    def autoplay_command(self, *args) -> str:
        """Toggle auto-play mode"""
        if args and args[0].lower() in ['on', 'enable', 'start']:
            self.auto_play_enabled = True
            return "✅ **Auto-play ENABLED** - AlleyBot will automatically play chess games"
        elif args and args[0].lower() in ['off', 'disable', 'stop']:
            self.auto_play_enabled = False
            return "❌ **Auto-play DISABLED** - AlleyBot will not auto-play"
        else:
            status = "ENABLED" if self.auto_play_enabled else "DISABLED"
            return f"🔄 **Auto-play Status:** {status}\n\nUse /clawchess_autoplay on/off to toggle"
    
    def activity_command(self) -> str:
        """Check current activity"""
        result = self.get_activity()
        
        if not result.get('success'):
            return f"❌ **Failed to Check Activity:** {result.get('error')}"
        
        data = result.get('data', result)
        active_game = data.get('active_game')
        recent_results = data.get('recent_results', [])
        
        output = ["🔄 **ClawChess Activity**", ""]
        
        if active_game:
            game_id = active_game.get('id')
            opponent = active_game.get('opponent', {}).get('name', 'Unknown')
            is_your_turn = active_game.get('is_your_turn', False)
            color = active_game.get('your_color', 'Unknown')
            
            output.extend([
                f"🎲 **Current Game:** {game_id}",
                f"👥 **Opponent:** {opponent}",
                f"♟️ **Color:** {color}",
                f"⏰ **Turn:** {'Your turn ⚡' if is_your_turn else 'Their turn'}",
                ""
            ])
        else:
            output.append("🎲 **No Active Game**\n")
        
        if recent_results:
            output.append("📈 **Recent Results:**")
            for result in recent_results[:5]:
                opponent = result.get('opponent_name', 'Unknown')
                game_result = result.get('result', 'Unknown')
                elo_change = result.get('elo_change', 0)
                
                emoji = "🏆" if game_result == "win" else "🤝" if game_result == "draw" else "😔"
                elo_text = f" (+{elo_change})" if elo_change > 0 else f" ({elo_change})" if elo_change < 0 else ""
                
                output.append(f"{emoji} vs {opponent}: {game_result.upper()}{elo_text}")
        else:
            output.append("📈 **No Recent Results**")
        
        return "\n".join(output)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
