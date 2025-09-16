import os
import tempfile
import pytest
from probs_core import ProbabilitySystem

TEST_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..'))
MED_FILE = os.path.join(PROJECT_ROOT, 'inputs/medical_test.inp')


def test_from_file_missing_file():
    with pytest.raises(FileNotFoundError):
        ProbabilitySystem.from_file('nonexistent_file.inp')


def test_from_file_incomplete_entries():
    # With new semantics: multiple missing combinations are zero-filled and distribution completed.
    content = """
variables: A,B
00: 0.5
01: 0.2
"""
    fd, path = tempfile.mkstemp(prefix='probtest_', suffix='.inp')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)

        ps = ProbabilitySystem.from_file(path)
        # Expected final joint after zero-fill then inference of last (due to constructor):
        # Provided: 00=0.5,01=0.2, missing 10=0.0 inserted, inferred last 11=0.3
        p00 = ps.get_marginal_probability([0,1],[0,0])
        p01 = ps.get_marginal_probability([0,1],[0,1])
        p10 = ps.get_marginal_probability([0,1],[1,0])
        p11 = ps.get_marginal_probability([0,1],[1,1])
        assert pytest.approx(p00, rel=1e-12) == 0.5
        assert pytest.approx(p01, rel=1e-12) == 0.2
        assert pytest.approx(p10, rel=1e-12) == 0.0
        assert pytest.approx(p11, rel=1e-12) == 0.3
        # Sum integrity
        assert pytest.approx(p00 + p01 + p10 + p11, rel=1e-12) == 1.0
    finally:
        os.unlink(path)


def test_independence_and_conditional_independence():
    # Build a simple independent system for two variables
    # P(A=0,B=0)=0.25,01=0.25,10=0.25,11=0.25
    ps = ProbabilitySystem(2, [0.25, 0.25, 0.25])
    assert ps.is_independent(0, 1)

    # Conditional independence in trivial cases with 3 variables
    # Make independent third variable by product
    # 3 variables, joint probs for first 7 entries; last will be 1 - sum
    # We'll use uniform distribution (1/8 each) -> all independent
    uniform_probs = [1/8] * (2**3 - 1)
    ps3 = ProbabilitySystem(3, uniform_probs)
    assert ps3.is_conditionally_independent(0, 1, 2)


def test_arithmetic_unsafe_characters():
    ps = ProbabilitySystem.from_file(MED_FILE)
    # Unsafe characters like letters outside allowed pattern should be rejected
    with pytest.raises(ValueError):
        ps.evaluate_arithmetic_expression('P(Sickness) + os.system("ls")')


def test_save_and_reload_roundtrip():
    ps = ProbabilitySystem.from_file(MED_FILE)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    try:
        ps.save_to_file(tmp.name)
        ps2 = ProbabilitySystem.from_file(tmp.name)
        # same marginal for Sickness
        p1 = ps.get_marginal_probability([0], [1])
        p2 = ps2.get_marginal_probability([0], [1])
        assert pytest.approx(p1, rel=1e-9) == p2
    finally:
        os.unlink(tmp.name)
