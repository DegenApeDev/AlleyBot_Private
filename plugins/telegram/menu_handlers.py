"""
menu_handlers.py — Command and callback query handlers for the inline menu system.

Registers:
    /menu        — open the interactive category menu
    /help        — short intro message with an "Open Menu" button (replaces old /help)
    /menu_debug  — dump full menu structure as text (admin debug tool)

Callback query prefixes handled:
    cat:<key>    — show command list for a category
    cmd:<name>   — show usage detail for a specific command
    back:main    — return to the main menu
    noop         — silently acknowledge (no edit)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from plugins.telegram.menu_registry import COMMAND_REGISTRY, get_commands_for_category
from plugins.telegram.menu_categories import CATEGORIES, CATEGORY_ORDER
from plugins.telegram.menu_builders import (
    build_main_menu,
    build_category_menu,
    build_command_detail,
    format_main_menu_text,
    format_category_text,
    format_command_detail,
)

if TYPE_CHECKING:
    from plugins.telegram.telegram import Telegram

logger = logging.getLogger(__name__)


class MenuHandlers:
    """Encapsulates all menu-related command and callback handlers."""

    def __init__(self, telegram_plugin: "Telegram") -> None:
        self.tg = telegram_plugin

    # ------------------------------------------------------------------
    # Registration helper — call this from Telegram._setup_handlers()
    # ------------------------------------------------------------------

    def register(self) -> None:
        """Register all menu handlers onto the Application instance."""
        app = self.tg.application
        app.add_handler(CommandHandler("menu", self.cmd_menu))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("menu_debug", self.cmd_menu_debug))
        # Single callback router for all inline button presses
        app.add_handler(CallbackQueryHandler(self.callback_router))

    # ------------------------------------------------------------------
    # /menu — open the interactive category menu
    # ------------------------------------------------------------------

    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the main category menu."""
        if not await self.tg._verify_owner(update):
            return
        await update.message.reply_text(
            text=format_main_menu_text(),
            reply_markup=build_main_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ------------------------------------------------------------------
    # /help — short intro + button to open menu
    # ------------------------------------------------------------------

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a short help intro with an Open Menu button."""
        logger.info(f"🔍 /help command received from user {update.effective_user.id}")
        if not await self.tg._verify_owner(update):
            logger.warning(f"⛔ /help rejected - not owner")
            return
        logger.info("✅ /help verified, sending response...")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 Open Command Menu", callback_data="back:main")
        ]])
        await update.message.reply_text(
            text=(
                "🦞 *AlleyBot* — private AI agent\n\n"
                "Tap the button below to browse all commands interactively, "
                "or send any message to chat with the AI directly."
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("✅ /help response sent successfully")

    # ------------------------------------------------------------------
    # /menu_debug — dump full menu structure
    # ------------------------------------------------------------------

    async def cmd_menu_debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Dump the full menu structure as plain text for verification."""
        if not await self.tg._verify_owner(update):
            return

        lines = [f"🔍 *Menu Debug* — {len(COMMAND_REGISTRY)} total commands\n"]
        for key in CATEGORY_ORDER:
            if key not in CATEGORIES:
                continue
            emoji, label, _ = CATEGORIES[key]
            cmds = get_commands_for_category(key)
            lines.append(f"\n{emoji} *{label}* ({len(cmds)} commands)")
            for cmd in sorted(cmds.keys()):
                _, desc, _, args, _ = cmds[cmd]
                arg_str = f" `{args}`" if args else ""
                lines.append(f"  • `/{cmd}`{arg_str} — {desc}")

        # Telegram message limit is 4096 chars — split if needed
        full_text = "\n".join(lines)
        chunk_size = 4000
        for i in range(0, len(full_text), chunk_size):
            await update.message.reply_text(
                text=full_text[i:i + chunk_size],
                parse_mode=ParseMode.MARKDOWN,
            )

    # ------------------------------------------------------------------
    # Callback query router — handles all inline button presses
    # ------------------------------------------------------------------

    async def callback_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Route all inline keyboard callbacks to the correct handler."""
        query = update.callback_query

        # Always answer the callback to remove the loading spinner
        await query.answer()

        # Verify the user pressing buttons is the admin
        if self.tg.owner_user_id and query.from_user.id != self.tg.owner_user_id:
            await query.answer("🔒 Private bot.", show_alert=True)
            return

        data: str = query.data or ""

        try:
            if data == "noop":
                # Decorative button — do nothing
                return

            elif data == "back:main":
                # Return to the main category menu
                await self._edit_or_reply(
                    query,
                    text=format_main_menu_text(),
                    reply_markup=build_main_menu(),
                )

            elif data.startswith("cat:"):
                # Show command list for the selected category
                cat_key = data[4:]
                if cat_key not in CATEGORIES:
                    await query.answer("Unknown category.", show_alert=True)
                    return
                await self._edit_or_reply(
                    query,
                    text=format_category_text(cat_key),
                    reply_markup=build_category_menu(cat_key),
                )

            elif data.startswith("cmd:"):
                # Show usage detail for the selected command
                cmd_name = data[4:]
                await self._edit_or_reply(
                    query,
                    text=format_command_detail(cmd_name),
                    reply_markup=build_command_detail(cmd_name),
                )

            else:
                logger.warning("MenuHandlers: unhandled callback data: %r", data)

        except BadRequest as exc:
            # Silently ignore "message is not modified" errors from double-taps
            if "not modified" not in str(exc).lower():
                logger.error("MenuHandlers callback error: %s", exc)
        except Exception as exc:
            logger.error("MenuHandlers callback error: %s", exc)

    # ------------------------------------------------------------------
    # Internal helper — edit existing message or send a new one
    # ------------------------------------------------------------------

    async def _edit_or_reply(
        self,
        query,
        text: str,
        reply_markup: InlineKeyboardMarkup,
    ) -> None:
        """Edit the message that contains the inline keyboard, or send a new one."""
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )
        except BadRequest as exc:
            if "not modified" not in str(exc).lower():
                raise
