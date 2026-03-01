"""
Base Chain Token Trading Plugin for AlleyBot
Integrates Uniswap V3 for token swaps on Base
"""
import os
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account

from plugin_manager import AlleyBotPlugin


class BaseTrading(AlleyBotPlugin):
    """Base chain token trading using Uniswap V3"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "base_trading"
        self.version = "1.0.0"
        
        # Base chain RPC
        self.rpc_url = "https://mainnet.base.org"
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Wallet configuration
        self.wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        self.wallet_private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        
        # Uniswap V3 Router address on Base
        self.router_address = "0x2626664c2603336E57B271c5C0b26F421741e481"
        
        # Common token addresses on Base
        self.tokens = {
            "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",  # Bridged USDC
            "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        }
        
        # Token decimals
        self.decimals = {
            "ETH": 18,
            "WETH": 18,
            "USDC": 6,
            "USDbC": 6,
            "DAI": 18,
        }
        
        # Uniswap V3 Router ABI (simplified - only swap functions)
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
        
        if not self.wallet_address or not self.wallet_private_key:
            print("⚠️ Base wallet not configured (BASE_WALLET_PUBLIC_ADDRESS, BASE_WALLET_PRIVATE_KEY)")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Base Trading initialized - Wallet: {self.wallet_address[:8]}...")
    
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
    
    def execute_swap(self, from_token: str, to_token: str, amount: float, slippage: float = 0.5) -> Dict[str, Any]:
        """
        Execute token swap on Base using Uniswap V3
        
        Args:
            from_token: Symbol of input token
            to_token: Symbol of output token
            amount: Amount to swap
            slippage: Slippage tolerance in percent (default: 0.5%)
        
        Returns:
            Swap result with transaction hash
        """
        if not self.enabled:
            return {"success": False, "error": "Wallet not configured"}
        
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
                return {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "input_amount": amount,
                    "input_token": from_token.upper(),
                    "output_token": to_token.upper(),
                    "explorer_url": f"https://basescan.org/tx/{tx_hash.hex()}"
                }
            else:
                return {"success": False, "error": "Transaction reverted"}
                
        except Exception as e:
            return {"success": False, "error": f"Swap failed: {str(e)}"}
    
    def get_price(self, from_token: str, to_token: str) -> Dict[str, Any]:
        """
        Get price quote (simplified - should use Uniswap quoter in production)
        
        Args:
            from_token: Symbol of input token
            to_token: Symbol of output token
        
        Returns:
            Price information
        """
        return {
            "success": True,
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "note": "Price quotes require Uniswap V3 Quoter integration (not implemented yet)",
            "recommendation": "Use small test swap to check price"
        }


PLUGIN_INFO = {
    "name": "base_trading",
    "version": "1.0.0",
    "description": "Base chain token trading using Uniswap V3",
    "author": "AlleyBot"
}


def create_plugin(config=None):
    return BaseTrading(config or {})
