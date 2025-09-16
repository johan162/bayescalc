import pytest

from probs_cli import _completion_candidates


def make_vars():
    return ["A", "B", "C", "marginals", "joint_table", "entropy"]


def test_simple_variable_completion():
    vars = make_vars()
    buf = "marg"
    candidates, ws, cur, funcs = _completion_candidates(buf, len(buf), vars)
    # should suggest 'marginals'
    assert any(c.lower().startswith("marg") for c in candidates)
    assert "marginals" in candidates


def test_isindep_completion_appends_paren():
    vars = make_vars()
    buf = "IsIn"
    candidates, ws, cur, funcs = _completion_candidates(buf, len(buf), vars)
    # should include IsIndep as a candidate and flag it as function-like
    assert any(c.lower().startswith("isind") for c in candidates)
    assert "IsIndep" in candidates
    assert "IsIndep" in funcs


def test_p_paren_suggests_variables():
    vars = make_vars()
    buf = "P("
    # cursor after the '('
    candidates, ws, cur, funcs = _completion_candidates(buf, len(buf), vars)
    # should suggest variable names
    for v in ["A", "B", "C"]:
        assert v in candidates


def test_entropy_paren_suggests_variables():
    vars = make_vars()
    buf = "entropy("
    candidates, ws, cur, funcs = _completion_candidates(buf, len(buf), vars)
    assert "A" in candidates
    assert "B" in candidates
