import math
import pytest
from probs_core import ProbabilitySystem


def test_entropy_uniform_and_degenerate():
    # For single boolean variable uniform (P(0)=P(1)=0.5) entropy should be 1 bit
    ps = ProbabilitySystem(1, [0.5])
    assert pytest.approx(ps.entropy([0]), rel=1e-9) == 1.0

    # Degenerate distribution: entropy 0
    ps2 = ProbabilitySystem(1, [1.0])
    assert pytest.approx(ps2.entropy([0]), rel=1e-9) == 0.0


def test_mutual_information_independent():
    # independent uniform two variables
    ps = ProbabilitySystem(2, [0.25, 0.25, 0.25])
    mi = ps.mutual_information(0, 1)
    assert pytest.approx(mi, abs=1e-9) == 0.0


def test_odds_ratio_and_relative_risk():
    # Construct a 2x2 contingency: exposure vs outcome
    # Use counts scaled to probabilities
    # p11 = 0.1, p10 = 0.2, p01 = 0.3, p00 = 0.4 -> sum 1.0 but order depends on binary mapping
    # For num_variables=2, joint entries provided are [00,01,10] then last (11) computed.
    # We'll provide entries such that the full table is: 00=0.4,01=0.3,10=0.2,11=0.1
    ps = ProbabilitySystem(2, [0.4, 0.3, 0.2])
    or_val = ps.odds_ratio(0, 1)
    # OR = (p11*p00)/(p10*p01) = (0.1*0.4)/(0.2*0.3) = 0.04/0.06 = 0.666666...
    assert pytest.approx(or_val, rel=1e-9) == 0.6666666666666666

    rr = ps.relative_risk(0, 1)
    # RR = P(outcome|exposure=1)/P(outcome|exposure=0)
    # P(outcome=1 | exposure=1) = p11/(p11+p10) = 0.1/(0.1+0.2)=1/3
    # P(outcome=1 | exposure=0) = p01/(p01+p00) = 0.3/(0.3+0.4)=3/7
    # RR = (1/3)/(3/7) = (1/3)*(7/3)=7/9 ~= 0.7777777
    assert pytest.approx(rr, rel=1e-9) == 7.0 / 9.0


def test_sampling_matches_marginals():
    ps = ProbabilitySystem(2, [0.4, 0.3, 0.2])
    samples = ps.sample(2000)
    # empirical marginal for variable 0 should approximate theoretical
    counts0 = sum(s[0] for s in samples)
    emp_p1 = counts0 / 2000.0
    theo_p1 = ps.get_marginal_probability([0], [1])
    assert abs(emp_p1 - theo_p1) < 0.05  # within 5%
