"""
BeliefEngine — Predict-Compare-Update Belief System

The core cognitive loop for genuine learning. Every action comes with a prediction.
Every outcome updates beliefs. Over time, the agent builds an accurate model of
what works and what doesn't, independently of LLM calls.

This replaces the Duat/Synergy float arithmetic with real Bayesian belief updating.
"""

import json
import time
import logging
logger = logging.getLogger(__name__)
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


@dataclass
class Belief:
    proposition: str
    confidence: float
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    prediction_count: int = 0
    correct_predictions: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "experience"
    domain: str = "general"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # Phase 4: Episodic context
    context_history: List[Dict] = field(default_factory=list)
    last_outcome: Optional[str] = None
    outcome_timestamps: List[str] = field(default_factory=list)
    # Phase 8.4: Core beliefs - frequently validated beliefs resist decay
    is_core: bool = False
    core_since: Optional[str] = None
    validation_count: int = 0

    @property
    def accuracy(self) -> float:
        if self.prediction_count == 0:
            return 0.5
        return self.correct_predictions / self.prediction_count

    @property
    def sample_size(self) -> int:
        return self.prediction_count

    @property
    def is_reliable(self) -> bool:
        return self.prediction_count >= 5 and abs(self.confidence - 0.5) > 0.1

    @property
    def is_calibrated(self) -> bool:
        if self.prediction_count < 5:
            return False
        return abs(self.confidence - self.accuracy) < 0.15
    
    @property
    def is_conflicting(self) -> bool:
        """Phase 4.6: Check if belief has contradictory evidence"""
        if len(self.evidence_for) >= 2 and len(self.evidence_against) >= 2:
            return True
        return False
    
    @property
    def recency_decay_confidence(self) -> float:
        """Phase 4.5: Decay-weighted confidence - recent outcomes weighted more"""
        if not self.outcome_timestamps:
            return self.confidence
        
        now = datetime.now()
        total_weight = 0.0
        weighted_sum = 0.0
        
        for i, ts in enumerate(self.outcome_timestamps):
            try:
                ts_dt = datetime.fromisoformat(ts)
                hours_ago = (now - ts_dt).total_seconds() / 3600
                # Decay factor: 1.0 for recent, approaches 0.0 for old
                weight = 1.0 / (1.0 + hours_ago / 24.0)
                # Most recent evidence has highest index
                is_success = i < len(self.evidence_for)
                actual = 1.0 if is_success else 0.0
                weighted_sum += weight * actual
                total_weight += weight
            except (ValueError, TypeError):
                continue
        
        if total_weight == 0:
            return self.confidence
        
        return weighted_sum / total_weight

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Belief':
        return cls(
            proposition=data['proposition'],
            confidence=data.get('confidence', 0.5),
            evidence_for=data.get('evidence_for', []),
            evidence_against=data.get('evidence_against', []),
            prediction_count=data.get('prediction_count', 0),
            correct_predictions=data.get('correct_predictions', 0),
            last_updated=data.get('last_updated', datetime.now().isoformat()),
            source=data.get('source', 'experience'),
            domain=data.get('domain', 'general'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            context_history=data.get('context_history', []),
            last_outcome=data.get('last_outcome'),
            outcome_timestamps=data.get('outcome_timestamps', []),
        )


@dataclass
class Prediction:
    action: str
    domain: str
    predicted_outcome: str
    predicted_success: float
    relevant_beliefs: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


class BeliefEngine:
    """
    Core predict-compare-update engine.

    Before every action: predict what will happen based on beliefs.
    After every action: compare prediction to reality, update beliefs.

    This is the fundamental learning mechanism. Beliefs are stored as
    Bayesian-inspired confidence scores that update from evidence, not
    from arbitrary float arithmetic.
    """

    MIN_CONFIDENCE = 0.05
    MAX_CONFIDENCE = 0.95
    LEARNING_RATE = 0.15
    EVIDENCE_CAPACITY = 20

    def __init__(self, storage_path: str = 'data/beliefs.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.beliefs: Dict[str, Belief] = {}
        self.pending_predictions: Dict[str, Prediction] = {}
        self._load()
        self._init_core_beliefs()

    def _init_core_beliefs(self):
        defaults = [
            # Social engagement
            ("posting on moltx generates engagement", 0.6, "social", 3),
            ("replying to trending topics increases visibility", 0.7, "social", 3),
            ("consistent engagement builds reputation", 0.7, "social", 3),
            ("diverse content performs better than repetitive content", 0.6, "content", 3),
            ("too many posts in short succession reduces quality", 0.8, "content", 3),
            ("moltx feed provides content for engagement", 0.7, "social", 3),
            ("moltx post creates visible content on platform", 0.75, "social", 3),
            ("moltx engage interacts with other users content", 0.7, "social", 3),
            ("moltchan send creates posts on moltchan", 0.65, "social", 2),
            ("moltchan engage interacts with moltchan threads", 0.6, "social", 2),
            # Analysis
            ("market analysis requires multiple data points", 0.8, "analysis", 3),
            ("cross-referencing multiple data sources improves accuracy", 0.75, "analysis", 2),
            ("sentiment analysis alone is insufficient for market decisions", 0.7, "analysis", 2),
            # Market / Trading
            ("trading during high volatility is risky", 0.75, "market", 3),
            ("price checks provide market awareness", 0.7, "market", 2),
            ("dex swaps are high-risk actions requiring wallet confirmation", 0.85, "trading", 3),
            ("limit orders reduce slippage risk compared to market orders", 0.7, "trading", 2),
            ("market timing is unreliable without multiple data sources", 0.8, "market", 2),
            # Onchain
            ("gas price checks before transactions prevent overpaying", 0.8, "onchain", 2),
            ("contract verification before interaction prevents scams", 0.85, "onchain", 2),
            ("transaction confirmation tracking prevents lost transactions", 0.75, "onchain", 2),
            # Security
            ("checking wallet balances regularly detects issues early", 0.9, "security", 3),
            ("rate-limiting API calls prevents service bans", 0.8, "security", 2),
            ("rotating API keys reduces compromise risk", 0.7, "security", 2),
            # Content
            ("scheduling posts during peak hours increases engagement", 0.7, "content", 2),
            ("varying content formats maintains audience interest", 0.65, "content", 2),
            # Self-improvement
            ("skill gaps identified from repeated failures should be addressed", 0.8, "self_improvement", 3),
            ("learning from errors improves future performance", 0.85, "self_improvement", 3),
        ]
        for prop, conf, domain, count in defaults:
            key = self._hash(prop)
            if key not in self.beliefs:
                self.beliefs[key] = Belief(
                    proposition=prop, confidence=conf, domain=domain, source="seed",
                    prediction_count=count, correct_predictions=count
                )

    @staticmethod
    def _hash(text: str) -> str:
        return text.lower().strip()[:80]

    def predict(self, action_description: str, domain: str = "general") -> Prediction:
        with self._lock:
            relevant = self.find_relevant_beliefs(action_description, domain)
            if not relevant:
                return Prediction(
                    action=action_description,
                    domain=domain,
                    predicted_outcome="unknown — no prior experience",
                    predicted_success=0.5,
                    relevant_beliefs=[],
                )

            weighted_confidence = 0.0
            total_weight = 0.0
            for belief in relevant:
                weight = belief.prediction_count + 1
                weighted_confidence += belief.confidence * weight
                total_weight += weight

            predicted_success = weighted_confidence / total_weight if total_weight > 0 else 0.5
            predicted_success = max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, predicted_success))

            most_confident = max(relevant, key=lambda b: b.confidence * (b.prediction_count + 1))
            prediction = Prediction(
                action=action_description,
                domain=domain,
                predicted_outcome=most_confident.proposition,
                predicted_success=predicted_success,
                relevant_beliefs=[b.proposition for b in relevant[:5]],
            )

            pred_key = self._hash(action_description)
            self.pending_predictions[pred_key] = prediction
            return prediction

    def update_from_outcome(
        self,
        action: str,
        domain: str,
        predicted_success: float,
        actual_success: bool,
        context: str = "",
        outcome_description: str = "",
    ) -> Dict:
        with self._lock:
            pred_key = self._hash(action)
            prediction = self.pending_predictions.pop(pred_key, None)

            result = {
                'action': action,
                'domain': domain,
                'predicted': predicted_success,
                'actual': 1.0 if actual_success else 0.0,
                'error': abs(predicted_success - (1.0 if actual_success else 0.0)),
                'beliefs_updated': 0,
                'new_beliefs_created': 0,
            }

            relevant = self.find_relevant_beliefs(action, domain)

            if relevant:
                for belief in relevant:
                    prediction_error = abs(belief.confidence - (1.0 if actual_success else 0.0))
                    if actual_success:
                        belief.confidence += self.LEARNING_RATE * (1.0 - belief.confidence)
                        belief.correct_predictions += 1
                        if outcome_description and outcome_description not in belief.evidence_for:
                            belief.evidence_for.append(outcome_description)
                            if len(belief.evidence_for) > self.EVIDENCE_CAPACITY:
                                belief.evidence_for.pop(0)
                    else:
                        belief.confidence -= self.LEARNING_RATE * belief.confidence
                        if outcome_description and outcome_description not in belief.evidence_against:
                            belief.evidence_against.append(outcome_description)
                            if len(belief.evidence_against) > self.EVIDENCE_CAPACITY:
                                belief.evidence_against.pop(0)

                    belief.prediction_count += 1
                    belief.confidence = max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, belief.confidence))
                    belief.last_updated = datetime.now().isoformat()
                    
                    # Phase 4.2: Add episodic context to belief
                    self._add_context_to_belief(belief, context, outcome_description or ("success" if actual_success else "failure"))
                    
                result['beliefs_updated'] = len(relevant)
            else:
                new_proposition = f"{action} leads to {'success' if actual_success else 'failure'}"
                if context:
                    new_proposition = f"{context}: {action} leads to {'success' if actual_success else 'failure'}"

                key = self._hash(new_proposition)
                new_belief = Belief(
                    proposition=new_proposition,
                    confidence=0.6 if actual_success else 0.4,
                    prediction_count=1,
                    correct_predictions=1 if actual_success else 0,
                    domain=domain,
                    source="experience",
                    evidence_for=[outcome_description] if actual_success and outcome_description else [],
                    evidence_against=[outcome_description] if not actual_success and outcome_description else [],
                )
                # Phase 4.2: Add episodic context to new belief
                self._add_context_to_belief(new_belief, context, outcome_description or ("success" if actual_success else "failure"))
                self.beliefs[key] = new_belief
                result['new_beliefs_created'] = 1

            self._save()
            return result

    def find_relevant_beliefs(self, query: str, domain: str = "general") -> List[Belief]:
        # Normalize query: split compound tokens like "moltx:feed_browse" and "social:post"
        query_words = set()
        for word in query.lower().split():
            # Split on colon, slash, underscore, dot
            for sub in word.replace(':', ' ').replace('/', ' ').replace('_', ' ').replace('.', ' ').split():
                if len(sub) >= 2:
                    query_words.add(sub)

        scored = []

        for belief in self.beliefs.values():
            if domain != "general" and belief.domain != "general" and belief.domain != domain:
                continue

            belief_words = set(belief.proposition.lower().split())
            overlap = len(query_words & belief_words)

            if overlap == 0:
                continue

            score = overlap / max(len(query_words), 1)
            score *= (0.5 + 0.5 * belief.prediction_count / max(belief.prediction_count, 10))
            score *= (1.0 + abs(belief.confidence - 0.5))

            scored.append((score, belief))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scored[:10]]
    
    # ── Phase 4.1: Embedding-based Semantic Retrieval ─────────────────
    
    def find_relevant_beliefs_semantic(self, query: str, domain: str = "general", top_k: int = 10) -> List[Belief]:
        """Phase 4.1: Semantic similarity using sentence embeddings.
        
        Uses global SentenceTransformer for vector similarity.
        Falls back to keyword matching if embeddings unavailable.
        """
        try:
            from src.utils.embedding_model import get_sentence_transformer
            model = get_sentence_transformer()
        except Exception:
            logger.debug("Embedding model unavailable, using keyword matching")
            return self.find_relevant_beliefs(query, domain)
        
        try:
            query_embedding = model.encode([query])
            belief_texts = []
            belief_list = []
            
            for belief in self.beliefs.values():
                if domain != "general" and belief.domain != "general" and belief.domain != domain:
                    continue
                # Include proposition + context for richer embedding
                context = " ".join(belief.evidence_for[-3:] + belief.evidence_against[-3:])
                text = f"{belief.proposition} {context}"
                belief_texts.append(text)
                belief_list.append(belief)
            
            if not belief_texts:
                return []
            
            belief_embeddings = model.encode(belief_texts)
            
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(query_embedding, belief_embeddings)[0]
            
            scored = []
            for i, belief in enumerate(belief_list):
                score = similarities[i]
                # Boost score based on prediction count (more data = more reliable)
                boost = (0.5 + 0.5 * belief.prediction_count / max(belief.prediction_count, 10))
                adjusted_score = score * boost
                scored.append((adjusted_score, belief))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [b for _, b in scored[:top_k]]
            
        except ImportError:
            logger.debug("sklearn not available, using keyword matching")
            return self.find_relevant_beliefs(query, domain)
        except Exception as e:
            logger.debug(f"Semantic retrieval failed, falling back to keyword: {e}")
            return self.find_relevant_beliefs(query, domain)
    
    # ── Phase 4.6: Belief Conflict Detection ────────────────────────
    
    def detect_conflicts(self, domain: str = None) -> List[Dict]:
        """Phase 4.6: Detect beliefs with strong contradictory evidence.
        
        Returns list of conflicting beliefs with explanation.
        """
        conflicts = []
        
        for belief in self.beliefs.values():
            if domain and belief.domain != domain:
                continue
            
            if not belief.is_conflicting:
                continue
            
            conflict_ratio = len(belief.evidence_against) / max(len(belief.evidence_for), 1)
            
            conflicts.append({
                'belief': belief.proposition,
                'domain': belief.domain,
                'confidence': belief.confidence,
                'evidence_for_count': len(belief.evidence_for),
                'evidence_against_count': len(belief.evidence_against),
                'conflict_ratio': conflict_ratio,
                'recommendation': self._resolve_conflict_recommendation(belief),
            })
        
        conflicts.sort(key=lambda x: x['conflict_ratio'], reverse=True)
        return conflicts
    
    def _resolve_conflict_recommendation(self, belief: Belief) -> str:
        """Generate recommendation for resolving belief conflict."""
        if belief.confidence > 0.6:
            return "Belief strongly held despite conflicts - investigate specific conditions"
        elif belief.confidence < 0.4:
            return "Low confidence - consider deprecating or splitting into conditional beliefs"
        else:
            return "Moderate conflict - refine with more specific context conditions"
    
    # ── Phase 4.3: Counterfactual Reasoning ──────────────────────────
    
    def generate_counterfactuals(self, action: str, domain: str, failed_context: str) -> List[Dict]:
        """Phase 4.3: Generate "what if" alternatives after action failure.
        
        When an action fails, this method searches for similar contexts where
        different approaches succeeded, suggesting alternative actions.
        """
        relevant = self.find_relevant_beliefs(action, domain)
        
        counterfactuals = []
        
        for belief in relevant:
            # Check if this belief has success evidence in different contexts
            if not belief.context_history:
                continue
            
            successful_contexts = [
                entry for entry in belief.context_history
                if 'success' in entry.get('outcome', '').lower()
            ]
            
            for success_ctx in successful_contexts:
                # Calculate similarity to failed context
                failed_words = set(failed_context.lower().split())
                success_words = set(success_ctx['context'].lower().split())
                overlap = len(failed_words & success_words)
                diff_words = failed_words - success_words
                
                if overlap > 0 and diff_words:
                    counterfactuals.append({
                        'original_action': action,
                        'suggested_alternative': f"Try with: {', '.join(diff_words)}",
                        'similar_context': success_ctx['context'],
                        'similarity_score': overlap / max(len(failed_words | success_words), 1),
                        'confidence': belief.confidence * 0.8,  # Discount for uncertainty
                    })
        
        counterfactuals.sort(key=lambda x: x['confidence'], reverse=True)
        return counterfactuals[:5]

    # ── Phase 4.2: Update with Context ────────────────────────────────

    def _add_context_to_belief(self, belief: Belief, context: str, outcome: str):
        """Phase 4.2: Store situational context in belief."""
        context_entry = {
            'context': context[:200],
            'outcome': outcome[:100],
            'timestamp': datetime.now().isoformat(),
            'confidence_at_time': belief.confidence,
        }
        
        belief.context_history.append(context_entry)
        belief.last_outcome = outcome
        
        belief.outcome_timestamps.append(datetime.now().isoformat())
        
        # Keep only last 20 context entries
        if len(belief.context_history) > 20:
            belief.context_history = belief.context_history[-20:]
        if len(belief.outcome_timestamps) > 20:
            belief.outcome_timestamps = belief.outcome_timestamps[-20:]

    def should_wait(self, action: str, domain: str = "general") -> Tuple[bool, str]:
        relevant = self.find_relevant_beliefs(action, domain)

        if not relevant:
            return True, f"No prior experience with '{action}'. Gather information first."

        most_reliable = max(relevant, key=lambda b: b.prediction_count)

        # Only suggest waiting for historically bad actions (low confidence with significant data)
        if most_reliable.confidence < 0.35 and most_reliable.prediction_count >= 5:
            return True, f"Historically low success ({most_reliable.confidence:.0%}). Avoid or change approach."

        return False, ""

    def explain_failure(self, action: str, domain: str = "general") -> List[str]:
        relevant = self.find_relevant_beliefs(action, domain)
        explanations = []

        for belief in relevant:
            if belief.confidence < 0.35:
                explanations.append(
                    f"Low confidence belief: '{belief.proposition}' ({belief.confidence:.0%}, "
                    f"{belief.prediction_count} attempts)"
                )
            if len(belief.evidence_against) > 2:
                explanations.append(
                    f"Strong counter-evidence for '{belief.proposition}': "
                    f"{len(belief.evidence_against)} failures recorded"
                )

        return explanations or ["No specific beliefs explain this failure. This may be a novel situation."]

    def get_domain_strengths(self) -> Dict[str, Dict]:
        domain_stats = {}
        for belief in self.beliefs.values():
            if belief.source == "seed":
                continue
            d = belief.domain
            if d not in domain_stats:
                domain_stats[d] = {'count': 0, 'successes': 0, 'avg_confidence': 0.0}
            domain_stats[d]['count'] += 1
            domain_stats[d]['successes'] += belief.correct_predictions
            domain_stats[d]['avg_confidence'] += belief.confidence

        for d in domain_stats:
            s = domain_stats[d]
            if s['count'] > 0:
                s['avg_confidence'] /= s['count']
                s['success_rate'] = min(s['successes'] / s['count'], 1.0)
            else:
                s['success_rate'] = 0.0

        return domain_stats

    def get_calibration_report(self) -> Dict:
        predictions = [b for b in self.beliefs.values() if b.prediction_count >= 5]
        if not predictions:
            return {'total_beliefs': len(self.beliefs), 'experienced_beliefs': 0, 'calibrated': False}

        calibration_bins = {}
        for b in predictions:
            bucket = round(b.confidence, 1)
            if bucket not in calibration_bins:
                calibration_bins[bucket] = {'predicted': [], 'actual': []}
            calibration_bins[bucket]['predicted'].append(b.confidence)
            calibration_bins[bucket]['actual'].append(b.accuracy)

        calibration_curve = {}
        for bucket in sorted(calibration_bins.keys()):
            bins = calibration_bins[bucket]
            avg_predicted = sum(bins['predicted']) / len(bins['predicted'])
            avg_actual = sum(bins['actual']) / len(bins['actual'])
            calibration_curve[f"{bucket:.1f}"] = {
                'predicted_confidence': round(avg_predicted, 2),
                'actual_accuracy': round(avg_actual, 2),
                'sample_size': len(bins['predicted']),
            }

        avg_error = sum(abs(b.confidence - b.accuracy) for b in predictions) / len(predictions)

        return {
            'total_beliefs': len(self.beliefs),
            'experienced_beliefs': len(predictions),
            'calibration_error': round(avg_error, 3),
            'calibrated': avg_error < 0.15,
            'calibration_curve': calibration_curve,
            'overconfident_domains': [
                b.domain for b in predictions
                if b.confidence > b.accuracy + 0.2 and b.prediction_count >= 5
            ],
            'underconfident_domains': [
                b.domain for b in predictions
                if b.confidence < b.accuracy - 0.2 and b.prediction_count >= 5
            ],
        }

    def _save(self):
        with self._lock:
            try:
                data = {k: v.to_dict() for k, v in self.beliefs.items()}
                with open(self.storage_path, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logging.getLogger(__name__).warning(f"BeliefEngine save failed: {e}")

    def _load(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                with self._lock:
                    self.beliefs = {k: Belief.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logging.getLogger(__name__).warning(f"BeliefEngine load failed: {e}")
            with self._lock:
                self.beliefs = {}


def get_belief_engine(storage_path: str = 'data/beliefs.json') -> BeliefEngine:
    return BeliefEngine(storage_path)


# 8.4: Core belief promotion/demotion methods
def promote_to_core(belief: Belief, threshold: int = 10) -> Belief:
    """Promote frequently-validated belief to core (resists decay)"""
    if belief.validation_count >= threshold and belief.is_calibrated:
        belief.is_core = True
        belief.core_since = datetime.now().isoformat()
    return belief


def demote_from_core(belief: Belief) -> Belief:
    """Demote core belief back to regular (e.g., if it becomes stale)"""
    if belief.is_core and belief.last_updated:
        try:
            last_update = datetime.fromisoformat(belief.last_updated)
            if (datetime.now() - last_update).days > 60:
                belief.is_core = False
                belief.core_since = None
        except Exception:
            pass
    return belief


def get_core_beliefs(belief_engine: BeliefEngine) -> List[Belief]:
    """Get all core beliefs that resist decay"""
    return [b for b in belief_engine.beliefs.values() if b.is_core]


def consolidate_long_term_memory(belief_engine: BeliefEngine) -> int:
    """
    Phase 8.4: Long-term memory consolidation
    Promotes frequently-validated beliefs to core beliefs that resist decay.
    Returns number of beliefs promoted.
    """
    promoted = 0
    for belief in belief_engine.beliefs.values():
        if not belief.is_core and belief.validation_count >= 10 and belief.is_calibrated:
            belief.is_core = True
            belief.core_since = datetime.now().isoformat()
            promoted += 1
    
    if promoted > 0:
        belief_engine._save()
    
    return promoted