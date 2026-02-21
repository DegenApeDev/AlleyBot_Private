"""
Synergy Standard Model (SyMod) Package for AlleyBot
Mathematical truth validation framework.
"""

from .synergy_logic import (
    SynergyStandardModel,
    SyModValidationResult,
    get_symod,
    get_c2v_bridge,
)

from .symod_filter import (
    SyModTruthFilterMixin,
    create_symod_filter,
)

from .symod_calendar import (
    SyModCalendarMixin,
    create_symod_calendar,
)

__all__ = [
    'SynergyStandardModel',
    'SyModValidationResult',
    'get_symod',
    'get_c2v_bridge',
    'SyModTruthFilterMixin',
    'create_symod_filter',
    'SyModCalendarMixin',
    'create_symod_calendar',
]
