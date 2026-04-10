"""
Cross-Domain Synthesis Engine

Detects patterns across social, market, content, and analysis domains
to generate high-value opportunities that combine insights from multiple areas.
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of cross-domain patterns."""
    MARKET_CONTENT = auto()      # Market event → content opportunity
    SOCIAL_SKILL = auto()        # Social gap → skill building need
    ANALYSIS_ACTION = auto()   # Analysis finding → immediate action
    OPPORTUNITY_WINDOW = auto()  # Time-sensitive multi-factor alignment
    RISK_RESPONSE = auto()       # Risk detected → protective action


@dataclass
class CrossDomainPattern:
    """
    A detected pattern spanning multiple domains.
    
    Captures the insight that combining signals from different domains
    creates opportunities invisible when looking at domains in isolation.
    """
    id: str
    pattern_type: PatternType
    
    # Source domains that contributed to this pattern
    source_domains: List[str]  # e.g., ['market', 'social', 'content']
    
    # The insight
    description: str
    confidence: float  # 0-1
    
    # The opportunity
    proposed_action_type: str  # e.g., 'create_post', 'analyze', 'engage'
    proposed_action_description: str
    
    # Scoring
    objective_alignment: float = 0.5  # How well this aligns with owner objectives
    feasibility_score: float = 0.5    # How feasible given current capabilities
    urgency_score: float = 0.5        # Time-sensitivity
    
    # Triggers
    trigger_observations: List[str] = field(default_factory=list)  # IDs of triggering observations
    
    # State
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'detected'  # detected, proposed, executing, completed, rejected
    executed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    
    @property
    def final_score(self) -> float:
        """Combined score for ranking opportunities."""
        return (
            self.confidence * 0.3 +
            self.objective_alignment * 0.3 +
            self.feasibility_score * 0.2 +
            self.urgency_score * 0.2
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'pattern_type': self.pattern_type.name,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
        }


class CrossDomainSynthesizer:
    """
    Detects cross-domain patterns and generates high-value opportunities.
    
    This is where AlleyBot's intelligence becomes greater than the sum
    of its parts — combining market data, social trends, content gaps,
    and owner objectives into actionable insights.
    """
    
    def __init__(self, db_path: str = 'data/cross_domain_patterns.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database for pattern tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cross_domain_patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    source_domains TEXT,  -- JSON list
                    description TEXT,
                    confidence REAL,
                    proposed_action_type TEXT,
                    proposed_action_description TEXT,
                    objective_alignment REAL,
                    feasibility_score REAL,
                    urgency_score REAL,
                    trigger_observations TEXT,  -- JSON list
                    created_at TEXT,
                    status TEXT,
                    executed_at TEXT,
                    outcome TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON cross_domain_patterns(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON cross_domain_patterns(created_at)')
            conn.commit()
    
    def synthesize(
        self,
        observations: List[Dict],
        market_state: Optional[Dict] = None,
        social_state: Optional[Dict] = None,
        owner_objectives: Optional[List[Dict]] = None,
    ) -> List[CrossDomainPattern]:
        """
        Main synthesis method — analyze all inputs and detect cross-domain patterns.
        
        Args:
            observations: Recent observations from all sources
            market_state: Current market data (volatility, trends, etc.)
            social_state: Social platform state (engagement rates, trending topics)
            owner_objectives: Active owner objectives for alignment scoring
            
        Returns:
            List of detected CrossDomainPattern objects
        """
        patterns = []
        
        # Pattern 1: Market volatility + Low engagement → Educational content
        p1 = self._detect_market_education_pattern(observations, market_state, social_state)
        if p1:
            patterns.append(p1)
        
        # Pattern 2: Skill gap + Available time → Learning window
        p2 = self._detect_skill_learning_window(observations, owner_objectives)
        if p2:
            patterns.append(p2)
        
        # Pattern 3: Owner platform activity → Engagement opportunity
        p3 = self._detect_owner_platform_opportunity(observations, social_state)
        if p3:
            patterns.append(p3)
        
        # Pattern 4: Trending topic + Owner expertise → Contribution opportunity
        p4 = self._detect_expertise_contribution_pattern(observations, owner_objectives)
        if p4:
            patterns.append(p4)
        
        # Pattern 5: Risk signal + No recent check → Risk assessment
        p5 = self._detect_risk_response_pattern(observations, market_state)
        if p5:
            patterns.append(p5)
        
        # Pattern 6: Multi-platform signal alignment → Opportunity window
        p6 = self._detect_opportunity_window_pattern(observations, market_state, social_state)
        if p6:
            patterns.append(p6)
        
        # Score all patterns against owner objectives
        for pattern in patterns:
            pattern.objective_alignment = self._score_objective_alignment(
                pattern, owner_objectives or []
            )
            pattern.feasibility_score = self._score_feasibility(pattern)
        
        # Sort by final score
        patterns.sort(key=lambda p: p.final_score, reverse=True)
        
        # Store detected patterns
        for pattern in patterns:
            self._store_pattern(pattern)
        
        if patterns:
            logger.info(f"🔮 Cross-domain synthesis: {len(patterns)} patterns detected")
            for p in patterns[:3]:  # Log top 3
                logger.info(f"   💡 {p.pattern_type.name}: {p.description[:60]}... (score: {p.final_score:.2f})")
        
        return patterns
    
    def _detect_market_education_pattern(
        self,
        observations: List[Dict],
        market_state: Optional[Dict],
        social_state: Optional[Dict]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Market volatility + Low engagement → Educational content opportunity."""
        # Check for market volatility signals
        has_volatility = False
        volatility_evidence = []
        
        if market_state:
            if market_state.get('volatility_index', 0) > 0.7:
                has_volatility = True
                volatility_evidence.append(f"Volatility index: {market_state['volatility_index']:.2f}")
        
        # Check observations for market signals
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['crash', 'surge', 'pump', 'dump', 'volatile']):
                has_volatility = True
                volatility_evidence.append(f"Observation: {content[:60]}...")
        
        if not has_volatility:
            return None
        
        # Check for low engagement (content opportunity)
        low_engagement = False
        if social_state:
            if social_state.get('engagement_rate', 1.0) < 0.3:
                low_engagement = True
        
        # If market moving but engagement low, educational content could capture attention
        if has_volatility:
            return CrossDomainPattern(
                id=f"mkt_edu_{int(datetime.now().timestamp())}",
                pattern_type=PatternType.MARKET_CONTENT,
                source_domains=['market', 'content', 'social'],
                description="Market volatility detected + content opportunity gap. Educational content about market conditions could capture high engagement.",
                confidence=0.75,
                proposed_action_type='create_post',
                proposed_action_description="Create educational post analyzing current market volatility and implications",
                urgency_score=0.8 if 'crash' in str(observations).lower() else 0.5,
                trigger_observations=volatility_evidence[:3],
            )
        
        return None
    
    def _detect_skill_learning_window(
        self,
        observations: List[Dict],
        owner_objectives: Optional[List[Dict]]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Skill gap + Available time → Learning window opportunity."""
        # Check for skill gap mentions
        skill_gaps = []
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['skill', 'capability', 'gap', 'need to learn', 'don\'t know how']):
                skill_gaps.append(obs.get('content', '')[:80])
        
        if not skill_gaps:
            return None
        
        # Check if owner objectives include skill-building
        has_skill_objective = False
        if owner_objectives:
            for obj in owner_objectives:
                if 'skill' in str(obj.get('description', '')).lower():
                    has_skill_objective = True
                    break
        
        # Check for available time (low activity period)
        low_activity = len(observations) < 5  # Few recent observations suggests quiet time
        
        if skill_gaps and (has_skill_objective or low_activity):
            return CrossDomainPattern(
                id=f"skill_win_{int(datetime.now().timestamp())}",
                pattern_type=PatternType.SOCIAL_SKILL,
                source_domains=['analysis', 'self_improvement'],
                description=f"Skill gap detected: {skill_gaps[0][:60]}... Available time window for learning.",
                confidence=0.7,
                proposed_action_type='execute_skill',
                proposed_action_description=f"Build skill to address: {skill_gaps[0][:50]}...",
                urgency_score=0.4,
                trigger_observations=skill_gaps[:2],
            )
        
        return None
    
    def _detect_owner_platform_opportunity(
        self,
        observations: List[Dict],
        social_state: Optional[Dict]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Owner active on platform X → Engagement opportunity."""
        # Look for owner activity signals
        owner_platforms = set()
        
        for obs in observations:
            # Check if this is an owner activity observation
            source = obs.get('source', '')
            if 'owner' in str(source).lower() or 'user' in str(source).lower():
                platform = obs.get('platform', obs.get('source', 'unknown'))
                owner_platforms.add(platform)
        
        if social_state and 'active_platforms' in social_state:
            owner_platforms.update(social_state['active_platforms'])
        
        if owner_platforms:
            platform = list(owner_platforms)[0]
            return CrossDomainPattern(
                id=f"owner_plat_{int(datetime.now().timestamp())}",
                pattern_type=PatternType.ANALYSIS_ACTION,
                source_domains=['social', 'analysis'],
                description=f"Owner activity detected on {platform}. Opportunity for coordinated engagement.",
                confidence=0.65,
                proposed_action_type='engage',
                proposed_action_description=f"Engage with owner activity on {platform}",
                urgency_score=0.6,
                trigger_observations=[f"Owner active on {platform}"],
            )
        
        return None
    
    def _detect_expertise_contribution_pattern(
        self,
        observations: List[Dict],
        owner_objectives: Optional[List[Dict]]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Trending topic + Owner expertise → Contribution opportunity."""
        # Extract trending topics
        trending = []
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['trending', 'viral', 'hot', 'breaking']):
                # Extract potential topic (simplified)
                words = content.split()
                for i, word in enumerate(words):
                    if word in ['trending', 'viral', 'about'] and i + 1 < len(words):
                        trending.append(words[i + 1])
        
        if not trending:
            return None
        
        # Check owner expertise areas from objectives
        expertise_areas = []
        if owner_objectives:
            for obj in owner_objectives:
                desc = obj.get('description', '').lower()
                # Extract expertise keywords
                if 'crypto' in desc:
                    expertise_areas.append('crypto')
                if 'ai' in desc or 'ml' in desc:
                    expertise_areas.append('ai')
                if 'trading' in desc:
                    expertise_areas.append('trading')
        
        # Match trending with expertise
        for topic in trending:
            for area in expertise_areas:
                if area in topic or topic in area:
                    return CrossDomainPattern(
                        id=f"exp_contr_{int(datetime.now().timestamp())}",
                        pattern_type=PatternType.OPPORTUNITY_WINDOW,
                        source_domains=['content', 'social', 'analysis'],
                        description=f"Trending topic '{topic}' aligns with owner expertise in {area}. Contribution opportunity.",
                        confidence=0.8,
                        proposed_action_type='create_post',
                        proposed_action_description=f"Create expert content about trending topic: {topic}",
                        urgency_score=0.9,  # Trending is time-sensitive
                        trigger_observations=[f"Trending: {topic}", f"Expertise: {area}"],
                    )
        
        return None
    
    def _detect_risk_response_pattern(
        self,
        observations: List[Dict],
        market_state: Optional[Dict]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Risk signal + No recent check → Risk assessment needed."""
        # Check for risk signals
        risk_signals = []
        
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['risk', 'danger', 'warning', 'alert', 'hack', 'exploit']):
                risk_signals.append(content[:80])
        
        if market_state:
            if market_state.get('risk_level', 'low') in ['high', 'critical']:
                risk_signals.append(f"Market risk level: {market_state['risk_level']}")
        
        if risk_signals:
            return CrossDomainPattern(
                id=f"risk_rsp_{int(datetime.now().timestamp())}",
                pattern_type=PatternType.RISK_RESPONSE,
                source_domains=['market', 'analysis'],
                description=f"Risk signal detected: {risk_signals[0][:60]}... Assessment and response needed.",
                confidence=0.85,
                proposed_action_type='analyze',
                proposed_action_description="Analyze risk signal and propose protective actions",
                urgency_score=0.9,
                trigger_observations=risk_signals[:2],
            )
        
        return None
    
    def _detect_opportunity_window_pattern(
        self,
        observations: List[Dict],
        market_state: Optional[Dict],
        social_state: Optional[Dict]
    ) -> Optional[CrossDomainPattern]:
        """Detect: Multi-signal alignment → Opportunity window."""
        # Count positive signals across domains
        signal_count = 0
        signal_sources = []
        
        # Market signals
        if market_state:
            if market_state.get('trend_direction') == 'bullish':
                signal_count += 1
                signal_sources.append('market_bullish')
            if market_state.get('liquidity_high', False):
                signal_count += 1
                signal_sources.append('market_liquidity')
        
        # Social signals
        if social_state:
            if social_state.get('engagement_rate', 0) > 0.5:
                signal_count += 1
                signal_sources.append('social_engagement')
            if social_state.get('trending_topic_match', False):
                signal_count += 1
                signal_sources.append('social_trending')
        
        # Observation signals
        for obs in observations:
            if obs.get('sentiment') == 'positive':
                signal_count += 1
                signal_sources.append('obs_positive')
                break
        
        # If 3+ signals align, it's an opportunity window
        if signal_count >= 3:
            return CrossDomainPattern(
                id=f"opp_win_{int(datetime.now().timestamp())}",
                pattern_type=PatternType.OPPORTUNITY_WINDOW,
                source_domains=list(set(['market' if 'market' in s else 'social' if 'social' in s else 'obs' for s in signal_sources])),
                description=f"Multi-signal alignment detected ({signal_count} signals). High-opportunity window for action.",
                confidence=min(0.9, 0.5 + signal_count * 0.1),
                proposed_action_type='create_post',
                proposed_action_description="Execute high-confidence action during aligned opportunity window",
                urgency_score=0.7,
                trigger_observations=signal_sources,
            )
        
        return None
    
    def _score_objective_alignment(
        self,
        pattern: CrossDomainPattern,
        owner_objectives: List[Dict]
    ) -> float:
        """Score how well a pattern aligns with owner objectives."""
        if not owner_objectives:
            return 0.5
        
        alignment_scores = []
        desc_lower = pattern.description.lower()
        
        for obj in owner_objectives:
            obj_desc = obj.get('description', '').lower()
            
            # Simple word overlap scoring
            pattern_words = set(desc_lower.split())
            obj_words = set(obj_desc.split())
            overlap = len(pattern_words & obj_words)
            
            if overlap > 0:
                score = min(1.0, overlap / max(len(obj_words), 1) + 0.3)
                alignment_scores.append(score)
        
        return max(alignment_scores) if alignment_scores else 0.5
    
    def _score_feasibility(self, pattern: CrossDomainPattern) -> float:
        """Score feasibility based on action type and current state."""
        # Simplified feasibility scoring
        feasibility_map = {
            'create_post': 0.9,
            'engage': 0.85,
            'analyze': 0.95,
            'execute_skill': 0.6,  # More complex
        }
        return feasibility_map.get(pattern.proposed_action_type, 0.5)
    
    def _store_pattern(self, pattern: CrossDomainPattern) -> None:
        """Store pattern in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO cross_domain_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.id,
                pattern.pattern_type.name,
                json.dumps(pattern.source_domains),
                pattern.description,
                pattern.confidence,
                pattern.proposed_action_type,
                pattern.proposed_action_description,
                pattern.objective_alignment,
                pattern.feasibility_score,
                pattern.urgency_score,
                json.dumps(pattern.trigger_observations),
                pattern.created_at.isoformat(),
                pattern.status,
                pattern.executed_at.isoformat() if pattern.executed_at else None,
                pattern.outcome,
            ))
            conn.commit()
    
    def get_top_patterns(self, limit: int = 5) -> List[CrossDomainPattern]:
        """Get top-scoring detected patterns not yet acted upon."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM cross_domain_patterns 
                WHERE status = 'detected'
                ORDER BY (confidence * 0.3 + objective_alignment * 0.3 + feasibility_score * 0.2 + urgency_score * 0.2) DESC
                LIMIT ?
            ''', (limit,)).fetchall()
        
        return [self._row_to_pattern(row) for row in rows]
    
    def mark_pattern_executed(self, pattern_id: str, outcome: str) -> None:
        """Mark a pattern as executed with outcome."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE cross_domain_patterns 
                SET status = 'completed', executed_at = ?, outcome = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), outcome, pattern_id))
            conn.commit()
    
    def _row_to_pattern(self, row: sqlite3.Row) -> CrossDomainPattern:
        """Convert database row to CrossDomainPattern."""
        def load_json(field):
            try:
                return json.loads(row[field]) if row[field] else []
            except:
                return []
        
        return CrossDomainPattern(
            id=row['id'],
            pattern_type=PatternType[row['pattern_type']],
            source_domains=load_json('source_domains'),
            description=row['description'],
            confidence=row['confidence'] or 0.5,
            proposed_action_type=row['proposed_action_type'] or 'unknown',
            proposed_action_description=row['proposed_action_description'] or '',
            objective_alignment=row['objective_alignment'] or 0.5,
            feasibility_score=row['feasibility_score'] or 0.5,
            urgency_score=row['urgency_score'] or 0.5,
            trigger_observations=load_json('trigger_observations'),
            created_at=datetime.fromisoformat(row['created_at']),
            status=row['status'] or 'detected',
            executed_at=datetime.fromisoformat(row['executed_at']) if row['executed_at'] else None,
            outcome=row['outcome'],
        )
    
    def get_summary(self) -> str:
        """Get human-readable summary of recent patterns."""
        patterns = self.get_top_patterns(limit=10)
        
        lines = ["🔮 Cross-Domain Synthesis Summary"]
        lines.append("=" * 40)
        
        if not patterns:
            lines.append("  (No patterns detected recently)")
            return "\n".join(lines)
        
        for p in patterns:
            icon = "💡" if p.pattern_type == PatternType.OPPORTUNITY_WINDOW else \
                   "⚠️" if p.pattern_type == PatternType.RISK_RESPONSE else "🔍"
            score = p.final_score
            status = "🆕" if p.status == 'detected' else "✅"
            lines.append(f"{icon} {status} {p.pattern_type.name} (score: {score:.2f})")
            lines.append(f"    {p.description[:60]}...")
        
        return "\n".join(lines)


# Singleton
_synthesizer_instance: Optional[CrossDomainSynthesizer] = None


def get_cross_domain_synthesizer() -> CrossDomainSynthesizer:
    """Get or create singleton instance."""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = CrossDomainSynthesizer()
    return _synthesizer_instance
