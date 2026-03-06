"""
Standardized Error Handling for AlleyBot
Provides consistent error handling, logging, and recovery patterns across all plugins.
"""
import logging
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base exception for plugin errors"""
    def __init__(self, plugin_name: str, message: str, original_error: Optional[Exception] = None):
        self.plugin_name = plugin_name
        self.message = message
        self.original_error = original_error
        self.timestamp = datetime.now().isoformat()
        super().__init__(f"[{plugin_name}] {message}")


class APIError(PluginError):
    """API-related errors"""
    pass


class ConfigurationError(PluginError):
    """Configuration-related errors"""
    pass


class AuthenticationError(PluginError):
    """Authentication/authorization errors"""
    pass


class RateLimitError(PluginError):
    """Rate limiting errors"""
    pass


class ErrorHandler:
    """Centralized error handling with logging and recovery"""
    
    def __init__(self, plugin_name: str, logger_instance: Optional[logging.Logger] = None):
        self.plugin_name = plugin_name
        self.logger = logger_instance or logger
        self.error_count = 0
        self.last_error = None
    
    def handle_error(
        self, 
        error: Exception, 
        context: str = "", 
        user_message: Optional[str] = None,
        silent: bool = False
    ) -> str:
        """
        Handle an error with consistent logging and user feedback
        
        Args:
            error: The exception that occurred
            context: Context about where/why the error occurred
            user_message: Custom message to show to user (if None, generates one)
            silent: If True, don't log to console (still logs to file)
        
        Returns:
            User-friendly error message
        """
        self.error_count += 1
        self.last_error = error
        
        # Generate error message
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Log the error
        log_msg = f"[{self.plugin_name}] {context}: {error_type}: {error_msg}"
        if not silent:
            self.logger.error(log_msg)
            if hasattr(error, '__traceback__'):
                self.logger.debug(traceback.format_exc())
        
        # Generate user message
        if user_message:
            return user_message
        
        # Default user messages based on error type
        if isinstance(error, (ConnectionError, TimeoutError)):
            return f"❌ Connection error in {self.plugin_name}. Please try again."
        elif isinstance(error, RateLimitError):
            return f"⏸️ Rate limit reached for {self.plugin_name}. Please wait a moment."
        elif isinstance(error, AuthenticationError):
            return f"🔒 Authentication failed for {self.plugin_name}. Check credentials."
        elif isinstance(error, ConfigurationError):
            return f"⚙️ Configuration error in {self.plugin_name}. Check settings."
        elif "404" in error_msg or "not found" in error_msg.lower():
            return f"❌ Resource not found in {self.plugin_name}"
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            return f"🔒 Access denied in {self.plugin_name}"
        elif "500" in error_msg or "503" in error_msg:
            return f"❌ {self.plugin_name} service temporarily unavailable"
        else:
            return f"❌ Error in {self.plugin_name}: {error_msg[:100]}"
    
    def safe_execute(
        self,
        func: Callable,
        *args,
        default_return: Any = None,
        error_message: Optional[str] = None,
        context: str = "",
        **kwargs
    ) -> Any:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            default_return: Value to return on error
            error_message: Custom error message for user
            context: Context about the operation
            **kwargs: Keyword arguments for func
        
        Returns:
            Function result or default_return on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = self.handle_error(e, context=context or func.__name__, user_message=error_message)
            if default_return is not None:
                return default_return
            return msg
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'plugin': self.plugin_name,
            'error_count': self.error_count,
            'last_error': str(self.last_error) if self.last_error else None,
            'last_error_type': type(self.last_error).__name__ if self.last_error else None
        }


def safe_plugin_method(
    default_return: Any = None,
    error_prefix: str = "❌",
    log_errors: bool = True
):
    """
    Decorator for plugin methods to add standardized error handling
    
    Usage:
        @safe_plugin_method(default_return="Error occurred")
        def my_method(self, arg):
            # method code
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                plugin_name = getattr(self, 'name', self.__class__.__name__)
                
                if log_errors:
                    logger.error(f"[{plugin_name}] Error in {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())
                
                # Try to use plugin's error handler if available
                if hasattr(self, 'error_handler'):
                    return self.error_handler.handle_error(
                        e, 
                        context=func.__name__,
                        user_message=f"{error_prefix} {func.__name__} failed"
                    )
                
                # Fallback to default return or error message
                if default_return is not None:
                    return default_return
                
                return f"{error_prefix} Error in {func.__name__}: {str(e)[:100]}"
        
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function on error with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exception types to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed for {func.__name__}: {e}")
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


def log_exceptions(logger_instance: Optional[logging.Logger] = None):
    """
    Decorator to log exceptions without suppressing them
    
    Usage:
        @log_exceptions()
        def my_function():
            # function code
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_instance or logger
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.error(f"Exception in {func.__name__}: {e}")
                log.debug(traceback.format_exc())
                raise
        
        return wrapper
    return decorator


# Convenience function for quick error handling
def handle_plugin_error(
    plugin_name: str,
    error: Exception,
    context: str = "",
    silent: bool = False
) -> str:
    """Quick error handling without creating ErrorHandler instance"""
    handler = ErrorHandler(plugin_name)
    return handler.handle_error(error, context=context, silent=silent)
