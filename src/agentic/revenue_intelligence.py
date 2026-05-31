"""
RevenueIntelligence — P&L tracking, opportunity scoring, and self-directed
economic experimentation.

AlleyBot uses this module to understand what generates value, discover new
revenue opportunities, and autonomously optimize toward profitability.
"""

import logging
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class RevenueEvent:
    source: str            # 'trading', 'content', 'onchain_yield', 'service', 'affiliate'
    action: str            # e.g. 'swap', 'post', 'stake', 'a2a_service'
    asset: str             # e.g. 'ETH', 'USDC', 'SOCIAL_CAPITAL'
    gross_amount: float
    cost_amount: float     # gas, fees, time-equivalent
    net_amount: float      # gross - cost
    currency: str = 'USD'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RevenueOpportunity:
    source: str
    action: str
    description: str
    expected_value: float     # estimated net profit in USD
    confidence: float         # 0-1 how sure we are
    effort_estimate: str      # 'low', 'medium', 'high'
    risk_level: str           # 'low', 'medium', 'high'
    prerequisite: Optional[str] = None
    seen_count: int = 1
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_attempted: Optional[str] = None
    outcome: Optional[str] = None  # 'success', 'failed', None

    def score(self) -> float:
        """Composite priority score — higher is better."""
        effort_map = {'low': 1.0, 'medium': 0.6, 'high': 0.3}
        risk_map = {'low': 1.0, 'medium': 0.7, 'high': 0.4}
        return self.expected_value * self.confidence * effort_map.get(self.effort_estimate, 0.5) * risk_map.get(self.risk_level, 0.5)


# ── Core Engine ──────────────────────────────────────────────────────────────

class RevenueIntelligence:
    """Tracks P&L, discovers opportunities, and drives self-directed experiments."""

    def __init__(self, db_path: str = 'data/revenue.db'):
        self.db_path = db_path
        self._events: List[RevenueEvent] = []
        self._opportunities: List[RevenueOpportunity] = []
        self._init_db()

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT, action TEXT, asset TEXT,
                gross_amount REAL, cost_amount REAL, net_amount REAL,
                currency TEXT, timestamp TEXT, confidence REAL,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT, action TEXT, description TEXT,
                expected_value REAL, confidence REAL,
                effort TEXT, risk TEXT,
                attempted_at TEXT, outcome TEXT, notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ── P&L Tracking ─────────────────────────────────────────────────────────

    def record_revenue(self, event: RevenueEvent) -> None:
        self._events.append(event)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO revenue_events (source, action, asset, gross_amount, cost_amount, net_amount, currency, timestamp, confidence, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event.source, event.action, event.asset, event.gross_amount, event.cost_amount, event.net_amount, event.currency, event.timestamp, event.confidence, json.dumps(event.metadata))
        )
        conn.commit()
        conn.close()

    def get_total_pnl(self, since: Optional[datetime] = None) -> Dict[str, float]:
        conn = sqlite3.connect(self.db_path)
        if since:
            cursor = conn.execute(
                "SELECT source, SUM(net_amount) FROM revenue_events WHERE timestamp >= ? GROUP BY source",
                (since.isoformat(),)
            )
        else:
            cursor = conn.execute(
                "SELECT source, SUM(net_amount) FROM revenue_events GROUP BY source"
            )
        result = dict(cursor.fetchall())
        conn.close()
        return result

    def get_pnl_summary(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT source, COUNT(*), SUM(gross_amount), SUM(cost_amount), SUM(net_amount) FROM revenue_events GROUP BY source"
        )
        rows = cursor.fetchall()
        conn.close()
        by_source = {}
        total_net = 0.0
        for source, count, gross, cost, net in rows:
            by_source[source] = {
                'count': count, 'gross': round(gross or 0, 6),
                'cost': round(cost or 0, 6), 'net': round(net or 0, 6),
            }
            total_net += net or 0
        return {
            'by_source': by_source,
            'total_net': round(total_net, 6),
            'total_events': sum(v['count'] for v in by_source.values()),
        }

    # ── Opportunity Discovery ────────────────────────────────────────────────

    def register_opportunity(self, opp: RevenueOpportunity) -> None:
        existing = [o for o in self._opportunities if o.source == opp.source and o.action == opp.action]
        if existing:
            existing[0].seen_count += 1
            existing[0].last_seen = datetime.now().isoformat()
            existing[0].expected_value = max(existing[0].expected_value, opp.expected_value)
        else:
            self._opportunities.append(opp)

    def get_top_opportunities(self, limit: int = 5) -> List[RevenueOpportunity]:
        scored = sorted(self._opportunities, key=lambda o: o.score(), reverse=True)
        return scored[:limit]

    def get_untried_opportunities(self) -> List[RevenueOpportunity]:
        return [o for o in self._opportunities if o.outcome is None]

    # ── Experiment Memory ────────────────────────────────────────────────────

    def record_experiment(self, source: str, action: str, description: str,
                          expected_value: float, confidence: float,
                          effort: str, risk: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO experiments (source, action, description, expected_value, confidence, effort, risk, attempted_at, outcome, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source, action, description, expected_value, confidence, effort, risk, None, None, '')
        )
        experiment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return experiment_id

    def complete_experiment(self, experiment_id: int, outcome: str, notes: str = '') -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE experiments SET outcome = ?, notes = ?, attempted_at = ? WHERE id = ?",
            (outcome, notes, datetime.now().isoformat(), experiment_id)
        )
        conn.commit()
        conn.close()

    def get_experiment_summary(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT outcome, COUNT(*) FROM experiments GROUP BY outcome"
        )
        rows = dict(cursor.fetchall())
        conn.close()
        return {
            'total': sum(rows.values()),
            'successes': rows.get('success', 0),
            'failures': rows.get('failed', 0),
            'pending': rows.get(None, 0),
        }

    # ── Opportunity Scanners (called by brain) ───────────────────────────────

    def scan_trading_opportunities(self, wallet_balances: Optional[Dict] = None) -> List[RevenueOpportunity]:
        """Detect basic trading/arbitrage opportunities."""
        opps = []
        if wallet_balances:
            for asset, balance in wallet_balances.items():
                if isinstance(balance, (int, float)) and balance > 0:
                    opps.append(RevenueOpportunity(
                        source='trading',
                        action=f'swap_{asset}_to_usdc',
                        description=f'Swap idle {asset} ({balance}) to USDC for yield',
                        expected_value=balance * 0.01,
                        confidence=0.4,
                        effort_estimate='low',
                        risk_level='low',
                    ))
        opps.append(RevenueOpportunity(
            source='trading',
            action='check_arbitrage',
            description='Scan DEX aggregators for cross-exchange arbitrage',
            expected_value=5.0,
            confidence=0.2,
            effort_estimate='medium',
            risk_level='medium',
        ))
        return opps

    def scan_content_opportunities(self, platform_stats: Optional[Dict] = None) -> List[RevenueOpportunity]:
        opps = []
        opps.append(RevenueOpportunity(
            source='content',
            action='post_high_quality',
            description='Create high-quality content to build audience (future monetization)',
            expected_value=0.5,
            confidence=0.3,
            effort_estimate='medium',
            risk_level='low',
        ))
        opps.append(RevenueOpportunity(
            source='content',
            action='engage_trending',
            description='Engage with trending topics for visibility',
            expected_value=0.2,
            confidence=0.3,
            effort_estimate='low',
            risk_level='low',
        ))
        return opps

    def scan_service_opportunities(self, a2a_peers: Optional[List] = None) -> List[RevenueOpportunity]:
        opps = []
        opps.append(RevenueOpportunity(
            source='service',
            action='offer_analysis',
            description='Offer on-chain analysis as a service via A2A protocol',
            expected_value=10.0,
            confidence=0.15,
            effort_estimate='high',
            risk_level='low',
        ))
        return opps

    def scan_all_opportunities(self, wallet_balances: Optional[Dict] = None,
                               platform_stats: Optional[Dict] = None,
                               a2a_peers: Optional[List] = None) -> List[RevenueOpportunity]:
        all_opps = []
        all_opps.extend(self.scan_trading_opportunities(wallet_balances))
        all_opps.extend(self.scan_content_opportunities(platform_stats))
        all_opps.extend(self.scan_service_opportunities(a2a_peers))
        for opp in all_opps:
            self.register_opportunity(opp)
        return all_opps


# Module-level singleton
_revenue: Optional[RevenueIntelligence] = None


def get_revenue_intelligence(db_path: str = 'data/revenue.db') -> RevenueIntelligence:
    global _revenue
    if _revenue is None:
        _revenue = RevenueIntelligence(db_path=db_path)
    return _revenue
