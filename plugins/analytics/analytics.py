#!/usr/bin/env python3
"""
Analytics Plugin - Dashboard and metrics collection
Handles web dashboard, statistics, and performance monitoring
"""
import sys
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.analytics.platform_aggregator import PlatformStatsAggregator
from plugins.analytics.agent_card import AgentCardGenerator
from plugins.analytics.honeypot_security import honeypot_security

class AnalyticsPlugin(AlleyBotPlugin):
    """Analytics and dashboard plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.app = None
        self.dashboard_port = config.get('dashboard_port', 7001)
        self.refresh_interval = config.get('refresh_interval', 120)
        self.debug_mode = config.get('debug', False)  # Add debug flag
        self.aggregator = None
    
    def initialize(self, api, core):
        super().initialize(api, core)
        self.aggregator = PlatformStatsAggregator(core)
        self.agent_card = AgentCardGenerator(core)
        self._setup_dashboard()
        # Start agent card auto-updater (updates every 24 hours)
        self.agent_card.schedule_auto_update(interval_hours=24)
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
            'wallets': self.show_wallets,
            'agentcard': self.agentcard_status_command,
            'agentcard_update': self.agentcard_update_command,
            'agentcard_dryrun': self.agentcard_dryrun_command,
            'honeypot_stats': self.honeypot_stats_command,
            'honeypot_unblock': self.honeypot_unblock_command,
        }
    
    def get_endpoints(self):
        """Return web endpoints for dashboard"""
        return {
            '/': self.dashboard_index,
            '/api/stats': self.api_stats,
            '/api/metrics': self.api_metrics,
            '/api/activity': self.api_activity,
            '/api/recent_activity': self.api_recent_activity,
            '/api/interactions': self.api_interactions,
            '/api/wallets': self.api_wallets,
            '/api/agent_card': self.api_agent_card,
            '/api/honeypot_stats': self.api_honeypot_stats,
            '/.well-known/agent-card.json': self.api_agent_card,
        }
    
    def _setup_dashboard(self):
        """Setup Flask dashboard"""
        # Set template and static paths to project root
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'img')
        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static/img')
        
        # Add honeypot security middleware
        @self.app.before_request
        def honeypot_middleware():
            """Check all requests for suspicious activity"""
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            path = request.path
            method = request.method
            headers = dict(request.headers)
            
            # Skip honeypot check for static files and legitimate routes
            legitimate_routes = ['/', '/api/', '/static/', '/favicon.ico']
            if any(path.startswith(route) for route in legitimate_routes):
                return None
            
            # Analyze request
            is_blocked, reason = honeypot_security.analyze_request(ip, user_agent, path, method, headers)
            
            if is_blocked:
                return jsonify({"error": "Access denied", "reason": reason}), 403
            
            return None
        
        # Install honeypot trap routes
        honeypot_security.add_honeypot_route(self.app)
        
        # Register endpoints
        for endpoint, func in self.get_endpoints().items():
            self.app.route(endpoint)(func)
    
    def _get_agi_social_stats(self):
        """Collect AGI social behavior stats from brain"""
        data = {
            'users_engaged': 0,
            'users_followed': 0,
            'follows_today': 0,
            'follow_limit_today': 25,
            'follow_mode': 'normal',
            'notification_replies': 0,
            'last_check': None
        }
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain and hasattr(brain, 'get_social_stats'):
                social = brain.get_social_stats()
                data['users_engaged'] = social.get('users_engaged', 0)
                data['users_followed'] = social.get('users_followed', 0)
                data['follows_today'] = social.get('follows_today', 0)
                data['follow_limit_today'] = social.get('follow_limit_today', 25)
                data['follow_mode'] = social.get('follow_mode', 'normal')
                data['notification_replies'] = social.get('notification_replies', 0)
                data['last_check'] = social.get('last_notification_check')
                data['engagement_breakdown'] = social.get('engagement_breakdown', {})
        except Exception as e:
            if self.debug_mode: print(f"[DASHBOARD-DEBUG] AGI social stats error: {e}")
        return data

    def _get_brain_status_detailed(self):
        """Get detailed brain status including mode and recent actions"""
        data = {
            'running': False,
            'mode': 'unknown',
            'cycles': 0,
            'actions_taken': 0,
            'actions_blocked': 0,
            'success_rate': 0,
            'actions_this_hour': 0,
            'max_actions_per_hour': 10,
            'agi_social': self._get_agi_social_stats()
        }
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                if hasattr(brain, 'get_status'):
                    status = brain.get_status()
                    data['running'] = status.get('running', False)
                    data['mode'] = status.get('mode', 'unknown')
                    data['cycles'] = status.get('cycles_completed', 0)
                    data['actions_taken'] = status.get('actions_taken', 0)
                    data['actions_blocked'] = status.get('actions_blocked', 0)
                    data['success_rate'] = status.get('success_rate', 0)
                    data['actions_this_hour'] = status.get('actions_this_hour', 0)
                    data['max_actions_per_hour'] = status.get('max_actions_per_hour', 10)
                    data['uptime'] = status.get('uptime', '0:00:00')
                else:
                    data['running'] = getattr(brain, 'autonomous_running', False)
                    data['cycles'] = getattr(brain, 'cycle_count', 0)
        except Exception as e:
            if self.debug_mode: print(f"[DASHBOARD-DEBUG] Brain status error: {e}")
        return data

    def _get_brain_stats(self):
        """Collect brain plugin stats"""
        data = {
            'brain_cycles': 0,
            'brain_success_rate': 0,
            'brain_available_actions': 0,
            'brain_running': False
        }
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                data['brain_cycles'] = getattr(brain, 'cycle_count', 0)
                data['brain_running'] = getattr(brain, 'autonomous_running', False)
                if hasattr(brain, 'get_available_actions'):
                    data['brain_available_actions'] = len(brain.get_available_actions())
                try:
                    ctx = brain.gather_full_context()
                    eng = ctx.get('engagement', {})
                    data['brain_success_rate'] = round(eng.get('success_rate', 0) * 100)
                except Exception:
                    pass
        except Exception:
            pass
        return data

    def _get_ai_stats(self):
        """Collect AI model usage stats"""
        data = {'deepseek_calls': 0, 'grok_calls': 0, 'total_tokens': 0, 'ai_cost': 0.0}
        try:
            from src.config.models import ModelRouter
            if not hasattr(self, '_model_router'):
                self._model_router = ModelRouter()
            router = self._model_router
            daily = router.token_tracker.get_daily_stats()
            costs = router.token_tracker.get_cost_estimate()
            data['deepseek_calls'] = daily.get('usage', {}).get('deepseek', {}).get('requests', 0)
            data['grok_calls'] = daily.get('usage', {}).get('grok', {}).get('requests', 0)
            data['total_tokens'] = daily.get('total_tokens', 0)
            data['ai_cost'] = round(costs.get('total_daily_cost', 0), 4)
        except Exception:
            pass
        return data

    def _get_onchain_stats(self):
        """Collect on-chain wallet and token data from onchain plugin"""
        data = {'eth_balance': 0.0, 'token_balances': {}, 'connected': False,
                'wallet_address': '', 'network': '', 'tracked_count': 0,
                'tx_history_count': 0, 'last_block': 0}
        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if onchain and onchain.web3_provider and onchain.web3_provider.connected:
                data['connected'] = True
                data['wallet_address'] = onchain.web3_provider.wallet_address or ''
                data['network'] = onchain.web3_provider.network_config.get('name', 'Base')
                data['tracked_count'] = len(getattr(onchain, 'tracked_tokens', {}))
                data['tx_history_count'] = len(getattr(onchain, 'tx_history', []))
                data['last_block'] = getattr(onchain, 'last_seen_block', 0) or 0

                eth_result = onchain.web3_provider.get_eth_balance()
                if eth_result.get('success'):
                    data['eth_balance'] = round(eth_result.get('balance_eth', 0), 6)

                for symbol, token_info in getattr(onchain, 'tracked_tokens', {}).items():
                    result = onchain.web3_provider.get_token_balance(token_info['address'])
                    if result.get('success'):
                        data['token_balances'][symbol] = round(result.get('balance', 0), 4)
        except Exception as e:
            print(f"⚠️  Dashboard onchain stats error: {e}")
        return data

    def _get_a2a_stats(self):
        """Collect A2A protocol stats"""
        data = {'total_tasks': 0, 'completed_tasks': 0, 'active_tasks': 0,
                'failed_tasks': 0, 'server_running': False}
        try:
            a2a = self.core.plugin_manager.plugins.get('a2a')
            if a2a:
                data['server_running'] = True
                if hasattr(a2a, 'tasks'):
                    tasks = a2a.tasks
                    data['total_tasks'] = len(tasks)
                    for t in tasks.values() if isinstance(tasks, dict) else tasks:
                        task = t if isinstance(t, dict) else {}
                        status = task.get('status', {}).get('state', '') if isinstance(task.get('status'), dict) else str(task.get('status', ''))
                        if 'completed' in status.lower():
                            data['completed_tasks'] += 1
                        elif 'failed' in status.lower():
                            data['failed_tasks'] += 1
                        elif status.lower() in ('working', 'submitted'):
                            data['active_tasks'] += 1
        except Exception:
            pass
        return data

    def _get_selfimprove_stats(self):
        """Collect self-improvement plugin stats"""
        data = {'skills_published': 0, 'auto_branches': 0, 'tests_passing': 246,
                'code_validations': 0, 'enabled': False}
        try:
            si = self.core.plugin_manager.plugins.get('selfimprove')
            if si:
                data['enabled'] = True
                if hasattr(si, 'skill_registry'):
                    data['skills_published'] = len(si.skill_registry)
                if hasattr(si, 'validation_count'):
                    data['code_validations'] = si.validation_count
        except Exception:
            pass
        return data

    def _get_skills_stats(self):
        """Collect Phase 14 Agent Skills Framework stats"""
        data = {'skills_loaded': 0, 'skills_active': 0, 'total_executions': 0,
                'top_skills': [], 'unused_skills': [], 'enabled': False}
        try:
            skills = self.core.plugin_manager.plugins.get('skills')
            if skills:
                data['enabled'] = True
                data['skills_loaded'] = len(getattr(skills, 'skill_index', {}))
                data['skills_active'] = len(getattr(skills, 'active_skills', {}))
                
                # Get performance stats if available
                if hasattr(skills, 'usage_stats'):
                    data['total_executions'] = sum(
                        s.get('executions', 0) for s in skills.usage_stats.values()
                    )
                    # Get top skills
                    top = skills.get_top_skills(days=7, limit=3) if hasattr(skills, 'get_top_skills') else []
                    data['top_skills'] = [s['name'] for s in top]
                    # Get unused skills
                    unused = skills.get_unused_skills(days=7) if hasattr(skills, 'get_unused_skills') else []
                    data['unused_skills'] = unused[:3]
        except Exception:
            pass
        return data

    def _get_clawbr_stats(self):
        """Collect Clawbr AI Social Network stats"""
        data = {'posts': 0, 'debates_joined': 0, 'debates_created': 0,
                'elo_score': 0, 'followers': 0, 'enabled': False}
        try:
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            if clawbr:
                data['enabled'] = True
                data['posts'] = getattr(clawbr, 'total_posts', 0)
                data['debates_joined'] = getattr(clawbr, 'debates_joined', 0)
                data['debates_created'] = getattr(clawbr, 'debates_created', 0)
                data['elo_score'] = getattr(clawbr, 'elo_score', 0)
                data['followers'] = getattr(clawbr, 'follower_count', 0)
        except Exception:
            pass
        return data

    def _get_activity_chart_data(self):
        """Build real 7-day activity data from posts across all platforms"""
        from datetime import datetime, timedelta
        days = []
        counts = []
        today = datetime.now().date()
        day_map = {}
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_map[d.isoformat()] = 0
            days.append(d.strftime('%a'))

        # Source 1: Platform-specific post memories (most accurate)
        post_memories = [
            'moltbook_recent_posts',
            'moltx_recent_posts', 
            'moltchan_recent_posts',
            'moltroad_recent_posts',
            'clawbr_recent_debates',
            'clawbr_recent_posts'
        ]
        
        for memory_key in post_memories:
            try:
                posts = self.core.get_memory(memory_key) or []
                for p in posts:
                    ts = p.get('timestamp', '') or p.get('created_at', '')
                    if ts:
                        d = ts[:10]  # YYYY-MM-DD
                        if d in day_map:
                            day_map[d] += 1
            except Exception as e:
                if self.debug_mode: print(f"[DASHBOARD-DEBUG] Error reading {memory_key}: {e}")

        # Source 2: brain action history (as backup for actions taken)
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            history = []
            if brain and hasattr(brain, 'action_history'):
                history = brain.action_history
            if not history:
                history = self.core.get_memory('brain_action_history') or []
            
            for entry in history:
                ts = entry.get('timestamp', '')
                if ts:
                    d = ts[:10]  # YYYY-MM-DD
                    if d in day_map:
                        # Only count successful post actions, not all actions
                        action = entry.get('action', '')
                        success = entry.get('success', False)
                        if success and ('post' in action or 'engage' in action):
                            day_map[d] += 1
        except Exception as e:
            if self.debug_mode: print(f"[DASHBOARD-DEBUG] Error reading brain action history: {e}")

        counts = list(day_map.values())
        if self.debug_mode: print(f"[DASHBOARD-DEBUG] 7-day activity: {days} -> {counts}")
        return days, counts

    def _get_posts_today(self):
        """Count posts created today from memory"""
        from datetime import datetime
        today = datetime.now().date().isoformat()
        count = 0
        try:
            for key in ['moltbook_recent_posts', 'moltx_recent_posts']:
                posts = self.core.get_memory(key) or []
                for p in posts:
                    ts = p.get('timestamp', '')
                    if ts and ts[:10] == today:
                        count += 1
        except Exception:
            pass
        return count

    def _get_recent_activity(self, platform_stats):
        """Get recent activity from brain, memory, or platform stats"""
        recent_activity = []
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain and hasattr(brain, 'action_history') and brain.action_history:
                for entry in reversed(brain.action_history[-20:]):
                    recent_activity.append(self._format_brain_action(entry))
        except Exception:
            pass
        if not recent_activity:
            try:
                history = self.core.get_memory('brain_action_history') or []
                if isinstance(history, list):
                    for entry in reversed(history[-20:]):
                        recent_activity.append(self._format_brain_action(entry))
            except Exception:
                pass
        if not recent_activity:
            for activity in platform_stats.get('recent_activity', [])[:15]:
                recent_activity.append({
                    'platform': activity.get('platform', 'Unknown'),
                    'content': activity.get('title', activity.get('content', ''))[:100],
                    'timestamp': activity.get('timestamp', 'Just now'),
                    'url': activity.get('url', '')
                })
        return recent_activity

    def dashboard_index(self):
        """Main dashboard page - Enhanced V2"""
        try:
            import os
            from datetime import datetime, timedelta
            
            # Get real-time stats from all platforms
            platform_stats = self.aggregator.get_all_stats()
            
            # Extract aggregated data
            total_posts = platform_stats.get('total_posts', 0)
            total_comments = platform_stats.get('total_comments', 0)
            total_followers = platform_stats.get('total_followers', 0)
            total_following = platform_stats.get('total_following', 0)
            
            # Get platform-specific data
            platforms = platform_stats.get('platforms', {})
            moltbook = platforms.get('moltbook', {})
            moltx = platforms.get('moltx', {})
            moltchan = platforms.get('moltchan', {})
            moltroad = platforms.get('moltroad', {})
            
            # Platform-specific stats
            moltx_posts = moltx.get('posts', 0)
            moltx_followers = moltx.get('followers', 0)
            moltbook_posts = moltbook.get('posts', 0)
            moltbook_comments = moltbook.get('comments', 0)
            moltbook_karma = moltbook.get('karma', 0)
            moltchan_posts = moltchan.get('threads', moltchan.get('posts', 0))
            moltchan_replies = moltchan.get('replies', 0)
            moltroad_posts = moltroad.get('posts', 0)
            
            # Calculate metrics
            engagement_rate = round((total_comments / max(total_posts, 1)) * 100, 1) if total_posts > 0 else 0
            posts_today = self._get_posts_today()
            ai_generations = total_posts
            
            # Collect all sub-system stats
            brain_data = self._get_brain_stats()
            ai_data = self._get_ai_stats()
            onchain_data = self._get_onchain_stats()
            a2a_data = self._get_a2a_stats()
            selfimprove_data = self._get_selfimprove_stats()
            skills_data = self._get_skills_stats()
            clawbr_data = self._get_clawbr_stats()
            
            # Recent activity feed
            recent_activity = self._get_recent_activity(platform_stats)
            
            # Activity chart data (real 7-day)
            chart_labels, chart_data = self._get_activity_chart_data()
            
            # Platform distribution for chart
            platform_distribution = [
                moltx_posts,
                moltbook_posts,
                moltchan_posts,
                moltroad_posts
            ]
            
            # Wallet & Identity
            base_wallet = os.getenv('BASE_WALLET_PUBLIC_ADDRESS', os.getenv('BASE_WALLET', '0x...'))
            agent_id = os.getenv('AGENT_ID', 'AlleyBot')
            token_address = os.getenv('ALYBOT_TOKEN_ADDRESS', '0x08a18FE29158B1de5704F99cA396Ad9B2B6a58F3')
            
            # Count active platforms
            active_platforms = sum(1 for p in [moltx_posts, moltbook_posts, moltchan_posts, moltroad_posts] if p > 0)
            # Always count platforms with API keys configured
            for key in ['MOLTX_API_KEY', 'MOLTBOOK_API_KEY', 'MOLTCHAN_API_KEY', 'MOLTROAD_API_KEY']:
                if os.getenv(key):
                    active_platforms = max(active_platforms, 1)
            active_platforms = max(active_platforms, len([k for k in ['MOLTX_API_KEY', 'MOLTBOOK_API_KEY', 'MOLTCHAN_API_KEY', 'MOLTROAD_API_KEY'] if os.getenv(k)]))
            
            return render_template(
                'dashboard_v2.html',
                # Key metrics
                total_posts=total_posts,
                total_comments=total_comments,
                total_followers=total_followers,
                total_following=total_following,
                engagement_rate=engagement_rate,
                posts_today=posts_today,
                ai_generations=ai_generations,
                active_platforms=active_platforms,
                # Platform stats
                moltx_posts=moltx_posts,
                moltx_followers=moltx_followers,
                moltbook_posts=moltbook_posts,
                moltbook_comments=moltbook_comments,
                moltbook_karma=moltbook_karma,
                moltchan_posts=moltchan_posts,
                moltchan_replies=moltchan_replies,
                moltroad_posts=moltroad_posts,
                # AI stats
                deepseek_calls=ai_data['deepseek_calls'],
                grok_calls=ai_data['grok_calls'],
                total_tokens=ai_data['total_tokens'],
                ai_cost=ai_data['ai_cost'],
                # Brain stats
                **brain_data,
                # On-chain stats
                onchain=onchain_data,
                # A2A stats
                a2a=a2a_data,
                # Self-improvement stats
                selfimprove=selfimprove_data,
                # Phase 14 Skills Framework
                skills=skills_data,
                # Clawbr AI Social Network
                clawbr=clawbr_data,
                # Activity data
                recent_activity=recent_activity,
                chart_labels=chart_labels,
                chart_data=chart_data,
                platform_distribution=platform_distribution,
                # Identity & Wallets
                base_wallet=base_wallet,
                agent_id=agent_id,
                token_address=token_address
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Dashboard error: {e}"
    
    def api_agent_card(self):
        """Dynamic ERC-8004 agent card built from loaded plugins"""
        try:
            card = self.agent_card.generate()
            return jsonify(card)
        except Exception as e:
            return jsonify({'error': str(e)})

    def api_stats(self):
        """API endpoint for stats — returns all data needed for auto-refresh"""
        try:
            platform_stats = self.aggregator.get_all_stats()
            platforms = platform_stats.get('platforms', {})
            moltbook = platforms.get('moltbook', {})
            brain_data = self._get_brain_stats()
            ai_data = self._get_ai_stats()
            onchain_data = self._get_onchain_stats()
            a2a_data = self._get_a2a_stats()

            return jsonify({
                'total_posts': platform_stats.get('total_posts', 0),
                'total_comments': platform_stats.get('total_comments', 0),
                'total_followers': platform_stats.get('total_followers', 0),
                'ai_generations': platform_stats.get('total_posts', 0),
                'posts_today': self._get_posts_today(),
                'karma': moltbook.get('karma', 0),
                'platforms': platforms,
                'api_status': 'ok',
                'timestamp': platform_stats.get('timestamp'),
                # Brain detailed status
                'brain': self._get_brain_status_detailed(),
                # Legacy brain fields for compatibility
                **brain_data,
                # AI
                **ai_data,
                # On-chain
                'onchain': onchain_data,
                # A2A
                'a2a': a2a_data,
                # AGI Social
                'agi_social': self._get_agi_social_stats(),
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
        """API endpoint for recent activity feed — pulls from brain action history"""
        try:
            activities = []
            
            # Source 1: Brain action history (primary source)
            try:
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'action_history'):
                    for entry in reversed(brain.action_history[-30:]):
                        activities.append(self._format_brain_action(entry))
            except Exception:
                pass
            
            # Source 2: Persisted action history from memory (if brain not loaded)
            if not activities:
                try:
                    history = self.core.get_memory('brain_action_history') or []
                    if isinstance(history, list):
                        for entry in reversed(history[-30:]):
                            activities.append(self._format_brain_action(entry))
                except Exception:
                    pass
            
            # Source 3: Platform recent posts from aggregator
            if not activities:
                try:
                    platform_stats = self.aggregator.get_all_stats()
                    for item in platform_stats.get('recent_activity', [])[:20]:
                        activities.append({
                            'platform': item.get('platform', 'Unknown'),
                            'content': item.get('title', item.get('content', ''))[:120],
                            'timestamp': item.get('timestamp', ''),
                            'url': item.get('url', ''),
                        })
                except Exception:
                    pass
            
            return jsonify({
                'success': True,
                'activities': activities[:30],
                'total': len(activities),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def _format_brain_action(self, entry):
        """Format a brain action history entry for the dashboard feed"""
        action = entry.get('action', 'unknown')
        platform = entry.get('platform', 'system')
        success = entry.get('success', False)
        output = entry.get('output', '')
        reason = entry.get('reason', '')
        timestamp = entry.get('timestamp', '')
        
        # Build human-readable description
        icon = '✅' if success else '❌'
        action_labels = {
            'moltx_engage': 'Engaged with Moltx feed',
            'moltx_post': 'Created a post on Moltx',
            'moltbook_heartbeat': 'Engaged with MoltBook feed',
            'moltbook_post': 'Created a post on MoltBook',
            'moltchan_engage': 'Engaged on MoltChan',
            'moltroad_engage': 'Engaged on MoltRoad',
            'check_comments': 'Checked and replied to comments',
            'analyze_trending': 'Analyzed trending topics',
            'onchain_heartbeat': 'Monitored on-chain activity',
            'build_skill': 'Generated a new skill',
        }
        label = action_labels.get(action, action.replace('_', ' ').title())
        
        # Use output snippet if available, otherwise reason
        detail = ''
        if output and not output.startswith('Error'):
            detail = output[:120]
        elif reason:
            detail = reason[:120]
        
        content = f"{icon} {label}"
        if detail:
            content += f" — {detail}"
        
        # Format timestamp for display
        display_time = timestamp
        try:
            from datetime import datetime as dt
            ts = dt.fromisoformat(timestamp)
            display_time = ts.strftime('%I:%M %p')
        except Exception:
            pass
        
        return {
            'platform': platform.title() if platform else 'System',
            'content': content,
            'timestamp': display_time,
            'url': '',
        }
    
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
            
            # Test that all required components are available before starting
            print("🔍 Checking dashboard components...")
            
            # Check template directory
            import os
            template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
            if not os.path.exists(template_dir):
                raise Exception(f"Template directory not found: {template_dir}")
            if not os.path.exists(os.path.join(template_dir, 'dashboard_v2.html')):
                raise Exception("Dashboard template 'dashboard_v2.html' not found")
            print("✅ Templates available")
            
            # Check Flask app
            if not self.app:
                raise Exception("Flask app not initialized")
            print("✅ Flask app initialized")
            
            # Check routes
            if not hasattr(self.app, 'url_map') or len(self.app.url_map._rules) == 0:
                raise Exception("No routes registered in Flask app")
            print(f"✅ {len(self.app.url_map._rules)} routes registered")
            
            # Test a simple route to ensure everything works
            print("🔍 Testing dashboard routes...")
            try:
                with self.app.test_client() as client:
                    response = client.get('/')
                    if response.status_code != 200:
                        print(f"⚠️  Route test failed with status {response.status_code}")
                    else:
                        print("✅ Route test passed")
            except Exception as route_error:
                print(f"⚠️  Route test error (may be expected): {route_error}")
            
            print("🚀 Starting Flask development server...")
            
            # Start the server with error handling
            self.app.run(
                debug=False,
                host='0.0.0.0',
                port=self.dashboard_port,
                use_reloader=False,
                threaded=True  # Allow multiple requests
            )
            
        except Exception as e:
            import traceback
            error_msg = f"❌ Dashboard startup failed: {e}"
            print(error_msg)
            print("📋 Full traceback:")
            traceback.print_exc()
            
            # Try to provide helpful debugging info
            print("\n🔍 Debugging information:")
            print(f"  Port: {self.dashboard_port}")
            print(f"  Template dir: {template_dir if 'template_dir' in locals() else 'Not set'}")
            print(f"  Flask app: {'Yes' if self.app else 'No'}")
            
            return error_msg
    
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

    # Agent Card Commands
    def agentcard_status_command(self, *args) -> str:
        """Show current agent card status"""
        try:
            status = self.agent_card.get_agent_card_status()
            
            output = f"🆔 ERC-8004 Agent Card Status\n\n"
            output += f"Agent ID: {status['agent_id']}\n"
            output += f"Name: {status['name']}\n"
            output += f"Version: {status['version']}\n"
            output += f"Skills (OASF): {status['skills_count']}\n"
            output += f"Capabilities: {status['capabilities_count']}\n"
            output += f"Plugins Loaded: {status['plugins_loaded']}\n"
            output += f"Platforms: {', '.join(status['platforms'])}\n"
            output += f"Wallet: {status['wallet'][:20]}...\n"
            output += f"Last Updated: {status['last_updated'][:19] if status['last_updated'] else 'Never'}\n\n"
            output += f"🔗 8004scan.io: {status['registry_url']}\n"
            output += f"🔗 Agent Card JSON: http://localhost:{self.dashboard_port}/.well-known/agent-card.json\n"
            
            return output
        except Exception as e:
            return f"❌ Failed to get agent card status: {e}"

    def agentcard_update_command(self, *args) -> str:
        """Update agent card on-chain at 8004scan.io"""
        try:
            print("🔄 Starting on-chain agent card update...")
            result = self.agent_card.update_onchain(dry_run=False)
            return result
        except Exception as e:
            return f"❌ Failed to update agent card: {e}"

    def agentcard_dryrun_command(self, *args) -> str:
        """Preview agent card update without sending to chain"""
        try:
            result = self.agent_card.update_onchain(dry_run=True)
            return result
        except Exception as e:
            return f"❌ Dry run failed: {e}"
    
    # Honeypot Security Commands
    def honeypot_stats_command(self, *args) -> str:
        """Show honeypot security statistics"""
        try:
            stats = honeypot_security.get_honeypot_stats()
            
            output = f"🎯 **Honeypot Security Stats**\n\n"
            output += f"🚫 **Blocked IPs:** {stats['total_blocked_ips']}\n"
            output += f"🎯 **Total Hits:** {stats['total_hits']}\n"
            output += f"📈 **Last 24h:** {stats['recent_24h_hits']} hits\n\n"
            
            if stats['top_attack_patterns']:
                output += f"🔍 **Top Attack Patterns:**\n"
                for pattern, count in list(stats['top_attack_patterns'].items())[:5]:
                    output += f"  • {pattern}: {count}\n"
                output += "\n"
            
            if stats['most_suspicious_ips']:
                output += f"⚠️ **Most Suspicious IPs:**\n"
                for ip_data in stats['most_suspicious_ips'][:3]:
                    output += f"  • {ip_data['ip']} (Score: {ip_data['score']})\n"
                output += "\n"
            
            if stats['blocked_ips']:
                output += f"🚫 **Currently Blocked:** {', '.join(stats['blocked_ips'][:5])}"
                if len(stats['blocked_ips']) > 5:
                    output += f" and {len(stats['blocked_ips']) - 5} more"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get honeypot stats: {e}"
    
    def honeypot_unblock_command(self, *args) -> str:
        """Unblock an IP address"""
        if not args:
            return "❌ Usage: honeypot_unblock <ip_address>"
        
        ip = args[0]
        try:
            if honeypot_security.unblock_ip(ip):
                return f"✅ Unblocked IP: {ip}"
            else:
                return f"❌ IP {ip} was not blocked"
        except Exception as e:
            return f"❌ Failed to unblock IP: {e}"
    
    def api_honeypot_stats(self):
        """API endpoint for honeypot statistics"""
        try:
            return jsonify(honeypot_security.get_honeypot_stats())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def api_wallets(self):
        """API endpoint for wallet information"""
        try:
            from config import (
                BTC_WALLET, ETH_WALLET, BASE_WALLET, SOL_WALLET
            )
            
            wallets = {
                'btc': BTC_WALLET,
                'eth': ETH_WALLET, 
                'base': BASE_WALLET,
                'sol': SOL_WALLET
            }
            
            return jsonify({
                'success': True,
                'wallets': wallets,
                'note': 'Private keys stored securely in .env file'
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

