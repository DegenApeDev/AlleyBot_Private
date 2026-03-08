"""
SyMod Truth Filter Mixin
Mandatory validation layer for AlleyBot Agentic System

Principle: Mathematical certainty over LLM probabilistic output
If the math fails, the thought is discarded.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import asdict


class SyModTruthFilterMixin:
    """
    Synergy Standard Model Truth Filter
    
    Validates all decisions through mathematical framework:
    1. DeFi trades: Me/Ma impedance check
    2. A2A timing: D(n)/Dg(n) Golden Window
    3. MCP data: Qa Arena Model validation
    4. All actions: Mathematical certainty gate
    """
    
    def _init_symod_filter(self):
        """Initialize the SyMod truth filter"""
        try:
            from src.synergy import get_symod, SyModValidationResult
            self._symod = get_symod()
            self._symod_enabled = True
            print("🔢 SyMod Truth Filter: ACTIVE - Mathematical validation enabled")
        except Exception as e:
            print(f"⚠️ SyMod Truth Filter failed to initialize: {e}")
            self._symod = None
            self._symod_enabled = False
    
    def validate_defi_trade_symod(
        self,
        amount: float,
        token_price: float,
        liquidity: float,
        slippage: float,
        context: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Mandatory DeFi trade validation using SyMod Me/Ma functions
        
        Returns: (is_valid, validation_details)
        If math indicates high impedance or insufficient mass, auto-rejects.
        """
        if not self._symod_enabled or not self._symod:
            # If SyMod unavailable, reject the trade (fail closed for safety)
            return False, {
                'error': 'SyMod validation unavailable - trade rejected for safety',
                'symod_required': True,
                'action': 'REJECT'
            }
        
        # Perform SyMod validation
        result = self._symod.validate_defi_trade(
            amount=amount,
            token_price=token_price,
            liquidity=liquidity,
            slippage=slippage
        )
        
        # Convert result to dict for logging
        details = asdict(result)
        
        # Auto-reject if not valid
        if not result.valid:
            print(f"🚫 SyMod REJECTED trade: {result.reason}")
            print(f"   Impedance: {result.impedance:.2e}, Mass: {result.mass:.2e}")
            return False, details
        
        # Check confidence threshold
        if result.confidence < 0.7:
            print(f"⚠️ SyMod LOW CONFIDENCE ({result.confidence:.1%}): {result.reason}")
            return False, details
        
        print(f"✅ SyMod APPROVED trade: {result.reason}")
        print(f"   Confidence: {result.confidence:.1%}, Golden Window: {result.golden_window}")
        return True, details
    
    def check_golden_window(
        self,
        block_height: int,
        min_confidence: float = 0.6
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if current Base block height aligns with Golden Window
        Uses D(n) and Dg(n) for calibration
        
        High-value A2A tasks and posts only execute in Golden Window
        """
        if not self._symod_enabled or not self._symod:
            return False, {
                'error': 'SyMod unavailable',
                'in_window': False
            }
        
        in_window, digital_root, group_digital = self._symod.check_golden_window(block_height)
        
        # Calculate harmonic confidence
        harmony = 1.0 if digital_root == group_digital else 0.5
        if abs(digital_root - group_digital) == 3:
            harmony = 0.8
        elif abs(digital_root - group_digital) == 6:
            harmony = 0.7
        
        result = {
            'in_window': in_window,
            'block_height': block_height,
            'digital_root': digital_root,
            'group_digital': group_digital,
            'harmony_score': harmony,
            'should_execute': in_window and harmony >= min_confidence
        }
        
        if result['should_execute']:
            print(f"🌟 GOLDEN WINDOW: Block {block_height} (D={digital_root}, Dg={group_digital})")
        else:
            print(f"⏳ Outside Golden Window: Block {block_height} (D={digital_root}, Dg={group_digital})")
        
        return result['should_execute'], result
    
    def validate_mcp_data_symod(
        self,
        data: Dict[str, Any],
        source: str = "mcp"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate MCP data using Qa Arena Model
        
        If physical world data doesn't fit Qp (Path Equation), 
        flag as anomaly and refuse to post about it.
        """
        if not self._symod_enabled or not self._symod:
            return False, {
                'error': 'SyMod validation unavailable',
                'valid': False
            }
        
        # Run Arena Model validation
        result = self._symod.validate_mcp_data(data)
        details = asdict(result)
        details['source'] = source
        
        if not result.valid:
            print(f"🚨 SyMod ANOMALY DETECTED from {source}: {result.reason}")
            print(f"   Confidence: {result.confidence:.1%}, Impedance: {result.impedance:.2e}")
            return False, details
        
        if result.confidence < 0.5:
            print(f"⚠️ SyMod SUSPICIOUS DATA from {source}: {result.reason}")
            return False, details
        
        print(f"✅ SyMod VALIDATED {source} data: {result.reason}")
        return True, details
    
    def validate_brain_action(
        self,
        action_id: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Mandatory validation for ALL brain actions
        
        This is the gatekeeper - all decisions pass through here.
        """
        if not self._symod_enabled:
            # Fail closed - reject if SyMod unavailable
            print(f"🚫 SyMod OFFLINE - Action {action_id} BLOCKED")
            return False, {'error': 'SyMod validation required but unavailable'}
        
        validation_results = {
            'action': action_id,
            'symod_enabled': True,
            'checks': {}
        }
        
        # Check 1: Golden Window alignment (for high-value actions)
        high_value_actions = ['moltbit_post', 'moltx_post', 'a2a_task']
        if action_id in high_value_actions or any(hv in action_id for hv in high_value_actions):
            # Get current block height from context or query
            block_height = context.get('block_height', 0)
            if block_height == 0 and hasattr(self, 'get_latest_block'):
                try:
                    block_height = self.get_latest_block()
                except:
                    pass
            
            if block_height > 0:
                in_window, window_details = self.check_golden_window(block_height)
                validation_results['checks']['golden_window'] = window_details
                
                if not in_window:
                    print(f"⏳ Action {action_id} delayed: Outside Golden Window")
                    return False, validation_results
        
        # Check 2: MCP data validation (if present)
        if 'mcp_data' in context:
            mcp_valid, mcp_details = self.validate_mcp_data_symod(
                context['mcp_data'],
                source=context.get('mcp_source', 'unknown')
            )
            validation_results['checks']['mcp'] = mcp_details
            
            if not mcp_valid:
                print(f"🚨 Action {action_id} BLOCKED: Invalid MCP data")
                return False, validation_results
        
        # Check 3: Impedance check for on-chain actions
        if action_id.startswith('onchain_') or 'defi' in action_id or 'trade' in action_id:
            trade_params = context.get('trade_params', {})
            if trade_params:
                trade_valid, trade_details = self.validate_defi_trade_symod(
                    amount=trade_params.get('amount', 0),
                    token_price=trade_params.get('token_price', 0),
                    liquidity=trade_params.get('liquidity', 0),
                    slippage=trade_params.get('slippage', 0.01)
                )
                validation_results['checks']['trade'] = trade_details
                
                if not trade_valid:
                    print(f"🚫 Action {action_id} REJECTED: Failed SyMod trade validation")
                    return False, validation_results
        
        # All checks passed
        validation_results['approved'] = True
        print(f"✅ Action {action_id} APPROVED by SyMod Truth Filter")
        return True, validation_results
    
    def get_symod_stats(self) -> Dict[str, Any]:
        """Get SyMod system statistics"""
        if not self._symod_enabled or not self._symod:
            return {'enabled': False, 'error': 'SyMod not initialized'}
        
        return {
            'enabled': True,
            'qa_arena': self._symod.Qa(),
            'feyn_constants': self._symod.Fhc(),
            'mass_natural_limit': self._symod.Mn(),
            'planck_radius_sample': self._symod.Fr(self._symod.Ma(1))
        }
    
    def symod_status_command(self) -> str:
        """CLI command to check SyMod status"""
        if not self._symod_enabled:
            return "🔢 SyMod Truth Filter: OFFLINE ❌"
        
        stats = self.get_symod_stats()
        qa = stats.get('qa_arena', {})
        
        output = [
            "🔢 SyMod Truth Filter: ACTIVE ✅",
            "",
            "Mathematical Framework:",
            f"  Arena ID: {qa.get('id', 'N/A'):.6e}",
            f"  Speed of Light (cy): {qa.get('cy', 0):.6e}",
            f"  Natural Mass Limit: {stats.get('mass_natural_limit', 0):.6e}",
            "",
            "Validation Functions:",
            "  • DeFi Trade (Me/Ma impedance) - ACTIVE",
            "  • Golden Window (D/Dg) - ACTIVE",
            "  • MCP Data (Qa Arena) - ACTIVE",
            "  • Brain Action Gate - ACTIVE",
            "",
            "⚠️  LLM outputs are secondary to mathematical certainty"
        ]
        
        return "\n".join(output)


# Helper function for direct use
def create_symod_filter() -> SyModTruthFilterMixin:
    """Factory function to create a standalone SyMod filter instance"""
    filter_instance = SyModTruthFilterMixin()
    filter_instance._init_symod_filter()
    return filter_instance
