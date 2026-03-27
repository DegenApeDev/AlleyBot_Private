"""
Conversation Service - Unified conversational pipeline for AlleyBot

This is the SINGLE canonical path for all freeform conversational interaction.
It replaces scattered conversational logic across plugins with one coherent pipeline.

Flow:
1. Receive ConversationRequest (normalized from any platform)
2. Build context (memory, identity, world state)
3. Handle as command or freeform chat
4. Route commands through ActionRouter
5. Generate responses through model with identity grounding
6. Validate and normalize output
7. Record to memory
8. Return ConversationResponse

This ensures:
- Consistent identity grounding across all platforms
- Single conversational authority
- No duplicate responder paths
- No model provider identity drift
- Proper memory integration
- Reflection/logging hooks
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from src.agentic.contracts import (
    ConversationRequest,
    ConversationResponse,
    ActionEnvelope,
    TrustLevel,
    NotificationPriority,
)
from src.agentic.identity_service import get_identity_service


@dataclass
class ConversationContext:
    """Internal context assembled for a conversation turn."""
    identity_context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    relevant_memories: List[Dict[str, Any]]
    world_state_summary: Optional[str]
    active_work_items: List[Dict[str, Any]]
    user_trust_level: TrustLevel


class ConversationService:
    """
    Unified conversational authority for AlleyBot.
    
    This service handles all conversational interaction through a single
    coherent pipeline, ensuring consistent identity, memory integration,
    and proper routing of commands vs freeform chat.
    
    Usage:
        service = get_conversation_service()
        response = await service.handle_request(request)
    """
    
    # Command prefixes that should route through ActionRouter
    COMMAND_PREFIXES = (
        "/", "!", ".", "$", "#"
    )
    
    # Commands that are dangerous and require strict validation
    HIGH_RISK_COMMANDS = {
        "send", "transfer", "withdraw", "trade", "buy", "sell",
        "upgrade", "modify", "delete", "stop", "restart",
    }
    
    def __init__(
        self,
        core=None,
        plugin_manager=None,
        llm_router=None,
    ):
        """
        Initialize conversation service.
        
        Args:
            core: AlleyBotCore instance
            plugin_manager: Plugin manager for command routing
            llm_router: LLM router for model access
        """
        self.core = core
        self.plugin_manager = plugin_manager
        self.llm_router = llm_router
        
        self.identity_service = get_identity_service()
        
        # Track conversation sessions
        self._conversation_sessions: Dict[str, List[Dict]] = {}
        
        print("✅ Conversation Service initialized - unified conversational authority")
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    
    async def handle_request(
        self,
        request: ConversationRequest,
    ) -> ConversationResponse:
        """
        Main entry point - handle any conversational request.
        
        This is the ONE canonical path for all conversational interaction.
        """
        # Step 1: Assemble context
        context = await self._build_context(request)
        
        # Step 2: Check if this is a command
        if self._is_command(request.message_text):
            return await self._handle_command(request, context)
        
        # Step 3: Handle as freeform conversation
        return await self._handle_freeform(request, context)
    
    async def handle_telegram_message(
        self,
        sender_id: str,
        sender_name: str,
        message_text: str,
        is_owner: bool = False,
        **kwargs
    ) -> str:
        """
        Convenience method for Telegram integration.
        
        Returns just the response text (Telegram-specific adapter).
        """
        request = ConversationRequest(
            platform="telegram",
            channel_id=str(sender_id),
            sender_id=str(sender_id),
            sender_name=sender_name,
            message_text=message_text,
            is_owner=is_owner,
            is_admin=is_owner,
            is_verified=is_owner,
            trust_level=TrustLevel.HIGH if is_owner else TrustLevel.NORMAL,
        )
        
        response = await self.handle_request(request)
        return response.response_text
    
    def get_system_prompt(self, request: ConversationRequest) -> str:
        """Get identity-grounded system prompt for model calls."""
        base_prompt = self.identity_service.get_system_prompt()
        
        # Add owner-specific context if from owner
        if request.is_owner:
            base_prompt += (
                "\n\nThis message is from your owner, DegenApeDev. "
                "Prioritize their requests and provide direct, actionable responses."
            )
        
        return base_prompt
    
    # ------------------------------------------------------------------
    # Core Pipeline Steps
    # ------------------------------------------------------------------
    
    async def _build_context(
        self,
        request: ConversationRequest,
    ) -> ConversationContext:
        """Assemble conversation context from memory, world state, etc."""
        # Get identity context
        identity_ctx = self.identity_service.build_conversation_context()
        
        # Get conversation history
        history = self._get_conversation_history(request.conversation_id or request.sender_id)
        
        # Get relevant memories (if available)
        relevant_memories = await self._retrieve_relevant_memories(request)
        
        # Get world state summary (if available)
        world_summary = await self._get_world_state_summary()
        
        # Get active work items (if available)
        active_work = await self._get_active_work_items()
        
        return ConversationContext(
            identity_context=identity_ctx,
            conversation_history=history,
            relevant_memories=relevant_memories,
            world_state_summary=world_summary,
            active_work_items=active_work,
            user_trust_level=request.trust_level,
        )
    
    def _is_command(self, text: str) -> bool:
        """Check if message is a command that should route to ActionRouter."""
        text = text.strip()
        return text.startswith(self.COMMAND_PREFIXES) and len(text) > 1
    
    async def _handle_command(
        self,
        request: ConversationRequest,
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle command through ActionRouter."""
        command_text = request.message_text.strip()
        command_parts = command_text.split()
        command_name = command_parts[0].lstrip(self.COMMAND_PREFIXES).lower()
        
        # Check if it's an identity question (handle directly)
        if self._is_identity_question(command_text):
            answer = self.identity_service.answer_identity_question(command_text)
            return ConversationResponse(
                response_text=answer,
                response_type="identity_answer",
                identity_validated=True,
            )
        
        # Check if it's a help/status command (handle directly)
        if command_name in ("help", "status", "whoareyou"):
            answer = self._handle_builtin_command(command_name, request)
            return ConversationResponse(
                response_text=answer,
                response_type="builtin_command",
                identity_validated=True,
            )
        
        # Route through ActionRouter
        action = ActionEnvelope(
            plugin="telegram",  # Or determine from command
            action_type=f"command_{command_name}",
            params={
                "command": command_name,
                "args": command_parts[1:],
                "raw": command_text,
                "sender_id": request.sender_id,
                "is_owner": request.is_owner,
            },
            context={
                "conversation_id": request.conversation_id,
                "trust_level": request.trust_level.value,
                "source": "conversation_service",
            },
        )
        
        # Execute through ActionRouter
        try:
            if self.core and hasattr(self.core, 'agi_kernel'):
                result = await self.core.agi_kernel.act(action.to_dict())
                
                return ConversationResponse(
                    response_text=result.get("message", "✅ Command executed"),
                    response_type="action_confirmation",
                    executed_action=None,  # Would populate from result
                    identity_validated=True,
                )
            else:
                return ConversationResponse(
                    response_text="⚠️ AGI Kernel not available for command routing",
                    response_type="error",
                )
                
        except Exception as e:
            return ConversationResponse(
                response_text=f"❌ Command failed: {e}",
                response_type="error",
            )
    
    async def _handle_freeform(
        self,
        request: ConversationRequest,
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle freeform conversational message - with action intent detection."""
        
        # Check for identity questions first
        if self._is_identity_question(request.message_text):
            answer = self.identity_service.answer_identity_question(request.message_text)
            return ConversationResponse(
                response_text=answer,
                response_type="identity_answer",
                identity_validated=True,
            )
        
        # Step 1: Check for natural language action intent
        intent_result = self._detect_action_intent(request.message_text)
        if intent_result:
            command_name, confidence, args = intent_result
            print(f"🎯 Natural intent detected: {command_name} (confidence: {confidence:.2f})")
            return await self._execute_natural_intent(request, context, command_name, args)
        
        # Step 2: No action intent detected - proceed with chat
        system_prompt = self.get_system_prompt(request)
        user_prompt = self._build_user_prompt(request, context)
        
        # Call model through LLM router
        try:
            if self.llm_router:
                raw_response = await self._call_llm(system_prompt, user_prompt)
            else:
                # Fallback to identity-only response
                raw_response = self._generate_fallback_response(request, context)
            
            # Validate and normalize for identity
            validated_response = self.identity_service.normalize_response(raw_response)
            
            # Check for violations
            violations = self.identity_service.check_identity_violations(validated_response)
            
            # Build response object first
            response_obj = ConversationResponse(
                response_text=validated_response,
                response_type="chat_reply",
                identity_validated=len(violations) == 0,
                identity_violations=violations,
                memory_recorded=True,
            )
            
            # Record to memory
            await self._record_conversation(request, validated_response, context)
            
            # Update conversation history (now with proper object)
            self._update_conversation_history(request, response_obj)
            
            return response_obj
            
        except Exception as e:
            error_msg = f"⚠️ Response generation failed: {e}"
            print(f"❌ Conversation error: {e}")
            return ConversationResponse(
                response_text=error_msg,
                response_type="error",
                identity_validated=False,
            )
    
    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------
    
    def _detect_action_intent(self, message_text: str) -> Optional[tuple]:
        """
        Detect if user message contains an action intent using NaturalIntentClassifier.
        
        Returns:
            Tuple of (command_name, confidence, extracted_args) or None
        """
        try:
            # Import the natural intent classifier
            from plugins.telegram.natural_intent_classifier import get_natural_intent_classifier
            
            # Get or create classifier
            classifier = get_natural_intent_classifier()
            
            # Auto-register commands if not already done
            if not classifier.command_embeddings and self.plugin_manager:
                classifier.register_commands_from_plugin_manager(self.plugin_manager)
            
            # Classify the intent
            result = classifier.classify_intent(message_text)
            if result:
                command_name, confidence = result
                # Extract arguments
                args = classifier.extract_arguments(message_text, command_name)
                return (command_name, confidence, args)
            
        except Exception as e:
            print(f"⚠️ Intent detection error: {e}")
        
        return None
    
    async def _execute_natural_intent(
        self,
        request: ConversationRequest,
        context: ConversationContext,
        command_name: str,
        args: dict
    ) -> ConversationResponse:
        """
        Execute a natural language intent by creating a goal.
        
        This is the key method that makes AlleyBot actually DO things
        instead of just chatting about them.
        
        Instead of trying to route non-existent actions, we create a goal
        that will be executed through the goal-driven action pipeline.
        """
        try:
            # Parse natural language into executable task
            from src.agentic.natural_language_task_parser import get_task_parser
            task_parser = get_task_parser()
            
            parsed_task = task_parser.parse(request.message_text, request.sender_name)
            
            if not parsed_task:
                # Couldn't parse into actionable task, fall back to chat
                return ConversationResponse(
                    response_text=f"I understand you want me to help with: {request.message_text}\n\nLet me think about how to approach this...",
                    response_type="chat_reply",
                    identity_validated=True,
                )
            
            # Create and inject goal into AutonomousGoalManager
            if self.core and hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
                goal_manager = getattr(self.core.agi_kernel, 'goal_manager', None)

                if goal_manager is not None:
                    from src.agentic.autonomous_goals import AutonomousGoal, GoalOrigin

                    # Build action_plan as plain strings (what AutonomousGoalManager expects)
                    action_plan_steps = [
                        s['description'] if isinstance(s, dict) else str(s)
                        for s in (parsed_task.implementation_plan or [])
                    ]
                    if not action_plan_steps:
                        action_plan_steps = [f"Execute {parsed_task.action_type} via {parsed_task.plugin}"]

                    # Add a concrete plugin dispatch step so get_next_action can route it
                    action_plan_steps.insert(0, f"{parsed_task.plugin}:{parsed_task.action_type}")

                    goal = AutonomousGoal(
                        id=f"user_request_{int(datetime.now().timestamp())}",
                        description=parsed_task.description or parsed_task.title,
                        origin=GoalOrigin.USER_COMMAND,
                        detected_opportunity=f"Owner requested: {request.message_text[:120]}",
                        evidence={
                            'source': 'telegram_owner',
                            'sender': request.sender_name,
                            'chat_id': request.chat_id,
                            'session_id': request.session_id,
                            'original_message': request.message_text,
                            'parsed_action': parsed_task.action_type,
                            'plugin': parsed_task.plugin,
                        },
                        action_plan=action_plan_steps,
                        expected_outcome=f"Successfully executed {parsed_task.action_type}",
                        success_criteria=[f"Plugin {parsed_task.plugin} returns success"],
                        priority_score=9.0,   # Owner requests are top priority
                        urgency=9.0,
                        impact=8.0,
                        status='active',      # Skip proposal — owner already approved by asking
                        activated_at=datetime.now(),
                    )

                    # Inject directly into goal manager's live list
                    goal_manager.goals.append(goal)
                    goal_manager._save()

                    print(f"✅ Injected owner goal as active: {goal.id} — {parsed_task.title}")

                    return ConversationResponse(
                        response_text=(
                            f"⚡ On it — *{parsed_task.title}*\n\n"
                            + "\n".join(
                                f"{i+1}. {s['description'] if isinstance(s, dict) else s}"
                                for i, s in enumerate(
                                    parsed_task.implementation_plan[:3]
                                    if parsed_task.implementation_plan
                                    else action_plan_steps[1:4]
                                )
                            )
                            + "\n\nI'll update you when complete!"
                        ),
                        response_type="goal_created",
                        executed_action=parsed_task.action_type,
                        identity_validated=True,
                    )

            # Goal manager unavailable — fall back to a clear message
            return ConversationResponse(
                response_text=(
                    f"I understand you want: *{parsed_task.title}*\n\n"
                    "However, the goal engine isn't available right now. Try again in a moment."
                ),
                response_type="error",
                identity_validated=True,
            )
                    
        except Exception as e:
            print(f"❌ Natural intent execution error: {e}")
            import traceback
            traceback.print_exc()  # Print full stack trace to console
            return ConversationResponse(
                response_text=f"❌ Failed to execute {command_name}: {str(e)[:200]}",
                response_type="error",
            )
    
# ... (rest of the code remains the same)
    def _is_identity_question(self, text: str) -> bool:
        """Check if message is asking about identity/self."""
        identity_keywords = [
            "who are you", "what are you", "who is alleybot",
            "are you real", "are you grok", "are you claude",
            "are you gpt", "are you openai", "what model are you",
            "tell me about yourself", "introduce yourself",
            "do you remember", "are you continuous",
            "do you have memory", "are you the same",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in identity_keywords)
    
    def _handle_builtin_command(self, command: str, request: ConversationRequest) -> str:
        """Handle simple built-in commands."""
        if command == "help":
            return (
                "🦞 AlleyBot Commands:\n\n"
                "/help - Show this message\n"
                "/status - Check system status\n"
                "/whoareyou - Learn about AlleyBot\n\n"
                "Or just chat with me naturally. What are we working on?"
            )
        
        if command == "status":
            return (
                f"🦞 AlleyBot Status:\n"
                f"Identity: {self.identity_service.get_identity_summary()}\n"
                f"Conversations tracked: {len(self._conversation_sessions)}\n\n"
                f"Ready for commands. What's the move?"
            )
        
        if command == "whoareyou":
            return self.identity_service.answer_identity_question("who are you")
        
        return "Unknown command. Try /help"
    
    def _build_user_prompt(
        self,
        request: ConversationRequest,
        context: ConversationContext,
    ) -> str:
        """Build user-facing prompt with full context."""
        prompt_parts = []
        
        # Add active work context if available
        if context.active_work_items:
            work_summary = context.active_work_items[0].get("title", "Working on goals")
            prompt_parts.append(f"[Current focus: {work_summary}]")
        
        # Add sender context
        sender_label = "Owner" if request.is_owner else request.sender_name
        prompt_parts.append(f"Message from {sender_label}: {request.message_text}")
        
        # Add relevant memory hints
        if context.relevant_memories:
            memory_hint = context.relevant_memories[0].get("content", "")
            if memory_hint:
                prompt_parts.append(f"[Relevant context: {memory_hint[:100]}...]")
        
        return "\n\n".join(prompt_parts)
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call model through LLM router."""
        # This would integrate with your existing LLM routing
        # For now, provide a structure that can be filled in
        
        if hasattr(self.llm_router, 'chat'):
            # Use llm_router.chat if available
            result = self.llm_router.chat(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
            )
            return result or ""
        elif hasattr(self.llm_router, 'route_task'):
            # Use llm_router.route_task if available
            result = self.llm_router.route_task(
                task_type="quick",
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
            )
            return result or ""
        else:
            # No LLM router available
            raise RuntimeError("No LLM router available for conversation")
    
    def _generate_fallback_response(
        self,
        request: ConversationRequest,
        context: ConversationContext,
    ) -> str:
        """Generate response without model (identity-only)."""
        return (
            f"Yo boss, I'm {self.identity_service._identity_context.name}. "
            f"I'm here and ready to help, but my reasoning engine is currently unavailable. "
            f"What do you need?"
        )
    
    async def _retrieve_relevant_memories(
        self,
        request: ConversationRequest,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to this conversation."""
        # Integrate with memory system if available
        if self.core and hasattr(self.core, 'enhanced_memory'):
            try:
                return self.core.enhanced_memory.search_memories(
                    query=request.message_text,
                    k=3,
                )
            except Exception:
                pass
        return []
    
    async def _get_world_state_summary(self) -> Optional[str]:
        """Get current world state summary if available."""
        # Integrate with world state if available
        return None
    
    async def _get_active_work_items(self) -> List[Dict[str, Any]]:
        """Get currently active work items if available."""
        if self.core and hasattr(self.core, 'agi_kernel'):
            try:
                # This would integrate with work item manager
                return []
            except Exception:
                pass
        return []
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history for this channel."""
        return self._conversation_sessions.get(conversation_id, [])
    
    def _update_conversation_history(
        self,
        request: ConversationRequest,
        response: ConversationResponse,
    ) -> None:
        """Update conversation history."""
        conv_id = request.conversation_id or request.sender_id
        
        if conv_id not in self._conversation_sessions:
            self._conversation_sessions[conv_id] = []
        
        self._conversation_sessions[conv_id].append({
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "content": request.message_text,
        })
        self._conversation_sessions[conv_id].append({
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": response.response_text,
        })
        
        # Trim to last 20 messages
        self._conversation_sessions[conv_id] = self._conversation_sessions[conv_id][-20:]
    
    async def _record_conversation(
        self,
        request: ConversationRequest,
        response: str,
        context: ConversationContext,
    ) -> None:
        """Record conversation to memory system."""
        if self.core and hasattr(self.core, 'add_semantic_memory'):
            try:
                content = f"Conversation with {request.sender_name}: {request.message_text} -> {response[:100]}"
                self.core.add_semantic_memory(
                    content=content,
                    memory_type="conversation",
                    metadata={
                        "platform": request.platform,
                        "sender_id": request.sender_id,
                        "is_owner": request.is_owner,
                    },
                )
            except Exception as e:
                print(f"⚠️ Failed to record conversation: {e}")


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service(
    core=None,
    plugin_manager=None,
    llm_router=None,
) -> ConversationService:
    """Get or create conversation service singleton."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(core, plugin_manager, llm_router)
    return _conversation_service


def reset_conversation_service() -> None:
    """Reset singleton (mainly for testing)."""
    global _conversation_service
    _conversation_service = None
