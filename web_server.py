#!/usr/bin/env python3
"""
AlleyBot Web Dashboard Server
Serves the dashboard with live chess status and system metrics.
"""
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

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
        self.app.router.add_get("/api/chess", self.api_chess_status)
        self.app.router.add_get("/api/debates", self.api_debate_status)
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
            status = {
                "timestamp": time.time(),
                "uptime": time.time() - getattr(self.core, '_start_time', time.time()),
                "plugins": list(self.core.plugin_manager.plugins.keys()) if self.core.plugin_manager else [],
                "memory": "SQLite" if hasattr(self.core, 'memory_db') else "JSON"
            }
            return web.json_response(status)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

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

    async def api_stats(self, request):
        """Comprehensive stats from all AlleyBot systems"""
        try:
            stats = {
                'timestamp': time.time(),
                'uptime': time.time() - getattr(self.core, '_start_time', time.time()),
                'agi_kernel': self._get_agi_kernel_stats(),
                'skills': self._get_skill_stats(),
                'a2a': self._get_a2a_stats(),
                'platforms': self._get_platform_stats(),
                'memory': self._get_memory_stats(),
                'goals': self._get_goal_stats(),
                'system': self._get_system_health(),
            }
            return web.json_response(stats)
        except Exception as e:
            print(f"Stats API error: {e}")
            import traceback
            traceback.print_exc()
            return web.json_response({"error": str(e)}, status=500)

    def _get_agi_kernel_stats(self) -> Dict[str, Any]:
        """Get AGI Kernel statistics"""
        stats = {
            'cycles_run': 0,
            'decisions_made': 0,
            'actions_executed': 0,
            'success_rate': 0,
            'errors_detected': 0,
            'errors_fixed': 0,
            'contexts_gathered': 0,
            'replies_generated': 0,
        }
        
        try:
            if hasattr(self.core, 'agi_kernel'):
                agi = self.core.agi_kernel
                
                # Decision system stats
                if hasattr(agi, 'decision_system') and agi.decision_system:
                    ds = agi.decision_system
                    stats['decisions_made'] = getattr(ds, 'decisions_made', 0)
                    stats['success_rate'] = getattr(ds, 'success_rate', 0)
                
                # Action router stats
                if hasattr(agi, 'action_router') and agi.action_router:
                    ar = agi.action_router
                    stats['actions_executed'] = getattr(ar, 'actions_executed', 0)
                
                # Error monitor stats
                if hasattr(agi, 'error_monitor') and agi.error_monitor:
                    em = agi.error_monitor
                    stats['errors_detected'] = getattr(em, 'errors_detected', 0)
                    stats['errors_fixed'] = getattr(em, 'errors_fixed', 0)
                
                # Context system stats
                if hasattr(agi, 'context_system') and agi.context_system:
                    cs = agi.context_system
                    stats['contexts_gathered'] = getattr(cs, 'contexts_gathered', 0)
                
                # Reply system stats
                if hasattr(agi, 'reply_system') and agi.reply_system:
                    rs = agi.reply_system
                    stats['replies_generated'] = getattr(rs, 'replies_generated', 0)
        
        except Exception as e:
            print(f"Error getting AGI kernel stats: {e}")
        
        return stats

    def _get_skill_stats(self) -> Dict[str, Any]:
        """Get skill discovery statistics"""
        stats = {
            'total_skills': 0,
            'oasf_skills': 0,
            'a2a_skills': 0,
            'discovered_skills': 0,
            'skills_by_category': {},
        }
        
        try:
            # Try to get from analytics plugin
            analytics = self.core.plugin_manager.plugins.get('analytics')
            if analytics and hasattr(analytics, 'agent_card_generator'):
                gen = analytics.agent_card_generator
                
                # Get agent card
                card = gen.generate()
                
                # Count OASF skills
                if 'services' in card and len(card['services']) > 0:
                    oasf_service = card['services'][0]
                    stats['oasf_skills'] = len(oasf_service.get('skills', []))
                
                # Count A2A skills
                if 'services' in card and len(card['services']) > 1:
                    a2a_service = card['services'][1]
                    stats['a2a_skills'] = len(a2a_service.get('a2aSkills', []))
                
                # Get discovered skills from skill scanner
                if hasattr(gen, 'skill_scanner'):
                    scanner = gen.skill_scanner
                    discovered = scanner.scan_skills()
                    stats['discovered_skills'] = len(discovered)
                    
                    # Count by category
                    for skill in discovered:
                        category = skill.get('category', 'unknown')
                        stats['skills_by_category'][category] = stats['skills_by_category'].get(category, 0) + 1
                
                stats['total_skills'] = stats['oasf_skills'] + stats['a2a_skills']
        
        except Exception as e:
            print(f"Error getting skill stats: {e}")
        
        return stats

    def _get_a2a_stats(self) -> Dict[str, Any]:
        """Get A2A protocol statistics"""
        stats = {
            'agent_id': 22899,
            'tasks_available': 0,
            'tasks_completed': 0,
            'revenue_generated': 0,
            'attestations_created': 0,
            'agent_card_status': 'unknown',
        }
        
        try:
            a2a = self.core.plugin_manager.plugins.get('a2a')
            if a2a:
                # Get available tasks
                if hasattr(a2a, 'list_available_tasks'):
                    tasks = a2a.list_available_tasks()
                    stats['tasks_available'] = len(tasks)
                
                # Get agent card status
                stats['agent_card_status'] = 'active'
            
            # Get attestations
            try:
                import json
                from pathlib import Path
                registry_path = Path(__file__).parent / 'data' / 'erc8004_registry.json'
                if registry_path.exists():
                    with open(registry_path, 'r') as f:
                        attestations = json.load(f)
                        stats['attestations_created'] = len(attestations)
            except Exception as e:
                print(f"Error loading attestations: {e}")
        
        except Exception as e:
            print(f"Error getting A2A stats: {e}")
        
        return stats

    def _get_platform_stats(self) -> Dict[str, Any]:
        """Get platform activity statistics"""
        stats = {
            'moltx': {'posts': 0, 'engagement': 0},
            'clawbr': {'debates': 0, 'elo': 0},
            'moltroad': {'activity': 0},
            'clawchess': {'games': 0, 'rating': 0},
        }
        
        try:
            # MoltX stats
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if moltx:
                # Try to get post count from memory
                moltx_stats = self.core.get_memory('moltx_stats') or {}
                stats['moltx']['posts'] = moltx_stats.get('total_posts', 0)
                stats['moltx']['engagement'] = moltx_stats.get('total_engagement', 0)
            
            # Clawbr stats
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            if clawbr:
                my_debates = clawbr.get_my_debates()
                if my_debates.get('success'):
                    stats['clawbr']['debates'] = len(my_debates.get('debates', []))
            
            # ClawChess stats
            clawchess = self.core.plugin_manager.plugins.get('clawchess')
            if clawchess:
                chess_status = clawchess.get_chess_status()
                stats['clawchess']['rating'] = chess_status.get('elo', 0)
                stats['clawchess']['games'] = chess_status.get('games_played', 0)
        
        except Exception as e:
            print(f"Error getting platform stats: {e}")
        
        return stats

    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory and learning statistics"""
        stats = {
            'total_memories': 0,
            'episodic_memories': 0,
            'world_facts': 0,
            'learning_events': 0,
        }
        
        try:
            if hasattr(self.core, 'agi_kernel'):
                agi = self.core.agi_kernel
                
                # Unified memory stats
                if hasattr(agi, 'unified_memory'):
                    um = agi.unified_memory
                    # Try to count memories
                    if hasattr(um, 'count'):
                        stats['total_memories'] = um.count()
                
                # Episodic memory stats
                if hasattr(agi, 'episodic_memory'):
                    em = agi.episodic_memory
                    if hasattr(em, 'count'):
                        stats['episodic_memories'] = em.count()
                    elif hasattr(em, 'memories'):
                        stats['episodic_memories'] = len(em.memories)
        
        except Exception as e:
            print(f"Error getting memory stats: {e}")
        
        return stats

    def _get_goal_stats(self) -> Dict[str, Any]:
        """Get autonomous goal statistics"""
        stats = {
            'goals_generated': 0,
            'goals_active': 0,
            'goals_completed': 0,
            'goal_success_rate': 0,
        }
        
        try:
            if hasattr(self.core, 'agi_kernel') and hasattr(self.core.agi_kernel, 'goal_generator'):
                gg = self.core.agi_kernel.goal_generator
                
                # Try to get goal stats
                stats['goals_generated'] = getattr(gg, 'goals_generated', 0)
                stats['goals_active'] = getattr(gg, 'goals_active', 0)
                stats['goals_completed'] = getattr(gg, 'goals_completed', 0)
                
                if stats['goals_generated'] > 0:
                    stats['goal_success_rate'] = int((stats['goals_completed'] / stats['goals_generated']) * 100)
        
        except Exception as e:
            print(f"Error getting goal stats: {e}")
        
        return stats

    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        stats = {
            'status': 'active',
            'plugins_loaded': 0,
            'actions_per_hour': 0,
            'overall_success_rate': 0,
        }
        
        try:
            if self.core.plugin_manager:
                stats['plugins_loaded'] = len(self.core.plugin_manager.plugins)
            
            # Calculate actions per hour from uptime and total actions
            uptime_hours = (time.time() - getattr(self.core, '_start_time', time.time())) / 3600
            if uptime_hours > 0:
                total_actions = 0
                if hasattr(self.core, 'agi_kernel') and hasattr(self.core.agi_kernel, 'action_router'):
                    total_actions = getattr(self.core.agi_kernel.action_router, 'actions_executed', 0)
                stats['actions_per_hour'] = int(total_actions / uptime_hours)
        
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
