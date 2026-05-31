"""Tests for RevenueIntelligence: P&L tracking, opportunity scoring, experiments."""

import sys
import unittest
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.revenue_intelligence import (
    RevenueIntelligence, RevenueEvent, RevenueOpportunity,
    get_revenue_intelligence,
)


class TestRevenueEvent(unittest.TestCase):
    def test_to_dict(self):
        e = RevenueEvent(
            source='trading', action='swap', asset='ETH',
            gross_amount=100.0, cost_amount=2.0, net_amount=98.0,
        )
        d = e.to_dict()
        self.assertEqual(d['source'], 'trading')
        self.assertEqual(d['net_amount'], 98.0)


class TestRevenueOpportunity(unittest.TestCase):
    def test_score_low_risk_low_effort(self):
        opp = RevenueOpportunity(
            source='trading', action='arb', description='test',
            expected_value=10.0, confidence=0.8,
            effort_estimate='low', risk_level='low',
        )
        self.assertAlmostEqual(opp.score(), 10.0 * 0.8 * 1.0 * 1.0)

    def test_score_high_risk_high_effort(self):
        opp = RevenueOpportunity(
            source='service', action='build', description='test',
            expected_value=100.0, confidence=0.5,
            effort_estimate='high', risk_level='high',
        )
        self.assertAlmostEqual(opp.score(), 100.0 * 0.5 * 0.3 * 0.4)


class TestRevenueIntelligence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / 'test_revenue.db')
        self.ri = RevenueIntelligence(db_path=self.db_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_and_summarize_pnl(self):
        self.ri.record_revenue(RevenueEvent(
            source='trading', action='swap', asset='ETH',
            gross_amount=50.0, cost_amount=2.0, net_amount=48.0,
        ))
        summary = self.ri.get_pnl_summary()
        self.assertEqual(summary['total_events'], 1)
        self.assertEqual(summary['total_net'], 48.0)
        self.assertIn('trading', summary['by_source'])

    def test_get_total_pnl_empty(self):
        pnl = self.ri.get_total_pnl()
        self.assertEqual(pnl, {})

    def test_multiple_sources(self):
        self.ri.record_revenue(RevenueEvent(
            source='trading', action='swap', asset='ETH',
            gross_amount=100, cost_amount=5, net_amount=95,
        ))
        self.ri.record_revenue(RevenueEvent(
            source='content', action='post', asset='SOCIAL',
            gross_amount=10, cost_amount=0, net_amount=10,
        ))
        summary = self.ri.get_pnl_summary()
        self.assertEqual(summary['total_events'], 2)
        self.assertEqual(summary['total_net'], 105.0)

    def test_register_and_score_opportunities(self):
        opp = RevenueOpportunity(
            source='trading', action='arb', description='Arbitrage scan',
            expected_value=5.0, confidence=0.3,
            effort_estimate='medium', risk_level='medium',
        )
        self.ri.register_opportunity(opp)
        top = self.ri.get_top_opportunities(limit=5)
        self.assertEqual(len(top), 1)
        self.assertEqual(top[0].source, 'trading')

    def test_register_replaces_with_higher_value(self):
        self.ri.register_opportunity(RevenueOpportunity(
            source='trading', action='arb', description='test',
            expected_value=1.0, confidence=0.5,
            effort_estimate='low', risk_level='low',
        ))
        self.ri.register_opportunity(RevenueOpportunity(
            source='trading', action='arb', description='test',
            expected_value=10.0, confidence=0.5,
            effort_estimate='low', risk_level='low',
        ))
        top = self.ri.get_top_opportunities(1)
        self.assertEqual(top[0].expected_value, 10.0)

    def test_get_untried_opportunities(self):
        self.ri.register_opportunity(RevenueOpportunity(
            source='trading', action='arb', description='test',
            expected_value=5.0, confidence=0.5,
            effort_estimate='low', risk_level='low',
        ))
        untried = self.ri.get_untried_opportunities()
        self.assertEqual(len(untried), 1)

    def test_record_and_complete_experiment(self):
        eid = self.ri.record_experiment(
            source='trading', action='test_swap', description='test',
            expected_value=1.0, confidence=0.5,
            effort='low', risk='low',
        )
        self.assertGreater(eid, 0)
        self.ri.complete_experiment(eid, 'success', 'worked well')
        summary = self.ri.get_experiment_summary()
        self.assertEqual(summary['successes'], 1)
        self.assertEqual(summary['total'], 1)

    def test_scan_trading_no_balances(self):
        opps = self.ri.scan_trading_opportunities()
        self.assertGreater(len(opps), 0)

    def test_scan_trading_with_balances(self):
        opps = self.ri.scan_trading_opportunities({'ETH': 1.5})
        eth_opps = [o for o in opps if 'ETH' in o.action]
        self.assertGreater(len(eth_opps), 0)

    def test_scan_content_opportunities(self):
        opps = self.ri.scan_content_opportunities()
        self.assertGreater(len(opps), 0)

    def test_scan_service_opportunities(self):
        opps = self.ri.scan_service_opportunities()
        self.assertGreater(len(opps), 0)

    def test_scan_all_opportunities(self):
        opps = self.ri.scan_all_opportunities()
        self.assertGreater(len(opps), 0)

    def test_scan_registers_opportunities(self):
        self.ri.scan_all_opportunities()
        self.assertGreater(len(self.ri._opportunities), 0)


class TestGetRevenueIntelligence(unittest.TestCase):
    def test_singleton(self):
        ri1 = get_revenue_intelligence(db_path=':memory:')
        ri2 = get_revenue_intelligence(db_path=':memory:')
        self.assertIs(ri1, ri2)


if __name__ == '__main__':
    unittest.main()
