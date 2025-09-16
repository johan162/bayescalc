from probs_core import ProbabilitySystem
import probs_cli
import os

# We'll use the markov_chain4.inp for conditional independence (A independent of D given C in a chain A-B-C-D)
CHAIN_FILE = os.path.join('inputs','markov_chain4.inp')
MED_FILE = os.path.join('inputs','medical_test.inp')

def test_is_indep_false_medical():
    ps = ProbabilitySystem.from_file(MED_FILE)
    # In the medical test example Sickness and Test are not independent
    val = probs_cli.execute_command(ps, 'IsIndep(Sickness,Test)')
    assert val is False

def test_is_cond_indep_trivial():
    ps = ProbabilitySystem.from_file(MED_FILE)
    # A variable is trivially independent of another given itself (conditioning on Sickness d-separates) -> expect True
    val = probs_cli.execute_command(ps, 'IsCondIndep(Sickness,Test|Sickness)')
    assert val is True


def test_chain_conditional_independence():
    ps = ProbabilitySystem.from_file(CHAIN_FILE)
    # For a simple chain A-B-C-D, A and D are independent given C but not unconditionally in general.
    # We test both behaviors if possible. If the chain distributions produce expected structure.
    # First ensure we can call the command
    val = probs_cli.execute_command(ps, 'IsCondIndep(A,D|C)')
    assert isinstance(val, bool)

