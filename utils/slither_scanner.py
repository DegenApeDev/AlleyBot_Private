"""
Slither Security Scanner Integration
Real static analysis for smart contracts using Trail of Bits Slither
"""
import os
import json
import tempfile
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path


class SlitherScanner:
    """Wrapper for Slither static analysis tool"""
    
    def __init__(self):
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY', '')
        self.basescan_api_key = os.getenv('BASESCAN_API_KEY', '')
        
    def is_available(self) -> bool:
        """Check if slither is installed and available"""
        try:
            result = subprocess.run(
                ['slither', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def fetch_contract_source(self, address: str, chain: str = 'base') -> Optional[Dict]:
        """Fetch contract source code from block explorer"""
        import requests
        
        if chain.lower() == 'base':
            api_key = self.basescan_api_key
            base_url = 'https://api.basescan.org/api'
        else:
            api_key = self.etherscan_api_key
            base_url = 'https://api.etherscan.io/api'
        
        if not api_key:
            return None
        
        try:
            url = f"{base_url}?module=contract&action=getsourcecode&address={address}&apikey={api_key}"
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if data.get('status') == '1' and data.get('result'):
                result = data['result'][0]
                if result.get('SourceCode'):
                    return {
                        'source': result['SourceCode'],
                        'abi': result.get('ABI', ''),
                        'contract_name': result.get('ContractName', 'Unknown'),
                        'compiler_version': result.get('CompilerVersion', ''),
                        'optimization_used': result.get('OptimizationUsed', ''),
                        'runs': result.get('Runs', ''),
                        'verified': True
                    }
            return None
        except Exception as e:
            print(f"⚠️ Failed to fetch contract source: {e}")
            return None
    
    def scan_contract(self, address: str, chain: str = 'base', 
                      deep_scan: bool = False) -> Dict[str, Any]:
        """
        Run Slither analysis on a contract
        
        Args:
            address: Contract address
            chain: 'base' or 'ethereum'
            deep_scan: Include more detectors and longer timeout
            
        Returns:
            Dict with findings, severity counts, and recommendations
        """
        if not self.is_available():
            return {
                'error': 'Slither not installed. Run: pip install slither-analyzer',
                'address': address,
                'scan_type': 'slither'
            }
        
        # Fetch source code
        contract_info = self.fetch_contract_source(address, chain)
        
        if not contract_info:
            # Fallback: do basic bytecode analysis
            return self._bytecode_fallback_scan(address, chain)
        
        # Create temp directory for contract files
        with tempfile.TemporaryDirectory() as temp_dir:
            contract_path = Path(temp_dir) / f"{address}.sol"
            
            # Handle multi-file contracts (flattened or JSON)
            source = contract_info['source']
            if source.startswith('{') and source.endswith('}'):
                # Multi-file JSON format
                try:
                    source_json = json.loads(source)
                    # Write each file
                    for filename, content in source_json.items():
                        file_path = Path(temp_dir) / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content)
                    # Use first file as main
                    contract_path = Path(temp_dir) / list(source_json.keys())[0]
                except json.JSONDecodeError:
                    contract_path.write_text(source)
            else:
                contract_path.write_text(source)
            
            # Run Slither
            try:
                cmd = [
                    'slither',
                    str(contract_path),
                    '--json', '-',
                    '--filter-paths', 'node_modules|lib|test|mock',
                    '--exclude-informational' if not deep_scan else '',
                ]
                # Remove empty strings
                cmd = [c for c in cmd if c]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120 if deep_scan else 60,
                    cwd=temp_dir
                )
                
                # Parse results
                findings = []
                severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
                
                try:
                    slither_output = json.loads(result.stdout)
                    
                    for detector in slither_output.get('detectors', []):
                        severity = detector.get('impact', 'medium').lower()
                        if severity in severity_counts:
                            severity_counts[severity] += 1
                        
                        finding = {
                            'severity': severity,
                            'title': detector.get('check', 'Unknown issue'),
                            'description': detector.get('description', 'No description'),
                            'confidence': detector.get('confidence', 'Medium'),
                            'lines': detector.get('elements', [{}])[0].get('source_mapping', {}).get('lines', []),
                        }
                        findings.append(finding)
                except json.JSONDecodeError:
                    pass
                
                # Risk scoring
                risk_score = 'low'
                if severity_counts['critical'] > 0 or severity_counts['high'] > 0:
                    risk_score = 'high'
                elif severity_counts['medium'] > 0:
                    risk_score = 'medium'
                
                return {
                    'address': address,
                    'chain': chain,
                    'contract_name': contract_info['contract_name'],
                    'verified': True,
                    'findings': findings,
                    'severity_counts': severity_counts,
                    'risk_score': risk_score,
                    'total_findings': len(findings),
                    'scan_type': 'slither',
                    'deep_scan': deep_scan,
                    'compiler_version': contract_info.get('compiler_version', ''),
                    'slither_available': True,
                    'scan_timestamp': str(datetime.utcnow().isoformat()) + 'Z',
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'address': address,
                    'error': 'Slither scan timed out (contract too complex)',
                    'scan_type': 'slither',
                    'slither_available': True,
                }
            except Exception as e:
                return {
                    'address': address,
                    'error': f'Slither scan failed: {str(e)}',
                    'scan_type': 'slither',
                    'slither_available': True,
                }
    
    def _bytecode_fallback_scan(self, address: str, chain: str) -> Dict:
        """Fallback scan when source code not available - improved opcode detection"""
        try:
            from web3 import Web3
            import re
            
            # Connect to appropriate RPC
            if chain.lower() == 'base':
                rpc = os.getenv('BASE_RPC', 'https://mainnet.base.org')
            else:
                rpc = os.getenv('ETH_RPC', 'https://eth.llamarpc.com')
            
            w3 = Web3(Web3.HTTPProvider(rpc))
            
            # Get bytecode
            code = w3.eth.get_code(Web3.to_checksum_address(address))
            
            if code == b'':
                return {
                    'address': address,
                    'error': 'No contract found at this address (EOA or wrong chain)',
                    'scan_type': 'bytecode_fallback',
                }
            
            # Basic bytecode analysis with proper opcode detection
            findings = []
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            
            code_hex = code.hex()
            
            # Convert to bytes for proper analysis
            code_bytes = bytes.fromhex(code_hex)
            
            # Look for SELFDESTRUCT opcode (0xff) - check it's actually an opcode, not data
            # Pattern: 0xff preceded by valid push or standalone (not in PUSH data)
            selfdestruct_positions = []
            i = 0
            while i < len(code_bytes):
                byte = code_bytes[i]
                if byte == 0xff:
                    # Check if preceded by valid opcode that could lead to SELFDESTRUCT
                    # This is a heuristic - proper disassembly would be better
                    selfdestruct_positions.append(i)
                    i += 1
                elif 0x60 <= byte <= 0x7f:  # PUSH1-PUSH32
                    # Skip PUSH data
                    push_size = byte - 0x60 + 1
                    i += push_size + 1
                else:
                    i += 1
            
            # Check for DELEGATECALL opcode (0xf4) with same logic
            delegatecall_positions = []
            i = 0
            while i < len(code_bytes):
                byte = code_bytes[i]
                if byte == 0xf4:
                    delegatecall_positions.append(i)
                    i += 1
                elif 0x60 <= byte <= 0x7f:  # PUSH1-PUSH32
                    push_size = byte - 0x60 + 1
                    i += push_size + 1
                else:
                    i += 1
            
            # Additional checks - look for proxy patterns
            # EIP-1167 minimal proxy: 363d3d373d3d3d363d73...5af43d82803e903d91602b57fd5bf3
            eip1167_pattern = b'\x36\x3d\x3d\x37\x3d\x3d\x3d\x36\x3d\x73'
            is_eip1167_proxy = eip1167_pattern in code_bytes
            
            # OpenZeppelin proxy pattern detection
            oz_proxy_pattern = b'\x36\x82\x80\x37\x90\x3d\x91\x60'
            is_oz_proxy = oz_proxy_pattern in code_bytes
            
            # Report findings with more context
            if is_eip1167_proxy:
                findings.append({
                    'severity': 'low',
                    'title': 'EIP-1167 Minimal Proxy detected',
                    'description': 'Contract is a minimal proxy (clone) pattern - delegates calls to implementation'
                })
                severity_counts['low'] += 1
            elif is_oz_proxy:
                findings.append({
                    'severity': 'low',
                    'title': 'OpenZeppelin proxy pattern detected',
                    'description': 'Contract uses OpenZeppelin upgradeable proxy pattern'
                })
                severity_counts['low'] += 1
            
            # Only report SELFDESTRUCT if it appears in execution flow (not in push data)
            # Heuristic: if SELFDESTRUCT appears multiple times, likely real
            if len(selfdestruct_positions) >= 2:
                findings.append({
                    'severity': 'medium',
                    'title': 'Self-destruct capability detected',
                    'description': f'Contract contains SELFDESTRUCT opcode ({len(selfdestruct_positions)} occurrences) - can be destroyed by authorized party'
                })
                severity_counts['medium'] += 1
            
            # Only report DELEGATECALL if it appears multiple times (proxy pattern)
            if len(delegatecall_positions) >= 2:
                findings.append({
                    'severity': 'high' if not (is_eip1167_proxy or is_oz_proxy) else 'medium',
                    'title': 'DELEGATECALL detected',
                    'description': f'Contract uses DELEGATECALL ({len(delegatecall_positions)} occurrences) - could be proxy pattern or potential vulnerability'
                })
                if not (is_eip1167_proxy or is_oz_proxy):
                    severity_counts['high'] += 1
                else:
                    severity_counts['medium'] += 1
            
            # Contract size check
            contract_size_kb = len(code_bytes) / 1024
            if contract_size_kb > 24:  # Close to 24KB limit
                findings.append({
                    'severity': 'low',
                    'title': 'Large contract size',
                    'description': f'Contract is {contract_size_kb:.1f}KB - approaching 24KB limit'
                })
                severity_counts['low'] += 1
            
            # Risk scoring
            risk_score = 'low'
            if severity_counts['critical'] > 0 or severity_counts['high'] > 0:
                risk_score = 'high'
            elif severity_counts['medium'] > 0:
                risk_score = 'medium'
            
            return {
                'address': address,
                'chain': chain,
                'verified': False,
                'findings': findings,
                'severity_counts': severity_counts,
                'risk_score': risk_score,
                'total_findings': len(findings),
                'scan_type': 'bytecode_fallback',
                'contract_size_kb': round(contract_size_kb, 2),
                'note': 'Contract source code not verified on explorer - limited analysis. For full Slither analysis, verify contract on block explorer.',
                'slither_available': True,
            }
            
        except Exception as e:
            return {
                'address': address,
                'error': f'Bytecode analysis failed: {str(e)}',
                'scan_type': 'bytecode_fallback',
            }


# Global instance
_slither_scanner = None

def get_slither_scanner() -> SlitherScanner:
    """Get or create global SlitherScanner instance"""
    global _slither_scanner
    if _slither_scanner is None:
        _slither_scanner = SlitherScanner()
    return _slither_scanner
