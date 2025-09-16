import pytest

from probs_core import ProbabilitySystem
import probs_cli


def load_medical():
    return ProbabilitySystem.from_file("inputs/medical_test.inp")


def test_entropy_full_matches_method():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "entropy")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.entropy(None))


def test_entropy_single_var_matches_method():
    ps = load_medical()
    var = ps.variable_names[0]
    out = probs_cli.execute_command(ps, f"entropy({var})")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.entropy([0]))


def test_conditional_entropy_matches_method():
    ps = load_medical()
    a = ps.variable_names[0]
    b = ps.variable_names[1]
    out = probs_cli.execute_command(ps, f"cond_entropy({a}|{b})")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.conditional_entropy([0], [1]))


def test_mutual_information_matches_method():
    ps = load_medical()
    a = ps.variable_names[0]
    b = ps.variable_names[1]
    out = probs_cli.execute_command(ps, f"mutual_info({a},{b})")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.mutual_information(0, 1))


def test_invalid_variable_returns_error_string():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "entropy(UNKNOWN)")
    assert isinstance(out, str)
    assert out.startswith("Error:")
