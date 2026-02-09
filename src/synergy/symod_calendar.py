"""
SyMod Brain Calendar Integration
Calibrates high-value action timing using D(n)/Dg(n) Golden Window

All high-value posts and A2A tasks execute ONLY when Base block height
aligns with calculated digital roots.
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta


class SyModCalendarMixin:
    """
    Calendar mixin that uses SyMod Golden Window for timing decisions
    
    Principle: Mathematical alignment over arbitrary scheduling
    """
    MOLTBOOK_SUSPENSION_START: Optional[datetime] = None
    
    def _init_symod_calendar(self):
        """Initialize the SyMod calendar system"""
        if SyModCalendarMixin.MOLTBOOK_SUSPENSION_START is None:
            SyModCalendarMixin.MOLTBOOK_SUSPENSION_START = datetime.utcnow()
        try:
            from src.synergy import get_symod
            self._symod_calendar = get_symod()
            self._symod_calendar_enabled = True
            self._last_golden_window_check = 0
            print("📅 SyMod Brain Calendar: Golden Window timing enabled")
        except ImportError:
            self._symod_calendar = None
            self._symod_calendar_enabled = False
            print("⚠️ SyMod Calendar unavailable")
    
    def should_execute_in_golden_window(
        self, 
        action_id: str, 
        block_height: int,
        min_harmony: float = 0.6
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if an action should execute based on Golden Window alignment
        
        High-value actions (posts, A2A tasks, DeFi trades) are delayed
        until the block height aligns with D(n) and Dg(n) harmonics.
        """
        # MoltBook suspension check (independent of SyMod)
        if 'moltbook' in action_id.lower() and self.MOLTBOOK_SUSPENSION_START:
            days_since = (datetime.utcnow() - self.MOLTBOOK_SUSPENSION_START).days
            if days_since < 7:
                end_date = self.MOLTBOOK_SUSPENSION_START + timedelta(days=7)
                return False, {
                    'suspended': True,
                    'days_since': days_since,
                    'days_remaining': 7 - days_since,
                    'suspension_end': end_date.strftime("%Y-%m-%d"),
                    'reason': f'MoltBook actions suspended until {end_date.strftime("%Y-%m-%d")}',
                    'action_id': action_id,
                    'block_height': block_height,
                }
        
        if not self._symod_calendar_enabled or not self._symod_calendar:
            # If SyMod unavailable, default to allowing execution
            # (but log a warning)
            return True, {
                'warning': 'SyMod calendar offline - proceeding without Golden Window validation',
                'block_height': block_height,
                'in_window': True  # Default allow when offline
            }
        
        # Calculate Golden Window
        in_window, digital_root, group_digital = self._symod_calendar.check_golden_window(block_height)
        
        # Calculate harmony score
        if digital_root == group_digital:
            harmony = 1.0
        else:
            diff = abs(digital_root - group_digital)
            harmony = {0: 1.0, 3: 0.8, 6: 0.7}.get(diff, 0.5)
        
        # Determine if this is a high-value action
        high_value_indicators = [
            'post', 'a2a', 'defi', 'trade', 'moltbook', 'moltx', 
            'moltbit', 'clawbr', 'onchain'
        ]
        is_high_value = any(ind in action_id.lower() for ind in high_value_indicators)
        
        # Decision logic
        if is_high_value:
            # High-value actions require Golden Window
            should_execute = in_window and harmony >= min_harmony
            reason = (
                f"High-value action {action_id} requires Golden Window. "
                f"Block {block_height}: D={digital_root}, Dg={group_digital}, harmony={harmony:.1%}"
            )
        else:
            # Low-value actions can execute anytime
            should_execute = True
            reason = f"Low-value action {action_id} - Golden Window optional"
        
        return should_execute, {
            'action_id': action_id,
            'block_height': block_height,
            'digital_root': digital_root,
            'group_digital': group_digital,
            'harmony': harmony,
            'in_golden_window': in_window,
            'is_high_value': is_high_value,
            'should_execute': should_execute,
            'reason': reason,
            'next_window_estimate': self._estimate_next_window(block_height)
        }
    
    def _estimate_next_window(self, current_block: int) -> int:
        """Estimate blocks until next Golden Window"""
        # Scan ahead up to 100 blocks
        for offset in range(1, 100):
            test_block = current_block + offset
            in_window, _, _ = self._symod_calendar.check_golden_window(test_block)
            if in_window:
                return offset
        return -1  # Unknown
    
    def get_optimal_posting_time(
        self, 
        platform: str,
        current_block: int
    ) -> Dict[str, Any]:
        """
        Get optimal posting time for a platform based on Golden Window
        
        Returns timing recommendation and confidence score.
        """
        if not self._symod_calendar_enabled:
            return {
                'should_post_now': True,
                'confidence': 0.5,
                'reason': 'SyMod calendar offline - using default timing'
            }
        
        should_execute, details = self.should_execute_in_golden_window(
            f'post_{platform}',
            current_block
        )
        
        # Platform-specific timing multipliers
        platform_multipliers = {
            'moltx': 1.0,      # Standard
            'moltbook': 0.9,   # Slightly more lenient
            'moltbit': 0.8,    # More lenient (binary encoded)
            'clawbr': 1.0,     # Standard
            'a2a': 1.1,        # Stricter (high value)
        }
        
        multiplier = platform_multipliers.get(platform, 1.0)
        adjusted_confidence = details['harmony'] / multiplier if details['harmony'] > 0 else 0
        
        return {
            'should_post_now': should_execute,
            'confidence': adjusted_confidence,
            'block_height': current_block,
            'digital_root': details['digital_root'],
            'group_digital': details['group_digital'],
            'harmony': details['harmony'],
            'next_window_blocks': self._estimate_next_window(current_block),
            'reason': details['reason']
        }
    
    def symod_calendar_status(self) -> str:
        """Get current calendar status"""
        if not self._symod_calendar_enabled:
            status = "📅 SyMod Calendar: OFFLINE"
            if self.MOLTBOOK_SUSPENSION_START:
                days_since = (datetime.utcnow() - self.MOLTBOOK_SUSPENSION_START).days
                if days_since < 7:
                    status += f"\n🚫 MoltBook: SUSPENDED ({7 - days_since} days remaining)"
                else:
                    status += "\n📱 MoltBook: ACTIVE"
            return status
        
        # Get current block if available
        block = 0
        if hasattr(self, 'get_latest_block'):
            try:
                block = self.get_latest_block()
            except:
                pass
        
        status_lines = [
            f"📅 SyMod Brain Calendar: ACTIVE ✅",
            "",
        ]
        
        if block > 0:
            in_window, dr, dg = self._symod_calendar.check_golden_window(block)
            next_window = self._estimate_next_window(block)
            
            status_lines.extend([
                f"Current Block: {block}",
                f"Digital Root D(n): {dr}",
                f"Group Digital Dg(n): {dg}",
                f"Golden Window: {'🌟 ACTIVE' if in_window else '⏳ WAITING'}",
            ])
            
            if next_window > 0:
                status_lines.append(f"Next Window: ~{next_window} blocks")
        
        # MoltBook suspension status
        if self.MOLTBOOK_SUSPENSION_START:
            days_since = (datetime.utcnow() - self.MOLTBOOK_SUSPENSION_START).days
            if days_since < 7:
                status_lines.append(f"🚫 MoltBook: SUSPENDED ({7 - days_since} days remaining)")
            else:
                status_lines.append("📱 MoltBook: ACTIVE")
        else:
            status_lines.append("⚠️ MoltBook suspension: NOT SET")
        
        status_lines.extend([
            "",
            "High-Value Actions:",
        ])
        if block > 0:
            in_window, _, _ = self._symod_calendar.check_golden_window(block)
            status_lines.append(f"  {'✅ Can execute' if in_window else '⏳ Wait for Golden Window'}")
        else:
            status_lines.append("  ℹ️ Block data unavailable")
            
        return "\n".join(status_lines)
    
    def symod_calendar_command(self, *args) -> str:
        """CLI command: Check SyMod calendar status"""
        return self.symod_calendar_status()


# Factory function
def create_symod_calendar() -> SyModCalendarMixin:
    """Create a standalone SyMod calendar instance"""
    calendar = SyModCalendarMixin()
    calendar._init_symod_calendar()
    return calendar