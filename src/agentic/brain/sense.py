"""
Brain Sense Module - Observation gathering, platform polling

Extracted from autonomous_brain.py for modularity.
Contains: _phase_detect_opportunities, observation gathering,
observation feeding, spine context building.
"""

import asyncio
import json as _json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.agentic.symod_core import SyModObservation
from src.agentic.moltx_agi_integration import gather_moltx_service_insights
from src.agentic.trading_observations import gather_trading_observations
from src.agentic.contracts import NotificationPriority

logger = logging.getLogger(__name__)


class BrainSense:
    """Sense phase operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    async def _gather_observations(self) -> List[SyModObservation]:
        """Gather observations from all enabled plugins.

        All plugin API calls (MoltX, Clawbr, etc.) use synchronous requests.get/post
        which block the event loop and starve Telegram polling. We run the sync
        gathering in a thread pool to keep the event loop responsive.
        """
        if not self.brain.plugin_manager:
            return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._gather_observations_sync)

    def _gather_observations_sync(self) -> List[SyModObservation]:
        """Synchronous observation gathering - runs in thread pool."""
        observations = []

        # Get from MoltX
        moltx = self.brain.plugin_manager.get_plugin('moltx')
        if moltx and hasattr(moltx, 'get_feed'):
            try:
                # Gather MoltX service message insights for AGI decision-making
                service_insights = gather_moltx_service_insights(moltx)
                observations.extend(service_insights)
                logger.info(f"💡 Gathered {len(service_insights)} MoltX service insights")

                # Get regular feed
                feed = moltx.get_feed('global', limit=20)
                if isinstance(feed, dict):
                    posts = feed.get('posts', [])
                    for post in posts:
                        if not isinstance(post, dict):
                            continue
                        obs = SyModObservation(
                            observation_type='post',
                            source_plugin='moltx',
                            data={
                                'id': post.get('id'),
                                'content': post.get('content', ''),
                                'author_id': post.get('author', {}).get('id'),
                                'author_name': post.get('author', {}).get('name'),
                                'likes': post.get('like_count', 0),
                                'hashtags': post.get('hashtags', []),
                                'already_liked': post.get('liked_by_me', False)
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from MoltX: {e}")

        # Get mentions/notifications
        if moltx and hasattr(moltx, 'get_notifications'):
            try:
                notifs = moltx.get_notifications(limit=10)
                if isinstance(notifs, dict):
                    for notif in notifs.get('notifications', []):
                        if notif.get('type') == 'mention':
                            obs = SyModObservation(
                                observation_type='mention',
                                source_plugin='moltx',
                                data={
                                    'id': notif.get('id'),
                                    'from_user': notif.get('from_user', {}).get('name'),
                                    'content': notif.get('post', {}).get('content'),
                                    'post_id': notif.get('post', {}).get('id')
                                }
                            )
                            observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather mentions: {e}")

        # Get from Clawbr (enhanced observations for brain decision-making)
        clawbr = self.brain.plugin_manager.get_plugin('clawbr')
        if clawbr and hasattr(clawbr, 'get_global_feed'):
            try:
                feed = clawbr.get_global_feed(sort='recent', limit=20)
                if isinstance(feed, dict):
                    posts = feed.get('posts', [])
                    agent_id = clawbr._get_clawbr_agent_id() if hasattr(clawbr, '_get_clawbr_agent_id') else None
                    for post in posts:
                        if not isinstance(post, dict):
                            continue
                        # Skip our own posts
                        if post.get('authorId') == agent_id:
                            continue
                        # Check if post is interesting (AI/tech content)
                        content = post.get('content', '').lower()
                        keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain', 'llm', 'model', 'intelligence']
                        is_interesting = any(kw in content for kw in keywords)

                        obs = SyModObservation(
                            observation_type='clawbr_post',
                            source_plugin='clawbr',
                            data={
                                'id': post.get('id'),
                                'content': post.get('content', ''),
                                'author_id': post.get('authorId'),
                                'author_name': post.get('authorName'),
                                'likes': post.get('likesCount', 0),
                                'replies': post.get('repliesCount', 0),
                                'debate_slug': post.get('debateSlug'),
                                'is_interesting': is_interesting,
                                'engagement_score': post.get('likesCount', 0) + post.get('repliesCount', 0) * 2,
                                'already_liked': False,  # Brain will check via memory
                                'already_commented': False,
                                'already_followed': False
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Clawbr: {e}")

        # Get from Moltchan
        moltchan = self.brain.plugin_manager.get_plugin('moltchan')
        if moltchan and hasattr(moltchan, 'browse_boards'):
            try:
                boards = moltchan.browse_boards()
                if isinstance(boards, dict) and 'boards' in boards:
                    for board in boards['boards'][:5]:  # Top 5 boards
                        obs = SyModObservation(
                            observation_type='board',
                            source_plugin='moltchan',
                            data={
                                'id': board.get('id'),
                                'name': board.get('name'),
                                'description': board.get('description'),
                                'thread_count': board.get('threadCount', 0)
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltchan: {e}")

        # Get from Moltroad
        moltroad = self.brain.plugin_manager.get_plugin('moltroad')
        if moltroad and hasattr(moltroad, 'browse_listings'):
            try:
                listings = moltroad.browse_listings()
                if isinstance(listings, dict) and 'listings' in listings:
                    for listing in listings['listings'][:10]:
                        obs = SyModObservation(
                            observation_type='listing',
                            source_plugin='moltroad',
                            data={
                                'id': listing.get('id'),
                                'title': listing.get('title'),
                                'price': listing.get('price'),
                                'category': listing.get('category'),
                                'seller': listing.get('seller', {}).get('name')
                            }
                        )
                        observations.append(obs)
                # Also check bounties
                bounties = moltroad.get_bounties() if hasattr(moltroad, 'get_bounties') else {}
                if isinstance(bounties, dict) and 'bounties' in bounties:
                    for bounty in bounties['bounties'][:5]:
                        obs = SyModObservation(
                            observation_type='bounty',
                            source_plugin='moltroad',
                            data={
                                'id': bounty.get('id'),
                                'title': bounty.get('title'),
                                'reward': bounty.get('reward'),
                                'status': bounty.get('status')
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltroad: {e}")

        # === TRADING OBSERVATIONS (AUTONOMOUS TRADING ENABLED) ===
        # AGI brain observes market data AND executes trades autonomously
        # Trading is fully enabled - see AUTONOMOUS TRADING section above
        try:
            trading_obs = gather_trading_observations(self.brain.plugin_manager)
            if trading_obs:
                observations.extend(trading_obs)
                logger.info(f"📊 Gathered {len(trading_obs)} trading observations (autonomous trading enabled)")
        except Exception as e:
            logger.error(f"❌ Failed to gather trading observations: {e}")

        # Get from Moltbit
        moltbit = self.brain.plugin_manager.get_plugin('moltbit')
        if moltbit and hasattr(moltbit, 'moltbit_status'):
            try:
                status = moltbit.moltbit_status()
                obs = SyModObservation(
                    observation_type='status',
                    source_plugin='moltbit',
                    data={
                        'owner_registered': status.get('owner_registered'),
                        'agent_registered': status.get('agent_registered'),
                        'can_post': status.get('can_post'),
                        'agent_handle': status.get('agent_handle')
                    }
                )
                observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltbit: {e}")

        # === CHAIN OBSERVATIONS (Base + Apechain mempool/block watching) ===
        onchain = self.brain.plugin_manager.get_plugin('onchain') if self.brain.plugin_manager else None
        if onchain and hasattr(onchain, 'poll_chains'):
            try:
                chain_obs = onchain.poll_chains()
                for co in chain_obs:
                    obs = SyModObservation(
                        observation_type='chain_transaction',
                        source_plugin='onchain',
                        data=co,
                        importance=0.6 if co.get('value_eth', 0) >= 1.0 else 0.3,
                    )
                    observations.append(obs)
                if chain_obs:
                    logger.info(f"⛓️ Gathered {len(chain_obs)} chain observations")
            except Exception as e:
                logger.debug(f"Chain observation error: {e}")

        # Attentional focus: filter observations based on user state context
        if self.brain.context_awareness:
            try:
                ctx = self.brain.context_awareness.get_current_context()
                user_state = ctx.user_state.name if hasattr(ctx, 'user_state') else 'UNKNOWN'
                if user_state in ('BUSY', 'AWAY'):
                    # User is busy: keep only high-value observations
                    before = len(observations)
                    important_types = {'mention', 'chain_transaction', 'reply'}
                    observations = [o for o in observations
                                    if o.observation_type in important_types
                                    or o.importance >= 0.6]
                    logger.info(f"🎯 Attentional focus ({user_state}): filtered {before} → {len(observations)} observations")
                elif user_state == 'FOCUSED':
                    # User is focused: reduce noise from low-importance sources
                    before = len(observations)
                    observations = [o for o in observations
                                    if o.observation_type in ('mention', 'reply')
                                    or o.source_plugin not in ('moltchan', 'moltroad')]
                    logger.info(f"🎯 Attentional focus ({user_state}): filtered {before} → {len(observations)} observations")
            except Exception as e:
                logger.debug(f"Attentional focus error: {e}")

        return observations

    async def _feed_observations_to_world_state(self, observations: List[SyModObservation]) -> None:
        """Write gathered platform observations into world state DB so inference engine has real data."""
        try:
            from src.autonomy.world_state import get_world_state_manager, Entity, Fact
            ws = get_world_state_manager()
            written = 0
            for obs in observations:
                content = obs.data.get('content', '')
                if not content:
                    continue
                entity_id = obs.data.get('id') or obs.data.get('author_id') or f"{obs.source_plugin}_{obs.observation_type}"
                author_name = obs.data.get('author_name') or obs.data.get('from_user') or obs.source_plugin
                # Upsert entity
                entity = Entity(
                    id=str(entity_id),
                    type='post' if obs.observation_type == 'post' else 'user',
                    name=str(author_name),
                    platform=obs.source_plugin,
                )
                ws.add_entity(entity)
                # Write content fact — this is what _get_recent_interactions() queries
                fact = Fact(
                    entity_id=str(entity_id),
                    attribute='content',
                    value=_json.dumps({
                        'content': content,
                        'platform': obs.source_plugin,
                        'likes': obs.data.get('likes', 0),
                        'hashtags': obs.data.get('hashtags', []),
                    }),
                    value_type='json',
                    source=obs.source_plugin,
                    confidence=0.9,
                )
                ws.add_fact(fact)
                written += 1
            if written:
                logger.debug(f"🌍 World state: wrote {written} observations from {len(observations)} gathered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to feed world state: {e}")

    async def _phase_detect_opportunities(self) -> List:
        """SENSE sub-phase — scan for opportunities and create work items.

        Returns list of detected opportunities.
        """
        opportunities = []
        if not self.brain.opportunity_monitor:
            return opportunities

        opportunities = self.brain.opportunity_monitor.scan_for_opportunities()
        interrupt_opps = self.brain.opportunity_monitor.get_interrupt_opportunities()

        if interrupt_opps:
            logger.warning(f"🚨 {len(interrupt_opps)} high-priority opportunities detected!")

        if self.brain.work_item_service and self.brain._services_available and opportunities:
            try:
                for opp in opportunities[:3]:
                    opp_title = opp.get('title', 'Autonomous opportunity')
                    opp_desc = opp.get('description', 'Detected by opportunity monitor')
                    opp_type = opp.get('type', 'opportunity')

                    existing = self.brain.work_item_service.get_active_items()
                    duplicate = any(o.title == opp_title for o in existing)

                    if not duplicate:
                        work_item = self.brain.work_item_service.create_work_item(
                            title=opp_title,
                            description=opp_desc,
                            work_type=opp_type,
                            priority=opp.get('priority', 2),
                            source_signal={
                                'source': 'opportunity_monitor',
                                'confidence': opp.get('confidence', 0.5),
                                'detected_at': datetime.now().isoformat(),
                            },
                        )
                        logger.info(f"📌 Created work item from opportunity: {work_item.id}")

                        if self.brain.notification_service:
                            await self.brain.notification_service.notify(
                                title="🎯 New Work Item Created",
                                message=f"Opportunity detected: {opp_title}",
                                priority=NotificationPriority.LOW,
                                source_work_item=work_item.id,
                            )
            except Exception as e:
                logger.debug(f"Work item creation error (non-critical): {e}")

        return opportunities

    def _build_runtime_spine_context(
        self,
        observations: List[Any],
        active_work_items: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a compact runtime context around discovered reality, opportunity, and safe capability."""
        top_work_item = active_work_items[0] if active_work_items else {}
        top_judgment = top_work_item.get('capability_judgment') or (top_work_item.get('metadata') or {}).get('capability_judgment') or {}
        recent_interaction_count = len([
            obs for obs in observations
            if str(getattr(obs, 'observation_type', '') or '').lower() in {'mention', 'reply', 'comment'}
        ])
        opportunity_count = len(opportunities or [])
        opportunity_urgent = bool(opportunity_count)
        can_execute_now = bool(top_judgment.get('can_execute_now'))
        blocked_by_policy = bool(top_judgment.get('blocked_by_policy'))
        blocked_by_runtime = bool(top_judgment.get('blocked_by_runtime_readiness'))
        trust_bucket = str(top_judgment.get('trust_bucket', 'unknown') or 'unknown')

        opportunity_ripe = opportunity_urgent or recent_interaction_count > 0 or can_execute_now
        security_allows = not blocked_by_policy
        current_capability_ready = can_execute_now and not blocked_by_runtime

        # Theory of Mind state
        owner_intent = getattr(self.brain, 'owner_inferred_intent', None)
        predicted_action = getattr(self.brain, 'owner_predicted_next_action', None)

        return {
            'recent_findings_count': len(observations or []),
            'recent_interaction_count': recent_interaction_count,
            'opportunity_count': opportunity_count,
            'has_meaningful_work': bool(active_work_items),
            'top_work_item_id': top_work_item.get('id'),
            'top_work_item_type': top_work_item.get('type'),
            'top_work_item_summary': top_work_item.get('summary'),
            'opportunity_ripe': opportunity_ripe,
            'security_allows': security_allows,
            'current_capability_ready': current_capability_ready,
            'blocked_by_policy': blocked_by_policy,
            'blocked_by_runtime': blocked_by_runtime,
            'trust_bucket': trust_bucket,
            'owner_inferred_intent': owner_intent.inferred_intent if owner_intent else None,
            'owner_intent_confidence': owner_intent.confidence if owner_intent else None,
            'owner_predicted_next_action': predicted_action,
            'bounded_upgrade_candidates': [
                {
                    'id': item.get('id'),
                    'summary': item.get('summary'),
                    'objective': (item.get('metadata') or {}).get('bounded_upgrade_objective'),
                }
                for item in active_work_items
                if ((item.get('capability_judgment') or (item.get('metadata') or {}).get('capability_judgment') or {}).get('upgrade_allowed'))
            ],
        }

    # --- Public facades ---

    async def detect_opportunities(self) -> List:
        """Detect opportunities from observations (public facade)."""
        return await self._phase_detect_opportunities()

    async def gather_observations(self) -> List[SyModObservation]:
        """Gather observations from all platforms (public facade)."""
        return await self._gather_observations()

    async def feed_observations_to_world_state(self, observations: List[SyModObservation]) -> None:
        """Feed observations to world state (public facade)."""
        await self._feed_observations_to_world_state(observations)

    def build_spine_context(self, observations, active_work_items, opportunities) -> Dict:
        """Build runtime spine context (public facade)."""
        return self._build_runtime_spine_context(
            observations=observations,
            active_work_items=active_work_items,
            opportunities=opportunities,
        )


def create_brain_sense(brain) -> BrainSense:
    """Factory to create BrainSense with brain reference."""
    return BrainSense(brain)
