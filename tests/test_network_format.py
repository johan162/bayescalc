import tempfile, os, math
import pytest
from probs_core import ProbabilitySystem


def write(tmp_content: str):
    fd, path = tempfile.mkstemp(suffix='.net')
    with os.fdopen(fd,'w') as f:
        f.write(tmp_content)
    return path


def test_simple_chain_network():
    content = """\nvariables: A,B,C\nA: None\n1: 0.4\nB: A\n1: 0.7\n0: 0.2\nC: B\n1: 0.8\n0: 0.3\n"""
    path = write(content)
    try:
        ps = ProbabilitySystem.from_file(path)
        # Compute P(A=1) should be 0.4 directly
        assert abs(ps.get_marginal_probability([0],[1]) - 0.4) < 1e-9
        # P(B=1) = P(B=1|A=1)P(A=1)+P(B=1|A=0)P(A=0)=0.7*0.4+0.2*0.6=0.28+0.12=0.40
        assert abs(ps.get_marginal_probability([1],[1]) - 0.40) < 1e-9
        # P(C=1|B=1)=0.8 check conditional
        p_c1_b1 = ps.get_conditional_probability([1],[1],[2],[1])
        assert abs(p_c1_b1 - 0.8) < 1e-9
    finally:
        os.unlink(path)


def test_explaining_away_network_equivalence():
    content = """\nvariables: B,E,A,J,M\nB: None\n1: 0.01\nE: None\n1: 0.002\nA: B,E\n11: 0.99\n10: 0.99\n01: 0.99\n00: 0.0005\nJ: A\n1: 0.90\n0: 0.05\nM: A\n1: 0.70\n0: 0.01\n"""
    path = write(content)
    try:
        ps = ProbabilitySystem.from_file(path)
        # Basic sanity: all probs sum to 1 implicitly
        total = sum(ps.get_marginal_probability([0,1,2,3,4],[b,e,a,j,m]) for b in [0,1] for e in [0,1] for a in [0,1] for j in [0,1] for m in [0,1])
        assert abs(total - 1.0) < 1e-9
        # Check base rates
        p_b = ps.get_marginal_probability([0],[1])
        assert abs(p_b - 0.01) < 1e-9
        p_e = ps.get_marginal_probability([1],[1])
        assert abs(p_e - 0.002) < 1e-9
        # Alarm high given any cause
        p_a_given_b1e0 = ps.get_conditional_probability([0,1],[1,0],[2],[1])
        assert abs(p_a_given_b1e0 - 0.99) < 1e-9
    finally:
        os.unlink(path)


def test_network_missing_cpt_error():
    content = """\nvariables: X,Y\nX: None\n1: 0.3\nY: X\n1: 0.8\n"""  # Missing 0: line for Y|X=0
    path = write(content)
    try:
        with pytest.raises(ValueError):
            ProbabilitySystem.from_file(path)
    finally:
        os.unlink(path)
