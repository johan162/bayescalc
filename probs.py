#!/usr/bin/env python3

"""Minimal wrapper for the probability system.

This file keeps command-line compatibility for `python probs.py` while the
actual implementation lives in `probs_core.py` and `probs_cli.py`.
"""

from probs_core import ProbabilitySystem
from probs_cli import main


if __name__ == "__main__":
    main()
