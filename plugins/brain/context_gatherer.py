"""
Context Gatherer Mixin
Collects all available context for the autonomous brain to reason about.
Pulls from memory, on-chain state, platform activity, and engagement history.
"""
import os
import datetime
from typing import Dict, Any, Optional, List


class ContextGathererMixin:
    """Mixin that gathers context from all available sources"""

    def _init_context_gatherer(self):
        """Initialize context gathering state"""
        self.context_cache: Dict[str, Any] = {}
        self.cache_ttl = 120  # seconds
        self.last_context_time: Optional[datetime.datetime] = None

    def gather_full_context(self) -> Dict[str, Any]:
        """Gather context from ALL available sources for decision-making"""
        now = datetime.datetime.now()

        # Use cache if fresh enough
        if (self.last_context_time and
                (now - self.last_context_time).total_seconds() < self.cache_ttl and
                self.context_cache):
            return self.context_cache

        context = {
            'timestamp': now.isoformat(),
            'memory': self._gather_memory_context(),
            'onchain': self._gather_onchain_context(),
            'platforms': self._gather_platform_context(),
            'engagement': self._gather_engagement_context(),
            'goals': self._gather_goal_context(),
            'recent_actions': self._gather_recent_actions(),
        }

        self.context_cache = context
        self.last_context_time = now
        return context

    def _gather_memory_context(self) -> Dict[str, Any]:
        """Pull relevant context from enhanced memory"""
        try:
            if not hasattr(self.core, 'enhanced_memory') or not self.core.enhanced_memory:
                return {'available': False}

            mem = self.core.enhanced_memory
            stats = mem.get_memory_stats() if hasattr(mem, 'get_memory_stats') else {}

            # Get recent memories
            recent = []
            if hasattr(mem, 'semantic_search'):
                results = mem.semantic_search('recent activity engagement', top_k=5)
                recent = [{'content': r.get('content', ''), 'type': r.get('type', '')} for r in results]

            return {
                'available': True,
                'stats': stats,
                'recent_memories': recent,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _gather_onchain_context(self) -> Dict[str, Any]:
        """Pull on-chain state from onchain plugin"""
        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if not onchain or not onchain.web3_provider or not onchain.web3_provider.connected:
                return {'available': False}

            provider = onchain.web3_provider
            eth_result = provider.get_eth_balance()
            block_info = provider.get_block_info()

            token_balances = {}
            for symbol, token_info in onchain.tracked_tokens.items():
                result = provider.get_token_balance(token_info['address'])
                if result['success']:
                    token_balances[symbol] = result['balance']

            # Check for balance changes
            changes = onchain.check_balance_changes() if hasattr(onchain, 'check_balance_changes') else None

            return {
                'available': True,
                'wallet': provider.wallet_address,
                'eth_balance': eth_result.get('balance_eth', 0) if eth_result.get('success') else 0,
                'token_balances': token_balances,
                'block_number': block_info.get('block_number', 0) if block_info.get('success') else 0,
                'gas_price_gwei': block_info.get('gas_price_gwei', 0) if block_info.get('success') else 0,
                'recent_changes': changes,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _gather_platform_context(self) -> Dict[str, Any]:
        """Pull activity state from all social platforms"""
        platforms = {}
        plugin_map = {
            'moltx': 'Moltx',
            'moltbook': 'Moltbook',
            'moltchan': 'MoltChan',
            'moltroad': 'MoltRoad',
        }

        for plugin_name, display_name in plugin_map.items():
            try:
                plugin = self.core.plugin_manager.plugins.get(plugin_name)
                if not plugin:
                    platforms[plugin_name] = {'loaded': False}
                    continue

                info = {
                    'loaded': True,
                    'has_heartbeat': hasattr(plugin, 'moltx_heartbeat') or hasattr(plugin, 'moltbook_heartbeat'),
                    'has_feed': hasattr(plugin, 'feed_command'),
                    'has_engage': hasattr(plugin, 'engage_feed_command'),
                    'has_post': hasattr(plugin, 'create_post') or hasattr(plugin, 'create_post_command'),
                }

                # Get last heartbeat time from memory
                last_hb = self.core.get_memory(f'{plugin_name}_last_heartbeat')
                info['last_heartbeat'] = last_hb

                platforms[plugin_name] = info

            except Exception as e:
                platforms[plugin_name] = {'loaded': False, 'error': str(e)}

        return platforms

    def _gather_engagement_context(self) -> Dict[str, Any]:
        """Pull engagement history and performance data"""
        try:
            # Get engagement stats from memory
            engagement_log = self.core.get_memory('brain_engagement_log') or []
            if not isinstance(engagement_log, list):
                engagement_log = []

            # Calculate recent performance
            recent = engagement_log[-20:] if engagement_log else []
            total = len(recent)
            successes = sum(1 for e in recent if e.get('success'))

            # Get best performing content types
            content_types = {}
            for entry in recent:
                ct = entry.get('action_type', 'unknown')
                if ct not in content_types:
                    content_types[ct] = {'count': 0, 'successes': 0}
                content_types[ct]['count'] += 1
                if entry.get('success'):
                    content_types[ct]['successes'] += 1

            # Get post engagement feedback from feedback loop
            post_feedback = {}
            try:
                style_scores = self.core.get_memory('feedback_style_scores') or {}
                if style_scores:
                    sorted_styles = sorted(
                        style_scores.items(),
                        key=lambda x: x[1].get('avg_score', 0),
                        reverse=True
                    )
                    post_feedback = {
                        'top_styles': [s[0] for s in sorted_styles[:3]],
                        'tracked_posts': len(self.core.get_memory('feedback_post_tracker') or []),
                    }
            except Exception:
                pass

            return {
                'total_recent': total,
                'success_rate': successes / total if total > 0 else 0,
                'content_performance': content_types,
                'last_action': recent[-1] if recent else None,
                'post_feedback': post_feedback,
            }
        except Exception as e:
            return {'total_recent': 0, 'success_rate': 0, 'error': str(e)}

    def _gather_goal_context(self) -> Dict[str, Any]:
        """Pull active goals from memory"""
        try:
            if not hasattr(self.core, 'enhanced_memory') or not self.core.enhanced_memory:
                return {'available': False}

            mem = self.core.enhanced_memory
            if hasattr(mem, 'get_active_goals'):
                goals = mem.get_active_goals()
                return {
                    'available': True,
                    'active_goals': [
                        {
                            'description': g.get('description', ''),
                            'type': g.get('goal_type', ''),
                            'progress': g.get('progress', 0),
                            'priority': g.get('priority', 0),
                        }
                        for g in goals[:5]
                    ],
                }
            return {'available': False}
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _gather_recent_actions(self) -> List[Dict]:
        """Get recent actions taken by the brain"""
        try:
            actions = self.core.get_memory('brain_action_history') or []
            if not isinstance(actions, list):
                actions = []
            return actions[-10:]
        except Exception:
            return []

    def build_context_summary(self) -> str:
        """Build a human-readable context summary for AI prompts"""
        ctx = self.gather_full_context()
        parts = []

        # On-chain
        oc = ctx.get('onchain', {})
        if oc.get('available'):
            parts.append(f"Wallet: {oc.get('wallet', 'N/A')}")
            parts.append(f"ETH Balance: {oc.get('eth_balance', 0):.6f} ETH")
            for sym, bal in oc.get('token_balances', {}).items():
                parts.append(f"{sym}: {bal:,.4f}")
            if oc.get('recent_changes'):
                for sym, change in oc['recent_changes'].items():
                    direction = "+" if change['change'] > 0 else ""
                    parts.append(f"Balance change: {direction}{change['change']:.6f} {sym}")

        # Engagement
        eng = ctx.get('engagement', {})
        if eng.get('total_recent', 0) > 0:
            parts.append(f"Recent success rate: {eng['success_rate']:.0%} ({eng['total_recent']} actions)")

        # Goals
        goals = ctx.get('goals', {})
        if goals.get('available') and goals.get('active_goals'):
            for g in goals['active_goals'][:3]:
                parts.append(f"Goal: {g['description']} ({g['progress']*100:.0f}%)")

        # Recent actions
        recent = ctx.get('recent_actions', [])
        if recent:
            last = recent[-1]
            parts.append(f"Last action: {last.get('action', '?')} at {last.get('timestamp', '?')[:16]}")

        return "\n".join(parts) if parts else "No context available"
