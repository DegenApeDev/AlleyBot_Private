import asyncio
import os
import json
from datetime import datetime
import logging
from typing import List, Dict, Any

from plugins.base_plugin import BasePlugin, PluginRegistry, AsyncPluginMixin
from src.agentic.action_logger import get_action_logger, ActionRecord

logger = logging.getLogger(__name__)

@PluginRegistry.register("skill_evolver")
class SkillEvolverPlugin(BasePlugin, AsyncPluginMixin):
    """
    Monitors ActionLogger for repetitive successful terminal/assistant actions.
    If a sequence of 3 successes is found, it uses the Model Router to abstract
    them into a permanent Python skill script inside the skills/ directory.
    """
    name = "skill_evolver"
    supported_channels = ["system"]
    description = "Hermes Learning Loop: Abstracts successful terminal sequences into reusable skills."
    
    def on_load(self) -> None:
        pass
        
    async def start_background(self) -> None:
        """Start the background monitoring loop for skill graduation."""
        logger.info("🧠 Skill Evolver starting background learning loop...")
        self.create_task(self._evolution_loop(), "evolution_loop")
        
    async def _evolution_loop(self) -> None:
        # Check every 30 minutes
        interval = 30 * 60
        
        while not self.stop_event.is_set():
            try:
                logger.info("🧠 [Skill Evolver] Scanning recent actions for learning opportunities...")
                await self._check_for_graduations()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Skill Evolver error: {e}")
                await asyncio.sleep(60)

    async def _check_for_graduations(self):
        action_logger = get_action_logger()
        # Look for the last 50 successful terminal actions
        recent_actions = action_logger.get_recent_actions(
            action_type='terminal', 
            outcome='success', 
            limit=50
        )
        
        if len(recent_actions) < 3:
            return

        # Simple clustering: if the last 3 terminal commands share identical structure
        # (For this MVP, we just take the last 3 if they happened close together contextually)
        last_three = recent_actions[:3]
        commands = []
        for a in last_three:
            if isinstance(a.trigger_data, dict):
                params = a.trigger_data.get('validation', {}).get('params', {})
                if 'command' in params:
                    commands.append(params['command'])
                elif a.content:
                    commands.append(a.content)
            elif a.content:
                commands.append(a.content)

        if len(commands) >= 3:
            # Check if this is a sandbox drafted skill promotion
            sandbox_target = None
            import re
            for cmd in commands:
                match = re.search(r'sandbox/draft_skills/([^/\s]+)', cmd)
                if match:
                    sandbox_target = match.group(1)
                    break
                    
            if sandbox_target and all(sandbox_target in c for c in commands):
                logger.info(f"🧠 [Skill Evolver] Detected 3 successful sandbox executions for drafted skill '{sandbox_target}'. Promoting...")
                await self._hot_promote_sandbox_skill(sandbox_target)
            else:
                logger.info(f"🧠 [Skill Evolver] Detected sequence of 3 successful raw terminal actions. Graduating...")
                await self._graduate_skill(commands)

    async def _hot_promote_sandbox_skill(self, skill_id: str):
        """Promote a proven drafted skill from the sandbox into permanent intelligence."""
        import shutil
        source_dir = os.path.abspath(f"sandbox/draft_skills/{skill_id}")
        target_dir = os.path.abspath(f"skills/dynamic/{skill_id}")
        
        try:
            if os.path.exists(source_dir):
                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                shutil.move(source_dir, target_dir)
                logger.info(f"✅ Skill {skill_id} has been empirically proven and promoted to {target_dir}!")
            else:
                logger.warning(f"Could not promote {skill_id}: Draft directory {source_dir} missing.")
        except Exception as e:
            logger.error(f"Failed to promote sandbox skill {skill_id}: {e}")

    async def _graduate_skill(self, commands: List[str]):
        """Use the ModelRouter to turn commands into a Python skill."""
        if not hasattr(self._agi_kernel, 'model_router'):
            logger.warning("No model router available for skill graduation.")
            return

        prompt = (
            "You are AlleyBot's Skill Evolver. I have executed the following terminal commands successfully 3 times "
            "and I want to abstract them into a permanent Python skill script.\n"
            "Commands:\n" + "\n".join(commands) + "\n\n"
            "Generate a Python script (with a run() function) that standardizes this workflow. "
            "Output ONLY valid Python code, no markdown blocks."
        )

        try:
            # Using deepseek or grok depending on router config
            generated_code = await self._agi_kernel.model_router.generate(prompt=prompt, system_prompt="You are a senior python engineer.")
            
            # Clean formatting
            generated_code = generated_code.replace('```python', '').replace('```', '').strip()
            
            # Save the new skill
            skill_name = f"auto_skill_{int(datetime.now().timestamp())}.py"
            skill_path = os.path.join(os.getcwd(), 'skills', 'dynamic', skill_name)
            
            os.makedirs(os.path.join(os.getcwd(), 'skills', 'dynamic'), exist_ok=True)
            
            with open(skill_path, 'w') as f:
                f.write(generated_code)
                
            logger.info(f"✅ Skill {skill_name} successfully graduated and saved to {skill_path}!")
            
            # Optionally update Agent Card logic here...
            
        except Exception as e:
            logger.error(f"Failed to graduate skill: {e}")

    async def on_event(self, event, symod) -> None:
        pass
        
    async def execute_action(self, action, symod):
        pass
