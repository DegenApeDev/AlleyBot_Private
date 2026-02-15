"""
Telegram Commands for Tier 2 Synergy Gate Validation

Provides /validate, /integrity, and /attest commands
for owner to test and monitor the SyMod cryptographic trust layer.

Part of AGI Core - Phase 8 (Synergy Audit)
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging
import json

logger = logging.getLogger(__name__)


class SynergyCommands:
    """Telegram commands for Tier 2 Synergy Gate validation"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
    
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
    
    async def validate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Test Synergy Gate validation on a thought/action.
        
        Usage: /validate <action description>
        Example: /validate Deploy liquidity mining strategy
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        # Get action description from args
        if not context.args:
            await update.message.reply_text(
                "🔐 **Synergy Gate Validation**\n\n"
                "Usage: `/validate <action description>`\n"
                "Example: `/validate Deploy liquidity mining strategy`\n\n"
                "Tests if an action passes Tier 2 cryptographic trust.",
                parse_mode='Markdown'
            )
            return
        
        action_desc = ' '.join(context.args)
        
        # Import here to avoid startup issues if not available
        try:
            from lib.synergy_gate import validate_action
        except ImportError:
            await update.message.reply_text(
                "❌ **Tier 2 framework not available**\n\n"
                "The Synergy Gate module is not loaded. Check logs.",
                parse_mode='Markdown'
            )
            return
        
        # Run validation
        await update.message.reply_text(f"🔐 Validating: _{action_desc[:50]}..._", parse_mode='Markdown')
        
        try:
            can_execute, reason, result = validate_action({
                'content': action_desc,
                'evidence_strength': 0.9,
                'urgency': 1.0,
                'recursion_depth': 0
            }, threshold=0.85)
            
            # Build response
            status_emoji = "✅" if can_execute else "❌"
            field_emoji = {
                'STABLE': '🟢',
                'VOLATILE': '🟡',
                'COLLAPSE': '🔴',
                'UNKNOWN': '⚪'
            }.get(result.field_status.value, '⚪')
            
            response = (
                f"{status_emoji} **Synergy Gate Result**\n\n"
                f"🎯 **Action**: `{action_desc[:40]}`\n"
                f"📊 **Confidence**: `{result.confidence:.3f}` (threshold: 0.85)\n"
                f"🔢 **Digital Root**: `{result.digital_root}`\n"
                f"{field_emoji} **Field Status**: `{result.field_status.value}`\n"
                f"⚡ **Impedance**: `{result.impedance:.2e}`\n"
                f"🔄 **RCA Triggered**: {'Yes' if result.rca_triggered else 'No'}\n\n"
            )
            
            if can_execute:
                response += "✅ **EXECUTION ALLOWED** - All checks passed"
            else:
                response += f"❌ **EXECUTION BLOCKED**\n📝 Reason: `{reason[:100]}`"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            await update.message.reply_text(f"❌ Validation failed: {str(e)}")
    
    async def integrity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show geometric integrity report of the codebase.
        
        Usage: /integrity
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        report_path = 'data/geometric_integrity_report.json'
        
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            status_emoji = {
                'STABLE': '🟢',
                'VOLATILE': '🟡',
                'COLLAPSE': '🔴'
            }.get(report['integrity_status'], '⚪')
            
            response = (
                f"📐 **Geometric Integrity Report**\n\n"
                f"{status_emoji} **Status**: `{report['integrity_status']}`\n"
                f"🔢 **Aggregate D(n)**: `{report['aggregate_digital_root']}`\n"
                f"📁 **Files Scanned**: `{report['total_files']}`\n"
                f"📏 **Total Lines**: `{report['total_lines']:,}`\n"
                f"⏰ **Generated**: `{report['report_generated'][:16]}`\n\n"
                f"🎯 **Root Distribution**:\n"
            )
            
            for root, count in sorted(report['root_distribution'].items(), key=lambda x: -x[1]):
                bar = '█' * min(10, count // 5)
                response += f"  D(n)={root}: {bar} ({count})\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except FileNotFoundError:
            await update.message.reply_text(
                "📐 **Integrity Report Not Found**\n\n"
                "Generate it first with:\n"
                "```\nvenv/bin/python scripts/generate_integrity_report.py\n```",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Integrity report error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def attest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Generate ERC-8004 attestation for a completed action.
        
        Usage: /attest <task_id>
        Example: /attest task_12345
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📜 **ERC-8004 Attestation**\n\n"
                "Usage: `/attest <task_id>`\n"
                "Example: `/attest task_12345`\n\n"
                "Generates cryptographic proof of execution.",
                parse_mode='Markdown'
            )
            return
        
        task_id = context.args[0]
        
        try:
            import sys
            from pathlib import Path
            import types
            # Workaround: import machinery hangs, use exec instead
            src_path = Path(__file__).parent.parent.parent
            module_path = src_path / 'src/agentic/erc8004_a2a_integration.py'
            
            if 'src.agentic.erc8004_a2a_integration' not in sys.modules:
                erc8004_module = types.ModuleType('erc8004_a2a_integration')
                erc8004_module.__file__ = str(module_path)
                with open(module_path, 'r') as f:
                    exec(f.read(), erc8004_module.__dict__)
                sys.modules['src.agentic.erc8004_a2a_integration'] = erc8004_module
            else:
                erc8004_module = sys.modules['src.agentic.erc8004_a2a_integration']
            
            validate_and_attest = erc8004_module.validate_and_attest
            
            attestation = validate_and_attest(
                task_id=task_id,
                inputs={'source': 'telegram_command'},
                outputs={'status': 'completed'},
                code_version='manual'
            )
            
            response = (
                f"📜 **Attestation Generated**\n\n"
                f"🆔 **ID**: `{attestation.attestation_id}`\n"
                f"🔗 **Task**: `{attestation.task_id}`\n"
                f"⏰ **Time**: `{attestation.timestamp[:16]}`\n"
                f"🔐 **Hash**: `{attestation.generate_full_hash()[:32]}...`\n\n"
                f"✅ Stored in local registry for on-chain submission."
            )
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except ImportError:
            await update.message.reply_text(
                "❌ **ERC-8004 module not available**\n\n"
                "Tier 2 framework not loaded.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Attestation error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def synergy_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show overall Tier 2 Synergy system status.
        
        Usage: /synergy
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        # Check what's available
        tier2_available = False
        gate_status = "❌ Not loaded"
        recursive_available = False
        erc8004_available = False
        
        try:
            from lib.synergy_gate import get_synergy_gate
            gate = get_synergy_gate()
            tier2_available = True
            gate_status = f"✅ Active (threshold={gate.confidence_threshold})"
        except:
            pass
        
        try:
            from src.agentic.recursive_strategy import RecursiveStrategyEngine
            recursive_available = True
        except:
            pass
        
        try:
            import sys
            from pathlib import Path
            import types
            # Workaround: import machinery hangs, use exec instead
            src_path = Path(__file__).parent.parent.parent
            module_path = src_path / 'src/agentic/erc8004_a2a_integration.py'
            
            erc8004_module = types.ModuleType('erc8004_a2a_integration')
            erc8004_module.__file__ = str(module_path)
            
            with open(module_path, 'r') as f:
                exec(f.read(), erc8004_module.__dict__)
            
            # Inject into sys.modules so future imports work
            sys.modules['src.agentic.erc8004_a2a_integration'] = erc8004_module
            ERC8004Registry = erc8004_module.ERC8004Registry
            erc8004_available = True
        except Exception as e:
            logger.debug(f"ERC-8004 not available: {e}")
            pass
        
        response = (
            f"🔐 **Tier 2 Synergy Status**\n\n"
            f"**Synergy Gate**: {gate_status}\n"
            f"**Recursive Strategy**: {'✅ Available' if recursive_available else '❌ Not loaded'}\n"
            f"**ERC-8004 Attestation**: {'✅ Available' if erc8004_available else '❌ Not loaded'}\n\n"
        )
        
        if tier2_available:
            response += (
                "📋 **Available Commands**:\n"
                "  • `/validate <action>` - Test SyMod validation\n"
                "  • `/integrity` - Show geometric report\n"
                "  • `/attest <task_id>` - Generate attestation\n"
                "  • `/synergy` - This status\n\n"
                "🛡️ **High-stakes actions are cryptographically gated.**"
            )
        else:
            response += "⚠️ Tier 2 framework not available. Check imports."
        
        await update.message.reply_text(response, parse_mode='Markdown')


# Command handler map for registration
COMMAND_HANDLERS = {
    'validate': 'validate',
    'integrity': 'integrity',
    'attest': 'attest',
    'synergy': 'synergy_status',
}
