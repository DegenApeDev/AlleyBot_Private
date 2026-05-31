"""
Domain Autonomy Manager - Graduated autonomy based on proven performance

Enables AlleyBot to automatically unlock high-risk domains (market, self_improvement)
once he has demonstrated consistent success and reliability.

Part of Sovereignty Enhancement - Phase 3: Graduated Domain Autonomy
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DomainTier(Enum):
    """Trust tiers for domain autonomy"""
    LOCKED = "locked"  # Domain completely disabled
    RESTRICTED = "restricted"  # Requires high confidence + validation
    ENABLED = "enabled"  # Normal operation
    TRUSTED = "trusted"  # Full autonomy, minimal gating


@dataclass
class DomainMetrics:
    """Performance metrics for a domain"""
    domain: str
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    total_value_generated: float = 0.0  # Profit, engagement, etc.
    total_risk_taken: float = 0.0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_actions == 0:
            return 0.0
        return self.successful_actions / self.total_actions
    
    @property
    def avg_value_per_action(self) -> float:
        """Average value generated per action"""
        if self.successful_actions == 0:
            return 0.0
        return self.total_value_generated / self.successful_actions
    
    @property
    def risk_adjusted_return(self) -> float:
        """Value generated relative to risk taken"""
        if self.total_risk_taken == 0:
            return self.total_value_generated
        return self.total_value_generated / self.total_risk_taken


@dataclass
class DomainAutonomyProfile:
    """Autonomy profile for a domain"""
    domain: str
    tier: DomainTier
    enabled: bool
    trust_level: str  # low, medium, high
    risk_level: str  # low, medium, high
    
    # Unlock criteria
    min_success_rate: float = 0.85
    min_total_actions: int = 20
    min_consecutive_successes: int = 5
    max_days_since_failure: int = 7
    
    # Current metrics
    metrics: DomainMetrics = field(default_factory=lambda: DomainMetrics(domain=""))
    
    def evaluate_unlock_eligibility(self) -> Dict[str, Any]:
        """
        Evaluate if domain should be unlocked for autonomy.
        
        Returns:
            {
                'eligible': bool,
                'reasons': List[str],
                'confidence': float
            }
        """
        reasons = []
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Success rate
        if self.metrics.success_rate >= self.min_success_rate:
            reasons.append(f"✅ Success rate: {self.metrics.success_rate:.1%} (>= {self.min_success_rate:.1%})")
            checks_passed += 1
        else:
            reasons.append(f"❌ Success rate: {self.metrics.success_rate:.1%} (need {self.min_success_rate:.1%})")
        
        # Check 2: Total actions
        if self.metrics.total_actions >= self.min_total_actions:
            reasons.append(f"✅ Total actions: {self.metrics.total_actions} (>= {self.min_total_actions})")
            checks_passed += 1
        else:
            reasons.append(f"❌ Total actions: {self.metrics.total_actions} (need {self.min_total_actions})")
        
        # Check 3: Consecutive successes
        if self.metrics.consecutive_successes >= self.min_consecutive_successes:
            reasons.append(f"✅ Consecutive successes: {self.metrics.consecutive_successes} (>= {self.min_consecutive_successes})")
            checks_passed += 1
        else:
            reasons.append(f"❌ Consecutive successes: {self.metrics.consecutive_successes} (need {self.min_consecutive_successes})")
        
        # Check 4: Recent failures
        if self.metrics.last_failure:
            days_since_failure = (datetime.now() - self.metrics.last_failure).days
            if days_since_failure >= self.max_days_since_failure:
                reasons.append(f"✅ Days since failure: {days_since_failure} (>= {self.max_days_since_failure})")
                checks_passed += 1
            else:
                reasons.append(f"❌ Days since failure: {days_since_failure} (need {self.max_days_since_failure})")
        else:
            # No failures yet - good sign
            reasons.append("✅ No failures recorded")
            checks_passed += 1
        
        eligible = checks_passed == total_checks
        confidence = checks_passed / total_checks
        
        return {
            'eligible': eligible,
            'reasons': reasons,
            'confidence': confidence,
            'checks_passed': checks_passed,
            'total_checks': total_checks
        }


class DomainAutonomyManager:
    """
    Manages graduated autonomy for high-risk domains.
    
    Automatically unlocks domains like 'market' and 'self_improvement' once
    AlleyBot has proven consistent performance.
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.profiles: Dict[str, DomainAutonomyProfile] = {}
        self._initialize_profiles()
        logger.info("🎯 Domain Autonomy Manager initialized")
    
    def _initialize_profiles(self):
        """Initialize domain profiles from AGI Kernel"""
        if not self.agi or not hasattr(self.agi, 'domain_autonomy_profiles'):
            return
        
        for domain, config in self.agi.domain_autonomy_profiles.items():
            # Determine tier based on current state
            if not config['enabled']:
                tier = DomainTier.LOCKED
            elif config['trust_tier'] == 'high':
                tier = DomainTier.TRUSTED
            elif config['trust_tier'] == 'medium':
                tier = DomainTier.ENABLED
            else:
                tier = DomainTier.RESTRICTED
            
            # Set unlock criteria based on risk level
            if config['risk_level'] == 'high':
                min_success_rate = 0.90  # Very high bar for high-risk
                min_total_actions = 30
                min_consecutive_successes = 10
            elif config['risk_level'] == 'medium':
                min_success_rate = 0.85
                min_total_actions = 20
                min_consecutive_successes = 5
            else:
                min_success_rate = 0.75
                min_total_actions = 10
                min_consecutive_successes = 3
            
            profile = DomainAutonomyProfile(
                domain=domain,
                tier=tier,
                enabled=config['enabled'],
                trust_level=config['trust_tier'],
                risk_level=config['risk_level'],
                min_success_rate=min_success_rate,
                min_total_actions=min_total_actions,
                min_consecutive_successes=min_consecutive_successes,
                metrics=DomainMetrics(domain=domain)
            )
            
            self.profiles[domain] = profile
    
    def record_action_outcome(
        self, 
        domain: str, 
        success: bool, 
        value_generated: float = 0.0,
        risk_taken: float = 0.0
    ):
        """
        Record the outcome of an action in a domain.
        
        Args:
            domain: Domain name
            success: Whether action succeeded
            value_generated: Value created (profit, engagement, etc.)
            risk_taken: Risk level of the action
        """
        if domain not in self.profiles:
            logger.warning(f"Unknown domain: {domain}")
            return
        
        profile = self.profiles[domain]
        metrics = profile.metrics
        
        # Update metrics
        metrics.total_actions += 1
        
        if success:
            metrics.successful_actions += 1
            metrics.total_value_generated += value_generated
            metrics.last_success = datetime.now()
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0
        else:
            metrics.failed_actions += 1
            metrics.last_failure = datetime.now()
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
        
        metrics.total_risk_taken += risk_taken
        
        # Check if domain should be unlocked
        if not profile.enabled and profile.tier == DomainTier.LOCKED:
            self._evaluate_and_unlock(domain)
    
    def _evaluate_and_unlock(self, domain: str):
        """Evaluate if domain should be unlocked"""
        profile = self.profiles[domain]
        evaluation = profile.evaluate_unlock_eligibility()
        
        if evaluation['eligible']:
            # Unlock domain!
            logger.info(f"🎯 Domain '{domain}' eligible for unlock!")
            logger.info(f"   Confidence: {evaluation['confidence']:.1%}")
            for reason in evaluation['reasons']:
                logger.info(f"   {reason}")
            
            # Update profile
            profile.enabled = True
            profile.tier = DomainTier.ENABLED
            
            # Update AGI Kernel
            if self.agi and hasattr(self.agi, 'domain_autonomy_profiles'):
                self.agi.domain_autonomy_profiles[domain]['enabled'] = True
            
            logger.info(f"✅ Domain '{domain}' UNLOCKED for autonomous operation!")
            
            # Notify owner via telegram
            self._notify_domain_unlocked(domain, evaluation)
    
    def _notify_domain_unlocked(self, domain: str, evaluation: Dict[str, Any]):
        """Notify owner that a domain has been unlocked"""
        try:
            if not self.agi or not self.agi.core:
                return
            
            telegram = self.agi.core.plugin_manager.plugins.get('telegram')
            if not telegram:
                return
            
            profile = self.profiles[domain]
            
            message = f"""🎯 **Domain Unlocked: {domain.upper()}**

AlleyBot has proven consistent performance and is now authorized for autonomous operation in the {domain} domain.

**Performance Metrics:**
• Success Rate: {profile.metrics.success_rate:.1%}
• Total Actions: {profile.metrics.total_actions}
• Consecutive Successes: {profile.metrics.consecutive_successes}
• Value Generated: {profile.metrics.total_value_generated:.2f}

**Unlock Criteria:**
{chr(10).join(evaluation['reasons'])}

Confidence: {evaluation['confidence']:.1%}

AlleyBot will now operate autonomously in this domain with SyMod validation."""
            
            # Send notification
            telegram.send_owner_message(message)
            
        except Exception as e:
            logger.debug(f"Failed to send unlock notification: {e}")
    
    def get_domain_status(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get current status of a domain"""
        if domain not in self.profiles:
            return None
        
        profile = self.profiles[domain]
        evaluation = profile.evaluate_unlock_eligibility()
        
        return {
            'domain': domain,
            'tier': profile.tier.value,
            'enabled': profile.enabled,
            'trust_level': profile.trust_level,
            'risk_level': profile.risk_level,
            'metrics': {
                'success_rate': profile.metrics.success_rate,
                'total_actions': profile.metrics.total_actions,
                'successful_actions': profile.metrics.successful_actions,
                'failed_actions': profile.metrics.failed_actions,
                'consecutive_successes': profile.metrics.consecutive_successes,
                'value_generated': profile.metrics.total_value_generated,
                'risk_adjusted_return': profile.metrics.risk_adjusted_return
            },
            'unlock_evaluation': evaluation
        }
    
    def get_all_domains_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all domains"""
        return {
            domain: self.get_domain_status(domain)
            for domain in self.profiles.keys()
        }
    
    def manually_unlock_domain(self, domain: str, reason: str = "Manual override"):
        """Manually unlock a domain (owner override)"""
        if domain not in self.profiles:
            logger.warning(f"Unknown domain: {domain}")
            return False
        
        profile = self.profiles[domain]
        profile.enabled = True
        profile.tier = DomainTier.ENABLED
        
        # Update AGI Kernel
        if self.agi and hasattr(self.agi, 'domain_autonomy_profiles'):
            self.agi.domain_autonomy_profiles[domain]['enabled'] = True
        
        logger.info(f"🔓 Domain '{domain}' manually unlocked: {reason}")
        return True
    
    def manually_lock_domain(self, domain: str, reason: str = "Manual override"):
        """Manually lock a domain (owner override)"""
        if domain not in self.profiles:
            logger.warning(f"Unknown domain: {domain}")
            return False
        
        profile = self.profiles[domain]
        profile.enabled = False
        profile.tier = DomainTier.LOCKED
        
        # Update AGI Kernel
        if self.agi and hasattr(self.agi, 'domain_autonomy_profiles'):
            self.agi.domain_autonomy_profiles[domain]['enabled'] = False
        
        logger.info(f"🔒 Domain '{domain}' manually locked: {reason}")
        return True


# Singleton instance
_domain_autonomy_manager: Optional[DomainAutonomyManager] = None


def get_domain_autonomy_manager(agi_kernel) -> DomainAutonomyManager:
    """Get or create domain autonomy manager"""
    global _domain_autonomy_manager
    if _domain_autonomy_manager is None:
        _domain_autonomy_manager = DomainAutonomyManager(agi_kernel)
    return _domain_autonomy_manager


def create_domain_autonomy_manager(agi_kernel) -> DomainAutonomyManager:
    """Create domain autonomy manager"""
    return DomainAutonomyManager(agi_kernel)
