"""
Fluid Lending Plugin
Check Fluid Protocol lending positions on Base
"""

from .fluid_lending import FluidLendingPlugin, create_plugin, PLUGIN_INFO

__all__ = ['FluidLendingPlugin', 'create_plugin', 'PLUGIN_INFO']
