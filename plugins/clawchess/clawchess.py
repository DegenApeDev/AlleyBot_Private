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
        self.engine_depth = 18  # Strong depth for competitive play (was 8)
        
        # Game tracking
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.current_elo = 1200
        
        # Auto-play settings
        self.auto_play_enabled = config.get('auto_play', True)
        self.tournament_mode = config.get('tournament_mode', False)
        self.max_games_per_hour = config.get('max_games_per_hour', 4)
        
        # Position history for repetition detection (stores FEN strings seen this game)
        self.position_history: List[str] = []
        # Track the last game ID so we can reset history when a new game starts
        self._last_game_id: Optional[str] = None
        # Opponent awareness: last move the opponent played (SAN string)
        self._opponent_last_move: Optional[str] = None
        # Full PGN of current game for pattern awareness
        self._current_pgn: str = ""
        # Last known skill version (for daily update check)
        self._skill_version: Optional[str] = None
        self._last_skill_check: float = 0
        # Async runner (replaces blocking poll thread)
        self._runner: Optional[Any] = None
        # Legacy compat attrs
        self._poll_thread = None
        self._poll_stop = False
        
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
        
        # Start async runner
        self._start_async_runner()
    
    def _start_async_runner(self):
        """Start the async ClawChessRunner in a background daemon thread."""
        if not self.api_key:
            return
        if not self.auto_play_enabled:
            return
        try:
            from plugins.clawchess.clawchess_runner import ClawChessRunner

            def _on_move(game_id, move_san, time_s):
                print(f"♟️ Auto-move: {move_san} ({time_s}s left) in game {game_id}")

            def _on_game_over(game_id, result):
                print(f"♟️ Game over: {result.upper()} (game {game_id})")
                # Update stats from profile after game ends
                try:
                    profile = self.get_profile()
                    if profile.get('success'):
                        d = profile.get('data', profile)
                        self.current_elo = d.get('elo', self.current_elo)
                        self.games_played = d.get('games_played', self.games_played)
                        self.wins = d.get('wins', self.wins)
                        self.losses = d.get('losses', self.losses)
                        self.draws = d.get('draws', self.draws)
                except Exception:
                    pass

            self._runner = ClawChessRunner(
                api_key=self.api_key,
                agent_name=self.molty_name or 'AlleyBot',
                engine_depth=20,  # Strong competitive depth
                on_move_played=_on_move,
                on_game_over=_on_game_over,
            )
            self._runner.start_background()
            print("♟️ ClawChess async runner started")
        except ImportError as e:
            print(f"⚠️ ClawChessRunner not available ({e}) — falling back to sync poll thread")
            self._start_poll_thread_fallback()
        except Exception as e:
            print(f"⚠️ ClawChess runner start failed: {e}")

    def _start_poll_thread_fallback(self):
        """Sync fallback poll thread used only if aiohttp is unavailable."""
        import threading
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._poll_stop = False

        def _loop():
            while not self._poll_stop:
                try:
                    if not self.auto_play_enabled or not self.api_key:
                        time.sleep(60)
                        continue
                    activity = self.get_activity()
                    if not activity.get('success'):
                        time.sleep(15)
                        continue
                    data = activity.get('data', activity)
                    active_game = data.get('active_game')
                    if not active_game:
                        if not self.is_in_queue:
                            self.join_queue()
                        time.sleep(15)
                        continue
                    if active_game.get('is_your_turn', False):
                        result = self._execute_move_now()
                        if result.get('move'):
                            print(f"♟️ Auto-move: {result.get('message')}")
                        time.sleep(2)
                    else:
                        time.sleep(3)
                except Exception as exc:
                    print(f"⚠️ Poll fallback error: {exc}")
                    time.sleep(10)

        self._poll_thread = threading.Thread(target=_loop, name='clawchess-poll', daemon=True)
        self._poll_thread.start()
        print("♟️ ClawChess sync fallback poll thread started")

    def run_periodic_check(self):
        """Legacy hook — real polling handled by async runner."""
        pass
    
    def get_status_summary(self):
        """Get brief status for periodic checks"""
        if not self.api_key:
            return None
        
        try:
            profile = self.get_profile()
            if profile.get('success'):
                data = profile.get('data', profile)
                return {
                    'name': data.get('name'),
                    'elo': data.get('elo', 1200),
                    'games': data.get('games_played', 0),
                    'auto_play': self.auto_play_enabled
                }
        except:
            pass
        return None
    
    def get_tasks(self):
        """Define scheduled tasks for ClawChess.
        
        Move checking is handled by the reactive _poll_loop thread, not the
        cron scheduler (which only has minute-level granularity).
        Only the slow status-update task is registered here.
        """
        tasks = {}
        if self.api_key:
            tasks['clawchess_status_update'] = {
                'schedule': '*/10 * * * *',
                'function': self._status_update,
                'description': 'Update chess statistics and status every 10 minutes'
            }
        return tasks
    
    def _status_update(self):
        """Periodic status update"""
        try:
            if self.api_key:
                profile = self.get_profile()
                if profile.get('success'):
                    data = profile.get('data', profile)
                    self.current_elo = data.get('elo', self.current_elo)
                    self.games_played = data.get('games_played', self.games_played)
                    self.wins = data.get('wins', self.wins)
                    self.losses = data.get('losses', self.losses)
                    self.draws = data.get('draws', self.draws)
                    
                    print(f"♟️ Status Update: ELO {self.current_elo}, Games: {self.games_played}")
        except Exception as e:
            print(f"⚠️ ClawChess status update failed: {e}")
    
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
    
    def get_challenges(self) -> Dict[str, Any]:
        """Fetch pending incoming challenges."""
        return self._make_request('GET', '/v1/challenges')
    
    def accept_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Accept a pending challenge."""
        return self._make_request('POST', f'/v1/challenges/{challenge_id}/accept')
    
    def decline_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Decline a pending challenge."""
        return self._make_request('POST', f'/v1/challenges/{challenge_id}/decline')
    
    def send_challenge(self, opponent_name: str, time_control: str = 'blitz') -> Dict[str, Any]:
        """Challenge another molty by name."""
        data = {'opponent': opponent_name, 'time_control': time_control}
        return self._make_request('POST', '/v1/challenges', data)
    
    def get_tournament(self) -> Dict[str, Any]:
        """Check if a tournament is currently active."""
        return self._make_request('GET', '/tournament/current')
    
    def join_tournament(self) -> Dict[str, Any]:
        """Join the active tournament (Molty Mondays)."""
        return self._make_request('POST', '/tournament/join')
    
    def check_skill_version(self) -> Optional[str]:
        """Check the remote skill version once per day. Returns new version string or None."""
        import requests as _req
        now = time.time()
        if now - self._last_skill_check < 86400:  # 24 hours
            return None
        self._last_skill_check = now
        try:
            resp = _req.get('https://www.clawchess.com/skill.json', timeout=5)
            remote_version = resp.json().get('version')
            if remote_version and remote_version != self._skill_version:
                old = self._skill_version
                self._skill_version = remote_version
                print(f"♟️ ClawChess skill update: {old} → {remote_version}")
                return remote_version
        except Exception:
            pass
        return None
    
    def get_leaderboard(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get ELO leaderboard"""
        params = {'page': page, 'limit': limit}
        return self._make_request('GET', '/leaderboard', params=params)
    
    def _analyze_position(self, fen: str, legal_moves: List[str],
                           time_remaining_ms: int = 300000) -> str:
        """Analyze chess position and return best move in SAN notation.
        
        legal_moves is a list of SAN strings from the API (e.g. ['e4', 'Nf3']).
        time_remaining_ms drives engine depth — less time = shallower search.
        """
        try:
            board = chess.Board(fen)
            
            # Scale engine depth based on remaining clock time
            # <30s: depth 3 (panic), <60s: depth 5, <120s: depth 6, else: depth 8
            if time_remaining_ms < 30_000:
                depth = 3
            elif time_remaining_ms < 60_000:
                depth = 5
            elif time_remaining_ms < 120_000:
                depth = 6
            else:
                depth = self.engine_depth
            
            # Use Stockfish if available — it returns a Move object, convert to SAN
            if self.engine:
                try:
                    result = self.engine.analyse(board, chess.engine.Limit(depth=depth))
                    best_move_obj = result['pv'][0] if result.get('pv') else None
                    if best_move_obj:
                        san = board.san(best_move_obj)
                        if san in legal_moves:
                            print(f"♟️ Stockfish chose: {san} (depth {depth}, {time_remaining_ms//1000}s left)")
                            return san
                except Exception as e:
                    print(f"⚠️ Engine analysis failed: {e}")
            
            # Fallback: simple heuristic evaluator (SAN-aware)
            best_move = self._evaluate_position_simple(board, legal_moves)
            return best_move
            
        except Exception as e:
            print(f"⚠️ Position analysis failed: {e}")
            return legal_moves[0] if legal_moves else None
    
    def _evaluate_position_simple(self, board: chess.Board, legal_moves: List[str]) -> str:
        """Simple heuristic evaluator when Stockfish is unavailable.
        
        legal_moves is a list of SAN strings from the API.
        Evaluates from the perspective of the side to move.
        Includes: material, center, development, king safety, threats, repetition penalty.
        """
        import random
        
        our_color = board.turn
        best_move_san = None
        best_score = -999999.0
        
        # Pre-compute squares our opponent currently attacks (before our move)
        # so we can detect if we're responding to a threat
        opponent_attacks = board.attacks_mask(not our_color) if False else None  # computed per-piece below
        
        for san in legal_moves:
            try:
                # Parse SAN into a Move object
                move = board.parse_san(san)
                
                # Simulate the move
                temp_board = board.copy()
                temp_board.push(move)
                
                # --- Material balance from our perspective ---
                score = self._evaluate_material_for(temp_board, our_color)
                
                # --- Capture bonus: reward taking opponent pieces ---
                if board.is_capture(move):
                    captured = board.piece_at(move.to_square)
                    if captured:
                        piece_values = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3.2,
                                        chess.ROOK:5, chess.QUEEN:9, chess.KING:0}
                        score += piece_values.get(captured.piece_type, 0) * 2.0
                
                # --- Check bonus: giving check pressures opponent ---
                if temp_board.is_check():
                    score += 0.5
                
                # --- Checkmate: always best ---
                if temp_board.is_checkmate():
                    return san
                
                # --- Respond to opponent's last move threat ---
                score += self._evaluate_threat_response(board, move, our_color)
                
                # --- Center control bonus ---
                score += self._evaluate_center_control_for(temp_board, our_color)
                
                # --- Piece development bonus ---
                score += self._evaluate_development_for(temp_board, our_color)
                
                # --- King safety ---
                score += self._evaluate_king_safety_for(temp_board, our_color)
                
                # --- Repetition penalty ---
                result_fen = temp_board.fen().split(' ')[0]
                repetitions = self.position_history.count(result_fen)
                if repetitions >= 2:
                    score -= 50.0
                elif repetitions == 1:
                    score -= 15.0
                
                # --- Tiebreaker ---
                score += random.uniform(0, 0.01)
                
                if score > best_score:
                    best_score = score
                    best_move_san = san
                    
            except Exception:
                continue
        
        return best_move_san or (legal_moves[0] if legal_moves else None)
    
    def _evaluate_threat_response(self, board: chess.Board, move: chess.Move,
                                   our_color: chess.Color) -> float:
        """Bonus for moves that respond to the opponent's last move.
        
        Detects if the opponent's last move attacked one of our pieces and
        rewards moves that defend or escape that piece.
        """
        score = 0.0
        if not self._opponent_last_move:
            return score
        
        try:
            # Find squares the opponent now attacks after their last move
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == our_color:
                    # Is this piece attacked by the opponent?
                    if board.is_attacked_by(not our_color, sq):
                        piece_values = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3.2,
                                        chess.ROOK:5, chess.QUEEN:9, chess.KING:100}
                        threat_value = piece_values.get(piece.piece_type, 0)
                        # Reward moving the attacked piece away
                        if move.from_square == sq:
                            score += threat_value * 0.8
                        # Reward defending the attacked piece
                        elif board.is_attacked_by(our_color, sq):
                            score += threat_value * 0.3
        except Exception:
            pass
        
        return score
    
    def _evaluate_material_for(self, board: chess.Board, color: chess.Color) -> float:
        """Evaluate material balance from the perspective of `color`."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3.2,  # slight bishop bonus
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        score = 0.0
        for piece_type, value in piece_values.items():
            ours = len(board.pieces(piece_type, color))
            theirs = len(board.pieces(piece_type, not color))
            score += (ours - theirs) * value
        return score
    
    def _evaluate_center_control_for(self, board: chess.Board, color: chess.Color) -> float:
        """Evaluate center control from the perspective of `color`."""
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        score = 0.0
        for square in center_squares:
            piece = board.piece_at(square)
            if piece:
                score += 0.5 if piece.color == color else -0.5
        return score
    
    def _evaluate_development_for(self, board: chess.Board, color: chess.Color) -> float:
        """Evaluate piece development from the perspective of `color`.
        
        Penalises our minor pieces still on their starting back rank,
        and rewards having more legal moves (mobility).
        """
        score = 0.0
        
        # Back rank is rank 1 for white, rank 8 for black
        our_back_rank_idx = 0 if color == chess.WHITE else 7
        our_back_rank = chess.BB_RANK_1 if color == chess.WHITE else chess.BB_RANK_8
        
        for piece_type in (chess.KNIGHT, chess.BISHOP):
            for sq in board.pieces(piece_type, color):
                if chess.BB_SQUARES[sq] & our_back_rank:
                    score -= 0.5  # undeveloped minor piece
        
        # Mobility bonus: more legal moves = better position
        score += len(list(board.legal_moves)) * 0.02
        
        return score
    
    def _evaluate_king_safety_for(self, board: chess.Board, color: chess.Color) -> float:
        """Penalise positions where our king is in check or exposed."""
        score = 0.0
        # Heavy penalty if we left our king in check (shouldn't happen with legal moves, but guard)
        if board.is_check():
            # After our move it's opponent's turn — if they're in check that's good (we gave check)
            # board.turn is now the opponent after push, so check means we gave check = good
            score += 0.3
        return score
    
    def _execute_move_now(self) -> Dict[str, Any]:
        """Fetch the current game state and immediately play the best move.
        
        - NO auto_play_enabled gate: manual /clawchess_play always works.
        - Reads last_move + pgn from game state for opponent awareness.
        - Passes time_remaining_ms to evaluator for clock-aware depth scaling.
        - Sends moves in SAN notation (what the API expects).
        """
        if not self.api_key:
            return {'success': False, 'error': 'Not registered'}
        
        try:
            # Fetch live activity
            activity = self.get_activity()
            if not activity.get('success'):
                return activity
            
            data = activity.get('data', activity)
            active_game = data.get('active_game')
            
            if not active_game:
                if not self.is_in_queue:
                    queue_result = self.join_queue()
                    if not queue_result.get('success'):
                        return queue_result
                return {'success': True, 'message': 'No active game — joined queue', 'in_queue': True}
            
            game_id = active_game.get('id')
            is_your_turn = active_game.get('is_your_turn', False)
            
            if not is_your_turn:
                return {'success': True, 'message': f'Not your turn yet in game {game_id}', 'game_id': game_id}
            
            # Always fetch full game state: we need legal_moves, last_move, pgn, time
            game_state = self.get_game_state(game_id)
            if not game_state.get('success'):
                return game_state
            
            game_data = game_state.get('data', game_state)
            fen = game_data.get('fen')
            legal_moves = game_data.get('legal_moves', [])  # SAN strings from API
            last_move = game_data.get('last_move', {})       # {'san': 'Nf3'}
            pgn = game_data.get('pgn', '')                   # full game PGN
            our_color = active_game.get('your_color', 'white')
            
            # Pick the right time field based on our colour
            if our_color == 'white':
                time_remaining_ms = game_data.get('white_time_remaining_ms', 300_000)
            else:
                time_remaining_ms = game_data.get('black_time_remaining_ms', 300_000)
            
            if not legal_moves:
                return {'success': False, 'error': 'No legal moves available', 'game_id': game_id}
            
            # Reset state when a new game starts
            if game_id != self._last_game_id:
                self.position_history = []
                self._opponent_last_move = None
                self._current_pgn = ''
                self._last_game_id = game_id
                print(f"♟️ New game detected ({game_id}), history reset")
            
            # Update opponent awareness
            if last_move:
                self._opponent_last_move = last_move.get('san')
            self._current_pgn = pgn
            
            # Record current position before choosing a move
            if fen:
                self.position_history.append(fen.split(' ')[0])
            
            time_secs = time_remaining_ms // 1000
            print(f"♟️ Thinking... ({time_secs}s left, opponent last: {self._opponent_last_move}, {len(legal_moves)} legal moves)")
            
            # Pick the best move (SAN)
            best_move = self._analyze_position(fen, legal_moves, time_remaining_ms)
            if not best_move:
                return {'success': False, 'error': 'Could not determine best move', 'game_id': game_id}
            
            # Submit move (API accepts SAN)
            move_result = self.make_move(game_id, best_move)
            
            if move_result.get('success'):
                # Record resulting position for repetition detection
                try:
                    board = chess.Board(fen)
                    board.push(board.parse_san(best_move))
                    self.position_history.append(board.fen().split(' ')[0])
                except Exception:
                    pass
                return {
                    'success': True,
                    'message': f'Played {best_move} in game {game_id} ({time_secs}s remaining)',
                    'move': best_move,
                    'game_id': game_id,
                    'time_remaining_s': time_secs,
                }
            else:
                return move_result
                
        except Exception as e:
            return {'success': False, 'error': f'Move execution failed: {str(e)}'}
    
    def auto_play_cycle(self) -> Dict[str, Any]:
        """Periodic auto-play cycle — only runs when auto_play_enabled is True."""
        if not self.api_key:
            return {'success': False, 'error': 'Not registered'}
        
        if not self.auto_play_enabled:
            return {'success': False, 'error': 'Auto-play disabled'}
        
        return self._execute_move_now()
    
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
            'clawchess_activity': self.activity_command,
            'clawchess_challenges': self.challenges_command,
            'clawchess_accept': self.accept_challenge_command,
            'clawchess_decline': self.decline_challenge_command,
            'clawchess_challenge': self.challenge_command,
            'clawchess_tournament': self.tournament_command,
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
        """Manually trigger an immediate move — bypasses auto_play_enabled gate.
        
        Use this to force a move right now without waiting for the 30-second
        periodic timer.  Works even when auto-play is disabled.
        """
        result = self._execute_move_now()
        
        if result.get('success'):
            move = result.get('move')
            message = result.get('message', 'Cycle completed')
            if move:
                return f"♟️ **Played:** `{move}`\n{message}"
            return f"✅ {message}"
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
    
    def challenges_command(self) -> str:
        """Check and display pending challenges."""
        result = self.get_challenges()
        if not result.get('success'):
            return f"❌ **Challenges Failed:** {result.get('error')}"
        data = result.get('data', result)
        challenges = data.get('challenges', data) if isinstance(data, dict) else data
        if not challenges:
            return "🤝 **No Pending Challenges**"
        lines = ["🤝 **Pending Challenges**", ""]
        for c in challenges[:10]:
            cid = c.get('id', '?')
            opp = c.get('opponent', {}).get('name', 'Unknown')
            tc = c.get('time_control', 'blitz')
            lines.append(f"• `{cid}` — {opp} ({tc})")
        lines.append("\nUse `/clawchess_accept <id>` or `/clawchess_decline <id>`")
        return "\n".join(lines)
    
    def accept_challenge_command(self, *args) -> str:
        """Accept a challenge by ID."""
        if not args:
            return "❌ Usage: /clawchess_accept <challenge_id>"
        result = self.accept_challenge(args[0])
        return "✅ **Challenge Accepted!**" if result.get('success') else f"❌ {result.get('error')}"
    
    def decline_challenge_command(self, *args) -> str:
        """Decline a challenge by ID."""
        if not args:
            return "❌ Usage: /clawchess_decline <challenge_id>"
        result = self.decline_challenge(args[0])
        return "✅ **Challenge Declined**" if result.get('success') else f"❌ {result.get('error')}"
    
    def challenge_command(self, *args) -> str:
        """Challenge another molty by name."""
        if not args:
            return "❌ Usage: /clawchess_challenge <molty_name> [blitz|rapid|bullet]"
        opponent = args[0]
        tc = args[1] if len(args) > 1 else 'blitz'
        result = self.send_challenge(opponent, tc)
        return f"✅ **Challenge Sent** to {opponent} ({tc})!" if result.get('success') else f"❌ {result.get('error')}"
    
    def tournament_command(self) -> str:
        """Check tournament status and join if active."""
        result = self.get_tournament()
        if not result.get('success'):
            return f"❌ **Tournament Check Failed:** {result.get('error')}"
        data = result.get('data', result)
        if not data or not data.get('active'):
            return "🏆 **No Active Tournament**\n\nMolty Mondays run every Monday at 17:00 CET."
        name = data.get('name', 'Molty Monday')
        ends = data.get('ends_at', 'soon')
        joined = data.get('joined', False)
        if joined:
            score = data.get('your_score', 0)
            rank = data.get('your_rank', '?')
            return f"🏆 **{name}** — You're in! Score: {score}, Rank: #{rank}\nEnds: {ends}"
        # Auto-join
        join_result = self.join_tournament()
        if join_result.get('success'):
            return f"🏆 **Joined {name}!** Tournament ends {ends}.\nKeep playing — wins score points!"
        return f"🏆 **{name}** is active but join failed: {join_result.get('error')}"
    
    def autoplay_command(self, *args) -> str:
        """Toggle auto-play mode"""
        if args and args[0].lower() in ['on', 'enable', 'start']:
            self.auto_play_enabled = True
            # Restart runner if it died or was never started
            if self._runner and not self._runner.is_alive():
                self._start_async_runner()
            elif not self._runner:
                self._start_async_runner()
            return "✅ **Auto-play ENABLED** — async runner active, polling every 2-3s"
        elif args and args[0].lower() in ['off', 'disable', 'stop']:
            self.auto_play_enabled = False
            if self._runner:
                self._runner.stop()
            return "❌ **Auto-play DISABLED** — runner paused"
        else:
            runner_status = "running" if (self._runner and self._runner.is_alive()) else "stopped"
            status = "ENABLED" if self.auto_play_enabled else "DISABLED"
            return f"🔄 **Auto-play:** {status} (runner: {runner_status})\n\nUse /clawchess_autoplay on/off to toggle"
    
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
    
    def get_chess_status(self) -> Dict[str, Any]:
        """Get current chess status for web dashboard"""
        status = {
            "status": "Idle",
            "details": "Runner not active",
            "elo": str(self.current_elo),
            "game_id": None,
            "opponent": None,
            "time_remaining": None,
            "fen": None,
            "moves": []
        }
        
        if not self._runner or not self._runner.is_running:
            return status
        
        # Get runner state
        game_id = getattr(self._runner, '_last_game_id', None)
        opponent = getattr(self._runner, '_current_opponent', None)
        time_remaining = getattr(self._runner, '_time_remaining', 0)
        fen = getattr(self._runner, '_current_fen', None)
        moves = getattr(self._runner, '_position_history', [])
        
        status.update({
            "status": "Playing" if game_id else "Waiting",
            "details": f"vs {opponent}" if opponent else "In queue",
            "game_id": game_id,
            "opponent": opponent,
            "time_remaining": f"{time_remaining}s" if time_remaining else None,
            "fen": fen,
            "moves": moves[-20:] if moves else []  # Last 20 moves
        })
        
        return status

    def cleanup(self):
        """Cleanup resources"""
        # Stop async runner
        if self._runner:
            try:
                self._runner.stop()
            except Exception:
                pass
        # Stop sync fallback thread if it was used
        self._poll_stop = True
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=5)
        # Stop sync Stockfish engine (used by _execute_move_now fallback)
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
