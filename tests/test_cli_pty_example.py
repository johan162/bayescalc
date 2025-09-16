import sys
import pytest

from tests.conftest import run_in_pty, extract_result_values, assert_goodbye


@pytest.mark.pty
def test_example_pty_run():
    """Simple example test showing how to use the shared PTY helper.

    This test is marked with @pytest.mark.pty so it only runs when PTY tests are enabled
    (use `pytest --run-pty` or `RUN_PTY_TESTS=1`). It demonstrates sending a query and
    asserting on a small, robust marker in the output.
    """
    out = run_in_pty([
        sys.executable,
        "probs_cli.py",
        "inputs/medical_test.inp",
        "--cmds",
        "P(Sickness);exit"
    ], [], timeout=6)

    values, lines = extract_result_values(out, return_lines=True)
    assert values, f"No result values found in output:\n{out}"
    assert abs(values[0] - 0.01) < 1e-6, f"Expected 0.01 got {values[0]} lines={lines}\nOutput:\n{out}"
    assert any("--> 0.010000" in l for l in lines)

    assert_goodbye(out)
