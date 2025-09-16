#!/usr/bin/env python3
"""
Core ProbabilitySystem class, delegating parsing and stats to submodules.
"""
from typing import Dict, List, Tuple, Optional, Union
import os
import re
import itertools

from .parsing import (
    strip_negation,
    parse_probability_query_text,
    match_probability_query,
    match_independence_conditional,
    match_independence,
)

from . import stats


class ProbabilitySystem:
    """A system for handling probabilistic calculations with boolean random variables."""

    def __init__(
        self,
        num_variables: int,
        joint_probs: List[float],
        variable_names: Optional[List[str]] = None,
    ):
        self.num_variables = num_variables

        if variable_names is not None:
            if len(variable_names) != num_variables:
                raise ValueError(
                    f"Expected {num_variables} variable names, got {len(variable_names)}"
                )
            self.variable_names = variable_names
        else:
            self.variable_names = [chr(65 + i) for i in range(num_variables)]

        expected_probs = 2**num_variables - 1
        if len(joint_probs) != expected_probs:
            raise ValueError(
                f"Expected {expected_probs} probabilities, got {len(joint_probs)}"
            )

        last_prob = 1.0 - sum(joint_probs)
        if last_prob < -1e-10:
            raise ValueError(
                f"Joint probabilities sum to more than 1 (sum={sum(joint_probs)})"
            )

        all_probs = joint_probs + [max(0, last_prob)]

        self.joint_probabilities = {}
        for i, prob in enumerate(all_probs):
            binary = [(i >> (num_variables - j - 1)) & 1 for j in range(num_variables)]
            self.joint_probabilities[tuple(binary)] = prob

    @classmethod
    def from_file(
        cls, file_path: str, variable_names: Optional[List[str]] = None
    ) -> "ProbabilitySystem":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        joint_probs_dict = {}
        file_variable_names = None

        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.lower().startswith("variables:"):
                    names_part = line[len("variables:") :].strip()
                    file_variable_names = [name.strip() for name in names_part.split(",")]
                    continue

                try:
                    parts = line.split(":", 1)
                    if len(parts) != 2:
                        raise ValueError(f"Invalid format in line {line_num}: {line}")

                    binary_str = parts[0].strip()
                    prob_str = parts[1].strip()

                    if not all(bit in "01" for bit in binary_str):
                        raise ValueError(
                            f"Invalid binary pattern in line {line_num}: {binary_str}"
                        )

                    try:
                        prob = float(prob_str)
                    except ValueError:
                        raise ValueError(
                            f"Invalid probability in line {line_num}: {prob_str}"
                        )

                    if prob < 0 or prob > 1:
                        raise ValueError(
                            f"Probability must be between 0 and 1 in line {line_num}: {prob}"
                        )

                    binary_tuple = tuple(int(bit) for bit in binary_str)
                    joint_probs_dict[binary_tuple] = prob

                except Exception as e:
                    raise ValueError(f"Error parsing line {line_num}: {e}")

        if not joint_probs_dict:
            raise ValueError("No valid probability entries found in the file")

        num_variables = len(next(iter(joint_probs_dict.keys())))
        expected_entries = 2**num_variables

        names_to_use = variable_names or file_variable_names
        if names_to_use and len(names_to_use) != num_variables:
            print(
                f"Warning: Expected {num_variables} variable names, got {len(names_to_use)}. Using default names."
            )
            names_to_use = None

        if not all(len(key) == num_variables for key in joint_probs_dict.keys()):
            raise ValueError("Inconsistent binary pattern lengths in the file")

        if len(joint_probs_dict) == expected_entries - 1:
            all_combinations = set(itertools.product([0, 1], repeat=num_variables))
            missing_combination = all_combinations - set(joint_probs_dict.keys())

            if len(missing_combination) != 1:
                raise ValueError(
                    f"Expected exactly one missing combination, found {len(missing_combination)}"
                )

            remaining_prob = 1.0 - sum(joint_probs_dict.values())
            if remaining_prob < -1e-10:
                raise ValueError(
                    f"Joint probabilities sum to more than 1: {sum(joint_probs_dict.values())}"
                )

            joint_probs_dict[next(iter(missing_combination))] = max(0, remaining_prob)
        elif len(joint_probs_dict) == expected_entries:
            total_prob = sum(joint_probs_dict.values())
            if abs(total_prob - 1.0) > 1e-10:
                raise ValueError(f"Joint probabilities do not sum to 1: {total_prob}")
        else:
            raise ValueError(
                f"Expected {expected_entries} or {expected_entries - 1} probability entries, "
                f"got {len(joint_probs_dict)}"
            )

        sorted_combinations = sorted(joint_probs_dict.keys())
        joint_probs = [joint_probs_dict[combo] for combo in sorted_combinations[:-1]]

        return cls(num_variables, joint_probs, names_to_use)

    # --- Arithmetic & query evaluation
    def evaluate_arithmetic_expression(self, expr: str) -> float:
        def prob_replacer(match):
            prob_query = match.group(0)
            value = self.evaluate_query(prob_query)
            return str(value)

        prob_pattern = r"P\((?:[^()]+|\([^()]*\))*\)"
        expr_with_values = re.sub(prob_pattern, prob_replacer, expr)

        try:
            if not re.match(r"^[\d\.\+\-\*/\(\)eE ]+$", expr_with_values):
                raise ValueError("Unsafe characters in expression.")
            result = eval(expr_with_values, {"__builtins__": None}, {})
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")
        return result

    def get_joint_probability(self, variable_values: Tuple[int, ...]) -> float:
        return self.joint_probabilities.get(variable_values, 0.0)

    def get_marginal_probability(self, variables: List[int], values: List[int]) -> float:
        if len(variables) != len(values):
            raise ValueError("Number of variables must match number of values")

        result = 0.0
        for joint_values, prob in self.joint_probabilities.items():
            match = True
            for var_idx, var_value in zip(variables, values):
                if joint_values[var_idx] != var_value:
                    match = False
                    break
            if match:
                result += prob

        return result

    def get_conditional_probability(
        self,
        condition_vars: List[int],
        condition_values: List[int],
        target_vars: List[int],
        target_values: List[int],
    ) -> float:
        joint_vars = target_vars + condition_vars
        joint_values = target_values + condition_values
        joint_prob = self.get_marginal_probability(joint_vars, joint_values)

        condition_prob = self.get_marginal_probability(condition_vars, condition_values)

        if condition_prob == 0:
            return 0

        return joint_prob / condition_prob

    def is_independent(self, var1: int, var2: int) -> bool:
        for val1 in [0, 1]:
            for val2 in [0, 1]:
                joint_prob = self.get_marginal_probability([var1, var2], [val1, val2])
                marg_prob1 = self.get_marginal_probability([var1], [val1])
                marg_prob2 = self.get_marginal_probability([var2], [val2])
                if abs(joint_prob - marg_prob1 * marg_prob2) > 1e-10:
                    return False

        return True

    def is_conditionally_independent(
        self, var1: int, var2: int, given_var: int
    ) -> bool:
        for val1 in [0, 1]:
            for val2 in [0, 1]:
                for given_val in [0, 1]:
                    joint_cond_prob = self.get_conditional_probability(
                        [given_var], [given_val], [var1, var2], [val1, val2]
                    )

                    cond_prob1 = self.get_conditional_probability(
                        [given_var], [given_val], [var1], [val1]
                    )

                    cond_prob2 = self.get_conditional_probability(
                        [given_var], [given_val], [var2], [val2]
                    )

                    if abs(joint_cond_prob - cond_prob1 * cond_prob2) > 1e-10:
                        return False

        return True

    # --- Parsing related methods (use parsing helpers)
    def parse_variable_expression(self, expr: str) -> Tuple[List[int], List[int]]:
        variables = []
        values = []

        parts = [p.strip() for p in expr.split(",")]

        for part in parts:
            if not part:
                continue

            negated = False

            if part.startswith("Not(") and part.endswith(")"):
                negated = True
                part = part[4:-1].strip()
            else:
                if part.startswith("~"):
                    negated = True
                    part = part[1:].strip()
                    if part.startswith("(") and part.endswith(")"):
                        part = part[1:-1].strip()

            try:
                var_idx = self.variable_names.index(part)
            except ValueError:
                if len(part) == 1 and "A" <= part <= "Z":
                    var_idx = ord(part) - ord("A")
                    if var_idx >= self.num_variables:
                        raise ValueError(f"Variable {part} is out of range")
                else:
                    raise ValueError(f"Unknown variable name: {part}")

            variables.append(var_idx)
            values.append(0 if negated else 1)

        return variables, values

    def parse_probability_query(self, query: str) -> Dict:
        m = match_probability_query(query)
        if not m:
            raise ValueError(f"Invalid probability query format: {query}")

        content = m.group(1)
        is_cond, target_text, condition_text = parse_probability_query_text(content)

        if is_cond:
            target_vars, target_values = self.parse_variable_expression(target_text)
            condition_vars, condition_values = self.parse_variable_expression(condition_text)

            return {
                "type": "conditional",
                "target_vars": target_vars,
                "target_values": target_values,
                "condition_vars": condition_vars,
                "condition_values": condition_values,
            }
        else:
            vars, values = self.parse_variable_expression(target_text)
            return {"type": "marginal", "vars": vars, "values": values}

    def parse_independence_query(self, query: str) -> Dict:
        m = match_independence_conditional(query)
        if m:
            var1_name, var2_name, given_var_name = [
                strip_negation(g) for g in m.groups()
            ]

            def _name_to_idx(name: str) -> int:
                try:
                    return self.variable_names.index(name)
                except ValueError:
                    if len(name) == 1 and "A" <= name <= "Z":
                        idx = ord(name) - ord("A")
                        if idx >= self.num_variables:
                            raise ValueError(f"Variable {name} is out of range")
                    else:
                        raise ValueError(f"Unknown variable name: {name}")
                    return idx

            var1_idx = _name_to_idx(var1_name)
            var2_idx = _name_to_idx(var2_name)
            given_var_idx = _name_to_idx(given_var_name)

            return {
                "type": "conditional_independence",
                "var1": var1_idx,
                "var2": var2_idx,
                "given_var": given_var_idx,
            }

        m2 = match_independence(query)
        if m2:
            var1_name, var2_name = [strip_negation(g) for g in m2.groups()]

            def _name_to_idx_simple(name: str) -> int:
                try:
                    return self.variable_names.index(name)
                except ValueError:
                    if len(name) == 1 and "A" <= name <= "Z":
                        idx = ord(name) - ord("A")
                        if idx >= self.num_variables:
                            raise ValueError(f"Variable {name} is out of range")
                    else:
                        raise ValueError(f"Unknown variable name: {name}")
                    return idx

            var1_idx = _name_to_idx_simple(var1_name)
            var2_idx = _name_to_idx_simple(var2_name)

            return {"type": "independence", "var1": var1_idx, "var2": var2_idx}

        raise ValueError(f"Invalid independence query format: {query}")

    def evaluate_query(self, query: str) -> Union[float, bool]:
        if query.startswith("P("):
            parsed = self.parse_probability_query(query)

            if parsed["type"] == "conditional":
                return self.get_conditional_probability(
                    parsed["condition_vars"],
                    parsed["condition_values"],
                    parsed["target_vars"],
                    parsed["target_values"],
                )
            else:
                return self.get_marginal_probability(parsed["vars"], parsed["values"])
        elif query.startswith("IsIndep(") or query.startswith("IsCondIndep("):
            parsed = self.parse_independence_query(query)

            if parsed["type"] == "independence":
                return self.is_independent(parsed["var1"], parsed["var2"])
            else:
                return self.is_conditionally_independent(
                    parsed["var1"], parsed["var2"], parsed["given_var"]
                )
        else:
            raise ValueError(f"Unknown query type: {query}")

    # --- Pretty print helpers
    def pretty_print_joint_table(self):
        print("\nJoint Probability Table:")
        print("========================\n")

        header = " | ".join(self.variable_names) + " | Probability"
        print(header)
        print("-" * len(header))

        for values, prob in sorted(self.joint_probabilities.items()):
            row = " | ".join(str(val) for val in values)
            from .formatting import fmt
            print(f"{row} | {fmt(prob)}")

    def pretty_print_marginals(self):
        print("\nMarginal Probabilities:")
        print("======================\n")

        print("Single variable marginals:")
        for i, var_name in enumerate(self.variable_names):
            p0 = self.get_marginal_probability([i], [0])
            p1 = self.get_marginal_probability([i], [1])
            from .formatting import fmt
            print(f"P({var_name}=0) = {fmt(p0)},  P({var_name}=1) = {fmt(p1)}")

        if self.num_variables >= 2:
            print("\nTwo variable marginals:")
            for i, var_i in enumerate(self.variable_names):
                for j in range(i + 1, self.num_variables):
                    var_j = self.variable_names[j]
                    for val_i in [0, 1]:
                        for val_j in [0, 1]:
                            p = self.get_marginal_probability([i, j], [val_i, val_j])
                            from .formatting import fmt
                            print(f"P({var_i}={val_i}, {var_j}={val_j}) = {fmt(p)}")

    def pretty_print_independence_table(self):
        if self.num_variables < 2:
            print("Need at least 2 variables to test independence.")
            return

        print("\nIndependence Table:")
        print("=================\n")

        print(f"{'Variables':15} | {'Independent?' }")
        print("-" * 30)

        for i in range(self.num_variables):
            for j in range(i + 1, self.num_variables):
                var_i = self.variable_names[i]
                var_j = self.variable_names[j]
                is_indep = self.is_independent(i, j)
                status = "Yes" if is_indep else "No"
                print(f"{var_i} and {var_j:10} | {status}")

    def pretty_print_conditional_independence_table(self):
        if self.num_variables < 3:
            print("Need at least 3 variables to test conditional independence.")
            return

        print("\nConditional Independence Table:")
        print("=============================\n")

        print(f"{'Variables':20} | {'Given':10} | {'Conditionally Independent?' }")
        print("-" * 60)

        for i in range(self.num_variables):
            for j in range(i + 1, self.num_variables):
                for k in range(self.num_variables):
                    if k != i and k != j:
                        var_i = self.variable_names[i]
                        var_j = self.variable_names[j]
                        var_k = self.variable_names[k]

                        is_cond_indep = self.is_conditionally_independent(i, j, k)
                        status = "Yes" if is_cond_indep else "No"

                        print(f"{var_i} and {var_j:10} | {var_k:10} | {status}")

    def pretty_print_conditional_probabilities(self, target_size: int, condition_size: int):
        if target_size < 1 or target_size > self.num_variables:
            print(f"Error: Target size must be between 1 and {self.num_variables}.")
            return

        if condition_size < 1 or condition_size > self.num_variables:
            print(f"Error: Condition size must be between 1 and {self.num_variables}.")
            return

        if target_size + condition_size > self.num_variables:
            print(
                f"Error: Combined size (n+m={target_size+condition_size}) exceeds number of variables ({self.num_variables})."
            )
            return

        print(
            f"\nConditional Probabilities Table: {target_size}-tuples given {condition_size}-tuples"
        )
        print("=" * 60)

        from itertools import combinations

        target_var_combos = list(combinations(range(self.num_variables), target_size))
        condition_var_combos = list(combinations(range(self.num_variables), condition_size))

        valid_pairs = []
        for target_combo in target_var_combos:
            for condition_combo in condition_var_combos:
                if not any(var in condition_combo for var in target_combo):
                    valid_pairs.append((target_combo, condition_combo))

        if not valid_pairs:
            print(
                f"No valid variable combinations where {target_size}-tuples and {condition_size}-tuples don't overlap."
            )
            return

        header = f"{'Conditional Probability':30} | {'Value'}"
        print(header)
        print("-" * len(header))

        for target_vars, condition_vars in valid_pairs:
            for target_values_tuple in itertools.product([0, 1], repeat=target_size):
                for condition_values_tuple in itertools.product([0, 1], repeat=condition_size):
                    target_vars_list = list(target_vars)
                    target_values_list = list(target_values_tuple)
                    condition_vars_list = list(condition_vars)
                    condition_values_list = list(condition_values_tuple)

                    cond_prob = self.get_conditional_probability(
                        condition_vars_list,
                        condition_values_list,
                        target_vars_list,
                        target_values_list,
                    )

                    target_var_names = [self.variable_names[idx] for idx in target_vars]
                    condition_var_names = [self.variable_names[idx] for idx in condition_vars]

                    target_expr = ", ".join(
                        f"{var}={val}"
                        for var, val in zip(target_var_names, target_values_tuple)
                    )
                    condition_expr = ", ".join(
                        f"{var}={val}"
                        for var, val in zip(condition_var_names, condition_values_tuple)
                    )

                    prob_expr = f"P({target_expr} | {condition_expr})"

                    print(f"{prob_expr:30} | {cond_prob:.6f}")

        print(
            "\nNote: Only showing combinations where target and condition variables don't overlap."
        )

    def save_to_file(self, file_path: str):
        with open(file_path, "w") as f:
            f.write("variables: " + ",".join(self.variable_names) + "\n")
            for i in range(2**self.num_variables):
                binary_tuple = tuple((i >> j) & 1 for j in range(self.num_variables))
                prob = self.joint_probabilities.get(binary_tuple, 0.0)
                binary_str = "".join(str(bit) for bit in binary_tuple)
                f.write(f"{binary_str}: {prob}\n")

    # --- Statistics wrappers using stats module
    def marginal_distribution(self, variables: List[int]) -> Dict[Tuple[int, ...], float]:
        return stats.marginal_distribution(self.joint_probabilities, variables)

    def entropy(self, variables: Optional[List[int]] = None, base: float = 2.0) -> float:
        return stats.entropy(self.joint_probabilities, variables, base=base)

    def conditional_entropy(self, target_vars: List[int], given_vars: List[int], base: float = 2.0) -> float:
        return stats.conditional_entropy(self.joint_probabilities, target_vars, given_vars, base=base)

    def mutual_information(self, var1: int, var2: int, base: float = 2.0) -> float:
        return stats.mutual_information(self.joint_probabilities, var1, var2, base=base)

    def odds_ratio(self, exposure: int, outcome: int) -> Optional[float]:
        return stats.odds_ratio(self.get_marginal_probability, exposure, outcome)

    def relative_risk(self, exposure: int, outcome: int) -> Optional[float]:
        return stats.relative_risk(self.get_conditional_probability, exposure, outcome)

    def sample(self, n: int = 1):
        return stats.sample(self.joint_probabilities, n=n)
