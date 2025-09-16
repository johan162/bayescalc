from probs_core.probability import ProbabilitySystem

EPS = 1e-9

def approx(a,b,eps=EPS):
    assert abs(a-b) <= eps, f"Expected {b}, got {a} diff={abs(a-b)}"


def test_medical_diagnosis_root_marginal():
    ps = ProbabilitySystem.from_file('inputs/medical_diagnosis_mini.net')
    approx(ps.probability_of({'Disease':'None'}), 0.7)
    approx(ps.probability_of({'Disease':'Severe'}), 0.1)


def test_medical_diagnosis_testresult_given_disease():
    ps = ProbabilitySystem.from_file('inputs/medical_diagnosis_mini.net')
    approx(ps.conditional_probability_of({'TestResult':'StrongPos'},{'Disease':'Severe'}), 0.70)
    total = 0.0
    for st in ['Negative','WeakPos','StrongPos']:
        total += ps.conditional_probability_of({'TestResult':st},{'Disease':'Severe'})
    approx(total,1.0)


def test_medical_diagnosis_treatment_factorization():
    ps = ProbabilitySystem.from_file('inputs/medical_diagnosis_mini.net')
    # Joint P(Disease=Mild, SymptomA=Strong, SymptomB=Present, Treatment=Aggressive, TestResult=WeakPos)
    joint = ps.joint_probability_of({'Disease':'Mild','SymptomA':'Strong','SymptomB':'Present','Treatment':'Aggressive','TestResult':'WeakPos'})
    p_dis = ps.probability_of({'Disease':'Mild'})
    p_symA = ps.conditional_probability_of({'SymptomA':'Strong'},{'Disease':'Mild'})
    p_symB = ps.conditional_probability_of({'SymptomB':'Present'},{'Disease':'Mild'})
    p_test = ps.conditional_probability_of({'TestResult':'WeakPos'},{'Disease':'Mild'})
    p_treat = ps.conditional_probability_of({'Treatment':'Aggressive'},{'Disease':'Mild','SymptomA':'Strong','SymptomB':'Present'})
    approx(joint, p_dis * p_symA * p_symB * p_test * p_treat)
