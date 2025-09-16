import math
from probs_core.probability import ProbabilitySystem

EPS = 1e-9

def approx(a,b,eps=EPS):
    assert abs(a-b) <= eps, f"Expected {b}, got {a} diff={abs(a-b)}"


def test_alarm_subset_root_marginals():
    ps = ProbabilitySystem.from_file('inputs/alarm_subset.net')
    # Root marginals from CPT
    approx(ps.probability_of({'VentMach':'On'}), 0.85)
    approx(ps.probability_of({'VentTube':'Clear'}), 0.9)


def test_alarm_subset_press_conditional():
    ps = ProbabilitySystem.from_file('inputs/alarm_subset.net')
    # P(Press=Low | VentMach=Off, VentTube=Blocked) = 0.55
    approx(ps.conditional_probability_of({'Press':'Low'},{'VentMach':'Off','VentTube':'Blocked'}), 0.55)
    # Sum over states given parents should be 1
    total = 0.0
    for st in ['Low','Normal','High']:
        total += ps.conditional_probability_of({'Press':st},{'VentMach':'Off','VentTube':'Blocked'})
    approx(total,1.0)


def test_alarm_subset_alarm_joint_factorization():
    ps = ProbabilitySystem.from_file('inputs/alarm_subset.net')
    # Joint: P(VentMach=On, VentTube=Blocked, Press=High, CO2=High, Alarm=Yes)
    joint_direct = ps.joint_probability_of({'VentMach':'On','VentTube':'Blocked','Press':'High','CO2':'High','Alarm':'Yes'})
    p_vm = ps.probability_of({'VentMach':'On'})
    p_vt = ps.probability_of({'VentTube':'Blocked'})
    p_press = ps.conditional_probability_of({'Press':'High'},{'VentMach':'On','VentTube':'Blocked'})
    p_co2 = ps.conditional_probability_of({'CO2':'High'},{'Press':'High'})
    p_alarm = ps.conditional_probability_of({'Alarm':'Yes'},{'Press':'High','CO2':'High'})
    approx(joint_direct, p_vm * p_vt * p_press * p_co2 * p_alarm)


def test_alarm_subset_alarm_marginal_via_summation():
    ps = ProbabilitySystem.from_file('inputs/alarm_subset.net')
    # P(Alarm=Yes) = sum_{press,co2} P(press) P(co2|press) P(Alarm=Yes|press,co2)
    total = 0.0
    for press in ['Low','Normal','High']:
        p_press = ps.probability_of({'Press':press})
        for co2 in ['Low','Normal','High']:
            p_co2_given_press = ps.conditional_probability_of({'CO2':co2},{'Press':press})
            p_alarm = ps.conditional_probability_of({'Alarm':'Yes'},{'Press':press,'CO2':co2})
            total += p_press * p_co2_given_press * p_alarm
    approx(total, ps.probability_of({'Alarm':'Yes'}))
