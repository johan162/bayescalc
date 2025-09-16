import subprocess
import sys


def test_import_probability_system():
    # ensure the canonical import works
    from probs_core import ProbabilitySystem

    assert hasattr(ProbabilitySystem, 'from_file')


def test_entrypoint_runs():
    # run the entrypoint with a small input and ensure exit code 0
    p = subprocess.run([sys.executable, 'probs.py', 'inputs/medical_test.inp'], capture_output=True, text=True)
    assert p.returncode == 0
    assert 'Joint Probability Table' in p.stdout
