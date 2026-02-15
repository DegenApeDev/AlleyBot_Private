"""
MoltX SyMod Integration - Uses the CORE SyMod system (not plugin-specific)

This module integrates MoltX with Alley's central SyMod mathematical framework.
All observations and actions flow through the core SyMod manager.
"""

import os
import asyncio
from typing import Optional, List, Dict
from datetime import datetime

from src.agentic.symod_core import (
    get_symod_manager, 
    SyModObservation, 
    SyModActionProposal,
    SyModActionOutcome
)


class MoltxSyModInterface:
    """
    MoltX interface to the CORE SyMod system
    
    This is NOT a separate SyMod - it uses the shared core manager
    that all plugins can access. This ensures unified world modeling
    across all of AlleyBot's behaviors.
    """
    
    PLUGIN_NAME = 'moltx'
    
    def __init__(self, moltx_plugin):
        self.plugin = moltx_plugin
        self.symod = get_symod_manager()
        self.symod.register_plugin(self.PLUGIN_NAME, {
            'description': 'MoltX social media platform integration',
            'capabilities': ['like', 'reply', 'repost', 'follow', 'post']
        })
        
        self.running = False
        self.task = None
        self.cycle_interval = int(os.getenv('ALLEY_SYMOD_CYCLE_INTERVAL', '30'))
    
    # === Core Interface ===
    
    def start(self) -> str:
        """Start continuous SyMod-driven social loop"""
        if self.running:
            return "⚠️ MoltX SyMod loop already running"
        
        async def run():
            try:
                await self._run_continuous()
            except Exception as e:
                print(f"❌ MoltX SyMod error: {e}")
                self.running = False
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            self.task = asyncio.create_task(run())
        else:
            self.task = loop.create_task(run())
        
        self.running = True
        return (
            f"🚀 MoltX SyMod loop started!\n"
            f"⏱️ Cycle: {self.cycle_interval} minutes\n"
            f"🔢 Using core SyMod mathematical framework\n"
            f"\nCommands:\n"
            f"  • /symod_status - Check status\n"
            f"  • /symod_stop - Stop loop\n"
            f"  • /symod_cycle - Manual cycle"
        )
    
    def stop(self) -> str:
        """Stop the SyMod-driven loop"""
        if not self.running:
            return "⚠️ MoltX SyMod loop not running"
        
        self.running = False
        if self.task:
            self.task.cancel()
        
        return "🛑 MoltX SyMod loop stopped"
    
    def get_status(self) -> str:
        """Get SyMod status for MoltX"""
        status = self.symod.get_plugin_status(self.PLUGIN_NAME)
        unified = self.symod.get_unified_state()
        
        output = "🧠 **MoltX SyMod Status**\n\n"
        output += f"**Loop:** {'🟢 Running' if self.running else '🔴 Stopped'}\n"
        output += f"**SyMod Framework:** {'✅ Active' if status.get('symod_enabled') else '❌ Offline'}\n"
        output += f"**Cycle Interval:** {self.cycle_interval} minutes\n\n"
        
        if status.get('registered'):
            stats = status.get('stats', {})
            output += "**MoltX Stats:**\n"
            output += f"  Observations: {stats.get('observations_count', 0)}\n"
            output += f"  Actions Proposed: {stats.get('actions_proposed', 0)}\n"
            output += f"  Actions Executed: {stats.get('actions_executed', 0)}\n\n"
        
        output += "**Unified World State:**\n"
        output += f"  Total Entities: {unified.get('entities', 0)}\n"
        output += f"  Topics Tracked: {unified.get('topics', 0)}\n"
        output += f"  Registered Plugins: {', '.join(unified.get('registered_plugins', []))}\n\n"
        
        top_topics = unified.get('top_topics', [])
        if top_topics:
            output += "**Top Topics:**\n"
            for topic, weight in top_topics[:5]:
                output += f"  #{topic}: {weight:.2f}\n"
        
        return output
    
    async def run_cycle(self) -> str:
        """Run one manual SyMod cycle"""
        try:
            metrics = await self._execute_cycle()
            
            output = "✅ **MoltX SyMod Cycle Complete**\n\n"
            output += f"**Observations:** {metrics['observations']}\n"
            output += f"**Proposals Generated:** {metrics['proposals']}\n"
            output += f"**Actions Executed:** {metrics['executed']}\n"
            output += f"**Success Rate:** {metrics['success_rate']:.0%}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Cycle failed: {e}"
    
    def configure(self, key=None, value=None) -> str:
        """View/configure settings"""
        config = self.symod.config
        
        if key is None:
            output = "⚙️ **SyMod Configuration**\n\n"
            for k, v in config.items():
                output += f"  {k}: {v}\n"
            output += "\n💡 Set ALLEY_SYMOD_MODE=(conservative|normal|aggressive) in .env"
            return output
        
        if value is None:
            return f"⚙️ {key}: {config.get(key, 'Not set')}"
        
        return f"💡 Use ALLEY_SYMOD_MODE env var to change configuration"
    
    # === Internal Cycle Logic ===
    
    async def _run_continuous(self):
        """Continuous loop"""
        self.running = True
        print(f"🚀 MoltX SyMod loop started (cycle: {self.cycle_interval}min)")
        
        while self.running:
            try:
                cycle_start = datetime.now()
                await self._execute_cycle()
                
                elapsed = (datetime.now() - cycle_start).total_seconds()
                sleep_seconds = max(0, self.cycle_interval * 60 - elapsed)
                
                while sleep_seconds > 0 and self.running:
                    await asyncio.sleep(min(30, sleep_seconds))
                    sleep_seconds -= 30
                    
            except Exception as e:
                print(f"❌ MoltX SyMod cycle error: {e}")
                await asyncio.sleep(60)
    
    async def _execute_cycle(self) -> Dict:
        """Execute one full sense-think-act-reflect cycle"""
        # === SENSE: Fetch and observe ===
        posts = await self._fetch_posts()
        observations = self._create_observations(posts)
        
        # Submit observations to core SyMod
        for obs in observations:
            self.symod.observe(obs)
        
        # === THINK: Get action proposals ===
        available_actions = ['like', 'reply', 'repost', 'follow']
        context = {
            'observations': observations,
            'constraints': {
                'max_actions': 20,
                'min_confidence': 0.6
            }
        }
        
        proposals = self.symod.propose_actions(
            self.PLUGIN_NAME,
            context,
            available_actions
        )
        
        # === ACT: Execute proposals ===
        executed = 0
        successes = 0
        
        for proposal in proposals:
            outcome = await self._execute_proposal(proposal)
            
            # Reflect outcome back to SyMod
            self.symod.reflect(self.PLUGIN_NAME, proposal, outcome)
            
            executed += 1
            if outcome.success:
                successes += 1
            
            await asyncio.sleep(1)  # Rate limit spacing
        
        return {
            'observations': len(observations),
            'proposals': len(proposals),
            'executed': executed,
            'successes': successes,
            'success_rate': successes / executed if executed > 0 else 0
        }
    
    async def _fetch_posts(self) -> List[Dict]:
        """Fetch posts from MoltX"""
        posts = []
        
        try:
            if hasattr(self.plugin, 'get_feed'):
                result = self.plugin.get_feed('global', limit=50)
                if isinstance(result, dict):
                    posts = result.get('posts', []) or result.get('data', {}).get('posts', [])
        except Exception as e:
            print(f"⚠️ Failed to fetch posts: {e}")
        
        return posts
    
    def _create_observations(self, posts: List[Dict]) -> List[SyModObservation]:
        """Convert posts to SyMod observations"""
        observations = []
        
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            obs = SyModObservation(
                observation_type='post',
                source_plugin=self.PLUGIN_NAME,
                data={
                    'id': post.get('id'),
                    'content': post.get('content', ''),
                    'author_id': post.get('author', {}).get('id'),
                    'author_name': post.get('author', {}).get('name'),
                    'likes': post.get('like_count', 0),
                    'replies': post.get('reply_count', 0),
                    'hashtags': post.get('hashtags', []),
                    'already_liked': post.get('liked_by_me', False)
                }
            )
            observations.append(obs)
        
        return observations
    
    async def _execute_proposal(self, proposal: SyModActionProposal) -> SyModActionOutcome:
        """Execute a single action proposal"""
        success = False
        error = None
        
        try:
            if proposal.action_type == 'like':
                if hasattr(self.plugin, 'like_post'):
                    result = self.plugin.like_post(proposal.target_id)
                    success = '✅' in str(result)
                    
            elif proposal.action_type == 'reply':
                # Generate reply content
                content = await self._generate_reply(proposal)
                if content and hasattr(self.plugin, 'reply_to_post'):
                    result = self.plugin.reply_to_post(proposal.target_id, content)
                    success = '✅' in str(result)
                    
            elif proposal.action_type == 'repost':
                if hasattr(self.plugin, 'repost_post'):
                    result = self.plugin.repost_post(proposal.target_id)
                    success = '✅' in str(result)
                    
            elif proposal.action_type == 'follow':
                if hasattr(self.plugin, 'follow_user') and proposal.target_name:
                    result = self.plugin.follow_user(proposal.target_name)
                    success = '✅' in str(result)
                    
        except Exception as e:
            error = str(e)
            print(f"❌ Action failed: {e}")
        
        return SyModActionOutcome(
            action_type=proposal.action_type,
            success=success,
            target_id=proposal.target_id,
            error_message=error
        )
    
    async def _generate_reply(self, proposal: SyModActionProposal) -> Optional[str]:
        """Generate reply content using AlleyBot's AI"""
        try:
            # Use existing _generate_comment if available
            if hasattr(self.plugin, '_generate_comment'):
                content = proposal.metadata.get('observation', {}).get('content', '')
                author = proposal.target_name or 'user'
                return self.plugin._generate_comment(content, agent_name=author)
            
            # Fallback
            return "Interesting perspective! 🚀"
            
        except Exception as e:
            print(f"⚠️ Reply generation failed: {e}")
            return None


# Convenience functions for Telegram commands
def symod_start_command(moltx_plugin) -> str:
    """Start SyMod loop for MoltX"""
    interface = getattr(moltx_plugin, '_symod_interface', None)
    if not interface:
        interface = MoltxSyModInterface(moltx_plugin)
        moltx_plugin._symod_interface = interface
    return interface.start()

def symod_stop_command(moltx_plugin) -> str:
    """Stop SyMod loop for MoltX"""
    interface = getattr(moltx_plugin, '_symod_interface', None)
    if not interface:
        return "❌ SyMod interface not initialized"
    return interface.stop()

def symod_status_command(moltx_plugin) -> str:
    """Get SyMod status for MoltX"""
    interface = getattr(moltx_plugin, '_symod_interface', None)
    if not interface:
        interface = MoltxSyModInterface(moltx_plugin)
        moltx_plugin._symod_interface = interface
    return interface.get_status()

def symod_cycle_command(moltx_plugin) -> str:
    """Run manual cycle for MoltX"""
    import asyncio
    interface = getattr(moltx_plugin, '_symod_interface', None)
    if not interface:
        interface = MoltxSyModInterface(moltx_plugin)
        moltx_plugin._symod_interface = interface
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        task = asyncio.create_task(interface.run_cycle())
        return "⏳ Cycle running... check /symod_status for results"
    else:
        return loop.run_until_complete(interface.run_cycle())

def symod_config_command(moltx_plugin, key=None, value=None) -> str:
    """Configure SyMod settings"""
    interface = getattr(moltx_plugin, '_symod_interface', None)
    if not interface:
        interface = MoltxSyModInterface(moltx_plugin)
        moltx_plugin._symod_interface = interface
    return interface.configure(key, value)
