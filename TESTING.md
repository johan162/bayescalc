# Testing Guide

This project has a layered test strategy combining fast unit tests, functional CLI tests, and optional PTY‑based integration tests that exercise the interactive REPL under a pseudo‑terminal.

## Make targets

Makefile shortcuts (see `Makefile` for authoritative definitions):

| Target | What it runs | Includes PTY tests? | Includes long sampling test? |
|--------|--------------|---------------------|-------------------------------|
| `make test` | `pytest -q` | No (unless you add `--run-pty`) | No |
| `make test-pty` | `pytest -q --run-pty` | Yes | No |
| `make test-slow` | `pytest -q --run-pty --sample-test` | Yes | Yes |
| `make test-sample` | `pytest -q --sample-test` | No | Yes |
| `make test-all` | Alias: currently runs `test-slow` then `compile` | Yes (via `test-slow`) | Yes |

The interpreter used is controlled by the `PYTHON` variable (defaults to `.venv/bin/python`). Override with `make PYTHON=$(which python3) test` if needed.

## Pytest markers & opt‑in flags

Two optional groups of tests are controlled by markers and flags:

| Marker | Purpose | Enable via CLI | Enable via env var |
|--------|---------|----------------|--------------------|
| `@pytest.mark.pty` | Interactive REPL tests using a pseudo‑terminal | `--run-pty` | `RUN_PTY_TESTS=1` |
| `@pytest.mark.sample_test` | Long-running statistical / sampling checks | `--sample-test` | `RUN_SAMPLE_TESTS=1` |

Collection logic in `tests/conftest.py` skips these unless explicitly enabled. This keeps default runs fast & deterministic.

## Running directly with pytest

```bash
# Fast default (skips PTY + sampling):
python -m pytest -q

# Include PTY tests:
python -m pytest -q --run-pty
# or
RUN_PTY_TESTS=1 python -m pytest -q

# Include sampling tests:
python -m pytest -q --sample-test

# Run everything (interactive + sampling):
python -m pytest -q --run-pty --sample-test
```

## PTY test helper

Interactive tests use the shared helper `run_in_pty` defined in `tests/conftest.py`:

Signature:
```python
out = run_in_pty(cmd_args, keystrokes, timeout=5)
```
Parameters:
- `cmd_args`: list of arguments (e.g. `[sys.executable, 'probs_cli.py', 'inputs/medical_test.inp']`).
- `keystrokes`: either a single `bytes` object or a list/tuple of `bytes` chunks. Each chunk is written sequentially with a small delay and a prompt wait. Use `\n` (LF) to submit a line; CR also works.
- `timeout`: overall per-phase timeout (seconds) for reading prompts/output.

Returns: decoded combined stdout+stderr captured from the PTY session.

Example (from `test_cli_pty_example.py`):
```python
out = run_in_pty(
    [sys.executable, 'probs_cli.py', 'inputs/medical_test.inp'],
    [b'P(Sickness)\n', b'exit\n']
)
assert 'P(Sickness)' in out
# Centralized goodbye assertion (see section below)
from tests.conftest import assert_goodbye
assert_goodbye(out)
```

### Robustness considerations

The CLI prints a deterministic goodbye line on clean exit. Internally a sentinel (`__EXIT__`) and an idempotent printer ensure exactly one farewell line even under PTY timing. Use the shared `assert_goodbye(output)` helper (documented below) instead of duplicating substring assertions in each test. This centralization lets us change the farewell copy once without touching every PTY test.

If you need to debug a failing PTY run:
1. Temporarily print `repr(out)` in the test.
2. Increase `timeout` in the helper call (e.g. `timeout=8`).
3. Add a unique marker in the CLI (temporary `print('DEBUG:X')`).
4. Run a single test with `-vv -k pty_example --run-pty`.

### Writing new PTY tests
Keep them minimal:
```python
@pytest.mark.pty
def test_show_entropy():
    out = run_in_pty([sys.executable, 'probs_cli.py', 'inputs/medical_test.inp'], [b'entropy\n', b'exit\n'])
    assert 'entropy' in out  # echoed command
    assert 'Goodbye' in out
```
Avoid asserting on entire tables unless necessary—prefer presence of a few stable tokens.

### Result parsing & goodbye helpers

Two additional helpers live in `tests/conftest.py` to keep PTY tests concise and robust:

1. `extract_result_values(output: str, return_lines: bool = False)`
   - Scans all lines starting with `-->` (the CLI's result marker) and returns a list of parsed floats.
   - Use it when you need to validate one or more numeric probability results without brittle string slicing.
   - Example:
     ```python
     values = extract_result_values(out)
     assert values and abs(values[0] - 0.01) < 1e-9
     ```

2. `assert_goodbye(output: str)`
   - Asserts that a graceful farewell line was emitted (currently matches either the canonical phrase or a fallback containing `Goodbye`).
   - Rationale: Previously each PTY test repeated a custom substring check; centralizing avoids drift and eases future wording changes.
   - Example:
     ```python
     from tests.conftest import assert_goodbye
     assert_goodbye(out)
     ```

Guidelines:
* Always call `assert_goodbye(out)` in PTY tests that issue an `exit` (or otherwise terminate the REPL) to verify a clean shutdown.
* Prefer `extract_result_values` over manual regexes or fragile string splits for probability outputs.
* If you need both raw lines and numeric values, call `extract_result_values(out, return_lines=True)` which returns `(values, lines)`.

## Sampling / statistical tests

Sampling tests can be slower or probabilistic. They are guarded behind `--sample-test` / `RUN_SAMPLE_TESTS=1`. Keep any statistical thresholds conservative to avoid flakiness across platforms.

## CI guidance

- Recommended default in CI: run without PTY or sampling to maximize speed:
  ```bash
  python -m pytest -q
  ```
- Add PTY tests only if the CI runner allocates a functional pseudo-terminal (most Linux hosted runners do). Enable with `--run-pty` or `RUN_PTY_TESTS=1`.
- Add sampling tests when you explicitly need distribution checks (`--sample-test`).

Example GitHub Actions (full suite):
```yaml
- name: Run full suite (PTY + sampling)
  run: |
    python -m pytest -q --run-pty --sample-test
  env:
    CI: true
```

Example (fast path):
```yaml
- name: Run fast tests
  run: python -m pytest -q
```

## Platform notes

- Linux/macOS: PTY tests should work out of the box.
- Windows (native): Python's `pty` module is not fully supported—keep PTY tests disabled (they will auto-skip unless forced).
- Containers: Some minimal containers may lack proper PTY handling; prefer the fast suite there.

## Quick reference

| Need | Command |
|------|---------|
| Fast dev loop | `make test` |
| Add PTY coverage | `make test-pty` or `pytest --run-pty` |
| Run everything | `make test-slow` |
| Just sampling | `pytest --sample-test` |
| Single PTY test | `pytest -k cli_pty_example --run-pty -vv` |

## Helper location
`run_in_pty` lives in `tests/conftest.py`. Reuse it; do not fork custom PTY plumbing unless you need fundamentally different behavior.

---
Prefer adding ordinary (non-PTY) tests for logic. Reserve PTY tests for cases where readline / prompt / interactive sequencing itself needs validation.
