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
