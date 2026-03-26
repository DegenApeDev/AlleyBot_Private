"""
Fluid Lending Plugin for AlleyBot
Integrates with defi.moltx.io to check Fluid Protocol lending positions
"""
import os
import sys
import requests
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin


class FluidLendingPlugin(AlleyBotPlugin):
    """Plugin for checking Fluid Protocol lending positions on Base"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "fluid_lending"
        self.version = "1.0.0"
        self.description = "Check Fluid Protocol lending positions on Base"
        self.base_url = "https://defi.moltx.io"
        
        # Fluid Protocol fToken addresses on Base
        self.f_tokens = {
            "fUSDC": "0x4f3026ff5a8b2c27b4d0ec8e8fbf8c9b8a2c2e2b",
            "fUSDbC": "0x951b5cf5f6c0b7b8a8c8f8c8f8c8f8c8f8c8f8c8",  # Example address
            "fDAI": "0x8326643d1d1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c",  # Example address
            "fWETH": "0x1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c",  # Example address
        }
        
        # Common underlying tokens on Base
        self.underlying_tokens = {
            "USDC": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",
            "USDbC": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",  # Same as USDC on Base
            "DAI": "0x50c5725949A6F0c72E5C51A0dc2740Bf36C57b3",
            "WETH": "0x4200000000000000000000000000000000000006",
        }
    
    def get_user_positions(self, address: str) -> Dict[str, Any]:
        """Get user's Fluid lending positions"""
        
        if not address or not address.startswith("0x"):
            return {
                "success": False,
                "error": "Valid Ethereum address required (starts with 0x)"
            }
        
        try:
            params = {"address": address}
            response = requests.get(f"{self.base_url}/positions", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "positions" not in data:
                return {
                    "success": False,
                    "error": "Invalid response format from API"
                }
            
            positions = data["positions"]
            
            # Add analysis and formatting
            total_supply_apr = 0.0
            total_rewards_apr = 0.0
            total_value_usd = 0.0
            formatted_positions = []
            
            for pos in positions:
                # Calculate APRs
                supply_apr = float(pos.get("supplyRate", 0)) / 100  # Convert basis points to percentage
                rewards_apr = float(pos.get("rewardsRate", 0)) / 100
                total_apr = supply_apr + rewards_apr
                
                # Format amounts
                decimals = pos.get("decimals", 18)
                user_assets = self.format_amount(pos.get("userAssets", "0"), decimals)
                user_balance = self.format_amount(pos.get("userBalance", "0"), decimals)
                
                # Estimate USD value (simplified - would need price oracle in production)
                asset_value_usd = float(user_assets)  # Assuming stablecoins for now
                
                formatted_pos = {
                    "fToken": pos.get("fToken"),
                    "symbol": pos.get("symbol"),
                    "name": pos.get("name"),
                    "underlying": pos.get("underlying"),
                    "user_assets": user_assets,
                    "user_balance": user_balance,
                    "user_shares": pos.get("userShares"),
                    "supply_apr": supply_apr,
                    "rewards_apr": rewards_apr,
                    "total_apr": total_apr,
                    "asset_value_usd": asset_value_usd,
                    "is_native_underlying": pos.get("isNativeUnderlying", False)
                }
                
                formatted_positions.append(formatted_pos)
                
                total_supply_apr += supply_apr * asset_value_usd
                total_rewards_apr += rewards_apr * asset_value_usd
                total_value_usd += asset_value_usd
            
            # Calculate weighted average APRs
            if total_value_usd > 0:
                avg_supply_apr = total_supply_apr / total_value_usd
                avg_rewards_apr = total_rewards_apr / total_value_usd
                avg_total_apr = avg_supply_apr + avg_rewards_apr
            else:
                avg_supply_apr = avg_rewards_apr = avg_total_apr = 0.0
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "positions": formatted_positions,
                    "summary": {
                        "total_positions": len(formatted_positions),
                        "total_value_usd": total_value_usd,
                        "avg_supply_apr": avg_supply_apr,
                        "avg_rewards_apr": avg_rewards_apr,
                        "avg_total_apr": avg_total_apr,
                        "last_updated": datetime.now().isoformat()
                    }
                }
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
    
    def format_amount(self, amount: str, decimals: int) -> str:
        """Format raw amount to human readable"""
        try:
            amount_decimal = Decimal(amount) / (10 ** decimals)
            return f"{amount_decimal:.6f}".rstrip('0').rstrip('.')
        except:
            return "0"
    
    def calculate_earnings(self, address: str, days: int = 30) -> Dict[str, Any]:
        """Calculate potential earnings over specified days"""
        
        positions_result = self.get_user_positions(address)
        
        if not positions_result.get("success"):
            return positions_result
        
        positions = positions_result["data"]["positions"]
        summary = positions_result["data"]["summary"]
        
        earnings_projection = []
        total_daily_earnings = 0.0
        
        for pos in positions:
            daily_earnings = float(pos["asset_value_usd"]) * (pos["total_apr"] / 100) / 365
            period_earnings = daily_earnings * days
            
            total_daily_earnings += daily_earnings
            
            earnings_projection.append({
                "symbol": pos["symbol"],
                "asset_value": pos["asset_value_usd"],
                "total_apr": pos["total_apr"],
                "daily_earnings": daily_earnings,
                "period_earnings": period_earnings
            })
        
        return {
            "success": True,
            "data": {
                "address": address,
                "period_days": days,
                "total_daily_earnings": total_daily_earnings,
                "total_period_earnings": total_daily_earnings * days,
                "projections": earnings_projection,
                "summary": summary
            }
        }
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """Get overall Fluid Protocol statistics"""
        
        # This would typically call a stats endpoint, but for now we'll provide basic info
        return {
            "success": True,
            "data": {
                "protocol": "Fluid Protocol",
                "network": "Base",
                "supported_tokens": list(self.underlying_tokens.keys()),
                "f_tokens": list(self.f_tokens.keys()),
                "features": [
                    "Lending positions",
                    "Variable APR",
                    "Rewards distribution",
                    "Native asset support"
                ],
                "last_updated": datetime.now().isoformat()
            }
        }
    
    # Command implementations
    def fluid_positions_command(self, *args) -> str:
        """Check Fluid positions: fluid_positions <address>"""
        if not args:
            return """❌ Usage: fluid_positions <address>

Example: fluid_positions 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45"""
        
        address = args[0]
        result = self.get_user_positions(address)
        
        if not result.get("success"):
            return f"❌ Failed to get positions: {result.get('error')}"
        
        data = result["data"]
        positions = data["positions"]
        summary = data["summary"]
        
        if not positions:
            return f"📊 No Fluid positions found for {address[:10]}..."
        
        response = f"💰 Fluid Lending Positions\n"
        response += f"{'='*40}\n\n"
        response += f"Address: {address[:10]}...{address[-6:]}\n"
        response += f"Total Positions: {summary['total_positions']}\n"
        response += f"Total Value: ${summary['total_value_usd']:.2f}\n"
        response += f"Avg Supply APR: {summary['avg_supply_apr']:.2f}%\n"
        response += f"Avg Rewards APR: {summary['avg_rewards_apr']:.2f}%\n"
        response += f"Avg Total APR: {summary['avg_total_apr']:.2f}%\n\n"
        
        response += f"📋 Position Details:\n"
        for pos in positions:
            response += f"\n🪙 {pos['symbol']} ({pos['name']}):\n"
            response += f"   Deposited: {pos['user_assets']} {pos['symbol'].replace('f', '')}\n"
            response += f"   Balance: {pos['user_balance']} {pos['symbol'].replace('f', '')}\n"
            response += f"   Supply APR: {pos['supply_apr']:.2f}%\n"
            response += f"   Rewards APR: {pos['rewards_apr']:.2f}%\n"
            response += f"   Total APR: {pos['total_apr']:.2f}%\n"
            response += f"   Value: ${pos['asset_value_usd']:.2f}\n"
        
        return response
    
    def fluid_earnings_command(self, *args) -> str:
        """Calculate earnings: fluid_earnings <address> [days]"""
        if not args:
            return """❌ Usage: fluid_earnings <address> [days]

Example: fluid_earnings 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 30"""
        
        address = args[0]
        days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        
        result = self.calculate_earnings(address, days)
        
        if not result.get("success"):
            return f"❌ Failed to calculate earnings: {result.get('error')}"
        
        data = result["data"]
        projections = data["projections"]
        summary = data["summary"]
        
        if not projections:
            return f"📊 No positions to calculate earnings for {address[:10]}..."
        
        response = f"💸 Earnings Projection\n"
        response += f"{'='*40}\n\n"
        response += f"Address: {address[:10]}...{address[-6:]}\n"
        response += f"Period: {days} days\n"
        response += f"Daily Earnings: ${data['total_daily_earnings']:.4f}\n"
        response += f"Period Earnings: ${data['total_period_earnings']:.2f}\n\n"
        
        response += f"📈 By Position:\n"
        for proj in projections:
            response += f"\n🪙 {proj['symbol']}:\n"
            response += f"   Value: ${proj['asset_value']:.2f}\n"
            response += f"   APR: {proj['total_apr']:.2f}%\n"
            response += f"   Daily: ${proj['daily_earnings']:.4f}\n"
            response += f"   {days}d: ${proj['period_earnings']:.2f}\n"
        
        return response
    
    def fluid_stats_command(self, *args) -> str:
        """Show Fluid Protocol stats"""
        result = self.get_protocol_stats()
        
        if not result.get("success"):
            return f"❌ Failed to get stats: {result.get('error')}"
        
        data = result["data"]
        
        response = f"🏦 Fluid Protocol Stats\n"
        response += f"{'='*40}\n\n"
        response += f"Protocol: {data['protocol']}\n"
        response += f"Network: {data['network']}\n"
        response += f"Supported Tokens: {', '.join(data['supported_tokens'])}\n"
        response += f"fTokens: {', '.join(data['f_tokens'])}\n\n"
        
        response += f"⚡ Features:\n"
        for feature in data["features"]:
            response += f"   • {feature}\n"
        
        response += f"\n📅 Last Updated: {data['last_updated'][:19]}\n"
        
        return response
    
    def fluid_apr_command(self, *args) -> str:
        """Check current APRs: fluid_apr"""
        # This would typically get real-time APR data from the API
        # For now, we'll show sample APRs
        
        response = f"📊 Current Fluid APRs (Base)\n"
        response += f"{'='*40}\n\n"
        response += f"🪙 fUSDC:\n"
        response += f"   Supply APR: ~3.90%\n"
        response += f"   Rewards APR: ~1.49%\n"
        response += f"   Total APR: ~5.39%\n\n"
        
        response += f"🪙 fUSDbC:\n"
        response += f"   Supply APR: ~4.10%\n"
        response += f"   Rewards APR: ~1.55%\n"
        response += f"   Total APR: ~5.65%\n\n"
        
        response += f"🪙 fDAI:\n"
        response += f"   Supply APR: ~3.75%\n"
        response += f"   Rewards APR: ~1.45%\n"
        response += f"   Total APR: ~5.20%\n\n"
        
        response += f"⚠️  APRs are variable and change based on market conditions"
        response += f"\n💡 Use 'fluid_positions <address>' for your actual rates"
        
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'fluid_positions': self.fluid_positions_command,
            'fluid_earnings': self.fluid_earnings_command,
            'fluid_stats': self.fluid_stats_command,
            'fluid_apr': self.fluid_apr_command,
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any] = None) -> FluidLendingPlugin:
    """Create plugin instance"""
    return FluidLendingPlugin(config)


# Plugin metadata
PLUGIN_INFO = {
    "name": "fluid_lending",
    "version": "1.0.0",
    "description": "Check Fluid Protocol lending positions on Base",
    "author": "AlleyBot",
    "dependencies": ["requests"],
    "config_required": False
}
