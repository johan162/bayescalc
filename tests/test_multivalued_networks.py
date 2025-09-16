import math
import tempfile, os
import pytest
from probs_core import ProbabilitySystem

def write_tmp(content: str, suffix: str = '.net'):
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd,'w') as f:
        f.write(content)
    return path

def test_multivalued_root_only():
    content = """
# Simple single multi-valued variable
variable Weather {Sunny, Rainy, Cloudy}
Weather <- None
Sunny: 0.5
Rainy: 0.3
Cloudy: 0.2
"""
    path = write_tmp(content)
    try:
        ps = ProbabilitySystem.from_file(path)
        # Indices: Weather states order given
        # P(Weather=Sunny)
        p_sunny = ps.get_marginal_probability([0],[0])
        assert abs(p_sunny - 0.5) < 1e-9
        # Sum to 1
        total = sum(ps.get_marginal_probability([0],[i]) for i in range(3))
        assert abs(total - 1.0) < 1e-9
    finally:
        os.unlink(path)

def test_multivalued_with_parent():
    content = """
# Two variables with dependency
variable Age {Child, Teen, Adult}
variable Car {Budget, Standard}
Age <- None
Child: 0.4
Teen: 0.35
Adult: 0.25
Car <- (Age)
(Budget | Child): 0.01
(Standard | Child): 0.99
(Budget | Teen): 0.8
(Standard | Teen): 0.2
(Budget | Adult): 0.3
(Standard | Adult): 0.7
"""
    path = write_tmp(content)
    try:
        ps = ProbabilitySystem.from_file(path)
        # P(Age=Teen)=0.35 (index 1)
        assert abs(ps.get_marginal_probability([0],[1]) - 0.35) < 1e-9
        # P(Car=Budget | Age=Adult)=0.3
        p_budget_adult = ps.get_conditional_probability([0],[2],[1],[0])
        assert abs(p_budget_adult - 0.3) < 1e-9
        # Joint: P(Age=Adult, Car=Standard) = P(Age=Adult)*P(Standard|Adult)=0.25*0.7=0.175
        joint = ps.get_marginal_probability([0,1],[2,1])
        assert abs(joint - 0.175) < 1e-9
    finally:
        os.unlink(path)

def test_mixed_boolean_and_multivalued():
    content = """
variable Rain
variable Season {Winter, Summer}
Rain <- None
0: 0.7  # P(Rain=1)=0.7 using binary legacy root notation should be rejected in new format (expect failure)
"""
    path = write_tmp(content)
    try:
        with pytest.raises(Exception):
            ProbabilitySystem.from_file(path)
    finally:
        os.unlink(path)

def test_multivalued_query_parsing():
    content = """
variable Weather {Sunny, Rainy}
variable Traffic {Light, Heavy}
Weather <- None
Sunny: 0.6
Rainy: 0.4
Traffic <- (Weather)
(Light | Sunny): 0.7
(Heavy | Sunny): 0.3
(Light | Rainy): 0.2
(Heavy | Rainy): 0.8
"""
    path = write_tmp(content)
    try:
        ps = ProbabilitySystem.from_file(path)
        # Query P(Weather=Rainy)
        assert abs(ps.evaluate_query('P(Weather=Rainy)') - 0.4) < 1e-9
        # Query conditional P(Traffic=Heavy|Weather=Sunny)=0.3
        assert abs(ps.evaluate_query('P(Traffic=Heavy|Weather=Sunny)') - 0.3) < 1e-9
    finally:
        os.unlink(path)

def test_cpt_sum_validation():
    content = """
variable X {A,B}
variable Y {C,D}
X <- None
A: 0.6
B: 0.3  # sums to 0.9 -> invalid
Y <- (X)
(C | A): 0.5
(D | A): 0.5
(C | B): 0.5
(D | B): 0.5
"""
    path = write_tmp(content)
    try:
        with pytest.raises(Exception):
            ProbabilitySystem.from_file(path)
    finally:
        os.unlink(path)
