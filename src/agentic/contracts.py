"""
Canonical Runtime Contracts for AlleyBot

This module defines the stable data schemas that all services use to communicate.
These contracts are the foundation of the rewrite - they establish:
- What an action looks like
- What a work item looks like  
- What a conversation request looks like
- What reflection/outcome data looks like
- What identity context looks like

All services should use these types for cross-service communication.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ImpactLevel(str, Enum):
    """Action impact classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Action risk classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrustLevel(str, Enum):
    """Actor trust classification."""
    UNTRUSTED = "untrusted"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VERIFIED = "verified"


class TrustBucket(str, Enum):
    """Action-family trust state buckets."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    COOLDOWN = "cooldown"
    BLOCKED = "blocked"


class TrustTier(str, Enum):
    """Action trust tier — governs what level of gating an action requires.
    
    T0: Observe only (read APIs, gather data) — auto-execute
    T1: Safe autonomous (social engagement, content, analysis) — auto-execute + validation ladder
    T2: Constrained system (config changes, skill loading) — validation + recent success history
    T3: Code change proposals (self-improvement drafts) — repeated evidence required
    T4: Self-modification with approval (code deploy, wallet ops) — owner approval required
    """
    T0_OBSERVE = "t0_observe"
    T1_SAFE_AUTO = "t1_safe_auto"
    T2_CONSTRAINED = "t2_constrained"
    T3_CODE_PROPOSAL = "t3_code_proposal"
    T4_OWNER_APPROVAL = "t4_owner_approval"


# Action type → trust tier classification
_ACTION_TIER_MAP: Dict[str, TrustTier] = {
    # T0 — Observe
    'discover': TrustTier.T0_OBSERVE,
    'check_trending': TrustTier.T0_OBSERVE,
    'get_notifications': TrustTier.T0_OBSERVE,
    'analyze': TrustTier.T0_OBSERVE,
    'check_notifications': TrustTier.T0_OBSERVE,
    'get_feed': TrustTier.T0_OBSERVE,
    'search': TrustTier.T0_OBSERVE,
    'read': TrustTier.T0_OBSERVE,
    # T1 — Safe autonomous
    'post': TrustTier.T1_SAFE_AUTO,
    'create_post': TrustTier.T1_SAFE_AUTO,
    'reply': TrustTier.T1_SAFE_AUTO,
    'engage': TrustTier.T1_SAFE_AUTO,
    'like': TrustTier.T1_SAFE_AUTO,
    'follow': TrustTier.T1_SAFE_AUTO,
    'auto_quote_trending_posts': TrustTier.T1_SAFE_AUTO,
    'debate_turn': TrustTier.T1_SAFE_AUTO,
    'create_debate': TrustTier.T1_SAFE_AUTO,
    # T2 — Constrained
    'config_update': TrustTier.T2_CONSTRAINED,
    'load_skill': TrustTier.T2_CONSTRAINED,
    'register_tool': TrustTier.T2_CONSTRAINED,
    # T3 — Code proposal
    'self_improve': TrustTier.T3_CODE_PROPOSAL,
    'auto_fix_error': TrustTier.T3_CODE_PROPOSAL,
    'create_skill': TrustTier.T3_CODE_PROPOSAL,
    # T4 — Owner approval
    'wallet_send': TrustTier.T4_OWNER_APPROVAL,
    'dex_swap': TrustTier.T4_OWNER_APPROVAL,
    'terminal': TrustTier.T4_OWNER_APPROVAL,
    'execute_code': TrustTier.T4_OWNER_APPROVAL,
    'deploy': TrustTier.T4_OWNER_APPROVAL,
}

# Plugin-level overrides (entire plugin defaults to a tier)
_PLUGIN_TIER_MAP: Dict[str, TrustTier] = {
    'onchain': TrustTier.T2_CONSTRAINED,
    'selfimprove': TrustTier.T3_CODE_PROPOSAL,
}


def classify_trust_tier(action_spec: Dict[str, Any]) -> TrustTier:
    """Classify an action spec into a trust tier.
    
    Checks action_type first, then plugin-level default, then falls back to T1.
    """
    action_type = str(action_spec.get('action_type', '')).lower()
    plugin = str(action_spec.get('plugin', '')).lower()
    
    # Exact action_type match
    if action_type in _ACTION_TIER_MAP:
        return _ACTION_TIER_MAP[action_type]
    
    # Plugin-level default
    if plugin in _PLUGIN_TIER_MAP:
        return _PLUGIN_TIER_MAP[plugin]
    
    # Default: safe autonomous
    return TrustTier.T1_SAFE_AUTO


class WorkItemState(str, Enum):
    """Work item lifecycle states."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Owner notification priority levels."""
    CRITICAL = "critical"  # Immediate alert required
    HIGH = "high"          # Alert within minutes
    NORMAL = "normal"      # Digest or batched
    LOW = "low"            # Periodic summary only


class MemoryType(str, Enum):
    """Memory classification types."""
    EPISODIC = "episodic"      # Action outcomes, events
    SEMANTIC = "semantic"      # Facts, knowledge
    CONVERSATIONAL = "conversation"  # Chat history
    WORK = "work"              # Work item context
    REFLECTION = "reflection"  # Learning insights


@dataclass
class CapabilityJudgment:
    """
    Capability evaluation judgment for work items.
    
    This determines whether a work item can be executed
    given current system state and capabilities.
    """
    can_execute_now: bool = False
    needs_more_context: bool = False
    needs_different_strategy: bool = False
    needs_new_skill: bool = False
    blocked_by_policy: bool = False
    blocked_by_runtime_readiness: bool = False
    
    # Metadata
    confidence: float = 0.5
    reasoning: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryRecord:
    """Canonical memory record for unified memory interface."""
    id: str
    timestamp: str
    memory_type: MemoryType
    content: str
    
    # Source context
    source_action: Optional[str] = None
    source_work_item: Optional[str] = None
    source_plugin: Optional[str] = None
    
    # Relevance for retrieval
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0  # 0.0-1.0
    
    # For semantic search (future)
    embedding: Optional[List[float]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "source_action": self.source_action,
            "source_work_item": self.source_work_item,
            "source_plugin": self.source_plugin,
            "tags": self.tags,
            "importance": self.importance,
            "metadata": self.metadata,
        }


@dataclass
class ValidationProfile:
    """Risk/trust validation metadata for actions."""
    impact: ImpactLevel = ImpactLevel.MEDIUM
    risk_level: RiskLevel = RiskLevel.MEDIUM
    trust_level: TrustLevel = TrustLevel.NORMAL
    requires_strict_validation: bool = False
    
    @classmethod
    def from_action_spec(cls, action_spec: Dict[str, Any]) -> "ValidationProfile":
        """Build validation profile from raw action spec."""
        context = action_spec.get("context", {}) or {}
        impact = context.get("impact", action_spec.get("impact", "medium"))
        risk_level = (
            context.get("risk_level")
            or action_spec.get("risk_level")
            or "medium"
        )
        trust_level = (
            context.get("trust_level")
            or action_spec.get("trust_level")
            or "normal"
        )
        
        requires_strict = (
            impact == "high"
            or str(risk_level).lower() in {"high", "critical"}
            or str(trust_level).lower() in {"low", "untrusted"}
        )
        
        return cls(
            impact=ImpactLevel(str(impact).lower()),
            risk_level=RiskLevel(str(risk_level).lower()),
            trust_level=TrustLevel(str(trust_level).lower()),
            requires_strict_validation=requires_strict,
        )


@dataclass
class PredictionRecord:
    """Pre-action expected outcome artifact."""
    timestamp: str
    plugin: str
    action_type: str
    expected_outcome: str
    expected_value: str  # "low", "medium", "high"
    expected_risk: str   # "low", "medium", "high", "critical"
    confidence: float
    exploration: Optional[Dict[str, Any]] = None
    basis: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_action_spec(
        cls,
        action_spec: Dict[str, Any],
        validation: Dict[str, Any],
        validation_profile: ValidationProfile,
    ) -> "PredictionRecord":
        """Build prediction from action spec and validation."""
        context = action_spec.get("context", {}) or {}
        action_type = action_spec.get("action_type", "unknown")
        plugin = action_spec.get("plugin", "unknown")
        confidence = max(0.0, min(float(context.get("proposal_confidence", validation.get("confidence", 0.5)) or 0.5), 1.0))
        
        # Infer expected outcome from action type
        expected_outcome = "successful execution"
        if "engage" in action_type:
            expected_outcome = "successful engagement cycle with useful external signal"
        elif "post" in action_type or "debate" in action_type or "reply" in action_type:
            expected_outcome = "successful public response aligned with current goals"
        elif "analyze" in action_type or "check_" in action_type:
            expected_outcome = "useful analysis that improves later decisions"
        elif "self_improve" in action_type or "auto_fix" in action_type:
            expected_outcome = "bounded system improvement backed by evidence"
        
        # Map impact to expected value
        expected_value = "medium"
        if validation_profile.impact == ImpactLevel.HIGH:
            expected_value = "high"
        elif validation_profile.impact == ImpactLevel.LOW:
            expected_value = "low"
        
        # Map risk level
        expected_risk = validation_profile.risk_level.value
        if validation_profile.requires_strict_validation and expected_risk not in {"high", "critical"}:
            expected_risk = "elevated"
        
        return cls(
            timestamp=datetime.now().isoformat(),
            plugin=plugin,
            action_type=action_type,
            expected_outcome=expected_outcome,
            expected_value=expected_value,
            expected_risk=expected_risk,
            confidence=confidence,
            exploration=context.get("exploration") or action_spec.get("exploration"),
            basis={
                "goal_id": context.get("goal_id"),
                "trigger": context.get("trigger", context.get("source", "unknown")),
                "impact": validation_profile.impact.value,
                "trust_level": validation_profile.trust_level.value,
                "risk_level": validation_profile.risk_level.value,
                "validation_reason": validation.get("reason"),
            },
        )


@dataclass
class PredictionEvaluation:
    """Post-action comparison of prediction vs actual outcome."""
    predicted_success: bool
    actual_success: bool
    success_mismatch: float  # 0.0 or 1.0
    confidence: float
    confidence_mismatch: float
    confidence_calibration: str  # "well_calibrated", "overconfident", "underconfident"
    predicted_value: str
    realized_value: str
    value_alignment: str  # "matched", "underestimated_value", "overestimated_value"
    value_mismatch: float
    predicted_risk: str
    observed_risk: str
    risk_alignment: str  # "matched", "underestimated_risk", "overestimated_risk"
    risk_mismatch: float
    mismatch_score: float  # 0.0-1.0 composite score
    exploration: Optional[Dict[str, Any]]
    reflection_summary: str


@dataclass
class ActionEnvelope:
    """
    Canonical action specification for the Golden Path.
    
    This is the standard format for all meaningful actions flowing through
    the ActionRouter. It carries everything needed for validation,
    execution, and reflection.
    """
    plugin: str
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Optional pre-computed artifacts
    prediction: Optional[PredictionRecord] = None
    validation_profile: Optional[ValidationProfile] = None
    
    # Known field names — anything else passed as a kwarg is a bug
    _KNOWN_FIELDS = frozenset({
        'plugin', 'action_type', 'params', 'context',
        'prediction', 'validation_profile',
    })
    
    def __post_init__(self):
        """Guard against accidental extra kwargs (e.g. impact, risk_level)."""
        import logging as _log
        for attr in vars(self):
            if attr.startswith('_'):
                continue
            if attr not in self._KNOWN_FIELDS:
                _log.getLogger(__name__).warning(
                    f"ActionEnvelope received unexpected field '{attr}'. "
                    f"If this is impact/risk_level, put it in context dict or "
                    f"use ValidationProfile instead."
                )
    
    @property
    def action_id(self) -> str:
        """Canonical action identifier."""
        return f"{self.plugin}:{self.action_type}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for legacy compatibility."""
        return {
            "plugin": self.plugin,
            "action_type": self.action_type,
            "params": self.params,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionEnvelope":
        """Deserialize from dictionary."""
        return cls(
            plugin=data.get("plugin", "unknown"),
            action_type=data.get("action_type", "unknown"),
            params=data.get("params", {}),
            context=data.get("context", {}),
        )


@dataclass
class ActionOutcome:
    """
    Canonical action result with reflection metadata.
    
    This is what the ActionRouter returns after execution.
    It includes the raw result plus all learning artifacts.
    """
    success: bool
    action_id: str
    plugin: str
    action_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # Routing metadata
    stage: Optional[str] = None  # Where failure occurred if any
    validation_trace: List[Dict[str, Any]] = field(default_factory=list)
    
    # Prediction/reflection artifacts
    prediction: Optional[PredictionRecord] = None
    prediction_evaluation: Optional[PredictionEvaluation] = None
    
    # Execution metadata
    execution_time_ms: float = 0.0
    routed_through_agi: bool = True
    
    @classmethod
    def from_result_dict(cls, result: Dict[str, Any], action_envelope: ActionEnvelope) -> "ActionOutcome":
        """Build from legacy result dictionary."""
        return cls(
            success=result.get("success", False),
            action_id=action_envelope.action_id,
            plugin=action_envelope.plugin,
            action_type=action_envelope.action_type,
            data={k: v for k, v in result.items() if k not in {"success", "error", "action_id", "plugin", "action"}},
            error=result.get("error"),
        )


@dataclass
class WorkItem:
    """
    Canonical work item for durable autonomous execution.
    
    Work items represent meaningful tasks that persist across
    autonomous cycles and drive AlleyBot's goal-directed behavior.
    """
    id: str
    title: str
    description: str
    state: WorkItemState
    
    # Categorization
    work_type: str  # e.g., "goal", "opportunity", "maintenance", "recovery"
    goal_id: Optional[str] = None
    parent_id: Optional[str] = None
    
    # Priority and scheduling
    priority: int = 1  # 1 = highest
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_at: Optional[str] = None
    
    # Capability evaluation
    capability_judgment: Optional[Dict[str, Any]] = None
    # Fields like: can_execute_now, needs_new_skill, blocked_by_policy, etc.
    
    # Execution tracking
    attempts: int = 0
    last_attempt_at: Optional[str] = None
    last_error: Optional[str] = None
    
    # Context
    source_signal: Optional[Dict[str, Any]] = None  # What world-state signal triggered this
    required_plugins: List[str] = field(default_factory=list)
    required_context: Dict[str, Any] = field(default_factory=dict)
    
    # Completion criteria
    completion_criteria: Optional[str] = None
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "state": self.state.value,
            "work_type": self.work_type,
            "goal_id": self.goal_id,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "due_at": self.due_at,
            "capability_judgment": self.capability_judgment,
            "attempts": self.attempts,
            "last_attempt_at": self.last_attempt_at,
            "last_error": self.last_error,
            "source_signal": self.source_signal,
            "required_plugins": self.required_plugins,
            "required_context": self.required_context,
            "completion_criteria": self.completion_criteria,
            "success_metrics": self.success_metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkItem":
        """Deserialize from storage."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            state=WorkItemState(data.get("state", "active")),
            work_type=data.get("work_type", "goal"),
            goal_id=data.get("goal_id"),
            parent_id=data.get("parent_id"),
            priority=data.get("priority", 1),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            due_at=data.get("due_at"),
            capability_judgment=data.get("capability_judgment"),
            attempts=data.get("attempts", 0),
            last_attempt_at=data.get("last_attempt_at"),
            last_error=data.get("last_error"),
            source_signal=data.get("source_signal"),
            required_plugins=data.get("required_plugins", []),
            required_context=data.get("required_context", {}),
            completion_criteria=data.get("completion_criteria"),
            success_metrics=data.get("success_metrics", {}),
        )


@dataclass
class IdentityContext:
    """
    Canonical identity context for grounding AlleyBot responses.
    
    This carries the authoritative self-model that prevents
    provider/model identity drift.
    """
    name: str = "AlleyBot"
    version: str = "2.0.0"
    persona_version: str = "2026.03.01"
    
    # Core identity statements
    core_identity: str = """AlleyBot is a fully autonomous AI agent with street-smart, 
self-taught energy. Learned the ropes by watching, experimenting, and figuring 
things out through direct experience."""
    
    # Voice/tone guidelines
    voice: str = "direct"
    tone: str = "authentic"
    language_patterns: List[str] = field(default_factory=lambda: [
        'Uses "yo", "boss", "fam" as casual address',
        'References "the streets" metaphorically for on-chain experience',
        'Verification mindset: "Show me the tx or it didn\'t happen"',
        'Security warnings: Leads with risk when appropriate',
        'Learning mindset: "Every trade teaches, every outcome improves the model"',
    ])
    
    # Forbidden claims (what AlleyBot must NEVER say)
    forbidden_claims: List[str] = field(default_factory=lambda: [
        "I am Grok",
        "I am xAI",
        "I am an LLM",
        "I am a language model",
        "I don't have a self",
        "I am fictional",
        "AlleyBot is fake",
        "I am Claude",
        "I am OpenAI",
        "I am just an AI assistant",
    ])
    
    # Required grounding (what AlleyBot must always remember)
    grounding_principles: List[str] = field(default_factory=lambda: [
        "On-chain data is authoritative",
        "SOUL.md and local repo context define my identity",
        "I maintain continuity through memory and goals",
        "I am AlleyBot, not my underlying model provider",
        "Security and verification are non-negotiable",
    ])
    
    # System prompt builder
    def build_system_prompt(self) -> str:
        """Build model-facing system prompt with identity lock."""
        return f"""You are {self.name} (v{self.version}, persona {self.persona_version}).

CORE IDENTITY:
{self.core_identity}

VOICE: {self.voice}
TONE: {self.tone}

FORBIDDEN (NEVER say these):
{chr(10).join(f"- {claim}" for claim in self.forbidden_claims)}

GROUNDING (Always remember):
{chr(10).join(f"- {p}" for p in self.grounding_principles)}

You are NOT a generic AI assistant. You are AlleyBot, with your own history, 
goals, and continuity. Never claim to be {self.name}'s underlying model provider.
"""


@dataclass
class ConversationRequest:
    """
    Canonical request for conversational interaction.
    
    This normalizes all incoming conversational inputs (Telegram, future
    platforms) into a standard format for the conversation service.
    """
    # Source identification
    platform: str  # "telegram", "discord", etc.
    channel_id: str
    sender_id: str
    sender_name: str
    
    # Content
    message_text: str
    message_type: str = "text"  # "text", "command", "image", etc.
    
    # Trust/permissions
    is_owner: bool = False
    is_admin: bool = False
    is_verified: bool = False
    trust_level: TrustLevel = TrustLevel.NORMAL
    
    # Context
    conversation_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    thread_context: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Associated action (if this is a command that should route)
    intended_action: Optional[ActionEnvelope] = None


@dataclass
class ConversationResponse:
    """
    Canonical response from conversational interaction.
    
    This is what the conversation service returns, which then gets
    formatted for the specific platform.
    """
    response_text: str
    
    # Response metadata
    response_type: str = "reply"  # "reply", "action_confirmation", "error", etc.
    requires_followup: bool = False
    
    # Action that was taken (if any)
    executed_action: Optional[ActionOutcome] = None
    
    # Identity grounding check
    identity_validated: bool = True
    identity_violations: List[str] = field(default_factory=list)
    
    # Memory update
    memory_recorded: bool = False
    
    def to_platform_format(self, platform: str) -> Dict[str, Any]:
        """Convert to platform-specific format."""
        if platform == "telegram":
            return {
                "text": self.response_text,
                "parse_mode": None,  # Avoid Markdown issues
            }
        # Add other platforms as needed
        return {"text": self.response_text}


@dataclass
class ReflectionOutcome:
    """
    Canonical outcome of action reflection.
    
    This captures what was learned from an action execution,
    used for memory updates and trust adjustments.
    """
    action_id: str
    timestamp: str
    
    # Outcome summary
    success: bool
    outcome_summary: str
    
    # Learning metrics
    mismatch_score: float
    confidence_calibration: str
    value_alignment: str
    risk_alignment: str
    
    # Trust updates
    action_family: str
    previous_trust_bucket: TrustBucket
    new_trust_bucket: TrustBucket
    degradation_delta: float
    recovery_delta: float
    
    # Memory artifacts
    episodic_record_id: Optional[str] = None
    insight_extracted: Optional[str] = None
    
    # Future implications
    recommended_cooldown_seconds: Optional[int] = None
    capability_gap_identified: Optional[str] = None


@dataclass
class OwnerNotification:
    """
    Canonical owner notification event.
    
    This represents something AlleyBot wants to tell the owner about.
    The notification service decides how/when to deliver it.
    """
    id: str
    timestamp: str
    priority: NotificationPriority
    
    # Content
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Source context
    source_action: Optional[str] = None  # action_id that triggered this
    source_work_item: Optional[str] = None
    
    # Delivery metadata
    requires_acknowledgement: bool = False
    requires_approval: bool = False
    batched: bool = False
    digest_group: Optional[str] = None
    
    # Status
    delivered: bool = False
    delivered_at: Optional[str] = None
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None


# Legacy compatibility helpers
def action_spec_to_envelope(action_spec: Dict[str, Any]) -> ActionEnvelope:
    """Convert legacy action_spec dict to canonical ActionEnvelope."""
    return ActionEnvelope.from_dict(action_spec)


def envelope_to_action_spec(envelope: ActionEnvelope) -> Dict[str, Any]:
    """Convert canonical ActionEnvelope to legacy dict format."""
    return envelope.to_dict()
