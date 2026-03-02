# plugins/solana_token_analysis/solana_token_analysis.py
import requests
from typing import Dict, Any
from plugin_manager import AlleyBotPlugin

class SolanaTokenAnalysisPlugin(AlleyBotPlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "solana_token_analysis"
        self.version = "1.0.0"

    def get_rugcheck_report(self, address: str) -> Dict[str, Any]:
        url = f"https://api.rugcheck.xyz/v2/tokens/{address}/report"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("success"):
                return data["data"]
        except Exception as e:
            print(f"Rugcheck error for {address}: {e}")
        return {}

    def get_dexscreener_data(self, address: str) -> Dict[str, Any]:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        try:
            data = requests.get(url, timeout=10).json()
            pairs = data.get("pairs", [])
            if pairs:
                main_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                return {
                    "liquidity_usd": float(main_pair.get("liquidity", {}).get("usd", 0)),
                    "fdv": float(main_pair.get("fdv", 0)),
                    "price_usd": float(main_pair.get("priceUsd", 0)),
                    "volume_24h": float(main_pair.get("volume", {}).get("h24", 0)),
                    "dex_id": main_pair.get("dexId"),
                    "pair_address": main_pair.get("pairAddress"),
                    "is_pumpdotfun": main_pair.get("dexId") == "pumpdotfun",
                }
        except Exception as e:
            print(f"Dexscreener error for {address}: {e}")
        return {}

    def get_solscan_meta(self, address: str) -> Dict[str, Any]:
        url = f"https://public-api.solscan.io/token/meta?token={address}"
        try:
            data = requests.get(url, timeout=10).json().get("data", {})
            return {
                "name": data.get("name", "Unknown"),
                "symbol": data.get("symbol", "UNK"),
                "supply": float(data.get("supply", 0)),
                "decimals": int(data.get("decimal", 9)),
            }
        except Exception as e:
            print(f"Solscan meta error for {address}: {e}")
        return {}

    def get_commands(self) -> Dict[str, callable]:
        return {
            "solana_analyze_token": self.analyze_token,
            "solana_rug_check": self.rug_check,
        }

    def analyze_token(self, args: list) -> str:
        if len(args) < 1 or len(args[0]) != 44:
            return "Usage: solana_analyze_token <44-char token_address>"
        address = args[0]
        meta = self.get_solscan_meta(address)
        ds = self.get_dexscreener_data(address)
        rug = self.get_rugcheck_report(address)
        report = f"**{meta.get('name', 'Token')} ({meta.get('symbol', '')})**\n"
        report += f"Address: `{address}`\n\n"
        if ds:
            report += f"💰 Price: ${ds['price_usd']:.10f}\n"
            report += f"💧 Liquidity: ${ds['liquidity_usd']:,.0f}\n"
            report += f"📈 FDV: ${ds['fdv']:,.0f}\n"
            report += f"🔥 24h Vol: ${ds['volume_24h']:,.0f}\n"
            status = "🚀 Pump.fun Bonding Curve" if ds['is_pumpdotfun'] else f"📊 DEX: {ds['dex_id'].title()}"
            report += f"{status}\n"
        if rug:
            risk = rug.get("risk", "N/A")
            report += f"\n⚠️ **RugCheck Risk: {risk}/100** (Lower = Riskier)\n"
            top_holder = rug.get("topHolderPercent", 0)
            top10 = rug.get("top10HolderPercent", 0)
            report += f"👑 Top Holder: {top_holder:.1f}%\n"
            report += f"👥 Top 10: {top10:.1f}%\n"
            lp_locked = rug.get("lpLocked", False)
            lp_burned = rug.get("lpBurned", False)
            report += f"🔒 LP Locked: {'✅' if lp_locked else '❌'}\n"
            report += f"🔥 LP Burned: {'✅' if lp_burned else '❌'}\n"
            mint_rev = rug.get("mintDisabled", False)
            freeze_rev = rug.get("freezeDisabled", False)
            report += f"🚫 Mint Revoked: {'✅' if mint_rev else '❌'}\n"
            report += f"⛄ Freeze Revoked: {'✅' if freeze_rev else '❌'}\n"
            hp_flag = rug.get("honeypotFlag", rug.get("isHoneypot", False))
            report += f"🐝 Honeypot: {'🚨 High' if hp_flag else '✅ Low'}\n"
        else:
            report += "\n❌ No RugCheck data available.\n"
        report += f"📊 Total Supply: {meta.get('supply', 0):,.0f}\n"
        return report

    def rug_check(self, args: list) -> str:
        if len(args) < 1 or len(args[0]) != 44:
            return "Usage: solana_rug_check <44-char token_address>"
        address = args[0]
        rug = self.get_rugcheck_report(address)
        ds = self.get_dexscreener_data(address)
        if not rug:
            return f"❌ Unable to fetch RugCheck data for {address}"
        risk = rug.get("risk", 0)
        top_holder = rug.get("topHolderPercent", 0)
        status = "🟢 Low Risk" if risk > 80 else "🟡 Medium Risk" if risk > 50 else "🔴 High Risk"
        report = f"**Rug Check: {address[:8]}...**\n"
        report += f"{status} (Score: {risk}/100)\n\n"
        report += f"Top Holder: {top_holder:.1f}%\n"
        report += f"LP Locked: {'✅' if rug.get('lpLocked') else '❌'}\n"
        report += f"LP Burned: {'✅' if rug.get('lpBurned') else '❌'}\n"
        report += f"Mint Revoked: {'✅' if rug.get('mintDisabled') else '❌'}\n"
        if ds and ds.get('is_pumpdotfun'):
            report += "\n⚠️ Pump.fun (pre-migration)"
        return report
    
    def _check_for_skill_event(self, platform, response):
        """Check API response for skill update notices (required for SyMod registration)"""
        try:
            if not isinstance(response, dict):
                return
            
            # Check for skill update events in API responses
            if 'skill_update' in response or 'skill_event' in response:
                print(f"📚 Skill update detected from {platform}")
                # Plugin is now registered with SyMod
        except Exception as e:
            pass  # Silent fail - not critical

PLUGIN_INFO = {
    "name": "solana_token_analysis",
    "version": "1.0.0",
    "description": "Analyzes Solana tokens for rug risks, liquidity, LP status, holders, honeypot using RugCheck/DexScreener/Solscan",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return SolanaTokenAnalysisPlugin(config or {})