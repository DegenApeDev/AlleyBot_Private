"""
Solana Wallet Balance Plugin for AlleyBot
Check token balances for any wallet address on Solana network
"""
import requests
from typing import Dict, Any, List, Callable

from plugin_manager import AlleyBotPlugin


class SolanaWalletBalancePlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "solana_wallet_balance"
        self.version = "1.0.0"
        
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
                "name": "dogwifhat",
                "symbol": "WIF",
                "decimals": 6
            }
        }
    
    def is_valid_solana_address(self, addr: str) -> bool:
        """Validate Solana wallet address format"""
        if not addr or not (32 <= len(addr) <= 44):
            return False
        valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
        return all(c in valid_chars for c in addr)
    
    def make_rpc_call(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """Make RPC call to Solana network with fallback endpoints"""
        params = params or []
        for rpc_url in self.rpc_urls:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params
                }
                response = requests.post(rpc_url, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    continue
                if "result" in data and data["result"] is not None:
                    return {"success": True, "data": data["result"]}
                elif "error" in data:
                    error_info = data["error"]
                    error_msg = error_info.get("message") if isinstance(error_info, dict) else str(error_info)
                    return {"success": False, "error": error_msg}
            except Exception:
                continue
        return {"success": False, "error": "All RPC endpoints failed"}
    
    def get_sol_balance(self, address: str) -> Dict[str, Any]:
        """Get SOL balance for address"""
        if not self.is_valid_solana_address(address):
            return {"success": False, "error": "Invalid Solana address"}
        
        result = self.make_rpc_call("getBalance", [address])
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "RPC failed")}
        
        data = result.get("data")
        if data is None or "value" not in data or data["value"] is None:
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": "SOL",
                    "balance_lamports": 0,
                    "balance": 0.0,
                    "formatted": "0.000000 SOL"
                }
            }
        
        try:
            balance_lamports = int(data["value"])
            balance_sol = balance_lamports / 1e9
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
        except (ValueError, TypeError):
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": "SOL",
                    "balance_lamports": 0,
                    "balance": 0.0,
                    "formatted": "0.000000 SOL"
                }
            }
    
    def get_token_balance(self, address: str, token_address: str, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get SPL token balance, summing all accounts for the mint"""
        if not self.is_valid_solana_address(address):
            return {"success": False, "error": "Invalid Solana address"}
        
        result = self.make_rpc_call("getTokenAccountsByOwner", [
            address,
            {"mint": token_address},
            {"encoding": "jsonParsed"}
        ])
        if not result.get("success"):
            return {
                "success": True,
                "data": {
                    "address": address,
                    "token": token_info["symbol"],
                    "token_address": token_address,
                    "balance_raw": 0,
                    "balance": 0.0,
                    "formatted": f"0 {token_info['symbol']}",
                    "decimals": token_info["decimals"]
                }
            }
        
        data = result.get("data")
        token_accounts = data.get("value", []) if data else []
        
        total_amount = 0
        for account_info in token_accounts:
            try:
                parsed = account_info.get("account", {}).get("data", {}).get("parsed", {})
                info = parsed.get("info", {})
                token_amount = info.get("tokenAmount", {})
                amount_str = token_amount.get("amount", "0")
                total_amount += int(amount_str)
            except (ValueError, TypeError, KeyError):
                continue
        
        decimals = token_info["decimals"]
        balance = total_amount / (10 ** decimals)
        symbol = token_info["symbol"]
        
        return {
            "success": True,
            "data": {
                "address": address,
                "token": symbol,
                "token_address": token_address,
                "balance_raw": total_amount,
                "balance": balance,
                "formatted": f"{balance:.6f} {symbol}",
                "decimals": decimals
            }
        }
    
    def get_all_balances(self, address: str, tokens: List[str] = None) -> Dict[str, Any]:
        """Get balances for multiple tokens"""
        if not self.is_valid_solana_address(address):
            return {"success": False, "error": "Invalid Solana address format"}
        
        results = []
        errors = []
        if tokens is None:
            tokens = list(self.tokens.keys())
        
        for token_symbol in tokens:
            if token_symbol not in self.tokens:
                errors.append(f"Unknown token '{token_symbol}'")
                continue
            
            token_info = self.tokens[token_symbol]
            if token_symbol == "SOL":
                result = self.get_sol_balance(address)
            else:
                result = self.get_token_balance(address, token_info["address"], token_info)
            
            if result.get("success"):
                results.append(result["data"])
            else:
                errors.append(f"{token_symbol}: {result.get('error', 'Failed to fetch')}")
        
        return {
            "success": True,
            "data": results,
            "errors": errors,
            "address": address
        }
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "balance": self.balance,
        }
    
    def balance(self, args: list) -> str:
        """Command: !balance <wallet> [tokens...] - Check Solana wallet balances"""
        if not args:
            return "Usage: !balance <solana_wallet> [SOL USDC USDT ...]\nExample: !balance EKpQGSJ... USDC BONK"
        
        address = args[0].strip()
        if not self.is_valid_solana_address(address):
            short_addr = f"{address[:8]}..." if address else "empty"
            return f"❌ Invalid Solana address: {short_addr}"
        
        tokens = [t.strip().upper() for t in args[1:]] if len(args) > 1 else None
        
        print(f"Fetching balances for Solana address: {address}")
        all_balances = self.get_all_balances(address, tokens)
        
        if not all_balances.get("success"):
            return f"❌ Error: {all_balances.get('error', 'Unknown error')}"
        
        results = all_balances["data"]
        errors = all_balances.get("errors", [])
        short_addr = f"{address[:4]}...{address[-4:]}"
        
        msg = f"💰 Solana Balances for `{short_addr}`:\n"
        if not results:
            msg += "  No tokens found or all zero balances.\n"
        else:
            # Sort SOL first
            sol_balance = None
            other_balances = []
            for bal in results:
                if bal["token"] == "SOL":
                    sol_balance = bal
                else:
                    other_balances.append(bal)
            if sol_balance:
                msg += f"  🌞 SOL: {sol_balance['formatted']}\n"
            for bal in other_balances:
                msg += f"  🪙 {bal['token']}: {bal['formatted']}\n"
        
        if errors:
            msg += f"\n⚠️  Errors: {', '.join(errors)}"
        
        return msg


PLUGIN_INFO = {
    "name": "solana_wallet_balance",
    "version": "1.0.0",
    "description": "Check token balances for any wallet on Solana network",
    "author": "AlleyBot"
}


def create_plugin(config=None):
    return SolanaWalletBalancePlugin(config or {})