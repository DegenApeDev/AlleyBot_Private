"""
menu_registry_1_agi_goals.py — Registry section 1: AGI Meta-Brain, Goals & Plans, Reflection.

Tuple format per command:
    "cmd_name": (cat_key, "Short description", "usage string", "args hint", "module")
"""

from typing import Dict, Tuple

# (cat, desc, usage, args, module)
REGISTRY_1: Dict[str, Tuple[str, str, str, str, str]] = {

    # -----------------------------------------------------------------------
    # AGI META-BRAIN
    # -----------------------------------------------------------------------
    "agi_cycle":              ("agi", "Run the full 14-phase AGI reasoning cycle",       "/agi_cycle",                                    "",                    "telegram.py"),
    "multi_platform":         ("agi", "Blast a topic post to all 6 platforms",           "/multi_platform [topic]",                       "[topic]",             "telegram.py"),
    "think":                  ("agi", "Run one autonomous think cycle",                  "/think",                                        "",                    "intelligent_commands.py"),
    "brain_start":            ("agi", "Start the autonomous brain loop",                 "/brain_start",                                  "",                    "brain_commands.py"),
    "brain_stop":             ("agi", "Stop the autonomous brain loop",                  "/brain_stop",                                   "",                    "brain_commands.py"),
    "brain_status":           ("agi", "Show current brain / autonomous mode status",     "/brain_status",                                 "",                    "brain_commands.py"),
    "brain":                  ("agi", "Alias for /brain_status",                         "/brain",                                        "",                    "brain_commands.py"),
    "brain_mode":             ("agi", "Switch brain operating mode",                     "/brain_mode [mode]",                            "[mode]",              "brain_commands.py"),
    "brain_log":              ("agi", "Show recent brain activity log",                  "/brain_log",                                    "",                    "brain_commands.py"),
    "brain_confidence_debug": ("agi", "Debug brain confidence scoring internals",        "/brain_confidence_debug",                       "",                    "brain_commands.py"),
    "chat":                   ("agi", "Chat naturally with the AI",                      "/chat [message]",                               "[message]",           "intelligent_commands.py"),

    # -----------------------------------------------------------------------
    # GOALS & PLANS
    # -----------------------------------------------------------------------
    "goals":                  ("goals", "List all active goals",                         "/goals",                                        "",                    "goal_commands.py"),
    "goals_scan":             ("goals", "Scan context and propose new goals",            "/goals_scan",                                   "",                    "goal_commands.py"),
    "goals_propose":          ("goals", "Manually propose a new goal",                   "/goals_propose [goal description]",             "[goal description]",  "goal_commands.py"),
    "goals_approve":          ("goals", "Approve a pending goal by ID",                  "/goals_approve [goal_id]",                      "[goal_id]",           "goal_commands.py"),
    "goals_reject":           ("goals", "Reject a pending goal by ID",                   "/goals_reject [goal_id]",                       "[goal_id]",           "goal_commands.py"),
    "goals_start":            ("goals", "Mark a goal as in-progress",                    "/goals_start [goal_id]",                        "[goal_id]",           "goal_commands.py"),
    "goals_complete":         ("goals", "Mark a goal as completed",                      "/goals_complete [goal_id]",                     "[goal_id]",           "goal_commands.py"),
    "goals_detail":           ("goals", "Show full detail for a goal",                   "/goals_detail [goal_id]",                       "[goal_id]",           "goal_commands.py"),
    "goals_stats":            ("goals", "Show goal completion statistics",               "/goals_stats",                                  "",                    "goal_commands.py"),
    "plan_create":            ("goals", "Create a new execution plan",                   "/plan_create [description]",                    "[description]",       "plan_commands.py"),
    "plan_status":            ("goals", "Show status of the current plan",               "/plan_status",                                  "",                    "plan_commands.py"),
    "plan_next":              ("goals", "Execute the next step in the active plan",      "/plan_next",                                    "",                    "plan_commands.py"),
    "plan_retry":             ("goals", "Retry the last failed plan step",               "/plan_retry",                                   "",                    "plan_commands.py"),
    "plan_list":              ("goals", "List all plans",                                "/plan_list",                                    "",                    "plan_commands.py"),

    # -----------------------------------------------------------------------
    # REFLECTION & SELF-IMPROVEMENT
    # -----------------------------------------------------------------------
    "reflection_status":           ("reflection", "Show self-reflection system status",          "/reflection_status",                                "",                       "reflection_commands.py"),
    "reflection_log":              ("reflection", "Show recent reflection log entries",           "/reflection_log",                                   "",                       "reflection_commands.py"),
    "reflection_tune":             ("reflection", "Tune reflection parameters",                   "/reflection_tune [param] [value]",                  "[param] [value]",        "reflection_commands.py"),
    "evolve":                      ("reflection", "Trigger an evolution / self-improvement cycle","/evolve",                                           "",                       "reflection_commands.py"),
    "strategies":                  ("reflection", "Show active strategies derived from reflection","/strategies",                                       "",                       "reflection_commands.py"),
    "improve_status":              ("reflection", "Show self-improvement pipeline status",        "/improve_status",                                   "",                       "intelligent_commands.py"),
    "improve_self_update_confirm": ("reflection", "Confirm a pending self-update by ID",          "/improve_self_update_confirm [update_id]",           "[update_id]",            "intelligent_commands.py"),
    "skills":                      ("reflection", "List all loaded skills",                       "/skills",                                           "",                       "intelligent_commands.py"),
    "skill":                       ("reflection", "Execute a specific skill by name",             "/skill [skill_name] [args...]",                     "[skill_name] [args...]", "intelligent_commands.py"),
}
