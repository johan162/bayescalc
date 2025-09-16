from probs_core import ProbabilitySystem
from probs_cli import execute_command
import io, sys

def capture(fn):
    old = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = old
    return buf.getvalue()

def test_list_separator_length_covers_rows():
    # Create variable with long state names
    states = ["StateOne","StateTwo","StateThree","AReallyLongStateNameForTesting"]
    ps = ProbabilitySystem(1, [0.25,0.25,0.25,0.25], variable_names=['Node'], variable_states=[states])
    out = capture(lambda: execute_command(ps, 'list'))
    # Extract separator lines
    lines = [l for l in out.splitlines() if l.startswith('-')]
    assert len(lines) >= 3  # top, header underline, bottom
    sep_len = len(lines[0])
    # All subsequent separator lines should be same length
    assert all(len(l) == sep_len for l in lines)
    # Longest data line length should not exceed separator length
    data_lines = [l for l in out.splitlines() if l.startswith('Node')]
    assert data_lines, 'Expected a data line starting with Node'
    for dl in data_lines:
        assert len(dl) <= sep_len
