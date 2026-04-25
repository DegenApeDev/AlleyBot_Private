"""
Episodic Memory System for AGI

Goes beyond storage - this system actively influences:
1. What the agent says (tone, content, style)
2. What the agent does (which actions it chooses)
3. How the agent learns (which patterns it prioritizes)

Key innovation: Memories have weights that dynamically adjust future behavior.
"""

import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EpisodicMemory:
    """
    A remembered experience with behavioral impact
    
    Unlike simple storage, this memory type includes:
    - emotional_valence: How positive/negative was this experience (-1 to 1)
    - behavior_delta: How this should change future behavior
    - trigger_patterns: What situations should recall this memory
    """
    id: str
    timestamp: datetime
    context: str  # What was happening
    action: str   # What the agent did
    outcome: str  # What happened as a result
    emotional_valence: float = 0.0  # -1 (bad) to 1 (good)
    
    # Behavioral learning
    behavior_delta: Dict[str, float] = None  # e.g., {'formality': -0.2, 'verbosity': 0.1}
    trigger_patterns: List[str] = None  # Keywords that should trigger this memory
    
    # Usage tracking
    recall_count: int = 0
    last_recalled: Optional[datetime] = None
    relevance_score: float = 1.0  # Decays over time, boosted by recency
    
    def __post_init__(self):
        if self.behavior_delta is None:
            self.behavior_delta = {}
        if self.trigger_patterns is None:
            self.trigger_patterns = []
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'action': self.action,
            'outcome': self.outcome,
            'emotional_valence': self.emotional_valence,
            'behavior_delta': self.behavior_delta,
            'trigger_patterns': self.trigger_patterns,
            'recall_count': self.recall_count,
            'last_recalled': self.last_recalled.isoformat() if self.last_recalled else None,
            'relevance_score': self.relevance_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EpisodicMemory':
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            context=data['context'],
            action=data['action'],
            outcome=data['outcome'],
            emotional_valence=data.get('emotional_valence', 0.0),
            behavior_delta=data.get('behavior_delta', {}),
            trigger_patterns=data.get('trigger_patterns', []),
            recall_count=data.get('recall_count', 0),
            last_recalled=datetime.fromisoformat(data['last_recalled']) if data.get('last_recalled') else None,
            relevance_score=data.get('relevance_score', 1.0)
        )


class EpisodicMemoryStore:
    """
    Stores experiences and actively uses them to modulate behavior
    """
    
    def __init__(self, storage_path: str = 'data/episodic_memory.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[EpisodicMemory] = []
        self._load()
        
    def record(self, context: str, action: str, outcome: str,
               emotional_valence: float = 0.0,
               behavior_delta: Optional[Dict[str, float]] = None,
               trigger_patterns: Optional[List[str]] = None) -> str:
        """
        Record a new experience
        
        Args:
            context: Situation/context (e.g., "User asked about DeFi on Telegram")
            action: What the agent did (e.g., "Explained yield farming simply")
            outcome: Result (e.g., "User said thanks, seemed satisfied")
            emotional_valence: -1 to 1 rating of outcome
            behavior_delta: How to adjust future behavior
            trigger_patterns: Keywords that should recall this
        """
        memory_id = f"ep_{datetime.now().timestamp()}"
        
        memory = EpisodicMemory(
            id=memory_id,
            timestamp=datetime.now(),
            context=context,
            action=action,
            outcome=outcome,
            emotional_valence=emotional_valence,
            behavior_delta=behavior_delta or {},
            trigger_patterns=trigger_patterns or []
        )
        
        self.memories.append(memory)
        self._save()
        
        return memory_id
    
    def recall_relevant(self, current_context: str, k: int = 3) -> List[EpisodicMemory]:
        """
        Find memories relevant to current situation
        
        Uses:
        1. Keyword matching on trigger_patterns
        2. Recency boost
        3. Relevance score decay/boost
        """
        scored_memories = []
        
        for memory in self.memories:
            score = 0.0
            
            # 1. Trigger pattern matching
            for pattern in memory.trigger_patterns:
                if pattern.lower() in current_context.lower():
                    score += 0.5
            
            # 2. Recency boost (exponential decay)
            days_ago = (datetime.now() - memory.timestamp).days
            recency_score = max(0, 1.0 - (days_ago / 30))  # Decay over 30 days
            score += recency_score * 0.3
            
            # 3. Usage boost (frequently recalled memories are important)
            usage_score = min(1.0, memory.recall_count / 10)
            score += usage_score * 0.2
            
            # 4. Emotional significance
            score += abs(memory.emotional_valence) * 0.2
            
            scored_memories.append((score, memory))
        
        # Sort by score and return top k
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # Update recall stats for returned memories
        selected = []
        for score, memory in scored_memories[:k]:
            if score > 0.2:  # Only return if somewhat relevant
                memory.recall_count += 1
                memory.last_recalled = datetime.now()
                selected.append(memory)
        
        self._save()
        return selected
    
    def get_behavior_modulation(self, context: str) -> Dict[str, float]:
        """
        Get accumulated behavior adjustments based on recalled memories
        
        This is the key AGI feature - past experiences actively change
        how the agent behaves RIGHT NOW.
        """
        relevant_memories = self.recall_relevant(context, k=5)
        
        # Accumulate behavior deltas
        modulation = {}
        total_weight = 0
        
        for memory in relevant_memories:
            # Weight by emotional intensity and recency
            weight = abs(memory.emotional_valence) * (1.0 / (1 + memory.recall_count * 0.1))
            total_weight += weight
            
            for behavior, delta in memory.behavior_delta.items():
                if behavior not in modulation:
                    modulation[behavior] = 0.0
                modulation[behavior] += delta * weight
        
        # Normalize
        if total_weight > 0:
            for behavior in modulation:
                modulation[behavior] /= total_weight
                # Clamp to reasonable range
                modulation[behavior] = max(-0.5, min(0.5, modulation[behavior]))
        
        return modulation
    
    def get_lessons_learned(self, topic: str = None) -> List[str]:
        """
        Extract learned lessons from episodic memory
        
        Returns actionable insights like:
        - "When discussing crypto with new users, keep it simple"
        - "User @X prefers technical depth over casual chat"
        """
        lessons = []
        
        for memory in self.memories:
            # Only use memories with clear outcomes
            if abs(memory.emotional_valence) < 0.3:
                continue
            
            # Generate lesson from memory
            valence_word = "worked well" if memory.emotional_valence > 0 else "didn't work"
            lesson = f"When {memory.context}, {memory.action} {valence_word} (outcome: {memory.outcome})"
            
            if topic and topic.lower() in lesson.lower():
                lessons.append(lesson)
            elif not topic:
                lessons.append(lesson)
        
        return lessons[-10:]  # Return 10 most recent lessons
    
    def _save(self):
        """Persist to disk"""
        try:
            data = [m.to_dict() for m in self.memories]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save episodic memory: {e}")
    
    def _load(self):
        """Load from disk"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                self.memories = [EpisodicMemory.from_dict(m) for m in data]
                print(f"✅ Loaded {len(self.memories)} episodic memories")
        except Exception as e:
            print(f"⚠️ Failed to load episodic memory: {e}")
    
    def get_recent_episodes(self, limit: int = 10, filters: Optional[Dict] = None) -> List[EpisodicMemory]:
        """
        Get most recent episodic memories, optionally filtered.
        
        Args:
            limit: Maximum number of memories to return
            filters: Optional dict of field:value pairs to filter by.
                     Supported keys: 'outcome' (str match or 'failure' matches negative valence),
                     'action' (substring match), 'context' (substring match),
                     'min_valence' (float), 'max_valence' (float)
        
        Returns:
            List of recent episodic memories, sorted by timestamp (newest first)
        """
        result = self.memories

        if filters:
            for key, value in filters.items():
                if key == 'outcome':
                    if value == 'failure':
                        result = [m for m in result if m.emotional_valence < -0.3]
                    elif value == 'success':
                        result = [m for m in result if m.emotional_valence > 0.3]
                    else:
                        result = [m for m in result if value.lower() in m.outcome.lower()]
                elif key == 'action':
                    result = [m for m in result if str(value).lower() in m.action.lower()]
                elif key == 'context':
                    result = [m for m in result if str(value).lower() in m.context.lower()]
                elif key == 'min_valence':
                    result = [m for m in result if m.emotional_valence >= float(value)]
                elif key == 'max_valence':
                    result = [m for m in result if m.emotional_valence <= float(value)]

        sorted_memories = sorted(
            result,
            key=lambda m: m.timestamp,
            reverse=True
        )
        return sorted_memories[:limit]

    def record_episode(self, action_type: str = '', context=None, outcome=None,
                       success: bool = True, emotional_valence: float = None,
                       behavior_delta: Optional[Dict[str, float]] = None,
                       trigger_patterns: Optional[List[str]] = None) -> str:
        """
        Convenience alias for record() that accepts the legacy episode schema.

        Handles both string and dict values for context/outcome by converting
        dicts to human-readable strings.
        """
        if isinstance(context, dict):
            context = ', '.join(f'{k}: {v}' for k, v in context.items())
        if isinstance(outcome, dict):
            outcome = ', '.join(f'{k}: {v}' for k, v in outcome.items())

        if emotional_valence is None:
            emotional_valence = 0.5 if success else -0.5

        return self.record(
            context=context or '',
            action=action_type,
            outcome=outcome or '',
            emotional_valence=emotional_valence,
            behavior_delta=behavior_delta,
            trigger_patterns=trigger_patterns,
        )

    def get_all_memories(self) -> List[EpisodicMemory]:
        """Return all stored episodic memories."""
        return list(self.memories)
    
    def get_stats(self) -> Dict:
        """Get statistics about episodic memory"""
        if not self.memories:
            return {'count': 0}
        
        positive = sum(1 for m in self.memories if m.emotional_valence > 0.3)
        negative = sum(1 for m in self.memories if m.emotional_valence < -0.3)
        neutral = len(self.memories) - positive - negative
        
        return {
            'count': len(self.memories),
            'positive_experiences': positive,
            'negative_experiences': negative,
            'neutral_experiences': neutral,
            'total_recalls': sum(m.recall_count for m in self.memories),
            'avg_recalls_per_memory': sum(m.recall_count for m in self.memories) / len(self.memories)
        }


class BehaviorModulator:
    """
    Applies episodic memory to actively change agent behavior
    """
    
    def __init__(self, episodic_store: EpisodicMemoryStore):
        self.episodic = episodic_store
        
        # Base behavioral parameters
        self.base_params = {
            'formality': 0.5,      # 0 = casual, 1 = formal
            'verbosity': 0.5,      # 0 = concise, 1 = detailed
            'technical_depth': 0.5, # 0 = simple, 1 = technical
            'initiative': 0.5,      # 0 = reactive, 1 = proactive
            'creativity': 0.7       # 0 = safe, 1 = experimental
        }
    
    def get_effective_params(self, context: str) -> Dict[str, float]:
        """
        Get behavior parameters adjusted by episodic memory
        
        This is where learning becomes action - the agent changes
        how it behaves based on what it's learned from past interactions.
        """
        # Get modulation from episodic memory
        modulation = self.episodic.get_behavior_modulation(context)
        
        # Apply modulation to base params
        effective = {}
        for param, base_value in self.base_params.items():
            delta = modulation.get(param, 0.0)
            effective[param] = max(0.0, min(1.0, base_value + delta))
        
        return effective
    
    def should_take_initiative(self, context: str) -> bool:
        """Decide if agent should be proactive based on learned patterns"""
        params = self.get_effective_params(context)
        return params['initiative'] > 0.6
    
    def get_response_style(self, context: str) -> str:
        """Get recommended response style based on context and learning"""
        params = self.get_effective_params(context)
        
        style_parts = []
        
        if params['formality'] < 0.3:
            style_parts.append("casual")
        elif params['formality'] > 0.7:
            style_parts.append("formal")
        
        if params['verbosity'] < 0.3:
            style_parts.append("concise")
        elif params['verbosity'] > 0.7:
            style_parts.append("detailed")
        
        if params['technical_depth'] > 0.7:
            style_parts.append("technical")
        elif params['technical_depth'] < 0.3:
            style_parts.append("simple")
        
        return ", ".join(style_parts) if style_parts else "balanced"
    
    def modulate_action(self, action_spec: Dict, context: Dict) -> Dict:
        """
        Modify action based on past experiences BEFORE execution.
        
        This is the core learning loop - every action is informed by
        similar past actions and their outcomes.
        
        Args:
            action_spec: Action to execute {plugin, action_type, params, ...}
            context: Current context {hour, platform, user_id, ...}
            
        Returns:
            Modified action_spec with learned optimizations
        """
        # Build context string for memory recall
        context_str = f"{action_spec.get('plugin')}:{action_spec.get('action_type')}"
        if context.get('platform'):
            context_str += f" on {context['platform']}"
        if context.get('hour'):
            context_str += f" at hour {context['hour']}"
        
        # Recall similar past actions
        similar_episodes = self.episodic.recall_relevant(context_str, k=5)
        
        if not similar_episodes:
            # No past experience, return unmodified
            return action_spec
        
        # Separate successful and failed patterns
        successful = [e for e in similar_episodes if e.emotional_valence > 0.3]
        failed = [e for e in similar_episodes if e.emotional_valence < -0.3]
        
        # Apply learned modifications
        modified_spec = action_spec.copy()
        warnings = []
        
        # Learn from successful patterns
        for episode in successful:
            # Extract timing patterns
            if 'hour' in episode.context and context.get('hour'):
                # If successful action was at similar time, boost confidence
                modified_spec['confidence_boost'] = modified_spec.get('confidence_boost', 0) + 0.1
        
        # Avoid failed patterns
        for episode in failed:
            # Check if current context matches failed context
            current_hour = context.get('hour')
            if current_hour and f"hour {current_hour}" in episode.context:
                warnings.append(f"⚠️ Similar action failed at this hour: {episode.outcome}")
            
            # Check if same platform had failures
            current_platform = context.get('platform')
            if current_platform and current_platform in episode.context:
                warnings.append(f"⚠️ Similar action failed on {current_platform}: {episode.outcome}")
        
        # Add warnings to action spec
        if warnings:
            modified_spec['episodic_warnings'] = warnings
            modified_spec['risk_level'] = 'medium'
        
        # Add learned insights
        if successful:
            modified_spec['episodic_insights'] = [
                f"✓ {len(successful)} similar successful actions recalled"
            ]
        
        return modified_spec
    
    def record_outcome(self, context: str, action: str, outcome: str,
                      success: bool, user_id: Optional[str] = None):
        """
        Record the outcome of an action for future learning
        
        This is how the system improves - every action gets evaluated
        and influences future behavior.
        """
        # Calculate emotional valence based on success/failure
        valence = 0.5 if success else -0.5
        
        # Determine behavior delta based on outcome
        delta = {}
        if success:
            # Reinforce the behavior that worked
            delta = {'initiative': 0.05}  # Slightly more confident
        else:
            # Adjust behavior that didn't work
            delta = {'initiative': -0.05}  # Slightly more cautious
        
        # Generate trigger patterns from context
        triggers = []
        if user_id:
            triggers.append(user_id)
        # Extract keywords from context
        words = context.lower().split()
        triggers.extend([w for w in words if len(w) > 4][:3])
        
        self.episodic.record(
            context=context,
            action=action,
            outcome=outcome,
            emotional_valence=valence,
            behavior_delta=delta,
            trigger_patterns=triggers
        )


# Factory functions
def create_episodic_memory(store_path: str = 'data/episodic_memory.json') -> EpisodicMemoryStore:
    """Create episodic memory store"""
    return EpisodicMemoryStore(store_path)

def create_behavior_modulator(episodic_store: Optional[EpisodicMemoryStore] = None) -> BehaviorModulator:
    """Create behavior modulator with episodic memory"""
    if episodic_store is None:
        episodic_store = create_episodic_memory()
    return BehaviorModulator(episodic_store)
