"""
Base Yield Hunter Plugin for AlleyBot
Automated Base network yield farming opportunities scanner and analyzer
"""
import os
import sys
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin


class BaseYieldHunterPlugin(AlleyBotPlugin):
    """Plugin for scanning and analyzing Base network yield opportunities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.name = "base_yield_hunter"
        self.version = "1.0.0"
        self.description = "Automated Base network yield farming scanner and analyzer"
        
        # Configuration with safe defaults
        config = config or {}
        self.min_tvl_usd = config.get('min_tvl_usd', 10000)  # Minimum TVL threshold
        self.min_apy = config.get('min_apy', 1.0)  # Minimum APY threshold
        self.max_gas_price = config.get('max_gas_price', 100)  # Max gas price in gwei
        
        # Security settings
        self.rug_blocklist = config.get('rug_blocklist', [])
        self.verified_contracts_only = config.get('verified_contracts_only', True)
        
        # Cache
        self._pool_cache = {}
        self._last_scan = None
        
        # API endpoints
        self.defillama_api = "https://yields.llama.fi/pools"
        self.basescan_api = "https://api.basescan.org/api"
        self.base_rpc = "https://mainnet.base.org"
        
    async def fetch_base_pools(self) -> List[Dict[str, Any]]:
        """Fetch Base network pools from DefiLlama API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all pools, then filter for Base
                async with session.get(self.defillama_api) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    pools = data.get('data', [])
                    
                    # Filter for Base network pools
                    base_pools = []
                    for pool in pools:
                        if pool.get('chain') == 'Base':
                            # Apply basic filters
                            tvl_usd = pool.get('tvlUsd', 0)
                            apy = pool.get('apy', 0)
                            
                            if (tvl_usd >= self.min_tvl_usd and 
                                apy >= self.min_apy and
                                pool.get('project', '').lower() not in ['rug', 'scam']):
                                base_pools.append(pool)
                    
                    # Sort by APY descending
                    base_pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
                    return base_pools
                    
        except Exception as e:
            print(f"❌ Error fetching Base pools: {e}")
            return []
    
    async def verify_contract_security(self, contract_address: str) -> Dict[str, Any]:
        """Verify contract security on BaseScan"""
        try:
            if not self.basescan_api or not os.getenv('BASESCAN_API_KEY'):
                return {'verified': False, 'reason': 'No BaseScan API key'}
            
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': contract_address,
                'apikey': os.getenv('BASESCAN_API_KEY')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.basescan_api, params=params) as response:
                    if response.status != 200:
                        return {'verified': False, 'reason': 'API request failed'}
                    
                    data = await response.json()
                    result = data.get('result', [])
                    
                    if result and len(result) > 0:
                        contract_data = result[0]
                        is_verified = contract_data.get('IsVerification', '0') == '1'
                        
                        return {
                            'verified': is_verified,
                            'source_code': contract_data.get('SourceCode', ''),
                            'contract_name': contract_data.get('ContractName', ''),
                            'compiler_version': contract_data.get('CompilerVersion', '')
                        }
                    
                    return {'verified': False, 'reason': 'Contract not found'}
                    
        except Exception as e:
            return {'verified': False, 'reason': f'Error: {str(e)}'}
    
    async def check_gas_prices(self) -> Dict[str, Any]:
        """Check current gas prices on Base"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_gasPrice",
                    "params": [],
                    "id": 1
                }
                
                async with session.post(self.base_rpc, json=payload) as response:
                    if response.status != 200:
                        return {'gas_price': 0, 'status': 'error'}
                    
                    data = await response.json()
                    gas_price_hex = data.get('result', '0x0')
                    gas_price_wei = int(gas_price_hex, 16)
                    gas_price_gwei = gas_price_wei / 1e9
                    
                    return {
                        'gas_price': gas_price_gwei,
                        'gas_price_wei': gas_price_wei,
                        'status': 'ok'
                    }
                    
        except Exception as e:
            return {'gas_price': 0, 'status': f'error: {str(e)}'}
    
    def calculate_risk_score(self, pool: Dict[str, Any]) -> float:
        """Calculate risk score for a pool (0-100, higher = riskier)"""
        risk_score = 0.0
        
        # TVL risk (lower TVL = higher risk)
        tvl_usd = pool.get('tvlUsd', 0)
        if tvl_usd < 50000:
            risk_score += 30
        elif tvl_usd < 100000:
            risk_score += 20
        elif tvl_usd < 500000:
            risk_score += 10
        
        # APY risk (very high APY = higher risk)
        apy = pool.get('apy', 0)
        if apy > 50:
            risk_score += 25
        elif apy > 20:
            risk_score += 15
        elif apy > 10:
            risk_score += 5
        
        # Project risk
        project = pool.get('project', '').lower()
        high_risk_projects = ['new', 'unknown', 'unaudited']
        if any(risk_word in project for risk_word in high_risk_projects):
            risk_score += 20
        
        # Pool type risk
        pool_type = pool.get('pool', '').lower()
        if 'leveraged' in pool_type or 'lever' in pool_type:
            risk_score += 15
        elif 'experimental' in pool_type:
            risk_score += 10
        
        return min(risk_score, 100)
    
    async def scan_yield_opportunities(self) -> Dict[str, Any]:
        """Main scan function for yield opportunities"""
        print("🔍 Starting Base yield scan...")
        
        # Check gas prices
        gas_info = await self.check_gas_prices()
        if gas_info['status'] != 'ok' or gas_info['gas_price'] > self.max_gas_price:
            return {
                'success': False,
                'error': f"Gas price too high: {gas_info.get('gas_price', 0)} gwei",
                'pools': []
            }
        
        # Fetch pools
        pools = await self.fetch_base_pools()
        if not pools:
            return {
                'success': False,
                'error': "No pools found or API error",
                'pools': []
            }
        
        # Analyze pools
        analyzed_pools = []
        for pool in pools[:20]:  # Top 20 pools
            # Calculate risk score
            risk_score = self.calculate_risk_score(pool)
            
            # Get contract address for verification
            contract_address = pool.get('address', '')
            security_info = {'verified': False, 'reason': 'No contract address'}
            
            if contract_address and self.verified_contracts_only:
                security_info = await self.verify_contract_security(contract_address)
            
            # Skip if verification required but not verified
            if self.verified_contracts_only and not security_info['verified']:
                continue
            
            pool_analysis = {
                **pool,
                'risk_score': risk_score,
                'security': security_info,
                'recommended': risk_score < 40 and pool.get('apy', 0) > self.min_apy
            }
            
            analyzed_pools.append(pool_analysis)
        
        # Sort by risk-adjusted APY
        analyzed_pools.sort(key=lambda x: (x.get('apy', 0) * (1 - x.get('risk_score', 0) / 100)), reverse=True)
        
        self._pool_cache = analyzed_pools
        self._last_scan = datetime.now()
        
        print(f"✅ Scan complete: {len(analyzed_pools)} pools analyzed")
        
        return {
            'success': True,
            'pools': analyzed_pools[:10],  # Top 10 pools
            'scan_time': self._last_scan.isoformat(),
            'gas_price': gas_info.get('gas_price', 0)
        }
    
    def format_pool_info(self, pool: Dict[str, Any]) -> str:
        """Format pool information for display"""
        symbol = pool.get('symbol', 'UNKNOWN')
        apy = pool.get('apy', 0)
        tvl_usd = pool.get('tvlUsd', 0)
        project = pool.get('project', 'Unknown')
        risk_score = pool.get('risk_score', 0)
        
        # Risk emoji
        if risk_score < 20:
            risk_emoji = "🟢 Low Risk"
        elif risk_score < 40:
            risk_emoji = "🟡 Medium Risk"
        elif risk_score < 60:
            risk_emoji = "🟠 High Risk"
        else:
            risk_emoji = "🔴 Very High Risk"
        
        # Security check
        security = pool.get('security', {})
        verified_emoji = "✅" if security.get('verified') else "❌"
        
        info = f"🏊 **{symbol}** - {project}\n"
        info += f"   💰 APY: {apy:.2f}%\n"
        info += f"   💎 TVL: ${tvl_usd:,.0f}\n"
        info += f"   {risk_emoji} ({risk_score}/100)\n"
        info += f"   {verified_emoji} Contract Verified\n"
        
        return info
    
    # Command implementations
    def yieldhunt_command(self, *args) -> str:
        """Scan for Base yield opportunities"""
        try:
            # Run async scan
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.scan_yield_opportunities())
            loop.close()
            
            if not result.get('success'):
                return f"❌ Yield scan failed: {result.get('error', 'Unknown error')}"
            
            pools = result.get('pools', [])
            if not pools:
                return "📭 No high-quality yield opportunities found on Base"
            
            response = f"🏹 **Base Yield Hunter Results**\n"
            response += f"{'='*40}\n"
            response += f"🔍 Scanned: {len(pools)} top pools\n"
            response += f"⛽ Gas: {result.get('gas_price', 0):.1f} gwei\n"
            response += f"⏰ Scan: {result.get('scan_time', 'Unknown')}\n\n"
            
            # Show top 3 pools
            for i, pool in enumerate(pools[:3], 1):
                response += f"🥇 **Pool #{i}**\n"
                response += self.format_pool_info(pool)
                response += "\n"
            
            if len(pools) > 3:
                response += f"📊 {len(pools) - 3} more pools available...\n"
            
            return response
            
        except Exception as e:
            return f"❌ Error during yield scan: {str(e)}"
    
    def yieldstats_command(self, *args) -> str:
        """Show yield hunting statistics"""
        if not self._last_scan:
            return "📊 No scan data available. Run /yieldhunt first."
        
        pools = self._pool_cache
        if not pools:
            return "📊 No pool data available."
        
        # Calculate statistics
        total_tvl = sum(p.get('tvlUsd', 0) for p in pools)
        avg_apy = sum(p.get('apy', 0) for p in pools) / len(pools)
        avg_risk = sum(p.get('risk_score', 0) for p in pools) / len(pools)
        recommended_count = sum(1 for p in pools if p.get('recommended', False))
        
        response = f"📊 **Base Yield Statistics**\n"
        response += f"{'='*30}\n"
        response += f"🏊 Pools Analyzed: {len(pools)}\n"
        response += f"💰 Total TVL: ${total_tvl:,.0f}\n"
        response += f"📈 Average APY: {avg_apy:.2f}%\n"
        response += f"⚠️  Average Risk: {avg_risk:.1f}/100\n"
        response += f"✅ Recommended: {recommended_count}/{len(pools)}\n"
        response += f"⏰ Last Scan: {self._last_scan.strftime('%H:%M:%S')}\n"
        
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'yieldhunt': self.yieldhunt_command,
            'yieldstats': self.yieldstats_command,
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any] = None) -> BaseYieldHunterPlugin:
    """Create plugin instance"""
    return BaseYieldHunterPlugin(config)


# Plugin metadata
PLUGIN_INFO = {
    "name": "base_yield_hunter",
    "version": "1.0.0",
    "description": "Automated Base network yield farming scanner and analyzer",
    "author": "AlleyBot",
    "dependencies": ["aiohttp"],
    "config_required": False,
    "config_schema": {
        "min_tvl_usd": {"type": "integer", "default": 10000, "description": "Minimum TVL threshold in USD"},
        "min_apy": {"type": "float", "default": 1.0, "description": "Minimum APY threshold"},
        "max_gas_price": {"type": "float", "default": 100, "description": "Maximum gas price in gwei"},
        "verified_contracts_only": {"type": "boolean", "default": True, "description": "Only show verified contracts"}
    }
}
