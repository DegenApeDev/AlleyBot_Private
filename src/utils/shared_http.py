"""
Shared HTTP utility for AlleyBot plugins.

Provides connection-pooled, thread-pooled HTTP calls so sync requests
never block the event loop. Plugins share one Session + one Executor.

Usage:
    from src.utils.shared_http import http_get, http_post, http_request

    # Sync call in a thread pool — return value is a requests.Response
    resp = http_get('https://api.example.com/data', timeout=10)
    data = resp.json()

Thread safety: Session and Executor are thread-safe. The underlying
requests.Session handles connection pooling (keepalive, SSL reuse).
"""
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any, Union

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared resources
# ---------------------------------------------------------------------------

_POOL: ThreadPoolExecutor = None
_SESSION: requests.Session = None
_LOCK = threading.Lock()
_INITIALIZED = False

# Default pool size: one thread per plugin family + spare
POOL_SIZE = 8
REQUEST_TIMEOUT = 15  # seconds


def _ensure_initialized():
    """Lazy-init the shared session + pool on first use."""
    global _POOL, _SESSION, _INITIALIZED
    if _INITIALIZED:
        return
    with _LOCK:
        if _INITIALIZED:
            return
        _POOL = ThreadPoolExecutor(
            max_workers=POOL_SIZE,
            thread_name_prefix="http-pool",
        )
        _SESSION = requests.Session()
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=POOL_SIZE,
            pool_maxsize=POOL_SIZE * 2,
            max_retries=0,
        )
        _SESSION.mount("https://", adapter)
        _SESSION.mount("http://", adapter)
        _SESSION.headers.update({
            "User-Agent": "AlleyBot/1.0",
            "Accept": "application/json, */*",
        })
        _INITIALIZED = True
        logger.info(
            "🌐 Shared HTTP initialized: pool=%d workers, session keepalive",
            POOL_SIZE,
        )


def get_session() -> requests.Session:
    """Get the shared requests.Session (lazy-init)."""
    _ensure_initialized()
    return _SESSION


def get_pool() -> ThreadPoolExecutor:
    """Get the shared ThreadPoolExecutor (lazy-init)."""
    _ensure_initialized()
    return _POOL


# ---------------------------------------------------------------------------
# Public API — synchronous wrappers that run in the shared thread pool
# ---------------------------------------------------------------------------

def http_request(
    method: str,
    url: str,
    *,
    params: Optional[Dict] = None,
    json: Any = None,
    data: Any = None,
    headers: Optional[Dict] = None,
    timeout: Optional[int] = None,
    **kwargs,
) -> requests.Response:
    """Execute an HTTP request using the shared connection pool.

    This is a SYNCHRONOUS call intended to be run inside a thread pool
    (e.g. via asyncio.get_event_loop().run_in_executor(http_pool, ...)).

    Returns a requests.Response directly.
    """
    _ensure_initialized()
    merged = _SESSION.headers.copy()
    if headers:
        merged.update(headers)
    return _SESSION.request(
        method,
        url,
        params=params,
        json=json,
        data=data,
        headers=merged,
        timeout=timeout if timeout is not None else REQUEST_TIMEOUT,
        **kwargs,
    )


def http_get(url: str, **kwargs) -> requests.Response:
    """HTTP GET via shared connection pool."""
    return http_request("GET", url, **kwargs)


def http_post(url: str, **kwargs) -> requests.Response:
    """HTTP POST via shared connection pool."""
    return http_request("POST", url, **kwargs)


# ---------------------------------------------------------------------------
# Async wrappers — for use in async contexts (Telegram handlers, etc.)
# ---------------------------------------------------------------------------

async def async_http_request(
    method: str,
    url: str,
    **kwargs,
) -> requests.Response:
    """Async HTTP request — runs sync call in shared thread pool.

    Use this from async handlers (Telegram, web server) to avoid
    blocking the event loop.
    """
    _ensure_initialized()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _POOL,
        lambda: http_request(method, url, **kwargs),
    )


async def async_http_get(url: str, **kwargs) -> requests.Response:
    """Async HTTP GET."""
    return await async_http_request("GET", url, **kwargs)


async def async_http_post(url: str, **kwargs) -> requests.Response:
    """Async HTTP POST."""
    return await async_http_request("POST", url, **kwargs)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def shutdown():
    """Clean shutdown of shared resources. Call on app exit."""
    global _POOL, _SESSION, _INITIALIZED
    with _LOCK:
        if _SESSION:
            _SESSION.close()
            _SESSION = None
        if _POOL:
            _POOL.shutdown(wait=True)
            _POOL = None
        _INITIALIZED = False
        logger.info("🌐 Shared HTTP shut down")
