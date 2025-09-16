import os
from probs_core import ProbabilitySystem


def test_inline_comments_parsing(tmp_path):
    content = """\nvariables: A,B,C  # three variables with comments\n# Full line comment still ok\n000: 0.10   # baseline all zero\n001: 0.05   # C=1 only\n010: 0.05 # B=1 only (trailing spaces)\n011: 0.10 # B=1, C=1\n100: 0.20 # A=1 only\n101: 0.10 # A=1, C=1\n110: 0.15 # A=1, B=1\n# Last combination 111 missing; remainder auto-computed = 1 - 0.75 = 0.25\n"""
    p = tmp_path / "inline_example.inp"
    p.write_text(content)

    ps = ProbabilitySystem.from_file(str(p))

    # Check variable names retained
    assert ps.variable_names == ['A', 'B', 'C']

    # Verify some probabilities
    def q(qs: str):
        return ps.evaluate_query(qs)

    # Remainder probability (missing final row) should be 1 - sum(provided)
    listed_sum = 0.10 + 0.05 + 0.05 + 0.10 + 0.20 + 0.10 + 0.15  # = 0.75
    remainder = 1.0 - listed_sum  # 0.25

    # P(A=1) rows: 100,101,110,111
    assert abs(q('P(A)') - (0.20 + 0.10 + 0.15 + remainder)) < 1e-12

    # P(C=1) rows: 001,011,101,111
    assert abs(q('P(C)') - (0.05 + 0.10 + 0.10 + remainder)) < 1e-12

    # Missing row probability inferred correctly (A=1,B=1,C=1)
    assert abs(q('P(A=1,B=1,C=1)') - remainder) < 1e-12

    # Sum should be 1
    total = sum(ps.evaluate_query(f'P(A={a},B={b},C={c})') for a in [0,1] for b in [0,1] for c in [0,1])
    assert abs(total - 1.0) < 1e-9


def test_mixed_assignment_and_negation(tmp_path):
    content = """\nvariables: X,Y\n00: 0.4 # base\n01: 0.1 # Y only\n10: 0.2 # X only\n# Missing 11 -> remainder 0.3\n"""
    p = tmp_path / "mix.inp"
    p.write_text(content)
    from probs_core import ProbabilitySystem
    ps = ProbabilitySystem.from_file(str(p))

    # Check different syntactic forms map correctly
    assert abs(ps.evaluate_query('P(X)') - (0.2 + 0.3)) < 1e-12
    assert abs(ps.evaluate_query('P(X=1)') - (0.2 + 0.3)) < 1e-12
    assert abs(ps.evaluate_query('P(~X)') - (0.4 + 0.1)) < 1e-12
    assert abs(ps.evaluate_query('P(X=0)') - (0.4 + 0.1)) < 1e-12
    assert abs(ps.evaluate_query('P(Y=1|X=1)') - (0.3 / (0.2 + 0.3))) < 1e-12
    # Combined expression with assignment and negation
    assert abs(ps.evaluate_query('P(X=1,Y=0)') - 0.2) < 1e-12
