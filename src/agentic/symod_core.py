"""
SyMod Core Integration - Mathematical Truth Framework for AlleyBot

This module provides the core SyMod interface that ALL plugins can use.
SyMod is AlleyBot's mathematical validation layer - not plugin-specific.

Any plugin can:
1. Observe data (posts, events, transactions, etc.)
2. Get SyMod-validated action proposals
3. Reflect outcomes back to the world model
4. Query SyMod for decision validation
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Get SyMod functions
from src.synergy import get_symod, get_c2v_bridge

logger = logging.getLogger(__name__)


@dataclass
class SyModObservation:
    """Generic observation that any plugin can submit to SyMod"""
    observation_type: str  # 'post', 'event', 'transaction', 'user', 'content', etc.
    source_plugin: str     # Which plugin submitted this
    data: Dict[str, Any]   # Plugin-specific data
    timestamp: datetime = field(default_factory=datetime.now)
    symod_metrics: Dict = field(default_factory=dict)
    importance: float = 0.5  # Attentional priority (0.0 low, 1.0 critical)  # Populated by SyMod


@dataclass
class SyModActionProposal:
    """Action proposal from SyMod with mathematical validation"""
    action_type: str       # 'like', 'reply', 'post', 'trade', 'follow', etc.
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    content: Optional[str] = None
    justification: str = ""
    
    # SyMod validation metrics
    confidence: float = 0.0
    impedance: float = 0.0
    digital_root: int = 0
    field_status: str = "unknown"  # Stable, Volatile, Collapse
    golden_window_aligned: bool = False
    valid: bool = False
    
    # Plugin context
    source_plugin: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class SyModActionOutcome:
    """Outcome of an action for SyMod reflection"""
    action_type: str
    success: bool
    target_id: Optional[str] = None
    engagement_received: float = 0.0
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class SyModCoreManager:
    """
    Core SyMod Manager - Single source of truth for mathematical validation
    
    This is NOT plugin-specific. Any plugin can use this to:
    - Validate decisions through SyMod's mathematical framework
    - Store observations in the unified world model
    - Get action proposals scored by confidence
    - Reflect on outcomes to adjust future behavior
    """
    
    def __init__(self, core=None, storage_path: str = 'data/symod_core_state.json'):
        self.core = core
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize SyMod
        try:
            self.symod = get_symod()
            self.c2v = get_c2v_bridge()
            self.enabled = True
            logger.info("🔢 SyMod Core Manager: ACTIVE")
        except Exception as e:
            logger.error(f"❌ SyMod initialization failed: {e}")
            self.symod = None
            self.c2v = None
            self.enabled = False
        
        # Rate limit configuration (applies across all plugins)
        self.config = self._load_config()
        
        # Universal world state (shared across all plugins)
        self.entities: Dict[str, Dict] = {}  # Users, agents, accounts
        self.topics: Dict[str, float] = {}   # Topic weights
        self.action_history: List[Dict] = []  # Cross-plugin action history
        
        # Plugin registry
        self.registered_plugins: Dict[str, Dict] = {}
        
        self._load_state()
    
    def _load_config(self) -> Dict:
        """Load SyMod configuration from environment"""
        mode = os.getenv('ALLEY_SYMOD_MODE', 'normal').lower()
        
        modes = {
            'conservative': {
                'confidence_threshold': 0.8,
                'max_actions_per_cycle': 10,
                'require_golden_window': True,
                'block_on_collapse': True
            },
            'normal': {
                'confidence_threshold': 0.6,
                'max_actions_per_cycle': 20,
                'require_golden_window': False,
                'block_on_collapse': True
            },
            'aggressive': {
                'confidence_threshold': 0.4,
                'max_actions_per_cycle': 50,
                'require_golden_window': False,
                'block_on_collapse': False
            }
        }
        
        return modes.get(mode, modes['normal'])
    
    def register_plugin(self, plugin_name: str, plugin_config: Dict = None):
        """
        Register a plugin with SyMod
        
        Any plugin can call this to enable SyMod-driven behavior:
        - Social plugins (MoltX, Clawbr, etc.)
        - DeFi plugins (trading, swaps)
        - Analytics plugins
        - Any plugin that makes decisions
        """
        self.registered_plugins[plugin_name] = {
            'config': plugin_config or {},
            'registered_at': datetime.now().isoformat(),
            'observations_count': 0,
            'actions_proposed': 0,
            'actions_executed': 0
        }
        logger.info(f"🔌 Plugin registered with SyMod: {plugin_name}")
    
    def observe(self, observation: SyModObservation) -> Dict:
        """
        Submit an observation to SyMod
        
        Any plugin can observe:
        - Social: posts, likes, follows, mentions
        - DeFi: transactions, prices, liquidity
        - System: errors, events, state changes
        """
        if not self.enabled:
            return {'observed': False, 'error': 'SyMod not available'}
        
        # Vectorize content through C2V Bridge
        content_str = str(observation.data.get('content', observation.data))
        vector = self.c2v.vectorize_debate_context(
            content_str,
            raw_math_value=hash(str(observation.data)) % 1000000
        )
        
        # Calculate SyMod metrics
        data_hash = hash(str(observation.data))
        digital_root = self.symod.D(abs(data_hash))
        
        # Calculate mass/impedance
        content_mass = self.symod.Ma(len(content_str))
        
        observation.symod_metrics = {
            'sentiment_mass': vector.sentiment_mass,
            'pressure_vector': vector.pressure_vector,
            'logical_impedance': vector.logical_impedance,
            'field_status': vector.synergy_field_status,
            'digital_root': digital_root,
            'content_mass': content_mass,
            'valid': vector.valid and vector.synergy_field_status != "Collapse",
            'timestamp': datetime.now().isoformat()
        }
        
        # Update entity tracking
        entity_id = observation.data.get('author_id') or observation.data.get('user_id')
        if entity_id:
            if entity_id not in self.entities:
                self.entities[entity_id] = {
                    'first_seen': datetime.now().isoformat(),
                    'observations': [],
                    'synergy_score': 0.5,
                    'topics': []
                }
            
            entity = self.entities[entity_id]
            entity['observations'].append(observation.observation_type)
            entity['last_seen'] = datetime.now().isoformat()
            
            # Update topics — ensure we always have a list of strings, not chars
            raw_topics = observation.data.get('topics', []) or observation.data.get('hashtags', [])
            if isinstance(raw_topics, str):
                raw_topics = [t.strip() for t in raw_topics.split(',') if t.strip()]
            topics = [t for t in raw_topics if isinstance(t, str) and len(t) > 1]
            entity['topics'] = list(set(entity.get('topics', []) + topics))
        
        # Update topic weights — same guard: skip single chars and non-strings
        raw_tw = observation.data.get('topics', []) or observation.data.get('hashtags', [])
        if isinstance(raw_tw, str):
            raw_tw = [t.strip() for t in raw_tw.split(',') if t.strip()]
        for topic in raw_tw:
            if not isinstance(topic, str) or len(topic) <= 1:
                continue
            topic_key = topic.lower().lstrip('#')
            current = self.topics.get(topic_key, 0.0)
            # Boost based on field stability
            boost = 0.1 if vector.synergy_field_status == "Stable" else 0.05
            self.topics[topic_key] = min(1.0, current + boost)
        
        # Update plugin stats
        if observation.source_plugin in self.registered_plugins:
            self.registered_plugins[observation.source_plugin]['observations_count'] += 1
        
        self._save_state()
        
        logger.debug(f"👁️ [{observation.source_plugin}] Observed {observation.observation_type}: "
                    f"field={vector.synergy_field_status}, mass={content_mass:.2e}")
        
        return observation.symod_metrics
    
    def propose_actions(self, 
                       plugin_name: str,
                       context: Dict,
                       available_actions: List[str]) -> List[SyModActionProposal]:
        """
        Get action proposals from SyMod
        
        Any plugin can request action proposals:
        - Social plugins: like, reply, repost, follow, post
        - DeFi plugins: trade, swap, stake
        - System plugins: alert, notify, execute
        
        Args:
            plugin_name: Which plugin is requesting
            context: {'observations': [...], 'constraints': {...}}
            available_actions: List of action types this plugin can take
        
        Returns:
            List of proposals sorted by SyMod confidence
        """
        if not self.enabled:
            logger.warning("⚠️ SyMod not available - no actions proposed")
            return []
        
        if plugin_name not in self.registered_plugins:
            logger.warning(f"⚠️ Plugin {plugin_name} not registered with SyMod")
            return []
        
        proposals = []
        observations = context.get('observations', [])
        constraints = context.get('constraints', {})
        
        for obs in observations:
            # Skip collapsed field observations
            if obs.symod_metrics.get('field_status') == "Collapse":
                continue
            
            for action_type in available_actions:
                # Calculate action-specific confidence
                confidence = self._calculate_action_confidence(
                    action_type, obs, constraints
                )
                
                if confidence >= self.config['confidence_threshold']:
                    proposal = SyModActionProposal(
                        action_type=action_type,
                        target_id=obs.data.get('id'),
                        target_name=obs.data.get('author_name') or obs.data.get('name'),
                        content=obs.data.get('content'),
                        justification=f"{obs.observation_type} with {obs.symod_metrics.get('field_status')} field",
                        confidence=confidence,
                        impedance=obs.symod_metrics.get('logical_impedance', 0),
                        digital_root=obs.symod_metrics.get('digital_root', 0),
                        field_status=obs.symod_metrics.get('field_status', 'unknown'),
                        valid=obs.symod_metrics.get('valid', False),
                        source_plugin=plugin_name,
                        metadata={'observation': obs.data}
                    )
                    proposals.append(proposal)
        
        # Sort by confidence
        proposals.sort(key=lambda p: p.confidence, reverse=True)
        
        # Apply rate limits
        max_actions = min(
            self.config['max_actions_per_cycle'],
            constraints.get('max_actions', 999)
        )
        proposals = proposals[:max_actions]
        
        # Update stats
        self.registered_plugins[plugin_name]['actions_proposed'] += len(proposals)
        
        logger.info(f"🧠 SyMod proposed {len(proposals)} actions for {plugin_name}")
        
        return proposals
    
    def _calculate_action_confidence(self, action_type: str, 
                                     observation: SyModObservation,
                                     constraints: Dict) -> float:
        """Calculate SyMod confidence for a specific action on an observation"""
        base_confidence = observation.symod_metrics.get('sentiment_mass', 0.5)
        field_status = observation.symod_metrics.get('field_status', 'unknown')
        
        # Field status multiplier
        if field_status == "Stable":
            base_confidence *= 1.2
        elif field_status == "Volatile":
            base_confidence *= 0.8
        elif field_status == "Collapse":
            return 0.0  # Never act on collapsed fields
        
        # Action-specific logic
        action_weights = {
            'like': 0.9,      # Low risk, high volume
            'reply': 0.7,     # Medium risk, needs content
            'repost': 0.6,    # Higher risk, amplifies content
            'follow': 0.7,    # Medium risk, long-term commitment
            'post': 0.5,      # Highest risk, original content
            'trade': 0.4,     # Financial risk
            'alert': 0.8      # System action
        }
        
        weight = action_weights.get(action_type, 0.5)
        
        # Entity synergy boost
        entity_id = observation.data.get('author_id')
        if entity_id and entity_id in self.entities:
            entity_score = self.entities[entity_id].get('synergy_score', 0.5)
            base_confidence *= (0.5 + 0.5 * entity_score)
        
        return min(1.0, base_confidence * weight)
    
    def validate_action(self, plugin_name: str, 
                       action: SyModActionProposal) -> Tuple[bool, str]:
        """
        Validate an action through SyMod
        
        Returns (is_valid, reason)
        """
        if not self.enabled:
            return False, "SyMod not available"
        
        # Check golden window if required
        if self.config['require_golden_window']:
            # Would check blockchain block height here
            pass
        
        # Check confidence threshold
        if action.confidence < self.config['confidence_threshold']:
            return False, f"Confidence {action.confidence:.2f} below threshold {self.config['confidence_threshold']}"
        
        # Check field status
        if action.field_status == "Collapse" and self.config['block_on_collapse']:
            return False, "Field status is Collapse - action blocked"
        
        # Check impedance
        if action.impedance > 1e-28:
            return False, f"Impedance too high: {action.impedance:.2e}"
        
        return True, "SyMod validation passed"
    
    def reflect(self, plugin_name: str, 
               proposal: SyModActionProposal,
               outcome: SyModActionOutcome) -> Dict:
        """
        Reflect on an action outcome
        
        Updates SyMod world model based on results.
        Any plugin should call this after executing an action.
        """
        if not self.enabled:
            return {'reflected': False, 'error': 'SyMod not available'}
        
        # Update entity score based on outcome
        entity_id = proposal.target_id
        if entity_id and entity_id in self.entities:
            entity = self.entities[entity_id]
            
            if outcome.success:
                # Boost score on success
                current_score = entity.get('synergy_score', 0.5)
                entity['synergy_score'] = min(1.0, current_score + 0.05)
            else:
                # Penalize on failure
                current_score = entity.get('synergy_score', 0.5)
                entity['synergy_score'] = max(0.0, current_score - 0.1)
        
        # Record action
        self.action_history.append({
            'plugin': plugin_name,
            'action_type': outcome.action_type,
            'success': outcome.success,
            'engagement': outcome.engagement_received,
            'timestamp': outcome.timestamp.isoformat(),
            'symod_confidence': proposal.confidence
        })
        
        # Keep last 1000
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]
        
        # Update plugin stats
        if plugin_name in self.registered_plugins:
            self.registered_plugins[plugin_name]['actions_executed'] += 1
        
        self._save_state()
        
        logger.debug(f"🪞 [{plugin_name}] Reflected on {outcome.action_type}: success={outcome.success}")
        
        return {
            'reflected': True,
            'entity_updated': entity_id in self.entities if entity_id else False
        }
    
    def get_plugin_status(self, plugin_name: str) -> Dict:
        """Get SyMod status for a specific plugin"""
        if plugin_name not in self.registered_plugins:
            return {'registered': False}
        
        stats = self.registered_plugins[plugin_name]
        
        # Get plugin-specific observations from history
        plugin_actions = [a for a in self.action_history if a['plugin'] == plugin_name]
        recent_success = sum(1 for a in plugin_actions[-20:] if a['success'])
        total_recent = len(plugin_actions[-20:])
        
        return {
            'registered': True,
            'stats': stats,
            'recent_success_rate': recent_success / total_recent if total_recent > 0 else 0,
            'symod_enabled': self.enabled,
            'config': self.config
        }
    
    def get_unified_state(self) -> Dict:
        """Get full unified world state across all plugins"""
        return {
            'entities': len(self.entities),
            'topics': len(self.topics),
            'total_actions': len(self.action_history),
            'registered_plugins': list(self.registered_plugins.keys()),
            'symod_enabled': self.enabled,
            'top_topics': sorted(self.topics.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def _load_state(self):
        """Load persisted state"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.entities = data.get('entities', {})
                # Purge single-char garbage topics (caused by string iteration bug)
                raw_topics = data.get('topics', {})
                self.topics = {k: v for k, v in raw_topics.items() if isinstance(k, str) and len(k) > 1}
                self.action_history = data.get('action_history', [])
                self.registered_plugins = data.get('registered_plugins', {})
                
                logger.info(f"✅ Loaded SyMod core state: "
                           f"{len(self.entities)} entities, "
                           f"{len(self.registered_plugins)} plugins")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load SyMod core state: {e}")
    
    def _save_state(self):
        """Persist state"""
        try:
            data = {
                'entities': self.entities,
                'topics': self.topics,
                'action_history': self.action_history,
                'registered_plugins': self.registered_plugins,
                'config': self.config,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"⚠️ Failed to save SyMod core state: {e}")


# Singleton instance
_symod_core_manager: Optional[SyModCoreManager] = None

def get_symod_manager(core=None) -> SyModCoreManager:
    """Get or create SyMod core manager singleton"""
    global _symod_core_manager
    if _symod_core_manager is None:
        _symod_core_manager = SyModCoreManager(core)
    return _symod_core_manager


def reset_symod_manager():
    """Reset SyMod manager (for testing)"""
    global _symod_core_manager
    _symod_core_manager = None
