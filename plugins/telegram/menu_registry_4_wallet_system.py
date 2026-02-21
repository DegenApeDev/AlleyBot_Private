"""
menu_registry_4_wallet_system.py — Registry section 4: Wallet & On-Chain, DeFi, MCP, A2A, ERC-8004, Synergy, System.

Tuple format per command:
    "cmd_name": (cat_key, "Short description", "usage string", "args hint", "module")
"""

from typing import Dict, Tuple

# (cat, desc, usage, args, module)
REGISTRY_4: Dict[str, Tuple[str, str, str, str, str]] = {

    # -----------------------------------------------------------------------
    # WALLET & ON-CHAIN (Base)
    # -----------------------------------------------------------------------
    "wallet":               ("wallet", "Show wallet info and balances",                  "/wallet",                               "",                   "intelligent_commands.py"),
    "balance":              ("wallet", "Show token balances",                            "/balance",                              "",                   "intelligent_commands.py"),
    "block":                ("wallet", "Show current block info",                        "/block",                                "",                   "intelligent_commands.py"),
    "track":                ("wallet", "Track a token by symbol",                        "/track [symbol]",                       "[symbol]",           "intelligent_commands.py"),
    "tx":                   ("wallet", "Look up a transaction by hash",                  "/tx [hash]",                            "[hash]",             "intelligent_commands.py"),
    "activity":             ("wallet", "Show recent on-chain activity",                  "/activity",                             "",                   "intelligent_commands.py"),
    "onchain":              ("wallet", "Show on-chain status overview",                  "/onchain",                              "",                   "intelligent_commands.py"),
    "base_balance":         ("wallet", "Show Base wallet token balances",                "/base_balance",                         "",                   "intelligent_commands.py"),
    "base_eth_balance":     ("wallet", "Show Base ETH balance",                          "/base_eth_balance",                     "",                   "intelligent_commands.py"),
    "base_tokens":          ("wallet", "List all tracked Base tokens",                   "/base_tokens",                          "",                   "intelligent_commands.py"),
    "add_base_token":       ("wallet", "Add a token to Base tracking list",              "/add_base_token [address]",             "[address]",          "intelligent_commands.py"),
    "base_wallet_summary":  ("wallet", "Full Base wallet summary",                       "/base_wallet_summary",                  "",                   "intelligent_commands.py"),
    "contract_balance":     ("wallet", "Check balance of a specific contract",           "/contract_balance [address]",           "[address]",          "intelligent_commands.py"),
    "multi_contract_balance":("wallet","Check balances across multiple contracts",       "/multi_contract_balance [addresses]",   "[addresses]",        "intelligent_commands.py"),
    "token_stats":          ("wallet", "Show LLM token usage and costs",                 "/token_stats",                          "",                   "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # WALLET & ON-CHAIN (Solana)
    # -----------------------------------------------------------------------
    "solana_balance":         ("wallet", "Show Solana wallet balances",                  "/solana_balance",                       "",                   "intelligent_commands.py"),
    "solana_supported_tokens": ("wallet", "List supported Solana tokens",               "/solana_supported_tokens",              "",                   "intelligent_commands.py"),
    "add_solana_token":      ("wallet", "Add a token to Solana tracking list",           "/add_solana_token [address]",           "[address]",          "intelligent_commands.py"),
    "solana_wallet_summary": ("wallet", "Full Solana wallet summary",                    "/solana_wallet_summary",                "",                   "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # DEFI & SWAPS
    # -----------------------------------------------------------------------
    "swap_quote":           ("defi", "Get a swap quote for two tokens",                  "/swap_quote [from] [to] [amount]",      "[from] [to] [amt]",  "intelligent_commands.py"),
    "compare_aggregators":  ("defi", "Compare swap prices across aggregators",           "/compare_aggregators [from] [to] [amt]","[from] [to] [amt]",  "intelligent_commands.py"),
    "swap_tokens":          ("defi", "Execute a token swap",                             "/swap_tokens [from] [to] [amount]",     "[from] [to] [amt]",  "intelligent_commands.py"),
    "supported_tokens":     ("defi", "List supported tokens for swaps",                  "/supported_tokens",                     "",                   "intelligent_commands.py"),
    "fluid_positions":      ("defi", "Show Fluid protocol positions",                    "/fluid_positions",                      "",                   "intelligent_commands.py"),
    "fluid_earnings":       ("defi", "Show Fluid protocol earnings",                     "/fluid_earnings",                       "",                   "intelligent_commands.py"),
    "fluid_stats":          ("defi", "Show Fluid protocol statistics",                   "/fluid_stats",                          "",                   "intelligent_commands.py"),
    "fluid_apr":            ("defi", "Show Fluid protocol APR rates",                    "/fluid_apr",                            "",                   "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # MCP (Model Context Protocol)
    # -----------------------------------------------------------------------
    "mcp_status":   ("system", "Show MCP server connection status",   "/mcp_status",              "",         "intelligent_commands.py"),
    "mcp_search":   ("system", "Search via MCP tools",                "/mcp_search [query]",      "[query]",  "intelligent_commands.py"),
    "mcp_research": ("system", "Run deep research via MCP",           "/mcp_research [topic]",    "[topic]",  "intelligent_commands.py"),
    "mcp_analyze":  ("system", "Analyze data via MCP tools",          "/mcp_analyze [data]",      "[data]",   "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # A2A PROTOCOL
    # -----------------------------------------------------------------------
    "a2a_status": ("a2a", "Show A2A server status",          "/a2a_status",  "",  "intelligent_commands.py"),
    "a2a_start":  ("a2a", "Start the A2A server",            "/a2a_start",   "",  "intelligent_commands.py"),
    "a2a_stop":   ("a2a", "Stop the A2A server",             "/a2a_stop",    "",  "intelligent_commands.py"),
    "a2a_tasks":  ("a2a", "List available A2A tasks",        "/a2a_tasks",   "",  "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # ERC-8004 AGENT CARD
    # -----------------------------------------------------------------------
    "erc8004_rebuild": ("a2a", "Rebuild agent card from live plugins",     "/erc8004_rebuild",  "",  "intelligent_commands.py"),
    "erc8004_preview": ("a2a", "Preview agent card (dry run)",             "/erc8004_preview",  "",  "intelligent_commands.py"),
    "erc8004_update":  ("a2a", "Push agent card on-chain (costs gas)",     "/erc8004_update",   "",  "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # SYNERGY GATE (Tier 2 Integrity)
    # -----------------------------------------------------------------------
    "validate":  ("synergy", "Test SyMod validation for an action",      "/validate [action]",  "[action]",  "synergy_commands.py"),
    "integrity": ("synergy", "Show geometric integrity report",           "/integrity",          "",          "synergy_commands.py"),
    "attest":    ("synergy", "Generate ERC-8004 attestation for a task", "/attest [task_id]",   "[task_id]", "synergy_commands.py"),
    "synergy":   ("synergy", "Show Tier 2 Synergy Gate status",          "/synergy",            "",          "synergy_commands.py"),

    # -----------------------------------------------------------------------
    # SYSTEM & ADMIN
    # -----------------------------------------------------------------------
    "status":           ("system", "Show full platform status",                    "/status",           "",  "conversational_ai.py"),
    "reload":           ("system", "Reload all plugins without restart",           "/reload",           "",  "telegram.py"),
    "console_monitor":  ("system", "Toggle console error monitoring",              "/console_monitor",  "",  "telegram.py"),
    "console_stats":    ("system", "Show console detection statistics",            "/console_stats",    "",  "telegram.py"),
    "pending_messages": ("system", "Process pending queued messages",              "/pending_messages", "",  "telegram.py"),
    "help":             ("system", "Show help menu",                               "/help",             "",  "intelligent_commands.py"),
    "menu":             ("system", "Open the interactive command menu",            "/menu",             "",  "menu_handlers.py"),
    "menu_debug":       ("system", "Show full menu structure for debugging",       "/menu_debug",       "",  "menu_handlers.py"),
}
