"""
SIH26161 (NTRO) hydrodynamic modelling package.

Modules
-------
breach : parametric dam-breach parameterisation and Q(t) hydrograph
engine : ANUGA 4.x 2D shallow-water solver driving real DEMs
"""

from .breach import (BreachParams, breach_hydrograph, froehlich_2008,
                     macdonald_langridge, von_thun_gillette,
                     peak_discharge_estimate)
try:
    from .engine import run_dam_break, ANUGA_VERSION
except Exception:
    def run_dam_break(*args, **kwargs):
        raise RuntimeError("ANUGA solver is not installed in this environment.")
    ANUGA_VERSION = "not_installed"

__all__ = [
    "BreachParams",
    "breach_hydrograph",
    "froehlich_2008",
    "macdonald_langridge",
    "von_thun_gillette",
    "peak_discharge_estimate",
    "run_dam_break",
    "ANUGA_VERSION",
]
