"""
AlleyBot Theory of Mind & Social Intelligence - Phase 12

Understands and predicts other agents'/users' behavior.
Implements agent modeling, intent prediction, deception detection,
collaboration negotiation, and reputation modeling.

Part of AGI Core - Phase 12: Theory of Mind & Social Intelligence
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import logging
import statistics

from src.autonomy.world_state import WorldStateManager, get_world_state_manager

logger = logging.getLogger(__name__)


@dataclass
class AgentModel:
    """A model of another agent/user"""
    entity_id: str
    entity_type: str  # 'user', 'ai_agent', 'bot', 'organization'
    
    # Behavioral patterns
    communication_style: str  # 'formal', 'casual', 'technical', 'aggressive'
    response_patterns: Dict[str, float]  # How often they respond to different triggers
    active_hours: List[int]  # Hours of day they're typically active
    
    # Goals and motivations (inferred)
    inferred_goals: List[str]
    inferred_values: List[str]
    
    # Reputation tracking
    trust_score: float  # 0-1
    reliability_score: float  # 0-1
    interaction_count: int
    
    # Risk assessment
    deception_flags: List[str]  # Suspicious behaviors observed
    bot_probability: float  # 0-1
    
    # Metadata
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    model_version: int = 1


@dataclass
class IntentPrediction:
    """Predicted intent of an entity"""
    entity_id: str
    predicted_intent: str
    confidence: float
    supporting_evidence: List[str]
    predicted_next_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CollaborationProposal:
    """A proposal for joint action"""
    id: str
    target_entity: str
    proposed_action: str
    mutual_benefit: str
    terms: Dict[str, Any]
    status: str = 'pending'  # 'pending', 'accepted', 'rejected', 'completed'
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReputationAssessment:
    """Reputation assessment for an entity"""
    entity_id: str
    overall_score: float  # 0-1
    dimensions: Dict[str, float]  # Specific reputation dimensions
    assessment_basis: List[str]  # What evidence supports this
    last_updated: datetime = field(default_factory=datetime.now)


class SocialIntelligence:
    """
    Theory of Mind & Social Intelligence Engine
    
    Capabilities:
    1. Agent Modeling - Build profiles of other AI agents (style, goals, patterns)
    2. User Intent Prediction - Predict what users want before they ask
    3. Deception Detection - Spot fake engagement, bots, manipulation
    4. Collaboration Negotiation - Propose and negotiate joint actions
    5. Reputation Modeling - Track trustworthiness of other entities
    6. Social Dynamics Simulation - Predict how communities will react
    
    Usage:
        social = SocialIntelligence()
        
        # Model an agent
        model = social.model_agent(entity_id)
        
        # Predict intent
        intent = social.predict_intent(entity_id, context)
        
        # Check for deception
        deception = social.detect_deception(entity_id, interaction)
        
        # Propose collaboration
        proposal = social.propose_collaboration(entity_id, joint_goal)
        
        # Get reputation
        reputation = social.get_reputation(entity_id)
    """
    
    DB_PATH = Path('data/social_intelligence.db')
    
    # Thresholds
    MIN_INTERACTIONS_FOR_MODEL = 3
    DECEPTION_THRESHOLD = 0.7  # Bot probability above this triggers warning
    
    def __init__(self, world_state: Optional[WorldStateManager] = None):
        self.world_state = world_state or get_world_state_manager()
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize social intelligence database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_models (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT,
                    communication_style TEXT,
                    response_patterns TEXT,
                    active_hours TEXT,
                    inferred_goals TEXT,
                    inferred_values TEXT,
                    trust_score REAL,
                    reliability_score REAL,
                    interaction_count INTEGER,
                    deception_flags TEXT,
                    bot_probability REAL,
                    first_seen TEXT,
                    last_seen TEXT,
                    model_version INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS intent_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT,
                    predicted_intent TEXT,
                    confidence REAL,
                    supporting_evidence TEXT,
                    predicted_next_action TEXT,
                    timestamp TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collaboration_proposals (
                    id TEXT PRIMARY KEY,
                    target_entity TEXT,
                    proposed_action TEXT,
                    mutual_benefit TEXT,
                    terms TEXT,
                    status TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reputation_assessments (
                    entity_id TEXT PRIMARY KEY,
                    overall_score REAL,
                    dimensions TEXT,
                    assessment_basis TEXT,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT,
                    interaction_type TEXT,
                    content TEXT,
                    timestamp TEXT,
                    response_time_seconds REAL,
                    engagement_received REAL
                )
            ''')
            
            conn.commit()
    
    def model_agent(self, entity_id: str, force_refresh: bool = False) -> Optional[AgentModel]:
        """
        Build or update a model of an agent/user.
        
        Analyzes historical interactions to infer behavioral patterns,
        communication style, and potential goals.
        
        Args:
            entity_id: Entity to model
            force_refresh: Force model refresh even if recently updated
            
        Returns:
            AgentModel or None if insufficient data
        """
        # Check if we have enough interactions
        interactions = self._get_entity_interactions(entity_id)
        
        if len(interactions) < self.MIN_INTERACTIONS_FOR_MODEL:
            logger.info(f"Insufficient data to model {entity_id} ({len(interactions)} interactions)")
            return None
        
        # Check for existing model
        existing = self._load_model(entity_id)
        
        if existing and not force_refresh:
            # Refresh if older than 7 days
            if (datetime.now() - existing.last_seen).days < 7:
                return existing
        
        # Build model from interactions
        model = self._build_model_from_interactions(entity_id, interactions)
        
        # Save model
        self._save_model(model)
        
        logger.info(f"🎭 Updated model for {entity_id} (v{model.model_version})")
        
        return model
    
    def _get_entity_interactions(self, entity_id: str, limit: int = 100) -> List[Dict]:
        """Get historical interactions with an entity"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT * FROM interactions 
                   WHERE entity_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?''',
                (entity_id, limit)
            ).fetchall()
            
            return [
                {
                    'type': row['interaction_type'],
                    'content': row['content'],
                    'timestamp': datetime.fromisoformat(row['timestamp']),
                    'response_time': row['response_time_seconds'],
                    'engagement': row['engagement_received']
                }
                for row in rows
            ]
    
    def _build_model_from_interactions(self, entity_id: str, 
                                        interactions: List[Dict]) -> AgentModel:
        """Build agent model from interaction history"""
        
        # Determine communication style
        all_text = ' '.join([i['content'] for i in interactions if i['content']])
        style = self._analyze_communication_style(all_text)
        
        # Calculate active hours
        hours = [i['timestamp'].hour for i in interactions]
        active_hours = list(set(hours))
        
        # Calculate response patterns
        patterns = defaultdict(float)
        for i in interactions:
            if i['response_time'] is not None:
                if i['response_time'] < 60:
                    patterns['quick_responder'] += 1
                elif i['response_time'] < 300:
                    patterns['normal_responder'] += 1
                else:
                    patterns['slow_responder'] += 1
        
        # Normalize patterns
        total = sum(patterns.values())
        if total > 0:
            patterns = {k: v/total for k, v in patterns.items()}
        
        # Detect bot probability
        bot_prob = self._calculate_bot_probability(interactions)
        
        # Infer goals (simple keyword-based)
        goals = self._infer_goals(all_text)
        
        # Calculate trust and reliability
        trust = self._calculate_trust_score(interactions)
        reliability = self._calculate_reliability_score(interactions)
        
        # Check for deception flags
        deception_flags = self._detect_deception_flags(interactions)
        
        # Determine entity type
        entity_type = 'bot' if bot_prob > 0.8 else 'user' if bot_prob < 0.3 else 'unknown'
        
        # Model version
        version = 1
        if interactions:
            first = min(i['timestamp'] for i in interactions)
            last = max(i['timestamp'] for i in interactions)
        else:
            first = last = datetime.now()
        
        return AgentModel(
            entity_id=entity_id,
            entity_type=entity_type,
            communication_style=style,
            response_patterns=dict(patterns),
            active_hours=active_hours,
            inferred_goals=goals,
            inferred_values=[],  # Would need more sophisticated analysis
            trust_score=trust,
            reliability_score=reliability,
            interaction_count=len(interactions),
            deception_flags=deception_flags,
            bot_probability=bot_prob,
            first_seen=first,
            last_seen=last,
            model_version=version
        )
    
    def _analyze_communication_style(self, text: str) -> str:
        """Analyze communication style from text"""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Check for formal indicators
        formal_words = ['therefore', 'furthermore', 'regarding', 'pursuant']
        formal_count = sum(1 for w in formal_words if w in text_lower)
        
        # Check for technical indicators
        technical_indicators = len(re.findall(r'\b[A-Z]{2,}\b|\b\w+_\w+\b', text))
        
        # Check for aggressive indicators
        aggressive_words = ['wrong', 'terrible', 'stupid', 'hate', 'angry']
        aggressive_count = sum(1 for w in aggressive_words if w in text_lower)
        
        # Determine style
        if aggressive_count > 2:
            return 'aggressive'
        elif technical_indicators > 5:
            return 'technical'
        elif formal_count > 1:
            return 'formal'
        else:
            return 'casual'
    
    def _calculate_bot_probability(self, interactions: List[Dict]) -> float:
        """Calculate probability that entity is a bot"""
        if not interactions:
            return 0.5
        
        flags = 0
        
        # Check response time consistency (bots often respond very fast)
        response_times = [i['response_time'] for i in interactions if i['response_time']]
        if response_times:
            if all(rt < 5 for rt in response_times[:5]):  # Consistently under 5 seconds
                flags += 0.3
            
            # Very consistent timing is suspicious
            if len(response_times) > 3:
                try:
                    cv = statistics.stdev(response_times) / statistics.mean(response_times)
                    if cv < 0.1:  # Very consistent
                        flags += 0.2
                except:
                    pass
        
        # Check content patterns (repetition)
        contents = [i['content'] for i in interactions if i['content']]
        if len(contents) > 5:
            unique_ratio = len(set(contents)) / len(contents)
            if unique_ratio < 0.5:  # High repetition
                flags += 0.3
        
        # Check timing patterns (24/7 activity is suspicious)
        hours = [i['timestamp'].hour for i in interactions]
        if hours:
            unique_hours = len(set(hours))
            if unique_hours > 20:  # Active almost all hours
                flags += 0.2
        
        return min(1.0, flags)
    
    def _infer_goals(self, text: str) -> List[str]:
        """Infer goals from text content"""
        goals = []
        text_lower = text.lower()
        
        goal_keywords = {
            'promotion': ['check out', 'follow me', 'subscribe', 'promote'],
            'engagement': ['what do you think', 'reply', 'comment', 'share your'],
            'information': ['learn about', 'understand', 'explain', 'teach'],
            'networking': ['connect', 'collaborate', 'partner', 'work together'],
            'support': ['help', 'assist', 'support', 'guidance']
        }
        
        for goal, keywords in goal_keywords.items():
            if any(kw in text_lower for kw in keywords):
                goals.append(goal)
        
        return goals[:3]  # Top 3 inferred goals
    
    def _calculate_trust_score(self, interactions: List[Dict]) -> float:
        """Calculate trust score based on interaction patterns"""
        if not interactions:
            return 0.5
        
        # Factors:
        # - Consistency in engagement
        # - Follow-through on implied commitments
        # - Response reciprocity
        
        score = 0.5
        
        # More interactions = higher trust (up to a point)
        score += min(0.2, len(interactions) * 0.02)
        
        # Check for engagement reciprocity
        engaged = sum(1 for i in interactions if i.get('engagement', 0) > 0)
        if len(interactions) > 0:
            engagement_rate = engaged / len(interactions)
            score += engagement_rate * 0.2
        
        return min(1.0, max(0.0, score))
    
    def _calculate_reliability_score(self, interactions: List[Dict]) -> float:
        """Calculate reliability score"""
        if not interactions:
            return 0.5
        
        # Consistency in response time
        response_times = [i['response_time'] for i in interactions if i['response_time']]
        
        if len(response_times) > 3:
            try:
                cv = statistics.stdev(response_times) / statistics.mean(response_times)
                # Lower CV = more reliable
                reliability = max(0, 1 - cv)
                return min(1.0, 0.5 + reliability * 0.5)
            except:
                pass
        
        return 0.5
    
    def _detect_deception_flags(self, interactions: List[Dict]) -> List[str]:
        """Detect flags that might indicate deception"""
        flags = []
        
        # Check for rapid-fire interactions (bot-like)
        timestamps = [i['timestamp'] for i in interactions]
        if len(timestamps) > 1:
            timestamps.sort()
            intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                        for i in range(len(timestamps)-1)]
            
            very_fast = sum(1 for interval in intervals if interval < 1)
            if very_fast > len(intervals) * 0.5:
                flags.append('rapid_fire_interactions')
        
        # Check for copy-paste content
        contents = [i['content'] for i in interactions if i['content']]
        if len(contents) > 3:
            duplicates = len(contents) - len(set(contents))
            if duplicates > len(contents) * 0.3:
                flags.append('repetitive_content')
        
        return flags
    
    def _load_model(self, entity_id: str) -> Optional[AgentModel]:
        """Load existing model from database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM agent_models WHERE entity_id = ?',
                (entity_id,)
            ).fetchone()
            
            if row:
                return AgentModel(
                    entity_id=row['entity_id'],
                    entity_type=row['entity_type'],
                    communication_style=row['communication_style'],
                    response_patterns=json.loads(row['response_patterns']),
                    active_hours=json.loads(row['active_hours']),
                    inferred_goals=json.loads(row['inferred_goals']),
                    inferred_values=json.loads(row['inferred_values']),
                    trust_score=row['trust_score'],
                    reliability_score=row['reliability_score'],
                    interaction_count=row['interaction_count'],
                    deception_flags=json.loads(row['deception_flags']),
                    bot_probability=row['bot_probability'],
                    first_seen=datetime.fromisoformat(row['first_seen']),
                    last_seen=datetime.fromisoformat(row['last_seen']),
                    model_version=row['model_version']
                )
        
        return None
    
    def _save_model(self, model: AgentModel) -> None:
        """Save model to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO agent_models
                (entity_id, entity_type, communication_style, response_patterns, active_hours,
                 inferred_goals, inferred_values, trust_score, reliability_score,
                 interaction_count, deception_flags, bot_probability, first_seen, last_seen, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model.entity_id,
                model.entity_type,
                model.communication_style,
                json.dumps(model.response_patterns),
                json.dumps(model.active_hours),
                json.dumps(model.inferred_goals),
                json.dumps(model.inferred_values),
                model.trust_score,
                model.reliability_score,
                model.interaction_count,
                json.dumps(model.deception_flags),
                model.bot_probability,
                model.first_seen.isoformat(),
                model.last_seen.isoformat(),
                model.model_version
            ))
            conn.commit()
    
    def predict_intent(self, entity_id: str, 
                       context: Optional[Dict] = None) -> Optional[IntentPrediction]:
        """
        Predict what an entity wants before they ask.
        
        Args:
            entity_id: Entity to predict intent for
            context: Optional context (time, recent interactions, etc.)
            
        Returns:
            IntentPrediction or None
        """
        model = self.model_agent(entity_id)
        if not model:
            return None
        
        # Simple prediction based on model
        likely_goals = model.inferred_goals
        
        if not likely_goals:
            return IntentPrediction(
                entity_id=entity_id,
                predicted_intent='unknown',
                confidence=0.3,
                supporting_evidence=['insufficient_data']
            )
        
        # Use time context if available
        current_hour = datetime.now().hour
        if context and 'hour' in context:
            current_hour = context['hour']
        
        # Predict based on typical active hours
        if model.active_hours and current_hour not in model.active_hours:
            # Outside normal hours - might be urgent or automated
            confidence = 0.4
        else:
            confidence = 0.7
        
        prediction = IntentPrediction(
            entity_id=entity_id,
            predicted_intent=likely_goals[0],
            confidence=confidence,
            supporting_evidence=[f"historical_goal: {g}" for g in likely_goals[:3]],
            predicted_next_action=f"engage_with_{likely_goals[0]}"
        )
        
        # Store prediction
        self._save_prediction(prediction)
        
        return prediction
    
    def _save_prediction(self, prediction: IntentPrediction) -> None:
        """Save prediction to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO intent_predictions
                (entity_id, predicted_intent, confidence, supporting_evidence,
                 predicted_next_action, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                prediction.entity_id,
                prediction.predicted_intent,
                prediction.confidence,
                json.dumps(prediction.supporting_evidence),
                prediction.predicted_next_action,
                prediction.timestamp.isoformat()
            ))
            conn.commit()
    
    def detect_deception(self, entity_id: str, 
                        interaction: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect potential deception or bot activity.
        
        Args:
            entity_id: Entity to check
            interaction: Optional specific interaction to analyze
            
        Returns:
            Deception assessment
        """
        model = self.model_agent(entity_id)
        
        if not model:
            return {
                'entity_id': entity_id,
                'bot_probability': 0.5,
                'deception_detected': False,
                'flags': ['insufficient_data'],
                'recommendation': 'monitor'
            }
        
        deception_detected = (
            model.bot_probability > self.DECEPTION_THRESHOLD or
            len(model.deception_flags) > 2
        )
        
        recommendation = 'allow'
        if model.bot_probability > 0.9:
            recommendation = 'block'
        elif model.bot_probability > 0.7:
            recommendation = 'challenge'
        elif deception_detected:
            recommendation = 'monitor'
        
        return {
            'entity_id': entity_id,
            'bot_probability': model.bot_probability,
            'deception_detected': deception_detected,
            'flags': model.deception_flags,
            'trust_score': model.trust_score,
            'recommendation': recommendation
        }
    
    def propose_collaboration(self, target_entity: str, 
                              joint_goal: str,
                              mutual_benefit: str) -> CollaborationProposal:
        """
        Propose a joint action to another entity.
        
        Args:
            target_entity: Entity to collaborate with
            joint_goal: What you want to achieve together
            mutual_benefit: How both parties benefit
            
        Returns:
            CollaborationProposal
        """
        proposal = CollaborationProposal(
            id=f"prop_{target_entity}_{hash(joint_goal) % 10000}_{datetime.now().strftime('%Y%m%d')}",
            target_entity=target_entity,
            proposed_action=joint_goal,
            mutual_benefit=mutual_benefit,
            terms={
                'proposed_by': 'AlleyBot',
                'expected_duration': 'to_be_negotiated',
                'resource_contribution': 'to_be_discussed'
            }
        )
        
        # Store proposal
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO collaboration_proposals
                (id, target_entity, proposed_action, mutual_benefit, terms, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                proposal.id,
                proposal.target_entity,
                proposal.proposed_action,
                proposal.mutual_benefit,
                json.dumps(proposal.terms),
                proposal.status,
                proposal.created_at.isoformat()
            ))
            conn.commit()
        
        logger.info(f"🤝 Collaboration proposed to {target_entity}: {joint_goal[:50]}...")
        
        return proposal
    
    def get_reputation(self, entity_id: str) -> Optional[ReputationAssessment]:
        """
        Get reputation assessment for an entity.
        
        Args:
            entity_id: Entity to assess
            
        Returns:
            ReputationAssessment or None
        """
        model = self.model_agent(entity_id)
        if not model:
            return None
        
        # Build assessment from model
        dimensions = {
            'trustworthiness': model.trust_score,
            'reliability': model.reliability_score,
            'authenticity': 1 - model.bot_probability,
            'engagement_quality': min(1.0, model.interaction_count / 50)
        }
        
        overall = statistics.mean(dimensions.values())
        
        assessment = ReputationAssessment(
            entity_id=entity_id,
            overall_score=overall,
            dimensions=dimensions,
            assessment_basis=[
                f"{model.interaction_count} interactions analyzed",
                f"Communication style: {model.communication_style}",
                f"Bot probability: {model.bot_probability:.0%}"
            ]
        )
        
        # Store assessment
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO reputation_assessments
                (entity_id, overall_score, dimensions, assessment_basis, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                assessment.entity_id,
                assessment.overall_score,
                json.dumps(assessment.dimensions),
                json.dumps(assessment.assessment_basis),
                assessment.last_updated.isoformat()
            ))
            conn.commit()
        
        return assessment
    
    def simulate_community_reaction(self, action: str, 
                                   target_community: Optional[str] = None) -> Dict[str, Any]:
        """
        Predict how a community will react to an action.
        
        Args:
            action: The action to simulate
            target_community: Optional specific community
            
        Returns:
            Predicted reaction
        """
        # Simple heuristic-based simulation
        # In a real implementation, this would use historical data
        
        positive_indicators = ['help', 'support', 'giveaway', 'insight', 'learn']
        negative_indicators = ['spam', 'promote', 'sell', 'scam', 'fake']
        
        action_lower = action.lower()
        
        positive_score = sum(1 for w in positive_indicators if w in action_lower)
        negative_score = sum(1 for w in negative_indicators if w in action_lower)
        
        if positive_score > negative_score:
            sentiment = 'positive'
            confidence = 0.6 + (positive_score * 0.1)
        elif negative_score > positive_score:
            sentiment = 'negative'
            confidence = 0.6 + (negative_score * 0.1)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'predicted_sentiment': sentiment,
            'confidence': min(0.95, confidence),
            'estimated_engagement': 'medium' if sentiment == 'neutral' else 'high',
            'risk_factors': [w for w in negative_indicators if w in action_lower],
            'positive_factors': [w for w in positive_indicators if w in action_lower]
        }
    
    def record_interaction(self, entity_id: str, 
                          interaction_type: str,
                          content: str,
                          response_time: Optional[float] = None,
                          engagement: float = 0) -> None:
        """Record an interaction for future modeling"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO interactions
                (entity_id, interaction_type, content, timestamp, response_time_seconds, engagement_received)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                interaction_type,
                content,
                datetime.now().isoformat(),
                response_time,
                engagement
            ))
            conn.commit()
    
    def get_social_summary(self) -> Dict[str, Any]:
        """Get summary of social intelligence data"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            models = conn.execute(
                "SELECT COUNT(*) as count FROM agent_models"
            ).fetchone()
            
            predictions = conn.execute(
                "SELECT COUNT(*) as count FROM intent_predictions WHERE timestamp > ?",
                ((datetime.now() - timedelta(days=7)).isoformat(),)
            ).fetchone()
            
            proposals = conn.execute(
                "SELECT status, COUNT(*) as count FROM collaboration_proposals GROUP BY status"
            ).fetchall()
            
            high_risk = conn.execute(
                "SELECT COUNT(*) as count FROM agent_models WHERE bot_probability > ?",
                (self.DECEPTION_THRESHOLD,)
            ).fetchone()
        
        return {
            'entities_modeled': models['count'] if models else 0,
            'recent_predictions': predictions['count'] if predictions else 0,
            'collaboration_proposals': {row['status']: row['count'] for row in proposals},
            'high_risk_entities': high_risk['count'] if high_risk else 0
        }


# Fix import
import re

# Singleton
_social_intelligence_instance: Optional[SocialIntelligence] = None


def get_social_intelligence(world_state=None) -> SocialIntelligence:
    """Get or create SocialIntelligence singleton"""
    global _social_intelligence_instance
    if _social_intelligence_instance is None:
        _social_intelligence_instance = SocialIntelligence(world_state)
    return _social_intelligence_instance
