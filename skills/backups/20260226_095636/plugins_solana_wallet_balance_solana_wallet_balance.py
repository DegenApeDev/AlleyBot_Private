"""
Solana Wallet Balance Plugin for AlleyBot
Check token balances for any wallet address on Solana network
"""
import os
import sys
import asyncio
import requests
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin


class SolanaWalletBalancePlugin(AlleyBotPlugin):
    """Plugin for checking wallet balances on Solana network"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "solana_wallet_balance"
        self.version = "1.0.0"
        self.description = "Check token balances for any wallet on Solana network"
        
        # Solana RPC endpoints
        self.rpc_urls = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com",
            "https://rpc.ankr.com/solana"
        ]
        
        # Common token addresses on Solana
        self.tokens = {
            "SOL": {
                "address": "native",
                "name": "Solana",
                "symbol": "SOL",
                "decimals": 9
            },
            "USDC": {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "name": "USD Coin",
                "symbol": "USDC",
                "decimals": 6
            },
            "USDT": {
                "address": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "name": "Tether USD",
                "symbol": "USDT",
                "decimals": 6
            },
            "RAY": {
                "address": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59T5DGpnXBHRtHhK",
                "name": "Raydium",
                "symbol": "RAY",
                "decimals": 6
            },
            "SRM": {
                "address": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
                "name": "Serum",
                "symbol": "SRM",
                "decimals": 6
            },
            "SAMO": {
                "address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                "name": "Samoyedcoin",
                "symbol": "SAMO",
                "decimals": 9
            },
            "BONK": {
                "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "name": "Bonk",
                "symbol": "BONK",
                "decimals": 5
            },
            "WIF": {
                "address": "EKpQGSJtjMJqZvNspFbkck64jZ7oBfJZnmpGyrSZqWrB",
                "name": "Dogwifhat",
                "symbol": "WIF",
                "decimals": 6
            }
        }
    
    def make_rpc_call(self, method: str, params: List = None) -> Dict[str, Any]:
        """Make RPC call to Solana network"""
        
        for rpc_url in self.rpc_urls:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params or []
                }
                
                response = requests.post(rpc_url, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if "result" in data:
                    return {"success": True, "data": data["result"]}
                elif "error" in data:
                    return {"success": False, "error": data["error"]["message"]}
                else:
                    return {"success": False, "error": "Invalid response"}
                    
            except requests.exceptions.RequestException as e:
                continue  # Try next RPC URL
            except Exception as e:
                continue
        
        return {"success": False, "error": "All RPC endpoints failed"}
    
    def get_sol_balance(self, address: str) -> Dict[str, Any]:
        """Get SOL balance for address"""
        
        if not address or len(address) < 32:
            return {"success": False, "error": "Valid Solana address required"}
        
        try:
            result = self.make_rpc_call("getBalance", [address])
            
            if not result.get("success"):
                return result
            
            balance_lamports = result["data"]["value"]
            balance_sol = balance_lamports / (10 ** 9)
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": "SOL",
                    "balance_lamports": balance_lamports,
                    "balance": balance_sol,
                    "formatted": f"{balance_sol:.6f} SOL"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get SOL balance: {str(e)}"}
    
    def get_token_balance(self, address: str, token_address: str, token_info: Dict) -> Dict[str, Any]:
        """Get SPL token balance"""
        
        if not address or len(address) < 32:
            return {"success": False, "error": "Valid Solana address required"}
        
        try:
            # Get token accounts for the specific mint
            result = self.make_rpc_call("getTokenAccountsByOwner", [
                address,
                {"mint": token_address},
                {"encoding": "jsonParsed"}
            ])
            
            if not result.get("success"):
                return result
            
            token_accounts = result["data"]["value"]
            
            if not token_accounts:
                return {
                    "success": True,
                    "data": {
                        "address": address,
                        "token": token_info["symbol"],
                        "token_address": token_address,
                        "balance_raw": 0,
                        "balance": 0,
                        "formatted": f"0.00 {token_info['symbol']}",
                        "decimals": token_info["decimals"]
                    }
                }
            
            # Get the first token account balance
            token_account = token_accounts[0]
            balance_raw = token_account["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
            balance_decimals = token_account["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
            
            decimals = token_info["decimals"]
            balance_tokens = float(balance_decimals or 0)
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": token_info["symbol"],
                    "token_address": token_address,
                    "balance_raw": int(balance_raw),
                    "balance": balance_tokens,
                    "formatted": f"{balance_tokens:.6f} {token_info['symbol']}",
                    "decimals": decimals
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get token balance: {str(e)}"}
    
    def get_all_balances(self, address: str, tokens: List[str] = None) -> Dict[str, Any]:
        """Get balances for multiple tokens"""
        
        results = []
        errors = []
        
        # Handle standard tokens
        if tokens is None:
            tokens = list(self.tokens.keys())
        
        for token_symbol in tokens:
            if token_symbol not in self.tokens:
                errors.append(f"Unknown token: {token_symbol}")
                continue
            
            token_info = self.tokens[token_symbol]
            
            if token_symbol == "SOL":
                result = self.get_sol_balance(address)
            else:
                result = self.get_token_balance(address, token_info["address"], token_info)
            
            if result.get("success"):
                results.append(result["data"])
            else:
                errors.append(f"{token_symbol}: {result.get('error')}")
        
        # Calculate total USD value (simplified - would need price oracle in production)
        total_usd_value = 0.0
        for result in results:
            if result["token"] in ["USDC", "USDT"]:
                total_usd_value += result["balance"]
            elif result["token"] == "SOL":
                total_usd_value += result["balance"] * 150  # Assumed SOL price
            elif result["token"] == "RAY":
                total_usd_value += result["balance"] * 5  # Assumed RAY price
            elif result["token"] == "SRM":
                total_usd_value += result["balance"] * 3  # Assumed SRM price
        
        return {
            "success": True,
            "data": {
                "address": address,
                "balances": results,
                "total_usd_value": total_usd_value,
                "errors": errors,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def add_custom_token(self, symbol: str, address: str, name: str, decimals: int) -> Dict[str, Any]:
        """Add a custom token to the token list"""
        
        if not address or len(address) < 32:
            return {"success": False, "error": "Valid token address required"}
        
        self.tokens[symbol.upper()] = {
            "address": address,
            "name": name,
            "symbol": symbol.upper(),
            "decimals": decimals
        }
        
        return {
            "success": True,
            "data": {
                "message": f"Token {symbol.upper()} added successfully",
                "token_info": self.tokens[symbol.upper()]
            }
        }
    
    # Command implementations
    def solana_balance_command(self, *args) -> str:
        """Check Solana wallet balance: solana_balance <address> [token]"""
        if not args:
            return """❌ Usage: solana_balance <address> [token]

Examples:
  solana_balance 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
  solana_balance 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU USDC
  solana_balance 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU SOL,USDC,RAY"""
        
        address = args[0]
        tokens = args[1].split(",") if len(args) > 1 else None
        
        if tokens and len(tokens) == 1:
            # Single token check
            token_symbol = tokens[0].upper()
            if token_symbol not in self.tokens:
                return f"❌ Unknown token: {token_symbol}. Use /solana_supported_tokens to see available tokens."
            
            token_info = self.tokens[token_symbol]
            
            if token_symbol == "SOL":
                result = self.get_sol_balance(address)
            else:
                result = self.get_token_balance(address, token_info["address"], token_info)
            
            if not result.get("success"):
                return f"❌ Failed to get {token_symbol} balance: {result.get('error')}"
            
            data = result["data"]
            
            response = f"💰 Solana Token Balance\n"
            response += f"{'='*40}\n\n"
            response += f"Address: {address[:10]}...{address[-6:]}\n"
            response += f"Token: {data['token']} ({token_info['name']})\n"
            response += f"Balance: {data['formatted']}\n"
            
            if data['token'] != "SOL":
                response += f"Raw: {data['balance_raw']}\n"
            
            return response
        
        else:
            # Multiple tokens check
            result = self.get_all_balances(address, tokens)
            
            if not result.get("success"):
                return f"❌ Failed to get balances: {result.get('error')}"
            
            data = result["data"]
            balances = data["balances"]
            errors = data["errors"]
            
            response = f"💰 Solana Wallet Balances\n"
            response += f"{'='*40}\n\n"
            response += f"Address: {address[:10]}...{address[-6:]}\n"
            response += f"Network: Solana\n"
            response += f"Total USD Value: ${data['total_usd_value']:.2f}\n\n"
            
            if balances:
                response += f"🪙 Balances:\n"
                for balance in sorted(balances, key=lambda x: x['balance'], reverse=True):
                    if balance['balance'] > 0:
                        response += f"   {balance['formatted']}\n"
                    else:
                        response += f"   {balance['formatted']} (empty)\n"
            
            if errors:
                response += f"\n⚠️  Errors:\n"
                for error in errors:
                    response += f"   {error}\n"
            
            return response
    
    def solana_supported_tokens_command(self, *args) -> str:
        """List supported Solana tokens"""
        response = f"💰 Supported Tokens (Solana)\n"
        response += f"{'='*40}\n\n"
        
        for symbol, info in self.tokens.items():
            response += f"🪙 {symbol} ({info['name']})\n"
            response += f"   Address: {info['address']}\n"
            response += f"   Decimals: {info['decimals']}\n\n"
        
        response += f"💡 Use /solana_balance <address> <token> to check specific token"
        response += f"\n📝 Use /add_solana_token <symbol> <address> <name> <decimals> for custom tokens"
        
        return response
    
    def add_solana_token_command(self, *args) -> str:
        """Add custom Solana token: add_solana_token <symbol> <address> <name> <decimals>"""
        if len(args) < 4:
            return """❌ Usage: add_solana_token <symbol> <address> <name> <decimals>

Example: add_solana_token TOKEN 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU "My Token" 9"""
        
        symbol = args[0]
        address = args[1]
        name = args[2]
        decimals = int(args[3])
        
        result = self.add_custom_token(symbol, address, name, decimals)
        
        if not result.get("success"):
            return f"❌ Failed to add token: {result.get('error')}"
        
        data = result["data"]
        
        response = f"✅ Solana Token Added Successfully\n"
        response += f"{'='*40}\n\n"
        response += f"Symbol: {symbol.upper()}\n"
        response += f"Name: {name}\n"
        response += f"Address: {address}\n"
        response += f"Decimals: {decimals}\n\n"
        
        response += f"💡 You can now check balance with: /solana_balance <address> {symbol.upper()}"
        
        return response
    
    def solana_wallet_summary_command(self, *args) -> str:
        """Get Solana wallet summary: solana_wallet_summary <address>"""
        if not args:
            return "❌ Usage: solana_wallet_summary <address>"
        
        address = args[0]
        
        # Get all major token balances
        major_tokens = ["SOL", "USDC", "USDT", "RAY", "SRM", "BONK", "WIF"]
        result = self.get_all_balances(address, major_tokens)
        
        if not result.get("success"):
            return f"❌ Failed to get wallet summary: {result.get('error')}"
        
        data = result["data"]
        balances = data["balances"]
        
        # Filter non-zero balances
        non_zero_balances = [b for b in balances if b['balance'] > 0]
        
        response = f"💼 Solana Wallet Summary\n"
        response += f"{'='*40}\n\n"
        response += f"Address: {address[:10]}...{address[-6:]}\n"
        response += f"Network: Solana\n"
        response += f"Total Tokens: {len(non_zero_balances)}\n"
        response += f"Total USD Value: ${data['total_usd_value']:.2f}\n\n"
        
        if non_zero_balances:
            response += f"🪙 Holdings:\n"
            for balance in sorted(non_zero_balances, key=lambda x: x['balance'], reverse=True):
                response += f"   {balance['formatted']}\n"
        else:
            response += f"📭 No tokens found\n"
        
        response += f"\n📅 Last Updated: {data['last_updated'][:19]}"
        
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'solana_balance': self.solana_balance_command,
            'solana_supported_tokens': self.solana_supported_tokens_command,
            'add_solana_token': self.add_solana_token_command,
            'solana_wallet_summary': self.solana_wallet_summary_command,
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any] = None) -> SolanaWalletBalancePlugin:
    """Create plugin instance"""
    return SolanaWalletBalancePlugin(config)


# Plugin metadata
PLUGIN_INFO = {
    "name": "solana_wallet_balance",
    "version": "1.0.0",
    "description": "Check token balances for any wallet on Solana network",
    "author": "AlleyBot",
    "dependencies": ["requests"],
    "config_required": False
}
