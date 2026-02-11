"""
Synergy Standard Model (SyMod) Package for AlleyBot
Mathematical truth validation framework.
"""

from .synergy_logic import (
    SynergyStandardModel,
    SyModValidationResult,
    get_symod,
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
    'SyModTruthFilterMixin',
    'create_symod_filter',
    'SyModCalendarMixin',
    'create_symod_calendar',
]
