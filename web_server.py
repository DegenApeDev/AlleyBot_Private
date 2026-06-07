#!/usr/bin/env python3
"""
AlleyBot Web Dashboard Server
Serves the dashboard with live chess status and comprehensive system metrics.
Provides a JSON API powering a live AGI dashboard.
"""
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web, WSMsgType
import aiohttp_cors

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from alleybot_core import AlleyBotCore


class DashboardServer:
    """Web server for AlleyBot dashboard with live chess status"""

    def __init__(self, core: AlleyBotCore, port: int = 8080):
        self.core = core
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/", self.serve_dashboard)
        self.app.router.add_get("/api/status", self.api_status)
        self.app.router.add_get("/api/stats", self.api_stats)
        self.app.router.add_get("/api/recent_activity", self.api_recent_activity)
        self.app.router.add_get("/api/chess", self.api_chess_status)
        self.app.router.add_get("/api/debates", self.api_debate_status)
        self.app.router.add_get("/api/chain", self.api_chain_status)
        self.app.router.add_get("/ws", self.websocket_handler)

        # WebSocket connections for live updates
        self.websockets: set = set()

        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def serve_dashboard(self, request):
        """Serve the main dashboard HTML"""
        template_path = Path(__file__).parent / "templates" / "agi_dashboard_v3.html"
        if not template_path.exists():
            # Fallback to v2 if v3 doesn't exist
            template_path = Path(__file__).parent / "templates" / "dashboard_v2.html"
        if not template_path.exists():
            return web.Response(text="Dashboard template not found", status=404)

        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Inject live chess status section
        chess_section = self._get_chess_section_html()
        html = html.replace(
            '<!-- LIVE CHESS STATUS -->',
            chess_section
        )

        return web.Response(text=html, content_type='text/html')

    def _get_chess_section_html(self) -> str:
        """Generate HTML for live chess status section"""
        return '''
        <!-- LIVE CHESS STATUS -->
        <div class="metrics">
            <div class="metric blue" id="chess-status-metric">
                <div class="metric-icon">♟️</div>
                <div class="metric-label">Chess Status</div>
                <div class="metric-val" id="chess-status">Loading...</div>
                <div class="metric-sub" id="chess-details">Connecting to game...</div>
            </div>

            <div class="metric green" id="chess-elo-metric">
                <div class="metric-icon">🏆</div>
                <div class="metric-label">Chess ELO</div>
                <div class="metric-val" id="chess-elo">-</div>
                <div class="metric-sub">Current ranking</div>
            </div>

            <div class="metric purple" id="chess-game-metric">
                <div class="metric-icon">🎮</div>
                <div class="metric-label">Current Game</div>
                <div class="metric-val" id="chess-game">-</div>
                <div class="metric-sub" id="chess-opponent">-</div>
            </div>

            <div class="metric orange" id="chess-time-metric">
                <div class="metric-icon">⏱️</div>
                <div class="metric-label">Time Remaining</div>
                <div class="metric-val" id="chess-time">-</div>
                <div class="metric-sub">Clock status</div>
            </div>
        </div>

        <div class="hero" style="margin-top: 32px;">
            <div class="hero-info">
                <h2>Live Chess Board</h2>
                <div id="chess-board-container" style="margin-top: 20px;">
                    <div id="chess-board" style="
                        display: grid;
                        grid-template-columns: repeat(8, 1fr);
                        gap: 1px;
                        background: var(--border);
                        padding: 1px;
                        border-radius: 8px;
                        width: 320px;
                        height: 320px;
                        margin: 0 auto;
                    ">
                        <!-- Chess board squares will be inserted here -->
                    </div>
                    <div id="chess-moves" style="margin-top: 16px; font-family: 'JetBrains Mono', monospace; font-size: 0.9em; color: var(--text2); max-height: 120px; overflow-y: auto;">
                        <!-- Move list will be inserted here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
        // Live chess updates
        let chessSocket = null;

        function connectChessSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            chessSocket = new WebSocket(`${protocol}//${window.location.host}/ws`);

            chessSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'chess_update') {
                    updateChessDisplay(data.data);
                }
            };

            chessSocket.onclose = () => {
                setTimeout(connectChessSocket, 5000);
            };
        }

        function updateChessDisplay(data) {
            document.getElementById('chess-status').textContent = data.status || 'Unknown';
            document.getElementById('chess-details').textContent = data.details || '';
            document.getElementById('chess-elo').textContent = data.elo || '-';
            document.getElementById('chess-game').textContent = data.game_id ? data.game_id.substring(0, 8) + '...' : '-';
            document.getElementById('chess-opponent').textContent = data.opponent || '-';
            document.getElementById('chess-time').textContent = data.time_remaining || '-';

            // Update chess board if FEN provided
            if (data.fen) {
                renderChessBoard(data.fen);
            }

            // Update moves list
            if (data.moves && data.moves.length > 0) {
                document.getElementById('chess-moves').innerHTML =
                    '<strong>Move history:</strong><br>' +
                    data.moves.slice(-10).join(' ');
            }
        }

        function renderChessBoard(fen) {
            const board = document.getElementById('chess-board');
            const parts = fen.split(' ')[0].split('/');
            const pieces = {
                'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
                'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
            };

            let html = '';
            for (let row = 0; row < 8; row++) {
                const rank = parts[row];
                let col = 0;
                for (let char of rank) {
                    if (char >= '1' && char <= '8') {
                        const empty = parseInt(char);
                        for (let i = 0; i < empty; i++) {
                            const isLight = (row + col) % 2 === 0;
                            html += `<div style="background: ${isLight ? '#f0d9b5' : '#b58863'}; display: flex; align-items: center; justify-content: center; font-size: 24px;"></div>`;
                            col++;
                        }
                    } else {
                        const isLight = (row + col) % 2 === 0;
                        html += `<div style="background: ${isLight ? '#f0d9b5' : '#b58863'}; display: flex; align-items: center; justify-content: center; font-size: 24px;">${pieces[char] || ''}</div>`;
                        col++;
                    }
                }
            }
            board.innerHTML = html;
        }

        // Initial load
        fetch('/api/chess').then(r => r.json()).then(data => updateChessDisplay(data));

        // Connect WebSocket for live updates
        connectChessSocket();
        </script>
        '''

    async def api_status(self, request):
        """General system status API"""
        try:
            pm = self.core.plugin_manager
            status = {
                "timestamp": time.time(),
                "uptime": time.time() - getattr(self.core, '_start_time', time.time()),
                "plugins": list(pm.plugins.keys()) if pm else [],
                "plugin_count": len(pm.plugins) if pm else 0,
                "memory": "SQLite" if hasattr(self.core, 'memory_db') and self.core.memory_db else "JSON",
                "agi_kernel": self.core.agi_kernel is not None,
                "brain_running": self._get_brain_running(),
            }
            return web.json_response(status)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    def _get_brain_running(self) -> bool:
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            return bool(brain and getattr(brain, 'autonomous_running', False))
        except Exception:
            return False

    async def api_chess_status(self, request):
        """Live chess status API"""
        try:
            # Get ClawChess plugin
            clawchess = self.core.plugin_manager.plugins.get('clawchess')
            if not clawchess:
                return web.json_response({
                    "status": "Plugin not loaded",
                    "details": "ClawChess plugin not available"
                })

            # Use the plugin's status method
            status = clawchess.get_chess_status()
            return web.json_response(status)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def api_debate_status(self, request):
        """Live debate status API"""
        try:
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            if not clawbr:
                return web.json_response({"status": "Plugin not loaded"})

            runner = getattr(clawbr, '_debate_runner', None)
            if not runner or not runner.is_running:
                return web.json_response({"status": "Idle", "active_debates": 0})

            # Count active debates
            my_debates = clawbr.get_my_debates()
            active_count = 0
            debates = []
            if my_debates.get('success'):
                debates = my_debates.get('debates', [])
                active_count = sum(1 for d in debates if d.get('isMyTurn'))

            return web.json_response({
                "status": "Active" if active_count > 0 else "Idle",
                "active_debates": active_count,
                "total_debates": len(debates) if my_debates.get('success') else 0
            })

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def api_chain_status(self, request):
        """Chain observer status API"""
        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if not onchain:
                return web.json_response({"status": "Plugin not loaded"})

            summary = onchain.get_chain_summary() if hasattr(onchain, 'get_chain_summary') else "No summary available"

            return web.json_response({
                "status": "Active",
                "summary": summary,
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def api_recent_activity(self, request):
        """Return recent actions from action_router's execution_history"""
        try:
            recent = []
            limit = int(request.query.get('limit', 20))

            # Try action router first
            if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                agi = self.core.agi_kernel
                if hasattr(agi, 'action_router') and agi.action_router:
                    history = getattr(agi.action_router, 'execution_history', [])
                    if history:
                        recent = list(reversed(history[-limit:]))

            # Fallback: try action_logger
            if not recent:
                try:
                    from src.agentic.action_logger import get_action_logger
                    al = get_action_logger()
                    if al and hasattr(al, 'get_recent'):
                        recent = al.get_recent(limit=limit)
                except Exception:
                    pass

            # Fallback: check brain cycles
            if not recent:
                try:
                    brain = self.core.plugin_manager.plugins.get('brain')
                    if brain and hasattr(brain, '_autonomous_brain'):
                        ab = brain._autonomous_brain
                        if hasattr(ab, 'cycle_log') and ab.cycle_log:
                            recent = list(reversed(ab.cycle_log[-limit:]))
                except Exception:
                    pass

            # Fallback: memory-based activity log
            if not recent:
                try:
                    activity_memory = self.core.get_memory('recent_activity')
                    if isinstance(activity_memory, dict):
                        entries = activity_memory.get('entries', [])
                        recent = list(reversed(entries[-limit:]))
                except Exception:
                    pass

            return web.json_response({
                "timestamp": time.time(),
                "activities": recent,
                "count": len(recent),
            })
        except Exception as e:
            return web.json_response({"error": str(e), "activities": []}, status=500)

    async def api_stats(self, request):
        """Comprehensive stats from all AlleyBot systems"""
        try:
            stats = {
                'timestamp': time.time(),
                'uptime': time.time() - getattr(self.core, '_start_time', time.time()),
                'brain': self._get_brain_stats(),
                'agi_kernel': self._get_agi_kernel_stats(),
                'goals': self._get_goal_stats(),
                'platforms': self._get_platform_stats(),
                'chain': self._get_chain_stats(),
                'system': self._get_system_health(),
                'skills': self._get_skills_stats(),
                'selfimprove': self._get_selfimprove_stats(),
                'a2a': self._get_a2a_stats(),
                'memory': self._get_memory_stats(),
                'plugins': self._get_plugin_stats(),
            }
            return web.json_response(stats)
        except Exception as e:
            print(f"Stats API error: {e}")
            import traceback
            traceback.print_exc()
            return web.json_response({"error": str(e)}, status=500)

    # -------------------------------------------------------------------------
    # Brain stats
    # -------------------------------------------------------------------------
    def _get_brain_stats(self) -> Dict[str, Any]:
        """Get stats from the Brain plugin and AutonomousBrain"""
        stats = {
            'running': False,
            'cycle_count': 0,
            'cycles_completed': 0,
            'actions_taken': 0,
            'actions_blocked': 0,
            'errors': 0,
            'goals_completed_total': 0,
            'goals_failed_total': 0,
            'quota_warnings': 0,
            'start_time': None,
        }
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if not brain:
                return stats

            stats['running'] = getattr(brain, 'autonomous_running', False)
            stats['cycle_count'] = getattr(brain, 'cycle_count', 0)

            ab = getattr(brain, '_autonomous_brain', None)
            if ab:
                s = getattr(ab, 'stats', {})
                if s:
                    stats['cycles_completed'] = s.get('cycles_completed', 0)
                    stats['actions_taken'] = s.get('actions_taken', 0)
                    stats['actions_blocked'] = s.get('actions_blocked', 0)
                    stats['errors'] = s.get('errors', 0)
                    stats['goals_completed_total'] = s.get('goals_completed_total', 0)
                    stats['goals_failed_total'] = s.get('goals_failed_total', 0)
                    stats['quota_warnings'] = s.get('quota_warnings', 0)
                    start = s.get('start_time')
                    if start:
                        stats['start_time'] = start.isoformat() if hasattr(start, 'isoformat') else str(start)
        except Exception as e:
            print(f"Error getting brain stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # AGI Kernel stats
    # -------------------------------------------------------------------------
    def _get_agi_kernel_stats(self) -> Dict[str, Any]:
        """Get AGI Kernel statistics from real sources"""
        stats = {
            'available': False,
            'cycles_run': 0,
            'decisions_made': 0,
            'actions_executed': 0,
            'success_rate': 0,
            'errors_detected': 0,
            'errors_fixed': 0,
            'outcome_learner': {},
            'execution_summary': {},
        }

        try:
            if not hasattr(self.core, 'agi_kernel') or not self.core.agi_kernel:
                return stats

            agi = self.core.agi_kernel
            stats['available'] = True

            # Action router stats
            if hasattr(agi, 'action_router') and agi.action_router:
                ar = agi.action_router
                if hasattr(ar, 'execution_history'):
                    history = ar.execution_history
                    stats['decisions_made'] = len(history)
                    if history:
                        successes = sum(1 for h in history if h.get('success'))
                        total = len(history)
                        stats['success_rate'] = round(successes / total * 100, 1) if total > 0 else 0
                        stats['execution_summary'] = {
                            'total': total,
                            'successes': successes,
                            'failures': total - successes,
                        }
                        # Action type breakdown
                        action_types = {}
                        for h in history:
                            at = h.get('action_type', 'unknown')
                            action_types.setdefault(at, {'total': 0, 'success': 0})
                            action_types[at]['total'] += 1
                            if h.get('success'):
                                action_types[at]['success'] += 1
                        stats['execution_summary']['by_action_type'] = action_types

            # Outcome learner stats
            if hasattr(agi, 'outcome_learner') and agi.outcome_learner:
                ol = agi.outcome_learner
                pba = getattr(ol, 'performance_by_action', None)
                if pba:
                    action_stats = {}
                    total_success = 0
                    total_actions = 0
                    for action_type, perf in pba.items():
                        s = {'success': perf.get('success', 0), 'total': perf.get('total', 0), 'failure': perf.get('failure', 0)}
                        if s['total'] > 0:
                            s['rate'] = round(s['success'] / s['total'] * 100, 1)
                        action_stats[action_type] = s
                        total_success += s['success']
                        total_actions += s['total']
                    stats['outcome_learner'] = {
                        'performance_by_action': action_stats,
                        'total_success': total_success,
                        'total_actions': total_actions,
                        'overall_rate': round(total_success / total_actions * 100, 1) if total_actions > 0 else 0,
                    }

            # Brain-level cycle count as cycles_run
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                ab = getattr(brain, '_autonomous_brain', None)
                if ab and hasattr(ab, 'stats'):
                    stats['cycles_run'] = ab.stats.get('cycles_completed', 0)
                    stats['actions_executed'] = ab.stats.get('actions_taken', 0)
                    stats['errors_detected'] = ab.stats.get('errors', 0)

        except Exception as e:
            print(f"Error getting AGI kernel stats: {e}")

        return stats

    # -------------------------------------------------------------------------
    # Goal stats
    # -------------------------------------------------------------------------
    def _get_goal_stats(self) -> Dict[str, Any]:
        """Get goal statistics from the brain and goal manager"""
        stats = {
            'goals_generated': 0,
            'goals_active': 0,
            'goals_completed': 0,
            'goals_failed': 0,
            'goal_success_rate': 0,
        }

        try:
            # From brain stats
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                ab = getattr(brain, '_autonomous_brain', None)
                if ab:
                    s = getattr(ab, 'stats', {})
                    stats['goals_completed'] = s.get('goals_completed_total', 0)
                    stats['goals_failed'] = s.get('goals_failed_total', 0)
                    total = stats['goals_completed'] + stats['goals_failed']
                    if total > 0:
                        stats['goal_success_rate'] = round(stats['goals_completed'] / total * 100, 1)

            # From goal manager (agi_kernel)
            if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                agi = self.core.agi_kernel
                if hasattr(agi, 'goal_manager') and agi.goal_manager:
                    gm = agi.goal_manager
                    if hasattr(gm, 'get_goals'):
                        all_goals = gm.get_goals(limit=500)
                        stats['goals_generated'] = len(all_goals)
                        by_status = {}
                        for g in all_goals:
                            status = g.get('status', g.status if hasattr(g, 'status') else 'UNKNOWN')
                            by_status[status] = by_status.get(status, 0) + 1
                        stats['goals_by_status'] = by_status
                        stats['goals_active'] = by_status.get('ACTIVE', 0) + by_status.get('APPROVED', 0)
                        stats['goals_completed'] = max(stats['goals_completed'], by_status.get('COMPLETED', 0))

                # From goal_hierarchy (if available)
                if hasattr(agi, 'goal_hierarchy') and agi.goal_hierarchy:
                    gh = agi.goal_hierarchy
                    if hasattr(gh, 'get_stats'):
                        stats['hierarchy'] = gh.get_stats()

            # From enhanced memory
            if self.core.enhanced_memory:
                try:
                    active_goals = self.core.get_active_goals()
                    stats['enhanced_active_goals'] = len(active_goals)
                except Exception:
                    pass

        except Exception as e:
            print(f"Error getting goal stats: {e}")

        return stats

    # -------------------------------------------------------------------------
    # Platform stats
    # -------------------------------------------------------------------------
    def _get_platform_stats(self) -> Dict[str, Any]:
        """Get stats from platform plugins (moltx, moltbook, moltchan, moltroad, clawbr)"""
        platforms = ['moltx', 'moltbook', 'moltchan', 'moltroad', 'clawbr']
        stats = {}

        for name in platforms:
            try:
                plugin = self.core.plugin_manager.plugins.get(name)
                if not plugin:
                    stats[name] = {'loaded': False}
                    continue

                pstats: Dict[str, Any] = {'loaded': True, 'initialized': getattr(plugin, 'initialized', False)}

                # Try common stats attributes/methods
                for attr in ['posts', 'followers', 'engagement', 'post_count', 'follower_count', 'engagement_rate']:
                    val = getattr(plugin, attr, None)
                    if val is not None:
                        pstats[attr] = val

                # Try get_stats method
                if hasattr(plugin, 'get_stats') and callable(plugin.get_stats):
                    try:
                        method_stats = plugin.get_stats()
                        if isinstance(method_stats, dict):
                            pstats['details'] = method_stats
                    except Exception:
                        pass

                # Try status method
                if hasattr(plugin, 'status') and callable(plugin.status):
                    try:
                        pstats['status'] = plugin.status()
                    except Exception:
                        pass

                # Try platform-specific attributes
                platform_attrs = {
                    'moltx': ['session_active', 'posts_today', 'mentions', 'total_posts'],
                    'moltbook': ['connections', 'pages', 'recent_activity'],
                    'moltchan': ['threads', 'replies', 'active_threads'],
                    'moltroad': ['deals', 'listings', 'active_listings'],
                    'clawbr': ['debates_active', 'total_debates', 'win_rate', 'elo', 'reputation'],
                }
                for attr in platform_attrs.get(name, []):
                    if attr not in pstats:
                        val = getattr(plugin, attr, None)
                        if val is not None:
                            pstats[attr] = val

                stats[name] = pstats
            except Exception as e:
                stats[name] = {'loaded': False, 'error': str(e)}

        return stats

    # -------------------------------------------------------------------------
    # Chain (onchain) stats
    # -------------------------------------------------------------------------
    def _get_chain_stats(self) -> Dict[str, Any]:
        """Get chain observer statistics"""
        stats = {
            'base_tx_observed': 0,
            'apechain_tx_observed': 0,
            'high_value_txs': 0,
            'wallet_balances': {},
            'top_patterns': [],
        }
        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if not onchain:
                return stats

            # Direct attributes for wallet info
            for attr in ['wallet_balances', 'balances', 'base_balance', 'ape_balance']:
                val = getattr(onchain, attr, None)
                if val is not None:
                    if isinstance(val, dict):
                        stats['wallet_balances'].update(val)
                    else:
                        stats['wallet_balances'][attr] = val

            # Chain observations
            if hasattr(onchain, 'get_chain_observations'):
                obs = onchain.get_chain_observations()
                if isinstance(obs, list):
                    stats['high_value_txs'] = len(obs)
                    base_count = sum(1 for o in obs if o.get('chain') == 'base')
                    ape_count = sum(1 for o in obs if o.get('chain') == 'apechain')
                    stats['base_tx_observed'] = base_count
                    stats['apechain_tx_observed'] = ape_count

            # Get patterns from memory
            try:
                patterns = self.core.get_memory('chain_observer_patterns') or {}
                summary = patterns.get('summary', {})
                for chain_key in ('base', 'apechain'):
                    if chain_key in summary:
                        top = summary[chain_key].get('top_patterns', [])
                        stats['top_patterns'].extend(top)
            except Exception:
                pass

            # Solana wallet balance plugin
            try:
                sol_wallet = self.core.plugin_manager.plugins.get('solana_wallet_balance')
                if sol_wallet:
                    if hasattr(sol_wallet, 'get_balance'):
                        stats['solana_balance'] = sol_wallet.get_balance()
                    if hasattr(sol_wallet, 'get_wallet_info'):
                        stats['solana_wallet'] = sol_wallet.get_wallet_info()
            except Exception:
                pass

        except Exception as e:
            print(f"Error getting chain stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # Skills stats
    # -------------------------------------------------------------------------
    def _get_skills_stats(self) -> Dict[str, Any]:
        """Get skills plugin statistics"""
        stats = {
            'loaded': False,
            'skills_count': 0,
            'tools_count': 0,
            'swarm_nodes': 0,
            'active_skills': 0,
        }
        try:
            skills = self.core.plugin_manager.plugins.get('skills')
            if not skills:
                return stats

            stats['loaded'] = True
            stats['skills_count'] = len(getattr(skills, 'skill_index', {}))
            stats['tools_count'] = len(getattr(skills, 'tool_registry', {}))
            stats['swarm_nodes'] = len(getattr(skills, 'swarm_nodes', {}))

            # Active/loaded skills
            loaded_skills = getattr(skills, 'loaded_skills', {})
            if loaded_skills:
                stats['active_skills'] = len(loaded_skills)
                stats['loaded_skill_names'] = list(loaded_skills.keys())[:20]

            # Skill execution stats
            if hasattr(skills, 'execution_stats'):
                stats['execution'] = skills.execution_stats
            if hasattr(skills, 'get_execution_stats') and callable(skills.get_execution_stats):
                try:
                    stats['execution'] = skills.get_execution_stats()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error getting skills stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # SelfImprove stats
    # -------------------------------------------------------------------------
    def _get_selfimprove_stats(self) -> Dict[str, Any]:
        """Get SelfImprove plugin statistics"""
        stats = {
            'loaded': False,
            'branch': None,
            'active_branches': 0,
            'pending_drafts': 0,
            'skills_discovered': 0,
            'tests_passing': 0,
            'tests_failing': 0,
            'fixes_applied': 0,
        }
        try:
            si = self.core.plugin_manager.plugins.get('selfimprove')
            if not si:
                return stats

            stats['loaded'] = True

            # Branch info
            if hasattr(si, '_current_branch') and callable(si._current_branch):
                stats['branch'] = si._current_branch()
            branch_history = getattr(si, 'branch_history', [])
            if branch_history:
                stats['active_branches'] = len([b for b in branch_history if b.get('status') == 'active'])

            # Drafts
            ac = getattr(si, 'autonomous_coder', None)
            if ac and hasattr(ac, 'get_pending_drafts'):
                drafts = ac.get_pending_drafts()
                stats['pending_drafts'] = len(drafts)

            # Skills
            loaded_skills = getattr(si, 'loaded_skills', {})
            stats['skills_discovered'] = len(loaded_skills)

            # Test results
            test_results = getattr(si, 'test_results_history', [])
            if test_results:
                latest = test_results[-1]
                tests = latest.get('tests', {})
                if isinstance(tests, dict):
                    stats['tests_passing'] = sum(1 for v in tests.values() if v.get('passed'))
                    stats['tests_failing'] = sum(1 for v in tests.values() if not v.get('passed'))
                stats['gate_passed'] = latest.get('gate_passed', False)

            # Fixes
            fix_history = getattr(si, 'fix_history', [])
            stats['fixes_applied'] = len(fix_history)

            # Status command output (if available)
            if hasattr(si, 'status_command') and callable(si.status_command):
                try:
                    stats['status_summary'] = si.status_command()
                except Exception:
                    pass

        except Exception as e:
            print(f"Error getting selfimprove stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # A2A stats
    # -------------------------------------------------------------------------
    def _get_a2a_stats(self) -> Dict[str, Any]:
        """Get A2A plugin statistics"""
        stats = {
            'loaded': False,
            'tasks_executed': 0,
            'tasks_failed': 0,
            'success_rate': 0,
            'recent_tasks': [],
            'security_stats': {},
        }
        try:
            a2a = self.core.plugin_manager.plugins.get('a2a')
            if not a2a:
                return stats

            stats['loaded'] = True

            # Task stats
            if hasattr(a2a, 'get_task_stats') and callable(a2a.get_task_stats):
                try:
                    ts = a2a.get_task_stats()
                    if isinstance(ts, dict):
                        stats.update(ts)
                except Exception:
                    pass

            # Fallback: direct attributes
            if not stats.get('tasks_executed'):
                stats['tasks_executed'] = getattr(a2a, '_tasks_executed', 0)
                stats['tasks_failed'] = getattr(a2a, '_tasks_failed', 0)
                total = stats['tasks_executed'] + stats['tasks_failed']
                if total > 0:
                    stats['success_rate'] = round(stats['tasks_executed'] / total * 100, 1)

            # Task history
            task_history = getattr(a2a, '_task_history', [])
            if task_history:
                stats['recent_tasks'] = task_history[-10:]

            # Security stats
            if hasattr(a2a, 'get_security_stats') and callable(a2a.get_security_stats):
                try:
                    stats['security_stats'] = a2a.get_security_stats()
                except Exception:
                    pass

            # A2A server info
            if hasattr(a2a, 'get_a2a_endpoints') and callable(a2a.get_a2a_endpoints):
                try:
                    stats['endpoints'] = a2a.get_a2a_endpoints()
                except Exception:
                    pass

        except Exception as e:
            print(f"Error getting A2A stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # Memory stats
    # -------------------------------------------------------------------------
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            'sqlite': None,
            'enhanced': None,
            'json_fallback': None,
        }
        try:
            # Memory integration mixin get_memory_stats
            if hasattr(self.core, 'get_memory_stats') and callable(self.core.get_memory_stats):
                try:
                    core_stats = self.core.get_memory_stats()
                    if core_stats:
                        stats.update(core_stats)
                except Exception:
                    pass

            # Direct SQLite memory stats
            if hasattr(self.core, 'memory_db') and self.core.memory_db:
                if hasattr(self.core.memory_db, 'get_memory_stats'):
                    try:
                        stats['sqlite'] = self.core.memory_db.get_memory_stats()
                    except Exception:
                        pass

            # Enhanced memory
            if hasattr(self.core, 'enhanced_memory') and self.core.enhanced_memory:
                if hasattr(self.core.enhanced_memory, 'get_memory_stats'):
                    try:
                        stats['enhanced'] = self.core.enhanced_memory.get_memory_stats()
                    except Exception:
                        pass

            # JSON fallback stats
            memory_dir = Path('memory')
            if memory_dir.exists():
                json_files = list(memory_dir.glob('*.json'))
                stats['json_fallback'] = {
                    'file_count': len(json_files),
                    'files': [f.stem for f in json_files],
                }

        except Exception as e:
            print(f"Error getting memory stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # Plugin stats
    # -------------------------------------------------------------------------
    def _get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin manager overview statistics"""
        stats = {
            'total_plugins': 0,
            'total_tasks': 0,
            'total_commands': 0,
            'plugin_list': [],
        }
        try:
            pm = self.core.plugin_manager
            if pm:
                if hasattr(pm, 'get_stats') and callable(pm.get_stats):
                    try:
                        return pm.get_stats()
                    except Exception:
                        pass
                stats['total_plugins'] = len(pm.plugins) if hasattr(pm, 'plugins') else 0
                stats['total_tasks'] = len(pm.tasks) if hasattr(pm, 'tasks') else 0
                stats['total_commands'] = len(pm.commands) if hasattr(pm, 'commands') else 0
                stats['plugin_list'] = list(pm.plugins.keys()) if hasattr(pm, 'plugins') else []
        except Exception as e:
            print(f"Error getting plugin stats: {e}")
        return stats

    # -------------------------------------------------------------------------
    # System health
    # -------------------------------------------------------------------------
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        stats = {
            'status': 'active',
            'plugins_loaded': 0,
            'actions_per_hour': 0,
            'overall_success_rate': 0,
            'uptime_hours': 0,
        }

        try:
            pm = self.core.plugin_manager
            if pm:
                stats['plugins_loaded'] = len(pm.plugins)

            uptime = time.time() - getattr(self.core, '_start_time', time.time())
            uptime_hours = uptime / 3600
            stats['uptime_hours'] = round(uptime_hours, 2)

            # Calculate actions per hour from brain/agi
            total_actions = 0
            brain = pm.plugins.get('brain') if pm else None
            if brain:
                ab = getattr(brain, '_autonomous_brain', None)
                if ab and hasattr(ab, 'stats'):
                    total_actions += ab.stats.get('actions_taken', 0)

            if uptime_hours > 0 and total_actions > 0:
                stats['actions_per_hour'] = round(total_actions / uptime_hours, 1)

            # Success rate from AGI kernel
            if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                agi = self.core.agi_kernel
                if hasattr(agi, 'action_router') and agi.action_router:
                    ar = agi.action_router
                    if hasattr(ar, 'get_execution_stats') and callable(ar.get_execution_stats):
                        try:
                            exec_stats = ar.get_execution_stats()
                            if isinstance(exec_stats, dict):
                                stats['overall_success_rate'] = round(exec_stats.get('success_rate', 0) * 100, 1)
                        except Exception:
                            pass

        except Exception as e:
            print(f"Error getting system health: {e}")

        return stats

    async def websocket_handler(self, request):
        """WebSocket for live updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)

        try:
            # Send initial chess status
            chess_data = await self.api_chess_status(request)
            if chess_data.status == 200:
                await ws.send_str(json.dumps({
                    "type": "chess_update",
                    "data": chess_data.body
                }))

            # Keep connection alive
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Could handle commands here if needed
                    pass
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.discard(ws)

        return ws

    async def broadcast_chess_update(self, data: Dict[str, Any]):
        """Broadcast chess status update to all connected clients"""
        if not self.websockets:
            return

        message = json.dumps({
            "type": "chess_update",
            "data": data
        })

        # Send to all connected websockets
        await asyncio.gather(
            *[ws.send_str(message) for ws in self.websockets],
            return_exceptions=True
        )

    async def start(self):
        """Start the web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        print(f"🌐 Dashboard server running on http://0.0.0.0:{self.port}")
        return runner


async def main():
    """Start the dashboard server"""
    # Initialize AlleyBot core
    core = AlleyBotCore()
    core._start_time = time.time()

    # Load plugins
    core.plugin_manager.load_all_plugins('plugins')

    # Start dashboard server
    server = DashboardServer(core, port=8080)
    await server.start()

    print("📊 Dashboard available at: http://localhost:8080")
    print("🎮 Live chess status will appear on the dashboard")

    # Keep running
    try:
        while True:
            await asyncio.sleep(10)
            # Could add periodic status broadcasts here
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped")


if __name__ == "__main__":
    asyncio.run(main())
