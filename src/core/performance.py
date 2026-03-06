"""
Performance Optimization Utilities for AlleyBot
Provides caching, rate limiting, and performance monitoring tools.
"""
import time
import functools
import logging
from typing import Any, Callable, Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 128, ttl: Optional[int] = None):
        """
        Args:
            max_size: Maximum number of items to cache
            ttl: Time-to-live in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Tuple[bool, Any]:
        """Get item from cache. Returns (found, value)"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return False, None
            
            # Check TTL
            if self.ttl and key in self.timestamps:
                age = time.time() - self.timestamps[key]
                if age > self.ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    self.misses += 1
                    return False, None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return True, self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    if oldest_key in self.timestamps:
                        del self.timestamps[oldest_key]
            
            self.cache[key] = value
            if self.ttl:
                self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cached items"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hits = 0
            self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, calls_per_second: float = 1.0, burst: int = 1):
        """
        Args:
            calls_per_second: Maximum sustained rate
            burst: Maximum burst size
        """
        self.rate = calls_per_second
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a call
        
        Args:
            blocking: If True, wait until permission granted
            timeout: Maximum time to wait (None = infinite)
        
        Returns:
            True if permission granted, False otherwise
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                self.last_update = now
                
                # Add tokens based on elapsed time
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if not blocking:
                    return False
                
                if timeout and (time.time() - start_time) >= timeout:
                    return False
            
            # Wait a bit before retrying
            time.sleep(0.01)


def cached(max_size: int = 128, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results
    
    Args:
        max_size: Maximum cache size
        ttl: Time-to-live in seconds
        key_func: Custom function to generate cache key from args
    
    Usage:
        @cached(max_size=256, ttl=300)
        def expensive_function(arg1, arg2):
            return result
    """
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size=max_size, ttl=ttl)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use string representation of args/kwargs
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            found, value = cache.get(cache_key)
            if found:
                return value
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        # Expose cache for inspection
        wrapper.cache = cache
        return wrapper
    
    return decorator


def rate_limited(calls_per_second: float = 1.0, burst: int = 1):
    """
    Decorator to rate limit function calls
    
    Args:
        calls_per_second: Maximum sustained rate
        burst: Maximum burst size
    
    Usage:
        @rate_limited(calls_per_second=2.0, burst=5)
        def api_call():
            return response
    """
    def decorator(func: Callable) -> Callable:
        limiter = RateLimiter(calls_per_second=calls_per_second, burst=burst)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            limiter.acquire(blocking=True)
            return func(*args, **kwargs)
        
        # Expose limiter for inspection
        wrapper.limiter = limiter
        return wrapper
    
    return decorator


def timed(log_threshold: Optional[float] = None):
    """
    Decorator to measure and log function execution time
    
    Args:
        log_threshold: Only log if execution time exceeds this (seconds)
    
    Usage:
        @timed(log_threshold=1.0)
        def slow_function():
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            if log_threshold is None or elapsed >= log_threshold:
                logger.info(f"{func.__name__} took {elapsed:.3f}s")
            
            return result
        
        return wrapper
    
    return decorator


class MemoryCache:
    """Simple in-memory cache with TTL support for plugin data"""
    
    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.lock = threading.Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        with self.lock:
            if key not in self._cache:
                return default
            
            value, expires_at = self._cache[key]
            
            # Check expiration
            if time.time() > expires_at:
                del self._cache[key]
                return default
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        with self.lock:
            expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
            self._cache[key] = (value, expires_at)
    
    def delete(self, key: str):
        """Delete key from cache"""
        with self.lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cached data"""
        with self.lock:
            self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self.lock:
            now = time.time()
            expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class BatchProcessor:
    """Batch multiple operations for efficient processing"""
    
    def __init__(self, batch_size: int = 10, flush_interval: float = 1.0):
        """
        Args:
            batch_size: Process when this many items accumulated
            flush_interval: Process after this many seconds
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.items = []
        self.last_flush = time.time()
        self.lock = threading.Lock()
    
    def add(self, item: Any) -> bool:
        """
        Add item to batch
        
        Returns:
            True if batch was flushed
        """
        with self.lock:
            self.items.append(item)
            
            # Check if we should flush
            should_flush = (
                len(self.items) >= self.batch_size or
                (time.time() - self.last_flush) >= self.flush_interval
            )
            
            if should_flush:
                return True
            
            return False
    
    def get_batch(self) -> list:
        """Get current batch and reset"""
        with self.lock:
            batch = self.items.copy()
            self.items.clear()
            self.last_flush = time.time()
            return batch


def debounce(wait: float):
    """
    Decorator to debounce function calls (only execute after wait seconds of inactivity)
    
    Args:
        wait: Seconds to wait before executing
    
    Usage:
        @debounce(wait=2.0)
        def on_change():
            # Only called after 2 seconds of no calls
            pass
    """
    def decorator(func: Callable) -> Callable:
        timer = None
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            
            def call_func():
                func(*args, **kwargs)
            
            with lock:
                if timer:
                    timer.cancel()
                timer = threading.Timer(wait, call_func)
                timer.start()
        
        return wrapper
    
    return decorator


def memoize_with_expiry(expiry_seconds: int = 3600):
    """
    Memoize function results with expiration
    
    Args:
        expiry_seconds: Cache expiration time
    
    Usage:
        @memoize_with_expiry(expiry_seconds=300)
        def get_data(key):
            return expensive_operation(key)
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        timestamps = {}
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            
            with lock:
                # Check if cached and not expired
                if key in cache:
                    age = time.time() - timestamps[key]
                    if age < expiry_seconds:
                        return cache[key]
                
                # Compute and cache
                result = func(*args, **kwargs)
                cache[key] = result
                timestamps[key] = time.time()
                return result
        
        return wrapper
    
    return decorator


# Global performance monitoring
class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
    
    def record(self, metric_name: str, value: float):
        """Record a performance metric"""
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            self.metrics[metric_name].append({
                'value': value,
                'timestamp': time.time()
            })
            # Keep last 1000 entries
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        with self.lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return {}
            
            values = [m['value'] for m in self.metrics[metric_name]]
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'recent': values[-1] if values else 0
            }
    
    def clear(self):
        """Clear all metrics"""
        with self.lock:
            self.metrics.clear()


# Global instance
perf_monitor = PerformanceMonitor()
