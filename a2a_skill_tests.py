#!/usr/bin/env python3
"""
A2A Skill Validation Suite - Production Ready Test Runner
Tests all 15 AlleyBot A2A skills via curl against https://tasks.apeshit.fun

Usage: python3 a2a_skill_tests.py
"""

import asyncio
import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import aiohttp
import sys


@dataclass
class TestResult:
    """Result of a single skill test."""
    skill_id: str
    tier: str  # 'public' or 'paid'
    price_usdc: Optional[str]
    status: str  # 'PASS', 'FAIL', 'TIMEOUT', 'ERROR'
    response_time_ms: float
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    payment_simulated: bool = False
    retries: int = 0


@dataclass
class TestReport:
    """Complete test report."""
    timestamp: str
    endpoint: str
    total_tests: int
    passed: int
    failed: int
    results: List[TestResult] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


class A2ASkillTester:
    """Production-ready A2A skill test runner with parallel execution."""
    
    BASE_URL = "https://tasks.apeshit.fun"
    ENDPOINT = f"{BASE_URL}/message:send"
    AGENT_CARD_URL = f"{BASE_URL}/.well-known/agent-card.json"
    
    # Test configurations
    TIMEOUT_SECONDS = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    RATE_LIMIT_DELAY = 7  # 7 seconds between requests = ~8.5 req/min (under 10 limit)
    
    # Test wallet address (AlleyBot's public address)
    TEST_WALLET = "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5"
    
    # Test contract on Base
    TEST_CONTRACT = "0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07"  # ALLEY token
    
    # Test transaction hash
    TEST_TX_HASH = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    # x402 Payment simulation (Base Sepolia testnet USDC)
    X402_TEST_CONFIG = {
        "chain_id": 84532,  # Base Sepolia
        "token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # USDC testnet
        "sender": "0xtest_wallet_address",
        "max_amount": "1000000",  # 1 USDC (6 decimals)
    }
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS),
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _build_a2a_message(self, skill_id: str, params: Dict, simulate_payment: bool = False) -> Dict:
        """Build A2A protocol compliant message."""
        message = {
            "messageId": f"test-{skill_id}-{int(time.time() * 1000)}",
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": f"Execute skill: {skill_id}"
                },
                {
                    "type": "data",
                    "data": {
                        "skill_id": skill_id,
                        "params": params,
                        "test_run": True,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            ]
        }
        
        # Simulate x402 payment for paid skills
        if simulate_payment:
            message["metadata"] = {
                "payment": {
                    "protocol": "x402",
                    "chainId": self.X402_TEST_CONFIG["chain_id"],
                    "token": self.X402_TEST_CONFIG["token"],
                    "maxAmount": self.X402_TEST_CONFIG["max_amount"],
                    "sender": self.X402_TEST_CONFIG["sender"],
                    "intent": "pay_for_skill_execution",
                    "skill_id": skill_id
                }
            }
        
        return message
    
    async def _send_request(self, skill_id: str, params: Dict, 
                           tier: str, price_usdc: Optional[str]) -> TestResult:
        """Send request with retry logic."""
        retries = 0
        last_error = None
        
        simulate_payment = tier == 'paid'
        
        while retries < self.MAX_RETRIES:
            start_time = time.time()
            try:
                message = self._build_a2a_message(skill_id, params, simulate_payment)
                
                payload = {
                    "message": message,
                    "contextId": f"test-context-{skill_id}"
                }
                
                async with self.session.post(
                    self.ENDPOINT,
                    json=payload,
                    ssl=False  # Allow for local testing
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return TestResult(
                            skill_id=skill_id,
                            tier=tier,
                            price_usdc=price_usdc,
                            status='PASS',
                            response_time_ms=response_time,
                            response_data=data,
                            payment_simulated=simulate_payment,
                            retries=retries
                        )
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"
                        
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                response_time = (time.time() - start_time) * 1000
                return TestResult(
                    skill_id=skill_id,
                    tier=tier,
                    price_usdc=price_usdc,
                    status='TIMEOUT',
                    response_time_ms=response_time,
                    error_message=last_error,
                    payment_simulated=simulate_payment,
                    retries=retries
                )
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
            
            retries += 1
            if retries < self.MAX_RETRIES:
                await asyncio.sleep(self.RETRY_DELAY)
        
        # All retries exhausted
        return TestResult(
            skill_id=skill_id,
            tier=tier,
            price_usdc=price_usdc,
            status='FAIL',
            response_time_ms=(time.time() - start_time) * 1000,
            error_message=last_error,
            payment_simulated=simulate_payment,
            retries=retries
        )
    
    # === Skill Test Methods ===
    
    async def test_capabilities(self) -> TestResult:
        """Test agent.capabilities (FREE)."""
        return await self._send_request(
            'agent.capabilities',
            {},
            'public',
            None
        )
    
    async def test_health(self) -> TestResult:
        """Test agent.health (FREE)."""
        return await self._send_request(
            'agent.health',
            {},
            'public',
            None
        )
    
    async def test_stats(self) -> TestResult:
        """Test agent.stats (FREE)."""
        return await self._send_request(
            'agent.stats',
            {},
            'public',
            None
        )
    
    async def test_skills(self) -> TestResult:
        """Test agent.skills (FREE)."""
        return await self._send_request(
            'agent.skills',
            {},
            'public',
            None
        )
    
    async def test_generate_post(self) -> TestResult:
        """Test content.generate_post ($0.25)."""
        return await self._send_request(
            'content.generate_post',
            {
                "topic": "ALLEY token pump - why this is the 100x gem everyone's sleeping on",
                "platform": "x",
                "style": "engaging",
                "max_length": 280
            },
            'paid',
            '0.25'
        )
    
    async def test_analyze_trend(self) -> TestResult:
        """Test content.analyze_trend ($0.10)."""
        return await self._send_request(
            'content.analyze_trend',
            {
                "platform": "moltx",
                "category": "crypto"
            },
            'paid',
            '0.10'
        )
    
    async def test_check_balance(self) -> TestResult:
        """Test blockchain.check_balance ($0.05)."""
        return await self._send_request(
            'blockchain.check_balance',
            {
                "address": self.TEST_WALLET,
                "token": "ETH"
            },
            'paid',
            '0.05'
        )
    
    async def test_lookup_tx(self) -> TestResult:
        """Test blockchain.lookup_tx ($0.05)."""
        # Note: Using dummy tx hash - real implementation would use valid hash
        return await self._send_request(
            'blockchain.lookup_tx',
            {
                "tx_hash": self.TEST_TX_HASH
            },
            'paid',
            '0.05'
        )
    
    async def test_generate_image(self) -> TestResult:
        """Test media.generate_image ($0.35)."""
        return await self._send_request(
            'media.generate_image',
            {
                "prompt": "A futuristic crypto trading bot in neon blue and purple colors, cyberpunk style, with the text 'AlleyBot' glowing",
                "aspect_ratio": "16:9",
                "format": "base64"
            },
            'paid',
            '0.35'
        )
    
    async def test_price_alert(self) -> TestResult:
        """Test crypto.price_alert ($0.05)."""
        return await self._send_request(
            'crypto.price_alert',
            {
                "token": "ETH",
                "threshold": 3000,
                "condition": "above"
            },
            'paid',
            '0.05'
        )
    
    async def test_shill_post(self) -> TestResult:
        """Test social.shill_post ($0.30)."""
        return await self._send_request(
            'social.shill_post',
            {
                "project": "AlleyBot AI Agent",
                "platform": "x",
                "tone": "degen",
                "include_hashtags": True
            },
            'paid',
            '0.30'
        )
    
    async def test_wallet_audit(self) -> TestResult:
        """Test wallet.audit ($0.15)."""
        return await self._send_request(
            'wallet.audit',
            {
                "address": self.TEST_WALLET,
                "chain": "base",
                "deep_scan": True
            },
            'paid',
            '0.15'
        )
    
    async def test_apy_optimizer(self) -> TestResult:
        """Test defi.apy_optimizer ($0.35)."""
        return await self._send_request(
            'defi.apy_optimizer',
            {
                "protocols": ["aave", "compound", "yearn"],
                "capital": 5000,
                "days": 30,
                "risk_level": "medium"
            },
            'paid',
            '0.35'
        )
    
    async def test_slither_scan(self) -> TestResult:
        """Test contract.slither_scan ($0.45)."""
        return await self._send_request(
            'contract.slither_scan',
            {
                "address": self.TEST_CONTRACT,
                "chain": "base",
                "deep_scan": True
            },
            'paid',
            '0.45'
        )
    
    async def test_skill_recommend(self) -> TestResult:
        """Test a2a.skill_recommend ($0.20)."""
        return await self._send_request(
            'a2a.skill_recommend',
            {
                "task": "defi yield optimization and best farming opportunities",
                "budget": 2.0,
                "min_reputation": 80,
                "chain": "base"
            },
            'paid',
            '0.20'
        )
    
    async def run_all_tests(self) -> TestReport:
        """Run all 15 skill tests sequentially with rate limiting."""
        print("🚀 Starting AlleyBot A2A Skill Validation Suite")
        print(f"📍 Endpoint: {self.ENDPOINT}")
        print(f"⏱️  Timeout: {self.TIMEOUT_SECONDS}s | Retries: {self.MAX_RETRIES}")
        print(f"🐌 Rate limit: 10 req/min | Delay: {self.RATE_LIMIT_DELAY}s between requests")
        print("=" * 80)
        
        # Define all test methods
        test_methods = [
            ("agent.capabilities", self.test_capabilities),
            ("agent.health", self.test_health),
            ("agent.stats", self.test_stats),
            ("agent.skills", self.test_skills),
            ("content.generate_post", self.test_generate_post),
            ("content.analyze_trend", self.test_analyze_trend),
            ("blockchain.check_balance", self.test_check_balance),
            ("blockchain.lookup_tx", self.test_lookup_tx),
            ("media.generate_image", self.test_generate_image),
            ("crypto.price_alert", self.test_price_alert),
            ("social.shill_post", self.test_shill_post),
            ("wallet.audit", self.test_wallet_audit),
            ("defi.apy_optimizer", self.test_apy_optimizer),
            ("contract.slither_scan", self.test_slither_scan),
            ("a2a.skill_recommend", self.test_skill_recommend),
        ]
        
        # Run tests sequentially with delays
        start_time = time.time()
        processed_results = []
        
        for i, (skill_name, test_method) in enumerate(test_methods, 1):
            print(f"\n[{i}/15] Testing {skill_name}...", end=" ", flush=True)
            
            try:
                result = await test_method()
                processed_results.append(result)
                status_icon = "✅" if result.status == "PASS" else "❌"
                print(f"{status_icon} {result.status} ({result.response_time_ms:.0f}ms)")
                
                # Add delay between requests (except after last)
                if i < len(test_methods):
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)
                    
            except Exception as e:
                print(f"💥 ERROR: {e}")
                processed_results.append(TestResult(
                    skill_id=skill_name,
                    tier="unknown",
                    price_usdc=None,
                    status="ERROR",
                    response_time_ms=0,
                    error_message=str(e)
                ))
                if i < len(test_methods):
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)
        
        total_time = time.time() - start_time
        
        # Calculate summary
        passed = sum(1 for r in processed_results if r.status == 'PASS')
        failed = len(processed_results) - passed
        
        report = TestReport(
            timestamp=datetime.utcnow().isoformat() + "Z",
            endpoint=self.ENDPOINT,
            total_tests=len(processed_results),
            passed=passed,
            failed=failed,
            results=processed_results,
            summary={
                "total_execution_time_sec": round(total_time, 2),
                "pass_rate_percent": round(passed / len(processed_results) * 100, 1),
                "avg_response_time_ms": round(
                    sum(r.response_time_ms for r in processed_results) / len(processed_results), 2
                ),
                "public_skills_tested": sum(1 for r in processed_results if r.tier == 'public'),
                "paid_skills_tested": sum(1 for r in processed_results if r.tier == 'paid'),
                "x402_payments_simulated": sum(1 for r in processed_results if r.payment_simulated),
            }
        )
        
        return report
    
    def print_results_table(self, report: TestReport):
        """Print formatted results table."""
        print("\n" + "=" * 100)
        print(f"{'SKILL ID':<35} {'TIER':<8} {'PRICE':<8} {'STATUS':<8} {'TIME(ms)':<10} {'RETRIES':<8}")
        print("-" * 100)
        
        for result in report.results:
            price = result.price_usdc or "FREE"
            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"{result.skill_id:<35} {result.tier:<8} {price:<8} "
                  f"{status_icon} {result.status:<6} {result.response_time_ms:<10.1f} {result.retries:<8}")
            
            if result.error_message:
                print(f"   ⚠️  {result.error_message[:80]}")
        
        print("=" * 100)
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {report.total_tests}")
        print(f"   ✅ Passed: {report.passed}")
        print(f"   ❌ Failed: {report.failed}")
        print(f"   📈 Pass Rate: {report.summary['pass_rate_percent']}%")
        print(f"   ⏱️  Total Time: {report.summary['total_execution_time_sec']}s")
        print(f"   💰 x402 Payments Simulated: {report.summary['x402_payments_simulated']}")
        print(f"\n📁 Report saved to: ./a2a_test_report.json")
    
    def save_report(self, report: TestReport):
        """Save report to JSON file."""
        report_dict = {
            "timestamp": report.timestamp,
            "endpoint": report.endpoint,
            "total_tests": report.total_tests,
            "passed": report.passed,
            "failed": report.failed,
            "summary": report.summary,
            "results": [
                {
                    "skill_id": r.skill_id,
                    "tier": r.tier,
                    "price_usdc": r.price_usdc,
                    "status": r.status,
                    "response_time_ms": r.response_time_ms,
                    "payment_simulated": r.payment_simulated,
                    "retries": r.retries,
                    "error_message": r.error_message,
                    "response_preview": str(r.response_data)[:500] if r.response_data else None
                }
                for r in report.results
            ]
        }
        
        output_path = Path("./a2a_test_report.json")
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        return output_path


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("   AlleyBot A2A Skill Validation Suite v1.0")
    print("   Testing 15 skills against production endpoint")
    print("=" * 80 + "\n")
    
    try:
        async with A2ASkillTester() as tester:
            report = await tester.run_all_tests()
            tester.print_results_table(report)
            output_file = tester.save_report(report)
            
            # Exit with appropriate code for CI/CD
            if report.failed > 0:
                print(f"\n⚠️  {report.failed} test(s) failed")
                sys.exit(1)
            else:
                print("\n🎉 All tests passed!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
