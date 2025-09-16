import sys
import pytest
from tests.conftest import run_in_pty, extract_result_values, assert_goodbye

# PTY test for explaining_away_alarm network verifying conditional call probabilities.
# We use --cmds for deterministic non-interactive execution.

@pytest.mark.pty
def test_explaining_away_alarm_children_given_alarm():
    out = run_in_pty([
        sys.executable,
        'probs_cli.py',
        'inputs/explaining_away_alarm.inp',
        '--cmds',
        'P(J|A);P(M|A);exit'
    ], [], timeout=8)

    values = extract_result_values(out)

    # Expect at least two outputs (P(J|A), P(M|A)) before goodbye.
    assert len(values) >= 2, f"Expected at least two result lines. Output:\n{out}"

    # Displayed formatted values (6-dec precision) should match 0.900000 and 0.700000.
    # Use strict absolute tolerance on displayed values.
    assert abs(values[0] - 0.9) < 1e-6, f"P(J|A) mismatch: {values[0]} Output:\n{out}"
    assert abs(values[1] - 0.7) < 1e-6, f"P(M|A) mismatch: {values[1]} Output:\n{out}"

    # Confirm graceful shutdown
    assert_goodbye(out)

