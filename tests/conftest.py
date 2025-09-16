"""Pytest configuration helpers.

This file ensures the project root is on `sys.path` when pytest runs so tests
can import the local `probs_core` package even when the `pytest` command in
PATH is not the same Python interpreter as `python`/the virtualenv.

Prefer installing the package in editable mode (e.g. `pip install -e .`) in
your virtualenv for a long-term solution. This shim is a low-risk convenience
that is commonly used in small projects.
"""
import os
import sys


# Insert the project root (parent of the tests/ directory) at the front of
# sys.path so local imports (like `import probs_core`) resolve to the workspace
# copy instead of requiring an installed package.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pytest_addoption(parser):
    parser.addoption(
        "--run-pty",
        action="store_true",
        default=False,
        help="Run PTY-based integration tests marked with @pytest.mark.pty",
    )
    parser.addoption(
        "--sample-test",
        action="store_true",
        default=False,
        help="Run the long statistical sampling test marked with @pytest.mark.sample_test",
    )


def pytest_collection_modifyitems(config, items):
    import pytest as _pytest

    run_pty = config.getoption("--run-pty") or os.getenv("RUN_PTY_TESTS") == "1"
    skip_pty = _pytest.mark.skip(reason="skipping PTY tests; use --run-pty to enable")
    run_sample = config.getoption("--sample-test") or os.getenv("RUN_SAMPLE_TESTS") == "1"
    skip_sample = _pytest.mark.skip(reason="skipping long statistical sample test; use --sample-test to enable")
    for item in items:
        if "pty" in item.keywords and not run_pty:
            item.add_marker(skip_pty)
        if "sample_test" in item.keywords and not run_sample:
            item.add_marker(skip_sample)


# Reusable PTY helper for integration tests that need a terminal-like environment.
# Tests can import and call `run_in_pty(cmd_args, keystrokes, timeout=5)` directly, or
# use the `pty_runner` fixture below which yields the helper function.
def run_in_pty(cmd_args, keystrokes, timeout=5):
    """Spawn a process attached to a PTY, write `keystrokes` (bytes), and return output.

    - `cmd_args` is a list of program arguments, e.g. `[sys.executable, 'probs_cli.py', 'inputs/med.inp']`.
        - `keystrokes` should be bytes (raw terminal input), e.g. `b'P(Sickness)\rexit\r'`.
            Alternatively, pass a list/tuple of bytes chunks which will be written sequentially
            with a short delay between them, e.g. `[b'P(Sickness)\r', b'exit\r']`.
    - Returns the decoded stdout+stderr output captured from the PTY as a string.
    """
    import os
    import pty
    import subprocess
    import time
    import select

    master, slave = pty.openpty()
    proc = subprocess.Popen(cmd_args, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)

    out = b""

    try:
        # Wait a short time for the CLI to emit its startup text and prompt.
        startup_deadline = time.time() + min(3.0, timeout)
        while time.time() < startup_deadline:
            rlist, _, _ = select.select([master], [], [], 0.1)
            if master in rlist:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                out += chunk
                if b"Query:" in out or b"Type 'help'" in out:
                    break

        # Helper to wait for prompt (used after sending a command chunk).
        def wait_for_prompt(deadline):
            """Read from master until a prompt marker or until deadline.

            Returns the bytes read (may be empty) and a boolean indicating whether
            a prompt was seen.
            """
            buf = b""
            while time.time() < deadline:
                rlist, _, _ = select.select([master], [], [], 0.1)
                if master in rlist:
                    try:
                        c = os.read(master, 4096)
                    except OSError:
                        break
                    if not c:
                        break
                    buf += c
                    if b"Query:" in buf or b"Type 'help'" in buf:
                        return buf, True
                time.sleep(0.01)
            return buf, False

        # Send keystrokes. Support chunked input so callers can sequence commands
        # and avoid races (e.g., send "P...\n" then wait for prompt, then send "exit\n").
        if isinstance(keystrokes, (list, tuple)):
            for idx, chunk in enumerate(keystrokes):
                os.write(master, chunk)
                # Wait a short time for the command to be processed and prompt to return.
                per_chunk_deadline = time.time() + min(2.0, timeout)
                chunk_buf, saw_prompt = wait_for_prompt(per_chunk_deadline)
                out += chunk_buf
                # Additional read loop for result marker (e.g. '-->') if this is not the final chunk
                # and we did not yet see one in the recent chunk buffer. This helps ensure that
                # interactive command output (a probability) is captured before sending the next command.
                if idx < len(keystrokes) - 1 and b"-->" not in chunk_buf:
                    extra_deadline = time.time() + 0.5
                    while time.time() < extra_deadline:
                        rlist, _, _ = select.select([master], [], [], 0.05)
                        if master in rlist:
                            try:
                                more = os.read(master, 4096)
                            except OSError:
                                break
                            if not more:
                                break
                            out += more
                            if b"-->" in more or b"Query:" in more:
                                break
                        else:
                            # small sleep to avoid busy loop
                            time.sleep(0.01)
        else:
            os.write(master, keystrokes)

        # After sending input, continue reading until timeout or process exit.
        end_time = time.time() + timeout
        while time.time() < end_time:
            rlist, _, _ = select.select([master], [], [], 0.1)
            if master in rlist:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                out += chunk

            if proc.poll() is not None:
                # drain any remaining output
                while True:
                    rlist, _, _ = select.select([master], [], [], 0)
                    if master in rlist:
                        try:
                            chunk = os.read(master, 4096)
                        except OSError:
                            break
                        if not chunk:
                            break
                        out += chunk
                    else:
                        break
                break

    finally:
        # Ensure process is terminated and file descriptors closed.
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1)
        except Exception:
            pass
        try:
            os.close(master)
        except Exception:
            pass

    return out.decode(errors="replace")


def pty_runner():
    """Convenience fixture-like function for tests.

    Usage in tests::

        from tests.conftest import pty_runner
        out = pty_runner()([sys.executable, 'probs_cli.py', 'inputs/medical_test.inp'], b'P(Sickness)\rexit\r')

    (We don't make this a real pytest fixture to keep import simplicity; tests can import the
    helper directly or call `run_in_pty`.)
    """
    return run_in_pty


def extract_result_values(output: str, return_lines: bool = False):
    """Extract numeric result values from CLI output.

    The CLI prints evaluated query results on lines beginning with '-->' followed by
    a space and a formatted floating point number (or boolean). This helper parses
    those lines and returns a list of floats (skipping booleans / non-numeric values).

    Args:
        output: Full captured stdout from a PTY or non-interactive run.
        return_lines: If True, returns a tuple (values, lines) where lines are the
            raw '-->' lines (stripped). When False (default) returns only values.

    Returns:
        List[float] or (List[float], List[str]) if return_lines=True.
    """
    import re as _re
    values = []
    lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith('-->'):
            continue
        lines.append(stripped)
        m = _re.search(r"-->\s*([0-9]+\.[0-9]+)", stripped)
        if m:
            try:
                values.append(float(m.group(1)))
            except ValueError:
                pass
    return (values, lines) if return_lines else values


def assert_goodbye(output: str):
    """Assert that the CLI session ended with a graceful goodbye message.

    Centralizes the logic so updates to the farewell text only need to be
    changed here instead of every PTY test.
    """
    if ("Thank you for using the Probability System" not in output
            and "Goodbye" not in output):
        raise AssertionError(
            "Goodbye message not found in output. Expected a farewell line.\nOutput:\n" + output
        )
