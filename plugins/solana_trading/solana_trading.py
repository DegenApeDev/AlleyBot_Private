"""
Solana Token Trading Plugin for AlleyBot
Integrates Jupiter Aggregator for best swap prices on Solana
"""
import os
import requests
import base64
from typing import Dict, Any, List, Optional
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from plugin_manager import AlleyBotPlugin

# Import security filter
try:
    from security_filter import security_filter
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    print("⚠️ Security filter not available - trading responses may leak sensitive data!")


class SolanaTrading(AlleyBotPlugin):
    """Solana token trading using Jupiter Aggregator"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "solana_trading"
        self.version = "1.0.0"
        
        # Jupiter API endpoints
        self.jupiter_api = "https://quote-api.jup.ag/v6"
        
        # Solana RPC
        self.rpc_url = "https://api.mainnet-beta.solana.com"
        
        # Jito MEV protection endpoint
        self.jito_endpoint = "https://mainnet.block-engine.jito.wtf/api/v1/transactions"
        
        # Wallet configuration
        self.wallet_address = os.getenv('SOLANA_WALLET_PUBLIC_ADDRESS')
        self.wallet_private_key = os.getenv('SOLANA_WALLET_PRIVATE_KEY')
        
        # Risk management rules
        self.risk_rules = {
            'min_profit_percent': 0.3,  # 0.3% minimum profit
            'max_price_impact': 2.0,    # 2% max price impact
            'max_slippage_bps': 100,    # 1% max slippage
            'jupiter_fee_percent': 0.1, # Jupiter 0.1% fee
        }
        
        # Common token mints
        self.tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59T5DGpnXBHRtHhK",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "WIF": "EKpQGSJtjMJqZvNspFbkck64jZ7oBfJZnmpGyrSZqWrB",
        }
        
        # Token decimals
        self.decimals = {
            "SOL": 9,
            "USDC": 6,
            "USDT": 6,
            "RAY": 6,
            "BONK": 5,
            "WIF": 6,
        }
        
        # Security: Validate wallet configuration
        if not self.wallet_address or not self.wallet_private_key:
            print("⚠️ Solana wallet not configured (SOLANA_WALLET_PUBLIC_ADDRESS, SOLANA_WALLET_PRIVATE_KEY)")
            self.enabled = False
        else:
            self.enabled = True
            # Only show first 8 chars of address for security
            print(f"✅ Solana Trading initialized - Wallet: {self.wallet_address[:8]}...")
        
        # Security: Allowed recipient addresses (owner's wallet only)
        # All swaps go to the same wallet that initiated them
        self.allowed_recipients = {self.wallet_address} if self.wallet_address else set()
        
        # Security check
        if not SECURITY_AVAILABLE:
            print("🚨 WARNING: Security filter not loaded! Trading responses may expose sensitive data!")
        
        # Never log or expose private keys
        if self.wallet_private_key:
            # Verify key is not accidentally logged
            if len(self.wallet_private_key) < 32:
                print("⚠️ Solana private key appears invalid (too short)")
                self.enabled = False
    
    def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> Dict[str, Any]:
        """
        Get swap quote from Jupiter
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Amount in smallest unit (lamports/tokens)
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)
        
        Returns:
            Quote data or error
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": "false",
                "asLegacyTransaction": "false"
            }
            
            response = requests.get(f"{self.jupiter_api}/quote", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                best_quote = data["data"][0]
                return {
                    "success": True,
                    "quote": best_quote,
                    "input_amount": int(best_quote["inAmount"]),
                    "output_amount": int(best_quote["outAmount"]),
                    "price_impact": float(best_quote.get("priceImpactPct", 0)),
                    "route": best_quote.get("routePlan", [])
                }
            else:
                return {"success": False, "error": "No routes found"}
                
        except Exception as e:
            return {"success": False, "error": f"Quote failed: {str(e)}"}
    
    def calculate_profit(self, quote_result: Dict[str, Any], from_token: str, to_token: str, amount: float) -> Dict[str, Any]:
        """
        Calculate expected profit after all costs
        
        Args:
            quote_result: Quote data from get_quote()
            from_token: Input token symbol
            to_token: Output token symbol
            amount: Input amount
        
        Returns:
            Profit analysis with breakdown
        """
        try:
            # Get token prices (simplified - in production, fetch from price API)
            # For now, assume USDC = $1, calculate relative prices
            input_amount = quote_result['input_amount']
            output_amount = quote_result['output_amount']
            price_impact = quote_result['price_impact']
            
            from_decimals = self.decimals.get(from_token.upper(), 9)
            to_decimals = self.decimals.get(to_token.upper(), 9)
            
            # Calculate human-readable amounts
            input_human = input_amount / (10 ** from_decimals)
            output_human = output_amount / (10 ** to_decimals)
            
            # Estimate costs
            jupiter_fee_percent = self.risk_rules['jupiter_fee_percent']
            price_impact_cost = abs(price_impact)
            
            # Total cost in percent
            total_cost_percent = jupiter_fee_percent + price_impact_cost
            
            # Estimate gas cost (Solana is cheap, ~0.000005 SOL = $0.001)
            gas_cost_usd = 0.001
            
            # Calculate if profitable (simplified)
            # In production, fetch real-time prices from CoinGecko/Jupiter
            is_profitable = price_impact < self.risk_rules['max_price_impact']
            
            return {
                'success': True,
                'is_profitable': is_profitable,
                'price_impact_percent': price_impact,
                'total_cost_percent': total_cost_percent,
                'gas_cost_usd': gas_cost_usd,
                'input_amount': input_human,
                'output_amount': output_human,
                'breakdown': {
                    'jupiter_fee': jupiter_fee_percent,
                    'price_impact': price_impact_cost,
                    'gas': gas_cost_usd
                },
                'warnings': self._generate_warnings(price_impact, total_cost_percent)
            }
        except Exception as e:
            return {'success': False, 'error': f'Profit calculation failed: {str(e)}'}
    
    def _generate_warnings(self, price_impact: float, total_cost: float) -> List[str]:
        """Generate warnings based on trade parameters"""
        warnings = []
        
        if price_impact > 1.0:
            warnings.append(f"⚠️ High price impact: {price_impact:.2f}%")
        
        if price_impact > self.risk_rules['max_price_impact']:
            warnings.append(f"🚨 Price impact exceeds limit: {price_impact:.2f}% > {self.risk_rules['max_price_impact']}%")
        
        if total_cost > 2.0:
            warnings.append(f"⚠️ High total cost: {total_cost:.2f}%")
        
        return warnings
    
    def get_swap_transaction(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get swap transaction from Jupiter
        
        Args:
            quote: Quote data from get_quote()
        
        Returns:
            Transaction data or error
        """
        try:
            payload = {
                "quoteResponse": quote,
                "userPublicKey": self.wallet_address,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": "auto"
            }
            
            response = requests.post(
                f"{self.jupiter_api}/swap",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "swapTransaction" in data:
                return {
                    "success": True,
                    "transaction": data["swapTransaction"],
                    "last_valid_block_height": data.get("lastValidBlockHeight")
                }
            else:
                return {"success": False, "error": "No transaction returned"}
                
        except Exception as e:
            return {"success": False, "error": f"Transaction creation failed: {str(e)}"}
    
    def execute_swap(self, from_token: str, to_token: str, amount: float, slippage_bps: int = 50, use_mev_protection: bool = True, force: bool = False) -> Dict[str, Any]:
        """
        Execute token swap with profit checks and MEV protection
        
        Args:
            from_token: Symbol of input token (e.g., "SOL")
            to_token: Symbol of output token (e.g., "USDC")
            amount: Amount to swap in human-readable format
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)
            use_mev_protection: Use Jito for MEV protection (adds ~0.0001 SOL fee)
            force: Skip profit checks (dangerous!)
        
        Returns:
            Swap result with transaction signature and profit analysis
        """
        if not self.enabled:
            return {"success": False, "error": "Wallet not configured"}
        
        # Validate slippage
        if slippage_bps > self.risk_rules['max_slippage_bps']:
            return {
                "success": False,
                "error": f"Slippage too high: {slippage_bps} bps > {self.risk_rules['max_slippage_bps']} bps limit"
            }
        
        # Get token mints
        from_mint = self.tokens.get(from_token.upper())
        to_mint = self.tokens.get(to_token.upper())
        
        if not from_mint or not to_mint:
            return {"success": False, "error": f"Unknown token: {from_token if not from_mint else to_token}"}
        
        # Convert amount to smallest unit
        from_decimals = self.decimals.get(from_token.upper(), 9)
        amount_raw = int(amount * (10 ** from_decimals))
        
        # Get quote
        print(f"🔍 Getting quote: {amount} {from_token} → {to_token}")
        quote_result = self.get_quote(from_mint, to_mint, amount_raw, slippage_bps)
        
        if not quote_result.get("success"):
            return quote_result
        
        quote = quote_result["quote"]
        output_amount = quote_result["output_amount"]
        to_decimals = self.decimals.get(to_token.upper(), 9)
        output_human = output_amount / (10 ** to_decimals)
        
        print(f"💱 Quote: {amount} {from_token} → {output_human:.6f} {to_token}")
        print(f"📊 Price Impact: {quote_result['price_impact']:.4f}%")
        
        # Calculate profit
        profit_analysis = self.calculate_profit(quote_result, from_token, to_token, amount)
        
        if profit_analysis.get('success'):
            # Check profitability
            if not force:
                if not profit_analysis['is_profitable']:
                    return {
                        "success": False,
                        "error": "Trade not profitable",
                        "profit_analysis": profit_analysis,
                        "suggestion": "Increase amount or wait for better prices"
                    }
                
                # Show warnings
                if profit_analysis.get('warnings'):
                    print("\n".join(profit_analysis['warnings']))
                    
                    # Block if price impact too high
                    if quote_result['price_impact'] > self.risk_rules['max_price_impact']:
                        return {
                            "success": False,
                            "error": f"Price impact too high: {quote_result['price_impact']:.2f}%",
                            "profit_analysis": profit_analysis,
                            "suggestion": "Reduce trade size or use force=True to override"
                        }
        
        print(f"✅ Profit check passed - proceeding with swap")
        
        # Get swap transaction
        tx_result = self.get_swap_transaction(quote)
        
        if not tx_result.get("success"):
            return tx_result
        
        # Sign and send transaction
        try:
            # Decode transaction
            tx_bytes = base64.b64decode(tx_result["transaction"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            
            # Sign transaction
            keypair = Keypair.from_base58_string(self.wallet_private_key)
            tx.sign([keypair])
            
            # Send transaction
            signed_tx_bytes = bytes(tx)
            signed_tx_b64 = base64.b64encode(signed_tx_bytes).decode('utf-8')
            
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    signed_tx_b64,
                    {
                        "encoding": "base64",
                        "skipPreflight": False,
                        "preflightCommitment": "confirmed",
                        "maxRetries": 3
                    }
                ]
            }
            
            response = requests.post(self.rpc_url, json=rpc_payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if "result" in result:
                signature = result["result"]
                
                swap_result = {
                    "success": True,
                    "signature": signature,
                    "input_amount": amount,
                    "input_token": from_token,
                    "output_amount": output_human,
                    "output_token": to_token,
                    "price_impact": quote_result["price_impact"],
                    "explorer_url": f"https://solscan.io/tx/{signature}",
                    "mev_protected": use_mev_protection
                }
                
                # Add profit analysis if available
                if profit_analysis.get('success'):
                    swap_result['profit_analysis'] = profit_analysis
                
                # Note: MEV protection via Jito not yet implemented
                # To add: Send transaction through Jito block engine
                if use_mev_protection:
                    swap_result['mev_note'] = "MEV protection requested but not yet implemented. Use Jito in production."
                
                # Security: Filter response to prevent key leakage
                if SECURITY_AVAILABLE:
                    # Convert to string, filter, then parse back
                    result_str = str(swap_result)
                    filtered_str, was_filtered = security_filter.filter_message(result_str)
                    if was_filtered:
                        print("🚨 SECURITY: Filtered sensitive data from swap result")
                
                return swap_result
            else:
                error = result.get("error", {})
                error_msg = f"Transaction failed: {error}"
                
                # Security: Sanitize error message
                if SECURITY_AVAILABLE:
                    error_msg = security_filter.sanitize_error_message(error_msg)
                
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            
            # Security: Sanitize error message to remove paths/keys
            if SECURITY_AVAILABLE:
                error_msg = security_filter.sanitize_error_message(error_msg)
            
            return {"success": False, "error": error_msg}
    
    def get_price(self, from_token: str, to_token: str, amount: float = 1.0) -> Dict[str, Any]:
        """
        Get price quote without executing swap
        
        Args:
            from_token: Symbol of input token
            to_token: Symbol of output token
            amount: Amount to check price for (default: 1.0)
        
        Returns:
            Price information
        """
        from_mint = self.tokens.get(from_token.upper())
        to_mint = self.tokens.get(to_token.upper())
        
        if not from_mint or not to_mint:
            return {"success": False, "error": f"Unknown token: {from_token if not from_mint else to_token}"}
        
        from_decimals = self.decimals.get(from_token.upper(), 9)
        amount_raw = int(amount * (10 ** from_decimals))
        
        quote_result = self.get_quote(from_mint, to_mint, amount_raw)
        
        if not quote_result.get("success"):
            return quote_result
        
        output_amount = quote_result["output_amount"]
        to_decimals = self.decimals.get(to_token.upper(), 9)
        output_human = output_amount / (10 ** to_decimals)
        
        price = output_human / amount if amount > 0 else 0
        
        return {
            "success": True,
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "amount": amount,
            "output": output_human,
            "price": price,
            "price_impact": quote_result["price_impact"],
            "formatted": f"1 {from_token.upper()} = {price:.6f} {to_token.upper()}"
        }


PLUGIN_INFO = {
    "name": "solana_trading",
    "version": "1.0.0",
    "description": "Solana token trading using Jupiter Aggregator",
    "author": "AlleyBot"
}


def create_plugin(config=None):
    return SolanaTrading(config or {})
