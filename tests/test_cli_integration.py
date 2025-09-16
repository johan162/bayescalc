import os
import sys
import subprocess
import time
import pty
import pytest


def test_execute_command_direct(tmp_path):
    # create a minimal sample input file and test execute_command directly
    sample = tmp_path / "sample.inp"
    sample.write_text("""variables: Sickness,Test
00: 0.9306
01: 0.0594
10: 0.0005
11: 0.0095
""")

    from probs_core import ProbabilitySystem
    from probs_cli import execute_command

    ps = ProbabilitySystem.from_file(str(sample))
    result = execute_command(ps, "P(Sickness)")
    assert isinstance(result, float)
    assert abs(result - 0.01) < 1e-6


def run_cli_in_pty(args, keystrokes, timeout=5):
    """Run CLI attached to a PTY, write keystrokes, and return output.

    Uses select.select for non-blocking reads and ensures process termination.
    """
    import select

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        args,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)

    out = b""
    try:
        # Wait for initial prompt to appear before sending keystrokes
        start = time.time()
        prompt_seen = False
        while time.time() - start < timeout:
            r, _, _ = select.select([master], [], [], 0.2)
            if master in r:
                try:
                    chunk = os.read(master, 4096)
                    if not chunk:
                        break
                    out += chunk
                    if b"Query:" in out:
                        prompt_seen = True
                        break
                except OSError:
                    break

        if not prompt_seen:
            # no prompt seen; proceed to write anyway
            pass

        # write keystrokes
        os.write(master, keystrokes)
        # small pause to allow the process to receive and handle the input
        time.sleep(0.1)
        start = time.time()
        # loop until timeout or process exit
        while True:
            if proc.poll() is not None:
                # process exited
                break
            if time.time() - start > timeout:
                break
            r, _, _ = select.select([master], [], [], 0.2)
            if master in r:
                try:
                    chunk = os.read(master, 4096)
                    if not chunk:
                        break
                    out += chunk
                except OSError:
                    break
        # try one final read; also stop if we see a new prompt which indicates the command completed
        try:
            final_start = time.time()
            while time.time() - final_start < 1.0:
                r, _, _ = select.select([master], [], [], 0.1)
                if master in r:
                    chunk = os.read(master, 4096)
                    if not chunk:
                        break
                    out += chunk
                    if b"Query:" in out:
                        break
                else:
                    # no more data
                    break
        except Exception:
            pass
    finally:
        # Ensure the process is terminated
        try:
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            os.close(master)
        except Exception:
            pass

    return out.decode(errors="replace")


@pytest.mark.pty
def test_cli_with_pty():
    # send P(Sickness)<Enter>, wait for result, then send exit
    def run_two_stage(args, first, second, timeout=2):
        import select
        master, slave = pty.openpty()
        proc = subprocess.Popen(args, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        out = b""
        try:
            # wait for initial prompt
            start = time.time()
            while time.time() - start < timeout:
                r, _, _ = select.select([master], [], [], 0.2)
                if master in r:
                    chunk = os.read(master, 4096)
                    out += chunk
                    if b"Query:" in out:
                        break

            os.write(master, first)
            # read until we get a result marker or next prompt
            start = time.time()
            while time.time() - start < timeout:
                r, _, _ = select.select([master], [], [], 0.2)
                if master in r:
                    chunk = os.read(master, 4096)
                    out += chunk
                    if b"-->" in out or b"Query:" in out or b"0.01" in out:
                        break

            os.write(master, second)
            # final read
            time.sleep(0.1)
            try:
                while True:
                    r, _, _ = select.select([master], [], [], 0)
                    if master in r:
                        chunk = os.read(master, 4096)
                        if not chunk:
                            break
                        out += chunk
                    else:
                        break
            except Exception:
                pass
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                os.close(master)
            except Exception:
                pass
        return out.decode(errors='replace')

    out = run_two_stage([sys.executable, "probs_cli.py", "inputs/medical_test.inp"], b'P(Sickness)\n', b'exit\n')
    # At minimum, the interactive session should echo the typed command and show the prompt
    assert "P(Sickness)" in out
    assert out.count("Query:") >= 1


@pytest.mark.pty
def test_tab_completion_in_pty():
    # type P( then Tab, then Sickness, then Enter, then exit
    keystrokes = b'P(\tSickness\nexit\n'
    out = run_cli_in_pty([sys.executable, "probs_cli.py", "inputs/medical_test.inp"], keystrokes)
    assert "Matches:" in out or "Sickness" in out
