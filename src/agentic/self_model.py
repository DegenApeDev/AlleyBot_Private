"""
SelfModel — The Agent's Model of Its Own Capabilities

Tracks what the agent is good at, what it should avoid, what it should
learn, and whether its confidence predictions match reality (calibration).

This replaces MetaCognitionEngine's 5-statistic average + letter grade
with genuine calibration tracking and capability assessment.
"""

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class CapabilityEstimate:
    domain: str
    action_type: str
    success_rate: float = 0.0
    sample_size: int = 0
    recent_trend: str = "unknown"
    best_conditions: List[str] = field(default_factory=list)
    worst_conditions: List[str] = field(default_factory=list)
    avg_predicted_confidence: float = 0.0
    avg_actual_success: float = 0.0
    last_attempt: str = field(default_factory=lambda: datetime.now().isoformat())
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    @property
    def is_reliable(self) -> bool:
        return self.sample_size >= 10

    @property
    def is_calibrated(self) -> bool:
        if self.sample_size < 5:
            return True
        return abs(self.avg_predicted_confidence - self.avg_actual_success) < 0.2

    @property
    def is_overconfident(self) -> bool:
        return self.avg_predicted_confidence > self.avg_actual_success + 0.15 and self.sample_size >= 5

    @property
    def is_underconfident(self) -> bool:
        return self.avg_predicted_confidence < self.avg_actual_success - 0.15 and self.sample_size >= 5

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CapabilityEstimate':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SelfModel:
    """
    Genuine self-model: what am I good at? What should I avoid?
    Am I calibrated? What should I learn next?

    Uses actual outcome data, not heuristics. The calibration curve
    tells us whether the agent's confidence matches reality.
    """

    def __init__(self, storage_path: str = 'data/self_model.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.capabilities: Dict[str, CapabilityEstimate] = {}
        self.outcome_history: List[Dict] = []
        self._load()

    def record_outcome(
        self,
        domain: str,
        action_type: str,
        predicted_confidence: float,
        actual_success: bool,
        context: str = "",
    ) -> Dict:
        with self._lock:
            key = f"{domain}:{action_type}"
            cap = self.capabilities.get(key, CapabilityEstimate(
                domain=domain, action_type=action_type
            ))

            cap.sample_size += 1
            cap.avg_actual_success = (
                (cap.avg_actual_success * (cap.sample_size - 1) + (1.0 if actual_success else 0.0))
                / cap.sample_size
            )
            cap.avg_predicted_confidence = (
                (cap.avg_predicted_confidence * (cap.sample_size - 1) + predicted_confidence)
                / cap.sample_size
            )

            if actual_success:
                cap.consecutive_successes += 1
                cap.consecutive_failures = 0
                if context and context not in cap.best_conditions:
                    cap.best_conditions.append(context)
                    if len(cap.best_conditions) > 10:
                        cap.best_conditions.pop(0)
            else:
                cap.consecutive_failures += 1
                cap.consecutive_successes = 0
                if context and context not in cap.worst_conditions:
                    cap.worst_conditions.append(context)
                    if len(cap.worst_conditions) > 10:
                        cap.worst_conditions.pop(0)

            recent = self._get_recent_outcomes(key, count=10)
            if len(recent) >= 3:
                recent_rate = sum(1 for r in recent if r.get('actual', False)) / len(recent)
                overall_rate = cap.avg_actual_success
                if recent_rate > overall_rate + 0.1:
                    cap.recent_trend = "improving"
                elif recent_rate < overall_rate - 0.1:
                    cap.recent_trend = "declining"
                else:
                    cap.recent_trend = "stable"
            else:
                cap.recent_trend = "unknown"

            cap.success_rate = cap.avg_actual_success
            cap.last_attempt = datetime.now().isoformat()
            self.capabilities[key] = cap

            self.outcome_history.append({
                'domain': domain,
                'action_type': action_type,
                'predicted': predicted_confidence,
                'actual': actual_success,
                'context': context,
                'timestamp': datetime.now().isoformat(),
            })
            if len(self.outcome_history) > 1000:
                self.outcome_history = self.outcome_history[-500:]

            self._save()

            return {
                'domain': domain,
                'action_type': action_type,
                'confidence': predicted_confidence,
                'success': actual_success,
                'calibrated': cap.is_calibrated,
                'trend': cap.recent_trend,
                'sample_size': cap.sample_size,
            }

    def _get_recent_outcomes(self, key: str, count: int = 10) -> List[Dict]:
        matches = [
            o for o in self.outcome_history
            if f"{o['domain']}:{o['action_type']}" == key
        ]
        return matches[-count:]

    def get_confidence_for(self, domain: str, action_type: str) -> float:
        key = f"{domain}:{action_type}"
        cap = self.capabilities.get(key)
        if not cap or cap.sample_size < 3:
            return 0.5
        return cap.avg_actual_success

    def should_attempt(self, domain: str, action_type: str) -> Tuple[bool, str]:
        key = f"{domain}:{action_type}"
        cap = self.capabilities.get(key)

        if not cap or cap.sample_size < 3:
            return True, f"No strong signal yet ({cap.sample_size if cap else 0} attempts). Worth trying."

        if cap.consecutive_failures >= 5:
            return False, f"5 consecutive failures in {domain}.{action_type}. Stop and rethink."

        if cap.success_rate < 0.2 and cap.sample_size >= 10:
            return False, f"Very low success rate ({cap.success_rate:.0%}) over {cap.sample_size} attempts. Avoid."

        if cap.is_overconfident and cap.sample_size >= 10:
            return True, f"Proceed cautiously — historically overconfident in {domain} (predicted {cap.avg_predicted_confidence:.0%}, actual {cap.avg_actual_success:.0%})."

        return True, f"Success rate {cap.success_rate:.0%} over {cap.sample_size} attempts. Trend: {cap.recent_trend}."

    def what_should_i_learn(self) -> List[Dict]:
        blind_spots = []
        for key, cap in self.capabilities.items():
            if cap.sample_size < 5 and cap.consecutive_failures > 0:
                blind_spots.append({
                    'domain': cap.domain,
                    'action_type': cap.action_type,
                    'reason': 'low_data_with_failures',
                    'sample_size': cap.sample_size,
                    'success_rate': cap.success_rate,
                    'priority': 'high',
                })
            elif cap.sample_size < 10:
                blind_spots.append({
                    'domain': cap.domain,
                    'action_type': cap.action_type,
                    'reason': 'insufficient_data',
                    'sample_size': cap.sample_size,
                    'success_rate': cap.success_rate,
                    'priority': 'medium',
                })
        blind_spots.sort(key=lambda x: x['sample_size'])
        return blind_spots[:5]

    def what_should_i_avoid(self) -> List[Dict]:
        avoid = []
        for key, cap in self.capabilities.items():
            if cap.sample_size >= 5 and cap.success_rate < 0.3:
                avoid.append({
                    'domain': cap.domain,
                    'action_type': cap.action_type,
                    'success_rate': cap.success_rate,
                    'sample_size': cap.sample_size,
                    'consecutive_failures': cap.consecutive_failures,
                })
            elif cap.consecutive_failures >= 3:
                avoid.append({
                    'domain': cap.domain,
                    'action_type': cap.action_type,
                    'success_rate': cap.success_rate,
                    'sample_size': cap.sample_size,
                    'consecutive_failures': cap.consecutive_failures,
                })
        avoid.sort(key=lambda x: x['success_rate'])
        return avoid

    def what_am_i_good_at(self) -> List[Dict]:
        strengths = []
        for key, cap in self.capabilities.items():
            if cap.is_reliable and cap.success_rate > 0.7:
                strengths.append({
                    'domain': cap.domain,
                    'action_type': cap.action_type,
                    'success_rate': cap.success_rate,
                    'sample_size': cap.sample_size,
                    'trend': cap.recent_trend,
                    'best_conditions': cap.best_conditions[:3],
                })
        strengths.sort(key=lambda x: x['success_rate'], reverse=True)
        return strengths

    def get_calibration_curve(self) -> Dict:
        predictions = [o for o in self.outcome_history if o.get('predicted') is not None]
        if len(predictions) < 10:
            return {'total_outcomes': len(self.outcome_history), 'with_predictions': len(predictions), 'calibrated': False, 'message': 'Need more data'}

        bins = defaultdict(lambda: {'predicted': [], 'actual': []})
        for o in predictions:
            bucket = round(o['predicted'], 1)
            bins[bucket]['predicted'].append(o['predicted'])
            bins[bucket]['actual'].append(1.0 if o['actual'] else 0.0)

        curve = {}
        for bucket in sorted(bins.keys()):
            b = bins[bucket]
            curve[f"{bucket:.1f}"] = {
                'predicted_confidence': round(sum(b['predicted']) / len(b['predicted']), 2),
                'actual_success_rate': round(sum(b['actual']) / len(b['actual']), 2),
                'sample_size': len(b['predicted']),
            }

        all_errors = [abs(o['predicted'] - (1.0 if o['actual'] else 0.0)) for o in predictions]
        mean_abs_error = sum(all_errors) / len(all_errors)

        return {
            'total_outcomes': len(self.outcome_history),
            'with_predictions': len(predictions),
            'mean_absolute_error': round(mean_abs_error, 3),
            'calibrated': mean_abs_error < 0.2,
            'calibration_curve': curve,
            'overconfident_domains': list({
                cap.domain for cap in self.capabilities.values() if cap.is_overconfident and cap.is_reliable
            }),
            'underconfident_domains': list({
                cap.domain for cap in self.capabilities.values() if cap.is_underconfident and cap.is_reliable
            }),
        }

    def generate_self_awareness_report(self) -> Dict:
        calibration = self.get_calibration_curve()
        strengths = self.what_am_i_good_at()
        avoid = self.what_should_i_avoid()
        learn = self.what_should_i_learn()

        domain_summary = {}
        for key, cap in self.capabilities.items():
            domain_summary[cap.domain] = {
                'success_rate': round(cap.success_rate, 2),
                'attempts': cap.sample_size,
                'trend': cap.recent_trend,
                'calibrated': cap.is_calibrated,
            }

        return {
            'generated_at': datetime.now().isoformat(),
            'overall_calibration': calibration,
            'strengths': strengths,
            'weaknesses': avoid,
            'learning_priorities': learn,
            'domain_capabilities': domain_summary,
            'recommendation': self._generate_recommendation(strengths, avoid, learn),
        }

    def _generate_recommendation(self, strengths, avoid, learn) -> str:
        parts = []
        if strengths:
            best = max(strengths, key=lambda x: x['success_rate'])
            parts.append(f"Leverage {best['domain']}.{best['action_type']} (success rate: {best['success_rate']:.0%})")
        if avoid:
            worst = min(avoid, key=lambda x: x['success_rate'])
            parts.append(f"Avoid {worst['domain']}.{worst['action_type']} (success rate: {worst['success_rate']:.0%})")
        if learn:
            top_learn = learn[0]
            parts.append(f"Practice {top_learn['domain']}.{top_learn['action_type']} to build data (only {top_learn['sample_size']} attempts)")
        return " | ".join(parts) if parts else "Continue standard operations"

    def _save(self):
        with self._lock:
            try:
                data = {
                    'capabilities': {k: v.to_dict() for k, v in self.capabilities.items()},
                    'outcome_history': self.outcome_history[-500:],
                }
                with open(self.storage_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logging.getLogger(__name__).warning(f"SelfModel save failed: {e}")

    def _load(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                with self._lock:
                    self.capabilities = {
                        k: CapabilityEstimate.from_dict(v)
                        for k, v in data.get('capabilities', {}).items()
                    }
                    self.outcome_history = data.get('outcome_history', [])
        except Exception as e:
            logging.getLogger(__name__).warning(f"SelfModel load failed: {e}")
            with self._lock:
                self.capabilities = {}
                self.outcome_history = []


def get_self_model(storage_path: str = 'data/self_model.json') -> SelfModel:
    return SelfModel(storage_path)