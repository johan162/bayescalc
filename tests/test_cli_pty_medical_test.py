import sys
import pytest
from tests.conftest import run_in_pty, extract_result_values, assert_goodbye


@pytest.mark.pty
def test_medical_test_conditional_probability():
    """Verify P(Sickness|Test) matches expected value using PTY REPL.

    We send two commands sequentially:
      1. P(Sickness|Test)
      2. exit
    The helper waits for prompts between chunks, reducing race conditions.
    """
    out = run_in_pty(
        [sys.executable, "probs_cli.py", "inputs/medical_test.inp", "--cmds", "P(Sickness|Test);exit"],
        [],
        timeout=6,
    )

    # In --cmds non-interactive mode the original command may not be echoed, so we directly
    # assert on the computed output value line instead.

    expected = 0.137881
    values, lines = extract_result_values(out, return_lines=True)
    assert values, f"No result values parsed. Output:\n{out}"
    val = values[0]
    assert abs(val - expected) < 1e-6, f"Expected displayed {expected} got {val}. Lines: {lines}\nFull output:\n{out}"
    # Ensure the formatted line is present exactly
    assert any(f"--> {val:.6f}" in ln for ln in lines)

    # Confirm graceful shutdown
    assert_goodbye(out)
