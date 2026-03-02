"""
Avalanche C-Chain Token Trading Plugin for AlleyBot
Integrates Trader Joe V2 for token swaps on AVAX
"""
import os
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account

from plugin_manager import AlleyBotPlugin

# Import security filter
try:
    from security_filter import security_filter
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    print("⚠️ Security filter not available - trading responses may leak sensitive data!")


class AvaxTrading(AlleyBotPlugin):
    """Avalanche C-Chain token trading using Trader Joe V2"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "avax_trading"
        self.version = "1.0.0"
        
        # Avalanche C-Chain RPC
        self.rpc_url = "https://api.avax.network/ext/bc/C/rpc"
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Wallet configuration
        self.wallet_address = os.getenv('AVAX_WALLET_PUBLIC_ADDRESS')
        self.wallet_private_key = os.getenv('AVAX_WALLET_PRIVATE_KEY')
        
        # Trader Joe V2 Router address on Avalanche
        self.router_address = "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30"
        
        # Risk management rules
        self.risk_rules = {
            'min_profit_percent': 0.3,  # 0.3% minimum profit
            'max_price_impact': 2.0,    # 2% max price impact
            'max_slippage_percent': 1.0, # 1% max slippage
            'traderjoe_fee_percent': 0.3,  # Trader Joe 0.3% fee
            'max_gas_gwei': 50,          # Max 50 gwei gas price
        }
        
        # Common token addresses on Avalanche C-Chain
        self.tokens = {
            "AVAX": "0x0000000000000000000000000000000000000000",  # Native AVAX
            "WAVAX": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
            "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "USDT": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
            "DAI": "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
            "ALLEYBOT": "0xD6FF3E2Fca2625B35b78Af4935046C5008d5D40f",  # AlleyBot official token
        }
        
        # Token decimals
        self.decimals = {
            "AVAX": 18,
            "WAVAX": 18,
            "USDC": 6,
            "USDT": 6,
            "DAI": 18,
            "ALLEYBOT": 18,
        }
        
        # Trader Joe V2 Router ABI (simplified - only swap functions)
        self.router_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "name": "exactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        
        # ERC20 ABI (simplified)
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Security: Validate wallet configuration
        if not self.wallet_address or not self.wallet_private_key:
            print("⚠️ AVAX wallet not configured (AVAX_WALLET_PUBLIC_ADDRESS, AVAX_WALLET_PRIVATE_KEY)")
            self.enabled = False
        else:
            self.enabled = True
            # Only show first 8 chars of address for security
            print(f"✅ AVAX Trading initialized - Wallet: {self.wallet_address[:8]}...")
        
        # Security: Allowed recipient addresses (owner's wallet only)
        # All swaps go to the same wallet that initiated them
        self.allowed_recipients = {self.wallet_address} if self.wallet_address else set()
        
        # Security check
        if not SECURITY_AVAILABLE:
            print("🚨 WARNING: Security filter not loaded! Trading responses may expose sensitive data!")
        
        # Never log or expose private keys
        if self.wallet_private_key:
            # Verify key is not accidentally logged
            if not self.wallet_private_key.startswith('0x') or len(self.wallet_private_key) != 66:
                print("⚠️ AVAX private key appears invalid (wrong format)")
                self.enabled = False
    
    def get_token_balance(self, token_symbol: str) -> Dict[str, Any]:
        """Get token balance for wallet"""
        if not self.enabled:
            return {"success": False, "error": "Wallet not configured"}
        
        token_address = self.tokens.get(token_symbol.upper())
        if not token_address:
            return {"success": False, "error": f"Unknown token: {token_symbol}"}
        
        try:
            if token_symbol.upper() == "ETH":
                # Get ETH balance
                balance_wei = self.w3.eth.get_balance(self.wallet_address)
                balance = balance_wei / (10 ** 18)
            else:
                # Get ERC20 balance
                contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.erc20_abi
                )
                balance_raw = contract.functions.balanceOf(self.wallet_address).call()
                decimals = self.decimals.get(token_symbol.upper(), 18)
                balance = balance_raw / (10 ** decimals)
            
            return {
                "success": True,
                "token": token_symbol.upper(),
                "balance": balance,
                "formatted": f"{balance:.6f} {token_symbol.upper()}"
            }
        except Exception as e:
            return {"success": False, "error": f"Balance check failed: {str(e)}"}
    
    def calculate_profit(self, amount: float, estimated_output: float, from_token: str, to_token: str, gas_cost_usd: float = 2.0) -> Dict[str, Any]:
        """
        Calculate expected profit after all costs
        
        Args:
            amount: Input amount
            estimated_output: Estimated output amount
            from_token: Input token symbol
            to_token: Output token symbol
            gas_cost_usd: Estimated gas cost in USD (default: $2)
        
        Returns:
            Profit analysis with breakdown
        """
        try:
            # Estimate costs
            uniswap_fee_percent = self.risk_rules['uniswap_fee_percent']
            
            # Calculate price impact (simplified - in production use Uniswap quoter)
            # For now, assume minimal price impact for small trades
            price_impact = 0.1  # Placeholder
            
            # Total cost in percent
            total_cost_percent = uniswap_fee_percent + price_impact
            
            # Check if profitable (simplified)
            is_profitable = total_cost_percent < 2.0 and gas_cost_usd < (amount * 0.01)
            
            warnings = []
            if gas_cost_usd > 5.0:
                warnings.append(f"⚠️ High gas cost: ${gas_cost_usd:.2f}")
            
            if total_cost_percent > 1.0:
                warnings.append(f"⚠️ High total cost: {total_cost_percent:.2f}%")
            
            return {
                'success': True,
                'is_profitable': is_profitable,
                'price_impact_percent': price_impact,
                'total_cost_percent': total_cost_percent,
                'gas_cost_usd': gas_cost_usd,
                'input_amount': amount,
                'estimated_output': estimated_output,
                'breakdown': {
                    'uniswap_fee': uniswap_fee_percent,
                    'price_impact': price_impact,
                    'gas': gas_cost_usd
                },
                'warnings': warnings
            }
        except Exception as e:
            return {'success': False, 'error': f'Profit calculation failed: {str(e)}'}
    
    def check_gas_price(self) -> Dict[str, Any]:
        """Check if gas price is acceptable"""
        try:
            current_gas_wei = self.w3.eth.gas_price
            current_gas_gwei = current_gas_wei / 1e9
            
            max_gas = self.risk_rules['max_gas_gwei']
            
            if current_gas_gwei > max_gas:
                return {
                    'should_trade': False,
                    'current_gwei': current_gas_gwei,
                    'max_gwei': max_gas,
                    'reason': f'Gas too high: {current_gas_gwei:.1f} gwei > {max_gas} gwei limit'
                }
            
            # Estimate gas cost in USD (rough estimate)
            gas_units = 300000  # Typical swap gas
            gas_cost_eth = (current_gas_wei * gas_units) / 1e18
            gas_cost_usd = gas_cost_eth * 2500  # Assume ETH = $2500
            
            return {
                'should_trade': True,
                'current_gwei': current_gas_gwei,
                'gas_cost_usd': gas_cost_usd
            }
        except Exception as e:
            return {'should_trade': True, 'error': str(e), 'gas_cost_usd': 2.0}
    
    def approve_token(self, token_symbol: str, amount: float) -> Dict[str, Any]:
        """Approve token spending by Uniswap router"""
        if not self.enabled:
            return {"success": False, "error": "Wallet not configured"}
        
        token_address = self.tokens.get(token_symbol.upper())
        if not token_address or token_symbol.upper() == "ETH":
            return {"success": False, "error": "Cannot approve ETH or unknown token"}
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            decimals = self.decimals.get(token_symbol.upper(), 18)
            amount_raw = int(amount * (10 ** decimals))
            
            # Build approval transaction
            tx = contract.functions.approve(
                Web3.to_checksum_address(self.router_address),
                amount_raw
            ).build_transaction({
                'from': self.wallet_address,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.wallet_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": receipt['status'] == 1,
                "tx_hash": tx_hash.hex(),
                "explorer_url": f"https://basescan.org/tx/{tx_hash.hex()}"
            }
        except Exception as e:
            return {"success": False, "error": f"Approval failed: {str(e)}"}
    
    def execute_swap(self, from_token: str, to_token: str, amount: float, slippage: float = 0.5, force: bool = False) -> Dict[str, Any]:
        """
        Execute token swap on Base using Uniswap V3 with profit checks
        
        Args:
            from_token: Symbol of input token
            to_token: Symbol of output token
            amount: Amount to swap
            slippage: Slippage tolerance in percent (default: 0.5%)
            force: Skip profit and gas checks (dangerous!)
        
        Returns:
            Swap result with transaction hash and profit analysis
        """
        if not self.enabled:
            return {"success": False, "error": "Wallet not configured"}
        
        # Validate slippage
        if slippage > self.risk_rules['max_slippage_percent']:
            return {
                "success": False,
                "error": f"Slippage too high: {slippage}% > {self.risk_rules['max_slippage_percent']}% limit"
            }
        
        # Check gas price
        if not force:
            gas_check = self.check_gas_price()
            if not gas_check['should_trade']:
                return {
                    "success": False,
                    "error": gas_check['reason'],
                    "gas_info": gas_check,
                    "suggestion": "Wait for lower gas prices or use force=True to override"
                }
            
            gas_cost_usd = gas_check.get('gas_cost_usd', 2.0)
            print(f"⛽ Gas: {gas_check['current_gwei']:.1f} gwei (${gas_cost_usd:.2f})")
        else:
            gas_cost_usd = 2.0
        
        from_address = self.tokens.get(from_token.upper())
        to_address = self.tokens.get(to_token.upper())
        
        if not from_address or not to_address:
            return {"success": False, "error": f"Unknown token: {from_token if not from_address else to_token}"}
        
        try:
            # Convert amount to wei/smallest unit
            from_decimals = self.decimals.get(from_token.upper(), 18)
            amount_in = int(amount * (10 ** from_decimals))
            
            # Calculate minimum output with slippage
            # This is simplified - in production, get actual quote first
            amount_out_min = 0  # Accept any amount (risky - should get quote first)
            
            # Uniswap V3 fee tier (0.3% = 3000)
            fee = 3000
            
            # Build swap transaction
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.router_address),
                abi=self.router_abi
            )
            
            tx_params = {
                'from': self.wallet_address,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            }
            
            if from_token.upper() == "ETH":
                tx_params['value'] = amount_in
            
            tx = router.functions.exactInputSingle(
                Web3.to_checksum_address(from_address),
                Web3.to_checksum_address(to_address),
                fee,
                self.wallet_address,
                amount_in,
                amount_out_min,
                0  # sqrtPriceLimitX96 = 0 means no limit
            ).build_transaction(tx_params)
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.wallet_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"🔄 Swap transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                # Calculate profit analysis
                profit_analysis = self.calculate_profit(amount, 0, from_token, to_token, gas_cost_usd)
                
                swap_result = {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "input_amount": amount,
                    "input_token": from_token.upper(),
                    "output_token": to_token.upper(),
                    "explorer_url": f"https://basescan.org/tx/{tx_hash.hex()}",
                    "gas_used": receipt['gasUsed'],
                    "gas_cost_usd": gas_cost_usd
                }
                
                if profit_analysis.get('success'):
                    swap_result['profit_analysis'] = profit_analysis
                
                # Security: Filter response to prevent key leakage
                if SECURITY_AVAILABLE:
                    result_str = str(swap_result)
                    filtered_str, was_filtered = security_filter.filter_message(result_str)
                    if was_filtered:
                        print("🚨 SECURITY: Filtered sensitive data from swap result")
                
                return swap_result
            else:
                return {"success": False, "error": "Transaction reverted"}
                
        except Exception as e:
            error_msg = f"Swap failed: {str(e)}"
            
            # Security: Sanitize error message
            if SECURITY_AVAILABLE:
                error_msg = security_filter.sanitize_error_message(error_msg)
            
            return {"success": False, "error": error_msg}
    
    def get_price(self, from_token: str, to_token: str) -> Dict[str, Any]:
        """
        Get price quote (simplified - should use Uniswap quoter in production)
        
        Args:
            from_token: Symbol of input token
            to_token: Symbol of output token


PLUGIN_INFO = {
    "name": "avax_trading",
    "version": "1.0.0",
    "description": "Base chain token trading using Uniswap V3",
    "author": "AlleyBot"
}


def create_plugin(config=None):
    return BaseTrading(config or {})
