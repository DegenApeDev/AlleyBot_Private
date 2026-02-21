"""
Security checks for Base Yield Hunter
Rug pull detection, contract verification, and safety analysis
"""
import os
import json
import aiohttp
from typing import Dict, List, Any, Set, Optional
from datetime import datetime, timedelta


class SecurityChecker:
    """Security analysis for DeFi pools and contracts"""
    
    def __init__(self):
        # Known rug projects and suspicious addresses
        self.rug_blocklist: Set[str] = set()
        self.suspicious_contracts: Set[str] = set()
        self.verified_contracts: Set[str] = set()
        
        # Load blocklists
        self._load_blocklists()
    
    def _load_blocklists(self):
        """Load known malicious addresses and projects"""
        # Known rug projects (simplified example)
        known_rugs = {
            '0x1234567890123456789012345678901234567890',  # Example rug contract
            # Add more known malicious contracts as needed
        }
        
        self.rug_blocklist.update(known_rugs)
    
    async def check_contract_reputation(self, contract_address: str) -> Dict[str, Any]:
        """Check contract reputation against various sources"""
        reputation = {
            'is_rug': False,
            'is_suspicious': False,
            'is_verified': False,
            'warnings': [],
            'confidence': 0.0
        }
        
        # Check against blocklist
        if contract_address.lower() in [addr.lower() for addr in self.rug_blocklist]:
            reputation['is_rug'] = True
            reputation['warnings'].append('Contract is on known rug pull blocklist')
            reputation['confidence'] = 1.0
            return reputation
        
        # Check for suspicious patterns
        if self._has_suspicious_patterns(contract_address):
            reputation['is_suspicious'] = True
            reputation['warnings'].append('Contract shows suspicious patterns')
            reputation['confidence'] = 0.7
        
        # Check verification status
        verification = await self._check_contract_verification(contract_address)
        reputation['is_verified'] = verification.get('verified', False)
        if not verification.get('verified', False):
            reputation['warnings'].append('Contract is not verified')
            reputation['confidence'] = max(reputation['confidence'], 0.3)
        
        return reputation
    
    def _has_suspicious_patterns(self, contract_address: str) -> bool:
        """Check for suspicious patterns in contract address"""
        # Simple heuristics for suspicious contracts
        suspicious_patterns = [
            '000000',  # Many zeros might indicate placeholder
            'dead',    # Dead address patterns
            'bad'      # Obviously bad patterns
        ]
        
        address_lower = contract_address.lower()
        return any(pattern in address_lower for pattern in suspicious_patterns)
    
    async def _check_contract_verification(self, contract_address: str) -> Dict[str, Any]:
        """Check if contract is verified on BaseScan"""
        try:
            if not os.getenv('BASESCAN_API_KEY'):
                return {'verified': False, 'reason': 'No API key'}
            
            url = "https://api.basescan.org/api"
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': contract_address,
                'apikey': os.getenv('BASESCAN_API_KEY')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {'verified': False, 'reason': 'API error'}
                    
                    data = await response.json()
                    result = data.get('result', [])
                    
                    if result and len(result) > 0:
                        contract_data = result[0]
                        is_verified = contract_data.get('IsVerification', '0') == '1'
                        
                        return {
                            'verified': is_verified,
                            'contract_name': contract_data.get('ContractName', ''),
                            'compiler_version': contract_data.get('CompilerVersion', ''),
                            'source_code_length': len(contract_data.get('SourceCode', ''))
                        }
                    
                    return {'verified': False, 'reason': 'Contract not found'}
                    
        except Exception as e:
            return {'verified': False, 'reason': f'Error: {str(e)}'}
    
    async def analyze_liquidity_locks(self, contract_address: str) -> Dict[str, Any]:
        """Analyze liquidity locks for the pool"""
        # This would integrate with liquidity lock analyzers
        # For now, return basic analysis
        
        return {
            'has_liquidity_lock': False,
            'lock_duration_days': 0,
            'locked_percentage': 0,
            'lock_contract': None,
            'warnings': ['Liquidity lock analysis not implemented']
        }
    
    def check_gas_anomalies(self, gas_price: float, historical_avg: float = None) -> Dict[str, Any]:
        """Check for gas price anomalies that might indicate MEV or network congestion"""
        warnings = []
        
        if gas_price > 100:
            warnings.append('Very high gas price - possible MEV activity')
        elif gas_price > 50:
            warnings.append('High gas price - network congestion')
        
        # Check against historical average if available
        if historical_avg and gas_price > historical_avg * 3:
            warnings.append('Gas price significantly above historical average')
        
        return {
            'is_anomalous': len(warnings) > 0,
            'warnings': warnings,
            'severity': 'high' if gas_price > 100 else 'medium' if gas_price > 50 else 'low'
        }
    
    async def comprehensive_security_check(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive security analysis on a pool"""
        contract_address = pool_data.get('address', '')
        
        # Contract reputation
        reputation = await self.check_contract_reputation(contract_address)
        
        # Liquidity analysis
        liquidity = await self.analyze_liquidity_locks(contract_address)
        
        # TVL and age analysis
        tvl_usd = pool_data.get('tvlUsd', 0)
        security_score = self._calculate_security_score(reputation, liquidity, tvl_usd)
        
        return {
            'security_score': security_score,
            'reputation': reputation,
            'liquidity': liquidity,
            'recommendation': self._get_security_recommendation(security_score),
            'warnings': reputation.get('warnings', []) + liquidity.get('warnings', [])
        }
    
    def _calculate_security_score(self, reputation: Dict, liquidity: Dict, tvl_usd: float) -> float:
        """Calculate overall security score (0-100, higher = more secure)"""
        score = 50.0  # Base score
        
        # Reputation factors
        if reputation.get('is_rug'):
            score -= 80
        elif reputation.get('is_suspicious'):
            score -= 40
        
        if reputation.get('is_verified'):
            score += 20
        
        # TVL factor
        if tvl_usd > 1000000:
            score += 15
        elif tvl_usd > 100000:
            score += 10
        elif tvl_usd < 10000:
            score -= 20
        
        # Liquidity locks
        if liquidity.get('has_liquidity_lock'):
            score += 15
            if liquidity.get('lock_duration_days', 0) > 365:
                score += 10
        
        return max(0, min(100, score))
    
    def _get_security_recommendation(self, security_score: float) -> str:
        """Get security recommendation based on score"""
        if security_score >= 80:
            return "SAFE - Low risk, appears secure"
        elif security_score >= 60:
            return "CAUTION - Medium risk, do your own research"
        elif security_score >= 40:
            return "RISKY - High risk, not recommended"
        else:
            return "DANGER - Very high risk, avoid"


# Global security checker instance
security_checker = SecurityChecker()
