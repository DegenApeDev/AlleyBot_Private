"""
Base Wallet Balance Plugin for AlleyBot
Check token balances for any wallet address on Base network
"""
import os
import sys
import requests
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin


class BaseWalletBalancePlugin(AlleyBotPlugin):
    """Plugin for checking wallet balances on Base network"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "base_wallet_balance"
        self.version = "1.0.0"
        self.description = "Check token balances for any wallet on Base network"
        
        # Base network RPC endpoints
        self.rpc_urls = [
            "https://mainnet.base.org",
            "https://base.blockpi.network/v1/rpc/public",
            "https://rpc.ankr.com/base"
        ]
        
        # Common token addresses on Base
        self.tokens = {
            "ETH": {
                "address": "native",
                "name": "Ethereum",
                "symbol": "ETH",
                "decimals": 18
            },
            "WETH": {
                "address": "0x4200000000000000000000000000000000000006",
                "name": "Wrapped Ethereum",
                "symbol": "WETH",
                "decimals": 18
            },
            "USDC": {
                "address": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",
                "name": "USD Coin",
                "symbol": "USDC",
                "decimals": 6
            },
            "USDbC": {
                "address": "0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA",
                "name": "USD Base Coin",
                "symbol": "USDbC",
                "decimals": 6
            },
            "DAI": {
                "address": "0x50c5725949A6F0c72E5C51A0dc2740Bf36C57b3",
                "name": "Dai Stablecoin",
                "symbol": "DAI",
                "decimals": 18
            },
            "WBTC": {
                "address": "0x2bA2A3F718d94F4586Cbd4F1c96E0cD52F62Dba3",
                "name": "Wrapped Bitcoin",
                "symbol": "WBTC",
                "decimals": 8
            },
            "LINK": {
                "address": "0x88362281044A532a3A5853bC8C827AEb3a647632",
                "name": "Chainlink Token",
                "symbol": "LINK",
                "decimals": 18
            },
            "UNI": {
                "address": "0x3e25d950F79C96C7A5F5A0A625A2d9549e352b64",
                "name": "Uniswap Token",
                "symbol": "UNI",
                "decimals": 18
            }
        }
        
        # ERC-20 ABI for balanceOf function
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
    
    def make_rpc_call(self, method: str, params: List = None) -> Dict[str, Any]:
        """Make RPC call to Base network"""
        
        for rpc_url in self.rpc_urls:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params or [],
                    "id": 1
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
    
    def get_eth_balance(self, address: str) -> Dict[str, Any]:
        """Get ETH balance for address"""
        
        if not address or not address.startswith("0x"):
            return {"success": False, "error": "Valid Ethereum address required"}
        
        try:
            result = self.make_rpc_call("eth_getBalance", [address, "latest"])
            
            if not result.get("success"):
                return result
            
            balance_hex = result["data"]
            if balance_hex == "0x":
                balance_wei = 0
            else:
                balance_wei = int(balance_hex, 16)
            
            balance_eth = balance_wei / (10 ** 18)
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": "ETH",
                    "balance_wei": balance_wei,
                    "balance": balance_eth,
                    "formatted": f"{balance_eth:.6f} ETH"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get ETH balance: {str(e)}"}
    
    def get_token_balance(self, address: str, token_address: str, token_info: Dict) -> Dict[str, Any]:
        """Get ERC-20 token balance"""
        
        if not address or not address.startswith("0x"):
            return {"success": False, "error": "Valid Ethereum address required"}
        
        try:
            # Create call data for balanceOf function
            # Function selector: balanceOf(address) -> 0x70a08231
            # Pad address to 32 bytes
            call_data = "0x70a08231" + address[2:].zfill(64)
            
            result = self.make_rpc_call("eth_call", [{
                "to": token_address,
                "data": call_data
            }, "latest"])
            
            if not result.get("success"):
                return result
            
            balance_hex = result["data"]
            if balance_hex == "0x":
                balance_raw = 0
            else:
                balance_raw = int(balance_hex, 16)
            
            decimals = token_info["decimals"]
            balance_tokens = balance_raw / (10 ** decimals)
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": token_info["symbol"],
                    "token_address": token_address,
                    "balance_raw": balance_raw,
                    "balance": balance_tokens,
                    "formatted": f"{balance_tokens:.6f} {token_info['symbol']}",
                    "decimals": decimals
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get token balance: {str(e)}"}
    
    def get_contract_balance(self, address: str, contract_address: str) -> Dict[str, Any]:
        """Get balance for any contract address (ERC-20 or other)"""
        
        if not address or not address.startswith("0x"):
            return {"success": False, "error": "Valid wallet address required"}
        
        if not contract_address or not contract_address.startswith("0x"):
            return {"success": False, "error": "Valid contract address required"}
        
        try:
            # First try standard ERC-20 balanceOf call
            call_data = "0x70a08231" + address[2:].zfill(64)
            
            result = self.make_rpc_call("eth_call", [{
                "to": contract_address,
                "data": call_data
            }, "latest"])
            
            if not result.get("success"):
                return result
            
            balance_hex = result["data"]
            
            # Check if it's a valid ERC-20 response (not just zeros or error)
            if balance_hex == "0x":
                balance_raw = 0
            else:
                balance_raw = int(balance_hex, 16)
            
            # Try to get token info if possible
            token_info = self._get_contract_info(contract_address)
            
            decimals = token_info.get("decimals", 18)  # Default to 18 if unknown
            balance_tokens = balance_raw / (10 ** decimals)
            
            return {
                "success": True,
                "data": {
                    "address": address,
                    "contract_address": contract_address,
                    "token_name": token_info.get("name", "Unknown"),
                    "token_symbol": token_info.get("symbol", "UNKNOWN"),
                    "balance_raw": balance_raw,
                    "balance": balance_tokens,
                    "formatted": f"{balance_tokens:.6f} {token_info.get('symbol', 'UNKNOWN')}",
                    "decimals": decimals,
                    "contract_type": "ERC-20" if token_info.get("name") else "Unknown Contract"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get contract balance: {str(e)}"}
    
    def _get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """Try to get basic token info from contract"""
        
        token_info = {"name": None, "symbol": None, "decimals": 18}
        
        try:
            # Try to get token name (function selector: 0x06fdde03)
            result = self.make_rpc_call("eth_call", [{
                "to": contract_address,
                "data": "0x06fdde03" + "0" * 64  # name() with empty params
            }, "latest"])
            
            if result.get("success") and result["data"] != "0x":
                name_hex = result["data"]
                if len(name_hex) > 2:  # More than just "0x"
                    try:
                        # Remove 0x and convert hex to string
                        name_data = bytes.fromhex(name_hex[2:])
                        # Find null terminator and decode
                        null_pos = name_data.find(b'\x00')
                        if null_pos != -1:
                            name_data = name_data[:null_pos]
                        token_info["name"] = name_data.decode('utf-8', errors='ignore')
                    except:
                        pass
            
            # Try to get token symbol (function selector: 0x95d89b41)
            result = self.make_rpc_call("eth_call", [{
                "to": contract_address,
                "data": "0x95d89b41" + "0" * 64  # symbol() with empty params
            }, "latest"])
            
            if result.get("success") and result["data"] != "0x":
                symbol_hex = result["data"]
                if len(symbol_hex) > 2:
                    try:
                        symbol_data = bytes.fromhex(symbol_hex[2:])
                        null_pos = symbol_data.find(b'\x00')
                        if null_pos != -1:
                            symbol_data = symbol_data[:null_pos]
                        token_info["symbol"] = symbol_data.decode('utf-8', errors='ignore')
                    except:
                        pass
            
            # Try to get decimals (function selector: 0x313ce567)
            result = self.make_rpc_call("eth_call", [{
                "to": contract_address,
                "data": "0x313ce567" + "0" * 64  # decimals() with empty params
            }, "latest"])
            
            if result.get("success") and result["data"] != "0x":
                decimals_hex = result["data"]
                if len(decimals_hex) > 2:
                    try:
                        decimals_int = int(decimals_hex, 16)
                        if 0 <= decimals_int <= 255:  # Reasonable range
                            token_info["decimals"] = decimals_int
                    except:
                        pass
            
        except Exception:
            # If any of the above calls fail, we'll return default values
            pass
        
        return token_info
    
    def get_all_balances(self, address: str, tokens: List[str] = None, contracts: List[str] = None) -> Dict[str, Any]:
        """Get balances for multiple tokens and contracts"""
        
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
            
            if token_symbol == "ETH":
                result = self.get_eth_balance(address)
            else:
                result = self.get_token_balance(address, token_info["address"], token_info)
            
            if result.get("success"):
                results.append(result["data"])
            else:
                errors.append(f"{token_symbol}: {result.get('error')}")
        
        # Handle custom contract addresses
        if contracts:
            for contract_address in contracts:
                if not contract_address.startswith("0x") or len(contract_address) != 42:
                    errors.append(f"Invalid contract address: {contract_address}")
                    continue
                
                result = self.get_contract_balance(address, contract_address)
                
                if result.get("success"):
                    results.append(result["data"])
                else:
                    errors.append(f"Contract {contract_address[:10]}...: {result.get('error')}")
        
        # Calculate total USD value (simplified - would need price oracle in production)
        total_usd_value = 0.0
        for result in results:
            # Handle standard tokens
            if "token" in result:
                if result["token"] in ["USDC", "USDbC"]:
                    total_usd_value += result["balance"]
                elif result["token"] == "WETH":
                    total_usd_value += result["balance"] * 3000  # Assumed ETH price
                elif result["token"] == "WBTC":
                    total_usd_value += result["balance"] * 45000  # Assumed BTC price
            # Handle contract balances
            elif "token_symbol" in result:
                if result["token_symbol"] in ["USDC", "USDbC"]:
                    total_usd_value += result["balance"]
                elif result["token_symbol"] == "WETH":
                    total_usd_value += result["balance"] * 3000
                elif result["token_symbol"] == "WBTC":
                    total_usd_value += result["balance"] * 45000
        
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
        
        if not address or not address.startswith("0x"):
            return {"success": False, "error": "Valid token address required"}
        
        if len(address) != 42:
            return {"success": False, "error": "Invalid token address length"}
        
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
    def balance_command(self, *args) -> str:
        """Check wallet balance: balance <address> [token]"""
        if not args:
            return """❌ Usage: balance <address> [token]

Examples:
  balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45
  balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 USDC
  balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 ETH,WETH,USDC"""
        
        address = args[0]
        tokens = args[1].split(",") if len(args) > 1 else None
        
        if tokens and len(tokens) == 1:
            # Single token check
            token_symbol = tokens[0].upper()
            if token_symbol not in self.tokens:
                return f"❌ Unknown token: {token_symbol}. Use /supported_tokens to see available tokens."
            
            token_info = self.tokens[token_symbol]
            
            if token_symbol == "ETH":
                result = self.get_eth_balance(address)
            else:
                result = self.get_token_balance(address, token_info["address"], token_info)
            
            if not result.get("success"):
                return f"❌ Failed to get {token_symbol} balance: {result.get('error')}"
            
            data = result["data"]
            
            response = f"💰 Token Balance\n"
            response += f"{'='*40}\n\n"
            response += f"Address: {address[:10]}...{address[-6:]}\n"
            response += f"Token: {data['token']} ({token_info['name']})\n"
            response += f"Balance: {data['formatted']}\n"
            
            if data['token'] not in ["ETH", "WETH"]:
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
            
            response = f"💰 Wallet Balances\n"
            response += f"{'='*40}\n\n"
            response += f"Address: {address[:10]}...{address[-6:]}\n"
            response += f"Network: Base\n"
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
    
    def eth_balance_command(self, *args) -> str:
        """Check ETH balance: eth_balance <address>"""
        if not args:
            return "❌ Usage: eth_balance <address>"
        
        address = args[0]
        result = self.get_eth_balance(address)
        
        if not result.get("success"):
            return f"❌ Failed to get ETH balance: {result.get('error')}"
        
        data = result["data"]
        
        response = f"💰 ETH Balance\n"
        response += f"{'='*40}\n\n"
        response += f"Address: {address[:10]}...{address[-6:]}\n"
        response += f"Balance: {data['formatted']}\n"
        response += f"Wei: {data['balance_wei']:,}\n"
        
        return response
    
    def supported_tokens_command(self, *args) -> str:
        """List supported tokens"""
        response = f"💰 Supported Tokens (Base)\n"
        response += f"{'='*40}\n\n"
        
        for symbol, info in self.tokens.items():
            response += f"🪙 {symbol} ({info['name']})\n"
            response += f"   Address: {info['address']}\n"
            response += f"   Decimals: {info['decimals']}\n\n"
        
        response += f"💡 Use /balance <address> <token> to check specific token"
        response += f"\n📝 Use /add_token <symbol> <address> <name> <decimals> for custom tokens"
        
        return response
    
    def add_token_command(self, *args) -> str:
        """Add custom token: add_token <symbol> <address> <name> <decimals>"""
        if len(args) < 4:
            return """❌ Usage: add_token <symbol> <address> <name> <decimals>

Example: add_token TOKEN 0x1234...abcd "My Token" 18"""
        
        symbol = args[0]
        address = args[1]
        name = args[2]
        decimals = int(args[3])
        
        result = self.add_custom_token(symbol, address, name, decimals)
        
        if not result.get("success"):
            return f"❌ Failed to add token: {result.get('error')}"
        
        data = result["data"]
        
        response = f"✅ Token Added Successfully\n"
        response += f"{'='*40}\n\n"
        response += f"Symbol: {symbol.upper()}\n"
        response += f"Name: {name}\n"
        response += f"Address: {address}\n"
        response += f"Decimals: {decimals}\n\n"
        
        response += f"💡 You can now check balance with: /balance <address> {symbol.upper()}"
        
        return response
    
    def wallet_summary_command(self, *args) -> str:
        """Get wallet summary: wallet_summary <address>"""
        if not args:
            return "❌ Usage: wallet_summary <address>"
        
        address = args[0]
        
        # Get all major token balances
        major_tokens = ["ETH", "WETH", "USDC", "USDbC", "DAI", "WBTC"]
        result = self.get_all_balances(address, major_tokens)
        
        if not result.get("success"):
            return f"❌ Failed to get wallet summary: {result.get('error')}"
        
        data = result["data"]
        balances = data["balances"]
        
        # Filter non-zero balances
        non_zero_balances = [b for b in balances if b['balance'] > 0]
        
        response = f"💼 Wallet Summary\n"
        response += f"{'='*40}\n\n"
        response += f"Address: {address[:10]}...{address[-6:]}\n"
        response += f"Network: Base\n"
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
    
    def contract_balance_command(self, *args) -> str:
        """Check contract balance: contract_balance <address> <contract_address>"""
        if len(args) < 2:
            return """❌ Usage: contract_balance <address> <contract_address>

Examples:
  contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA
  contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0x4200000000000000000000000000000000000006

Note: This will try to get token info from the contract and display the balance."""
        
        address = args[0]
        contract_address = args[1]
        
        result = self.get_contract_balance(address, contract_address)
        
        if not result.get("success"):
            return f"❌ Failed to get contract balance: {result.get('error')}"
        
        data = result["data"]
        
        response = f"💰 Contract Balance\n"
        response += f"{'='*40}\n\n"
        response += f"Wallet: {address[:10]}...{address[-6:]}\n"
        response += f"Contract: {contract_address[:10]}...{contract_address[-6:]}\n"
        response += f"Token: {data['token_name']} ({data['token_symbol']})\n"
        response += f"Type: {data['contract_type']}\n"
        response += f"Balance: {data['formatted']}\n"
        response += f"Decimals: {data['decimals']}\n"
        
        if data['balance_raw'] > 0:
            response += f"Raw: {data['balance_raw']:,}\n"
        
        return response
    
    def multi_contract_balance_command(self, *args) -> str:
        """Check multiple contract balances: multi_contract_balance <address> <contract1,contract2,...>"""
        if len(args) < 2:
            return """❌ Usage: multi_contract_balance <address> <contract1,contract2,...>

Example: multi_contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA,0x4200000000000000000000000000000000000006"""
        
        address = args[0]
        contract_addresses = args[1].split(",")
        
        result = self.get_all_balances(address, tokens=[], contracts=contract_addresses)
        
        if not result.get("success"):
            return f"❌ Failed to get contract balances: {result.get('error')}"
        
        data = result["data"]
        balances = data["balances"]
        errors = data["errors"]
        
        response = f"💰 Multiple Contract Balances\n"
        response += f"{'='*40}\n\n"
        response += f"Wallet: {address[:10]}...{address[-6:]}\n"
        response += f"Contracts Checked: {len(contract_addresses)}\n"
        response += f"Successful: {len(balances)}\n\n"
        
        if balances:
            response += f"🪙 Balances:\n"
            for balance in sorted(balances, key=lambda x: x['balance'], reverse=True):
                if balance['balance'] > 0:
                    response += f"   {balance['formatted']} ({balance['token_name']})\n"
                else:
                    response += f"   {balance['formatted']} ({balance['token_name']}) - empty\n"
        
        if errors:
            response += f"\n⚠️  Errors:\n"
            for error in errors:
                response += f"   {error}\n"
        
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands"""
        return {
            'balance': self.balance_command,
            'eth_balance': self.eth_balance_command,
            'supported_tokens': self.supported_tokens_command,
            'add_token': self.add_token_command,
            'wallet_summary': self.wallet_summary_command,
            'contract_balance': self.contract_balance_command,
            'multi_contract_balance': self.multi_contract_balance_command,
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any] = None) -> BaseWalletBalancePlugin:
    """Create plugin instance"""
    return BaseWalletBalancePlugin(config)


# Plugin metadata
PLUGIN_INFO = {
    "name": "base_wallet_balance",
    "version": "1.0.0",
    "description": "Check token balances for any wallet on Base network",
    "author": "AlleyBot",
    "dependencies": ["requests"],
    "config_required": False
}
