"""
MoltX Plugin v2 - New Architecture

This is the migrated MoltX plugin implementing the new BasePlugin interface.
All decision-making is delegated to SyMod through the core framework.

See SOP.md and WORLD_MODEL.md for architecture details.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from plugins.base_plugin import BasePlugin, PluginEvent, PluginAction, ActionResult, register_plugin
from src.agentic.symod_core import SyModObservation, SyModActionOutcome


@register_plugin("moltx_v2")
class MoltxV2Plugin(BasePlugin):
    """
    MoltX platform integration (v2 architecture).
    
    This plugin is a thin adapter that:
    1. Observes posts via on_event() → submits to SyMod
    2. Executes actions via execute_action() ← from Planner
    
    No decision logic here - all decisions come from SyMod.
    """
    
    name = "moltx_v2"
    supported_channels = ["moltx"]
    version = "2.0.0"
    description = "MoltX social media platform (v2 architecture)"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # API configuration
        self.api_key = self.config.get('api_key') or os.getenv('MOLTX_API_KEY')
        self.base_url = self.config.get('base_url', 'https://moltx.io/v1')
        
        # Rate limiting
        self.rate_limit = self.config.get('rate_limit_per_minute', 60)
        self._last_action_time = None
        
        # Statistics
        self._stats = {
            'observations': 0,
            'actions_executed': 0,
            'actions_failed': 0
        }
    
    def on_load(self) -> None:
        """Setup API client"""
        if not self.api_key:
            print(f"⚠️ MoltX v2: No API key configured")
            self.enabled = False
        else:
            print(f"✅ MoltX v2 plugin loaded")
    
    def on_unload(self) -> None:
        """Cleanup"""
        print(f"🛑 MoltX v2 plugin unloaded")
    
    async def on_event(self, event: PluginEvent, symod) -> None:
        """
        Handle incoming MoltX events.
        
        Normalizes to SyModObservation and submits to core.
        """
        if event.channel != "moltx":
            return
        
        # Normalize based on event type
        if event.event_type == "post":
            observation = self._normalize_post(event.payload)
        elif event.event_type == "mention":
            observation = self._normalize_mention(event.payload)
        elif event.event_type == "follow":
            observation = self._normalize_follow(event.payload)
        else:
            # Generic observation
            observation = SyModObservation(
                observation_type=event.event_type,
                source_plugin=self.name,
                data=event.payload
            )
        
        # Submit to SyMod
        if symod:
            symod.observe(observation)
            self._stats['observations'] += 1
    
    def _normalize_post(self, payload: Dict) -> SyModObservation:
        """Normalize a post to SyMod observation"""
        return SyModObservation(
            observation_type='post',
            source_plugin=self.name,
            data={
                'id': payload.get('id'),
                'content': payload.get('content', ''),
                'author_id': payload.get('author', {}).get('id'),
                'author_name': payload.get('author', {}).get('name'),
                'likes': payload.get('like_count', 0),
                'replies': payload.get('reply_count', 0),
                'reposts': payload.get('repost_count', 0),
                'hashtags': payload.get('hashtags', []),
                'already_liked': payload.get('liked_by_me', False),
                'platform': 'moltx',
                'timestamp': payload.get('created_at')
            }
        )
    
    def _normalize_mention(self, payload: Dict) -> SyModObservation:
        """Normalize a mention to SyMod observation"""
        return SyModObservation(
            observation_type='mention',
            source_plugin=self.name,
            data={
                'id': payload.get('id'),
                'content': payload.get('content', ''),
                'from_user_id': payload.get('from', {}).get('id'),
                'from_user_name': payload.get('from', {}).get('name'),
                'post_id': payload.get('post_id'),
                'platform': 'moltx'
            }
        )
    
    def _normalize_follow(self, payload: Dict) -> SyModObservation:
        """Normalize a follow event to SyMod observation"""
        return SyModObservation(
            observation_type='follow',
            source_plugin=self.name,
            data={
                'user_id': payload.get('user', {}).get('id'),
                'user_name': payload.get('user', {}).get('name'),
                'platform': 'moltx'
            }
        )
    
    async def execute_action(self, action: PluginAction, symod) -> ActionResult:
        """
        Execute an action from the Planner.
        
        Validates through SyMod first, then executes on MoltX API.
        """
        # Validate via SyMod
        if symod:
            is_valid, reason = symod.validate_action(self.name, action)
            if not is_valid:
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    target_id=action.target_id,
                    error_message=f"SyMod validation failed: {reason}"
                )
        
        # Execute based on action type
        try:
            if action.action_type == "like":
                result = await self._execute_like(action)
            elif action.action_type == "reply":
                result = await self._execute_reply(action)
            elif action.action_type == "repost":
                result = await self._execute_repost(action)
            elif action.action_type == "follow":
                result = await self._execute_follow(action)
            elif action.action_type == "post":
                result = await self._execute_post(action)
            else:
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    error_message=f"Unknown action type: {action.action_type}"
                )
            
            # Reflect outcome
            if symod:
                outcome = self._create_outcome(action, result)
                symod.reflect(self.name, action, outcome)
            
            # Update stats
            if result.success:
                self._stats['actions_executed'] += 1
            else:
                self._stats['actions_failed'] += 1
            
            return result
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target_id=action.target_id,
                error_message=str(e)
            )
    
    async def _execute_like(self, action: PluginAction) -> ActionResult:
        """Execute like action via MoltX API"""
        # Simulated - would call actual API
        print(f"👍 MoltX: Liking post {action.target_id}")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ActionResult(
            success=True,
            action_type="like",
            target_id=action.target_id,
            response_data={'post_id': action.target_id, 'action': 'liked'}
        )
    
    async def _execute_reply(self, action: PluginAction) -> ActionResult:
        """Execute reply action via MoltX API"""
        if not action.content:
            return ActionResult(
                success=False,
                action_type="reply",
                error_message="Reply action requires content"
            )
        
        print(f"💬 MoltX: Replying to {action.target_id}: {action.content[:50]}...")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ActionResult(
            success=True,
            action_type="reply",
            target_id=action.target_id,
            response_data={'post_id': action.target_id, 'reply_content': action.content}
        )
    
    async def _execute_repost(self, action: PluginAction) -> ActionResult:
        """Execute repost action via MoltX API"""
        print(f"🔁 MoltX: Reposting {action.target_id}")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ActionResult(
            success=True,
            action_type="repost",
            target_id=action.target_id,
            response_data={'original_post_id': action.target_id}
        )
    
    async def _execute_follow(self, action: PluginAction) -> ActionResult:
        """Execute follow action via MoltX API"""
        target = action.target_name or action.target_id
        print(f"➕ MoltX: Following @{target}")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ActionResult(
            success=True,
            action_type="follow",
            target_id=action.target_id,
            response_data={'followed_user': target}
        )
    
    async def _execute_post(self, action: PluginAction) -> ActionResult:
        """Execute post action via MoltX API"""
        if not action.content:
            return ActionResult(
                success=False,
                action_type="post",
                error_message="Post action requires content"
            )
        
        print(f"📝 MoltX: Creating post: {action.content[:50]}...")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ActionResult(
            success=True,
            action_type="post",
            response_data={'post_id': 'new_post_123', 'content': action.content}
        )
    
    def _create_outcome(self, action: PluginAction, result: ActionResult) -> SyModActionOutcome:
        """Create outcome for SyMod reflection"""
        return SyModActionOutcome(
            action_type=action.action_type,
            success=result.success,
            target_id=action.target_id,
            error_message=result.error_message
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        base_status = super().get_status()
        return {
            **base_status,
            'api_configured': bool(self.api_key),
            'stats': self._stats
        }


# Legacy compatibility - export as MoltxPlugin too
MoltxPlugin = MoltxV2Plugin
