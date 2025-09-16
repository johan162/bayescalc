import os
import sys
import math
from collections import Counter
import pytest

from probs_core import ProbabilitySystem

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.sample_test
def test_sampling_statistical_large_draw():
    """Statistically verify that ProbabilitySystem.sample() draws according to
    the joint distribution at 99% confidence using a large number of samples.

    This test is intentionally expensive and is skipped by default. Enable with
    `pytest --sample-test` or `RUN_SAMPLE_TESTS=1 pytest`.
    """
    # Load the example medical test distribution (small support, stable probabilities)
    ps = ProbabilitySystem.from_file(os.path.join(PROJECT_ROOT, "inputs/medical_test.inp"))

    # The theoretical distribution as a mapping from state tuple -> p
    theoret = ps.joint_probabilities

    # Number of samples (large to get good power)
    N = 500_000

    samples = ps.sample(N)
    assert len(samples) == N

    counts = Counter(samples)

    # 99% two-sided z critical value
    z99 = 2.5758293035489004

    failures = []
    for state, p in sorted(theoret.items()):
        observed = counts.get(state, 0)
        obs_prop = observed / N
        # Standard error for binomial proportion
        se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
        # For p==0 or p==1 use exact checks
        if p == 0.0:
            if observed != 0:
                failures.append((state, p, obs_prop, "expected zero probability but observed >0"))
            continue
        if p == 1.0:
            if observed != N:
                failures.append((state, p, obs_prop, "expected probability 1 but observed <N"))
            continue

        lower = p - z99 * se
        upper = p + z99 * se

        # Because of approximation issues for extremely small p, ensure lower>=0
        lower = max(0.0, lower)
        upper = min(1.0, upper)

        if not (lower <= obs_prop <= upper):
            failures.append((state, p, obs_prop, lower, upper, observed))

    if failures:
        msg_lines = [f"Sampling statistical test failed for N={N}; {len(failures)} state(s) out of {len(theoret)}:\n"]
        for f in failures:
            if len(f) == 4:
                state, p, obs_prop, reason = f
                msg_lines.append(f"  state={state} p={p:.6g} obs={obs_prop:.6g}  REASON={reason}")
            else:
                state, p, obs_prop, lower, upper, observed = f
                msg_lines.append(f"  state={state} p={p:.6g} obs={obs_prop:.6g} observed={observed} CI=[{lower:.6g},{upper:.6g}]")
        pytest.fail("\n".join(msg_lines))