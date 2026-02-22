# plugins/btc_vol_fed/btc_vol_fed.py
import os
import json
import time
import math
import re
import requests
from typing import Dict
from plugin_manager import AlleyBotPlugin


def mean(lst):
    return sum(lst) / len(lst) if lst else 0.0


def stdev(lst):
    n = len(lst)
    if n < 2:
        return 0.0
    m = mean(lst)
    variance = sum((x - m) ** 2 for x in lst) / (n - 1)
    return math.sqrt(variance)


class BtcVolFedPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "btc_vol_fed"
        self.version = "1.0.0"
        self.cache_file = os.path.join(os.path.dirname(__file__), "btc_vol_fed_cache.json")
        self.cache_ttls = {"btc": 300, "fed": 1800}
        self.cache = {"btc": {"ts": 0}, "fed": {"ts": 0}}
        self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, "r") as f:
                loaded = json.load(f)
                for key in ["btc", "fed"]:
                    if key in loaded:
                        self.cache[key] = loaded[key]
        except Exception:
            pass

    def save_cache(self, key: str, data: dict):
        self.cache[key]["data"] = data
        self.cache[key]["ts"] = time.time()
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def calculate_atr(self, highs: list, lows: list, closes: list, period: int = 14) -> float:
        if len(highs) < 2:
            return 0.0
        trs = []
        prev_c = closes[0]
        for h, l, c in zip(highs[1:], lows[1:], closes[1:]):
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            trs.append(tr)
            prev_c = c
        if not trs:
            return 0.0
        n = min(period, len(trs))
        return mean(trs[-n:])

    def fetch_btc(self, hours: int) -> dict:
        for attempt in range(3):
            try:
                days = max(1, int(hours / 24.0) + 1)
                url = f"https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days={days}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    ohlcv = resp.json()
                    now_ms = int(time.time() * 1000)
                    cutoff = now_ms - hours * 3600 * 1000
                    recent = [c for c in ohlcv if c[0] >= cutoff]
                    if not recent:
                        return {"error": "No recent data"}
                    highs = [float(c[2]) for c in recent]
                    lows = [float(c[3]) for c in recent]
                    closes = [float(c[4]) for c in recent]
                    log_rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
                    std_vol = stdev(log_rets) * 100 if len(log_rets) > 1 else 0.0
                    atr = self.calculate_atr(highs, lows, closes)
                    atr_pct = (atr / mean(closes)) * 100 if closes else 0.0
                    return {
                        "std_vol_pct": round(std_vol, 2),
                        "atr_pct": round(atr_pct, 2),
                        "n_candles": len(recent),
                        "period_hours": hours,
                        "mean_price": round(mean(closes), 2),
                    }
                time.sleep(1)
            except Exception:
                time.sleep(1)
        return {"error": "Failed after retries"}

    def fetch_fed(self, appid: str) -> dict:
        for attempt in range(3):
            try:
                url = "https://api.wolframalpha.com/v2/query"
                params = {
                    "input": "current federal funds rate",
                    "appid": appid,
                    "format": "plaintext",
                    "output": "json",
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    qr = data.get("queryresult", {})
                    rate = "N/A"
                    if qr.get("success"):
                        for pod in qr.get("pods", []):
                            if "funds" in pod.get("title", "").lower() or "rate" in pod.get("title", "").lower():
                                sp = pod.get("subpods", [{}])[0].get("plaintext", "")
                                match = re.search(r"(\d+\.?\d*)%", sp)
                                if match:
                                    rate = match.group(1)
                                break
                    params["input"] = "federal funds rate changes last 3 months"
                    resp2 = requests.get(url, params=params, timeout=10)
                    changes = "N/A"
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        qr2 = data2.get("queryresult", {})
                        if qr2.get("success"):
                            for pod in qr2.get("pods", []):
                                title = pod.get("title", "").lower()
                                if any(w in title for w in ["change", "history", "decision"]):
                                    changes = pod.get("subpods", [{}])[0].get("plaintext", "")[:150]
                                    break
                    return {"rate": rate, "recent_changes": changes}
                time.sleep(1)
            except Exception:
                time.sleep(1)
        return {"error": "Failed after retries"}

    def get_commands(self) -> Dict[str, callable]:
        return {
            "btc_vol_fed": self.btc_vol_fed,
        }

    def btc_vol_fed(self, args: list) -> str:
        hours = 24
        if args:
            try:
                hours = int(args[0])
            except ValueError:
                hours = 24
        appid = self.config.get("wolfram_appid", "DEMO")
        now = time.time()

        # BTC
        btc_key = "btc"
        if now - self.cache[btc_key]["ts"] > self.cache_ttls["btc"]:
            btc_data = self.fetch_btc(hours)
            self.save_cache(btc_key, btc_data)
        else:
            btc_data = self.cache[btc_key]["data"]

        # Fed
        fed_key = "fed"
        if now - self.cache[fed_key]["ts"] > self.cache_ttls["fed"]:
            fed_data = self.fetch_fed(appid)
            self.save_cache(fed_key, fed_data)
        else:
            fed_data = self.cache[fed_key]["data"]

        if "error" in btc_data:
            btc_summary = f"BTC fetch error: {btc_data['error']}"
        else:
            std_vol = btc_data.get("std_vol_pct", 0)
            atr_pct = btc_data.get("atr_pct", 0)
            n_candles = btc_data.get("n_candles", 0)
            mean_price = btc_data.get("mean_price", 0)
            btc_summary = f"""BTC {hours}h Vol:
Std log returns: {std_vol}%
ATR: {atr_pct}%
Price: ~${mean_price}
Candles: {n_candles}"""

        if "error" in fed_data:
            fed_summary = f"Fed fetch error: {fed_data['error']}"
        else:
            fed_summary = f"""Fed Rate: {fed_data.get('rate', 'N/A')}%
Recent: {fed_data.get('recent_changes', 'N/A')}"""

        alert = ""
        if btc_data.get("std_vol_pct", 0) > 2.0:
            alert += "High BTC vol detected. "
        changes = fed_data.get("recent_changes", "").lower()
        if any(word in changes for word in ["hike", "cut", "raised", "lowered", "change"]):
            alert += "Recent Fed rate event noted."

        note = "Note: Verify Fed data at federalreserve.gov; Wolfram is an oracle."
        return f"{btc_summary}\n\n{fed_summary}\n\n{alert}\n{note}".strip()


PLUGIN_INFO = {
    "name": "btc_vol_fed",
    "version": "1.0.0",
    "description": "BTC volatility (std/ATR) vs Fed funds rate correlations, with caching & alerts",
    "author": "AlleyBot",
}


def create_plugin(config=None):
    return BtcVolFedPlugin(config or {})