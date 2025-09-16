from probs_core import ProbabilitySystem
from probs_cli import execute_command
import io, sys


def capture(fn):
    old_out = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = old_out
    return buf.getvalue()


def test_list_command_multivalued():
    # Simple 2-variable multi-valued system (3 states x 2 states = 6 entries)
    joint = [0.1,0.2,0.15,0.05,0.25,0.25]  # sums to 1.0
    ps = ProbabilitySystem(2, joint,
                           variable_names=['Weather','Picnic'],
                           variable_states=[["Sunny","Cloudy","Rainy"],["Yes","No"]])
    out = capture(lambda: execute_command(ps, 'list'))
    assert 'Variable' in out
    assert 'Weather' in out
    assert 'Sunny' in out and 'Rainy' in out
    assert 'Picnic' in out
    assert 'Yes' in out and 'No' in out


def test_list_command_binary_fallback():
    # Binary legacy style using implicit states
    ps = ProbabilitySystem(1, [0.4], variable_names=['Alarm'])
    out = capture(lambda: execute_command(ps, 'list'))
    assert 'Alarm' in out
    assert '0, 1' in out or '0,1' in out


def test_list_command_filter_single():
    ps = ProbabilitySystem(2, [0.3,0.2,0.1,0.1,0.2,0.1], variable_names=['Weather','Picnic'], variable_states=[["Sunny","Cloudy","Rainy"],["Yes","No"]])
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        execute_command(ps, 'list Weather')
    finally:
        sys.stdout = old
    out = buf.getvalue()
    assert 'Variable:' in out
    assert 'Weather' in out
    assert 'Picnic' not in out  # ensure filtering applied
