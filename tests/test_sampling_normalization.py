import random
import math

from probs_core import stats


def test_sampling_with_tiny_probabilities_repects_normalization():
    # Two-state distribution with tiny probabilities; normalized should be 1/3 and 2/3
    joint = {(0,): 1e-12, (1,): 2e-12}

    random.seed(42)
    samples = stats.sample(joint, n=2000)

    counts = {s: 0 for s in joint}
    for s in samples:
        counts[s] += 1

    empirical = counts[(0,)] / 2000
    expected = 1e-12 / (1e-12 + 2e-12)

    # allow reasonable sampling noise
    assert math.isclose(empirical, expected, rel_tol=0.1)


def test_sampling_with_sum_not_exactly_one_normalizes():
    # Two-state distribution where the raw probabilities sum slightly above 1
    joint = {(0,): 0.30000003, (1,): 0.70000007}  # sum = 1.0000001

    random.seed(123)
    samples = stats.sample(joint, n=2000)

    counts = {s: 0 for s in joint}
    for s in samples:
        counts[s] += 1

    empirical0 = counts[(0,)] / 2000
    empirical1 = counts[(1,)] / 2000

    # Expected normalized probabilities
    total = 0.30000003 + 0.70000007
    expected0 = 0.30000003 / total
    expected1 = 0.70000007 / total

    assert math.isclose(empirical0, expected0, rel_tol=0.05)
    assert math.isclose(empirical1, expected1, rel_tol=0.05)
