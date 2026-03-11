"""
Best Crypto Swap Price - Telegram Commands

Provides Telegram bot commands for the swap skill:
- /best_swap_quote - Get best swap price
- /best_swap_execute - Execute a swap
- /best_swap_compare - Compare all aggregators
"""
import os
import sys
from typing import Dict, Any

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from skills.best_crypto_swap_price.best_crypto_swap_skill import BestCryptoSwapSkill, quick_swap


class BestSwapCommands:
    """Telegram commands for best crypto swap skill"""
    
    def __init__(self, plugin=None):
        self.plugin = plugin
        self.skill = BestCryptoSwapSkill()
    
    def get_commands(self) -> Dict[str, callable]:
        """Return command handlers"""
        return {
            'best_swap_quote': self.quote_command,
            'best_swap_execute': self.execute_command,
            'best_swap_compare': self.compare_command,
            'best_swap_tokens': self.tokens_command,
        }
    
    def quote_command(self, *args) -> str:
        """
        Get best swap quote. Usage: best_swap_quote <network> <from_token> <to_token> <amount>
        
        Example: best_swap_quote ethereum USDC WETH 100
        """
        if len(args) < 4:
            return """❌ Usage: best_swap_quote <network> <from_token> <to_token> <amount>

Examples:
  best_swap_quote ethereum USDC WETH 100
  best_swap_quote base USDC ETH 50
  best_swap_quote arbitrum WETH USDC 0.5

Supported networks: ethereum, base, arbitrum, polygon, plasma"""
        
        network = args[0].lower()
        from_token = args[1].upper()
        to_token = args[2].upper()
        
        try:
            amount = float(args[3])
        except ValueError:
            return "❌ Amount must be a number"
        
        # Get user address from config
        user_address = self._get_user_address(network)
        if not user_address:
            return f"❌ No wallet configured for {network}. Set {network.upper()}_WALLET_ADDRESS in .env"
        
        # Get token addresses
        sell_token = self.skill.get_token_address(network, from_token)
        buy_token = self.skill.get_token_address(network, to_token)
        
        if not sell_token:
            return f"❌ Unknown token: {from_token} on {network}"
        if not buy_token:
            return f"❌ Unknown token: {to_token} on {network}"
        
        # Get decimals (simplified - should query contract)
        decimals = 6 if from_token in ['USDC', 'USDT'] else 18
        amount_raw = int(amount * (10 ** decimals))
        
        # Get quote
        result = self.skill.get_best_quote(
            network=network,
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=str(amount_raw),
            user_address=user_address,
            slippage=1.0
        )
        
        if not result.get('success'):
            return f"❌ Failed to get quote: {result.get('error', 'Unknown error')}"
        
        best = result['best_route']
        summary = result['summary']
        
        output = f"📊 Best Swap Quote on {network.upper()}\n\n"
        output += f"🔄 {from_token} → {to_token}\n"
        output += f"💰 Sell: {amount} {from_token}\n"
        output += f"🎯 Best Route: {best.display_name}\n"
        output += f"📈 Buy Amount: {best.buy_amount} (raw units)\n"
        output += f"⚡ Price Impact: {best.price_impact}%\n"
        output += f"⛽ Gas Price: {best.gas_price}\n\n"
        
        # Show comparison
        if len(result['all_routes']) > 1:
            output += "🏆 All Routes:\n"
            for i, route in enumerate(result['all_routes'][:5], 1):
                output += f"  {i}. {route.display_name}: {route.buy_amount[:20]}...\n"
        
        output += f"\n💡 To execute: best_swap_execute {network} {from_token} {to_token} {amount}"
        
        return output
    
    def execute_command(self, *args) -> str:
        """
        Execute a swap. Usage: best_swap_execute <network> <from_token> <to_token> <amount>
        
        Example: best_swap_execute ethereum USDC WETH 100
        """
        if len(args) < 4:
            return "❌ Usage: best_swap_execute <network> <from_token> <to_token> <amount>"
        
        network = args[0].lower()
        from_token = args[1].upper()
        to_token = args[2].upper()
        
        try:
            amount = float(args[3])
        except ValueError:
            return "❌ Amount must be a number"
        
        # Get wallet credentials
        user_address = self._get_user_address(network)
        private_key = self._get_private_key(network)
        
        if not user_address or not private_key:
            return f"❌ Wallet not configured for {network}. Check your .env file."
        
        # Get decimals
        decimals = 6 if from_token in ['USDC', 'USDT'] else 18
        
        # Execute swap
        try:
            result = quick_swap(
                network=network,
                from_token_symbol=from_token,
                to_token_symbol=to_token,
                amount=amount,
                user_address=user_address,
                private_key=private_key,
                from_decimals=decimals,
                slippage=1.0
            )
            
            if result.get('success'):
                output = f"✅ Swap Executed Successfully!\n\n"
                output += f"🎯 Aggregator: {result.get('aggregator')}\n"
                output += f"🔗 Tx Hash: {result.get('tx_hash', 'N/A')[:20]}...\n"
                output += f"📦 Buy Amount: {result.get('buy_amount', 'N/A')}\n"
                output += f"⚡ Price Impact: {result.get('price_impact', 'N/A')}%\n"
                output += f"⛽ Gas Used: {result.get('gas_used', 'N/A')}\n"
                if result.get('explorer_url'):
                    output += f"\n📄 Explorer: {result.get('explorer_url')}"
                return output
            else:
                return f"❌ Swap failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Execution error: {str(e)}"
    
    def compare_command(self, *args) -> str:
        """
        Compare all aggregators. Usage: best_swap_compare <network> <from_token> <to_token> <amount>
        """
        if len(args) < 4:
            return "❌ Usage: best_swap_compare <network> <from_token> <to_token> <amount>"
        
        network = args[0].lower()
        from_token = args[1].upper()
        to_token = args[2].upper()
        
        try:
            amount = float(args[3])
        except ValueError:
            return "❌ Amount must be a number"
        
        user_address = self._get_user_address(network)
        if not user_address:
            user_address = "0x0000000000000000000000000000000000000000"  # Dummy for comparison
        
        sell_token = self.skill.get_token_address(network, from_token)
        buy_token = self.skill.get_token_address(network, to_token)
        
        if not sell_token:
            return f"❌ Unknown token: {from_token} on {network}"
        if not buy_token:
            return f"❌ Unknown token: {to_token} on {network}"
        
        decimals = 6 if from_token in ['USDC', 'USDT'] else 18
        amount_raw = int(amount * (10 ** decimals))
        
        comparison = self.skill.compare_aggregators(
            network=network,
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=str(amount_raw),
            user_address=user_address,
            slippage=1.0
        )
        
        return comparison
    
    def tokens_command(self, *args) -> str:
        """
        List supported tokens. Usage: best_swap_tokens [network]
        """
        network = args[0].lower() if args else 'all'
        
        output = "📋 Supported Tokens by Network\n\n"
        
        if network == 'all' or network == 'ethereum':
            output += "🔷 Ethereum:\n"
            for symbol, addr in self.skill.TOKENS['ethereum'].items():
                output += f"  {symbol}: {addr[:15]}...\n"
        
        if network == 'all' or network == 'base':
            output += "\n🔵 Base:\n"
            for symbol, addr in self.skill.TOKENS['base'].items():
                output += f"  {symbol}: {addr[:15]}...\n"
        
        if network == 'all' or network == 'arbitrum':
            output += "\n🟠 Arbitrum:\n"
            for symbol, addr in self.skill.TOKENS['arbitrum'].items():
                output += f"  {symbol}: {addr[:15]}...\n"
        
        if network == 'all' or network == 'polygon':
            output += "\n🟣 Polygon:\n"
            for symbol, addr in self.skill.TOKENS['polygon'].items():
                output += f"  {symbol}: {addr[:15]}...\n"
        
        return output
    
    def _get_user_address(self, network: str) -> str:
        """Get user wallet address for network"""
        import os
        
        # Try network-specific address first
        address = os.getenv(f'{network.upper()}_WALLET_PUBLIC_ADDRESS')
        if address:
            return address
        
        # Fall back to generic addresses
        if network in ['ethereum', 'base', 'polygon']:
            return os.getenv('BASE_WALLET_PUBLIC_ADDRESS') or os.getenv('WALLET_ADDRESS')
        
        return os.getenv('WALLET_ADDRESS')
    
    def _get_private_key(self, network: str) -> str:
        """Get private key for network"""
        import os
        
        # Try network-specific key first
        key = os.getenv(f'{network.upper()}_PRIVATE_KEY')
        if key:
            return key
        
        # Fall back to generic keys
        if network in ['ethereum', 'base', 'polygon']:
            return os.getenv('BASE_WALLET_PRIVATE_KEY') or os.getenv('PRIVATE_KEY')
        
        return os.getenv('PRIVATE_KEY')


# Singleton instance
_commands_instance = None

def get_commands(plugin=None):
    """Get command handlers"""
    global _commands_instance
    if _commands_instance is None:
        _commands_instance = BestSwapCommands(plugin)
    return _commands_instance.get_commands()
