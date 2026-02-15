"""
Telegram Commands for Self-Reflection System

Provides /reflection_status, /reflection_log, /reflection_tune, /evolve
for owner to monitor and tune Alley's learning capabilities.

Part of AGI Core - Phase 1
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.agentic.action_logger import ActionLogger, get_action_logger
from src.agentic.strategy_evolver import StrategyEvolver, get_strategy_evolver, StrategyType

logger = logging.getLogger(__name__)


class ReflectionCommands:
    """Telegram commands for self-reflection system"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._action_logger = None
        self._evolver = None
    
    def _get_action_logger(self):
        if self._action_logger is None:
            self._action_logger = get_action_logger()
        return self._action_logger
    
    def _get_evolver(self):
        if self._evolver is None:
            self._evolver = get_strategy_evolver()
        return self._evolver
    
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
    
    async def reflection_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show learning stats and reflection status.
        
        Usage: /reflection_status [hours]
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
        
        try:
            action_logger = self._get_action_logger()
            evolver = self._get_evolver()
            
            # Get action statistics
            stats = action_logger.get_statistics(hours=hours)
            
            # Get strategy summary
            strategies_by_type = evolver.get_strategies_ranked()
            
            # Build status message
            msg = f"📊 **Reflection Status (Last {hours}h)**\n\n"
            
            # Actions summary
            msg += f"📝 **Actions Logged:** {stats['total_actions']}\n"
            msg += f"✅ **Success Rate:** {stats['success_rate']:.1%}\n"
            
            if stats['by_outcome']:
                msg += "📈 **Outcomes:**\n"
                for outcome, count in stats['by_outcome'].items():
                    msg += f"  • {outcome}: {count}\n"
            
            msg += "\n"
            
            # Plugin breakdown
            if stats['by_plugin']:
                msg += "🔌 **By Plugin:**\n"
                for plugin, data in stats['by_plugin'].items():
                    msg += f"  • {plugin}: {data['count']} (avg conf: {data['avg_confidence']:.2f})\n"
                msg += "\n"
            
            # Strategy summary
            msg += "🧬 **Strategies by Type:**\n"
            for stype, strategies in strategies_by_type.items():
                if strategies:
                    best = strategies[0]
                    msg += f"  • {stype.value}: {len(strategies)} strategies"
                    if best.times_used > 0:
                        msg += f" (best: {best.name} @ {best.fitness_score:.0%})"
                    msg += "\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in reflection_status: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def reflection_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        View recent actions and outcomes.
        
        Usage: /reflection_log [limit] [plugin] [outcome]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        limit = 10
        plugin = None
        outcome = None
        
        if context.args:
            try:
                limit = min(50, int(context.args[0]))
                if len(context.args) > 1:
                    plugin = context.args[1]
                if len(context.args) > 2:
                    outcome = context.args[2]
            except ValueError:
                pass
        
        try:
            action_logger = self._get_action_logger()
            actions = action_logger.get_recent_actions(
                plugin=plugin,
                outcome=outcome,
                limit=limit
            )
            
            if not actions:
                await update.message.reply_text("📝 No actions found matching criteria")
                return
            
            msg = f"📋 **Recent Actions (Last {limit})**\n\n"
            
            for action in actions[:20]:  # Max 20 to avoid message size limits
                # Status emoji
                status = "⏳"
                if action.outcome == 'success':
                    status = "✅"
                elif action.outcome == 'failure':
                    status = "❌"
                elif action.outcome == 'blocked':
                    status = "🚫"
                
                msg += f"{status} **{action.action_type}** by {action.plugin}\n"
                msg += f"  ID: `{action.id}`\n"
                msg += f"  Time: {action.timestamp.strftime('%H:%M')}\n"
                msg += f"  Conf: {action.confidence:.2f} | Field: {action.field_status}\n"
                
                if action.target_name:
                    msg += f"  Target: {action.target_name}\n"
                
                if action.outcome:
                    msg += f"  Outcome: {action.outcome}"
                    if action.engagement_received > 0:
                        msg += f" (+{action.engagement_received:.0f} engagement)"
                    msg += "\n"
                
                msg += "\n"
            
            if len(actions) > 20:
                msg += f"_... and {len(actions) - 20} more actions_"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in reflection_log: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def reflection_tune(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Adjust learning parameters.
        
        Usage: /reflection_tune [parameter] [value]
        Parameters: mutation_rate, elite_threshold, cull_threshold
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args or len(context.args) < 2:
            evolver = self._get_evolver()
            msg = (
                "⚙️ **Current Learning Parameters**\n\n"
                f"🎲 Mutation Rate: {evolver.MUTATION_RATE:.0%}\n"
                f"👑 Elite Threshold: {evolver.ELITE_THRESHOLD:.0%}\n"
                f"🗑️ Cull Threshold: {evolver.CULL_THRESHOLD:.0%}\n"
                f"📊 Min Sample Size: {evolver.MIN_SAMPLE_SIZE} uses\n"
                f"📈 Max Strategies/Type: {evolver.MAX_STRATEGIES_PER_TYPE}\n\n"
                "**Usage:**\n"
                "`/reflection_tune mutation_rate 0.4`\n"
                "`/reflection_tune elite_threshold 0.75`\n"
                "`/reflection_tune cull_threshold 0.25`"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        param = context.args[0].lower()
        try:
            value = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Value must be a number")
            return
        
        evolver = self._get_evolver()
        
        if param == 'mutation_rate':
            if 0 <= value <= 1:
                evolver.MUTATION_RATE = value
                await update.message.reply_text(f"✅ Mutation rate set to {value:.0%}")
            else:
                await update.message.reply_text("❌ Mutation rate must be 0-1")
        
        elif param == 'elite_threshold':
            if 0 <= value <= 1:
                evolver.ELITE_THRESHOLD = value
                await update.message.reply_text(f"✅ Elite threshold set to {value:.0%}")
            else:
                await update.message.reply_text("❌ Elite threshold must be 0-1")
        
        elif param == 'cull_threshold':
            if 0 <= value <= 1:
                evolver.CULL_THRESHOLD = value
                await update.message.reply_text(f"✅ Cull threshold set to {value:.0%}")
            else:
                await update.message.reply_text("❌ Cull threshold must be 0-1")
        
        elif param == 'min_sample':
            if value >= 1:
                evolver.MIN_SAMPLE_SIZE = int(value)
                await update.message.reply_text(f"✅ Min sample size set to {int(value)}")
            else:
                await update.message.reply_text("❌ Min sample size must be >= 1")
        
        else:
            await update.message.reply_text(
                f"❌ Unknown parameter: {param}\n"
                "Available: mutation_rate, elite_threshold, cull_threshold, min_sample"
            )
    
    async def evolve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Trigger a manual evolution cycle.
        
        Usage: /evolve
        Runs one evolution cycle: evaluate, mutate top performers, cull underperformers.
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        await update.message.reply_text("🧬 Starting evolution cycle...")
        
        try:
            evolver = self._get_evolver()
            report = evolver.evolve()
            
            msg = (
                f"✅ **Evolution Complete**\n\n"
                f"📊 Strategies Evaluated: {report.strategies_evaluated}\n"
                f"👑 Top Performers: {len(report.top_performers)}\n"
                f"🗑️ Underperformers: {len(report.underperformers)}\n"
                f"🆕 New Mutations: {len(report.new_mutations)}\n\n"
            )
            
            if report.top_performers:
                msg += "🏆 **Top Strategies:**\n"
                for i, s in enumerate(report.top_performers[:3], 1):
                    msg += f"{i}. {s.name} (fitness: {s.fitness_score:.0%})\n"
                msg += "\n"
            
            if report.new_mutations:
                msg += "🆕 **New Mutations:**\n"
                for m in report.new_mutations[:3]:
                    msg += f"• {m.child_strategy.name}\n"
                    msg += f"  Mutations: {', '.join(m.mutations_applied)}\n"
                msg += "\n"
            
            if report.recommendations:
                msg += "💡 **Recommendations:**\n"
                for rec in report.recommendations[:3]:
                    msg += f"• {rec}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in evolve: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def strategies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show all active strategies ranked by performance.
        
        Usage: /strategies [type]
        Types: engagement, content, timing, targeting, tone
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        filter_type = None
        if context.args:
            type_arg = context.args[0].lower()
            try:
                filter_type = StrategyType(type_arg)
            except ValueError:
                await update.message.reply_text(
                    f"❌ Unknown type: {type_arg}\n"
                    "Available: engagement, content, timing, targeting, tone"
                )
                return
        
        try:
            evolver = self._get_evolver()
            strategies_by_type = evolver.get_strategies_ranked()
            
            msg = "🧬 **Active Strategies**\n\n"
            
            types_to_show = [filter_type] if filter_type else list(StrategyType)
            
            for stype in types_to_show:
                strategies = strategies_by_type.get(stype, [])
                
                if not strategies:
                    continue
                
                msg += f"**{stype.value.upper()}** ({len(strategies)} strategies)\n"
                
                for i, s in enumerate(strategies[:5], 1):
                    status = "🟢" if s.fitness_score > 0.7 else "🟡" if s.fitness_score > 0.4 else "🔴"
                    msg += f"{status} {i}. {s.name}\n"
                    msg += f"   Uses: {s.times_used} | Success: {s.success_rate:.0%} | Fitness: {s.fitness_score:.0%}\n"
                    if s.parent_id:
                        msg += f"   Parent: {s.parent_id[:20]}...\n"
                    msg += "\n"
                
                if len(strategies) > 5:
                    msg += f"_... and {len(strategies) - 5} more_\n"
                
                msg += "\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in strategies: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Return command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('reflection_status', self.reflection_status),
            CommandHandler('reflection_log', self.reflection_log),
            CommandHandler('reflection_tune', self.reflection_tune),
            CommandHandler('evolve', self.evolve),
            CommandHandler('strategies', self.strategies),
        ]


# Singleton
_reflection_commands_instance = None


def get_reflection_commands(telegram_plugin=None):
    """Get or create ReflectionCommands singleton"""
    global _reflection_commands_instance
    if _reflection_commands_instance is None and telegram_plugin is not None:
        _reflection_commands_instance = ReflectionCommands(telegram_plugin)
    return _reflection_commands_instance
