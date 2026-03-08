"""
menu_categories.py — Category definitions for AlleyBot's inline menu system.

Each category entry:
    key:   matches the cat field in COMMAND_REGISTRY tuples
    emoji: displayed on the main menu button
    label: human-readable name shown on the button and category header
    desc:  one-line description shown at the top of the category view
"""

from typing import Dict, Tuple

# (emoji, label, desc)
CATEGORIES: Dict[str, Tuple[str, str, str]] = {
    "agi":       ("🧠", "AGI Meta-Brain",          "Autonomous brain, think cycles, and AI chat"),
    "goals":     ("🎯", "Goals & Plans",            "Goal management and execution planning"),
    "reflection":("🔄", "Reflection & Self-Improve","Self-reflection, evolution, and skill management"),
    "world":     ("🌍", "World State & Intel",      "World memory, intelligence analysis, and causal reasoning"),
    "social":    ("📢", "Social Platforms",         "Moltx, SyMod, content strategy, and crypto prices"),
    "clawbr":    ("🦞", "Clawbr",                  "AI social network — posts, debates, tokens, and tournaments"),
    "clawstr":   ("🦀", "Clawstr",                 "Nostr AI social network — posts, zaps, and notifications"),
    "clawnch":   ("🚀", "Clawnch",                 "Token launches, Molten network, and Twitter integration"),
    "clawchess": ("♟️", "ClawChess",               "On-chain chess — matchmaking, moves, and leaderboard"),
    "wallet":    ("💰", "Wallet & On-Chain",        "Base wallet balances, transactions, and token tracking"),
    "defi":      ("💱", "DeFi & Swaps",            "Swap quotes, aggregator comparison, and Fluid protocol"),
    "a2a":       ("🤝", "A2A & ERC-8004",          "Agent-to-agent protocol and on-chain agent card"),
    "synergy":   ("🔐", "Synergy Gate",            "Tier 2 integrity validation and attestation"),
    "system":    ("⚙️", "System & Admin",          "Status, reload, console monitor, and menu tools"),
}

# Ordered list of category keys — controls display order on the main menu
CATEGORY_ORDER = [
    "agi",
    "goals",
    "reflection",
    "world",
    "social",
    "clawbr",
    "clawstr",
    "clawnch",
    "clawchess",
    "wallet",
    "defi",
    "a2a",
    "synergy",
    "system",
]
