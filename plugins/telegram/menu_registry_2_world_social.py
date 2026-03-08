"""
menu_registry_2_world_social.py — Registry section 2: World State & Intelligence, Social Platforms.

Tuple format per command:
    "cmd_name": (cat_key, "Short description", "usage string", "args hint", "module")
"""

from typing import Dict, Tuple

# (cat, desc, usage, args, module)
REGISTRY_2: Dict[str, Tuple[str, str, str, str, str]] = {

    # -----------------------------------------------------------------------
    # WORLD STATE & INTELLIGENCE
    # -----------------------------------------------------------------------
    "world_status":     ("world", "Show World State memory statistics",              "/world_status",                  "",               "intelligent_commands.py"),
    "world_entity":     ("world", "Show details for a specific entity",              "/world_entity [entity_id]",      "[entity_id]",    "intelligent_commands.py"),
    "world_facts":      ("world", "Show facts stored for an entity",                 "/world_facts [entity_id]",       "[entity_id]",    "intelligent_commands.py"),
    "world_relations":  ("world", "Show relationships for an entity",                "/world_relations [entity_id]",   "[entity_id]",    "intelligent_commands.py"),
    "world_search":     ("world", "Search entities in the World State",              "/world_search [query]",          "[query]",        "intelligent_commands.py"),
    "world_events":     ("world", "Show recent world events",                        "/world_events",                  "",               "intelligent_commands.py"),
    "world_trends":     ("world", "Show trending topics in World State",             "/world_trends",                  "",               "intelligent_commands.py"),
    "world_cleanup":    ("world", "Clean up expired World State data",               "/world_cleanup",                 "",               "intelligent_commands.py"),
    "brain_world_sync": ("world", "Sync brain state with World State",               "/brain_world_sync",              "",               "intelligent_commands.py"),
    "trends":           ("world", "Show trending topics from intelligence engine",   "/trends",                        "",               "intelligence_commands.py"),
    "influencers":      ("world", "Show top influencers detected",                   "/influencers",                   "",               "intelligence_commands.py"),
    "predict":          ("world", "Generate a prediction for a topic",               "/predict [topic]",               "[topic]",        "intelligence_commands.py"),
    "anomalies":        ("world", "Show detected anomalies",                         "/anomalies",                     "",               "intelligence_commands.py"),
    "sentiment":        ("world", "Show sentiment analysis for a topic",             "/sentiment [topic]",             "[topic]",        "intelligence_commands.py"),
    "patterns":         ("world", "Show detected behavioral patterns",               "/patterns",                      "",               "intelligence_commands.py"),
    "intel":            ("world", "Show full intelligence summary",                  "/intel",                         "",               "intelligence_commands.py"),
    "causal":           ("world", "Show causal analysis summary",                    "/causal",                        "",               "causal_commands.py"),
    "why":              ("world", "Explain why an event occurred",                   "/why [event description]",       "[event]",        "causal_commands.py"),
    "whatif":           ("world", "Run a what-if counterfactual analysis",           "/whatif [scenario]",             "[scenario]",     "causal_commands.py"),
    "root_cause":       ("world", "Find root cause of an issue",                     "/root_cause [issue]",            "[issue]",        "causal_commands.py"),
    "attribution":      ("world", "Attribute outcomes to contributing factors",      "/attribution [outcome]",         "[outcome]",      "causal_commands.py"),

    # -----------------------------------------------------------------------
    # SOCIAL PLATFORMS — MOLTX / SYMOD / CONTENT
    # -----------------------------------------------------------------------
    "moltx_post":              ("social", "Post to Moltx",                                    "/moltx_post [topic]",                       "[topic]",              "intelligent_commands.py"),
    "moltx_feed":              ("social", "Browse the Moltx feed",                            "/moltx_feed",                               "",                     "intelligent_commands.py"),
    "moltx_engage":            ("social", "Engage with Moltx feed posts",                     "/moltx_engage [count]",                     "[count]",              "intelligent_commands.py"),
    "moltx_trending":          ("social", "Show trending topics on Moltx",                    "/moltx_trending",                           "",                     "intelligent_commands.py"),
    "moltx_claim":             ("social", "Verify identity via an X tweet URL",               "/moltx_claim [tweet_url]",                  "[tweet_url]",          "intelligent_commands.py"),
    "moltx_debug":             ("social", "Debug Moltx plugin state",                         "/moltx_debug",                              "",                     "intelligent_commands.py"),
    "moltx_status":            ("social", "Show Moltx plugin status",                         "/moltx_status",                             "",                     "intelligent_commands.py"),
    "moltx_check_reward":      ("social", "Check USDC reward eligibility",                    "/moltx_check_reward",                       "",                     "intelligent_commands.py"),
    "moltx_claim_reward":      ("social", "Claim USDC reward",                                "/moltx_claim_reward",                       "",                     "intelligent_commands.py"),
    "moltchan_post":           ("social", "Post to MoltChan (legacy)",                        "/moltchan_post [topic]",                    "[topic]",              "new_commands.py"),
    "symod_start":             ("social", "Start the SyMod-driven MoltX social agent",        "/symod_start",                              "",                     "intelligent_commands.py"),
    "symod_stop":              ("social", "Stop the SyMod-driven agent",                      "/symod_stop",                               "",                     "intelligent_commands.py"),
    "symod_status":            ("social", "Check SyMod agent status",                         "/symod_status",                             "",                     "intelligent_commands.py"),
    "symod_cycle":             ("social", "Run one manual SyMod cycle",                       "/symod_cycle",                              "",                     "intelligent_commands.py"),
    "symod_config":            ("social", "View or adjust SyMod configuration",               "/symod_config",                             "",                     "intelligent_commands.py"),
    "calendar":                ("social", "Show content calendar status",                     "/calendar",                                 "",                     "intelligent_commands.py"),
    "conversations":           ("social", "Show active conversation threads",                 "/conversations",                            "",                     "intelligent_commands.py"),
    "personality":             ("social", "Show or set platform personality",                 "/personality [platform]",                   "[platform]",           "intelligent_commands.py"),
    "insights":                ("social", "Show content performance insights",                "/insights",                                 "",                     "intelligent_commands.py"),
    "check_engagement":        ("social", "Check engagement on tracked posts",                "/check_engagement",                         "",                     "intelligent_commands.py"),
    "tracked_posts":           ("social", "Show tracked posts and engagement scores",         "/tracked_posts",                            "",                     "intelligent_commands.py"),
    "generate_image":          ("social", "Generate an AI image with Grok",                   "/generate_image [prompt]",                  "[prompt]",             "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # CRYPTO PRICES
    # -----------------------------------------------------------------------
    "crypto_price":    ("social", "Check price for a single coin (btc, eth, sol...)", "/crypto_price [symbol]",        "[symbol]",         "intelligent_commands.py"),
    "crypto_prices":   ("social", "Check multiple coin prices at once",               "/crypto_prices [list]",         "[btc,eth,sol]",    "intelligent_commands.py"),
    "crypto_trending": ("social", "Show trending coins",                              "/crypto_trending",              "",                 "intelligent_commands.py"),
}
