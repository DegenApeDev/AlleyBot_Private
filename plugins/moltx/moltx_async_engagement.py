"""
MoltX Async Engagement
Non-blocking background engagement to prevent freezing the main thread
"""
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MoltxAsyncEngagementMixin:
    """Mixin for running engagement tasks asynchronously in background"""
    
    def __init__(self, *args, **kwargs):
        """Initialize async engagement"""
        super().__init__(*args, **kwargs)
        self._engagement_task = None
        self._engagement_running = False
    
    async def _run_engagement_async(self, engagement_func, *args, **kwargs) -> Optional[str]:
        """
        Run engagement function asynchronously in background
        
        Args:
            engagement_func: The engagement function to run
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Result from engagement function or None if already running
        """
        if self._engagement_running:
            logger.info("⏸️ Engagement already running in background, skipping...")
            return "⏸️ Engagement already in progress"
        
        try:
            self._engagement_running = True
            logger.info("🔄 Starting background engagement task...")
            
            # Run the engagement function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, engagement_func, *args, **kwargs)
            
            logger.info(f"✅ Background engagement complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Background engagement failed: {e}")
            return f"❌ Background engagement error: {e}"
        finally:
            self._engagement_running = False
    
    def start_engagement_background(self, engagement_func, *args, **kwargs) -> str:
        """
        Start engagement in background without blocking
        
        Args:
            engagement_func: The engagement function to run
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Status message
        """
        if self._engagement_running:
            return "⏸️ Engagement already running in background"
        
        # Create async task
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Schedule the task
        self._engagement_task = loop.create_task(
            self._run_engagement_async(engagement_func, *args, **kwargs)
        )
        
        return "🔄 Engagement started in background (non-blocking)"
    
    def is_engagement_running(self) -> bool:
        """Check if background engagement is currently running"""
        return self._engagement_running
    
    def get_engagement_status(self) -> Dict[str, Any]:
        """
        Get status of background engagement
        
        Returns:
            Dict with running status and task info
        """
        status = {
            'running': self._engagement_running,
            'has_task': self._engagement_task is not None
        }
        
        if self._engagement_task:
            status['task_done'] = self._engagement_task.done()
            if self._engagement_task.done():
                try:
                    status['result'] = self._engagement_task.result()
                except Exception as e:
                    status['error'] = str(e)
        
        return status


def make_engagement_async(func):
    """
    Decorator to make an engagement function run asynchronously
    
    Usage:
        @make_engagement_async
        def my_engagement_function(self, ...):
            # Long-running engagement code
            pass
    """
    async def async_wrapper(self, *args, **kwargs):
        if hasattr(self, 'start_engagement_background'):
            return self.start_engagement_background(func, self, *args, **kwargs)
        else:
            # Fallback to sync if mixin not available
            return func(self, *args, **kwargs)
    
    return async_wrapper
