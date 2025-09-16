from probs_core import ProbabilitySystem


def test_conditional_probability_two_vars():
    # Two-variable example with explicit joint probabilities for all 4 outcomes.
    # We'll provide 3 entries and let the last be inferred. The ordering in this
    # project expects the passed list to be all combinations except the last
    # sorted combination; construct a simple distribution manually via from_file
    ps = ProbabilitySystem(2, [0.2, 0.3, 0.1])

    # Compute P(A=1 | B=1). Manual calculation:
    # joint prob P(A=1,B=1) is the entry for (1,1) in joint_probabilities
    p11 = ps.get_marginal_probability([0, 1], [1, 1])
    p_b1 = ps.get_marginal_probability([1], [1])
    expected = p11 / p_b1 if p_b1 > 0 else 0

    assert abs(ps.get_conditional_probability([1], [1], [0], [1]) - expected) < 1e-12


def test_conditional_probability_three_vars():
    # 3-variable distribution: make a small deterministic-like distribution
    # choose joint probs such that P(A,B,C) nonzero for a subset — provide 7 values
    vals = [0.1, 0.0, 0.2, 0.0, 0.1, 0.0, 0.3]
    ps = ProbabilitySystem(3, vals)

    # Compute P(A=1 | B=0, C=1) using get_conditional_probability directly
    expected = ps.get_conditional_probability([1, 2], [0, 1], [0], [1])

    # Now compute manually: P(A=1,B=0,C=1) / P(B=0,C=1)
    p_joint = ps.get_marginal_probability([0, 1, 2], [1, 0, 1])
    p_cond = ps.get_marginal_probability([1, 2], [0, 1])
    manual = p_joint / p_cond if p_cond > 0 else 0

    assert abs(expected - manual) < 1e-12
