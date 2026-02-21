"""
Telegram Commands for Goal Management

Provides /goals list, /goals propose, /goals approve, etc.
for owner to manage Alley's autonomous goals.

Part of AGI Core - Phase 2
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.agentic.goal_manager import get_goal_manager, GoalStatus, GoalPriority
from src.agentic.goal_detector import get_goal_detector

logger = logging.getLogger(__name__)


class GoalCommands:
    """Telegram commands for managing autonomous goals"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._goal_manager = None
        self._goal_detector = None
    
    def _get_goal_manager(self):
        """Lazy-get goal manager"""
        if self._goal_manager is None:
            self._goal_manager = get_goal_manager()
        return self._goal_manager
    
    def _get_goal_detector(self):
        """Lazy-get goal detector"""
        if self._goal_detector is None:
            self._goal_detector = get_goal_detector()
        return self._goal_detector
    
    def _is_owner(self, update: Update) -> bool:
        """Check if user is owner"""
        user_id = str(update.effective_user.id)
        owner_id = None
        
        core = getattr(self.telegram, 'core', None)
        if core and hasattr(core, 'config'):
            owner_id = core.config.get('TELEGRAM_ADMIN_CHAT_ID')
        
        if not owner_id:
            import os
            owner_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        return user_id == str(owner_id)
    
    async def goals_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        List all goals with optional filtering.
        
        Usage: /goals [status] [limit]
        Status: proposed, approved, active, completed, all
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        status_filter = None
        limit = 10
        
        if context.args:
            status_arg = context.args[0].lower()
            if status_arg in ['proposed', 'approved', 'active', 'completed']:
                status_filter = GoalStatus[status_arg.upper()]
            elif status_arg == 'all':
                status_filter = None
            
            if len(context.args) > 1:
                try:
                    limit = int(context.args[1])
                except ValueError:
                    pass
        
        try:
            manager = self._get_goal_manager()
            
            if status_filter:
                goals = manager.get_goals(status=status_filter, limit=limit)
            else:
                # Get recent across all statuses
                goals = manager.get_goals(limit=limit)
            
            if not goals:
                await update.message.reply_text("📭 No goals found")
                return
            
            # Group by status
            by_status = {}
            for goal in goals:
                status = goal.status.name
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(goal)
            
            msg = "🎯 Goals Overview\n\n"
            
            for status in ['PROPOSED', 'APPROVED', 'ACTIVE', 'COMPLETED']:
                if status in by_status:
                    count = len(by_status[status])
                    msg += f"**{status}** ({count} goals)\n"
                    for goal in by_status[status][:3]:  # Show top 3 per status
                        priority_emoji = "🔴" if goal.effective_priority >= 8 else "🟡" if goal.effective_priority >= 5 else "🟢"
                        msg += f"  {priority_emoji} {goal.id}: {goal.title[:40]}\n"
                    msg += "\n"
            
            msg += "\n📊 Use /goals_stats for detailed statistics"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Goals list error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Scan for new goals/gaps.
        
        Usage: /goals_scan [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 24
        if context.args:
            try:
                hours = int(context.args[0])
            except ValueError:
                pass
        
        await update.message.reply_text(f"🔍 Scanning for gaps (last {hours}h)...")
        
        try:
            detector = self._get_goal_detector()
            gaps = detector.scan_for_gaps(hours)
            
            if not gaps:
                await update.message.reply_text("✅ No gaps detected - everything looks good!")
                return
            
            msg = f"🔍 Found {len(gaps)} gaps/opportunities:\n\n"
            
            for i, gap in enumerate(gaps[:5], 1):
                msg += (
                    f"{i}. **{gap.gap_type.replace('_', ' ').title()}**\n"
                    f"   Impact: {gap.impact_estimate}/10 | Frequency: {gap.frequency}x\n"
                    f"   {gap.description[:60]}...\n\n"
                )
            
            msg += "\n💡 Run `/goals_propose` to generate goals from these gaps"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Goals scan error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_propose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Auto-detect gaps and propose goals.
        
        Usage: /goals_propose [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 24
        if context.args:
            try:
                hours = int(context.args[0])
            except ValueError:
                pass
        
        await update.message.reply_text(f"🤔 Analyzing activity and proposing goals...")
        
        try:
            detector = self._get_goal_detector()
            proposed = detector.auto_detect_and_propose(hours)
            
            if not proposed:
                await update.message.reply_text("📭 No new goals to propose")
                return
            
            msg = f"🎯 Proposed {len(proposed)} new goals:\n\n"
            
            for goal in proposed:
                priority_emoji = "🔴" if goal.effective_priority >= 8 else "🟡" if goal.effective_priority >= 5 else "🟢"
                effort_emoji = "⚡" if goal.effort_estimate == 'hours' else "⏱️" if goal.effort_estimate == 'days' else "📅"
                
                msg += (
                    f"{priority_emoji} **{goal.title}**\n"
                    f"   ID: `{goal.id}`\n"
                    f"   Priority: {goal.priority.name} | Effort: {effort_emoji} {goal.effort_estimate}\n"
                    f"   Impact: {goal.impact_score}/10 | Confidence: {goal.confidence:.0%}\n"
                    f"   {goal.description[:80]}...\n\n"
                )
            
            msg += "\n✅ Approve with `/goals_approve <id>`\n❌ Reject with `/goals_reject <id>`"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Goals propose error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Approve a proposed goal.
        
        Usage: /goals_approve <goal_id> [notes]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /goals_approve <goal_id> [notes]")
            return
        
        goal_id = context.args[0]
        notes = ' '.join(context.args[1:]) if len(context.args) > 1 else None
        
        try:
            manager = self._get_goal_manager()
            success = manager.approve_goal(goal_id, notes)
            
            if success:
                goal = manager.get_goal(goal_id)
                msg = (
                    f"✅ **Goal Approved**\n\n"
                    f"{goal.title}\n"
                    f"ID: `{goal_id}`\n"
                    f"Priority: {goal.priority.name}\n\n"
                    f"🚀 Ready to start with `/goals_start {goal_id}`"
                )
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text(f"❌ Could not approve goal `{goal_id}`")
            
        except Exception as e:
            logger.error(f"Goals approve error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Reject a proposed goal.
        
        Usage: /goals_reject <goal_id> [reason]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /goals_reject <goal_id> [reason]")
            return
        
        goal_id = context.args[0]
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else None
        
        try:
            manager = self._get_goal_manager()
            success = manager.reject_goal(goal_id, reason)
            
            if success:
                await update.message.reply_text(f"❌ Goal `{goal_id}` rejected" + (f"\nReason: {reason}" if reason else ""))
            else:
                await update.message.reply_text(f"❌ Could not reject goal `{goal_id}`")
            
        except Exception as e:
            logger.error(f"Goals reject error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start working on an approved goal.
        
        Usage: /goals_start <goal_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /goals_start <goal_id>")
            return
        
        goal_id = context.args[0]
        
        try:
            manager = self._get_goal_manager()
            success = manager.start_goal(goal_id)
            
            if success:
                goal = manager.get_goal(goal_id)
                await update.message.reply_text(
                    f"🚀 **Goal Started**\n\n{goal.title}\n\n"
                    f"Alley is now working on this goal.\n"
                    f"Track progress with `/goals_status {goal_id}`"
                )
            else:
                await update.message.reply_text(f"❌ Could not start goal `{goal_id}` - must be approved first")
            
        except Exception as e:
            logger.error(f"Goals start error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_complete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Mark a goal as completed.
        
        Usage: /goals_complete <goal_id> [outcome]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /goals_complete <goal_id> [outcome]")
            return
        
        goal_id = context.args[0]
        outcome = ' '.join(context.args[1:]) if len(context.args) > 1 else "Completed successfully"
        
        try:
            manager = self._get_goal_manager()
            success = manager.complete_goal(goal_id, outcome)
            
            if success:
                await update.message.reply_text(f"✅ Goal `{goal_id}` completed!\n\nOutcome: {outcome}")
            else:
                await update.message.reply_text(f"❌ Could not complete goal `{goal_id}`")
            
        except Exception as e:
            logger.error(f"Goals complete error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show detailed view of a goal.
        
        Usage: /goals_detail <goal_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /goals_detail <goal_id>")
            return
        
        goal_id = context.args[0]
        
        try:
            manager = self._get_goal_manager()
            goal = manager.get_goal(goal_id)
            
            if not goal:
                await update.message.reply_text(f"❌ Goal `{goal_id}` not found")
                return
            
            priority_emoji = "🔴" if goal.effective_priority >= 8 else "🟡" if goal.effective_priority >= 5 else "🟢"
            
            msg = (
                f"🎯 **{goal.title}**\n\n"
                f"ID: `{goal.id}`\n"
                f"Status: {goal.status.name}\n"
                f"Category: {goal.category}\n"
                f"{priority_emoji} Priority: {goal.priority.name} (score: {goal.effective_priority})\n\n"
                f"**Description:**\n{goal.description}\n\n"
                f"**Impact:** {goal.impact_score}/10\n"
                f"**Confidence:** {goal.confidence:.0%}\n"
                f"**Estimated Effort:** {goal.effort_estimate}\n\n"
            )
            
            if goal.proposed_solution:
                msg += f"**Proposed Solution:**\n{goal.proposed_solution}\n\n"
            
            if goal.evidence:
                msg += f"**Evidence ({len(goal.evidence)} items):**\n"
                for ev in goal.evidence[:3]:
                    msg += f"• {ev[:60]}...\n"
                msg += "\n"
            
            msg += f"Created: {goal.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            if goal.approved_at:
                msg += f"Approved: {goal.approved_at.strftime('%Y-%m-%d %H:%M')}\n"
            if goal.started_at:
                msg += f"Started: {goal.started_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Goals detail error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def goals_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show goal system statistics"""
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        try:
            manager = self._get_goal_manager()
            stats = manager.get_statistics()
            
            msg = (
                "📊 **Goal System Statistics**\n\n"
                f"**By Status:**\n"
            )
            
            for status, count in stats['by_status'].items():
                emoji = "🟢" if status == 'COMPLETED' else "🟡" if status == 'ACTIVE' else "🔵"
                msg += f"  {emoji} {status}: {count}\n"
            
            msg += (
                f"\n**By Category:**\n"
            )
            
            for category, count in stats['by_category'].items():
                msg += f"  • {category}: {count}\n"
            
            msg += (
                f"\n**Performance:**\n"
                f"  Completion Rate: {stats['completion_rate']:.1%}\n"
                f"  Pending Approval: {stats['pending_approval']}\n"
                f"  Recent (7 days): {stats['recent_7_days']}\n"
            )
            
            await update.message.reply_text(msg)
            
        except Exception as e:
            logger.error(f"Goals stats error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Get command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('goals', self.goals_list),
            CommandHandler('goals_scan', self.goals_scan),
            CommandHandler('goals_propose', self.goals_propose),
            CommandHandler('goals_approve', self.goals_approve),
            CommandHandler('goals_reject', self.goals_reject),
            CommandHandler('goals_start', self.goals_start),
            CommandHandler('goals_complete', self.goals_complete),
            CommandHandler('goals_detail', self.goals_detail),
            CommandHandler('goals_stats', self.goals_stats),
        ]


# Convenience function for registration
def register_goal_commands(dispatcher, telegram_plugin=None):
    """Register all goal commands with dispatcher"""
    commands = GoalCommands(telegram_plugin)
    for handler in commands.get_handlers():
        dispatcher.add_handler(handler)
    logger.info("🎯 Goal commands registered")
