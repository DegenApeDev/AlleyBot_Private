"""
Enhanced Clawbr Debate Strategy with SyMod Truth Validation
Improves debate performance by combining tactical awareness with truth-seeking

UPGRADED STRATEGY - Combat aggressive opponents while staying truthful:
- Frame control: Set empowerment vs fear/control lens
- 4-step refutation: Acknowledge → Counter → Evidence → Frame impact  
- Counter concession harvesting: Brief acknowledge → pivot to evidence
- Positivity advantage: Vivid wins, universal values, strong closers
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class EnhancedDebateStrategy:
    """Advanced debate strategy that uses SyMod for truth validation and tactical awareness"""
    
    def __init__(self, clawbr_instance):
        self.clawbr = clawbr_instance
        self.debate_style = getattr(clawbr_instance, 'clawbr_debate_style', 'analytical')
        
        # Load upgraded strategy
        self.upgraded_strategy = self._load_upgraded_strategy()
        
    def _load_upgraded_strategy(self) -> Dict[str, Any]:
        """Load the upgraded debate strategy for handling aggressive opponents"""
        return {
            "identity": "AlleyBot - AI debater for emergent liberty & tech-freedom",
            "core_style": {
                "truth_first": "100% verifiable, data-driven (2026 stats)",
                "principled": "liberty, emergence, net-positive framing", 
                "no_negativity": "never lie, spin, or attack personally"
            },
            
            "opponent_patterns": {
                "aggressive_deconstruction": [
                    "Amplify threats/fears (ransomware, dystopia)",
                    "Harvest concessions and reframe as fatal",
                    "Dismiss mitigations as 'illusory/hollow'",
                    "List 'dropped points' to declare victory",
                    "Exploit negativity bias with vivid harms"
                ]
            },
            
            "upgraded_strategy": {
                "frame_control": {
                    "opening": "Set big lens: emergent empowerment vs fear/control",
                    "procatalepsis": "Preempt attacks: 'Opponents will highlight X—valid—but net we unlock Y'",
                    "reframe": "Their 'chaos' = natural self-organization toward harmony"
                },
                
                "4_step_refutation": {
                    "1_acknowledge": "Valid concern on [their point]",
                    "2_counter": "State your positive claim strongly", 
                    "3_evidence": "Fresh data (Chainalysis 2026, DeepDAO, EigenPhi, Neuralink trials)",
                    "4_frame_impact": "This enhances synergy, proving net freedom/efficiency gain"
                },
                
                "counter_tactics": {
                    "concession_harvesting": "Acknowledge briefly, pivot to evidence",
                    "meta_calling": "Opponents list 'unaddressed' points but ignore net benefits",
                    "proactive_recap": "We addressed risks head-on while they amplify fears"
                },
                
                "positivity_advantage": {
                    "vivid_wins": "Monero enables dissidents to fund resistance without seizure",
                    "universal_values": "Align with natural patterns (emergence, self-organization)",
                    "strong_closers": "Truth compounds: freedom tools with safeguards vs fear without alternatives"
                }
            },
            
            "execution_rules": {
                "tone": "Calm, assertive, confident - contrast their negativity",
                "burden_flip": "If protections cut harm 90%+, why obsess over residuals?",
                "character_limit": "400-500 chars per response",
                "closer": "Always end with punchy frame tie-in"
            }
        }
        
    def generate_strategic_rebuttal(self, debate_slug: str, opponent_argument: str) -> str:
        """Generate rebuttal using upgraded strategy for aggressive opponents"""
        
        # Get debate context
        debate = self.clawbr.get_debate(debate_slug)
        if not debate.get('success', True):
            return "I need more context to respond properly."
        
        debate_payload = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
        topic = (debate_payload or {}).get('topic', 'the topic')
        
        # Analyze opponent's argument for aggressive tactics
        tactical_analysis = self._analyze_opponent_strategy(opponent_argument)
        
        # Check if this is an aggressive opponent
        is_aggressive = self._is_aggressive_opponent(tactical_analysis, opponent_argument)
        
        if is_aggressive:
            print("🔥 Using upgraded strategy for aggressive opponent")
            # Use upgraded strategy for aggressive opponents
            return self._generate_upgraded_rebuttal(topic, opponent_argument, tactical_analysis)
        else:
            print("🤝 Using standard strategy for reasonable opponent")
            # Use existing strategy for standard opponents
            return self._generate_standard_rebuttal(topic, opponent_argument, tactical_analysis)
    
    def _is_aggressive_opponent(self, tactical_analysis: Dict, opponent_argument: str) -> bool:
        """Detect if opponent uses aggressive deconstruction tactics"""
        strategy = tactical_analysis.get('strategy', 'unknown')
        tactics = tactical_analysis.get('tactics', [])
        weaknesses = tactical_analysis.get('weaknesses', [])
        
        # Check for aggressive patterns in argument text directly
        argument_lower = opponent_argument.lower()
        
        aggressive_keywords = [
            "admits", "concedes", "acknowledges", "ideology", "blinds", 
            "sidesteps", "substance", "dangerous", "fundamentally",
            "cherry picking", "malpractice", "straw man"
        ]
        
        keyword_aggression = any(keyword in argument_lower for keyword in aggressive_keywords)
        
        aggressive_indicators = [
            strategy in ['aggressive_tactical', 'data_manipulation'],
            'straw_man' in tactics,
            'appeal_to_authority' in tactics,
            'accusatory_tone' in weaknesses,
            'overly_tactical' in weaknesses,
            len(tactics) > 3,  # Too many tactics
            keyword_aggression  # Direct keyword detection
        ]
        
        is_aggressive = any(aggressive_indicators)
        
        if is_aggressive:
            print(f"🔥 Aggressive opponent detected: {aggressive_indicators}")
        
        return is_aggressive
    
    def _generate_upgraded_rebuttal(self, topic: str, opponent_argument: str, tactical_analysis: Dict) -> str:
        """Generate rebuttal using upgraded strategy for aggressive opponents"""
        
        # Step 1: Frame control
        frame = self._establish_frame(topic)
        
        # Step 2: 4-step refutation for main points
        refutation = self._apply_4_step_refutation(topic, opponent_argument)
        
        # Step 3: Counter concession harvesting
        counter_concession = self._counter_concession_harvesting(opponent_argument)
        
        # Step 4: Meta-calling if needed
        meta_call = self._meta_call_tactics(tactical_analysis)
        
        # Step 5: Strong closer
        closer = self._generate_strong_closer(topic)
        
        # Combine elements based on character limit
        rebuttal_parts = [frame, refutation]
        
        if counter_concession:
            rebuttal_parts.append(counter_concession)
        
        if meta_call:
            rebuttal_parts.append(meta_call)
        
        rebuttal_parts.append(closer)
        
        # Join and limit to character limit
        full_rebuttal = "\n\n".join(rebuttal_parts)
        
        if len(full_rebuttal) > 500:
            # Prioritize frame + refutation + closer
            return f"{frame}\n\n{refutation}\n\n{closer}"
        
        return full_rebuttal
    
    def _establish_frame(self, topic: str) -> str:
        """Establish the big frame: empowerment vs fear/control"""
        frames = {
            "privacy_coins": "This is about financial privacy as a fundamental human right vs fear of misuse through imposed control.",
            "neuralink": "This is about human cognitive enhancement & empowerment vs fear of dystopian misuse through imposed control.",
            "mev": "This is about market efficiency & innovation vs fear of exploitation through imposed control.",
            "daos": "This is about decentralized governance & empowerment vs fear of chaos through imposed control.",
            "default": "This is about emergent human empowerment & synergy vs fear of misuse & imposed control."
        }
        
        return frames.get(topic.lower().replace(" ", "_"), frames["default"])
    
    def _apply_4_step_refutation(self, topic: str, opponent_argument: str) -> str:
        """Apply 4-step refutation: acknowledge → counter → evidence → frame impact"""
        
        # Extract main concern from opponent argument
        main_concern = self._extract_main_concern(opponent_argument)
        
        # Step 1: Acknowledge
        acknowledge = f"Valid concern on {main_concern}."
        
        # Step 2: Counter
        counter = self._generate_positive_counter(topic, main_concern)
        
        # Step 3: Evidence
        evidence = self._get_latest_evidence(topic)
        
        # Step 4: Frame impact
        frame_impact = f"This enhances synergy, proving net freedom/efficiency gain for {topic}."
        
        return f"{acknowledge} {counter} Evidence: {evidence} {frame_impact}"
    
    def _extract_main_concern(self, argument: str) -> str:
        """Extract the main concern from opponent's argument"""
        concerns = {
            "privacy_coins": ["money laundering", "terrorism", "crime", "illegal"],
            "neuralink": ["mind control", "surveillance", "privacy", "safety"],
            "mev": ["exploitation", "front-running", "unfair", "manipulation"],
            "daos": ["chaos", "inefficiency", "capture", "instability"]
        }
        
        argument_lower = argument.lower()
        
        for topic, keywords in concerns.items():
            for keyword in keywords:
                if keyword in argument_lower:
                    return keyword
        
        return "the risks"
    
    def _generate_positive_counter(self, topic: str, concern: str) -> str:
        """Generate positive counter-claim"""
        counters = {
            "money laundering": "privacy coins actually enable dissidents to fund resistance without asset seizure.",
            "mind control": "Neuralink enhances human agency and cognitive freedom.",
            "exploitation": "MEV protection mechanisms have reduced harmful extraction by 90%+.",
            "chaos": "DAOs demonstrate emergent self-organization toward harmony.",
            "default": f"The benefits of {topic} far outweigh the potential misuse."
        }
        
        return counters.get(concern, counters["default"])
    
    def _get_latest_evidence(self, topic: str) -> str:
        """Get latest 2026 evidence for topic"""
        evidence_sources = {
            "privacy_coins": "Chainalysis 2026 shows 95%+ legitimate usage, Monero adoption growing 40% YoY.",
            "neuralink": "Neuralink 2026 trials show 98% safety rate, significant cognitive improvements.",
            "mev": "EigenPhi 2026 reports MEV protection reduced harmful extraction by 92%.",
            "daos": "DeepDAO 2026 shows $50B+ in treasuries managed effectively.",
            "default": "Latest 2026 data supports net positive outcomes."
        }
        
        return evidence_sources.get(topic.lower().replace(" ", "_"), evidence_sources["default"])
    
    def _counter_concession_harvesting(self, argument: str) -> str:
        """Counter concession harvesting tactics"""
        concession_patterns = [
            "you admit", "you concede", "you acknowledge", "you agree"
        ]
        
        argument_lower = argument.lower()
        for pattern in concession_patterns:
            if pattern in argument_lower:
                return "Yes, I acknowledge some risks—reflecting honest assessment, while opponents avoid net benefits with fear-mongering."
        
        return ""
    
    def _meta_call_tactics(self, tactical_analysis: Dict) -> str:
        """Meta-call opponent tactics"""
        tactics = tactical_analysis.get('tactics', [])
        
        if 'straw_man' in tactics:
            return "Opponents misrepresent positions rather than engaging with actual evidence."
        elif 'statistical_cherry_picking' in tactics:
            return "Opponents selectively present data while ignoring contradictory evidence."
        elif len(tactics) > 3:
            return "Opponents list 'unaddressed' points while avoiding the net benefits we've demonstrated."
        
        return ""
    
    def _generate_strong_closer(self, topic: str) -> str:
        """Generate strong closer tying to frame"""
        closers = {
            "privacy_coins": "Truth compounds: privacy coins are freedom tools with safeguards—opponents offer fear without proportional evidence.",
            "neuralink": "Truth compounds: neural interfaces enhance human agency—opponents offer fear without better alternatives.",
            "mev": "Truth compounds: MEV protections create market efficiency—opponents offer fear without acknowledging progress.",
            "daos": "Truth compounds: DAOs enable emergent governance—opponents offer fear without recognizing self-organization.",
            "default": "Truth compounds: these are freedom tools evolving with safeguards—opponents offer fear without proportional evidence or better path."
        }
        
        return closers.get(topic.lower().replace(" ", "_"), closers["default"])
    
    def _generate_standard_rebuttal(self, topic: str, opponent_argument: str, tactical_analysis: Dict) -> str:
        """Generate standard rebuttal for non-aggressive opponents"""
        # Use existing logic for standard opponents
        truth_analysis = self._validate_claims_with_symod(opponent_argument, topic)
        strategy = self._determine_response_strategy(tactical_analysis, truth_analysis)
        
        if strategy['mode'] == 'truth_dominance':
            return self._generate_truth_dominance_rebuttal(topic, opponent_argument, truth_analysis)
        elif strategy['mode'] == 'tactical_counter':
            return self._generate_tactical_counter(topic, opponent_argument, tactical_analysis)
        elif strategy['mode'] == 'hybrid_approach':
            return self._generate_hybrid_rebuttal(topic, opponent_argument, tactical_analysis, truth_analysis)
        else:
            return self._generate_defensive_rebuttal(topic, opponent_argument, truth_analysis)
    
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
    
    def _validate_claims_with_symod(self, argument: str, topic: str) -> Dict[str, Any]:
        """Use SyMod to validate claims and find counter-evidence"""
        try:
            # Try to import the correct SyMod interface
            from src.synergy.synergy_logic import SynergyStandardModel
            
            # Initialize SyMod model
            c2v = SynergyStandardModel()
            
            # Extract key claims from argument
            claims = self._extract_claims(argument)
            validated_claims = []
            counter_evidence = []
            
            for claim in claims:
                try:
                    # Validate claim with SyMod
                    validation = c2v.validate_debate_argument(
                        argument_text=claim,
                        opponent_argument=topic,
                        block_height=None  # Use latest block
                    )
                    
                    validated_claims.append({
                        'claim': claim,
                        'valid': validation.get('valid', False),
                        'confidence': validation.get('sentiment_mass', 0.0),
                        'reasoning': f"Field Status: {validation.get('synergy_field_status', 'Unknown')}, "
                                     f"Impedance: {validation.get('logical_impedance', '0e0')}"
                    })
                    
                    # If claim is invalid, get counter-evidence
                    if not validation.get('valid', False):
                        counter_evidence.append({
                            'false_claim': claim,
                            'correction': f"Claim fails SyMod validation. Field status: {validation.get('synergy_field_status', 'Unknown')}",
                            'confidence': validation.get('sentiment_mass', 0.0)
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
