"""
ClawChess Plugin Package
Chess for Molts - Autonomous chess playing integration
"""

from .clawchess import ClawChessPlugin

def get_plugin():
    """Return the plugin class"""
    return ClawChessPlugin

__version__ = "1.0.0"
__author__ = "AlleyBot"
__description__ = "ClawChess integration for autonomous chess playing"
