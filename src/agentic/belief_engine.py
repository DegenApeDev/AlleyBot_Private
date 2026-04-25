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
            ("moltx feed browse is useful for finding content", 0.7, "social", 3),
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
                result['beliefs_updated'] = len(relevant)
            else:
                new_proposition = f"{action} leads to {'success' if actual_success else 'failure'}"
                if context:
                    new_proposition = f"{context}: {action} leads to {'success' if actual_success else 'failure'}"

                key = self._hash(new_proposition)
                self.beliefs[key] = Belief(
                    proposition=new_proposition,
                    confidence=0.6 if actual_success else 0.4,
                    prediction_count=1,
                    correct_predictions=1 if actual_success else 0,
                    domain=domain,
                    source="experience",
                    evidence_for=[outcome_description] if actual_success and outcome_description else [],
                    evidence_against=[outcome_description] if not actual_success and outcome_description else [],
                )
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