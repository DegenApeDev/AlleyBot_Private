"""
menu_registry.py — Merges all 4 registry sections into a single COMMAND_REGISTRY dict.

Import this module everywhere you need the full command list.

Each entry value is a tuple:
    (cat_key, desc, usage, args_hint, module)

Sections:
    menu_registry_1_agi_goals.py        — AGI, Goals & Plans, Reflection
    menu_registry_2_world_social.py     — World State, Social / Moltx, Crypto
    menu_registry_3_clawbr_clawstr_clawnch.py — Clawbr, Clawstr, Clawnch, ClawChess
    menu_registry_4_wallet_system.py    — Wallet, DeFi, MCP, A2A, ERC-8004, Synergy, System
"""

from typing import Dict, Tuple

from plugins.telegram.menu_registry_1_agi_goals import REGISTRY_1
from plugins.telegram.menu_registry_2_world_social import REGISTRY_2
from plugins.telegram.menu_registry_3_clawbr_clawstr_clawnch import REGISTRY_3
from plugins.telegram.menu_registry_4_wallet_system import REGISTRY_4

# Full merged registry — (cat, desc, usage, args, module)
COMMAND_REGISTRY: Dict[str, Tuple[str, str, str, str, str]] = {
    **REGISTRY_1,
    **REGISTRY_2,
    **REGISTRY_3,
    **REGISTRY_4,
}

# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_commands_for_category(cat_key: str) -> Dict[str, Tuple[str, str, str, str, str]]:
    """Return all commands belonging to a given category key."""
    return {cmd: data for cmd, data in COMMAND_REGISTRY.items() if data[0] == cat_key}


def get_command(cmd: str) -> Tuple[str, str, str, str, str] | None:
    """Return the registry tuple for a single command, or None if not found."""
    return COMMAND_REGISTRY.get(cmd)
