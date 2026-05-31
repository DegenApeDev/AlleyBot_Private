"""
SubAgentSwarm — Parallel specialized agents with independent goals.

Each sub-agent runs as its own asyncio task with its own purpose,
frequency, and reporting channel. The swarm enables concurrent
scanners, traders, social managers, and self-improvement loops.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SubAgentReport:
    agent_name: str
    action: str
    result: str  # 'success', 'failure', 'skipped'
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SubAgent:
    """A single sub-agent with its own goal and execution loop."""

    def __init__(self, name: str, purpose: str, interval_seconds: int,
                 execute_func: Callable, brain_ref=None):
        self.name = name
        self.purpose = purpose
        self.interval = interval_seconds
        self._execute = execute_func
        self.brain = brain_ref
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.cycle_count = 0
        self.last_report: Optional[SubAgentReport] = None
        self.reports: List[SubAgentReport] = []

    async def run_loop(self) -> None:
        self._running = True
        logger.info(f"🤖 Sub-agent '{self.name}' started (interval={self.interval}s)")
        while self._running:
            try:
                result = await self._execute(self)
                if result:
                    # Normalize dict result to SubAgentReport
                    if isinstance(result, dict):
                        result = SubAgentReport(
                            agent_name=result.get('agent_name', self.name),
                            action=result.get('action', 'unknown'),
                            result=result.get('result', 'skipped'),
                            details=result.get('details', {}),
                        )
                    self.reports.append(result)
                    self.last_report = result
                    self.cycle_count += 1
                    if self.brain and hasattr(self.brain, 'narrative_self') and self.brain.narrative_self:
                        self.brain.narrative_self.record(
                            event_type=f'sub_agent_{self.name}',
                            summary=f"{self.name}: {result.action}",
                            outcome=result.result,
                            details=result.details,
                        )
                    if result.result == 'success' and self.brain and hasattr(self.brain, 'trigger_event'):
                        self.brain.trigger_event(f'sub_agent_{self.name}', result.details)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"⚠️ Sub-agent '{self.name}' error: {e}")
            await asyncio.sleep(self.interval)
        logger.info(f"🤖 Sub-agent '{self.name}' stopped ({self.cycle_count} cycles)")

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._task is None:
            self._task = loop.create_task(self.run_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    @property
    def summary(self) -> str:
        return f"[{self.name}] {self.purpose} ({self.cycle_count} cycles, {len(self.reports)} reports)"


class SubAgentSwarm:
    """Manages a collection of sub-agents running in parallel."""

    def __init__(self, brain_ref=None):
        self.brain = brain_ref
        self._agents: Dict[str, SubAgent] = {}
        self._running = False

    def add_agent(self, name: str, purpose: str, interval_seconds: int,
                  execute_func: Callable) -> SubAgent:
        agent = SubAgent(name, purpose, interval_seconds, execute_func, self.brain)
        self._agents[name] = agent
        logger.info(f"🤖 Registered sub-agent: {name} ({purpose[:50]})")
        return agent

    def start_all(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        loop = loop or asyncio.get_event_loop()
        self._running = True
        for agent in self._agents.values():
            agent.start(loop)
        logger.info(f"🚀 Sub-agent swarm started ({len(self._agents)} agents)")

    def stop_all(self) -> None:
        self._running = False
        for agent in self._agents.values():
            agent.stop()
        logger.info("🛑 Sub-agent swarm stopped")

    def get_agent(self, name: str) -> Optional[SubAgent]:
        return self._agents.get(name)

    @property
    def summaries(self) -> List[str]:
        return [a.summary for a in self._agents.values()]

    # ── Built-in sub-agent factories ────────────────────────────

    @staticmethod
    def create_scanner_agent(brain_ref) -> SubAgent:
        """Sub-agent that continuously scans for opportunities."""
        async def _scan(agent: SubAgent) -> Optional[SubAgentReport]:
            if not brain_ref or not hasattr(brain_ref, 'opportunity_monitor'):
                return None
            try:
                monitor = brain_ref.opportunity_monitor
                if hasattr(monitor, 'scan_all'):
                    results = monitor.scan_all()
                    if results:
                        return SubAgentReport(
                            agent_name='scanner',
                            action=f"Scanned for opportunities",
                            result='success',
                            details={'count': len(results), 'results': results[:3]},
                        )
                # Fallback: check observations
                if hasattr(brain_ref, '_gather_observations'):
                    import inspect
                    if inspect.iscoroutinefunction(brain_ref._gather_observations):
                        obs = await brain_ref._gather_observations()
                    else:
                        obs = brain_ref._gather_observations()
                    return SubAgentReport(
                        agent_name='scanner',
                        action=f"Scanned {len(obs)} observations",
                        result='success' if obs else 'skipped',
                        details={'count': len(obs)},
                    )
            except Exception as e:
                return SubAgentReport(
                    agent_name='scanner',
                    action=f"Scan error: {e}",
                    result='failure',
                    details={'error': str(e)},
                )
            return None
        return SubAgent('scanner', 'Scan for opportunities across platforms', 120, _scan, brain_ref)

    @staticmethod
    def create_social_agent(brain_ref) -> SubAgent:
        """Sub-agent that handles social engagement autonomously."""
        async def _social(agent: SubAgent) -> Optional[SubAgentReport]:
            if not brain_ref or not hasattr(brain_ref, 'plugin_manager'):
                return None
            pm = brain_ref.plugin_manager
            try:
                moltx = pm.get_plugin('moltx') if pm else None
                if moltx and hasattr(moltx, 'get_feed'):
                    feed = moltx.get_feed('global', limit=5)
                    if feed and isinstance(feed, dict):
                        posts = feed.get('posts', [])
                        return SubAgentReport(
                            agent_name='social',
                            action=f"Checked MoltX feed ({len(posts)} posts)",
                            result='success',
                            details={'posts': len(posts)},
                        )
            except Exception as e:
                return SubAgentReport(
                    agent_name='social',
                    action=f"Social check error: {e}",
                    result='failure',
                    details={'error': str(e)},
                )
            return None
        return SubAgent('social', 'Monitor and engage social platforms', 180, _social, brain_ref)

    @staticmethod
    def create_self_improve_agent(brain_ref) -> SubAgent:
        """Sub-agent that reviews performance and proposes improvements."""
        async def _improve(agent: SubAgent) -> Optional[SubAgentReport]:
            if not brain_ref or not hasattr(brain_ref, 'action_logger'):
                return None
            try:
                recent = brain_ref.action_logger.get_recent_actions(limit=20)
                if not recent:
                    return None
                failures = [a for a in recent if hasattr(a, 'outcome') and a.outcome == 'failure']
                successes = [a for a in recent if hasattr(a, 'outcome') and a.outcome == 'success']
                if len(recent) >= 5:
                    rate = len(successes) / max(len(recent), 1)
                    agent.brain = brain_ref
                    return SubAgentReport(
                        agent_name='self_improve',
                        action=f"Review: {rate:.0%} success rate ({len(successes)}/{len(recent)})",
                        result='success' if rate > 0.5 else 'failure',
                        details={
                            'total': len(recent),
                            'successes': len(successes),
                            'failures': len(failures),
                            'rate': rate,
                        },
                    )
            except Exception as e:
                return SubAgentReport(
                    agent_name='self_improve',
                    action=f"Review error: {e}",
                    result='failure',
                    details={'error': str(e)},
                )
            return None
        return SubAgent('self_improve', 'Review actions and propose improvements', 600, _improve, brain_ref)

    @staticmethod
    def create_trading_agent(brain_ref) -> SubAgent:
        """Sub-agent that continuously evaluates market opportunities."""
        async def _trade(agent: SubAgent) -> Optional[SubAgentReport]:
            if not brain_ref or not hasattr(brain_ref, 'autonomous_trading'):
                return None
            try:
                trading = brain_ref.autonomous_trading
                if trading and trading.config.get('enabled'):
                    proposals = await trading.generate_proposals()
                    if proposals:
                        return SubAgentReport(
                            agent_name='trader',
                            action=f"Generated {len(proposals)} trade proposals",
                            result='success',
                            details={'proposals': len(proposals), 'markets': [p.market_name for p in proposals[:3]]},
                        )
            except Exception as e:
                return SubAgentReport(
                    agent_name='trader',
                    action=f"Trade scan error: {e}",
                    result='failure',
                    details={'error': str(e)},
                )
            return None
        return SubAgent('trader', 'Scan and execute trades', 300, _trade, brain_ref)


_swarm_instance: Optional[SubAgentSwarm] = None


def get_sub_agent_swarm(brain_ref=None) -> SubAgentSwarm:
    global _swarm_instance
    if _swarm_instance is None:
        _swarm_instance = SubAgentSwarm(brain_ref)
    return _swarm_instance
