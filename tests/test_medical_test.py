import os
from probs_core import ProbabilitySystem

TEST_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..'))
MED_FILE_INP = os.path.join(PROJECT_ROOT, 'inputs/medical_test.inp')
MED_FILE_NET = os.path.join(PROJECT_ROOT, 'inputs/medical_test.net')

def test_value_from_both_inp_and_net_files():
    ps = ProbabilitySystem.from_file(MED_FILE_INP)
    val_inp = ps.evaluate_query('P(Sickness|Test)')
    ps = ProbabilitySystem.from_file(MED_FILE_NET)
    val_net = ps.evaluate_query('P(Sickness|Test)')
    assert val_inp - val_net < 1e-6

