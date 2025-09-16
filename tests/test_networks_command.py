import io, sys, re, os
from probs_cli import execute_command
from probs_core import ProbabilitySystem

def test_networks_command_outputs_table():
    # Use a trivial system instance just to call execute_command
    ps = ProbabilitySystem(1, [0.5], variable_names=['A'])
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        execute_command(ps, 'networks')
    finally:
        sys.stdout = old
    out = buf.getvalue()
    # Basic structure expectations
    assert 'Available Networks:' in out
    assert 'File' in out and 'Description' in out and 'Vars' in out
    # At least one known file appears
    assert 'medical_test.inp' in out
    # Description line should have truncated or full description text (non-empty after filename separator)
    lines = [l for l in out.splitlines() if l.strip().startswith('medical_test.inp')]
    assert lines, 'Expected line for medical_test.inp'
    # Expect columns: File | Vars | Description
    parts = lines[0].split('|')
    assert len(parts) >= 3
    vars_field = parts[1].strip()
    assert vars_field.isdigit(), f"Vars column should be a number, got '{vars_field}'"
    desc_field = '|'.join(parts[2:]).strip()
    assert desc_field != ''


def _capture(ps, cmd):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        ret = execute_command(ps, cmd)
    finally:
        sys.stdout = old
    out = buf.getvalue()
    if isinstance(ret, str):
        out += ret
    return out


def test_networks_filter_net_only():
    ps = ProbabilitySystem(1, [0.5], variable_names=['A'])
    out = _capture(ps, 'networks net')
    assert 'Available .net Networks:' in out
    assert '.net' in out
    assert '.inp' not in out


def test_networks_filter_inp_only():
    ps = ProbabilitySystem(1, [0.5], variable_names=['A'])
    out = _capture(ps, 'networks inp')
    assert 'Available .inp Networks:' in out
    assert '.inp' in out
    assert '.net' not in out


def test_networks_bad_filter():
    ps = ProbabilitySystem(1, [0.5], variable_names=['A'])
    out = _capture(ps, 'networks foo')
    assert 'Error: Unsupported networks filter' in out
