import aiohttp
from typing import Dict, Any, Optional

class SolscanClient:
    BASE_URL = "https://public-api.solscan.io"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "SolscanClient":
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        url = f"{self.BASE_URL}{endpoint}"
        try:
            async with self.session.request(method, url, params=params) as resp:
                try:
                    data = await resp.json()
                except aiohttp.ContentTypeError:
                    data = await resp.text()
                if 200 <= resp.status < 300:
                    return {"success": True, "data": data.get("data", data) if isinstance(data, dict) and "data" in data else data}
                else:
                    return {"success": False, "error": f"HTTP {resp.status}: {data}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_token_meta(self, token_address: str) -> Dict[str, Any]:
        endpoint = "/token/meta"
        params = {"tokenAddress": token_address}
        return await self._request("GET", endpoint, params=params)

    async def get_token_supply(self, token_address: str) -> Dict[str, Any]:
        endpoint = "/token/supply"
        params = {"token": token_address}
        return await self._request("GET", endpoint, params=params)

    async def get_token_authority(self, token_address: str) -> Dict[str, Any]:
        endpoint = "/token/authority"
        params = {"token": token_address}
        return await self._request("GET", endpoint, params=params)

    async def get_top_holders(self, token_address: str, size: int = 10) -> Dict[str, Any]:
        endpoint = "/token/holders"
        params = {"tokenAddress": token_address, "offset": 0, "size": size}
        return await self._request("GET", endpoint, params=params)

    async def get_recent_transactions(self, token_address: str, limit: int = 10) -> Dict[str, Any]:
        endpoint = "/token/transfers"
        params = {"tokenAddress": token_address, "offset": 0, "limit": limit}
        return await self._request("GET", endpoint, params=params)

class BirdeyeClient:
    BASE_URL = "https://public-api.birdeye.so"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "BirdeyeClient":
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "X-API-KEY": self.api_key,
            "x-chain": "solana",
        }
        self.session = aiohttp.ClientSession(headers=headers, connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        try:
            async with self.session.request(method, url, params=params) as resp:
                try:
                    data = await resp.json()
                except aiohttp.ContentTypeError:
                    data = await resp.text()
                if 200 <= resp.status < 300:
                    return {"success": True, "data": data.get("data", data) if isinstance(data, dict) and "data" in data else data}
                else:
                    return {"success": False, "error": f"HTTP {resp.status}: {data}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_token_overview(self, token_address: str) -> Dict[str, Any]:
        endpoint = f"/defi/token_overview/solana/{token_address}"
        params = {
            "include_liquidity": "true",
            "check_liquidity": "true",
            "include_lps": "true",
            "lp_count": 5,
        }
        return await self._request("GET", endpoint, params=params)

    async def get_token_pools(self, token_address: str) -> Dict[str, Any]:
        endpoint = f"/defi/token_pools/solana/{token_address}"
        return await self._request("GET", endpoint)

    async def get_recent_transactions(self, token_address: str, limit: int = 50) -> Dict[str, Any]:
        endpoint = f"/defi/token_txs/solana/{token_address}"
        params = {"offset": 0, "limit": limit}
        return await self._request("GET", endpoint)

    async def get_security_check(self, token_address: str) -> Dict[str, Any]:
        endpoint = f"/defi/security/solana/{token_address}"
        return await self._request("GET", endpoint)