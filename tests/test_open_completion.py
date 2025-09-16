import os
from probs_cli import _completion_candidates

def test_open_file_completion(tmp_path):
    # Create sample files
    f1 = tmp_path / 'sample1.inp'
    f1.write_text('variables: A\n0: 0.5\n')
    f2 = tmp_path / 'network.net'
    f2.write_text('variables: A\nA: None\n1: 0.5\n')
    other = tmp_path / 'notes.txt'
    other.write_text('ignore')
    subdir = tmp_path / 'sub'
    subdir.mkdir()
    (subdir / 'inner.inp').write_text('variables: B\n0: 0.5\n')

    # Simulate buffer 'open <tmp_path>/' to list entries
    base = f"open {tmp_path}/"
    candidates, ws, cur, funcs = _completion_candidates(base, len(base), [])
    # Expect sample1.inp, network.net, sub/ (directory), but not notes.txt
    assert any(c.endswith('sample1.inp') for c in candidates)
    assert any(c.endswith('network.net') for c in candidates)
    assert any(c.endswith('sub/') for c in candidates)
    assert not any(c.endswith('notes.txt') for c in candidates)

    # Now test partial file name filtering
    partial = f"open {tmp_path}/sam"
    candidates2, _, _, _ = _completion_candidates(partial, len(partial), [])
    assert all('sample1.inp' in c for c in candidates2)
