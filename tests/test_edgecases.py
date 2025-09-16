import pytest

from probs_core import parsing
from probs_core import stats
from probs_core import ProbabilitySystem


def test_strip_negation_variants():
    assert parsing.strip_negation("~A") == "A"
    assert parsing.strip_negation("~(A)") == "A"
    assert parsing.strip_negation("Not(A)") == "A"
    # strip_negation doesn't recursively remove the inner ~, but returns the inner text
    assert parsing.strip_negation("Not(~A)") == "~A"
    assert parsing.strip_negation("  ~B  ") == "B"


def test_parse_variable_expression_negation_variants():
    ps = ProbabilitySystem(2, [0.1, 0.2, 0.3])
    vars_, vals = ps.parse_variable_expression("~A, B")
    assert vars_ == [0, 1] and vals == [0, 1]

    vars2, vals2 = ps.parse_variable_expression("Not(A), ~(B)")
    assert vars2 == [0, 1] and vals2 == [0, 0]


def test_parse_probability_query_whitespace():
    ps = ProbabilitySystem(3, [0.05] * 7)
    parsed = ps.parse_probability_query("P( A , B | C )")
    assert parsed["type"] == "conditional"
    assert isinstance(parsed["target_vars"], list)


def test_parse_independence_unknown_name_raises():
    ps = ProbabilitySystem(2, [0.2, 0.3, 0.1])
    with pytest.raises(ValueError):
        ps.parse_independence_query("IsIndep(X,Y)")


def test_name_out_of_range():
    ps = ProbabilitySystem(2, [0.2, 0.2, 0.2])
    with pytest.raises(ValueError):
        ps.parse_variable_expression("C")


def test_evaluate_arithmetic_expression_unsafe_rejected():
    ps = ProbabilitySystem(1, [0.5])
    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression("__import__('os').system('echo hi')")


def test_sample_zero_total_prob_raises():
    with pytest.raises(ValueError):
        stats.sample({(0,): 0.0}, n=1)


def test_odds_ratio_div_by_zero_returns_none():
    # Construct a distribution where p10 * p01 == 0
    ps = ProbabilitySystem(2, [0.5, 0.5, 0.0])
    assert ps.odds_ratio(0, 1) is None


def test_relative_risk_div_by_zero_returns_none():
    # Construct distribution with zero baseline risk when exposure=0
    ps = ProbabilitySystem(2, [0.5, 0.0, 0.25])
    assert ps.relative_risk(0, 1) is None
