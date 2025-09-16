import itertools
from typing import List, Tuple


def pretty_print_joint_table(variable_names: List[str], joint_probabilities: dict):
    """Print a simple table of joint probability entries.

    Args:
      variable_names: ordered list of variable names.
      joint_probabilities: dict mapping state tuples to probabilities.
    """
    print("\nJoint Probability Table:")
    print("========================\n")

    header = " | ".join(variable_names) + " | Probability"
    print(header)
    print("-" * len(header))

    from .formatting import fmt
    for values, prob in sorted(joint_probabilities.items()):
        row = " | ".join(str(val) for val in values)
        print(f"{row} | {fmt(prob)}")


def pretty_print_marginals(variable_names: List[str], joint_probabilities: dict, get_marginal):
    """Print marginal probability summaries for the provided joint table.

    Args:
      variable_names: ordered list of variable names.
      joint_probabilities: dictionary of joint probabilities (unused directly here
        except for formatting); the function uses `get_marginal` to obtain values.
      get_marginal: callable to fetch marginal probability given indices and values.
    """
    print("\nMarginal Probabilities:")
    print("======================\n")

    print("Single variable marginals:")
    from .formatting import fmt
    for i, var_name in enumerate(variable_names):
        p0 = get_marginal([i], [0])
        p1 = get_marginal([i], [1])
        print(f"P({var_name}=0) = {fmt(p0)},  P({var_name}=1) = {fmt(p1)}")

    if len(variable_names) >= 2:
        print("\nTwo variable marginals:")
        for i, var_i in enumerate(variable_names):
            for j in range(i + 1, len(variable_names)):
                var_j = variable_names[j]
                for val_i in [0, 1]:
                    for val_j in [0, 1]:
                        p = get_marginal([i, j], [val_i, val_j])
                        print(f"P({var_i}={val_i}, {var_j}={val_j}) = {fmt(p)}")


def pretty_print_independence_table(variable_names: List[str], num_variables: int, is_independent):
    """Print pairwise independence results for all variable pairs.

    Args:
      variable_names: list of variable names for display.
      num_variables: number of variables in the system.
      is_independent: callable taking two indices (i, j) and returning bool.
    """
    if num_variables < 2:
        print("Need at least 2 variables to test independence.")
        return

    print("\nIndependence Table:")
    print("=================\n")

    print(f"{'Variables':15} | {'Independent?' }")
    print("-" * 30)

    for i in range(num_variables):
        for j in range(i + 1, num_variables):
            var_i = variable_names[i]
            var_j = variable_names[j]
            is_indep = is_independent(i, j)
            status = "Yes" if is_indep else "No"
            print(f"{var_i} and {var_j:10} | {status}")


def pretty_print_conditional_independence_table(variable_names: List[str], num_variables: int, is_conditionally_independent):
    """Print conditional independence (i _||_ j | k) results for triples.

    Args:
      variable_names: list of variable names for display.
      num_variables: number of variables in the system.
      is_conditionally_independent: callable taking three indices (i, j, k) and returning bool.
    """
    if num_variables < 3:
        print("Need at least 3 variables to test conditional independence.")
        return

    print("\nConditional Independence Table:")
    print("=============================\n")

    print(f"{'Variables':20} | {'Given':10} | {'Conditionally Independent?' }")
    print("-" * 60)

    for i in range(num_variables):
        for j in range(i + 1, num_variables):
            for k in range(num_variables):
                if k != i and k != j:
                    var_i = variable_names[i]
                    var_j = variable_names[j]
                    var_k = variable_names[k]

                    is_cond_indep = is_conditionally_independent(i, j, k)
                    status = "Yes" if is_cond_indep else "No"

                    print(f"{var_i} and {var_j:10} | {var_k:10} | {status}")


def pretty_print_conditional_probabilities(variable_names: List[str], num_variables: int, get_conditional, target_size: int, condition_size: int):
    """Display conditional probabilities for all non-overlapping variable combos.

    Args:
      variable_names: list of variable names.
      num_variables: total variables available.
      get_conditional: callable to compute conditional probabilities.
      target_size: size of the left-side tuple (n in P(target|condition)).
      condition_size: size of the conditioning tuple (m in P(target|condition)).
    """
    if target_size < 1 or target_size > num_variables:
        print(f"Error: Target size must be between 1 and {num_variables}.")
        return

    if condition_size < 1 or condition_size > num_variables:
        print(f"Error: Condition size must be between 1 and {num_variables}.")
        return

    if target_size + condition_size > num_variables:
        print(
            f"Error: Combined size (n+m={target_size+condition_size}) exceeds number of variables ({num_variables})."
        )
        return

    print(
        f"\nConditional Probabilities Table: {target_size}-tuples given {condition_size}-tuples"
    )
    print("=" * 60)

    from itertools import combinations

    target_var_combos = list(combinations(range(num_variables), target_size))
    condition_var_combos = list(combinations(range(num_variables), condition_size))

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

                cond_prob = get_conditional(
                    condition_vars_list,
                    condition_values_list,
                    target_vars_list,
                    target_values_list,
                )

                target_var_names = [variable_names[idx] for idx in target_vars]
                condition_var_names = [variable_names[idx] for idx in condition_vars]

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
