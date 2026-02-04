#!/usr/bin/env python3
"""
Analytics Plugin - Dashboard and metrics collection
Handles web dashboard, statistics, and performance monitoring
"""
import sys
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.analytics.platform_aggregator import PlatformStatsAggregator

class AnalyticsPlugin(AlleyBotPlugin):
    """Analytics and dashboard plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.app = None
        self.dashboard_port = config.get('dashboard_port', 7001)
        self.refresh_interval = config.get('refresh_interval', 120)
        self.aggregator = None
    
    def initialize(self, api, core):
        super().initialize(api, core)
        self.aggregator = PlatformStatsAggregator(core)
        self._setup_dashboard()
        print("📊 Analytics system initialized")
    
    def get_tasks(self):
        """Return analytics-related tasks"""
        return {
            'update_metrics': {
                'schedule': '*/5 * * * *',  # Every 5 minutes
                'function': self.update_metrics,
                'description': 'Update performance metrics'
            }
        }
    
    def get_commands(self):
        """Return analytics-related commands"""
        return {
            'dashboard': self.start_dashboard,
            'stats': self.show_stats,
            'metrics': self.show_metrics,
            'analytics': self.analytics_status,
            'wallets': self.show_wallets
        }
    
    def get_endpoints(self):
        """Return web endpoints for dashboard"""
        return {
            '/': self.dashboard_index,
            '/api/stats': self.api_stats,
            '/api/metrics': self.api_metrics,
            '/api/activity': self.api_activity,
            '/api/recent_activity': self.api_recent_activity,
            '/api/interactions': self.api_interactions
        }
    
    def _setup_dashboard(self):
        """Setup Flask dashboard"""
        # Set template path to project root
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        
        # Register endpoints
        for endpoint, func in self.get_endpoints().items():
            self.app.route(endpoint)(func)
    
    def dashboard_index(self):
        """Main dashboard page - Enhanced V2"""
        try:
            import os
            from datetime import datetime, timedelta
            
            # Get real-time stats from all platforms
            print("📊 Fetching live stats from all platforms...")
            platform_stats = self.aggregator.get_all_stats()
            
            # Extract aggregated data
            total_posts = platform_stats.get('total_posts', 0)
            total_comments = platform_stats.get('total_comments', 0)
            total_followers = platform_stats.get('total_followers', 0)
            
            # Get platform-specific data
            platforms = platform_stats.get('platforms', {})
            moltbook = platforms.get('moltbook', {})
            moltx = platforms.get('moltx', {})
            moltchan = platforms.get('moltchan', {})
            moltroad = platforms.get('moltroad', {})
            clawtasks = platforms.get('clawtasks', {})
            fourclaw = platforms.get('fourclaw', {})
            
            # Platform-specific stats
            moltx_posts = moltx.get('posts', 0)
            moltx_followers = moltx.get('followers', 0)
            moltbook_posts = moltbook.get('posts', 0)
            moltbook_comments = moltbook.get('comments', 0)
            moltchan_posts = moltchan.get('posts', 0)
            moltroad_posts = moltroad.get('posts', 0)
            clawtasks_tasks = clawtasks.get('tasks_completed', 0)
            fourclaw_threads = fourclaw.get('threads', 0)
            
            # Calculate metrics
            engagement_rate = round((total_comments / max(total_posts, 1)) * 100, 1) if total_posts > 0 else 0
            posts_today = 5  # TODO: Track daily posts
            ai_generations = total_posts  # All posts are AI-generated
            
            # Get recent activity
            recent_activity = []
            for activity in platform_stats.get('recent_activity', [])[:15]:
                recent_activity.append({
                    'platform': activity.get('platform', 'Unknown'),
                    'content': activity.get('title', activity.get('content', ''))[:100],
                    'timestamp': activity.get('timestamp', 'Just now'),
                    'url': activity.get('url', '')
                })
            
            # AI Model Stats (mock data - would need tracking)
            deepseek_calls = 150
            grok_calls = 45
            total_tokens = 250000
            ai_cost = 2.45
            
            # Activity data for chart (last 7 days)
            activity_data = [12, 15, 18, 14, 20, 16, 19]
            
            # Platform distribution for chart
            platform_distribution = [
                moltx_posts,
                moltbook_posts,
                moltchan_posts,
                fourclaw_threads,
                moltroad_posts + clawtasks_tasks
            ]
            
            # Wallet & Identity
            base_wallet = os.getenv('BASE_WALLET', '0x...')
            agent_id = os.getenv('AGENT_ID', 'AlleyBot')
            token_address = os.getenv('TOKEN_ADDRESS', '0x...')
            
            print(f"✅ Dashboard V2 loaded: {total_posts} posts, {total_comments} comments, {total_followers} followers")
            
            # Use the new powerful dashboard template
            return render_template(
                'dashboard_v2.html',
                # Key metrics
                total_posts=total_posts,
                total_comments=total_comments,
                total_followers=total_followers,
                engagement_rate=engagement_rate,
                posts_today=posts_today,
                ai_generations=ai_generations,
                # Platform stats
                moltx_posts=moltx_posts,
                moltx_followers=moltx_followers,
                moltbook_posts=moltbook_posts,
                moltbook_comments=moltbook_comments,
                moltchan_posts=moltchan_posts,
                moltroad_posts=moltroad_posts,
                clawtasks_tasks=clawtasks_tasks,
                fourclaw_threads=fourclaw_threads,
                # AI stats
                deepseek_calls=deepseek_calls,
                grok_calls=grok_calls,
                total_tokens=total_tokens,
                ai_cost=ai_cost,
                # Activity data
                recent_activity=recent_activity,
                activity_data=activity_data,
                platform_distribution=platform_distribution,
                # Identity
                base_wallet=base_wallet,
                agent_id=agent_id,
                token_address=token_address
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Dashboard error: {e}"
    
    def api_stats(self):
        """API endpoint for stats"""
        try:
            # Get real-time stats from all platforms
            platform_stats = self.aggregator.get_all_stats()
            
            platforms = platform_stats.get('platforms', {})
            moltbook = platforms.get('moltbook', {})
            
            return jsonify({
                'posts': platform_stats.get('total_posts', 0),
                'comments': platform_stats.get('total_comments', 0),
                'upvotes': 0,  # TODO: Aggregate upvotes
                'karma': moltbook.get('karma', 0),
                'followers': platform_stats.get('total_followers', 0),
                'following': platform_stats.get('total_following', 0),
                'donations': 0,  # TODO: Track donations
                'platforms': platforms,
                'api_status': 'ok',
                'timestamp': platform_stats.get('timestamp')
            })
            
        except Exception as e:
            return jsonify({'error': str(e), 'api_status': 'error'})
    
    def api_metrics(self):
        """API endpoint for detailed metrics"""
        try:
            # Get plugin stats
            plugin_stats = {}
            for plugin_name, plugin in self.core.plugin_manager.plugins.items():
                if hasattr(plugin, 'get_stats'):
                    plugin_stats[plugin_name] = plugin.get_stats()
            
            # Get system stats
            state = self.core.get_memory('state') or {}
            interactions = self.core.get_memory('interactions') or []
            
            return jsonify({
                'plugin_stats': plugin_stats,
                'total_interactions': len(interactions),
                'uptime': state.get('uptime', 0),
                'memory_usage': self._get_memory_usage(),
                'timestamp': self._get_timestamp()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)})
    
    def api_activity(self):
        """API endpoint for activity timeline"""
        try:
            interactions = self.core.get_memory('interactions') or []
            
            # Group by date
            activity_by_date = {}
            for interaction in interactions:
                timestamp = interaction.get('timestamp', '')
                date = timestamp.split('T')[0] if 'T' in timestamp else 'unknown'
                
                if date not in activity_by_date:
                    activity_by_date[date] = {'posts': 0, 'comments': 0, 'upvotes': 0}
                
                itype = interaction.get('type', '')
                if itype == 'post':
                    activity_by_date[date]['posts'] += 1
                elif itype == 'comment':
                    activity_by_date[date]['comments'] += 1
                elif itype == 'upvote':
                    activity_by_date[date]['upvotes'] += 1
            
            return jsonify({'success': True, 'activity': activity_by_date})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def api_recent_activity(self):
        """API endpoint for recent activity feed"""
        try:
            # Try to get activity logger from event runner
            activity_data = []
            stats = {}
            
            if hasattr(self.core, 'event_runner') and hasattr(self.core.event_runner, 'activity_logger'):
                activity_logger = self.core.event_runner.activity_logger
                activity_data = activity_logger.get_recent_activities(limit=100)
                stats = activity_logger.get_stats()
            
            return jsonify({
                'success': True,
                'activities': activity_data,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def api_interactions(self):
        """API endpoint for recent interactions from all platforms"""
        try:
            # Get real-time stats from all platforms
            platform_stats = self.aggregator.get_all_stats()
            
            # Get recent activity
            recent_activity = platform_stats.get('recent_activity', [])
            
            # Format for dashboard
            interactions = []
            for activity in recent_activity[:50]:
                interaction = {
                    'type': activity.get('type', 'post'),
                    'platform': activity.get('platform', 'Unknown'),
                    'timestamp': activity.get('timestamp', ''),
                    'details': {
                        'post_id': activity.get('url', '').split('/')[-1] if activity.get('url') else None,
                        'post_title': activity.get('title', activity.get('content', ''))[:100],
                        'url': activity.get('url', ''),
                        'upvotes': activity.get('upvotes', activity.get('likes', 0)),
                        'comments': activity.get('comments', activity.get('replies', 0))
                    }
                }
                interactions.append(interaction)
            
            return jsonify({
                'success': True,
                'interactions': interactions,
                'total': len(interactions),
                'timestamp': platform_stats.get('timestamp')
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def start_dashboard(self):
        """Start the dashboard server"""
        try:
            print(f"� Starting analytics dashboard on port {self.dashboard_port}...")
            print(f"📊 Dashboard available at: http://localhost:{self.dashboard_port}")
            print(f"📊 Dashboard available at: http://0.0.0.0:{self.dashboard_port}")
            
            self.app.run(
                debug=False,
                host='0.0.0.0',
                port=self.dashboard_port,
                use_reloader=False
            )
            
        except Exception as e:
            return f"❌ Failed to start dashboard: {e}"
    
    def show_stats(self):
        """Show current statistics"""
        try:
            state = self.core.get_memory('state') or {}
            interactions = self.core.get_memory('interactions') or []
            
            output = "📊 Current Statistics:\n"
            output += f"  Posts: {state.get('totalPosts', 0)}\n"
            output += f"  Comments: {state.get('totalComments', 0)}\n"
            output += f"  Upvotes: {state.get('totalUpvotes', 0)}\n"
            output += f"  Total Interactions: {len(interactions)}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get stats: {e}"
    
    def show_metrics(self):
        """Show detailed metrics"""
        try:
            output = "📈 Detailed Metrics:\n"
            
            # Plugin metrics
            for plugin_name, plugin in self.core.plugin_manager.plugins.items():
                if hasattr(plugin, 'get_stats'):
                    stats = plugin.get_stats()
                    output += f"  {plugin_name}:\n"
                    for key, value in stats.items():
                        output += f"    {key}: {value}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get metrics: {e}"
    
    def analytics_status(self):
        """Show analytics system status"""
        try:
            output = "📊 Analytics Systems Status:\n"
            output += f"  Dashboard: {'✅' if self.app else '❌'}\n"
            output += f"  Port: {self.dashboard_port}\n"
            output += f"  Refresh Interval: {self.refresh_interval}s\n"
            output += f"  Plugins with stats: {len([p for p in self.core.plugin_manager.plugins.values() if hasattr(p, 'get_stats')])}\n"
            return output
            
        except Exception as e:
            return f"❌ Failed to get analytics status: {e}"
    
    def update_metrics(self):
        """Update performance metrics"""
        try:
            # Update system metrics
            state = self.core.get_memory('state') or {}
            state['uptime'] = state.get('uptime', 0) + 300  # 5 minutes
            state['last_metrics_update'] = self._get_timestamp()
            
            self.core.save_memory('state', state)
            
        except Exception as e:
            print(f"❌ Metrics update failed: {e}")
    
    def _get_dashboard_html(self):
        """Get dashboard HTML template"""
        # Simplified dashboard HTML (would normally be in templates folder)
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>AlleyBot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .content { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🦞 AlleyBot Dashboard</h1>
        <p>Real-time monitoring of AlleyBot's activity</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{{ total_posts }}</div>
            <div>Posts Created</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ total_comments }}</div>
            <div>Comments Made</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ total_upvotes }}</div>
            <div>Upvotes Given</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ karma }}</div>
            <div>Karma</div>
        </div>
    </div>
    
    <div class="content">
        <div class="card">
            <h2>Recent Activity</h2>
            {% for interaction in recent_interactions %}
            <div style="padding: 10px; border-left: 4px solid #667eea; margin-bottom: 10px;">
                <strong>{{ interaction.type }}</strong><br>
                {{ interaction.details }}<br>
                <small>{{ interaction.timestamp }}</small>
            </div>
            {% endfor %}
        </div>
        
        <div class="card">
            <h2>System Status</h2>
            <p>Agent: {{ agent.name or 'AlleyBot' }}</p>
            <p>Followers: {{ followers }}</p>
            <p>Following: {{ following }}</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 2 minutes
        setInterval(() => {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => console.log('Stats updated:', data));
        }, 120000);
    </script>
</body>
</html>
        '''
    
    def _get_memory_usage(self):
        """Get memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'rss': process.memory_info().rss,
                'vms': process.memory_info().vms,
                'percent': process.memory_percent()
            }
        except:
            return {'error': 'psutil not available'}
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def show_wallets(self):
        """Show wallet information"""
        try:
            from config import (
                BTC_WALLET, ETH_WALLET, BASE_WALLET, SOL_WALLET
            )
            
            output = "💰 AlleyBot's Wallets:\n\n"
            output += f"🟠 Bitcoin (BTC):\n  {BTC_WALLET}\n\n"
            output += f"🔷 Ethereum (ETH):\n  {ETH_WALLET}\n\n"
            output += f"🔵 Base L2:\n  {BASE_WALLET}\n\n"
            output += f"🟣 Solana (SOL):\n  {SOL_WALLET}\n\n"
            output += "⚠️  Private keys stored securely in .env file"
            
            return output
        except Exception as e:
            return f"❌ Failed to show wallets: {e}"
    
    def cleanup(self):
        """Cleanup analytics systems"""
        pass


# Helper function for render_template_string
from flask import render_template_string
