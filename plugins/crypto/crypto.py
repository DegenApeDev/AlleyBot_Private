"""
Crypto Price Plugin for AlleyBot
Fetches live crypto prices from CoinGecko (free, no API key needed).
"""
import os
import sys
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from plugin_manager import AlleyBotPlugin


# Common symbol → CoinGecko ID mapping
COIN_MAP = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'sol': 'solana',
    'usdc': 'usd-coin',
    'usdt': 'tether',
    'bnb': 'binancecoin',
    'xrp': 'ripple',
    'ada': 'cardano',
    'doge': 'dogecoin',
    'avax': 'avalanche-2',
    'dot': 'polkadot',
    'matic': 'matic-network',
    'pol': 'matic-network',
    'link': 'chainlink',
    'uni': 'uniswap',
    'aave': 'aave',
    'arb': 'arbitrum',
    'op': 'optimism',
    'base': 'base-protocol',
    'pepe': 'pepe',
    'wif': 'dogwifcoin',
    'bonk': 'bonk',
    'shib': 'shiba-inu',
    'atom': 'cosmos',
    'near': 'near',
    'apt': 'aptos',
    'sui': 'sui',
    'sei': 'sei-network',
    'ftm': 'fantom',
    'render': 'render-token',
    'inj': 'injective-protocol',
    'mkr': 'maker',
    'crv': 'curve-dao-token',
    'ldo': 'lido-dao',
    'pendle': 'pendle',
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class CryptoPlugin(AlleyBotPlugin):
    """Crypto price checking plugin using CoinGecko free API"""

    def __init__(self, config):
        super().__init__(config)
        self._cache = {}
        self._cache_ttl = 60  # seconds

    def initialize(self, api, core):
        super().initialize(api, core)
        print("✅ Crypto price plugin loaded")

    def _resolve_coin_id(self, symbol_or_id):
        """Resolve a ticker symbol or CoinGecko ID"""
        key = symbol_or_id.lower().strip().lstrip('$')
        return COIN_MAP.get(key, key)

    def _fetch_price(self, coin_id):
        """Fetch price data from CoinGecko with simple caching"""
        now = datetime.now().timestamp()
        if coin_id in self._cache:
            cached_time, cached_data = self._cache[coin_id]
            if now - cached_time < self._cache_ttl:
                return cached_data

        try:
            url = f"{COINGECKO_BASE}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false',
            }
            resp = requests.get(url, params=params, timeout=10)

            if resp.status_code == 429:
                return {'error': 'Rate limited — try again in a minute'}
            if resp.status_code == 404:
                return {'error': f'Coin "{coin_id}" not found on CoinGecko'}

            resp.raise_for_status()
            data = resp.json()

            market = data.get('market_data', {})
            result = {
                'id': data.get('id'),
                'symbol': data.get('symbol', '').upper(),
                'name': data.get('name'),
                'price_usd': market.get('current_price', {}).get('usd'),
                'price_btc': market.get('current_price', {}).get('btc'),
                'market_cap': market.get('market_cap', {}).get('usd'),
                'volume_24h': market.get('total_volume', {}).get('usd'),
                'change_24h': market.get('price_change_percentage_24h'),
                'change_7d': market.get('price_change_percentage_7d'),
                'ath': market.get('ath', {}).get('usd'),
                'ath_change': market.get('ath_change_percentage', {}).get('usd'),
                'circulating_supply': market.get('circulating_supply'),
                'total_supply': market.get('total_supply'),
            }

            self._cache[coin_id] = (now, result)
            return result

        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed: {e}'}
        except Exception as e:
            return {'error': f'Unexpected error: {e}'}

    def price_command(self, *args):
        """Check crypto price. Usage: crypto_price <symbol>"""
        if not args:
            return "❌ Usage: crypto_price <symbol>\nExample: crypto_price btc"

        query = args[0] if isinstance(args[0], str) else ' '.join(str(a) for a in args)
        coin_id = self._resolve_coin_id(query)
        data = self._fetch_price(coin_id)

        if 'error' in data:
            return f"❌ {data['error']}"

        price = data['price_usd']
        change_24h = data.get('change_24h')
        change_7d = data.get('change_7d')
        mcap = data.get('market_cap')
        vol = data.get('volume_24h')

        # Format price based on magnitude
        if price is None:
            return f"❌ No price data for {data.get('name', coin_id)}"
        elif price >= 1:
            price_str = f"${price:,.2f}"
        elif price >= 0.01:
            price_str = f"${price:,.4f}"
        else:
            price_str = f"${price:,.8f}"

        arrow_24h = "🟢" if change_24h and change_24h >= 0 else "🔴"
        arrow_7d = "🟢" if change_7d and change_7d >= 0 else "🔴"

        output = f"💰 {data['name']} ({data['symbol']})\n\n"
        output += f"  💵 Price: {price_str}\n"
        if change_24h is not None:
            output += f"  {arrow_24h} 24h: {change_24h:+.2f}%\n"
        if change_7d is not None:
            output += f"  {arrow_7d} 7d: {change_7d:+.2f}%\n"
        if mcap:
            output += f"  📊 MCap: ${mcap:,.0f}\n"
        if vol:
            output += f"  📈 Vol 24h: ${vol:,.0f}\n"
        if data.get('ath'):
            output += f"  🏔️ ATH: ${data['ath']:,.2f} ({data.get('ath_change', 0):+.1f}%)\n"

        return output

    def multi_price_command(self, *args):
        """Check multiple crypto prices. Usage: crypto_prices btc,eth,sol"""
        if not args:
            return "❌ Usage: crypto_prices btc,eth,sol"

        query = args[0] if isinstance(args[0], str) else ' '.join(str(a) for a in args)
        symbols = [s.strip() for s in query.replace(' ', ',').split(',') if s.strip()]

        if not symbols:
            return "❌ No symbols provided"

        if len(symbols) > 10:
            symbols = symbols[:10]

        output = "💰 Crypto Prices\n\n"
        for sym in symbols:
            coin_id = self._resolve_coin_id(sym)
            data = self._fetch_price(coin_id)
            if 'error' in data:
                output += f"  ❌ {sym.upper()}: {data['error']}\n"
            else:
                price = data['price_usd']
                change = data.get('change_24h')
                if price is None:
                    output += f"  ❌ {data['symbol']}: No price data\n"
                else:
                    arrow = "🟢" if change and change >= 0 else "🔴"
                    if price >= 1:
                        p = f"${price:,.2f}"
                    elif price >= 0.01:
                        p = f"${price:,.4f}"
                    else:
                        p = f"${price:,.8f}"
                    chg = f" ({change:+.1f}%)" if change is not None else ""
                    output += f"  {arrow} {data['symbol']}: {p}{chg}\n"

        return output

    def trending_command(self, *args):
        """Show trending coins on CoinGecko"""
        try:
            resp = requests.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
            if resp.status_code != 200:
                return "❌ Failed to fetch trending coins"

            data = resp.json()
            coins = data.get('coins', [])

            if not coins:
                return "❌ No trending data available"

            output = "🔥 Trending Coins (CoinGecko)\n\n"
            for i, item in enumerate(coins[:10], 1):
                coin = item.get('item', {})
                name = coin.get('name', '?')
                symbol = coin.get('symbol', '?')
                rank = coin.get('market_cap_rank', '?')
                output += f"  {i}. {name} ({symbol}) — Rank #{rank}\n"

            return output

        except Exception as e:
            return f"❌ Error: {e}"

    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'crypto_price': self.price_command,
            'crypto_prices': self.multi_price_command,
            'crypto_trending': self.trending_command,
        }

    def get_tasks(self):
        return {}

    def get_endpoints(self):
        return {}
