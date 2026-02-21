"""
menu_builders.py — Functions that build InlineKeyboardMarkup objects for the menu system.

Callback data prefixes used throughout:
    "cat:<key>"   — user tapped a category button on the main menu
    "cmd:<name>"  — user tapped a command button inside a category view
    "back:main"   — user tapped the ← Back button to return to main menu
    "noop"        — no-op button (e.g. decorative header row)
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from plugins.telegram.menu_registry import COMMAND_REGISTRY, get_commands_for_category
from plugins.telegram.menu_categories import CATEGORIES, CATEGORY_ORDER


# ---------------------------------------------------------------------------
# Main menu — one button per category, 2 columns
# ---------------------------------------------------------------------------

def build_main_menu() -> InlineKeyboardMarkup:
    """Build the top-level category selection keyboard."""
    buttons: List[InlineKeyboardButton] = []

    for key in CATEGORY_ORDER:
        if key not in CATEGORIES:
            continue
        emoji, label, _ = CATEGORIES[key]
        # Only show categories that have at least one command
        if not get_commands_for_category(key):
            continue
        buttons.append(
            InlineKeyboardButton(f"{emoji} {label}", callback_data=f"cat:{key}")
        )

    # Arrange into 2-column rows
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# Category view — list of command buttons + back button
# ---------------------------------------------------------------------------

def build_category_menu(cat_key: str) -> InlineKeyboardMarkup:
    """Build the command list keyboard for a given category."""
    commands = get_commands_for_category(cat_key)
    rows: List[List[InlineKeyboardButton]] = []

    for cmd_name in sorted(commands.keys()):
        _, desc, _, args, _ = commands[cmd_name]
        # Show args hint on button if present, otherwise just the command name
        label = f"/{cmd_name}" if not args else f"/{cmd_name} {args}"
        # Truncate long labels so they fit in a button
        if len(label) > 40:
            label = label[:37] + "…"
        rows.append([
            InlineKeyboardButton(label, callback_data=f"cmd:{cmd_name}")
        ])

    # Back button at the bottom
    rows.append([InlineKeyboardButton("← Back to Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# Command detail view — shows usage info + back-to-category button
# ---------------------------------------------------------------------------

def build_command_detail(cmd_name: str) -> InlineKeyboardMarkup:
    """Build the keyboard shown after a user taps a specific command button."""
    entry = COMMAND_REGISTRY.get(cmd_name)
    if not entry:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("← Back to Menu", callback_data="back:main")
        ]])

    cat_key = entry[0]
    # Back button returns to the category this command belongs to
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("← Back to Category", callback_data=f"cat:{cat_key}")
    ]])


# ---------------------------------------------------------------------------
# Helper — format command detail message text
# ---------------------------------------------------------------------------

def format_command_detail(cmd_name: str) -> str:
    """Return the message text shown when a user taps a command button."""
    entry = COMMAND_REGISTRY.get(cmd_name)
    if not entry:
        return f"❓ Unknown command: `/{cmd_name}`"

    cat_key, desc, usage, args, module = entry
    cat_emoji, cat_label, _ = CATEGORIES.get(cat_key, ("📋", cat_key, ""))

    lines = [
        f"*/{cmd_name}*",
        f"_{desc}_",
        "",
        f"*Usage:* `{usage}`",
    ]
    if args:
        lines.append(f"*Args:* `{args}`")
    lines += [
        f"*Category:* {cat_emoji} {cat_label}",
        f"*Module:* `{module}`",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper — format main menu intro text
# ---------------------------------------------------------------------------

def format_main_menu_text() -> str:
    """Return the intro message shown above the main menu keyboard."""
    total = len(COMMAND_REGISTRY)
    return (
        f"🦞 *AlleyBot Command Menu*\n"
        f"_{total} commands across {len(CATEGORY_ORDER)} categories_\n\n"
        "Tap a category to browse its commands."
    )


# ---------------------------------------------------------------------------
# Helper — format category header text
# ---------------------------------------------------------------------------

def format_category_text(cat_key: str) -> str:
    """Return the header message shown above a category's command list."""
    emoji, label, desc = CATEGORIES.get(cat_key, ("📋", cat_key, ""))
    commands = get_commands_for_category(cat_key)
    return (
        f"{emoji} *{label}*\n"
        f"_{desc}_\n\n"
        f"{len(commands)} command(s) — tap one for usage details."
    )
