import re
from probs_core import ProbabilitySystem


def test_save_file_fixed_10_decimal_format(tmp_path):
    # 2-variable distribution: provide 3 entries; remainder implied
    ps = ProbabilitySystem(2, [0.123456789, 0.2, 0.3])  # last prob = 1 - sum

    out_file = tmp_path / "saved.inp"
    ps.save_to_file(str(out_file))

    content = out_file.read_text().strip().splitlines()
    # First line variable names
    assert content[0].startswith("variables:")

    # Collect probability lines
    probs = []
    for line in content[1:]:
        parts = line.split(":")
        assert len(parts) == 2
        prob_str = parts[1].strip()
        # Match exactly fixed-point with 10 decimals, no scientific notation
        assert re.match(r"^[0-9]+\.[0-9]{10}$", prob_str), prob_str
        probs.append(float(prob_str))

    # Ensure they still sum (allow tiny tolerance due to float formatting)
    assert abs(sum(probs) - 1.0) < 1e-9
