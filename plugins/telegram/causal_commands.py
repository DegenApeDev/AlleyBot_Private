"""
Telegram Commands for Causal Analysis

Provides /causal, /why, /whatif, /root_cause commands
for owner to understand why things happen.

Part of AGI Core - Phase 5
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.agentic.causal_engine import get_causal_engine, CausalEngine

logger = logging.getLogger(__name__)


class CausalCommands:
    """Telegram commands for causal understanding"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._causal_engine = None
    
    def _get_causal_engine(self):
        if self._causal_engine is None:
            self._causal_engine = get_causal_engine()
        return self._causal_engine
    
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
    
    async def causal_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show causal analysis summary.
        
        Usage: /causal [hours]
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
            engine = self._get_causal_engine()
            summary = engine.get_causal_summary(hours=hours)
            
            msg = f"🔍 **Causal Analysis Summary (Last {hours}h)**\n\n"
            msg += f"📊 Observations Recorded: {summary['observations_recorded']}\n"
            msg += f"🔗 Causal Links Discovered: {summary['causal_links_discovered']}\n\n"
            
            if summary['top_correlations']:
                msg += "📈 **Top Correlations:**\n"
                for corr in summary['top_correlations'][:5]:
                    msg += f"• {corr['cause']} → {corr['effect']}\n"
                    msg += f"  Strength: {corr['strength']:.0%}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in causal_summary: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def why(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Analyze why an action had a specific outcome.
        
        Usage: /why <action_id> [outcome_type]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /why <action_id> [outcome_type]\n\n"
                "Example: /why abc123 high_engagement"
            )
            return
        
        action_id = context.args[0]
        outcome_type = context.args[1] if len(context.args) > 1 else "success"
        
        try:
            engine = self._get_causal_engine()
            causes = engine.find_causes(action_id, outcome_type)
            
            if not causes:
                await update.message.reply_text(
                    f"🤔 No clear causes found for `{action_id}`\n\n"
                    "Need more observations to establish causality."
                )
                return
            
            msg = f"🎯 **Why this outcome occurred**\n\n"
            msg += f"Action: `{action_id}`\n"
            msg += f"Outcome: {outcome_type}\n\n"
            msg += "**Probable Causes:**\n"
            
            for i, cause in enumerate(causes[:5], 1):
                msg += f"{i}. **{cause.cause_type}**\n"
                msg += f"   Strength: {cause.strength:.0%}\n"
                msg += f"   Confidence: {cause.confidence:.0%}\n"
                msg += f"   Evidence: {cause.evidence_count} observations\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in why: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def whatif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Counterfactual: "What if I had done X instead?"
        
        Usage: /whatif <action_id> <change>
        Example: /whatif abc123 time=night
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /whatif <action_id> <key=value>\n\n"
                "Examples:\n"
                "`/whatif abc123 time=night`\n"
                "`/whatif abc123 field_status=Volatile`\n"
                "`/whatif abc123 confidence_threshold=0.9`"
            )
            return
        
        action_id = context.args[0]
        change_str = context.args[1]
        
        # Parse key=value
        if '=' not in change_str:
            await update.message.reply_text("❌ Change must be in format key=value")
            return
        
        key, value = change_str.split('=', 1)
        
        # Try to parse as number/bool
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
        
        hypothetical_change = {key: value}
        
        try:
            engine = self._get_causal_engine()
            counterfactual = engine.simulate_counterfactual(action_id, hypothetical_change)
            
            msg = "🔄 **Counterfactual Analysis**\n\n"
            msg += f"**Actual:**\n"
            msg += f"Action: `{action_id}`\n"
            msg += f"Outcome: {counterfactual.actual_outcome}\n\n"
            
            msg += f"**Hypothetical Change:**\n"
            msg += f"{key} = {value}\n\n"
            
            msg += f"**Predicted Outcome:**\n"
            for k, v in counterfactual.predicted_outcome.items():
                msg += f"• {k}: {v}\n"
            
            msg += f"\n🎯 Confidence: {counterfactual.confidence:.0%}\n\n"
            
            # Compare
            if 'engagement' in counterfactual.actual_outcome:
                actual_eng = counterfactual.actual_outcome.get('engagement', 0)
                predicted_eng = counterfactual.predicted_outcome.get('engagement', actual_eng)
                diff = predicted_eng - actual_eng
                
                if diff > 0:
                    msg += f"📈 Would have performed {diff:.0f} points BETTER"
                elif diff < 0:
                    msg += f"📉 Would have performed {abs(diff):.0f} points WORSE"
                else:
                    msg += "➡️ Would have performed similarly"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
        except Exception as e:
            logger.error(f"Error in whatif: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def root_cause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Perform root cause analysis on an event.
        
        Usage: /root_cause <action_id> [depth]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /root_cause <action_id> [depth]\n\n"
                "Example: /root_cause abc123 3"
            )
            return
        
        action_id = context.args[0]
        depth = 3
        if len(context.args) > 1:
            try:
                depth = int(context.args[1])
                depth = max(1, min(5, depth))  # Clamp 1-5
            except ValueError:
                pass
        
        try:
            engine = self._get_causal_engine()
            analysis = engine.analyze_root_cause(action_id, depth=depth)
            
            msg = f"🔬 **Root Cause Analysis**\n\n"
            msg += f"Event: `{action_id}`\n"
            msg += f"Depth: {analysis.analysis_depth} levels\n"
            msg += f"Confidence: {analysis.confidence:.0%}\n\n"
            
            if analysis.root_causes:
                msg += "**Cause Chain:**\n"
                for i, cause in enumerate(analysis.root_causes, 1):
                    indent = "  " * cause['depth']
                    msg += f"{indent}{i}. {cause['cause_id']}\n"
                    msg += f"{indent}   Strength: {cause['strength']:.0%} | "
                    msg += f"Confidence: {cause['confidence']:.0%}\n"
            else:
                msg += "🔗 No causal chain found\n"
            
            if analysis.contributing_factors:
                msg += "\n**Contributing Factors:**\n"
                for factor in analysis.contributing_factors:
                    msg += f"• {factor}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in root_cause: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def attribution(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show impact attribution breakdown.
        
        Usage: /attribution <metric> [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /attribution <metric> [hours]\n\n"
                "Examples:\n"
                "`/attribution engagement 24`\n"
                "`/attribution success 48`"
            )
            return
        
        metric = context.args[0]
        hours = 24
        if len(context.args) > 1:
            try:
                hours = int(context.args[1])
            except ValueError:
                pass
        
        try:
            engine = self._get_causal_engine()
            attribution = engine.get_impact_attribution(metric, hours)
            
            if not attribution:
                await update.message.reply_text(
                    f"📊 No attribution data for '{metric}' in last {hours}h"
                )
                return
            
            msg = f"📊 **Impact Attribution: {metric}**\n"
            msg += f"Time window: {hours}h\n\n"
            msg += "**Top Contributing Factors:**\n"
            
            for factor, contribution in list(attribution.items())[:10]:
                bar = "█" * int(contribution * 20)
                msg += f"{bar} {contribution:.0%} {factor}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in attribution: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Return command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('causal', self.causal_summary),
            CommandHandler('why', self.why),
            CommandHandler('whatif', self.whatif),
            CommandHandler('root_cause', self.root_cause),
            CommandHandler('attribution', self.attribution),
        ]


# Singleton
_causal_commands_instance = None


def get_causal_commands(telegram_plugin=None):
    """Get or create CausalCommands singleton"""
    global _causal_commands_instance
    if _causal_commands_instance is None and telegram_plugin is not None:
        _causal_commands_instance = CausalCommands(telegram_plugin)
    return _causal_commands_instance
