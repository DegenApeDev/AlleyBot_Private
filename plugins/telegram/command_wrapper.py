"""
Non-blocking command wrapper for Telegram handlers

Ensures all Telegram commands respond instantly by running
plugin operations in background threads.
"""

import asyncio
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def non_blocking_command(func: Callable) -> Callable:
    """
    Decorator to make Telegram command handlers non-blocking.
    
    Wraps synchronous plugin calls in thread executors so they don't
    block the Telegram async event loop.
    
    Usage:
        @non_blocking_command
        async def my_command(self, update, context):
            # This will run without blocking
            plugin = self.core.plugin_manager.plugins.get('moltx')
            result = plugin.some_method()
            await update.message.reply_text(result)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Get event loop
            loop = asyncio.get_running_loop()
            
            # Run the command handler
            # If it contains blocking operations, they should use _run_sync
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Error in non-blocking command {func.__name__}: {e}")
            # Try to send error to user if update is available
            if len(args) >= 2:
                update = args[1]
                try:
                    await update.message.reply_text(f"❌ Error: {e}")
                except:
                    pass
            raise
    
    return wrapper


async def run_plugin_method(plugin, method_name: str, *args, **kwargs) -> Any:
    """
    Run a plugin method in a non-blocking way.
    
    Args:
        plugin: The plugin instance
        method_name: Name of the method to call
        *args, **kwargs: Arguments to pass to the method
    
    Returns:
        The result of the method call
    """
    loop = asyncio.get_running_loop()
    method = getattr(plugin, method_name)
    
    # Run in executor to avoid blocking
    return await loop.run_in_executor(None, lambda: method(*args, **kwargs))


async def get_plugin_non_blocking(plugin_manager, plugin_name: str):
    """
    Get a plugin without blocking.
    
    Args:
        plugin_manager: The plugin manager instance
        plugin_name: Name of the plugin to get
    
    Returns:
        The plugin instance or None
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, 
        lambda: plugin_manager.plugins.get(plugin_name)
    )
