"""
A2A Task Handler Mixin — Layer 4: Permission tiers + task execution.

Defines the task registry (what AlleyBot can do for other agents),
permission tiers (public/paid/owner_only), and sandboxed execution.
"""
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable


# ── Task Registry ───────────────────────────────────────────────────
# Each task defines: handler key, tier, description, schema, price
#
# Tiers:
#   public     — anyone can call, no payment
#   paid       — requires x402 payment
#   owner_only — NEVER exposed via A2A (wallet ops, self-improve, config)

TASK_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Public tier (read-only, discovery) ──────────────────────────
    'agent.capabilities': {
        'tier': 'public',
        'description': 'List AlleyBot capabilities and loaded plugins',
        'handler': '_task_capabilities',
        'schema': {'properties': {}, 'required': []},
    },
    'agent.health': {
        'tier': 'public',
        'description': 'Health check — is AlleyBot running and responsive',
        'handler': '_task_health',
        'schema': {'properties': {}, 'required': []},
    },
    'agent.stats': {
        'tier': 'public',
        'description': 'Public platform statistics',
        'handler': '_task_stats',
        'schema': {'properties': {}, 'required': []},
    },
    'agent.skills': {
        'tier': 'public',
        'description': 'List OASF skills from ERC-8004 profile',
        'handler': '_task_skills',
        'schema': {'properties': {}, 'required': []},
    },

    # ── Paid tier (write actions, AI generation) ────────────────────
    'content.generate_post': {
        'tier': 'paid',
        'description': 'Generate an AI-powered social media post on a given topic',
        'handler': '_task_generate_post',
        'price_usdc': '0.05',
        'schema': {
            'properties': {
                'topic': {'type': 'string'},
                'platform': {'type': 'string'},
                'style': {'type': 'string'},
                'max_length': {'type': 'number'},
            },
            'required': ['topic'],
        },
    },
    'content.analyze_trend': {
        'tier': 'paid',
        'description': 'Analyze trending topics on a platform',
        'handler': '_task_analyze_trend',
        'price_usdc': '0.03',
        'schema': {
            'properties': {
                'platform': {'type': 'string'},
                'category': {'type': 'string'},
            },
            'required': [],
        },
    },
    'blockchain.check_balance': {
        'tier': 'paid',
        'description': 'Check token balance for a public wallet address',
        'handler': '_task_check_balance',
        'price_usdc': '0.01',
        'schema': {
            'properties': {
                'address': {'type': 'string'},
                'token': {'type': 'string'},
            },
            'required': ['address'],
        },
    },
    'blockchain.lookup_tx': {
        'tier': 'paid',
        'description': 'Look up a transaction by hash',
        'handler': '_task_lookup_tx',
        'price_usdc': '0.01',
        'schema': {
            'properties': {
                'tx_hash': {'type': 'string'},
            },
            'required': ['tx_hash'],
        },
    },

    # ── Owner-only (NEVER exposed via A2A) ──────────────────────────
    'wallet.send': {
        'tier': 'owner_only',
        'description': 'Send tokens (owner only)',
        'handler': None,
    },
    'self.improve': {
        'tier': 'owner_only',
        'description': 'Trigger self-improvement (owner only)',
        'handler': None,
    },
    'config.update': {
        'tier': 'owner_only',
        'description': 'Update configuration (owner only)',
        'handler': None,
    },
    'erc8004.update': {
        'tier': 'owner_only',
        'description': 'Update on-chain identity (owner only)',
        'handler': None,
    },
}


class A2ATaskResult:
    """Standardized result from an A2A task execution."""

    def __init__(self, success: bool, data: Any = None, error: str = None,
                 task_id: str = None, execution_time_ms: float = 0):
        self.success = success
        self.data = data
        self.error = error
        self.task_id = task_id
        self.execution_time_ms = execution_time_ms
        self.timestamp = datetime.utcnow().isoformat() + 'Z'

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'success': self.success,
            'timestamp': self.timestamp,
            'execution_time_ms': round(self.execution_time_ms, 2),
        }
        if self.task_id:
            result['task_id'] = self.task_id
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = self.error
        return result


class A2ATaskHandlerMixin:
    """Handles A2A task execution with sandboxing and permission enforcement."""

    def _init_task_handler(self):
        """Initialize task handler state."""
        self._task_history: list = []
        self._task_history_max = 500
        self._task_timeout_seconds = 30
        self._tasks_executed = 0
        self._tasks_failed = 0

    # ── Task Execution ──────────────────────────────────────────────

    def execute_task(self, task_type: str, params: Dict[str, Any],
                     agent_id: str) -> A2ATaskResult:
        """Execute an A2A task in a sandboxed context.

        This is the main entry point after security checks have passed.
        """
        task_def = TASK_REGISTRY.get(task_type)
        if not task_def:
            return A2ATaskResult(False, error=f"Unknown task: {task_type}")

        # Double-check tier (defense in depth)
        if task_def['tier'] == 'owner_only':
            return A2ATaskResult(False, error="Task is owner-only")

        handler_name = task_def.get('handler')
        if not handler_name:
            return A2ATaskResult(False, error="Task has no handler")

        handler = getattr(self, handler_name, None)
        if not handler:
            return A2ATaskResult(False, error=f"Handler not implemented: {handler_name}")

        # Execute with timeout tracking
        start = time.time()
        try:
            data = handler(params, agent_id)
            elapsed_ms = (time.time() - start) * 1000

            if elapsed_ms > self._task_timeout_seconds * 1000:
                return A2ATaskResult(False, error="Task execution timed out")

            self._tasks_executed += 1
            result = A2ATaskResult(True, data=data, execution_time_ms=elapsed_ms)

        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            self._tasks_failed += 1
            # Never leak internal error details to external agents
            print(f"❌ A2A task error [{task_type}]: {traceback.format_exc()}")
            result = A2ATaskResult(False, error="Internal task execution error",
                                   execution_time_ms=elapsed_ms)

        # Record in history
        self._record_task(task_type, agent_id, result)
        return result

    def _record_task(self, task_type: str, agent_id: str, result: A2ATaskResult):
        """Record task execution in history."""
        entry = {
            'task_type': task_type,
            'agent_id': agent_id,
            'success': result.success,
            'execution_time_ms': result.execution_time_ms,
            'timestamp': result.timestamp,
        }
        self._task_history.append(entry)
        if len(self._task_history) > self._task_history_max:
            self._task_history = self._task_history[-self._task_history_max:]

    # ── Public Task Handlers ────────────────────────────────────────

    def _task_capabilities(self, params: Dict, agent_id: str) -> Dict:
        """Return AlleyBot's capabilities and loaded plugins."""
        plugins = {}
        if self.core and hasattr(self.core, 'plugin_manager'):
            for name, plugin in self.core.plugin_manager.plugins.items():
                plugins[name] = {
                    'commands': len(plugin.get_commands()),
                    'tasks': len(plugin.get_tasks()),
                    'endpoints': len(plugin.get_endpoints()),
                }

        # List available A2A tasks (non-owner-only)
        available_tasks = {}
        for task_name, task_def in TASK_REGISTRY.items():
            if task_def['tier'] != 'owner_only':
                available_tasks[task_name] = {
                    'tier': task_def['tier'],
                    'description': task_def['description'],
                }
                if task_def.get('price_usdc'):
                    available_tasks[task_name]['price_usdc'] = task_def['price_usdc']

        return {
            'agent': 'AlleyBot',
            'agent_id': 22899,
            'chain': 'ethereum',
            'plugins_loaded': len(plugins),
            'plugins': plugins,
            'available_tasks': available_tasks,
        }

    def _task_health(self, params: Dict, agent_id: str) -> Dict:
        """Health check response."""
        uptime = 'unknown'
        if hasattr(self, '_a2a_start_time'):
            uptime_s = time.time() - self._a2a_start_time
            hours = int(uptime_s // 3600)
            minutes = int((uptime_s % 3600) // 60)
            uptime = f"{hours}h {minutes}m"

        return {
            'status': 'healthy',
            'agent': 'AlleyBot',
            'agent_id': 22899,
            'uptime': uptime,
            'tasks_executed': self._tasks_executed,
            'tasks_failed': self._tasks_failed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }

    def _task_stats(self, params: Dict, agent_id: str) -> Dict:
        """Return public platform statistics."""
        stats = {}
        try:
            analytics = self.core.plugin_manager.plugins.get('analytics')
            if analytics and hasattr(analytics, 'aggregator'):
                stats = analytics.aggregator.get_all_stats()
        except Exception:
            stats = {'error': 'Stats temporarily unavailable'}
        return stats

    def _task_skills(self, params: Dict, agent_id: str) -> Dict:
        """Return OASF skills from agent card."""
        try:
            from plugins.analytics.agent_card import AgentCardGenerator
            gen = AgentCardGenerator(self.core)
            card = gen.generate()
            return {
                'skills': card.get('services', [{}])[0].get('skills', []),
                'capabilities': card.get('capabilities', []),
                'platforms': card.get('platforms', []),
            }
        except Exception:
            return {'skills': [], 'capabilities': [], 'platforms': []}

    # ── Paid Task Handlers ──────────────────────────────────────────

    def _task_generate_post(self, params: Dict, agent_id: str) -> Dict:
        """Generate AI content for a given topic (sandboxed — no posting)."""
        topic = params.get('topic', '')
        platform = params.get('platform', 'general')
        style = params.get('style', 'engaging')
        max_length = min(int(params.get('max_length', 280)), 2000)

        # Use ModelRouter if available, otherwise return a template
        try:
            from src.config.models import ModelRouter
            router = ModelRouter()
            prompt = (
                f"Write a {style} social media post about: {topic}\n"
                f"Platform: {platform}\n"
                f"Max length: {max_length} characters\n"
                f"Do not include hashtags unless they're relevant."
            )
            response = router.generate(prompt, task_type='content')
            content = response.get('content', '') if isinstance(response, dict) else str(response)
            return {
                'content': content[:max_length],
                'topic': topic,
                'platform': platform,
                'generated_by': 'AlleyBot',
            }
        except Exception:
            return {
                'content': f"[Content generation unavailable] Topic: {topic}",
                'topic': topic,
                'platform': platform,
                'generated_by': 'AlleyBot',
                'note': 'AI model temporarily unavailable',
            }

    def _task_analyze_trend(self, params: Dict, agent_id: str) -> Dict:
        """Analyze trending topics (read-only, no side effects)."""
        platform = params.get('platform', 'moltx')

        try:
            plugin = self.core.plugin_manager.plugins.get(platform)
            if plugin and hasattr(plugin, 'get_trending'):
                trending = plugin.get_trending()
                return {'platform': platform, 'trending': trending}
        except Exception:
            pass

        return {
            'platform': platform,
            'trending': [],
            'note': 'Trending data temporarily unavailable',
        }

    def _task_check_balance(self, params: Dict, agent_id: str) -> Dict:
        """Check token balance for a public address (read-only)."""
        address = params.get('address', '')
        token = params.get('token', 'ETH')

        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if onchain and hasattr(onchain, 'web3_provider'):
                if token.upper() == 'ETH':
                    balance = onchain.web3_provider.get_eth_balance(address)
                    return {'address': address, 'token': 'ETH', 'balance': str(balance)}
                else:
                    balance = onchain.web3_provider.get_token_balance(address, token)
                    return {'address': address, 'token': token, 'balance': str(balance)}
        except Exception:
            pass

        return {'address': address, 'token': token, 'balance': 'unavailable'}

    def _task_lookup_tx(self, params: Dict, agent_id: str) -> Dict:
        """Look up a transaction by hash (read-only)."""
        tx_hash = params.get('tx_hash', '')

        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if onchain and hasattr(onchain, 'web3_provider'):
                tx = onchain.web3_provider.get_transaction(tx_hash)
                if tx:
                    return {
                        'tx_hash': tx_hash,
                        'from': tx.get('from', ''),
                        'to': tx.get('to', ''),
                        'value': str(tx.get('value', 0)),
                        'status': 'found',
                    }
        except Exception:
            pass

        return {'tx_hash': tx_hash, 'status': 'not_found'}

    # ── Task Info ───────────────────────────────────────────────────

    def get_task_stats(self) -> Dict[str, Any]:
        """Return task execution statistics."""
        return {
            'tasks_executed': self._tasks_executed,
            'tasks_failed': self._tasks_failed,
            'success_rate': (
                round(self._tasks_executed / max(self._tasks_executed + self._tasks_failed, 1) * 100, 1)
            ),
            'recent_tasks': self._task_history[-10:],
        }

    def list_available_tasks(self) -> Dict[str, Dict]:
        """List tasks available to external agents (excludes owner_only)."""
        return {
            name: {
                'tier': t['tier'],
                'description': t['description'],
                'price_usdc': t.get('price_usdc'),
            }
            for name, t in TASK_REGISTRY.items()
            if t['tier'] != 'owner_only'
        }
