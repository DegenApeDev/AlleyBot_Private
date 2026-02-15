"""
Telegram Commands for Plan Management

Provides /plan create, /plan status, /plan next, etc.
for owner to manage multi-step plans.

Part of AGI Core - Phase 3
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime

from src.agentic.planning import (
    get_plan_manager, GoalDecomposer, Plan, PlanStep, 
    StepStatus, StepType
)
from src.agentic.goal_manager import get_goal_manager, GoalStatus

logger = logging.getLogger(__name__)


class PlanCommands:
    """Telegram commands for managing multi-step plans"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._plan_manager = None
        self._goal_manager = None
        self._decomposer = None
    
    def _get_plan_manager(self):
        if self._plan_manager is None:
            self._plan_manager = get_plan_manager()
        return self._plan_manager
    
    def _get_goal_manager(self):
        if self._goal_manager is None:
            self._goal_manager = get_goal_manager()
        return self._goal_manager
    
    def _get_decomposer(self):
        if self._decomposer is None:
            self._decomposer = GoalDecomposer()
        return self._decomposer
    
    def _is_owner(self, update: Update) -> bool:
        user_id = str(update.effective_user.id)
        owner_id = None
        
        core = getattr(self.telegram, 'core', None)
        if core and hasattr(core, 'config'):
            owner_id = core.config.get('TELEGRAM_ADMIN_CHAT_ID')
        
        if not owner_id:
            import os
            owner_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        return user_id == str(owner_id)
    
    async def plan_create(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Create a plan for a goal.
        
        Usage: /plan_create <goal_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /plan_create <goal_id>")
            return
        
        goal_id = context.args[0]
        
        try:
            # Get goal
            goal_manager = self._get_goal_manager()
            goal = goal_manager.get_goal(goal_id)
            
            if not goal:
                await update.message.reply_text(f"❌ Goal `{goal_id}` not found")
                return
            
            if goal.status != GoalStatus.APPROVED:
                await update.message.reply_text(
                    f"⚠️ Goal must be approved first.\n"
                    f"Current status: {goal.status.name}\n"
                    f"Use /goals_approve {goal_id}"
                )
                return
            
            # Decompose into plan
            decomposer = self._get_decomposer()
            plan = decomposer.decompose_goal(goal)
            
            # Save plan
            plan_manager = self._get_plan_manager()
            plan_manager.save_plan(plan)
            
            # Mark goal as active
            goal_manager.start_goal(goal_id)
            
            # Build response
            msg = (
                f"📋 **Plan Created**\n\n"
                f"Goal: {goal.title}\n"
                f"Plan ID: `{plan.id}`\n"
                f"Steps: {len(plan.steps)}\n\n"
                f"**Step Overview:**\n"
            )
            
            for i, step in enumerate(plan.steps.values(), 1):
                status_emoji = "🟢" if step.status == StepStatus.READY else "⏳"
                msg += f"{i}. {status_emoji} {step.title}\n"
            
            msg += f"\n🚀 Start with `/plan_next {plan.id}`"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Plan create error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def plan_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show plan status and progress.
        
        Usage: /plan_status <plan_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /plan_status <plan_id>")
            return
        
        plan_id = context.args[0]
        
        try:
            plan_manager = self._get_plan_manager()
            plan = plan_manager.get_plan(plan_id)
            
            if not plan:
                await update.message.reply_text(f"❌ Plan `{plan_id}` not found")
                return
            
            # Count by status
            by_status = {}
            for step in plan.steps.values():
                status = step.status.name
                by_status[status] = by_status.get(status, 0) + 1
            
            # Progress bar
            progress = int(plan.progress_percent / 10)
            bar = "█" * progress + "░" * (10 - progress)
            
            msg = (
                f"📋 **Plan Status**\n\n"
                f"{plan.title}\n"
                f"ID: `{plan.id}`\n"
                f"Status: {plan.status.upper()}\n\n"
                f"**Progress:** {bar} {plan.progress_percent:.0f}%\n"
            )
            
            for status, count in by_status.items():
                emoji = {"COMPLETED": "✅", "READY": "🟢", "ACTIVE": "🔵", 
                        "BLOCKED": "⏳", "FAILED": "❌", "PENDING": "⚪"}.get(status, "⚪")
                msg += f"{emoji} {status}: {count}\n"
            
            # Show current/next step
            ready = plan.get_ready_steps()
            if ready:
                msg += f"\n🎯 **Ready to execute:** {len(ready)} steps\n"
                msg += f"Next: {ready[0].title}\n"
            elif plan.is_complete:
                msg += "\n✅ **Plan Complete!**\n"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Plan status error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def plan_next(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Execute the next ready step in a plan.
        
        Usage: /plan_next <plan_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /plan_next <plan_id>")
            return
        
        plan_id = context.args[0]
        
        try:
            plan_manager = self._get_plan_manager()
            plan = plan_manager.get_plan(plan_id)
            
            if not plan:
                await update.message.reply_text(f"❌ Plan `{plan_id}` not found")
                return
            
            if plan.is_complete:
                await update.message.reply_text("✅ Plan is already complete!")
                return
            
            # Get next step
            step = plan.get_next_step()
            
            if not step:
                if plan.has_failures:
                    await update.message.reply_text(
                        "❌ No ready steps. Some steps failed.\n"
                        "Use `/plan_retry` to retry failed steps."
                    )
                else:
                    await update.message.reply_text("⏳ No steps ready - all remaining steps are blocked by dependencies")
                return
            
            # Execute step (simulated for now)
            step.status = StepStatus.ACTIVE
            step.started_at = datetime.now()
            step.attempts += 1
            
            # Simulate execution
            await update.message.reply_text(
                f"🔵 **Executing Step:** {step.title}\n"
                f"Type: {step.step_type.name}\n"
                f"Command: `{step.command}`\n\n"
                f"⏳ Working..."
            )
            
            # For now, auto-complete (in real implementation, this would actually execute)
            import asyncio
            await asyncio.sleep(2)
            
            # Complete step
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.output = f"Completed {step.title}"
            
            # Update plan
            plan.update_step_status(step.id, StepStatus.COMPLETED)
            plan.current_step_id = step.id
            
            # Save
            plan_manager.save_plan(plan)
            
            # Check if complete
            if plan.is_complete:
                # Mark goal as complete
                goal_manager = self._get_goal_manager()
                goal_manager.complete_goal(plan.goal_id, "All plan steps completed successfully")
                
                await update.message.reply_text(
                    f"✅ **Step Complete:** {step.title}\n\n"
                    f"🎉 **Plan Complete!**\n"
                    f"Goal achieved: {plan.title}"
                )
            else:
                # Show next step
                next_step = plan.get_next_step()
                next_msg = f"✅ **Step Complete:** {step.title}\n\n"
                if next_step:
                    next_msg += f"🎯 **Next Step:** {next_step.title}\n"
                    next_msg += f"Use `/plan_next {plan_id}` to continue"
                else:
                    next_msg += "⏳ Waiting for dependencies..."
                
                await update.message.reply_text(next_msg)
            
        except Exception as e:
            logger.error(f"Plan next error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def plan_retry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Retry a failed step.
        
        Usage: /plan_retry <plan_id> [step_id]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /plan_retry <plan_id> [step_id]")
            return
        
        plan_id = context.args[0]
        step_id = context.args[1] if len(context.args) > 1 else None
        
        try:
            plan_manager = self._get_plan_manager()
            plan = plan_manager.get_plan(plan_id)
            
            if not plan:
                await update.message.reply_text(f"❌ Plan `{plan_id}` not found")
                return
            
            # Find failed steps
            failed = [s for s in plan.steps.values() if s.status == StepStatus.FAILED]
            
            if not failed:
                await update.message.reply_text("✅ No failed steps to retry")
                return
            
            if step_id:
                # Retry specific step
                if step_id not in plan.steps:
                    await update.message.reply_text(f"❌ Step `{step_id}` not found")
                    return
                step = plan.steps[step_id]
                if step.status != StepStatus.FAILED:
                    await update.message.reply_text(f"⚠️ Step `{step_id}` is not failed")
                    return
                
                step.status = StepStatus.READY
                step.attempts = 0
                step.last_error = None
                plan_manager.save_plan(plan)
                
                await update.message.reply_text(f"🔄 Step `{step_id}` ready to retry\nUse `/plan_next {plan_id}`")
            else:
                # Retry all failed steps
                for step in failed:
                    step.status = StepStatus.READY
                    step.attempts = 0
                    step.last_error = None
                
                plan_manager.save_plan(plan)
                
                await update.message.reply_text(
                    f"🔄 Retrying {len(failed)} failed steps\n"
                    f"Use `/plan_next {plan_id}` to continue"
                )
            
        except Exception as e:
            logger.error(f"Plan retry error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def plan_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        List all active plans.
        
        Usage: /plan_list [status]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        await update.message.reply_text(
            "📋 **Active Plans**\n\n"
            "Plan tracking is stored in the database.\n"
            "Use `/plan_status <plan_id>` to check specific plans."
        )
    
    def get_handlers(self):
        """Get command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('plan_create', self.plan_create),
            CommandHandler('plan_status', self.plan_status),
            CommandHandler('plan_next', self.plan_next),
            CommandHandler('plan_retry', self.plan_retry),
            CommandHandler('plan_list', self.plan_list),
        ]


# Convenience function
def register_plan_commands(dispatcher, telegram_plugin=None):
    """Register all plan commands with dispatcher"""
    commands = PlanCommands(telegram_plugin)
    for handler in commands.get_handlers():
        dispatcher.add_handler(handler)
    logger.info("📋 Plan commands registered")
