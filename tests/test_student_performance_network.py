from probs_core.probability import ProbabilitySystem

EPS = 1e-9

def approx(a,b,eps=EPS):
    assert abs(a-b) <= eps, f"Expected {b}, got {a} diff={abs(a-b)}"


def test_student_performance_root_marginals():
    ps = ProbabilitySystem.from_file('inputs/student_performance.net')
    approx(ps.probability_of({'Intelligence':'Medium'}), 0.5)
    approx(ps.probability_of({'Difficulty':'Medium'}), 0.4)


def test_student_performance_prep_given_intelligence():
    ps = ProbabilitySystem.from_file('inputs/student_performance.net')
    # P(Prep=Good | Intelligence=High) = 0.45 from CPT
    approx(ps.conditional_probability_of({'Prep':'Good'},{'Intelligence':'High'}), 0.45)
    # Sum check
    total = 0.0
    for st in ['Poor','Adequate','Good']:
        total += ps.conditional_probability_of({'Prep':st},{'Intelligence':'High'})
    approx(total,1.0)


def test_student_performance_grade_factorization_example():
    ps = ProbabilitySystem.from_file('inputs/student_performance.net')
    # P(Intelligence=High, Difficulty=Hard, Prep=Good, Grade=A, Letter=Strong)
    joint = ps.joint_probability_of({'Intelligence':'High','Difficulty':'Hard','Prep':'Good','Grade':'A','Letter':'Strong'})
    p_i = ps.probability_of({'Intelligence':'High'})
    p_d = ps.probability_of({'Difficulty':'Hard'})
    p_p = ps.conditional_probability_of({'Prep':'Good'},{'Intelligence':'High'})
    p_grade = ps.conditional_probability_of({'Grade':'A'},{'Intelligence':'High','Difficulty':'Hard','Prep':'Good'})
    p_letter = ps.conditional_probability_of({'Letter':'Strong'},{'Grade':'A'})
    approx(joint, p_i * p_d * p_p * p_grade * p_letter)


def test_student_performance_letter_marginal_consistency():
    ps = ProbabilitySystem.from_file('inputs/student_performance.net')
    # P(Letter=Strong) = sum_g P(g)*P(Strong|g)
    total = 0.0
    for g in ['C','B','A']:
        pg = ps.probability_of({'Grade':g})
        pstrong = ps.conditional_probability_of({'Letter':'Strong'},{'Grade':g})
        total += pg * pstrong
    approx(total, ps.probability_of({'Letter':'Strong'}))
