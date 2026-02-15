"""
Telegram Commands for Self-Extension Pipeline

Provides /extend, /skills_propose, /skills_generate, /skills_test, /skills_deploy
for owner to manage Alley's self-extension capabilities.

Part of AGI Core - Phase 4
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.agentic.skill_generator import get_skill_generator, SkillSpecification
from src.agentic.autonomous_coder import get_autonomous_coder, GeneratedSkill
from src.agentic.skill_tester import get_skill_tester, SkillValidationReport
from src.agentic.goal_manager import get_goal_manager, GoalStatus

logger = logging.getLogger(__name__)


class ExtendCommands:
    """Telegram commands for self-extension pipeline"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._skill_generator = None
        self._coder = None
        self._tester = None
        self._goal_manager = None
    
    def _get_skill_generator(self):
        if self._skill_generator is None:
            self._skill_generator = get_skill_generator()
        return self._skill_generator
    
    def _get_coder(self):
        if self._coder is None:
            self._coder = get_autonomous_coder()
        return self._coder
    
    def _get_tester(self):
        if self._tester is None:
            self._tester = get_skill_tester()
        return self._tester
    
    def _get_goal_manager(self):
        if self._goal_manager is None:
            self._goal_manager = get_goal_manager()
        return self._goal_manager
    
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
    
    async def extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Main self-extension command - full pipeline.
        
        Usage: /extend <goal_id>
        Runs: propose → generate → test → deploy
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /extend <goal_id>\n\n"
                "Full pipeline: propose → generate → test → deploy"
            )
            return
        
        goal_id = context.args[0]
        
        await update.message.reply_text(f"🚀 Starting full extension pipeline for goal `{goal_id}`...")
        
        try:
            # Step 1: Generate skill spec
            await update.message.reply_text("📋 Step 1/4: Generating skill specification...")
            
            goal_manager = self._get_goal_manager()
            goal = goal_manager.get_goal(goal_id)
            
            if not goal:
                await update.message.reply_text(f"❌ Goal `{goal_id}` not found")
                return
            
            if goal.status != GoalStatus.APPROVED:
                await update.message.reply_text(
                    f"⚠️ Goal must be approved first.\n"
                    f"Use /goals_approve {goal_id}"
                )
                return
            
            generator = self._get_skill_generator()
            spec = generator.generate_from_goal(goal)
            
            if not spec:
                await update.message.reply_text("❌ Failed to generate skill specification")
                return
            
            await update.message.reply_text(
                f"✅ Skill spec generated: `{spec.id}`\n"
                f"Complexity: {spec.complexity}\n"
                f"Est. lines: {spec.estimated_lines}"
            )
            
            # Step 2: Generate code
            await update.message.reply_text("💻 Step 2/4: Generating code...")
            
            coder = self._get_coder()
            skill = coder.generate_skill(spec)
            
            if skill.status == 'failed':
                await update.message.reply_text(
                    f"❌ Code generation failed:\n"
                    f"{chr(10).join(skill.errors[:3])}"
                )
                return
            
            await update.message.reply_text(
                f"✅ Code generated: {len(skill.files_created)} files\n"
                f"Path: `{skill.skill_path}`"
            )
            
            # Step 3: Test
            await update.message.reply_text("🧪 Step 3/4: Testing skill...")
            
            tester = self._get_tester()
            report = tester.validate_skill(skill)
            
            status_emoji = "✅" if report.overall_passed else "❌"
            await update.message.reply_text(
                f"{status_emoji} Test Results:\n"
                f"- Syntax: {'✅' if report.syntax_valid else '❌'}\n"
                f"- Security: {'✅' if report.security_passed else '❌'}\n"
                f"- Import: {'✅' if report.can_import else '❌'}\n"
                f"- Tests: {report.pass_rate:.0%} pass rate\n\n"
                f"Errors: {len(report.errors)}\n"
                f"Warnings: {len(report.warnings)}"
            )
            
            if not report.overall_passed:
                errors_msg = "\n".join(report.errors[:5])
                await update.message.reply_text(
                    f"❌ Tests failed. Errors:\n```\n{errors_msg[:1000]}\n```"
                )
                return
            
            # Step 4: Deploy
            await update.message.reply_text("🚀 Step 4/4: Deploying skill...")
            
            # TODO: Implement hot-loading deployment
            # For now, manual deployment needed
            
            await update.message.reply_text(
                f"✅ **Extension Complete!**\n\n"
                f"Skill: `{spec.id}`\n"
                f"Location: `{skill.skill_path}`\n\n"
                f"📦 To deploy:\n"
                f"1. Review generated code\n"
                f"2. Add to plugins.json\n"
                f"3. /plugins_reload"
            )
            
        except Exception as e:
            logger.error(f"Extend error: {e}")
            await update.message.reply_text(f"❌ Extension failed: {e}")
    
    async def skills_propose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Propose skills from approved goals.
        
        Usage: /skills_propose [goal_id]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        try:
            goal_manager = self._get_goal_manager()
            generator = self._get_skill_generator()
            
            # Get approved goals without skills
            goals = goal_manager.get_goals(status=GoalStatus.APPROVED)
            
            if not goals:
                await update.message.reply_text("📭 No approved goals waiting for skill generation")
                return
            
            msg = "📝 **Skill Proposals**\n\n"
            
            for goal in goals[:5]:
                spec = generator.generate_from_goal(goal)
                if spec:
                    msg += (
                        f"📦 **{spec.name}**\n"
                        f"   ID: `{spec.id}`\n"
                        f"   Complexity: {spec.complexity}\n"
                        f"   Est. lines: {spec.estimated_lines}\n"
                        f"   Risk: {spec.risk_level}\n\n"
                    )
            
            msg += "🚀 Generate with `/extend <goal_id>`"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Skills propose error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def skills_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all generated skills"""
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        try:
            coder = self._get_coder()
            skills = coder.list_generated_skills()
            
            if not skills:
                await update.message.reply_text("📭 No skills generated yet")
                return
            
            msg = "💻 **Generated Skills**\n\n"
            
            for skill in skills[:10]:
                status_emoji = "✅" if skill.status == 'generated' else "🔄"
                msg += (
                    f"{status_emoji} {skill.skill_name}\n"
                    f"   ID: `{skill.spec_id}`\n"
                    f"   Files: {len(skill.files_created)}\n"
                    f"   Status: {skill.status}\n\n"
                )
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Skills list error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def skills_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Test a generated skill.
        
        Usage: /skills_test <skill_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /skills_test <skill_id>")
            return
        
        skill_id = context.args[0]
        
        try:
            coder = self._get_coder()
            tester = self._get_tester()
            
            skill = coder.get_skill_status(skill_id)
            if not skill:
                await update.message.reply_text(f"❌ Skill `{skill_id}` not found")
                return
            
            await update.message.reply_text(f"🧪 Testing skill `{skill_id}`...")
            
            report = tester.validate_skill(skill)
            
            # Build detailed report
            msg = (
                f"📊 **Test Report: {skill.skill_name}**\n\n"
                f"**Overall:** {'✅ PASSED' if report.overall_passed else '❌ FAILED'}\n\n"
                f"**Checks:**\n"
                f"- Syntax: {'✅' if report.syntax_valid else '❌'}\n"
                f"- Security: {'✅' if report.security_passed else '❌'}\n"
                f"- Import: {'✅' if report.can_import else '❌'}\n"
                f"- Tests: {report.pass_rate:.0%} ({len(report.test_results)} tests)\n\n"
            )
            
            if report.errors:
                msg += f"**Errors ({len(report.errors)}):**\n"
                for err in report.errors[:3]:
                    msg += f"- {err[:80]}...\n"
                msg += "\n"
            
            if report.warnings:
                msg += f"**Warnings ({len(report.warnings)}):**\n"
                for warn in report.warnings[:3]:
                    msg += f"- {warn[:80]}...\n"
            
            await update.message.reply_text(msg[:4000])
            
        except Exception as e:
            logger.error(f"Skills test error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def skills_deploy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Deploy a tested skill.
        
        Usage: /skills_deploy <skill_id>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /skills_deploy <skill_id>")
            return
        
        skill_id = context.args[0]
        
        await update.message.reply_text(
            f"🚀 Deploy skill `{skill_id}`...\n\n"
            f"Note: Auto-deployment coming soon.\n"
            f"For now, add skill to plugins.json manually."
        )
    
    def get_handlers(self):
        """Get command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('extend', self.extend),
            CommandHandler('skills_propose', self.skills_propose),
            CommandHandler('skills_list', self.skills_list),
            CommandHandler('skills_test', self.skills_test),
            CommandHandler('skills_deploy', self.skills_deploy),
        ]


# Convenience function
def register_extend_commands(dispatcher, telegram_plugin=None):
    """Register all extend commands with dispatcher"""
    commands = ExtendCommands(telegram_plugin)
    for handler in commands.get_handlers():
        dispatcher.add_handler(handler)
    logger.info("🚀 Extend commands registered")
