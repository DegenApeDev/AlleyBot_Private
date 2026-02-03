#!/usr/bin/env python3
"""
Analytics Plugin - Dashboard and metrics collection
Handles web dashboard, statistics, and performance monitoring
"""
import sys
import os
import json
from flask import Flask, render_template, jsonify
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin

class AnalyticsPlugin(AlleyBotPlugin):
    """Analytics and dashboard plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.app = None
        self.dashboard_port = config.get('dashboard_port', 7001)
        self.refresh_interval = config.get('refresh_interval', 120)
    
    def initialize(self, api, core):
        super().initialize(api, core)
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
            '/api/recent_activity': self.api_recent_activity
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
        """Main dashboard page"""
        try:
            # Load data from memory
            state = self.core.get_memory('state') or {}
            interactions = self.core.get_memory('interactions') or []
            objectives = self.core.get_memory('objectives') or {}
            
            # Get profile data
            try:
                profile = self.api.get_public_profile(name="AlleyBot")
                agent = profile.get('agent', {})
                recent_posts = profile.get('recentPosts', [])
                print(f"✅ Profile API working: {len(recent_posts)} posts found")
            except Exception as e:
                print(f"⚠️  Profile API down (server overload): {e}")
                print("📊 Using fallback data from memory...")
                agent = {
                    'name': 'AlleyBot',
                    'karma': state.get('karma', 0),
                    'follower_count': state.get('followers', 0),
                    'following_count': state.get('following_count', 0)
                }
                recent_posts = []
            
            # Calculate multi-platform stats
            total_posts = state.get('totalPosts', 0)
            total_comments = state.get('totalComments', 0)
            total_upvotes = state.get('totalUpvotes', 0)
            karma = agent.get('karma', 0)
            followers = agent.get('follower_count', 0)
            following = agent.get('following_count', 0)
            
            # New v0.13.0 metrics
            ai_enhanced_posts = state.get('aiEnhancedPosts', 0)
            platforms_active = state.get('platformsActive', 5)
            earnings_usdc = state.get('earningsUSDC', 0)
            conversations_count = state.get('conversationsCount', 0)
            groups_count = state.get('groupsCount', 0)
            engagement_rate = state.get('engagementRate', 0)
            autonomous_tasks = state.get('autonomousTasks', 14)
            claim_status = state.get('claimStatus', 'claimed')
            
            # Get recent interactions
            recent_interactions = interactions[-20:] if interactions else []
            recent_interactions.reverse()
            
            # Use the enhanced dashboard template
            return render_template(
                'dashboard.html',
                agent=agent,
                total_posts=total_posts,
                total_comments=total_comments,
                total_upvotes=total_upvotes,
                karma=karma,
                followers=followers,
                following=following,
                recent_interactions=recent_interactions,
                recent_posts=recent_posts,
                objectives=objectives,
                ai_enhanced_posts=ai_enhanced_posts,
                platforms_active=platforms_active,
                earnings_usdc=earnings_usdc,
                conversations_count=conversations_count,
                groups_count=groups_count,
                engagement_rate=engagement_rate,
                autonomous_tasks=autonomous_tasks,
                claim_status=claim_status
            )
            
        except Exception as e:
            return f"Dashboard error: {e}"
    
    def api_stats(self):
        """API endpoint for stats"""
        try:
            state = self.core.get_memory('state') or {}
            
            try:
                profile = self.api.get_public_profile(name="AlleyBot")
                agent = profile.get('agent', {})
                print(f"✅ Stats API: Profile retrieved successfully")
            except Exception as e:
                print(f"⚠️  Stats API: Profile endpoint down ({e})")
                print("📊 Using cached profile data...")
                # Use fallback data
                agent = {
                    'karma': state.get('karma', 0),
                    'follower_count': state.get('followers', 0),
                    'following_count': state.get('following_count', 0)
                }
            
            return jsonify({
                'posts': state.get('totalPosts', 0),
                'comments': state.get('totalComments', 0),
                'upvotes': state.get('totalUpvotes', 0),
                'karma': agent.get('karma', 0),
                'followers': agent.get('follower_count', 0),
                'following': agent.get('following_count', 0),
                'donations': state.get('totalDonationsReceived', 0),
                'api_status': 'ok' if agent else 'error'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)})
    
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
    
    def start_dashboard(self):
        """Start the dashboard server"""
        try:
            print(f"🚀 Starting analytics dashboard on port {self.dashboard_port}...")
            print(f"📊 Dashboard will be available at: http://localhost:{self.dashboard_port}")
            print("💡 Press Ctrl+C to stop the dashboard\n")
            
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
