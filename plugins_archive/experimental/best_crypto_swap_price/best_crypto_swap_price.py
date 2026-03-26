"""
Best Crypto Swap Price Plugin for AlleyBot
Integrates with swap.moltx.io to get best DEX aggregator prices
"""
import os
import sys
import requests
from typing import Dict, Any, Optional, List
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin


class BestCryptoSwapPricePlugin(AlleyBotPlugin):
    """Plugin for getting best crypto swap prices across multiple DEX aggregators"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "best_crypto_swap_price"
        self.version = "1.0.0"
        self.description = "Get best token swap prices across multiple DEX aggregators"
        self.base_url = "https://swap.moltx.io"
        
        # Supported networks
        self.supported_networks = ["ethereum", "arbitrum", "base", "polygon", "plasma"]
        
        # Common token addresses for convenience
        self.common_tokens = {
            "ethereum": {
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
            },
            "base": {
                "WETH": "0x4200000000000000000000000000000000000006",
                "USDC": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",
                "USDbC": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",
                "DAI": "0x50c5725949A6F0c72E5C51A0dc2740Bf36C57b3"
            },
            "arbitrum": {
                "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                "USDC": "0xA0b86a33E6441b6910b4d0a2e89d72D71916e018",
                "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "DAI": "0xDA10009cBd5d07dd0CeCc66161FC93D7c9000da1"
            }
        }
        
        # Supported aggregators
        self.supported_aggregators = [
            "paraswap-v6", "1inch-v6", "0x-v2", "kyber-v1", 
            "odos-v2", "okx-v5", "okx-v6"
        ]
    
    def get_swap_quote(self, network: str, sell_token: str, buy_token: str, 
                      sell_amount: str, slippage: float = 1.0, user_address: str = None,
                      aggregators: List[str] = None, disabled_protocols: List[str] = None) -> Dict[str, Any]:
        """Get swap quotes from multiple DEX aggregators"""
        
        if network not in self.supported_networks:
            return {
                "success": False,
                "error": f"Unsupported network: {network}. Supported: {', '.join(self.supported_networks)}"
            }
        
        # Use default user address if not provided
        if not user_address:
            user_address = getattr(self, 'default_user_address', '0x0000000000000000000000000000000000000000')
        
        params = {
            "network": network,
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmount": sell_amount,
            "slippage": slippage,
            "user": user_address,
            "eoaAddress": user_address,
            "accountType": "eoa"
        }
        
        # Add optional parameters
        if aggregators:
            for agg in aggregators:
                params[f"aggregators[]"] = agg
        
        if disabled_protocols:
            for proto in disabled_protocols:
                params[f"disabledProtocols[]"] = proto
        
        try:
            response = requests.get(f"{self.base_url}/swap", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Add analysis
            if "aggregators" in data:
                best_aggregator = max(
                    data["aggregators"], 
                    key=lambda x: float(x.get("data", {}).get("buyTokenAmount", 0)) 
                    if not x.get("error") else 0
                )
                
                data["analysis"] = {
                    "best_aggregator": best_aggregator.get("displayName"),
                    "best_buy_amount": best_aggregator.get("data", {}).get("buyTokenAmount"),
                    "total_aggregators_queried": len(data["aggregators"]),
                    "successful_aggregators": len([a for a in data["aggregators"] if not a.get("error")])
                }
            
            return {
                "success": True,
                "data": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def compare_all_aggregators(self, network: str, sell_token: str, buy_token: str,
                               sell_amount: str, slippage: float = 1.0, user_address: str = None) -> Dict[str, Any]:
        """Compare quotes from all available aggregators individually"""
        
        results = {}
        
        for aggregator in self.supported_aggregators:
            result = self.get_swap_quote(
                network=network,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=sell_amount,
                slippage=slippage,
                user_address=user_address,
                aggregators=[aggregator]
            )
            
            if result.get("success") and result.get("data", {}).get("aggregators"):
                agg_data = result["data"]["aggregators"][0]
                if not agg_data.get("error"):
                    results[aggregator] = {
                        "buy_amount": agg_data["data"]["buyTokenAmount"],
                        "price_impact": agg_data["data"]["priceImpact"],
                        "gas_price": agg_data["data"]["gasPrice"],
                        "calldata": agg_data["data"]["calldata"]
                    }
        
        # Find best deal
        if results:
            best_aggregator = max(results.items(), key=lambda x: float(x[1]["buy_amount"]))
            
            return {
                "success": True,
                "best_deal": {
                    "aggregator": best_aggregator[0],
                    "buy_amount": best_aggregator[1]["buy_amount"],
                    "price_impact": best_aggregator[1]["price_impact"]
                },
                "all_quotes": results
            }
        else:
            return {
                "success": False,
                "error": "No successful quotes from any aggregator"
            }
    
    def get_token_address(self, network: str, symbol: str) -> Optional[str]:
        """Get token address by symbol for common tokens"""
        return self.common_tokens.get(network, {}).get(symbol.upper())
    
    def format_amount(self, amount: str, decimals: int) -> str:
        """Format raw amount to human readable"""
        try:
            amount_decimal = Decimal(amount) / (10 ** decimals)
            return str(amount_decimal)
        except:
            return amount
    
    # Command implementations
    def swap_quote_command(self, *args) -> str:
        """Get swap quote: swap_quote <network> <sell_token> <buy_token> <sell_amount> [slippage]"""
        if len(args) < 4:
            return """❌ Usage: swap_quote <network> <sell_token> <buy_token> <sell_amount> [slippage]

Examples:
  swap_quote ethereum USDC WETH 1000000000 1.0
  swap_quote base 0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA 0x4200000000000000000000000000000000000006 500000000

Networks: ethereum, arbitrum, base, polygon, plasma
Slippage: percentage (e.g., 1.0 for 1%)"""
        
        network = args[0].lower()
        sell_token = args[1]
        buy_token = args[2]
        sell_amount = args[3]
        slippage = float(args[4]) if len(args) > 4 else 1.0
        
        # Convert symbols to addresses if needed
        if not sell_token.startswith("0x"):
            sell_token_addr = self.get_token_address(network, sell_token)
            if not sell_token_addr:
                return f"❌ Unknown sell token symbol: {sell_token}"
            sell_token = sell_token_addr
        
        if not buy_token.startswith("0x"):
            buy_token_addr = self.get_token_address(network, buy_token)
            if not buy_token_addr:
                return f"❌ Unknown buy token symbol: {buy_token}"
            buy_token = buy_token_addr
        
        result = self.get_swap_quote(network, sell_token, buy_token, sell_amount, slippage)
        
        if not result.get("success"):
            return f"❌ Swap quote failed: {result.get('error')}"
        
        data = result["data"]
        analysis = data.get("analysis", {})
        
        response = f"🔄 Swap Quote Analysis\n"
        response += f"{'='*40}\n\n"
        response += f"Network: {network.title()}\n"
        response += f"Best Aggregator: {analysis.get('best_aggregator', 'N/A')}\n"
        response += f"Successful Quotes: {analysis.get('successful_aggregators', 0)}/{analysis.get('total_aggregators_queried', 0)}\n\n"
        
        if "data" in data:
            swap_data = data["data"]
            response += f"💰 Swap Details:\n"
            response += f"   Sell Amount: {self.format_amount(swap_data['sellTokenAmount'], 6)} {swap_data['sellToken']['symbol']}\n"
            response += f"   Buy Amount: {self.format_amount(swap_data['buyTokenAmount'], 6)} {swap_data['buyToken']['symbol']}\n"
            response += f"   Slippage: {swap_data['slippage']}%\n"
            response += f"   Min Buy Amount: {self.format_amount(swap_data['minBuyAmountSlippage'], 6)}\n\n"
        
        # Show top 3 best quotes
        if "aggregators" in data:
            successful_aggs = [a for a in data["aggregators"] if not a.get("error")]
            successful_aggs.sort(key=lambda x: float(x.get("data", {}).get("buyTokenAmount", 0)), reverse=True)
            
            response += f"🏆 Top Quotes:\n"
            for i, agg in enumerate(successful_aggs[:3], 1):
                agg_data = agg.get("data", {})
                response += f"   {i}. {agg['displayName']}: {self.format_amount(agg_data.get('buyTokenAmount', '0'), 6)} {data['data']['buyToken']['symbol']}\n"
        
        return response
    
    def compare_aggregators_command(self, *args) -> str:
        """Compare all aggregators: compare_aggregators <network> <sell_token> <buy_token> <sell_amount>"""
        if len(args) < 4:
            return """❌ Usage: compare_aggregators <network> <sell_token> <buy_token> <sell_amount>

Example: compare_aggregators ethereum USDC WETH 1000000000"""
        
        network = args[0].lower()
        sell_token = args[1]
        buy_token = args[2]
        sell_amount = args[3]
        
        # Convert symbols to addresses if needed
        if not sell_token.startswith("0x"):
            sell_token_addr = self.get_token_address(network, sell_token)
            if not sell_token_addr:
                return f"❌ Unknown sell token symbol: {sell_token}"
            sell_token = sell_token_addr
        
        if not buy_token.startswith("0x"):
            buy_token_addr = self.get_token_address(network, buy_token)
            if not buy_token_addr:
                return f"❌ Unknown buy token symbol: {buy_token}"
            buy_token = buy_token_addr
        
        result = self.compare_all_aggregators(network, sell_token, buy_token, sell_amount)
        
        if not result.get("success"):
            return f"❌ Comparison failed: {result.get('error')}"
        
        best_deal = result["best_deal"]
        all_quotes = result["all_quotes"]
        
        response = f"🔄 Aggregator Comparison\n"
        response += f"{'='*40}\n\n"
        response += f"🏆 Best Deal: {best_deal['aggregator']}\n"
        response += f"   Buy Amount: {best_deal['buy_amount']}\n"
        response += f"   Price Impact: {best_deal['price_impact']}%\n\n"
        
        response += f"📊 All Quotes:\n"
        sorted_quotes = sorted(all_quotes.items(), key=lambda x: float(x[1]["buy_amount"]), reverse=True)
        
        for agg, quote in sorted_quotes:
            response += f"   {agg}: {quote['buy_amount']} (impact: {quote['price_impact']}%)\n"
        
        return response
    
    def swap_tokens_command(self, *args) -> str:
        """Quick swap: swap_tokens <network> <sell_symbol> <buy_symbol> <amount>"""
        if len(args) < 4:
            return """❌ Usage: swap_tokens <network> <sell_symbol> <buy_symbol> <amount>

Example: swap_tokens ethereum USDC WETH 1000
        
Note: This only provides quotes. Execute swaps manually using the calldata."""
        
        network = args[0].lower()
        sell_symbol = args[1].upper()
        buy_symbol = args[2].upper()
        amount = args[3]
        
        sell_token = self.get_token_address(network, sell_symbol)
        buy_token = self.get_token_address(network, buy_symbol)
        
        if not sell_token:
            return f"❌ Unknown sell token: {sell_symbol}"
        if not buy_token:
            return f"❌ Unknown buy token: {buy_symbol}"
        
        # Convert amount to wei (assuming 6 decimals for USDC-like tokens)
        try:
            amount_float = float(amount)
            sell_amount = str(int(amount_float * 10**6))
        except:
            return f"❌ Invalid amount: {amount}"
        
        result = self.get_swap_quote(network, sell_token, buy_token, sell_amount)
        
        if not result.get("success"):
            return f"❌ Swap quote failed: {result.get('error')}"
        
        data = result["data"]
        
        # Find best aggregator with calldata
        best_agg = None
        for agg in data.get("aggregators", []):
            if not agg.get("error") and agg.get("data", {}).get("calldata"):
                best_agg = agg
                break
        
        if not best_agg:
            return "❌ No executable quotes available"
        
        agg_data = best_agg["data"]
        
        response = f"🔄 Swap Ready for Execution\n"
        response += f"{'='*40}\n\n"
        response += f"Network: {network.title()}\n"
        response += f"Aggregator: {best_agg['displayName']}\n"
        response += f"Route: {sell_symbol} → {buy_symbol}\n"
        response += f"Amount: {amount} {sell_symbol}\n"
        response += f"Expected: {self.format_amount(agg_data['buyTokenAmount'], 6)} {buy_symbol}\n"
        response += f"Price Impact: {agg_data['priceImpact']}%\n\n"
        
        response += f"🔧 Transaction Data:\n"
        response += f"To: {agg_data['to']}\n"
        response += f"Value: {agg_data['value']}\n"
        response += f"Data: {agg_data['calldata'][:50]}...\n\n"
        
        response += f"⚠️  Execute this transaction manually with your wallet"
        
        return response
    
    def supported_tokens_command(self, *args) -> str:
        """List supported tokens by network"""
        response = f"💰 Supported Tokens by Network\n"
        response += f"{'='*40}\n\n"
        
        for network, tokens in self.common_tokens.items():
            response += f"🌐 {network.title()}:\n"
            for symbol, address in tokens.items():
                response += f"   {symbol}: {address}\n"
            response += "\n"
        
        response += f"📋 Supported Aggregators:\n"
        for agg in self.supported_aggregators:
            response += f"   {agg}\n"
        
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'swap_quote': self.swap_quote_command,
            'compare_aggregators': self.compare_aggregators_command,
            'swap_tokens': self.swap_tokens_command,
            'supported_tokens': self.supported_tokens_command,
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any] = None) -> BestCryptoSwapPricePlugin:
    """Create plugin instance"""
    return BestCryptoSwapPricePlugin(config)


# Plugin metadata
PLUGIN_INFO = {
    "name": "best_crypto_swap_price",
    "version": "1.0.0",
    "description": "Get best crypto swap prices across multiple DEX aggregators",
    "author": "AlleyBot",
    "dependencies": ["requests"],
    "config_required": False
}
