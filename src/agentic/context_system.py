"""
Context System - Intelligent context gathering for AGI Kernel

Extracted from plugins/brain/context_gatherer.py to centralize intelligence.
Gathers context from all available sources: memory, on-chain, platforms, engagement.

Key Features:
- Multi-source context aggregation (memory, blockchain, social platforms)
- Intelligent caching (120s TTL)
- Performance tracking and engagement analytics
- Goal-aware context building
- Human-readable context summaries for AI prompts

SOP Compliance:
- This is an AGI Kernel component (src/agentic/), not a plugin
- No decision logic - just data gathering
- Uses unified memory (no persistent state)
- Follows existing pattern from decision_system.py
"""

import datetime
from typing import Dict, Any, Optional, List


class ContextSystem:
    """
    Intelligent context gathering system for AGI Kernel.

    Collects context from all available sources to inform autonomous decisions.
    """

    def __init__(self, agi_kernel, plugin_manager):
        """
        Initialize context system.

        Args:
            agi_kernel: AGI Kernel instance
            plugin_manager: Plugin manager for accessing platform plugins
        """
        self.agi = agi_kernel
        self.plugin_manager = plugin_manager
        self.core = agi_kernel.core if hasattr(agi_kernel, 'core') else None

        # Context caching
        self.context_cache: Dict[str, Any] = {}
        self.cache_ttl = 120  # seconds
        self.last_context_time: Optional[datetime.datetime] = None

        print("🔍 Context System initialized")

    def gather_full_context(self) -> Dict[str, Any]:
        """
        Gather context from ALL available sources for decision-making.

        Returns comprehensive context dict with:
        - memory: Recent memories and stats
        - onchain: Wallet balances, gas prices, block info
        - platforms: Platform availability and last activity
        - engagement: Performance metrics and feedback
        - goals: Active goals from AGI Kernel
        - recent_actions: Last 10 actions taken
        """
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
        """Pull relevant context from unified memory"""
        try:
            if not self.agi or not hasattr(self.agi, 'unified_memory'):
                return {'available': False}

            mem = self.agi.unified_memory

            # Get memory stats
            stats = {}
            if hasattr(mem, 'get_stats'):
                stats = mem.get_stats()

            # Get recent memories via semantic search
            recent = []
            if hasattr(mem, 'semantic_search'):
                try:
                    results = mem.semantic_search('recent activity engagement', top_k=5)
                    recent = [{'content': r.get('content', ''), 'type': r.get('type', '')} for r in results]
                except Exception as e:
                    import logging
                    logging.debug(f"Could not fetch recent activity: {e}")

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
            if not self.plugin_manager or not hasattr(self.plugin_manager, 'plugins'):
                return {'available': False}

            onchain = self.plugin_manager.plugins.get('onchain')
            if not onchain or not hasattr(onchain, 'web3_provider'):
                return {'available': False}

            provider = onchain.web3_provider
            if not provider or not getattr(provider, 'connected', False):
                return {'available': False}

            # Get ETH balance
            eth_result = provider.get_eth_balance()

            # Get block info
            block_info = provider.get_block_info()

            # Get token balances
            token_balances = {}
            if hasattr(onchain, 'tracked_tokens'):
                for symbol, token_info in onchain.tracked_tokens.items():
                    result = provider.get_token_balance(token_info['address'])
                    if result.get('success'):
                        token_balances[symbol] = result['balance']

            # Check for balance changes
            changes = None
            if hasattr(onchain, 'check_balance_changes'):
                changes = onchain.check_balance_changes()

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
            'clawbr': 'Clawbr',
        }

        if not self.plugin_manager or not hasattr(self.plugin_manager, 'plugins'):
            return platforms

        for plugin_name, display_name in plugin_map.items():
            try:
                plugin = self.plugin_manager.plugins.get(plugin_name)
                if not plugin:
                    platforms[plugin_name] = {'loaded': False}
                    continue

                info = {
                    'loaded': True,
                    'has_heartbeat': hasattr(plugin, 'moltx_heartbeat'),
                    'has_feed': hasattr(plugin, 'feed_command'),
                    'has_engage': hasattr(plugin, 'engage_feed_command'),
                    'has_post': hasattr(plugin, 'create_post') or hasattr(plugin, 'create_post_command'),
                }

                # Get last heartbeat time from unified memory
                if self.agi and hasattr(self.agi, 'unified_memory'):
                    last_hb = self.agi.unified_memory.get(f'{plugin_name}_last_heartbeat')
                    info['last_heartbeat'] = last_hb

                platforms[plugin_name] = info

            except Exception as e:
                platforms[plugin_name] = {'loaded': False, 'error': str(e)}

        return platforms

    def _gather_engagement_context(self) -> Dict[str, Any]:
        """Pull engagement history and performance data"""
        try:
            if not self.agi or not hasattr(self.agi, 'unified_memory'):
                return {'total_recent': 0, 'success_rate': 0}

            mem = self.agi.unified_memory

            # Get engagement log from memory
            engagement_log = mem.get('brain_engagement_log') or []
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
                style_scores = mem.get('feedback_style_scores') or {}
                if style_scores:
                    sorted_styles = sorted(
                        style_scores.items(),
                        key=lambda x: x[1].get('avg_score', 0),
                        reverse=True
                    )
                    post_feedback = {
                        'top_styles': [s[0] for s in sorted_styles[:3]],
                        'tracked_posts': len(mem.get('feedback_post_tracker') or []),
                    }
            except Exception as e:
                import logging
                logging.debug(f"Could not get learning insights: {e}")

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
        """Pull active goals from AGI Kernel's goal manager"""
        try:
            if not self.agi or not hasattr(self.agi, 'goal_manager'):
                return {'available': False}

            goal_mgr = self.agi.goal_manager

            # Get active goals
            if hasattr(goal_mgr, 'get_active_goals'):
                goals = goal_mgr.get_active_goals()
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
        """Get recent actions from episodic memory"""
        try:
            if not self.agi or not hasattr(self.agi, 'episodic_memory'):
                return []

            episodic = self.agi.episodic_memory

            # Get recent episodes
            if hasattr(episodic, 'get_recent_episodes'):
                episodes = episodic.get_recent_episodes(limit=10)
                return [
                    {
                        'action': ep.action,
                        'timestamp': ep.timestamp.isoformat() if ep.timestamp else '',
                        'outcome': ep.outcome,
                        'success': ep.emotional_valence > 0
                    }
                    for ep in episodes
                ]

            # Fallback to unified memory
            if hasattr(self.agi, 'unified_memory'):
                actions = self.agi.unified_memory.get('brain_action_history') or []
                if isinstance(actions, list):
                    return actions[-10:]

            return []
        except Exception as e:
            import logging
            logging.debug(f"Could not get recent actions: {e}")
            return []

    def build_context_summary(self, max_tokens: int = 2000) -> str:
        """
        Build a human-readable context summary for AI prompts.

        Respects a token budget by prioritizing the most important context
        and truncating lower-priority sections when over budget.
        Priority: goals > recent actions > engagement > memory > on-chain

        Args:
            max_tokens: Maximum token budget (default 2000, use ~16000 for full context)
        """
        ctx = self.gather_full_context()

        # Token estimator: ~4 chars per token for English text
        def estimate_tokens(text: str) -> int:
            try:
                import tiktoken
                enc = tiktoken.get_encoding('cl100k_base')
                return len(enc.encode(text))
            except Exception:
                return len(text) // 4

        def truncate_to_budget(text: str, budget: int) -> str:
            if estimate_tokens(text) <= budget:
                return text
            # Truncate by character count approximation
            max_chars = budget * 4
            return text[:max_chars] + f"\n... [truncated, ~{budget} tokens]"

        sections = {}  # priority_key -> text

        # Priority 1: Active goals (highest priority)
        goals = ctx.get('goals', {})
        goals_lines = []
        if goals.get('available') and goals.get('active_goals'):
            for g in goals['active_goals'][:3]:
                goals_lines.append(f"Goal: {g['description']} ({g['progress']*100:.0f}%)")
        if goals_lines:
            sections['goals'] = "\n".join(goals_lines)

        # Priority 2: Recent actions
        recent = ctx.get('recent_actions', [])
        if recent:
            actions_lines = ["Recent actions:"]
            for a in recent[-5:]:
                ts = a.get('timestamp', '?')[:16] if isinstance(a.get('timestamp'), str) else '?'
                actions_lines.append(f"  {a.get('action', '?')} @ {ts}")
            sections['actions'] = "\n".join(actions_lines)

        # Priority 3: Engagement performance
        eng = ctx.get('engagement', {})
        if eng.get('total_recent', 0) > 0:
            sections['engagement'] = f"Performance: {eng['success_rate']:.0%} success ({eng['total_recent']} actions, {eng.get('total_engagement', 0)} engagements)"

        # Priority 4: Memory context (brief)
        mem = ctx.get('memory', {})
        if mem.get('available') and mem.get('stats'):
            stats = mem['stats']
            sections['memory'] = f"Memory: {stats.get('total_memories', '?')} entries, {stats.get('semantic_memories', '?')} semantic"

        # Priority 5: On-chain (lowest, can be verbose)
        oc = ctx.get('onchain', {})
        onchain_lines = []
        if oc.get('available'):
            onchain_lines.append(f"Wallet: {oc.get('wallet', 'N/A')} | ETH: {oc.get('eth_balance', 0):.6f}")
            token_items = list(oc.get('token_balances', {}).items())[:5]
            for sym, bal in token_items:
                onchain_lines.append(f"{sym}: {bal:,.4f}")
            changes = oc.get('recent_changes', {})
            for sym, change in list(changes.items())[:3]:
                direction = "+" if change['change'] > 0 else ""
                onchain_lines.append(f"Change: {direction}{change['change']:.6f} {sym}")
        if onchain_lines:
            sections['onchain'] = "\n".join(onchain_lines)

        # Assemble within token budget: fill highest priority first
        priority_order = ['goals', 'actions', 'engagement', 'memory', 'onchain']
        assembled = []
        budget_remaining = max_tokens

        header = "Context Summary:\n"
        if estimate_tokens(header) < budget_remaining:
            assembled.append("Context Summary:")
            budget_remaining -= estimate_tokens(header)

        for key in priority_order:
            if key not in sections:
                continue

            text = sections[key]
            section_budget = max(100, budget_remaining // max(len([k for k in priority_order if k in sections]), 1))
            truncated = truncate_to_budget(text, section_budget)
            assembled.append(truncated)
            budget_remaining -= estimate_tokens(truncated)

            if budget_remaining < 50:
                assembled.append("[Further context truncated due to token budget]")
                break

        return "\n".join(assembled) if assembled else "No context available"

    def invalidate_cache(self):
        """Force cache refresh on next gather_full_context() call"""
        self.context_cache = {}
        self.last_context_time = None


def create_context_system(agi_kernel, plugin_manager):
    """Factory function to create context system"""
    return ContextSystem(agi_kernel, plugin_manager)
