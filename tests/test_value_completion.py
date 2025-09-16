from probs_cli import _completion_candidates
from probs_core import ProbabilitySystem

# We'll craft a tiny multi-valued system directly

def make_system():
    # 1 variable with 3 states, encoded full joint
    ps = ProbabilitySystem(1, [0.2,0.3,0.5], variable_names=["Weather"], variable_states=[["Sunny","Cloudy","Rainy"]])
    return ps

def make_binary_system():
    ps = ProbabilitySystem(1, [0.4], variable_names=["Alarm"], variable_states=[["0","1"]])
    return ps


def test_value_completion_after_equals():
    ps = make_system()
    buffer = "P(Weather="  # cursor after '=' expecting states
    candidates, ws, cur, funcs = _completion_candidates(buffer, len(buffer), ps.variable_names, {"Weather": ps.variable_states[0]})
    assert set(candidates) == {"Sunny","Cloudy","Rainy"}


def test_value_completion_filters():
    ps = make_system()
    buffer = "P(Weather=R"  # partial 'R'
    candidates, ws, cur, funcs = _completion_candidates(buffer, len(buffer), ps.variable_names, {"Weather": ps.variable_states[0]})
    # Filtering is applied later in tab handler; here we still list all states; ensure Rainy present
    assert "Rainy" in candidates


def test_binary_value_completion():
    ps = make_binary_system()
    buffer = "P(Alarm="
    candidates, ws, cur, funcs = _completion_candidates(buffer, len(buffer), ps.variable_names, {"Alarm": ps.variable_states[0]})
    assert set(candidates) == {"0","1"}
