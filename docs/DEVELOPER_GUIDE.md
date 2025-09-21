# Developer Guide (New)

This document supersedes earlier ad-hoc developer notes. It focuses on:
1. Public computational API (overview + examples)
2. Extending the library (adding new computations & CLI commands + tab completion)
3. Testing strategies (unit, batch `--cmds`, PTY, keystroke/tab-completion) and shared helpers

---
## 1. Public API Overview

The core API lives in `probs_core.probability.ProbabilitySystem`. Load a system from either a raw joint table (`.inp`) or a Bayesian network (`.net`).

```python
from probs_core import ProbabilitySystem
ps = ProbabilitySystem.from_file('inputs/medical_test.inp')
```

### 1.1 Primary Methods
| Category | Method | Signature (simplified) | Description |
|----------|--------|------------------------|-------------|
| Creation | `from_file` | `(file_path, variable_names=None)` | Factory: parse `.inp` or `.net` and build system |
| Joint Access | `get_joint_probability` | `(assignment_tuple)` | Probability of a full assignment |
| Marginal | `get_marginal_probability` | `(vars, values)` | P(vars=values) via summation |
| Conditional | `get_conditional_probability` | `(cond_vars, cond_vals, target_vars, target_vals)` | P(target|condition) |
| Independence | `is_independent` | `(v1, v2)` | Pairwise independence test |
| Conditional Independence | `is_conditionally_independent` | `(v1, v2, given)` | Test given single conditioning var |
| Query Parsing | `parse_probability_query` | `(text)` | Parse `P(A,B|C)` → structured dict |
| Independence Parsing | `parse_independence_query` | `(text)` | Parse `IsIndep(A,B)` / `IsCondIndep(A,B|C)` |
| Query Evaluation | `evaluate_query` | `(text)` | Evaluate probability / independence query |
| Arithmetic Eval | `evaluate_arithmetic_expression` | `(expr)` | Evaluate arithmetic with embedded `P(...)` |
| Distribution | `marginal_distribution` | `(vars)` | Return dict of assignments → prob for subset |
| Entropy | `entropy` | `(vars=None, base=2.0)` | Shannon entropy (joint or subset) |
| Conditional Entropy | `conditional_entropy` | `(target_vars, given_vars, base)` | H(target|given) |
| Mutual Information | `mutual_information` | `(v1,v2,base)` | I(v1;v2) |
| Odds Ratio | `odds_ratio` | `(exposure, outcome)` | ad/bc (None if undefined) |
| Relative Risk | `relative_risk` | `(exposure, outcome)` | Risk_exposed / Risk_unexposed |
| Sampling | `sample` | `(n=1)` | Draw `n` samples |
| Persistence | `save_to_file` | `(path)` | Write joint table (10 decimal precision) |

### 1.2 Basic Usage Examples
```python
# Probability queries
p_sick = ps.get_marginal_probability([0],[1])
p_sick_given_test = ps.get_conditional_probability([1],[1],[0],[1])  # P(S|T)

# Using textual queries
parsed = ps.parse_probability_query('P(Sickness|Test)')
value = ps.evaluate_query('P(Sickness|Test)')
ratio = ps.evaluate_arithmetic_expression('P(Sickness|Test)/P(Sickness)')

# Independence / information
indep = ps.is_independent(0,1)
mi = ps.mutual_information(0,1)
H_cond = ps.conditional_entropy([0],[1])

# Epidemiology helpers
or_val = ps.odds_ratio(0,1)
rr_val = ps.relative_risk(0,1)

# Sampling
samples = ps.sample(5)
```

### 1.3 Name ↔ Index Mapping
Variable order is preserved from the input file (or override). Map name to index with `ps.variable_names.index('Name')`.

---
## 2. Extending the Library

Goal: add a new computed metric (e.g. `co_information(A,B,C)`) and expose it through the CLI (`coinf(A,B,C)`).

### 2.1 Steps Overview
1. Implement pure function in `probs_core/stats.py` (no I/O, accept primitive args & probability structures where possible).
2. (Optional) Add thin convenience method to `ProbabilitySystem` if widely useful; keep it minimal (call the pure stats function).
3. Update CLI command map in `probs_cli.py`:
   - Add entry in the dispatcher.
   - Provide help text (auto-generated help section if applicable).
4. Update tab-completion (if new command keyword should complete): ensure command is listed among recognized commands.
5. Add unit tests for the stats function and the new `ProbabilitySystem` wrapper (if added).
6. Add batch `--cmds` integration test verifying output line format and numeric value.
7. Only add PTY test if interactive behavior (completion / prompt / multi-line) differs from existing patterns.
8. Update documentation: README cheat sheet (Appendix E) + Developer Guide if new category of function.

### 2.2 Pure Function Pattern (`stats.py`)
```python
def co_information(joint_probs: Dict[Tuple[int,...], float], a: int, b: int, c: int, base: float = 2.0) -> float:
    """Compute co-information I(A;B;C) using inclusion-exclusion.

    Uses helper marginalization utilities from stats (reuse existing patterns: marginal_distribution, entropy).
    """
    # Pseudocode sketch (actual implementation would reuse existing entropy funcs):
    # H(A)+H(B)+H(C) - H(A,B) - H(A,C) - H(B,C) + H(A,B,C)
    return (
        entropy(joint_probs, [a], base=base)
        + entropy(joint_probs, [b], base=base)
        + entropy(joint_probs, [c], base=base)
        - entropy(joint_probs, [a,b], base=base)
        - entropy(joint_probs, [a,c], base=base)
        - entropy(joint_probs, [b,c], base=base)
        + entropy(joint_probs, [a,b,c], base=base)
    )
```

### 2.3 Thin Wrapper (`ProbabilitySystem`)
```python
class ProbabilitySystem:
    # ... existing methods ...
    def co_information(self, a: int, b: int, c: int, base: float = 2.0) -> float:
        from .stats import co_information
        return co_information(self.joint_probabilities, a, b, c, base=base)
```
(Add only if you expect repeated external use; otherwise callers can import the stats function directly.)

### 2.4 CLI Command (`probs_cli.py`)
Add to the command registry (illustrative snippet):
```python
COMMANDS = {
    # ...existing...
    'coinf': {
        'help': 'Co-information I(A;B;C) using inclusion-exclusion',
        'handler': handle_coinf,  # new function you write
    },
}
```
Handler pattern:
```python
def handle_coinf(ps, arg_text):
    # Expect something like: coinf(A,B,C base=10)
    # Parse args (reuse existing small parsers or implement a simple splitter)
    names_part, base = parse_optional_base(arg_text)
    names = [n.strip() for n in names_part.split(',') if n.strip()]
    if len(names) != 3:
        return "Error: coinf expects exactly three variables"
    idxs = [ps.variable_names.index(n) for n in names]
    val = ps.co_information(*idxs, base=base)
    return format_number(val)
```

### 2.5 Tab Completion
If completion logic enumerates commands, add `'coinf'`. For variable name completion the existing logic usually suffices.

### 2.6 Tests
- Unit: test numerical correctness on a small 3-variable synthetic distribution.
- API: call `ps.co_information(...)`.
- CLI (batch):
```python
def test_coinf_batch(tmp_path):
    out = run_cli_batch(['inputs/xor_triplet.inp'], 'coinf(A,B,C)')  # hypothetical helper
    assert '-->' in out  # or parse numeric token
```
- PTY (only if tab-completion: e.g. typing `coi<TAB>` should complete `coinf`).

### 2.7 Documentation
Update:
- README Appendix E (Quick Query Cheat Sheet)
- This guide (method table) if wrapper added
- CLI help generation if auto-doc system references command metadata

---
## 3. Testing Strategies

Testing is layered; choose the *lowest* layer that gives required confidence.

### 3.1 Strategy Layers
| Layer | Tooling | Trigger to Use | Avoid When |
|-------|---------|----------------|------------|
| Pure Unit | Direct API (`ProbabilitySystem`, stats functions) | Logic / math correctness | Needing CLI formatting |
| Command Dispatch | `execute_command` | Verify command routing & formatting | Complex multi-command chain |
| Batch CLI | `probs_cli.py --cmds` | Sequential commands deterministic output | Need tab completion |
| Subprocess (stdin) | `Popen` text mode | Legacy simple flows (optional) | Batch mode suffices |
| PTY | `run_in_pty` helper | Interactive features (completion, prompt) | Numerical-only checks |

### 3.2 Batch Command Testing (`--cmds`)
Deterministic, no timing races. Example:
```bash
python probs_cli.py inputs/medical_test.inp --cmds "P(Sickness) P(Sickness|Test) entropy exit"
```
Parse results in tests:
```python
values = extract_result_values(out)
assert abs(values[0] - 0.01) < 1e-6
```

### 3.3 PTY Command Testing
Use only for features requiring a terminal. Canonical example mirrors `tests/test_cli_pty_example.py`:
```python
import sys, pytest
from tests.conftest import run_in_pty, extract_result_values, assert_goodbye

@pytest.mark.pty
def test_example_pty_run():
    out = run_in_pty([
        sys.executable,
        'probs_cli.py',
        'inputs/medical_test.inp',
        '--cmds',
        'P(Sickness);exit'
    ], [], timeout=6)
    values, lines = extract_result_values(out, return_lines=True)
    assert values and abs(values[0]-0.01) < 1e-6
    assert any('--> 0.010000' in l for l in lines)
    assert_goodbye(out)
```

### 3.4 Keystroke-Level (Tab Completion) Tests
For tab-completion you must send actual keystrokes (not `--cmds`). Provide chunks to `run_in_pty` as a list/tuple so it waits between commands:
```python
out = run_in_pty([
    sys.executable,
    'probs_cli.py',
    'inputs/medical_test.inp'
], [b'P(\t', b'A\n', b'exit\n'])
assert 'Sickness' in out or 'Matches:' in out
```
Guidelines:
- Keep each keystroke chunk small.
- Wait logic inside helper reduces need for `sleep`.
- Assert on *presence* of completion tokens, not full formatted blocks.

### 3.5 `tests/conftest.py` Helpers / Fixtures
Provided utilities:
- `run_in_pty(cmd_args, keystrokes, timeout=5)` — PTY driver (supports list of bytes chunks)
- `extract_result_values(output, return_lines=False)` — Parse lines like `--> 0.123456`
- `assert_goodbye(output)` — Assert farewell line present (centralized so wording changes need one edit)

(If you add new helpers: keep names descriptive, pure logic separated, and reuse across tests.)

---
## 4. Minimal Example End-to-End (New Command Sketch)
```python
# stats.py
# def co_information(...):  # implement as above

# probability.py
# class ProbabilitySystem: def co_information(...): pass

# probs_cli.py handler (simplified):
# def handle_coinf(ps, text):
#     names = text.split(',')  # real code: robust parsing & base
#     idxs = [ps.variable_names.index(n.strip()) for n in names]
#     val = ps.co_information(*idxs)
#     print(format_number(val))

# test_stats_coinf.py (unit)
# def test_coinf_symmetry(ps_xyz): ...

# test_cli_coinf_batch.py (batch CLI)
# out = run_in_batch([... '--cmds', 'coinf(A,B,C);exit'])
# assert '-->' in out
```

---
## 5. Checklist for New Feature PR
- [ ] Pure function in `stats.py` (+ tests)
- [ ] Optional thin wrapper in `ProbabilitySystem`
- [ ] CLI command + help text + inclusion in completion list
- [ ] Batch test (`--cmds`) validating numeric output
- [ ] PTY test only if interactive nuance (completion etc.)
- [ ] README Appendix E updated (if user-facing)
- [ ] Developer guide (this file) updated if new category / pattern
- [ ] All tests (`make test`, optionally `make test-pty`) green
- [ ] Save format unaffected (10-decimal) or explicitly updated + documented

---
Feel free to iterate on this guide; keep examples minimal, deterministic, and aligned with the existing helper utilities.

---
## Appendix: Makefile Targets Reference

The `Makefile` provides convenience shortcuts for common workflows. You can always run the underlying commands directly, but the targets encode the canonical invocations.

| Target | Command Executed | Purpose | Includes PTY Tests? | Includes Sampling Tests? | Notes |
|--------|------------------|---------|---------------------|---------------------------|-------|
| `test` | `$(PYTHON) -m pytest -q` | Fast unit + integration (default skips PTY & sampling) | No (unless flags passed manually) | No | Use during rapid development |
| `test-pty` | `$(PYTHON) -m pytest -q --run-pty` | Adds PTY-marked interactive tests | Yes | No | Requires functional pseudo-terminal (Linux/macOS) |
| `test-sample` | `$(PYTHON) -m pytest -q --sample-test` | Adds long/statistical tests only | No | Yes | Use sparingly; may be slower / probabilistic |
| `test-slow` | `$(PYTHON) -m pytest -q --run-pty --sample-test` | Full suite (interactive + sampling) | Yes | Yes | CI full coverage candidate |
| `test-all` | Alias: runs `test-slow` then `compile` | Full suite + byte-compilation | Yes | Yes | Ensures code also byte-compiles cleanly |
| `compile` | `$(PYTHON) -m compileall -q .` | Byte-compile every Python file | N/A | N/A | Catches syntax errors / gross import issues |
| `regen-readme` | `$(PYTHON) scripts/generate_readme_help.py > README_CLI.md` | Regenerate CLI help snapshot | N/A | N/A | Does not modify main README directly |
| `inject-userguide` | Regenerates then injects help (`--inject docs/Userguide.md --confirm`) | Update Userguide CLI help block | N/A | N/A | Prompts before overwriting sentinel section |

### Environment Variable Override
`PYTHON` can be overridden when invoking make:
```bash
make PYTHON=$(which python3.12) test
```
If `.venv/bin/python` exists it is used by default; fallback controlled by the `PYTHON ?=` line in the `Makefile`.

### Typical Workflows
| Scenario | Recommended Target(s) |
|----------|-----------------------|
| Iterate on logic / parser | `make test` |
| Validate interactive additions | `make test-pty` |
| Run everything before release | `make test-slow` (or `make test-all`) |
| Update CLI help after changing commands | `make inject-readme` |

### CI Suggestions
1. Fast path (PRs): run `make test`.
2. Nightly / pre-release: run `make test-slow` (or `test-all` if you want compile check explicitly).
3. After editing CLI commands: run `make inject-readme` locally; commit resulting README changes.

### Extending the Makefile
Add new targets for repeatable scripts (e.g., profiling, linting). Example stub:
```makefile
lint:
    $(PYTHON) -m ruff check .
```
Document any additions here to keep the guide synchronized.

