import pytest

from probs_core import ProbabilitySystem
import probs_cli


def load_medical():
    return ProbabilitySystem.from_file("inputs/medical_test.inp")


def test_entropy_with_float_base():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "entropy base=2.0")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.entropy(None, base=2.0))


def test_entropy_with_parentheses_and_float_base():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "entropy(Sickness base=2.5)")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.entropy([0], base=2.5))


def test_cond_entropy_with_float_base():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "cond_entropy(Sickness|Test base=2.0)")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.conditional_entropy([0], [1], base=2.0))


def test_mutual_info_with_float_base():
    ps = load_medical()
    out = probs_cli.execute_command(ps, "mutual_info(Sickness,Test base=2.0)")
    assert isinstance(out, float)
    assert out == pytest.approx(ps.mutual_information(0, 1, base=2.0))
