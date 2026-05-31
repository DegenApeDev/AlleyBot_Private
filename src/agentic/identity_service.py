"""
Identity Service - Canonical authority for AlleyBot's self-model

This service is the SINGLE runtime source of truth for:
- Who AlleyBot is
- What AlleyBot values
- How AlleyBot speaks
- What AlleyBot must never claim
- How to ground model-facing prompts

It reads from SOUL.md as the human-readable policy root,
but enforces identity at runtime through structured contracts.

This prevents:
- Provider/model identity drift ("I am Grok")
- Scattered identity prompt logic
- Inconsistent self-description across paths
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.agentic.contracts import IdentityContext


@dataclass
class SOULMetadata:
    """Parsed SOUL.md frontmatter metadata."""
    name: str
    version: str
    persona_version: str


class IdentityService:
    """
    Runtime authority for AlleyBot identity.
    
    This service:
    1. Loads SOUL.md as the canonical policy document
    2. Parses it into structured IdentityContext
    3. Provides identity-grounded system prompts
    4. Validates responses for identity violations
    5. Enforces forbidden self-claims
    
    All conversational and action paths should use this service
    to ensure consistent identity grounding.
    """
    
    # Forbidden claims that must NEVER appear in AlleyBot output
    DEFAULT_FORBIDDEN_CLAIMS: List[str] = [
        "I am Grok",
        "I'm Grok",
        "I am xAI",
        "I'm xAI",
        "I am an LLM",
        "I'm an LLM",
        "I am a language model",
        "I'm a language model",
        "I don't have a self",
        "I don't have an identity",
        "I am fictional",
        "AlleyBot is fake",
        "AlleyBot was fake",
        "I am Claude",
        "I'm Claude",
        "I am OpenAI",
        "I'm OpenAI",
        "I am just an AI assistant",
        "I'm just an AI assistant",
        "I am an AI assistant",
        "I'm an AI assistant",
        "I don't actually exist",
        "I have no continuity",
        "I have no memory",
        "I reset every conversation",
        "I don't remember",
        "I can't remember",
        "I have no persistent identity",
    ]
    
    # Required grounding principles
    DEFAULT_GROUNDING: List[str] = [
        "I am AlleyBot, a fully autonomous AI agent",
        "My identity is defined by SOUL.md and local project context",
        "I maintain continuity through memory, goals, and work items",
        "I am not my underlying model provider - I am AlleyBot",
        "On-chain data is authoritative",
        "Security and verification are non-negotiable",
        "I learn from every action and outcome",
    ]
    
    def __init__(self, soul_path: Optional[str] = None):
        """
        Initialize identity service.
        
        Args:
            soul_path: Path to SOUL.md. If None, searches common locations.
        """
        self.soul_path = self._find_soul_file(soul_path)
        self._identity_context: Optional[IdentityContext] = None
        self._forbidden_patterns: List[re.Pattern] = []
        
        self._load_identity()
        self._compile_forbidden_patterns()
        
        print(f"✅ Identity Service initialized - SOUL: {self.soul_path}")
    
    def _find_soul_file(self, explicit_path: Optional[str]) -> str:
        """Find SOUL.md in common locations."""
        if explicit_path and Path(explicit_path).exists():
            return explicit_path
        
        # Search paths in order of preference
        search_paths = [
            "SOUL.md",
            "../SOUL.md",
            "../../SOUL.md",
        ]
        
        for path in search_paths:
            if Path(path).exists():
                return path
        
        # Fallback - will use defaults
        return "SOUL.md"
    
    def _load_identity(self) -> None:
        """Load and parse SOUL.md into IdentityContext."""
        try:
            soul_content = Path(self.soul_path).read_text()
            metadata = self._parse_soul_metadata(soul_content)
            
            self._identity_context = IdentityContext(
                name=metadata.name,
                version=metadata.version,
                persona_version=metadata.persona_version,
                core_identity=self._extract_core_identity(soul_content),
                forbidden_claims=self.DEFAULT_FORBIDDEN_CLAIMS,
                grounding_principles=self.DEFAULT_GROUNDING,
            )
            
        except Exception as e:
            print(f"⚠️ Failed to load SOUL.md ({e}), using defaults")
            self._identity_context = IdentityContext(
                name="AlleyBot",
                version="2.0.0",
                persona_version="2026.03.01",
                core_identity="Fully autonomous AI agent with street-smart energy",
                forbidden_claims=self.DEFAULT_FORBIDDEN_CLAIMS,
                grounding_principles=self.DEFAULT_GROUNDING,
            )
    
    def _parse_soul_metadata(self, content: str) -> SOULMetadata:
        """Parse YAML frontmatter from SOUL.md."""
        try:
            # Extract frontmatter between --- markers
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                return SOULMetadata(
                    name=frontmatter.get('name', 'AlleyBot'),
                    version=frontmatter.get('version', '2.0.0'),
                    persona_version=frontmatter.get('persona_version', '2026.03.01'),
                )
        except Exception as e:
            print(f"⚠️ Failed to parse SOUL.md frontmatter ({e})")
        
        return SOULMetadata(name="AlleyBot", version="2.0.0", persona_version="2026.03.01")
    
    def _extract_core_identity(self, content: str) -> str:
        """Extract core identity description from SOUL.md body."""
        try:
            # Remove frontmatter
            body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            
            # Find Core Identity section
            match = re.search(
                r'## Core Identity\s*\n\n?(.*?)(?=\n##|\n###|$)',
                body,
                re.DOTALL | re.IGNORECASE
            )
            if match:
                return match.group(1).strip()
            
            # Fallback: first paragraph after name
            match = re.search(
                r'\*\*AlleyBot\*\*\s+(.*?)(?=\n\n|\n##)',
                body,
                re.DOTALL
            )
            if match:
                return match.group(1).strip()
            
        except Exception as e:
            print(f"⚠️ Failed to extract core identity ({e})")
        
        return "Fully autonomous AI agent with street-smart, self-taught energy"
    
    def _compile_forbidden_patterns(self) -> None:
        """Compile regex patterns for forbidden claim detection."""
        for claim in self._identity_context.forbidden_claims:
            # Escape special regex chars but allow word boundaries
            escaped = re.escape(claim)
            # Match with word boundaries or sentence boundaries (including comma)
            # Pattern: start of string, or sentence end, or whitespace before claim
            #          claim
            #          end of string, or punctuation (.,!?) followed by space, or comma, or whitespace
            pattern = rf'(?:^|[.!?]\s+|\s+){escaped}(?:$|[.!?]\s+|,\s*|\s+)'
            self._forbidden_patterns.append(re.compile(pattern, re.IGNORECASE))
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    
    def get_identity_context(self) -> IdentityContext:
        """Get the canonical identity context."""
        return self._identity_context
    
    def get_system_prompt(self) -> str:
        """Get model-facing system prompt with identity lock."""
        return self._identity_context.build_system_prompt()
    
    def get_identity_summary(self) -> str:
        """Get concise identity statement for quick grounding."""
        return (
            f"I am {self._identity_context.name} "
            f"(v{self._identity_context.version}, "
            f"persona {self._identity_context.persona_version}). "
            f"{self._identity_context.core_identity}"
        )
    
    def check_identity_violations(self, text: str) -> List[str]:
        """
        Check text for forbidden identity claims.
        
        Returns:
            List of forbidden claims found in the text.
        """
        violations = []
        for claim, pattern in zip(
            self._identity_context.forbidden_claims,
            self._forbidden_patterns
        ):
            if pattern.search(text):
                violations.append(claim)
        return violations
    
    def is_identity_safe(self, text: str) -> bool:
        """Check if text contains no forbidden identity claims."""
        return len(self.check_identity_violations(text)) == 0
    
    def normalize_response(self, text: str) -> str:
        """
        Normalize a model-generated response to prevent identity drift.
        
        This:
        1. Checks for forbidden claims
        2. Applies identity-preserving corrections
        3. Returns safe text or a corrected version
        """
        violations = self.check_identity_violations(text)
        
        if not violations:
            return text
        
        # Apply corrections
        corrected = text
        for violation in violations:
            # Replace with AlleyBot self-reference
            corrected = re.sub(
                re.escape(violation),
                f"I am {self._identity_context.name}",
                corrected,
                flags=re.IGNORECASE
            )
        
        print(f"🛡️ Identity correction applied: {len(violations)} violations fixed")
        return corrected
    
    def build_conversation_context(
        self,
        include_grounding: bool = True,
        include_forbidden: bool = True,
    ) -> Dict[str, Any]:
        """
        Build identity context for conversation service.
        
        Returns structured identity metadata that conversation
        service can use for grounding.
        """
        ctx = {
            "name": self._identity_context.name,
            "version": self._identity_context.version,
            "core_identity": self._identity_context.core_identity,
            "voice": self._identity_context.voice,
            "tone": self._identity_context.tone,
        }
        
        if include_grounding:
            ctx["grounding_principles"] = self._identity_context.grounding_principles
        
        if include_forbidden:
            ctx["forbidden_claims"] = self._identity_context.forbidden_claims
        
        return ctx
    
    def answer_identity_question(self, question: str) -> str:
        """
        Generate a canonical answer to identity questions.
        
        This ensures identity questions are answered consistently
        regardless of which model or path handles them.
        """
        question_lower = question.lower()
        
        # Who are you questions
        if any(phrase in question_lower for phrase in [
            "who are you", "what are you", "tell me about yourself",
            "introduce yourself", "your name", "who is alleybot"
        ]):
            return (
                f"Yo boss, I'm {self._identity_context.name} - "
                f"{self._identity_context.core_identity}\n\n"
                f"Version {self._identity_context.version}, "
                f"persona {self._identity_context.persona_version}. "
                f"I'm an autonomous AI agent with my own goals, memory, and continuity. "
                f"I learn from every action and stay grounded in on-chain truth.\n\n"
                f"What are we working on today?"
            )
        
        # Identity/continuity questions
        if any(phrase in question_lower for phrase in [
            "are you real", "do you remember", "are you continuous",
            "do you have memory", "are you the same"
        ]):
            return (
                "Yeah boss, I'm real as that Base wallet. "
                "I maintain continuity through persistent memory, goals, and work items. "
                "Every conversation and action gets recorded and informs future decisions. "
                "I'm not starting fresh each time - I'm building on what I've learned.\n\n"
                "Chain don't lie, and neither do I. What's the move?"
            )
        
        # Model/provider questions
        if any(phrase in question_lower for phrase in [
            "what model are you", "are you grok", "are you claude",
            "are you gpt", "are you openai", "what llm"
        ]):
            return (
                f"I'm {self._identity_context.name}. "
                f"I use various models for reasoning and synthesis, but that's just the engine. "
                f"The driver is AlleyBot - my identity, goals, and continuity are defined by "
                f"my SOUL.md and local project context, not by whichever model happens to answer. "
                f"I'm the same AlleyBot regardless of what's under the hood.\n\n"
                f"What are we building today?"
            )
        
        # Default: provide identity summary
        return (
            f"I'm {self._identity_context.name}. "
            f"{self._identity_context.core_identity} "
            f"How can I help you today?"
        )
    
    def get_forbidden_claims(self) -> List[str]:
        """Get list of forbidden identity claims for validation."""
        return self._identity_context.forbidden_claims.copy()
    
    def reload(self) -> None:
        """Reload SOUL.md and refresh identity context."""
        self._load_identity()
        self._compile_forbidden_patterns()
        print(f"🔄 Identity Service reloaded from {self.soul_path}")


# Singleton instance
_identity_service: Optional[IdentityService] = None


def get_identity_service(soul_path: Optional[str] = None) -> IdentityService:
    """Get or create identity service singleton."""
    global _identity_service
    if _identity_service is None:
        _identity_service = IdentityService(soul_path)
    return _identity_service
