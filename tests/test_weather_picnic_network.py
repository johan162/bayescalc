import math
from probs_core.probability import ProbabilitySystem

# Tolerances for floating comparison
EPS = 1e-9

def approx(a,b,eps=EPS):
    assert abs(a-b) <= eps, f"Expected {b}, got {a} (diff={abs(a-b)})"


def test_weather_picnic_basic_marginals():
    ps = ProbabilitySystem.from_file('inputs/weather_picnic.net')
    # P(Weather=Sunny) directly from CPT
    p_sunny = ps.probability_of({'Weather':'Sunny'})
    approx(p_sunny, 0.5)
    # P(Picnic=Yes) = sum_w P(w)*sum_f P(f|w)*P(Yes|w,f)
    # We'll compute manually to validate the joint assembly
    weather_states = ['Sunny','Cloudy','Rainy']
    forecast_states = ['Sunny','Cloudy','Rainy']
    picnic_yes = 0.0
    for w in weather_states:
        pw = ps.probability_of({'Weather':w})
        for f in forecast_states:
            pf_given_w = ps.conditional_probability_of({'Forecast':f},{'Weather':w})
            py_given = ps.conditional_probability_of({'Picnic':'Yes'},{'Weather':w,'Forecast':f})
            picnic_yes += pw * pf_given_w * py_given
    approx(ps.probability_of({'Picnic':'Yes'}), picnic_yes)


def test_weather_picnic_conditionals_consistency():
    ps = ProbabilitySystem.from_file('inputs/weather_picnic.net')
    # Check that for each (Weather, Forecast) the Picnic conditional sums to 1
    for w in ['Sunny','Cloudy','Rainy']:
        for f in ['Sunny','Cloudy','Rainy']:
            total = 0.0
            for pstate in ['Yes','No']:
                total += ps.conditional_probability_of({'Picnic':pstate},{'Weather':w,'Forecast':f})
            approx(total,1.0)


def test_weather_picnic_example_query_matches_joint():
    ps = ProbabilitySystem.from_file('inputs/weather_picnic.net')
    # Joint P(Weather=Rainy, Forecast=Rainy, Picnic=No)
    joint_direct = ps.joint_probability_of({'Weather':'Rainy','Forecast':'Rainy','Picnic':'No'})
    # Factor form: P(Weather=Rainy)*P(Forecast=Rainy|Weather=Rainy)*P(Picnic=No|Weather=Rainy,Forecast=Rainy)
    p_w = ps.probability_of({'Weather':'Rainy'})
    p_f = ps.conditional_probability_of({'Forecast':'Rainy'},{'Weather':'Rainy'})
    p_p = ps.conditional_probability_of({'Picnic':'No'},{'Weather':'Rainy','Forecast':'Rainy'})
    approx(joint_direct, p_w * p_f * p_p)
