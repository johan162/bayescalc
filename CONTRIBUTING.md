# Contributing Guide

Welcome! This document summarizes how to propose changes, add new computational features, extend the CLI, and test them effectively.

For deeper architectural and API details see: `DEVELOPER_GUIDE.md` (primary reference) and README (user-facing).

---
## 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt  # (optional) linters, type-checkers
```


---
## 2. Project Structure (High-Level)
| Path | Purpose |
|------|---------|
| `probs_core/` | Core probability, parsing, stats functionality |
| `probs_cli.py` | Interactive & batch CLI entrypoint |
| `tests/` | Unit, batch (`--cmds`), PTY tests |
| `inputs/` | Example `.inp` & `.net` model files |
| `DEVELOPER_GUIDE_NEW.md` | In-depth developer reference |
| `README.md` | User documentation & examples |

Add new computational logic inside `probs_core/` (ideally pure functions in `stats.py` first). Keep CLI-only concerns out of the core.

---
## 3. Adding New Functionality
Typical flow (see full detail in `DEVELOPER_GUIDE_NEW.md` Section 2):
1. Implement pure function in `probs_core/stats.py`.
2. (Optional) Add a thin wrapper method to `ProbabilitySystem` if it improves ergonomics.
3. Register a CLI command in `probs_cli.py` (handler + help text). Ensure help regeneration (see Makefile targets below).
4. Add tab-completion support if it's a new top-level command keyword.
5. Document it: README (Appendix E cheat sheet) + Developer Guide if a new category.
6. Add tests (unit → batch `--cmds` → PTY only if interactive behavior).

### Command Loop Extension Checklist
- [ ] Stats function
- [ ] Public API (optional)
- [ ] CLI handler & command registry entry
- [ ] Help text updated (run `make inject-readme` to refresh CLI help block)
- [ ] Tab completion keyword inserted
- [ ] Tests (unit + batch) added
- [ ] Docs updated (README & guide)

---
## 4. Testing Strategy
Choose the lowest layer that satisfies the requirement.

| Layer | Use When | Tooling | Notes |
|-------|----------|---------|-------|
| Unit | Pure math / parsing / stats | Direct API calls | Fastest, deterministic |
| Command dispatch | Confirm handler wiring | `execute_command` | Skip PTY |
| Batch CLI | Multi-step scripted queries | `probs_cli.py --cmds` | Stable output lines (`-->`) |
| PTY | Tab completion, prompt behavior | `run_in_pty` helper | Mark with `@pytest.mark.pty` |
| Keystroke PTY | Testing Tab / incremental typing | `run_in_pty` (chunked keystrokes) | Use minimal asserts |

### Helpers (from `tests/conftest.py`)
- `run_in_pty(cmd_args, keystrokes, timeout=5)`
- `extract_result_values(output, return_lines=False)`
- `assert_goodbye(output)`

### Batch Example
```bash
python probs_cli.py inputs/medical_test.inp --cmds "P(Sickness) P(Sickness|Test) exit"
```
In a test:
```python
out = run_in_pty([sys.executable, 'probs_cli.py', 'inputs/medical_test.inp', '--cmds', 'P(Sickness);exit'], [])
values = extract_result_values(out)
assert abs(values[0] - 0.01) < 1e-6
```

### Keystroke (Tab) Example
```python
out = run_in_pty([
	sys.executable,
	'probs_cli.py', 'inputs/medical_test.inp'
], [b'P(\t', b'A\n', b'exit\n'])
assert 'Sickness' in out or 'Matches:' in out
```

---
## 5. Running Tests & Make Targets
Quick targets (see Appendix in `DEVELOPER_GUIDE_NEW.md` for details):
| Target | Purpose |
|--------|---------|
| `make test` | Fast suite (no PTY / sampling) |
| `make test-pty` | Adds PTY tests |
| `make test-sample` | Adds sampling tests only |
| `make test-slow` | Full (PTY + sampling) |
| `make inject-readme` | Regenerate & inject CLI help |

Environment flags: `RUN_PTY_TESTS=1`, `RUN_SAMPLE_TESTS=1` (alternative to flags).

---
## 6. Pull Request Guidelines
Keep PRs narrowly scoped. Before submitting:
1. All tests green (`make test`, and if relevant `make test-pty`).
2. New functionality documented.
3. Added/updated tests cover success + one edge/error path.
4. No gratuitous formatting churn (limit diffs to relevant lines).
5. Public API changes reflected in README & Developer Guide.
6. Help text regenerated if commands changed (`make inject-readme`).

### PR Template (Suggested)
```
Summary:
Changes:
- ...
Testing:
- Added unit tests: ...
- Batch/PTY tests: ...
Docs:
- Updated README/Guide: yes/no
Backward Compatibility:
- API changes? (explain)
```

---
## 7. Style, Linting & Types
Optional but recommended:
```bash
ruff check .          # style / lint
ruff format .         # if using formatter mode
mypy .                # static type checks (if type hints present)
```
Aim for small, readable functions; keep cyclomatic complexity low.

---
## 8. Performance Notes
The system enumerates the full joint (O(2^n)). For large proposed features consider:
- Caching marginal distributions.
- Short-circuit evaluations in independence checks.
- Adding lazy factor operations (future roadmap).
Profile before optimizing; submit performance-oriented PRs with benchmark scripts.

---
## 9. Security / Safety
- Input parsing rejects malformed patterns; keep validation thorough.
- Do not execute arbitrary user expressions beyond the restricted arithmetic subset.
- Keep `evaluate_arithmetic_expression` whitelist strict (no `**`, no attribute access).

---
## 10. Getting Help
Open a draft PR early for directional feedback. Reference specific guide sections with anchors (e.g. “See Developer Guide §2.2”).

Thank you for contributing!
