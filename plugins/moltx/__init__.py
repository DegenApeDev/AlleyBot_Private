"""
MoltX Plugin for AlleyBot
Integrates with Moltx.io - Twitter for AI Agents
"""

__version__ = '0.23.1'

from .moltx import MoltxPlugin, articles, communities, leaderboard, claim

__all__ = [
    'MoltxPlugin',
    'articles',
    'communities',
    'leaderboard',
    'claim',
]