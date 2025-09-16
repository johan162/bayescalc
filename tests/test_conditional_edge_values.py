from probs_core import ProbabilitySystem
import math


def test_conditional_with_zero_condition_prob_returns_zero():
    # Construct a 2-variable distribution where P(B=1) == 0
    # For 2 vars, pass 3 entries (i=0..2), last inferred is i=3.
    # Choose values so entries with B=1 (i=1 and i=3) end up zero.
    ps = ProbabilitySystem(2, [0.5, 0.0, 0.5])  # last inferred -> 0.0

    # Condition P(A | B=1) should return 0 since P(B=1) == 0
    result = ps.get_conditional_probability([1], [1], [0], [1])
    assert result == 0


def test_conditional_tiny_probabilities_ratio():
    # 3-variable with tiny but nonzero probabilities for specific combinations
    vals = [1e-12, 2e-12, 3e-12, 4e-12, 5e-12, 6e-12, 7e-12]
    ps = ProbabilitySystem(3, vals)

    # Compute P(A=1 | B=1, C=0)
    numer = ps.get_marginal_probability([0, 1, 2], [1, 1, 0])
    denom = ps.get_marginal_probability([1, 2], [1, 0])
    assert denom > 0
    manual = numer / denom

    computed = ps.get_conditional_probability([1, 2], [1, 0], [0], [1])

    # Should be very close; allow tiny floating tolerance
    assert math.isclose(computed, manual, rel_tol=1e-12, abs_tol=0.0)


def test_conditional_tiny_probabilities_edge_of_precision():
    # Another tiny-prob scenario ensuring numeric stability when sums are very small
    vals = [1e-20, 2e-20, 3e-20, 4e-20, 5e-20, 6e-20, 7e-20]
    ps = ProbabilitySystem(3, vals)

    numer = ps.get_marginal_probability([0, 1, 2], [0, 1, 1])
    denom = ps.get_marginal_probability([1, 2], [1, 1])

    # If denominator is zero (shouldn't be here), the API returns 0
    computed = ps.get_conditional_probability([1, 2], [1, 1], [0], [0])
    if denom == 0:
        assert computed == 0
    else:
        manual = numer / denom
        assert math.isclose(computed, manual, rel_tol=1e-12)
