from probs_core import ProbabilitySystem
import probs_cli

def test_open_command_loads_file(tmp_path):
    # Prepare a small .inp file
    f = tmp_path / 'mini.inp'
    f.write_text('variables: A,B\n00: 0.25\n01: 0.25\n10: 0.25\n11: 0.25\n')
    ps = ProbabilitySystem.from_file(str(f))
    # Modify system to something else
    ps.num_variables = 1
    ps.variable_names = ['X']
    # Execute open command to reload original file
    msg = probs_cli.execute_command(ps, f'open {f}')
    assert 'Opened' in msg
    assert ps.num_variables == 2
    assert ps.variable_names == ['A','B']
