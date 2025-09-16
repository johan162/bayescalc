import math
import pytest

from probs_core import ProbabilitySystem
import probs_cli


def test_entropy_and_mutual_info_integration():
    ps = ProbabilitySystem.from_file("inputs/medical_test.inp")

    # Full joint entropy should be non-negative and reasonably small for this model
    out_joint = probs_cli.execute_command(ps, "entropy")
    assert isinstance(out_joint, float)
    assert out_joint >= 0.0
    # Compare to method (within small tolerance)
    assert out_joint == pytest.approx(ps.entropy(None), rel=1e-6)

    # Single-variable entropy (Sickness) between 0 and 1 (bits)
    out_s = probs_cli.execute_command(ps, f"entropy({ps.variable_names[0]})")
    assert isinstance(out_s, float)
    assert 0.0 <= out_s <= 1.0
    assert out_s == pytest.approx(ps.entropy([0]), rel=1e-6)

    # Mutual information should be non-negative and less than each marginal entropy
    out_mi = probs_cli.execute_command(ps, f"mutual_info({ps.variable_names[0]},{ps.variable_names[1]})")
    assert isinstance(out_mi, float)
    assert out_mi >= 0.0
    h_s = ps.entropy([0])
    h_t = ps.entropy([1])
    assert out_mi <= max(h_s, h_t) + 1e-9
    assert out_mi == pytest.approx(ps.mutual_information(0, 1), rel=1e-6)
