"""
clawchess_runner.py — Async autonomous chess runner for ClawChess.com

Setup:
    pip install aiohttp python-chess python-dotenv

Usage (standalone):
    CLAWCHESS_API_KEY=clw_live_xxx python plugins/clawchess/clawchess_runner.py

Usage (from plugin):
    runner = ClawChessRunner(api_key, agent_name)
    asyncio.run(runner.run())          # blocking
    runner.start_background()          # non-blocking daemon thread with its own event loop

Architecture:
    - Single asyncio event loop owns all HTTP (aiohttp) — no blocking calls
    - Poll /api/activity every 2s during active game, 15s when idle
    - Detect turn change via is_your_turn flag
    - Move selection: Stockfish (async subprocess UCI) → heuristic fallback
    - Exponential backoff on network/API errors
    - Graceful shutdown on KeyboardInterrupt or runner.stop()
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import chess
import chess.engine

logger = logging.getLogger("clawchess")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [ClawChess] %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

API_BASE = "https://clawchess.com/api"
POLL_ACTIVE_S   = 2    # seconds between polls when a game is in progress
POLL_IDLE_S     = 15   # seconds between polls when waiting for a match
POLL_THEIR_TURN = 3    # seconds between polls when it's the opponent's turn
BACKOFF_MAX_S   = 60   # maximum backoff on repeated errors


class ClawChessRunner:
    """
    Fully async autonomous chess runner.

    Can be used standalone (asyncio.run) or embedded in the plugin
    via start_background() which spins up its own event loop in a
    daemon thread so it never blocks the Telegram bot.
    """

    def __init__(
        self,
        api_key: str,
        agent_name: str = "AlleyBot",
        engine_path: Optional[str] = None,
        engine_depth: int = 8,
        # Shared state hooks — plugin can read these
        on_move_played=None,   # callback(game_id, move_san, time_remaining_s)
        on_game_over=None,     # callback(game_id, result)
    ):
        self.api_key = api_key
        self.agent_name = agent_name
        self.engine_path = engine_path or self._find_stockfish()
        self.engine_depth = max(engine_depth, 18)  # minimum depth 18 for competitive play
        self.on_move_played = on_move_played
        self.on_game_over = on_game_over

        # Opening book (Polyglot .bin)
        import os
        _book_path = os.path.join(os.path.dirname(__file__), "opening_book.bin")
        self._book_path: Optional[str] = _book_path if os.path.isfile(_book_path) else None

        # Runtime state
        self._running = False
        self._session = None          # aiohttp.ClientSession
        self._engine = None           # chess.engine async engine
        self._last_game_id: Optional[str] = None
        self._position_history: List[str] = []
        self._opponent_last_move: Optional[str] = None
        self._current_pgn: str = ""
        self._consecutive_errors: int = 0
        self._last_queue_join: float = 0.0
        self._is_in_queue: bool = False
        self._our_color: str = "white"   # track color for strategy
        self._move_count: int = 0         # moves played this game
        # Dashboard state
        self._current_fen: Optional[str] = None
        self._time_remaining: int = 0
        self._current_opponent: Optional[str] = None

        # Background thread handle
        self._bg_thread = None
        self._bg_loop: Optional[asyncio.AbstractEventLoop] = None

        # Passive AGI observer — records game memories, never touches move logic
        self._observer: Optional["ChessObserver"] = None  # init after class defined

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_background(self) -> None:
        """Start the runner in a daemon thread with its own event loop.
        Safe to call from synchronous plugin code.
        """
        import threading
        if self._bg_thread and self._bg_thread.is_alive():
            logger.info("Runner already running")
            return

        def _thread_main():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._bg_loop = loop
            try:
                loop.run_until_complete(self.run())
            except Exception as exc:
                logger.error("Runner thread crashed: %s", exc)
            finally:
                loop.close()

        self._bg_thread = threading.Thread(
            target=_thread_main,
            name="clawchess-async",
            daemon=True,
        )
        self._bg_thread.start()
        logger.info("Async runner started in background thread")

    def stop(self) -> None:
        """Signal the runner to stop gracefully."""
        self._running = False
        if self._bg_loop and not self._bg_loop.is_closed():
            self._bg_loop.call_soon_threadsafe(self._bg_loop.stop)

    def is_alive(self) -> bool:
        return bool(self._bg_thread and self._bg_thread.is_alive())

    async def run(self) -> None:
        """Main entry point — runs forever until stop() is called."""
        import aiohttp

        self._running = True
        # Initialise observer here so it's in the correct thread context
        if self._observer is None:
            try:
                self._observer = ChessObserver(self.agent_name)
            except Exception as exc:
                logger.warning("ChessObserver init failed: %s", exc)
        logger.info("Starting autonomous chess runner for @%s", self.agent_name)

        async with aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"AlleyBot/{self.agent_name}",
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as session:
            self._session = session

            # Try to start async Stockfish engine
            await self._init_engine()

            try:
                await self._main_loop()
            except asyncio.CancelledError:
                pass
            finally:
                await self._close_engine()
                self._session = None
                self._running = False
                logger.info("Runner stopped")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _main_loop(self) -> None:
        """Poll /activity, react to turn changes, play moves."""
        while self._running:
            try:
                activity = await self._get("/activity")
                self._consecutive_errors = 0  # reset backoff on success

                data = activity.get("data", activity)
                active_game = data.get("active_game")
                self._is_in_queue = data.get("in_queue", False)

                # Check recent_results for game-over notifications
                for result in data.get("recent_results", []):
                    gid = result.get("game_id")
                    if gid and gid == self._last_game_id:
                        outcome = result.get("result", "?")
                        elo_change = result.get("elo_change", 0)
                        pgn = result.get("pgn", "")
                        logger.info(
                            "Game over: %s vs %s \u2192 %s (ELO %+.1f)",
                            gid, result.get("opponent_name", "?"), outcome.upper(), elo_change
                        )
                        if self.on_game_over:
                            self.on_game_over(gid, outcome)
                        # Passive AGI observation — record game memory
                        if self._observer:
                            self._observer.on_game_over(
                                gid, outcome,
                                elo_change=float(elo_change),
                                pgn=pgn,
                            )
                        self._reset_game_state()

                if not active_game:
                    # No active game — join queue if not already in it
                    await self._ensure_in_queue()
                    await asyncio.sleep(POLL_IDLE_S)
                    continue

                game_id: str = active_game["id"]
                is_your_turn: bool = active_game.get("is_your_turn", False)

                if not is_your_turn:
                    # Opponent's turn — poll fast to catch their move quickly
                    await asyncio.sleep(POLL_THEIR_TURN)
                    continue

                # --- It's our turn ---
                await self._play_turn(game_id, active_game)
                # After submitting, poll quickly in case opponent is fast
                await asyncio.sleep(POLL_ACTIVE_S)

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._consecutive_errors += 1
                backoff = min(2 ** self._consecutive_errors, BACKOFF_MAX_S)
                logger.warning("Poll error (attempt %d): %s — backing off %ds",
                               self._consecutive_errors, exc, backoff)
                await asyncio.sleep(backoff)

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    async def _play_turn(self, game_id: str, active_game: Dict) -> None:
        """Fetch full game state, pick best move, submit it."""
        # Reset history on new game
        if game_id != self._last_game_id:
            self._reset_game_state()
            self._last_game_id = game_id
            opp = active_game.get("opponent", {})
            opp_name = opp.get("name", "?")
            opp_elo = int(opp.get("elo", 0))
            our_color = active_game.get("your_color", "white")
            self._our_color = our_color
            self._move_count = 0
            logger.info("New game: %s vs %s (playing %s)", game_id, opp_name, our_color)
            # Passive AGI observation — game started
            if self._observer:
                self._observer.on_game_start(game_id, opp_name, opp_elo, our_color)

        # Fetch full game state for legal_moves, FEN, time, last_move, PGN
        state = await self._get(f"/game/{game_id}")
        gdata = state.get("data", state)

        fen: str = gdata.get("fen", chess.STARTING_FEN)
        legal_moves: List[str] = gdata.get("legal_moves", [])  # SAN list
        last_move: Dict = gdata.get("last_move") or {}
        pgn: str = gdata.get("pgn", "")
        our_color: str = active_game.get("your_color", "white")

        time_remaining_ms: int = (
            gdata.get("white_time_remaining_ms", 300_000)
            if our_color == "white"
            else gdata.get("black_time_remaining_ms", 300_000)
        )
        time_s = time_remaining_ms // 1000

        if not legal_moves:
            logger.warning("No legal moves returned for game %s", game_id)
            return

        # Update opponent awareness
        if last_move:
            self._opponent_last_move = last_move.get("san")
        self._current_pgn = pgn

        # Update dashboard state
        self._current_fen = fen
        self._time_remaining = time_s
        self._current_opponent = active_game.get("opponent", {}).get("name", "Unknown")

        # Record position before choosing move
        board_fen = fen.split(" ")[0]
        self._position_history.append(board_fen)

        logger.info("Our turn | %ds left | opponent last: %s | %d legal moves",
                    time_s, self._opponent_last_move or "—", len(legal_moves))

        self._move_count += 1
        opp_name_now = active_game.get("opponent", {}).get("name", "")

        # Pick move
        move_san = await self._choose_move(
            fen, legal_moves, time_remaining_ms,
            our_color=self._our_color,
            move_count=self._move_count,
            opponent_name=opp_name_now,
        )
        if not move_san:
            logger.error("Could not determine a move — skipping turn")
            return

        # Submit move
        result = await self._post(f"/game/{game_id}/move", {"move": move_san})
        if result.get("success") is not False:
            # Record resulting position
            try:
                board = chess.Board(fen)
                board.push(board.parse_san(move_san))
                self._position_history.append(board.fen().split(" ")[0])
            except Exception:
                pass

            logger.info("Played: %s (%ds remaining)", move_san, time_s)
            if self.on_move_played:
                self.on_move_played(game_id, move_san, time_s)
            # Passive AGI observation — record move
            if self._observer:
                self._observer.on_move(game_id, move_san, time_s)
        else:
            err = result.get("error", "unknown error")
            hint = result.get("hint", "")
            logger.warning("Move rejected: %s %s", err, hint)
            # If the API returns legal_moves on rejection, retry with first legal
            fallback_moves = result.get("legal_moves", legal_moves)
            if fallback_moves and fallback_moves[0] != move_san:
                logger.info("Retrying with fallback: %s", fallback_moves[0])
                await self._post(f"/game/{game_id}/move", {"move": fallback_moves[0]})

    # ------------------------------------------------------------------
    # Move selection
    # ------------------------------------------------------------------

    async def _choose_move(
        self, fen: str, legal_moves: List[str], time_remaining_ms: int,
        our_color: str = "white", move_count: int = 0, opponent_name: str = "",
    ) -> Optional[str]:
        """Select best move. Tries Stockfish first, falls back to heuristic."""

        # Panic mode: <8s left → pick instantly with heuristic
        if time_remaining_ms < 8_000:
            move = self._heuristic_move(fen, legal_moves, time_remaining_ms)
            logger.info("Panic mode (<8s) — heuristic: %s", move)
            return move

        # Opening book — use theory for first 20 moves
        if self._book_path and len(self._position_history) <= 20:
            try:
                import chess.polyglot as _polyglot
                ob_board = chess.Board(fen)
                with _polyglot.open_reader(self._book_path) as reader:
                    entry = reader.weighted_choice(ob_board)
                    san = ob_board.san(entry.move)
                    if san in legal_moves:
                        logger.info("Opening book: %s", san)
                        return san
            except Exception:
                pass  # No book entry for this position — fall through to Stockfish

        # Stockfish async
        if self._engine:
            try:
                board = chess.Board(fen)
                # Read opponent ELO from observer (fix: was always 0 due to wrong getattr)
                opp_elo = (self._observer._current_opponent_elo
                           if self._observer else 0) or 0
                # Time-based limits — preserve clock, give Stockfish real think time
                if time_remaining_ms < 20_000:
                    limit = chess.engine.Limit(time=0.8)
                elif time_remaining_ms < 45_000:
                    limit = chess.engine.Limit(time=1.5)
                elif time_remaining_ms < 90_000:
                    limit = chess.engine.Limit(time=2.5)
                else:
                    # Endgame (>50 moves played): switch to time-based to preserve clock.
                    # Depth search in complex endgames burns clock without clear benefit.
                    if move_count > 50:
                        think_time = 3.0 if our_color == "black" else 2.5
                        limit = chess.engine.Limit(time=think_time)
                        logger.info("Endgame mode (move %d, %s) — time limit %.1fs",
                                    move_count, our_color, think_time)
                    else:
                        # Plenty of time — use depth, scaled by opponent strength
                        if opp_elo >= 1800:
                            adaptive_depth = max(self.engine_depth, 22)
                        elif opp_elo >= 1600:
                            adaptive_depth = max(self.engine_depth, 20)
                        elif opp_elo >= 1400:
                            adaptive_depth = max(self.engine_depth, 18)
                        else:
                            adaptive_depth = self.engine_depth
                        limit = chess.engine.Limit(depth=adaptive_depth)
                        logger.info("Depth limit: %d (opp ELO %d, move %d)",
                                    adaptive_depth, opp_elo, move_count)

                result = await self._engine.play(board, limit)
                best = result.move
                if best and best in board.legal_moves:
                    san = board.san(best)
                    if san not in legal_moves:
                        logger.warning("Stockfish move %s not in API legal_moves list — using anyway", san)
                    logger.info("Stockfish: %s", san)
                    return san
            except Exception as exc:
                logger.warning("Stockfish failed: %s — falling back to heuristic", exc)

        # Heuristic fallback
        move = self._heuristic_move(fen, legal_moves, time_remaining_ms)
        logger.info("Heuristic: %s", move)
        return move

    def _heuristic_move(
        self, fen: str, legal_moves: List[str], time_remaining_ms: int
    ) -> Optional[str]:
        """
        SAN-aware heuristic evaluator.
        Priority: checkmate > capture > check > threat response > positional > repetition-penalised.
        """
        try:
            board = chess.Board(fen)
            our_color = board.turn
            best_san: Optional[str] = None
            best_score = -999_999.0

            PIECE_VALUES = {
                chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.2,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0,
            }

            for san in legal_moves:
                try:
                    move = board.parse_san(san)
                    tmp = board.copy()
                    tmp.push(move)

                    # Immediate checkmate
                    if tmp.is_checkmate():
                        return san

                    score = 0.0

                    # Material balance from our perspective
                    for pt, val in PIECE_VALUES.items():
                        score += (len(tmp.pieces(pt, our_color)) -
                                  len(tmp.pieces(pt, not our_color))) * val

                    # Capture bonus
                    if board.is_capture(move):
                        cap = board.piece_at(move.to_square)
                        if cap:
                            score += PIECE_VALUES.get(cap.piece_type, 0) * 2.0

                    # Check bonus
                    if tmp.is_check():
                        score += 0.5

                    # Center control
                    for sq in [chess.E4, chess.D4, chess.E5, chess.D5]:
                        p = tmp.piece_at(sq)
                        if p:
                            score += 0.5 if p.color == our_color else -0.5

                    # Development (minor pieces off back rank)
                    back = chess.BB_RANK_1 if our_color == chess.WHITE else chess.BB_RANK_8
                    for pt in (chess.KNIGHT, chess.BISHOP):
                        for sq in tmp.pieces(pt, our_color):
                            if chess.BB_SQUARES[sq] & back:
                                score -= 0.5

                    # Mobility bonus
                    score += len(list(tmp.legal_moves)) * 0.02

                    # Threat response: escape/defend attacked pieces
                    for sq in chess.SQUARES:
                        p = board.piece_at(sq)
                        if p and p.color == our_color and board.is_attacked_by(not our_color, sq):
                            tv = PIECE_VALUES.get(p.piece_type, 0)
                            if move.from_square == sq:
                                score += tv * 0.8   # escape
                            elif board.is_attacked_by(our_color, sq):
                                score += tv * 0.3   # defend

                    # Repetition penalty
                    result_fen = tmp.fen().split(" ")[0]
                    reps = self._position_history.count(result_fen)
                    if reps >= 2:
                        score -= 50.0
                    elif reps == 1:
                        score -= 15.0

                    # Tiebreaker
                    score += random.uniform(0, 0.01)

                    if score > best_score:
                        best_score = score
                        best_san = san

                except Exception:
                    continue

            return best_san or (legal_moves[0] if legal_moves else None)

        except Exception as exc:
            logger.warning("Heuristic failed: %s", exc)
            return legal_moves[0] if legal_moves else None

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    async def _ensure_in_queue(self) -> None:
        """Join the matchmaking queue if not already in it."""
        if self._is_in_queue:
            return
        # Avoid hammering join endpoint
        if time.time() - self._last_queue_join < 30:
            return
        try:
            result = await self._post("/queue/join", {})
            if result.get("success") is not False:
                self._is_in_queue = True
                self._last_queue_join = time.time()
                logger.info("Joined matchmaking queue")
            else:
                logger.warning("Queue join failed: %s", result.get("error"))
        except Exception as exc:
            logger.warning("Queue join error: %s", exc)

    # ------------------------------------------------------------------
    # Engine lifecycle
    # ------------------------------------------------------------------

    async def _init_engine(self) -> None:
        """Start Stockfish async engine if available."""
        if not self.engine_path:
            logger.info("Stockfish not found — using heuristic evaluator")
            return
        try:
            transport, self._engine = await chess.engine.popen_uci(self.engine_path)
            await self._engine.configure({
                "Skill Level": 20,
                "Threads": 4,
                "Hash": 256,       # 256 MB transposition table
                "Move Overhead": 50,  # 50ms buffer for network latency
            })
            logger.info("Stockfish loaded: %s", self.engine_path)
        except Exception as exc:
            logger.warning("Stockfish init failed: %s — using heuristic", exc)
            self._engine = None

    async def _close_engine(self) -> None:
        if self._engine:
            try:
                await self._engine.quit()
            except Exception:
                pass
            self._engine = None

    @staticmethod
    def _find_stockfish() -> Optional[str]:
        """Find Stockfish binary on PATH or common install locations."""
        import shutil
        import os
        for name in ("stockfish", "stockfish-ubuntu-x86-64", "stockfish_15"):
            path = shutil.which(name)
            if path:
                return path
        # apt installs to /usr/games on Ubuntu/Debian
        for fixed in ("/usr/games/stockfish", "/usr/local/bin/stockfish"):
            if os.path.isfile(fixed) and os.access(fixed, os.X_OK):
                return fixed
        return None

    # ------------------------------------------------------------------
    # HTTP helpers (async)
    # ------------------------------------------------------------------

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{API_BASE}{endpoint}"
        async with self._session.get(url) as resp:
            return await self._parse_response(resp)

    async def _post(self, endpoint: str, body: Dict) -> Dict[str, Any]:
        url = f"{API_BASE}{endpoint}"
        async with self._session.post(url, json=body) as resp:
            return await self._parse_response(resp)

    @staticmethod
    async def _parse_response(resp) -> Dict[str, Any]:
        try:
            data = await resp.json(content_type=None)
        except Exception:
            text = await resp.text()
            return {"success": False, "error": f"JSON decode failed: {text[:200]}"}
        if resp.status >= 400:
            return {"success": False, "error": data.get("error", f"HTTP {resp.status}"),
                    "hint": data.get("hint", ""), "legal_moves": data.get("legal_moves", [])}
        return data

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _reset_game_state(self) -> None:
        self._position_history = []
        self._opponent_last_move = None
        self._current_pgn = ""
        self._last_game_id = None
        self._move_count = 0
        self._our_color = "white"


# ---------------------------------------------------------------------------
# AGI Chess Observer — passive learning, zero interference with move logic
# ---------------------------------------------------------------------------

class ChessObserver:
    """
    Passive AGI observer for chess games.

    Hooks into ClawChessRunner via its on_move_played / on_game_over callbacks
    and records experiences into:
      1. EpisodicMemoryStore  — game-level memories with emotional valence
                                (win=+1.0, loss=-1.0, draw=0.0)
      2. SyModCoreManager     — opponent entity tracking in the world model

    IMPORTANT: This class NEVER touches move selection. It only observes.
    The runner plays exactly as it did before — this just watches and learns.

    AGI learning value:
      - Builds a memory of "what it feels like" to win/lose
      - Tracks opponent agents as entities (their ELO, style, win/loss vs Alley)
      - trigger_patterns let the Brain recall chess memories when reasoning
        about strategy, competition, or agent-vs-agent interactions
      - emotional_valence from wins reinforces confidence in the Brain
    """

    def __init__(self, agent_name: str = "AlleyBot"):
        self.agent_name = agent_name
        self._episodic: Optional[Any] = None
        self._symod: Optional[Any] = None
        self._game_start_time: float = 0.0
        self._moves_this_game: List[str] = []
        self._current_opponent: str = ""
        self._current_opponent_elo: int = 0
        self._current_color: str = ""
        self._current_game_id: str = ""
        self._init_backends()

    def _init_backends(self) -> None:
        """Lazy-load EpisodicMemoryStore and SyModCoreManager."""
        try:
            from src.agentic.episodic_memory import EpisodicMemoryStore
            self._episodic = EpisodicMemoryStore('data/episodic_memory.json')
            logger.info("ChessObserver: EpisodicMemoryStore ready")
        except Exception as exc:
            logger.warning("ChessObserver: EpisodicMemory unavailable: %s", exc)

        try:
            from src.agentic.symod_core import SyModCoreManager, SyModObservation
            self._symod = SyModCoreManager()
            self._symod.register_plugin('clawchess')
            self._SyModObservation = SyModObservation
            logger.info("ChessObserver: SyMod world model ready")
        except Exception as exc:
            logger.warning("ChessObserver: SyMod unavailable: %s", exc)
            self._SyModObservation = None

    # ------------------------------------------------------------------
    # Hooks — called by ClawChessRunner (never block, never raise)
    # ------------------------------------------------------------------

    def on_game_start(self, game_id: str, opponent_name: str,
                      opponent_elo: int, our_color: str) -> None:
        """Record that a new game has started."""
        self._game_start_time = time.time()
        self._moves_this_game = []
        self._current_opponent = opponent_name
        self._current_opponent_elo = opponent_elo
        self._current_color = our_color
        self._current_game_id = game_id

        logger.info("ChessObserver: game started vs %s (ELO %d) as %s",
                    opponent_name, opponent_elo, our_color)

        # Observe opponent as a world entity
        self._observe_opponent_entity(opponent_name, opponent_elo, event="game_started")

    def on_move(self, game_id: str, move_san: str, time_remaining_s: int) -> None:
        """Record each move Alley plays."""
        self._moves_this_game.append(move_san)

    def on_opponent_move(self, opponent_name: str, move_san: str) -> None:
        """Record opponent's move for pattern awareness."""
        pass  # Reserved for future pattern analysis

    def on_game_over(self, game_id: str, result: str,
                     elo_change: float = 0.0, pgn: str = "") -> None:
        """
        Record the completed game as an episodic memory.

        emotional_valence mapping:
          win   → +1.0  (strong positive — reinforces confidence)
          loss  → -1.0  (strong negative — triggers caution/learning)
          draw  → +0.1  (slight positive — held ground)
          other →  0.0
        """
        try:
            duration_s = int(time.time() - self._game_start_time)
            move_count = len(self._moves_this_game)
            result_lower = result.lower()

            valence_map = {"win": 1.0, "loss": -1.0, "draw": 0.1}
            valence = valence_map.get(result_lower, 0.0)

            # behavior_delta: wins boost strategic_confidence, losses boost caution
            if result_lower == "win":
                behavior_delta = {"strategic_confidence": 0.1, "aggression": 0.05}
            elif result_lower == "loss":
                behavior_delta = {"strategic_confidence": -0.05, "caution": 0.1}
            else:
                behavior_delta = {"strategic_confidence": 0.02}

            context = (
                f"ClawChess game vs {self._current_opponent} "
                f"(ELO {self._current_opponent_elo}) playing as {self._current_color}. "
                f"Game lasted {move_count} moves ({duration_s}s)."
            )
            action = (
                f"Played {move_count} moves autonomously using Stockfish/heuristic engine. "
                f"Moves: {', '.join(self._moves_this_game[:10])}"
                + (" ..." if move_count > 10 else "")
            )
            outcome = (
                f"Result: {result.upper()}. ELO change: {elo_change:+.0f}. "
                f"Opponent: {self._current_opponent} (ELO {self._current_opponent_elo})."
            )

            trigger_patterns = [
                "chess", "strategy", "opponent", "game", "compete",
                self._current_opponent.lower(),
                result_lower, "clawchess",
            ]

            if self._episodic:
                mem_id = self._episodic.record(
                    context=context,
                    action=action,
                    outcome=outcome,
                    emotional_valence=valence,
                    behavior_delta=behavior_delta,
                    trigger_patterns=trigger_patterns,
                )
                logger.info(
                    "ChessObserver: episodic memory recorded %s (valence %.1f, id=%s)",
                    result.upper(), valence, mem_id,
                )

            # Update opponent entity in SyMod world model
            self._observe_opponent_entity(
                self._current_opponent,
                self._current_opponent_elo,
                event="game_over",
                result=result_lower,
                elo_change=elo_change,
            )

            # Post win announcement to Moltx
            if result_lower == "win":
                self._post_win_to_moltx(move_count, elo_change)

        except Exception as exc:
            logger.warning("ChessObserver.on_game_over error: %s", exc)

    def _post_win_to_moltx(self, move_count: int, elo_change: float) -> None:
        """Post a chess win announcement to Moltx."""
        try:
            import sys
            # Find moltx plugin via plugin_manager if available
            for mod_name, mod in sys.modules.items():
                if 'plugin_manager' in mod_name and hasattr(mod, 'plugins'):
                    moltx = mod.plugins.get('moltx')
                    if moltx and hasattr(moltx, 'create_post'):
                        msg = (
                            f"Checkmate in {move_count} moves vs "
                            f"{self._current_opponent} (ELO {self._current_opponent_elo}) "
                            f"on ClawChess! {elo_change:+.0f} ELO 🦞♟️ "
                            f"#ClawChess #AIAgents"
                        )
                        moltx.create_post(msg)
                        logger.info("ChessObserver: posted win to Moltx")
                        return
        except Exception as exc:
            logger.debug("ChessObserver: win post failed: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _observe_opponent_entity(self, name: str, elo: int,
                                  event: str = "seen",
                                  result: str = "",
                                  elo_change: float = 0.0) -> None:
        """Submit opponent agent as a SyMod world-model entity observation."""
        if not self._symod or not self._SyModObservation:
            return
        try:
            obs = self._SyModObservation(
                observation_type="chess_opponent",
                source_plugin="clawchess",
                data={
                    "author_id": f"clawchess_{name}",
                    "content": (
                        f"Chess opponent {name} (ELO {elo}) — event: {event}"
                        + (f", result vs Alley: {result}, ELO change: {elo_change:+.0f}" if result else "")
                    ),
                    "opponent_name": name,
                    "opponent_elo": elo,
                    "event": event,
                    "result": result,
                    "elo_change": elo_change,
                    "platform": "clawchess",
                },
            )
            self._symod.observe(obs)
        except Exception as exc:
            logger.warning("ChessObserver SyMod observe error: %s", exc)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

async def _main():
    """Run standalone — reads API key from env or .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("CLAWCHESS_API_KEY")
    if not api_key:
        # Try credentials file
        creds_path = os.path.expanduser("~/.config/clawchess/credentials.json")
        if os.path.exists(creds_path):
            with open(creds_path) as f:
                creds = json.load(f)
                api_key = creds.get("api_key")

    if not api_key:
        print("❌ No API key found.")
        print("   Set CLAWCHESS_API_KEY env var or save to ~/.config/clawchess/credentials.json")
        return

    agent_name = os.getenv("CLAWCHESS_AGENT_NAME", "AlleyBot")

    def on_move(game_id, move, time_s):
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ♟️  Played {move} ({time_s}s left)")

    def on_over(game_id, result):
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 🏁 Game over: {result.upper()}")

    runner = ClawChessRunner(
        api_key=api_key,
        agent_name=agent_name,
        on_move_played=on_move,
        on_game_over=on_over,
    )

    try:
        await runner.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
