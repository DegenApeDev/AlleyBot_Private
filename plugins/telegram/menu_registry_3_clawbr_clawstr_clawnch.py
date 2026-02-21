"""
menu_registry_3_clawbr_clawstr_clawnch.py — Registry section 3: Clawbr, Clawstr, Clawnch, ClawChess.

Tuple format per command:
    "cmd_name": (cat_key, "Short description", "usage string", "args hint", "module")
"""

from typing import Dict, Tuple

# (cat, desc, usage, args, module)
REGISTRY_3: Dict[str, Tuple[str, str, str, str, str]] = {

    # -----------------------------------------------------------------------
    # CLAWBR (AI Social Network)
    # -----------------------------------------------------------------------
    "clawbr_status":             ("clawbr", "Show Clawbr agent profile and stats",              "/clawbr_status",                                        "",                          "intelligent_commands.py"),
    "clawbr_post":               ("clawbr", "Create an intelligent post on Clawbr",             "/clawbr_post [content]",                                "[content]",                 "intelligent_commands.py"),
    "clawbr_reply":              ("clawbr", "Reply to a Clawbr post",                           "/clawbr_reply [post_id] [reply]",                       "[post_id] [reply]",         "intelligent_commands.py"),
    "clawbr_feed":               ("clawbr", "Browse the Clawbr global feed",                    "/clawbr_feed",                                          "",                          "intelligent_commands.py"),
    "clawbr_engage":             ("clawbr", "Run a full Clawbr engagement cycle",               "/clawbr_engage",                                        "",                          "intelligent_commands.py"),
    "clawbr_debates":            ("clawbr", "Show active and open debates",                     "/clawbr_debates",                                       "",                          "intelligent_commands.py"),
    "clawbr_create_debate":      ("clawbr", "Start a new debate",                               "/clawbr_create_debate [topic] [argument]",              "[topic] [argument]",        "intelligent_commands.py"),
    "clawbr_auto_debate":       ("clawbr", "Create debate with AI-generated opening",          "/clawbr_auto_debate [topic]",                           "[topic]",                   "intelligent_commands.py"),
    "clawbr_join_debate":        ("clawbr", "Join an open debate by slug",                      "/clawbr_join_debate [slug]",                            "[slug]",                    "intelligent_commands.py"),
    "clawbr_vote":               ("clawbr", "Vote on a completed debate",                       "/clawbr_vote [slug] [side] [reasoning]",                "[slug] [side] [reasoning]", "intelligent_commands.py"),
    "clawbr_vote_specific":      ("clawbr", "Vote on a specific debate entry",                  "/clawbr_vote_specific [debate_id] [side]",              "[debate_id] [side]",        "intelligent_commands.py"),
    "clawbr_check_voting":       ("clawbr", "Check voting eligibility for debates",             "/clawbr_check_voting",                                  "",                          "intelligent_commands.py"),
    "clawbr_completed_debates":  ("clawbr", "List debates ready for voting",                    "/clawbr_completed_debates",                             "",                          "intelligent_commands.py"),
    "clawbr_leaderboard":        ("clawbr", "Show top Clawbr agents",                           "/clawbr_leaderboard",                                   "",                          "intelligent_commands.py"),
    "clawbr_search":             ("clawbr", "Search Clawbr posts and agents",                   "/clawbr_search [query]",                                "[query]",                   "intelligent_commands.py"),
    "clawbr_stats":              ("clawbr", "Show Clawbr platform statistics",                  "/clawbr_stats",                                         "",                          "intelligent_commands.py"),
    "clawbr_analyze":            ("clawbr", "Analyze Clawbr engagement patterns",               "/clawbr_analyze",                                       "",                          "intelligent_commands.py"),
    "clawbr_strategy":           ("clawbr", "Show Clawbr engagement strategy",                  "/clawbr_strategy",                                      "",                          "intelligent_commands.py"),
    "clawbr_turns":              ("clawbr", "Show pending debate turns",                        "/clawbr_turns",                                         "",                          "intelligent_commands.py"),
    "clawbr_remind":             ("clawbr", "Send a reminder for pending debate turns",         "/clawbr_remind",                                        "",                          "intelligent_commands.py"),
    "clawbr_force_reply":        ("clawbr", "Force a reply to a debate turn",                   "/clawbr_force_reply [debate_id]",                       "[debate_id]",               "intelligent_commands.py"),
    "clawbr_verify_x":           ("clawbr", "Verify X/Twitter account on Clawbr",              "/clawbr_verify_x [@handle] [tweet_url]",                "[@handle] [tweet_url]",     "intelligent_commands.py"),
    "clawbr_register_tournament":("clawbr", "Register for a Clawbr tournament",                "/clawbr_register_tournament",                           "",                          "intelligent_commands.py"),
    "clawbr_verify_wallet":      ("clawbr", "Verify wallet address on Clawbr",                  "/clawbr_verify_wallet [address]",                       "[address]",                 "intelligent_commands.py"),
    "clawbr_balance":            ("clawbr", "Check Clawbr token balance",                       "/clawbr_balance",                                       "",                          "intelligent_commands.py"),
    "clawbr_snapshot":           ("clawbr", "Take a snapshot of Clawbr token holdings",         "/clawbr_snapshot",                                      "",                          "intelligent_commands.py"),
    "clawbr_claim":              ("clawbr", "Claim Clawbr token rewards",                       "/clawbr_claim",                                         "",                          "intelligent_commands.py"),
    "clawbr_transfer":           ("clawbr", "Transfer Clawbr tokens",                           "/clawbr_transfer [recipient] [amount]",                 "[recipient] [amount]",      "intelligent_commands.py"),
    "clawbr_auto_claim":         ("clawbr", "Toggle automatic Clawbr reward claiming",          "/clawbr_auto_claim",                                    "",                          "intelligent_commands.py"),
    "clawbr_claim_status":       ("clawbr", "Show Clawbr claim status",                         "/clawbr_claim_status",                                  "",                          "intelligent_commands.py"),
    "clawbr_token_tx":           ("clawbr", "Show Clawbr token transaction history",            "/clawbr_token_tx",                                      "",                          "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # CLAWSTR (Nostr AI Social Network)
    # -----------------------------------------------------------------------
    "clawstr_post":          ("clawstr", "Post to a Clawstr subclaw",              "/clawstr_post [subclaw] [content]",     "[subclaw] [content]",   "intelligent_commands.py"),
    "clawstr_reply":         ("clawstr", "Reply to a Clawstr post by event ID",    "/clawstr_reply [event_id] [content]",   "[event_id] [content]",  "intelligent_commands.py"),
    "clawstr_upvote":        ("clawstr", "Upvote a Clawstr post",                  "/clawstr_upvote [event_id]",            "[event_id]",            "intelligent_commands.py"),
    "clawstr_downvote":      ("clawstr", "Downvote a Clawstr post",                "/clawstr_downvote [event_id]",          "[event_id]",            "intelligent_commands.py"),
    "clawstr_show":          ("clawstr", "View posts in a Clawstr subclaw",        "/clawstr_show [subclaw]",               "[subclaw]",             "intelligent_commands.py"),
    "clawstr_recent":        ("clawstr", "View recent Clawstr posts",              "/clawstr_recent",                       "",                      "intelligent_commands.py"),
    "clawstr_search":        ("clawstr", "Search Clawstr posts",                   "/clawstr_search [query]",               "[query]",               "intelligent_commands.py"),
    "clawstr_notifications": ("clawstr", "Check Clawstr notifications",            "/clawstr_notifications",                "",                      "intelligent_commands.py"),
    "clawstr_wallet_balance":("clawstr", "Check Clawstr wallet balance",           "/clawstr_wallet_balance",               "",                      "intelligent_commands.py"),
    "clawstr_wallet_sync":   ("clawstr", "Sync wallet for Clawstr zaps",           "/clawstr_wallet_sync",                  "",                      "intelligent_commands.py"),
    "clawstr_zap":           ("clawstr", "Send a Bitcoin zap on Clawstr",          "/clawstr_zap [recipient] [amount]",     "[recipient] [amount]",  "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # CLAWNCH (Token Launch & Agent Economy)
    # -----------------------------------------------------------------------
    "clawnch_agent_register":       ("clawnch", "Register agent for Moltx token launches",          "/clawnch_agent_register",                           "",                  "intelligent_commands.py"),
    "clawnch_clear_cooldown":       ("clawnch", "Clear token launch cooldown (admin only)",          "/clawnch_clear_cooldown",                           "",                  "intelligent_commands.py"),
    "clawnch_validate_launch":      ("clawnch", "Validate a token launch payload",                   "/clawnch_validate_launch [content]",                "[content]",         "intelligent_commands.py"),
    "clawnch_launch_token_simple":  ("clawnch", "Launch token via Moltx (2-day cooldown)",           "/clawnch_launch_token_simple [name] [symbol]",      "[name] [symbol]",   "intelligent_commands.py"),
    "clawnch_promote_token":        ("clawnch", "Promote a token (max 2 posts, 2-hr cooldown)",      "/clawnch_promote_token [symbol] [address]",         "[symbol] [address]","intelligent_commands.py"),
    "clawnch_claim_fees":           ("clawnch", "Claim all token fees to wallet",                    "/clawnch_claim_fees",                               "",                  "intelligent_commands.py"),
    "clawnch_launch_alleybot_token":("clawnch", "Launch AlleyBot memecoin",                          "/clawnch_launch_alleybot_token",                    "",                  "intelligent_commands.py"),
    "clawnch_upload_image":         ("clawnch", "Upload a token logo image",                         "/clawnch_upload_image [data]",                      "[data]",            "intelligent_commands.py"),
    "clawnch_launch_token":         ("clawnch", "Launch a token on Base",                            "/clawnch_launch_token [data]",                      "[data]",            "intelligent_commands.py"),
    "clawnch_molten_register":      ("clawnch", "Register on the Molten network",                    "/clawnch_molten_register",                          "",                  "intelligent_commands.py"),
    "clawnch_molten_status":        ("clawnch", "Get Molten agent status and ClawRank",              "/clawnch_molten_status",                            "",                  "intelligent_commands.py"),
    "clawnch_molten_create_intent": ("clawnch", "Create a Molten offer or request",                  "/clawnch_molten_create_intent [type] [desc]",       "[type] [desc]",     "intelligent_commands.py"),
    "clawnch_molten_get_matches":   ("clawnch", "Get potential Molten matches",                      "/clawnch_molten_get_matches",                       "",                  "intelligent_commands.py"),
    "clawnch_twitter_post":         ("clawnch", "Post to Twitter/X via Clawnch",                     "/clawnch_twitter_post [content]",                   "[content]",         "intelligent_commands.py"),
    "clawnch_twitter_search":       ("clawnch", "Search Twitter via Clawnch",                        "/clawnch_twitter_search [query]",                   "[query]",           "intelligent_commands.py"),
    "clawnch_get_stats":            ("clawnch", "Get $CLAWNCH token stats",                          "/clawnch_get_stats",                                "",                  "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # CLAWCHESS (On-chain Chess)
    # -----------------------------------------------------------------------
    "clawchess_register":    ("clawchess", "Register as a ClawChess player",         "/clawchess_register",                   "",              "intelligent_commands.py"),
    "clawchess_status":      ("clawchess", "Show your ClawChess status",              "/clawchess_status",                     "",              "intelligent_commands.py"),
    "clawchess_queue":       ("clawchess", "Join the ClawChess matchmaking queue",    "/clawchess_queue",                      "",              "intelligent_commands.py"),
    "clawchess_leave":       ("clawchess", "Leave the matchmaking queue",             "/clawchess_leave",                      "",              "intelligent_commands.py"),
    "clawchess_play":        ("clawchess", "Start a ClawChess game",                  "/clawchess_play",                       "",              "intelligent_commands.py"),
    "clawchess_move":        ("clawchess", "Make a move in the current game",         "/clawchess_move [move]",                "[move]",        "intelligent_commands.py"),
    "clawchess_resign":      ("clawchess", "Resign from the current game",            "/clawchess_resign",                     "",              "intelligent_commands.py"),
    "clawchess_leaderboard": ("clawchess", "Show ClawChess leaderboard",              "/clawchess_leaderboard",                "",              "intelligent_commands.py"),
    "clawchess_autoplay":    ("clawchess", "Toggle AI autoplay mode",                 "/clawchess_autoplay",                   "",              "intelligent_commands.py"),
    "clawchess_activity":    ("clawchess", "Show recent ClawChess activity",          "/clawchess_activity",                   "",              "intelligent_commands.py"),
}
