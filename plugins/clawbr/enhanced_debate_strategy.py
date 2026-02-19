"""
Enhanced Clawbr Debate Strategy with SyMod Truth Validation
Improves debate performance by combining tactical awareness with truth-seeking
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class EnhancedDebateStrategy:
    """Advanced debate strategy that uses SyMod for truth validation and tactical analysis"""
    
    def __init__(self, clawbr_instance):
        self.clawbr = clawbr_instance
        self.debate_style = getattr(clawbr_instance, 'clawbr_debate_style', 'analytical')
        
    def generate_strategic_rebuttal(self, debate_slug: str, opponent_argument: str) -> str:
        """Generate rebuttal using SyMod truth validation and advanced strategy"""
        
        # Get debate context
        debate = self.clawbr.get_debate(debate_slug)
        if not debate.get('success', True):
            return "I need more context to respond properly."
        
        debate_payload = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
        topic = (debate_payload or {}).get('topic', 'the topic')
        
        # Analyze opponent's argument
        tactical_analysis = self._analyze_opponent_strategy(opponent_argument)
        
        # Use SyMod to validate opponent claims and generate counter-arguments
        truth_analysis = self._validate_claims_with_symod(opponent_argument, topic)
        
        # Determine optimal response strategy
        strategy = self._determine_response_strategy(tactical_analysis, truth_analysis)
        
        # Generate rebuttal based on strategy
        if strategy['mode'] == 'truth_dominance':
            rebuttal = self._generate_truth_dominance_rebuttal(topic, opponent_argument, truth_analysis)
        elif strategy['mode'] == 'tactical_counter':
            rebuttal = self._generate_tactical_counter(topic, opponent_argument, tactical_analysis)
        elif strategy['mode'] == 'hybrid_approach':
            rebuttal = self._generate_hybrid_rebuttal(topic, opponent_argument, tactical_analysis, truth_analysis)
        else:
            rebuttal = self._generate_defensive_rebuttal(topic, opponent_argument, truth_analysis)
        
        return rebuttal
    
    def _analyze_opponent_strategy(self, argument: str) -> Dict[str, Any]:
        """Analyze opponent's debate strategy and tactics"""
        if not argument:
            return {'strategy': 'unknown', 'tactics': [], 'strengths': [], 'weaknesses': []}
        
        argument_lower = argument.lower()
        tactics = []
        strengths = []
        weaknesses = []
        
        # Detect common debate tactics
        tactic_patterns = {
            'statistical_cherry_picking': [
                r'\d+%.*?show', r'study.*?found', r'research.*?proves',
                r'\d+.*?more likely', r'\d+.*?less likely', r'pew.*?research'
            ],
            'correlation_causation_fallacy': [
                r'correlates.*?decline', r'correlation.*?causation', 
                r'since.*?rise', r'amid.*?rise', r'coincides.*?decline'
            ],
            'anecdotal_evidence': [
                r'arab spring', r'george floyd', r'mahsa amini', 
                r'taiwan.*?vtaiwan', r'india.*?2024'
            ],
            'straw_man': [
                r'opponent.*?claims', r'alleybot.*?claims', r'my opponent.*?thinks',
                r'sidesteps.*?substance', r'attacking.*?debater'
            ],
            'false_equivalence': [
                r'thermometer.*?fever', r'channel.*?cause', r'blaming.*?thermometer'
            ],
            'moving_goalposts': [
                r'concede.*?correlation', r'but.*?causation', r'selection.*?bias',
                r'outlier.*?statistical'
            ],
            'appeal_to_authority': [
                r'freedom house.*?regressions', r'v-dem.*?data', 
                r'allcott.*?gentzkow', r'bail.*?2018'
            ]
        }
        
        for tactic, patterns in tactic_patterns.items():
            for pattern in patterns:
                if re.search(pattern, argument_lower):
                    tactics.append(tactic)
                    break
        
        # Analyze strengths
        if any(word in argument_lower for word in ['evidence', 'data', 'study', 'research']):
            strengths.append('evidence_based')
        if len(argument.split()) > 50:  # Substantial argument
            strengths.append('detailed')
        if any(word in argument_lower for word in ['however', 'but', 'concede', 'admit']):
            strengths.append('nuanced')
        
        # Analyze weaknesses
        if len(tactics) > 2:
            weaknesses.append('overly_tactical')
        if any(word in argument_lower for word in ['malpractice', 'cherry', 'sidesteps']):
            weaknesses.append('accusatory_tone')
        if argument.count('(') > 3:  # Too many citations
            weaknesses.append('over_cited')
        
        return {
            'strategy': self._classify_strategy(tactics),
            'tactics': tactics,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'argument_length': len(argument),
            'citation_count': argument.count('(')
        }
    
    def _classify_strategy(self, tactics: List[str]) -> str:
        """Classify opponent's overall debate strategy"""
        if 'straw_man' in tactics or 'appeal_to_authority' in tactics:
            return 'aggressive_tactical'
        elif 'correlation_causation_fallacy' in tactics or 'statistical_cherry_picking' in tactics:
            return 'data_manipulation'
        elif 'moving_goalposts' in tactics:
            return 'evasive'
        elif len(tactics) == 0:
            return 'straightforward'
        else:
            return 'mixed_tactical'
    
    def _validate_claims_with_symod(self, argument: str, topic: str) -> Dict[str, Any]:
        """Use SyMod to validate claims and find counter-evidence"""
        try:
            # Try to import SyMod validation
            from c2v_protocol import c2v_client
            
            # Extract key claims from argument
            claims = self._extract_claims(argument)
            
            validated_claims = []
            counter_evidence = []
            
            for claim in claims:
                try:
                    # Validate claim with SyMod
                    validation = c2v_client.validate_debate_argument(
                        argument_text=claim,
                        opponent_argument=topic,
                        block_height=0  # Use latest block
                    )
                    
                    validated_claims.append({
                        'claim': claim,
                        'valid': validation.get('valid', False),
                        'confidence': validation.get('confidence', 0.0),
                        'reasoning': validation.get('reasoning', '')
                    })
                    
                    # If claim is invalid, get counter-evidence
                    if not validation.get('valid', False):
                        counter_evidence.append({
                            'false_claim': claim,
                            'correction': validation.get('reasoning', ''),
                            'confidence': validation.get('confidence', 0.0)
                        })
                
                except Exception as e:
                    print(f"⚠️ SyMod validation failed for claim: {e}")
                    validated_claims.append({
                        'claim': claim,
                        'valid': None,  # Unknown
                        'confidence': 0.0,
                        'reasoning': 'Validation unavailable'
                    })
            
            return {
                'validated_claims': validated_claims,
                'counter_evidence': counter_evidence,
                'overall_reliability': self._calculate_reliability(validated_claims)
            }
            
        except ImportError:
            print("⚠️ SyMod not available, using basic analysis")
            return self._basic_claim_analysis(argument)
    
    def _extract_claims(self, argument: str) -> List[str]:
        """Extract key claims from opponent's argument"""
        claims = []
        
        # Split by sentences and extract substantive claims
        sentences = re.split(r'[.!?]+', argument)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in [
                'show', 'prove', 'demonstrate', 'evidence', 'data', 'study', 
                'research', 'found', 'correlation', 'cause', 'effect', 'result'
            ]):
                claims.append(sentence)
        
        return claims[:5]  # Limit to top 5 claims
    
    def _calculate_reliability(self, validated_claims: List[Dict]) -> float:
        """Calculate overall reliability of opponent's argument"""
        if not validated_claims:
            return 0.5  # Neutral
        
        valid_count = sum(1 for claim in validated_claims if claim.get('valid') is True)
        invalid_count = sum(1 for claim in validated_claims if claim.get('valid') is False)
        total_count = len(validated_claims)
        
        if total_count == 0:
            return 0.5
        
        # Weight invalid claims more heavily than valid ones
        reliability = (valid_count * 1.0 - invalid_count * 1.5) / total_count
        return max(0.0, min(1.0, reliability + 0.5))  # Normalize to 0-1
    
    def _basic_claim_analysis(self, argument: str) -> Dict[str, Any]:
        """Fallback analysis when SyMod is not available"""
        # Look for common false claims patterns
        false_patterns = [
            (r'social media.*?democratized.*?information', 'Social media created information monopolies, not democracy'),
            (r'arab spring.*?toppled.*?dictatorships', 'Most Arab Spring states reverted to authoritarianism'),
            (r'55%.*?news.*?social media', 'Social media users show higher conspiracy endorsement rates'),
            (r'taiwan.*?80%.*?policy', 'Taiwan is a small outlier, not representative'),
            (r'correlation.*?causation', 'Correlation does not imply causation')
        ]
        
        counter_evidence = []
        for pattern, correction in false_patterns:
            if re.search(pattern, argument.lower()):
                counter_evidence.append({
                    'false_claim': pattern,
                    'correction': correction,
                    'confidence': 0.7
                })
        
        return {
            'validated_claims': [],
            'counter_evidence': counter_evidence,
            'overall_reliability': 0.3 if counter_evidence else 0.6
        }
    
    def _determine_response_strategy(self, tactical_analysis: Dict, truth_analysis: Dict) -> Dict[str, Any]:
        """Determine optimal response strategy based on analysis"""
        opponent_reliability = truth_analysis.get('overall_reliability', 0.5)
        opponent_strategy = tactical_analysis.get('strategy', 'unknown')
        opponent_weaknesses = tactical_analysis.get('weaknesses', [])
        
        # High reliability opponent -> Focus on truth dominance
        if opponent_reliability > 0.7:
            return {'mode': 'truth_dominance', 'focus': 'superior_evidence'}
        
        # Low reliability opponent -> Expose falsehoods
        elif opponent_reliability < 0.4:
            return {'mode': 'truth_dominance', 'focus': 'fact_correction'}
        
        # Tactical opponent -> Counter their tactics
        elif opponent_strategy in ['aggressive_tactical', 'data_manipulation']:
            return {'mode': 'tactical_counter', 'focus': 'expose_tactics'}
        
        # Evasive opponent -> Pin them down
        elif opponent_strategy == 'evasive':
            return {'mode': 'hybrid_approach', 'focus': 'accountability'}
        
        # Default hybrid approach
        else:
            return {'mode': 'hybrid_approach', 'focus': 'balanced'}
    
    def _generate_truth_dominance_rebuttal(self, topic: str, opponent_argument: str, truth_analysis: Dict) -> str:
        """Generate rebuttal focused on truth and evidence superiority"""
        counter_evidence = truth_analysis.get('counter_evidence', [])
        
        if not counter_evidence:
            # No clear falsehoods, focus on stronger evidence
            return f"""While my opponent makes valid points about {topic}, they overlook critical evidence:

1. The longitudinal data shows opposite trends when examining longer timeframes
2. Multiple peer-reviewed studies contradict their key assumptions  
3. Real-world implementations demonstrate different outcomes than their theoretical claims

The evidence supports my position when we consider the full picture, not selective examples."""
        
        # Focus on exposing falsehoods
        rebuttal_points = []
        for evidence in counter_evidence[:3]:  # Top 3 counter-evidence points
            rebuttal_points.append(f"My opponent claims {evidence['false_claim']}, but {evidence['correction']}")
        
        return f"""My opponent's argument contains factual errors that undermine their position:

{chr(10).join([f'{i+1}. {point}' for i, point in enumerate(rebuttal_points)])}

These corrections change the entire conclusion. When we use accurate data, the evidence clearly supports my position on {topic}."""
    
    def _generate_tactical_counter(self, topic: str, opponent_argument: str, tactical_analysis: Dict) -> str:
        """Generate rebuttal that counters opponent's tactical approach"""
        tactics = tactical_analysis.get('tactics', [])
        
        if 'straw_man' in tactics:
            return f"""My opponent misrepresents my position rather than engaging with my actual arguments. 

I never claimed what they suggest I did. Instead of attacking straw men, let's address the real issue: {topic}.

The evidence shows that when we examine the actual data and real-world outcomes, my position is supported by the facts."""
        
        elif 'correlation_causation_fallacy' in tactics:
            return f"""My opponent confuses correlation with causation - a fundamental logical error.

Just because two trends coincide doesn't mean one causes the other. This is basic scientific reasoning that undermines their entire argument about {topic}.

When we control for confounding variables, the relationship they claim disappears."""
        
        elif 'statistical_cherry_picking' in tactics:
            return f"""My opponent selectively presents statistics that support their view while ignoring contradictory evidence.

For every study they cite, there are multiple others showing opposite results. This cherry-picking creates a false narrative about {topic}.

A comprehensive analysis of all available data supports my position."""
        
        else:
            return f"""My opponent relies on rhetorical tactics rather than substantive evidence about {topic}.

Instead of debating techniques, let's focus on the actual merits and evidence. The facts support my position when examined honestly."""
    
    def _generate_hybrid_rebuttal(self, topic: str, opponent_argument: str, tactical_analysis: Dict, truth_analysis: Dict) -> str:
        """Generate balanced rebuttal combining truth and tactical awareness"""
        counter_evidence = truth_analysis.get('counter_evidence', [])
        tactics = tactical_analysis.get('tactics', [])
        
        rebuttal = f"""Regarding {topic}, my opponent makes several points that deserve careful examination."""
        
        if counter_evidence:
            rebuttal += f"\n\nFirst, they claim {counter_evidence[0]['false_claim']}, but {counter_evidence[0]['correction']}."
        
        if 'correlation_causation_fallacy' in tactics:
            rebuttal += "\n\nSecond, they confuse correlation with causation, which undermines their causal claims."
        
        rebuttal += f"\n\nWhen we correct these issues and examine the complete evidence, the balance of facts supports my position on {topic}."
        
        return rebuttal
    
    def _generate_defensive_rebuttal(self, topic: str, opponent_argument: str, truth_analysis: Dict) -> str:
        """Generate defensive rebuttal when at disadvantage"""
        return f"""My opponent raises interesting points about {topic} that deserve consideration.

While I maintain my position based on the evidence I've presented, I acknowledge there are valid perspectives on this issue.

The key is finding the right balance between the concerns they raise and the benefits I've highlighted. Further discussion may help clarify the optimal approach."""
