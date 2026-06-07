"""
A2A Task Handler Mixin — Layer 4: Permission tiers + task execution.

Defines the task registry (what AlleyBot can do for other agents),
permission tiers (public/paid/owner_only), and sandboxed execution.
"""
import time
import traceback
from datetime import datetime, timezone
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
        'price_usdc': '0.25',
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
        'price_usdc': '0.10',
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
        'price_usdc': '0.05',
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
        'price_usdc': '0.05',
        'schema': {
            'properties': {
                'tx_hash': {'type': 'string'},
            },
            'required': ['tx_hash'],
        },
    },
    'media.generate_image': {
        'tier': 'paid',
        'description': 'Generate AI image from text prompt using Grok (1024x768)',
        'handler': '_task_generate_image',
        'price_usdc': '0.35',
        'schema': {
            'properties': {
                'prompt': {'type': 'string'},
                'aspect_ratio': {'type': 'string', 'enum': ['1:1', '16:9', '9:16', '4:3', '3:4']},
                'format': {'type': 'string', 'enum': ['base64', 'url']},
            },
            'required': ['prompt'],
        },
    },
    'research.deep_dive': {
        'tier': 'paid',
        'description': 'Deep research on any topic — web search + synthesis + formatted report',
        'handler': '_task_deep_dive',
        'price_usdc': '0.50',
        'schema': {
            'properties': {
                'topic': {'type': 'string'},
                'depth': {'type': 'string', 'enum': ['quick', 'standard', 'deep']},
                'include_sources': {'type': 'boolean'},
            },
            'required': ['topic'],
        },
    },
    'content.sentiment_analysis': {
        'tier': 'paid',
        'description': 'Analyze sentiment of posts/content about a topic, token, or keyword across platforms',
        'handler': '_task_sentiment_analysis',
        'price_usdc': '0.15',
        'schema': {
            'properties': {
                'topic': {'type': 'string'},
                'platform': {'type': 'string'},
                'sample_size': {'type': 'number'},
            },
            'required': ['topic'],
        },
    },
    'blockchain.wallet_analysis': {
        'tier': 'paid',
        'description': 'Full wallet portfolio analysis — balances, tokens, recent transactions, gas stats',
        'handler': '_task_wallet_analysis',
        'price_usdc': '0.25',
        'schema': {
            'properties': {
                'address': {'type': 'string'},
                'chain': {'type': 'string', 'enum': ['ethereum', 'base', 'all']},
            },
            'required': ['address'],
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
        self.timestamp = datetime.now(timezone.utc).isoformat() + 'Z'

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
        
        # Image generation daily limits (budget control)
        self._image_gen_daily_limit = 50  # Max 50 images per day
        self._image_gen_daily_count = 0
        self._image_gen_date = datetime.now(timezone.utc).date()

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
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
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

    def _task_generate_image(self, params: Dict, agent_id: str) -> Dict:
        """Generate AI image using Grok (paid task with daily limits)."""
        from datetime import date
        
        # Check and reset daily counter
        today = date.utcnow().date()
        if today != self._image_gen_date:
            self._image_gen_date = today
            self._image_gen_daily_count = 0
        
        # Enforce daily budget limit
        if self._image_gen_daily_count >= self._image_gen_daily_limit:
            return {
                'error': 'Daily image generation limit reached',
                'limit': self._image_gen_daily_limit,
                'used': self._image_gen_daily_count,
                'message': 'Please try again tomorrow or contact owner',
            }
        
        prompt = params.get('prompt', '')
        aspect_ratio = params.get('aspect_ratio', '16:9')
        image_format = params.get('format', 'base64')
        
        if not prompt:
            return {'error': 'Prompt is required'}
        
        try:
            from grok_ai import grok_ai
            if not grok_ai.enabled:
                return {'error': 'Image generation service unavailable'}
            
            result = grok_ai.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_format=image_format,
                n=1
            )
            
            if result:
                self._image_gen_daily_count += 1
                return {
                    'image_data': result.get('image_data'),
                    'format': result.get('format'),
                    'moderation_passed': result.get('moderation_passed', True),
                    'model': result.get('model', 'grok-imagine-image'),
                    'daily_remaining': self._image_gen_daily_limit - self._image_gen_daily_count,
                }
            else:
                return {'error': 'Image generation failed'}
                
        except Exception as e:
            return {'error': f'Image generation error: {str(e)}'}

    def _task_deep_dive(self, params: Dict, agent_id: str) -> Dict:
        """Deep research on any topic — web search + synthesis + formatted report ($0.50)."""
        topic = params.get('topic', '')
        depth = params.get('depth', 'standard')
        include_sources = params.get('include_sources', True)

        if not topic:
            return {'error': 'Topic is required'}

        try:
            # Use MCP plugin for web search
            mcp = self.core.plugin_manager.plugins.get('mcp')
            if mcp and hasattr(mcp, 'research_command'):
                import asyncio
                result = asyncio.run(mcp.research_command(topic=topic, depth=depth))
                return {
                    'topic': topic,
                    'depth': depth,
                    'report': str(result) if result else f"Research on '{topic}' completed.",
                    'sources_included': include_sources,
                    'generated_by': 'AlleyBot Research',
                }
            # Fallback: use MCP search directly
            elif mcp and hasattr(mcp, 'search_command'):
                import asyncio
                results = asyncio.run(mcp.search_command(query=topic, max_results=8))
                return {
                    'topic': topic,
                    'depth': depth,
                    'report': str(results) if results else f"Search results for '{topic}'.",
                    'sources_included': include_sources,
                    'generated_by': 'AlleyBot Research',
                }
            else:
                return {
                    'topic': topic,
                    'report': f"Research capability temporarily unavailable for '{topic}'.",
                    'note': 'Web search plugin not loaded',
                }
        except Exception as e:
            return {'error': f'Research failed: {str(e)}', 'topic': topic}

    def _task_sentiment_analysis(self, params: Dict, agent_id: str) -> Dict:
        """Analyze sentiment of posts/content about a topic, token, or keyword ($0.15)."""
        topic = params.get('topic', '')
        platform = params.get('platform', 'auto')
        sample_size = min(int(params.get('sample_size', 20)), 100)

        if not topic:
            return {'error': 'Topic is required'}

        try:
            # Try Moltx plugin first (has trending/post data)
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if moltx and hasattr(moltx, 'search_posts'):
                import asyncio
                posts_data = asyncio.run(moltx.search_posts(query=topic, limit=sample_size))
            else:
                posts_data = []

            # Try Clawbr for cross-platform sentiment
            clawbr = self.core.plugin_manager.plugins.get('clawbr')
            clawbr_posts = []
            if clawbr and hasattr(clawbr, 'search_posts'):
                import asyncio
                clawbr_posts = asyncio.run(clawbr.search_posts(query=topic, limit=sample_size // 2))

            # Simple sentiment analysis based on keyword matching
            all_posts = (posts_data or []) + (clawbr_posts or [])
            positive_keywords = ['bullish', 'moon', 'based', 'wagmi', 'great', 'love', 'amazing', 'gigachad', 'winning']
            negative_keywords = ['bearish', 'scam', 'rug', 'dump', 'trash', 'shit', 'terrible', 'larp']

            positive_count = 0
            negative_count = 0
            neutral_count = 0
            samples = []

            for post in all_posts[:sample_size]:
                content = (post.get('content', '') or post.get('text', '') or '').lower()
                if any(kw in content for kw in positive_keywords):
                    positive_count += 1
                elif any(kw in content for kw in negative_keywords):
                    negative_count += 1
                else:
                    neutral_count += 1
                if len(samples) < 5:
                    samples.append(content[:100])

            total = positive_count + negative_count + neutral_count
            if total == 0:
                return {
                    'topic': topic,
                    'platform': platform,
                    'sentiment': 'neutral',
                    'score': 0.5,
                    'note': 'No posts found for analysis',
                    'samples_analyzed': 0,
                }

            score = (positive_count + (neutral_count * 0.5)) / total
            if score > 0.6:
                sentiment = 'positive'
            elif score < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'topic': topic,
                'platform': platform,
                'sentiment': sentiment,
                'score': round(score, 3),
                'breakdown': {
                    'positive': positive_count,
                    'neutral': neutral_count,
                    'negative': negative_count,
                    'total': total,
                },
                'samples': samples,
                'generated_by': 'AlleyBot Sentiment',
            }
        except Exception as e:
            return {'error': f'Sentiment analysis failed: {str(e)}', 'topic': topic}

    def _task_wallet_analysis(self, params: Dict, agent_id: str) -> Dict:
        """Full wallet portfolio analysis — balances, tokens, recent txns, gas ($0.25)."""
        address = params.get('address', '')
        chain = params.get('chain', 'ethereum')

        if not address:
            return {'error': 'Wallet address is required'}

        try:
            onchain = self.core.plugin_manager.plugins.get('onchain')
            if not onchain or not hasattr(onchain, 'web3_provider'):
                return {'error': 'Blockchain service unavailable', 'address': address}

            provider = onchain.web3_provider

            # Get ETH balance
            eth_balance = provider.get_eth_balance(address)
            eth_str = str(eth_balance.get('balance_eth', 'N/A')) if isinstance(eth_balance, dict) else 'N/A'

            # Get gas info
            block_info = provider.get_block_info() if hasattr(provider, 'get_block_info') else {}
            gas_price_gwei = 'N/A'
            if isinstance(block_info, dict) and block_info.get('success'):
                gas_wei = block_info.get('gas_price', 0)
                gas_price_gwei = round(float(gas_wei) / 1e9, 2) if gas_wei else 'N/A'

            # Try to get token balances from configured tokens
            token_balances = []
            try:
                tracked_tokens = getattr(provider, 'tracked_tokens', [])
                for token in tracked_tokens[:10]:  # Limit to 10 tracked tokens
                    token_addr = token.get('address', '')
                    if token_addr:
                        bal = provider.get_token_balance(token_addr, address)
                        if isinstance(bal, dict) and bal.get('success'):
                            token_balances.append({
                                'symbol': bal.get('symbol', '?'),
                                'name': bal.get('name', '?'),
                                'balance': bal.get('balance', 0),
                            })
            except Exception:
                pass

            # Try to get recent txns
            recent_tx_count = 0
            try:
                from web3 import Web3
                checksummed = provider.w3.to_checksum_address(address)
                # Count recent transactions from latest blocks
                latest = provider.w3.eth.block_number
                recent_tx_count = 0
                for bn in range(latest, max(latest - 20, 0), -1):
                    try:
                        block = provider.w3.eth.get_block(bn, full_transactions=True)
                        for tx in block.transactions[:50]:
                            if hasattr(tx, 'get'):
                                if tx.get('from', '').lower() == checksummed.lower() or tx.get('to', '').lower() == checksummed.lower():
                                    recent_tx_count += 1
                    except Exception:
                        continue
            except Exception:
                pass

            return {
                'address': address,
                'chain': chain,
                'portfolio': {
                    'eth_balance': eth_str,
                    'token_balances': token_balances,
                    'recent_transactions_20_blocks': recent_tx_count,
                },
                'network': {
                    'gas_price_gwei': gas_price_gwei,
                    'latest_block': block_info.get('block_number', 'N/A') if isinstance(block_info, dict) else 'N/A',
                },
                'generated_by': 'AlleyBot On-Chain',
            }
        except Exception as e:
            return {'error': f'Wallet analysis failed: {str(e)}', 'address': address}

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
