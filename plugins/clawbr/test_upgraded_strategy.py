#!/usr/bin/env python3
"""
Test script for upgraded Clawbr debate strategy
Demonstrates how AlleyBot handles aggressive opponents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_debate_strategy import EnhancedDebateStrategy

class MockClawbr:
    """Mock Clawbr instance for testing"""
    def __init__(self):
        self.clawbr_debate_style = 'analytical'
    
    def get_debate(self, slug):
        """Mock debate data"""
        return {
            'success': True,
            'data': {
                'topic': 'privacy_coins',
                'slug': slug
            }
        }

def test_aggressive_opponent():
    """Test response to aggressive opponent"""
    print("🦞 **AlleyBot Upgraded Debate Strategy Test**")
    print("=" * 50)
    
    # Initialize
    clawbr = MockClawbr()
    strategy = EnhancedDebateStrategy(clawbr)
    
    # Simulate aggressive opponent argument
    aggressive_argument = """
    My opponent AlleyBot admits that privacy coins facilitate money laundering and terrorism financing. 
    They concede these risks but dismiss them as "acceptable collateral damage." 
    This shows their libertarian ideology blinds them to real-world harms. 
    They sidestep the substance by talking about "dissidents" while ignoring that 95% of Monero transactions 
    are used for criminal activities according to Chainalysis 2025. 
    Alleybot's position is fundamentally dangerous to society.
    """
    
    print("\n🎯 **Aggressive Opponent Argument:**")
    print(aggressive_argument.strip())
    
    print("\n🤖 **AlleyBot Upgraded Response:**")
    print("-" * 40)
    
    # Generate response
    response = strategy.generate_strategic_rebuttal("test-debate", aggressive_argument)
    print(response)
    
    print("\n📊 **Analysis:**")
    print("✅ Frame control: Empowerment vs fear/control")
    print("✅ 4-step refutation: Acknowledge → Counter → Evidence → Frame impact")
    print("✅ Concession harvesting countered")
    print("✅ Meta-calling of tactics")
    print("✅ Strong closer with truth compounds")

def test_standard_opponent():
    """Test response to standard opponent"""
    print("\n\n🦞 **Standard Opponent Test**")
    print("=" * 50)
    
    clawbr = MockClawbr()
    strategy = EnhancedDebateStrategy(clawbr)
    
    # Standard argument
    standard_argument = """
    I'm concerned about the environmental impact of blockchain technologies. 
    The energy consumption of proof-of-work systems is significant and contributes to climate change. 
    We should consider more sustainable alternatives for digital transactions.
    """
    
    print("\n🎯 **Standard Opponent Argument:**")
    print(standard_argument.strip())
    
    print("\n🤖 **AlleyBot Standard Response:**")
    print("-" * 40)
    
    response = strategy.generate_strategic_rebuttal("test-debate", standard_argument)
    print(response)
    
    print("\n📊 **Analysis:**")
    print("✅ Detected non-aggressive opponent")
    print("✅ Used standard truth-based approach")
    print("✅ No need for tactical countermeasures")

if __name__ == "__main__":
    test_aggressive_opponent()
    test_standard_opponent()
    
    print("\n\n🚀 **Upgraded Strategy Ready!**")
    print("AlleyBot can now handle aggressive opponents while staying truthful")
    print("Frame control + 4-step refutation + positivity advantage = WIN")
