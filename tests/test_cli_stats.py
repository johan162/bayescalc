import re
import pytest
from probs_core import ProbabilitySystem
import probs_cli


def test_odds_ratio_cli_and_relative_risk_and_sample():
    # Setup a 2-variable system with known table: 00=0.4,01=0.3,10=0.2,11=0.1
    ps = ProbabilitySystem(2, [0.4, 0.3, 0.2])

    out_or = probs_cli.execute_command(ps, "odds_ratio(A,B)")
    assert isinstance(out_or, float) and pytest.approx(out_or, rel=1e-9) == 0.6666666666666666

    out_rr = probs_cli.execute_command(ps, "relative_risk(A,B)")
    assert isinstance(out_rr, float) and pytest.approx(out_rr, rel=1e-9) == 7.0/9.0

    out_sample = probs_cli.execute_command(ps, "sample(5)")
    # sample now returns the actual list of tuples
    assert isinstance(out_sample, list)
    assert len(out_sample) == 5
    # Ensure elements look like 2-tuples of 0/1
    for s in out_sample:
        assert isinstance(s, tuple)
        assert len(s) == 2
        assert all(v in (0, 1) for v in s)
