"""Central probability formatting configuration.

Provides a global precision for displaying probabilities in tables and CLI outputs.
Thread-safety: simple module-level integer; adjust with care if using threads.
"""
from typing import Optional

_PROB_PRECISION: int = 6  # default precision


def set_precision(p: int) -> None:
    """Set the global probability display precision (number of decimal places).

    Args:
        p: integer between 0 and 12 (inclusive) for safety.
    """
    if not isinstance(p, int):
        raise ValueError("Precision must be an integer")
    if p < 0 or p > 12:
        raise ValueError("Precision must be between 0 and 12")
    global _PROB_PRECISION
    _PROB_PRECISION = p


def get_precision() -> int:
    return _PROB_PRECISION


def fmt(prob: float, precision: Optional[int] = None) -> str:
    """Format a probability with current (or overridden) precision.

    Args:
        prob: probability value
        precision: optional override of global precision
    """
    prec = _PROB_PRECISION if precision is None else precision
    return f"{prob:.{prec}f}" 
