import pytest

from probs_core import ProbabilitySystem


def test_arithmetic_with_probabilities():
    # For the project's encoding the provided list gives P(A=0)=0.6 and
    # the remaining probability is P(A=1)=0.4, so P(A) evaluates to 0.4 here.
    ps = ProbabilitySystem(1, [0.6])
    assert abs(ps.evaluate_arithmetic_expression("P(A) + 0.2") - 0.6) < 1e-9


def test_arithmetic_scientific_notation_and_ops():
    ps = ProbabilitySystem(1, [0.5])
    val = ps.evaluate_arithmetic_expression("1e-1 + P(A) * 2")
    assert abs(val - (0.1 + 0.5 * 2)) < 1e-9


def test_arithmetic_rejects_unsafe_calls():
    ps = ProbabilitySystem(1, [0.5])
    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression("__import__('os').system('echo hi')")

    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression("(lambda x: x)(1)")
