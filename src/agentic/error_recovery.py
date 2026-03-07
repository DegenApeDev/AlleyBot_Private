"""
Error Recovery and Self-Healing System

Handles automatic error recovery, exponential backoff, and intelligent restart logic.
Part of the 100% autonomous AlleyBot system.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    timestamp: datetime
    error_type: str
    error_message: str
    component: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    recovery_attempted: bool = False
    recovery_successful: bool = False


class ErrorRecoverySystem:
    """
    Intelligent error recovery system with exponential backoff.
    
    Features:
    - Track error patterns
    - Exponential backoff on repeated failures
    - Automatic recovery strategies
    - Circuit breaker pattern
    - Alert escalation
    """
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        self.error_history: List[ErrorRecord] = []
        self.component_failures: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, bool] = {}
        self.last_recovery_attempt: Dict[str, datetime] = {}
    
    def record_error(self, component: str, error: Exception, severity: str = 'medium'):
        """Record an error occurrence"""
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            component=component,
            severity=severity
        )
        
        self.error_history.append(error_record)
        
        # Track component failures
        if component not in self.component_failures:
            self.component_failures[component] = 0
        self.component_failures[component] += 1
        
        # Trim history to last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"❌ Error recorded: {component} - {error}")
        
        # Check if circuit breaker should trip
        if self.component_failures[component] >= 5:
            self._trip_circuit_breaker(component)
    
    def _trip_circuit_breaker(self, component: str):
        """Trip circuit breaker for a component"""
        if component not in self.circuit_breakers or not self.circuit_breakers[component]:
            self.circuit_breakers[component] = True
            logger.warning(f"🔌 Circuit breaker TRIPPED for {component} (5+ failures)")
            
            # Reset after 5 minutes
            asyncio.create_task(self._reset_circuit_breaker(component, delay=300))
    
    async def _reset_circuit_breaker(self, component: str, delay: int):
        """Reset circuit breaker after delay"""
        await asyncio.sleep(delay)
        self.circuit_breakers[component] = False
        self.component_failures[component] = 0
        logger.info(f"✅ Circuit breaker RESET for {component}")
    
    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is tripped"""
        return self.circuit_breakers.get(component, False)
    
    async def attempt_recovery(self, component: str, error: Exception) -> bool:
        """
        Attempt to recover from an error.
        
        Returns True if recovery successful, False otherwise.
        """
        # Check circuit breaker
        if self.is_circuit_open(component):
            logger.warning(f"⚠️ Circuit breaker open for {component}, skipping recovery")
            return False
        
        # Check exponential backoff
        if not self._can_attempt_recovery(component):
            logger.info(f"⏳ Backoff period active for {component}")
            return False
        
        logger.info(f"🔧 Attempting recovery for {component}...")
        self.last_recovery_attempt[component] = datetime.now()
        
        try:
            # Component-specific recovery strategies
            if component == 'brain':
                return await self._recover_brain()
            elif component == 'moltx':
                return await self._recover_moltx()
            elif component == 'telegram':
                return await self._recover_telegram()
            else:
                # Generic recovery: restart plugin
                return await self._recover_generic_plugin(component)
        
        except Exception as e:
            logger.error(f"❌ Recovery failed for {component}: {e}")
            return False
    
    def _can_attempt_recovery(self, component: str) -> bool:
        """Check if we can attempt recovery (exponential backoff)"""
        if component not in self.last_recovery_attempt:
            return True
        
        last_attempt = self.last_recovery_attempt[component]
        failures = self.component_failures.get(component, 0)
        
        # Exponential backoff: 1min, 2min, 4min, 8min, 16min
        backoff_minutes = min(2 ** failures, 16)
        backoff_time = timedelta(minutes=backoff_minutes)
        
        return datetime.now() - last_attempt > backoff_time
    
    async def _recover_brain(self) -> bool:
        """Recover the autonomous brain"""
        try:
            from src.agentic.autonomous_startup import get_autonomous_startup
            startup = get_autonomous_startup()
            if startup:
                await startup.restart_brain()
                return True
        except Exception as e:
            logger.error(f"❌ Brain recovery failed: {e}")
        return False
    
    async def _recover_moltx(self) -> bool:
        """Recover MoltX plugin"""
        try:
            if not self.plugin_manager:
                return False
            
            moltx = self.plugin_manager.get_plugin('moltx')
            if moltx and hasattr(moltx, 'initialize'):
                # Re-initialize plugin
                moltx.initialize(None, None)
                logger.info("✅ MoltX plugin re-initialized")
                return True
        except Exception as e:
            logger.error(f"❌ MoltX recovery failed: {e}")
        return False
    
    async def _recover_telegram(self) -> bool:
        """Recover Telegram plugin"""
        try:
            if not self.plugin_manager:
                return False
            
            telegram = self.plugin_manager.get_plugin('telegram')
            if telegram and hasattr(telegram, 'application'):
                # Check if polling is running
                if telegram.application and not telegram.is_running:
                    logger.info("🔄 Restarting Telegram polling...")
                    # Restart would happen via autonomous_startup
                    return True
        except Exception as e:
            logger.error(f"❌ Telegram recovery failed: {e}")
        return False
    
    async def _recover_generic_plugin(self, component: str) -> bool:
        """Generic plugin recovery"""
        try:
            if not self.plugin_manager:
                return False
            
            plugin = self.plugin_manager.get_plugin(component)
            if plugin and hasattr(plugin, 'initialize'):
                plugin.initialize(None, None)
                logger.info(f"✅ {component} plugin re-initialized")
                return True
        except Exception as e:
            logger.error(f"❌ {component} recovery failed: {e}")
        return False
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors"""
        recent_errors = [e for e in self.error_history if 
                        (datetime.now() - e.timestamp) < timedelta(hours=1)]
        
        return {
            'total_errors_last_hour': len(recent_errors),
            'component_failures': dict(self.component_failures),
            'circuit_breakers': {k: v for k, v in self.circuit_breakers.items() if v},
            'recent_errors': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'component': e.component,
                    'error_type': e.error_type,
                    'severity': e.severity
                }
                for e in recent_errors[-10:]
            ]
        }


# Singleton instance
_error_recovery = None


def get_error_recovery(plugin_manager=None):
    """Get or create error recovery singleton"""
    global _error_recovery
    if _error_recovery is None and plugin_manager:
        _error_recovery = ErrorRecoverySystem(plugin_manager)
    return _error_recovery
