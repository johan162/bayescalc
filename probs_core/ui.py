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
    sorted_entries = sorted(joint_probabilities.items())
    
    # Limit to first 64 rows to avoid overwhelming output
    max_rows = 64
    entries_to_show = sorted_entries[:max_rows]
    
    for values, prob in entries_to_show:
        row = " | ".join(str(val) for val in values)
        print(f"{row} | {fmt(prob)}")
    
    # Show summary if table was truncated
    total_entries = len(sorted_entries)
    if total_entries > max_rows:
        print(f"\n... (showing first {max_rows} of {total_entries} entries)")
        print("Use 'table' command to see the full table.")


def pretty_print_joint_table_full(variable_names: List[str], joint_probabilities: dict):
    """Print the complete joint probability table without row limits.

    Args:
      variable_names: ordered list of variable names.
      joint_probabilities: dict mapping state tuples to probabilities.
    """
    print("\nFull Joint Probability Table:")
    print("=============================\n")

    header = " | ".join(variable_names) + " | Probability"
    print(header)
    print("-" * len(header))

    from .formatting import fmt
    sorted_entries = sorted(joint_probabilities.items())
    
    for values, prob in sorted_entries:
        row = " | ".join(str(val) for val in values)
        print(f"{row} | {fmt(prob)}")
    
    total_entries = len(sorted_entries)
    print(f"\nTotal entries: {total_entries}")


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


def pretty_print_contingency_table(variable_names: List[str], joint_probabilities: dict, get_marginal):
    """Print contingency tables for variable combinations.

    For 2 variables: prints a single 2x2 contingency table.
    For 3-4 variables: prints partitioned 2x2 tables for each unique combination of the remaining variables.
    For more than 4 variables: prints an error message.

    Args:
      variable_names: list of variable names.
      joint_probabilities: dict mapping state tuples to probabilities.
      get_marginal: callable to fetch marginal probability given indices and values.
    """
    num_vars = len(variable_names)

    if num_vars < 2:
        print("Error: Need at least 2 variables for contingency table.")
        return

    if num_vars > 4:
        print("Error: Contingency table supports up to 4 variables.")
        return

    print("\nContingency Table(s):")
    print("=" * 50)

    if num_vars == 2:
        # Simple 2x2 table
        _print_2x2_contingency_table(variable_names, get_marginal)
    else:
        # Partitioned tables
        _print_partitioned_contingency_tables(variable_names, get_marginal, joint_probabilities)


def _print_2x2_contingency_table(variable_names: List[str], get_marginal):
    """Print a single 2x2 contingency table for two variables."""
    var1, var2 = variable_names[0], variable_names[1]
    var1_idx, var2_idx = 0, 1

    # Get the four cell values
    p00 = get_marginal([var1_idx, var2_idx], [0, 0])  # P(var1=0, var2=0)
    p01 = get_marginal([var1_idx, var2_idx], [0, 1])  # P(var1=0, var2=1)
    p10 = get_marginal([var1_idx, var2_idx], [1, 0])  # P(var1=1, var2=0)
    p11 = get_marginal([var1_idx, var2_idx], [1, 1])  # P(var1=1, var2=1)

    # Calculate row and column totals
    row1_total = p00 + p01
    row2_total = p10 + p11
    col1_total = p00 + p10
    col2_total = p01 + p11
    total = row1_total + row2_total

    from .formatting import fmt

    # Print the table
    print(f"\n{var1} \\ {var2}")
    print("           0            1         Total")
    print("-" * 45)
    print(f"0  {fmt(p00):>12} {fmt(p01):>12} {fmt(row1_total):>12}")
    print(f"1  {fmt(p10):>12} {fmt(p11):>12} {fmt(row2_total):>12}")
    print("-" * 45)
    print(f"Total  {fmt(col1_total):>8} {fmt(col2_total):>12} {fmt(total):>12}")



def _print_partitioned_contingency_tables(variable_names: List[str], get_marginal, joint_probabilities: dict):
    """Print partitioned 2x2 contingency tables for each combination of conditioning variables."""
    from itertools import combinations, product

    num_vars = len(variable_names)

    # For 3 variables: condition on 1 variable, show 2x2 for the other 2
    # For 4 variables: condition on 2 variables, show 2x2 for the other 2
    if num_vars == 3:
        condition_size = 1
        table_vars_size = 2
    else:  # num_vars == 4
        condition_size = 2
        table_vars_size = 2

    # Get all combinations for conditioning variables
    all_indices = list(range(num_vars))
    condition_combos = list(combinations(all_indices, condition_size))

    for condition_combo in condition_combos:
        condition_indices = list(condition_combo)
        table_indices = [i for i in all_indices if i not in condition_indices]

        # Get variable names
        condition_vars = [variable_names[i] for i in condition_indices]
        table_vars = [variable_names[i] for i in table_indices]

        # For each possible combination of condition values
        for condition_values in product([0, 1], repeat=condition_size):
            # Print header for this partition
            condition_str = ", ".join(f"{var}={val}" for var, val in zip(condition_vars, condition_values))
            print(f"\nGiven: {condition_str}")
            print("-" * 40)

            # Print the 2x2 table for this condition
            _print_2x2_contingency_table_for_condition(table_vars, table_indices, condition_indices, list(condition_values), joint_probabilities)


def _print_2x2_contingency_table_for_condition(table_vars: List[str], table_indices: List[int], condition_indices: List[int], condition_values: List[int], joint_probabilities: dict):
    """Print a 2x2 contingency table conditioned on specific variable values."""
    var1, var2 = table_vars[0], table_vars[1]
    var1_idx, var2_idx = table_indices[0], table_indices[1]

    # Compute conditional probabilities for each cell
    p00 = _get_conditional_probability(joint_probabilities, [var1_idx, var2_idx], [0, 0], condition_indices, condition_values)
    p01 = _get_conditional_probability(joint_probabilities, [var1_idx, var2_idx], [0, 1], condition_indices, condition_values)
    p10 = _get_conditional_probability(joint_probabilities, [var1_idx, var2_idx], [1, 0], condition_indices, condition_values)
    p11 = _get_conditional_probability(joint_probabilities, [var1_idx, var2_idx], [1, 1], condition_indices, condition_values)

    # Calculate row and column totals
    row1_total = p00 + p01
    row2_total = p10 + p11
    col1_total = p00 + p10
    col2_total = p01 + p11
    total = row1_total + row2_total

    from .formatting import fmt

    # Print the table
    print(f"\n{var1} \\ {var2}")
    print("           0            1         Total")
    print("-" * 45)
    print(f"0  {fmt(p00):>12} {fmt(p01):>12} {fmt(row1_total):>12}")
    print(f"1  {fmt(p10):>12} {fmt(p11):>12} {fmt(row2_total):>12}")
    print("-" * 45)
    print(f"Total  {fmt(col1_total):>8} {fmt(col2_total):>12} {fmt(total):>12}")


def _get_conditional_probability(joint_probabilities: dict, target_indices: List[int], target_values: List[int], condition_indices: List[int], condition_values: List[int]) -> float:
    """Compute conditional probability P(target=target_values | condition=condition_values)."""
    # Sum joint probabilities for the target and condition
    joint_prob = 0.0
    condition_prob = 0.0

    for state, prob in joint_probabilities.items():
        # Check if condition matches
        condition_match = all(state[i] == condition_values[j] for j, i in enumerate(condition_indices))
        if condition_match:
            condition_prob += prob
            # Check if target also matches
            target_match = all(state[i] == target_values[j] for j, i in enumerate(target_indices))
            if target_match:
                joint_prob += prob

    if condition_prob == 0:
        return 0.0

    return joint_prob / condition_prob
