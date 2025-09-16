import os
import math
import pytest

from probs_core import ProbabilitySystem

TEST_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..'))
MED_FILE = os.path.join(PROJECT_ROOT, 'inputs/medical_test.inp')


def load_medical():
    ps = ProbabilitySystem.from_file(MED_FILE)
    return ps


def test_parse_negation_and_variable_lookup():
    ps = load_medical()
    # variable names in medical_test.inp are expected to be Sickness,Test
    assert 'Sickness' in ps.variable_names
    assert 'Test' in ps.variable_names

    # Test parsing of negation forms via evaluate_query indirect usage
    p_sickness = ps.evaluate_query('P(Sickness)')
    p_not_sickness = ps.evaluate_query('P(~Sickness)')
    p_not_sickness2 = ps.evaluate_query('P(Not(Sickness))')

    assert pytest.approx(p_not_sickness, rel=1e-6) == 1.0 - p_sickness
    assert pytest.approx(p_not_sickness2, rel=1e-6) == p_not_sickness


def test_conditional_probability_medical():
    ps = load_medical()

    # From earlier work we expect P(Sickness|Test) ~= 0.1379
    val = ps.evaluate_query('P(Sickness|Test)')
    assert pytest.approx(val, rel=1e-3) == 0.137931


def test_arithmetic_expression_replacement():
    ps = load_medical()
    # Expression: P(~Sickness) should be 0.99, and P(Sickness|Test) ~ 0.137931
    expr = 'P(~Sickness) * (1 - P(Sickness|Test)) + P(Sickness|Test)'
    res = ps.evaluate_arithmetic_expression(expr)

    # Just ensure the arithmetic evaluator runs and returns a float
    assert isinstance(res, float)
    # The result should be between 0 and 1
    assert 0.0 <= res <= 1.0
