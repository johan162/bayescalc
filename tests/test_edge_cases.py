import os
import pytest
import tempfile
from probs_core import ProbabilitySystem

TEST_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..'))
MED_FILE = os.path.join(PROJECT_ROOT, 'inputs/medical_test.inp')


def test_constructor_wrong_number_of_probabilities():
    # For 2 variables, expected 3 probabilities (2^2 - 1)
    with pytest.raises(ValueError):
        ProbabilitySystem(2, [0.2, 0.2])


def test_parse_malformed_probability_query():
    ps = ProbabilitySystem.from_file(MED_FILE)
    with pytest.raises(ValueError):
        ps.evaluate_query('P(Sickness')  # missing closing parenthesis


def test_unknown_variable_in_query():
    ps = ProbabilitySystem.from_file(MED_FILE)
    with pytest.raises(ValueError):
        ps.evaluate_query('P(UnknownVar)')


def test_conditional_with_zero_condition_probability():
    # Construct a system where conditioning event has zero probability
    # Two variables: set P(A=1,B=0)=1 and others 0 (so some conditions have zero prob)
    probs = [0.0, 1.0, 0.0]  # entries for 00,01,10 -> last calculated
    ps = ProbabilitySystem(2, probs)
    # The condition B=1 has zero probability; conditional should return 0 by implementation
    val = ps.evaluate_query('P(A|B)')
    assert val == 0


def test_arithmetic_division_by_zero_in_expression():
    ps = ProbabilitySystem.from_file(MED_FILE)
    # Force an expression that leads to division by zero after substitution
    # e.g., P(Sickness) / (P(~Sickness) - (1 - P(Sickness))) -> denominator ~0
    expr = 'P(Sickness) / (P(~Sickness) - (1 - P(Sickness)))'
    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression(expr)


def test_arithmetic_rejects_non_numeric_characters():
    ps = ProbabilitySystem.from_file(MED_FILE)
    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression('P(Sickness) + abc')
