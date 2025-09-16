import math
import itertools
import random
from typing import Dict, List, Tuple, Optional


def marginal_distribution(joint_probabilities: Dict[Tuple[int, ...], float], variables: List[int]) -> Dict[Tuple[int, ...], float]:
    dist: Dict[Tuple[int, ...], float] = {}
    for values, p in joint_probabilities.items():
        key = tuple(values[i] for i in variables)
        dist[key] = dist.get(key, 0.0) + p
    return dist


def entropy(joint_probabilities: Dict[Tuple[int, ...], float], variables: Optional[List[int]] = None, base: float = 2.0) -> float:
    if variables is None:
        probs = list(joint_probabilities.values())
    else:
        probs = list(marginal_distribution(joint_probabilities, variables).values())

    h = 0.0
    for p in probs:
        if p > 0:
            h -= p * math.log(p, base)
    return h


def conditional_entropy(joint_probabilities: Dict[Tuple[int, ...], float], target_vars: List[int], given_vars: List[int], base: float = 2.0) -> float:
    joint_vars = target_vars + given_vars
    return entropy(joint_probabilities, joint_vars, base=base) - entropy(joint_probabilities, given_vars, base=base)


def mutual_information(joint_probabilities: Dict[Tuple[int, ...], float], var1: int, var2: int, base: float = 2.0) -> float:
    h1 = entropy(joint_probabilities, [var1], base=base)
    h2 = entropy(joint_probabilities, [var2], base=base)
    h12 = entropy(joint_probabilities, [var1, var2], base=base)
    return h1 + h2 - h12


def odds_ratio(get_marginal, exposure: int, outcome: int) -> Optional[float]:
    p11 = get_marginal([exposure, outcome], [1, 1])
    p10 = get_marginal([exposure, outcome], [1, 0])
    p01 = get_marginal([exposure, outcome], [0, 1])
    p00 = get_marginal([exposure, outcome], [0, 0])
    denom = p10 * p01
    if denom == 0:
        return None
    return (p11 * p00) / denom


def relative_risk(get_conditional, exposure: int, outcome: int) -> Optional[float]:
    p_out_given_exp1 = get_conditional([exposure], [1], [outcome], [1])
    p_out_given_exp0 = get_conditional([exposure], [0], [outcome], [1])
    if p_out_given_exp0 == 0:
        return None
    return p_out_given_exp1 / p_out_given_exp0


def sample(joint_probabilities: Dict[Tuple[int, ...], float], n: int = 1):
    items = sorted(joint_probabilities.items())
    states = [s for s, _ in items]
    probs = [p for _, p in items]
    total = sum(probs)
    if total <= 0:
        raise ValueError("Total probability is zero or negative")
    probs = [p / total for p in probs]

    cum = []
    c = 0.0
    for p in probs:
        c += p
        cum.append(c)

    result = []
    for _ in range(n):
        r = random.random()
        for idx, threshold in enumerate(cum):
            if r <= threshold:
                result.append(states[idx])
                break
    return result
