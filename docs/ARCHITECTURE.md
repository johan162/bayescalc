## Architectural Overview

This project consists of a modular Python core (`probs_core/`), a feature-rich CLI (`probs_cli.py`) supporting both interactive and deterministic batch modes, and supporting documentation & test infrastructure. Design goals:

1. Keep computational logic pure and testable (low coupling, high cohesion).
2. Allow experimentation via a REPL with tab completion while preserving deterministic, scriptable execution (`--cmds`).
3. Provide stable public API imports (`from probs_core import ProbabilitySystem`).
4. Maintain backward compatibility with historical `python probs.py` entrypoint.
5. Encourage layered testing: unit → command dispatch → batch CLI → PTY.

### Current Top-Level Layout

- `probs_core/` — Core package
    - `probs_core/probability.py` — Contains the `ProbabilitySystem` class and core probability computations.
    - `probs_core/io.py` — File load/save helpers for joint probability tables.
    - `probs_core/core.py` — (Transitional) consolidated earlier logic; new code should extend specialized modules not this file.
    - `probs_core/ui.py` — Pretty-print/display helpers used by the CLI.
    - `probs_core/formatting.py` — Global probability formatting precision management (`set_precision`, `fmt`).
    - `probs_core/parsing.py` — Parsing helpers and regex matchers used to interpret user-style queries (e.g. `P(A|B)`, `IsIndep(A,B)`, support for negation `~` and `Not(...)`).
    - `probs_core/stats.py` — Statistical utilities (entropy, conditional entropy, mutual information) and epidemiological helpers (`odds_ratio`, `relative_risk`), plus sampling and marginal-distribution helpers.
    - `probs_core/__init__.py` — Re-exports `ProbabilitySystem` so tests and user code can do `from probs_core import ProbabilitySystem`.

- `probs_cli.py` — Command-line and interactive behavior
    - Contains the interactive loop, input helpers, and tab-completion utilities.
    - Responsibilities:
        - Terminal helpers: `_read_single_char`, `tab_complete_input`.
        - `run_interactive_loop(prob_system)`: drives the REPL for queries and commands.
        - `print_help()` and example formatting functions.
        - `main()` parses arguments, supports precision control, file opening, batch `--cmds` execution, and deterministic exit with a sentinel goodbye message.
        - Command descriptors (`COMMANDS`) feed generated help and README injection.
        - Batch mode (`--cmds "cmd1;cmd2;exit"`) enables deterministic multi-command execution without PTY timing races.

- `probs.py` — Thin compatibility wrapper (backwards compatibility)
    - Minimal file that imports `ProbabilitySystem` from the `probs_core` package and delegates `__main__` to `probs_cli.main()`.
    - Purpose: allow `python probs.py` to keep working while the implementation is split for maintainability.

- `sequential_demo.py` — Example script / educational demo
    - Demonstrates sequential (Bayesian) updating using the medical test input in `inputs/`.
    - Imports `ProbabilitySystem` directly from `probs_core`.

- `inputs/` — Example input files
    - Example joint probability files in the input format (e.g., `medical_test.inp`).
    - Bayesian network `.net` examples (e.g., `sprinkler.net`, `cancer.net`, `traffic.net`).

- `tests/` — Unit tests (pytest)
    - Layered tests: unit (pure functions), batch CLI (`--cmds`), PTY interactive (tab completion, incremental input), sampling (opt-in slow).
    - Helpers centralised in `tests/conftest.py`: `run_in_pty`, `extract_result_values`, `assert_goodbye`.

- `table_of_fixed_vars/` — Helper scripts and table generators (legacy utilities)
    - Contains small helper scripts used to produce documentation tables.

- `scripts/` — Developer automation (e.g., README CLI help generation and injection).

- `Makefile` — Convenience targets (`test`, `test-pty`, `test-slow`, `test-sample`, `inject-readme`).

- `docs/DEVELOPER_GUIDE.md` / `CONTRIBUTING.md` — Process and deep-dive references.

### Migration and Compatibility

The codebase previously shipped a single-file core implementation `probs_core.py`. That file has been refactored into the `probs_core/` package (see above). To avoid breaking older scripts, a legacy copy of the original file has been preserved as `probs_core_legacy.py` in the repository root.

Recommendation: Update your imports to use the modular package API:

```python
from probs_core import ProbabilitySystem
```

This ensures you get the canonical implementation in `probs_core/probability.py` and keeps UI/display helpers in `probs_core/ui.py`.

### How the Pieces Fit Together

- `ProbabilitySystem` (in `probs_core/probability.py`) implements the high-level API: loading/saving joint tables (delegates actual I/O to `io.py`), getting joint/marginal/conditional probabilities, independence tests, and high-level evaluation of user queries and arithmetic expressions. Pretty-print display helpers live in `ui.py` and are used by the CLI.
- Parsing of user queries (e.g., `P(A,B|C)`, `IsIndep(A,B)`) is handled by `probs_core/parsing.py`. This keeps regexes and string-normalisation logic (negation handling, stripping parentheses, etc.) isolated and easy to test.
- Statistical routines that operate on the joint probability table (entropy, mutual information, marginal distribution computations, sampling, odds/relative-risk) are implemented in `probs_core/stats.py`. `ProbabilitySystem` calls these helpers rather than embedding the math inline.
- `probs_cli.py` depends on `ProbabilitySystem` but intentionally avoids importing parsing/stats internals. Tests can therefore import the core directly without invoking TTY logic.

### Example Responsibilities by File

- `probs_core/parsing.py` —
    - Provide small, well-documented helpers:
        - Regex matchers for `P(...)`, `IsIndep(...)`, `IsCondIndep(...)`.
        - Small utility `strip_negation()` to normalise `~A` and `Not(A)` forms to core variable names.
        - A helper to split the content of `P(...)` into target and condition parts when `|` is present.
    - Rationale: keep fragile regexes and string handling in one place so it's easy to adjust supported syntax (e.g., add new negation forms) without touching the core computation logic.

- `probs_core/stats.py` —
    - Implement pure functions that operate on the joint probability dictionary:
        - `marginal_distribution(joint_probs, variables) -> Dict[tuple, float]`
        - `entropy(joint_probs, variables=None, base=2) -> float`
        - `conditional_entropy(...)`, `mutual_information(...)`
        - `odds_ratio(get_marginal_fn, exposure, outcome)` — small wrapper that uses the core's marginal function
        - `relative_risk(get_conditional_fn, exposure, outcome)` — small wrapper that uses the core's conditional function
        - `sample(joint_probs, n=1)` — sample states according to their probabilities
    - Rationale: these functions are useful standalone (for tests, notebooks, and docs) and are easier to validate when pure and small.

## Testing & Development Workflow

- Tests still run against the same public API; recommended import remains:

```python
from probs_core import ProbabilitySystem
```

- Run tests using the project's virtualenv:

```bash
.venv/bin/python -m pytest -q
```

### Extending or Refactoring Further

- To add new parsing features, update `probs_core/parsing.py` and add unit tests for the parser.
- To add new statistical measures, add pure functions to `probs_core/stats.py` and unit tests.
- If the codebase grows, consider splitting `core.py` further into `io.py` (file load/save), `probability.py` (probability math), and `ui.py` (display helpers).

### Compatibility Note

- `probs.py` is intentionally a thin wrapper to preserve the `python probs.py` entrypoint. Importing `ProbabilitySystem` directly from the `probs_core` package is the recommended pattern for programmatic use.

If you'd like, I can add a short compatibility test that asserts `import probs` exposes `ProbabilitySystem` (quick follow-up).


## Testing Layers (Detail)

- Unit tests: the project uses `pytest`. Unit tests exercise the pure library
    APIs in `probs_core` (parsing, statistics, arithmetic evaluation) and are
    fast and deterministic. Run them with:

```bash
.venv/bin/python -m pytest -q
```

- PTY-based integration tests: some tests exercise the interactive CLI and
    therefore need a terminal-like environment. These tests are marked with the
    pytest marker `@pytest.mark.pty` and are gated behind a test option so they
    don't run during quick CI or developer runs by default. Enable them either by
    adding the `--run-pty` flag to pytest or setting the environment variable
    `RUN_PTY_TESTS=1`.

    Example command (run full test-suite including PTY tests):

```bash
.venv/bin/python -m pytest -q --run-pty
```

- PTY helper: the test helper `run_in_pty(cmd_args, keystrokes, timeout=5)` is
    defined in `tests/conftest.py`. It spawns a subprocess attached to a PTY,
    writes the provided keystrokes (supports chunked bytes), and returns the
    decoded output. Use this helper to write robust integration tests that avoid
    brittle timing assumptions by sending commands in chunks and waiting for the
    REPL prompt between chunks.

- VS Code integration: `pytest.ini` and `.vscode/tasks.json` include test
    discovery and run configurations so you can run either the fast (no PTY) or
    full (with PTY) test runs from the editor. The Makefile provides convenience
    targets `make test` and `make test-pty` that map to these runs.

### Notes on Writing PTY Tests

* Prefer chunked input (list of byte segments) with prompt waits handled by the helper.
* Assert on semantic markers (`-->`, `Thank you for using`, `Query:`) not timing.
* Keep scope minimal; put probability correctness in pure tests where feasible.

### Batch Mode vs PTY
Use batch `--cmds` for multi-command deterministic flows. Reserve PTY for:
* Tab completion logic.
* Interactive prompt nuances.
* Keystroke-level regression (rare).

## CLI Command Architecture

Commands are described declaratively in the `COMMANDS` list (each entry: `cmd`, `summary`, optional `params` and `examples`). This supports:
* Unified help generation (`print_help`).
* README injection via `scripts/generate_readme_help.py` + `make inject-readme`.
* Easier extension (add entry, implement handler, update tests & docs).

### Precision Handling
Probability display precision is globally managed in `probs_core/formatting.py` (`set_precision`, `get_precision`, `fmt`). The CLI `precision <n>` command adjusts this at runtime; unit tests rely on deterministic formatting for parsing numeric outputs.

## Adding a New Feature (High-Level Path)
1. Implement or extend pure logic (prefer `stats.py` or a new focused module if domain-specific).
2. Add any needed parsing tokens to `parsing.py` (keep regex changes isolated, add tests).
3. Wire a CLI command (update handler dispatch, append to `COMMANDS`).
4. Regenerate & inject README help block (`make inject-readme`).
5. Add tests at the lowest viable layer.
6. Update `docs/DEVELOPER_GUIDE.md` and cheat sheet appendix (docs/Userguide.md) if user-facing.

## Performance Characteristics & Considerations
The core enumerates the full joint distribution (O(2^N)). Practical limits reached quickly (>18–20 vars). Current mitigations:
* Lazy computation limited; most operations iterate dictionary entries.
* Probability queries reuse summations; no caching yet.
Future optimizations (roadmap candidates):
* Memoize marginal subsets (keyed by variable index tuple).
* Introduce factor graph representation for Bayesian network inputs to avoid full expansion where feasible.
* Streamed sampling using alias method for large joints.

## Security & Safety Boundaries
* Arithmetic expression evaluation: regex substitution of `P(...)` results + strict AST whitelist (only numeric literals, + - * /, unary ±). No names, attributes, or power operator permitted.
* File loading: `.inp` joint tables and `.net` Bayesian networks validated for consistency (pattern coverage, probability sum tolerance, parent pattern completeness).
* Negation and assignments: Conflicting tokens (e.g., `~A=1`) raise `ValueError`.
* No arbitrary code execution or dynamic import inside query handling.

## Error Handling Principles
* Raise `ValueError` for malformed user queries, inconsistent probability tables, invalid precision, or unsupported operations.
* Fail fast on structural inconsistencies (duplicate CPT lines, probability sum > 1 with tolerance breach).
* CLI catches broad exceptions to show user-friendly messages while preserving deterministic exit path.

## Glossary (Core Terms)
* Joint Distribution: Mapping from full boolean assignments to probabilities.
* Marginal: Summation over joint eliminating variables.
* Conditional Probability: P(A|B) computed as joint(A,B)/marginal(B).
* Independence: P(A,B)=P(A)P(B) across all assignments.
* Conditional Independence: P(A,B|C)=P(A|C)P(B|C) across all assignments.
* Mutual Information: I(A;B) derived from entropies over marginal and joint distributions.

## Cross References
* `README.md` — Concise project overview and quick start guide.
* `docs/Userguide.md` — Comprehensive user concepts, file formats, example networks.
* `docs/DEVELOPER_GUIDE.md` — Expanded process/workflow & API tables.
* `CONTRIBUTING.md` — PR workflow & checklist.
* `TESTING.md` — (If present) deeper rationale for test layering.
* API Table Regeneration: run `make api-ref` to refresh the public `ProbabilitySystem` method table below.

<!-- API-TABLE:START -->
<!-- Generated by scripts/generate_api_reference.py; do not edit manually -->

| Method | Signature | Kind | Description |
|--------|-----------|------|-------------|
| `from_file` | `(file_path: str, variable_names: Optional[List[str]] = None) -> ProbabilitySystem` | class | Create a ProbabilitySystem by loading a joint-probability file. |
| `evaluate_arithmetic_expression` | `(expr: str) -> float` | instance | Evaluate an arithmetic expression that may contain `P(...)` probability calls. |
| `get_joint_probability` | `(variable_values: Tuple[int, ...]) -> float` | instance | Return the joint probability for a full assignment represented by a tuple of 0/1 values. |
| `get_marginal_probability` | `(variables: List[int], values: List[int]) -> float` | instance | Compute marginal probability P(vars=values) by summing the joint distribution. |
| `get_conditional_probability` | `(condition_vars: List[int], condition_values: List[int], target_vars: List[int], target_values: List[int]) -> float` | instance | Return conditional probability P(target_vars=target_values \| condition_vars=condition_values). |
| `is_independent` | `(var1: int, var2: int) -> bool` | instance | Test whether two variables are (pairwise) independent. |
| `is_conditionally_independent` | `(var1: int, var2: int, given_var: int) -> bool` | instance | Test whether var1 and var2 are conditionally independent given `given_var`. |
| `parse_variable_expression` | `(expr: str) -> Tuple` | instance | Parse a variable expression like 'A, ~B, C' into indices and binary values. |
| `parse_probability_query` | `(query: str) -> Dict` | instance | Parse a textual probability query like 'P(A,B\|C)' into structured parts. |
| `parse_independence_query` | `(query: str) -> Dict` | instance | Parse independence queries like 'IsIndep(A,B)' or 'IsCondIndep(A,B\|C)'. |
| `evaluate_query` | `(query: str) -> Union` | instance | Evaluate a query string and return either a numeric probability or a boolean. |
| `marginal_distribution` | `(variables: List[int]) -> Dict` | instance | Return the marginal distribution over a subset of variables. |
| `entropy` | `(variables: Optional[List[int]] = None, base: float = 2.0) -> float` | instance | Compute Shannon entropy (in given base) for the joint or marginal distribution. |
| `conditional_entropy` | `(target_vars: List[int], given_vars: List[int], base: float = 2.0) -> float` | instance | Return H(target_vars \| given_vars) in the specified base. |
| `mutual_information` | `(var1: int, var2: int, base: float = 2.0) -> float` | instance | Return mutual information I(var1; var2) using the provided base. |
| `odds_ratio` | `(exposure: int, outcome: int) -> Optional` | instance | Compute the odds ratio for binary `exposure` and `outcome` variables. |
| `relative_risk` | `(exposure: int, outcome: int) -> Optional` | instance | Compute relative risk (risk ratio) for an exposure and outcome. |
| `sample` | `(n: int = 1) -> List` | instance | Draw `n` iid samples from the joint distribution. |
| `save_to_file` | `(file_path: str)` | instance | Save the joint probabilities and variable names to a file. |
<!-- API-TABLE:END -->

---
End of Architecture Document.

