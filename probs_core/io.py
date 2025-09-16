import os
import itertools
from typing import List, Optional, Tuple
import math


def load_joint_prob_file(file_path: str, variable_names: Optional[List[str]] = None) -> Tuple[int, List[float], Optional[List[str]]]:
    """Read a joint probability file and return (num_variables, joint_probs_list, names_to_use).

    The returned `joint_probs_list` is the same format expected by ProbabilitySystem.__init__:
    a list of 2^n - 1 probabilities (the last probability is implied and computed).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    joint_probs_dict = {}
    file_variable_names = None

    with open(file_path, "r") as f:
        for line_num, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue

            # Skip full-line comments
            if line.startswith("#"):
                continue

            # Support trailing inline comments after probability entries or header lines.
            # We only split on the first '#'. This is simple and sufficient because the format
            # does not currently allow string literals containing '#'.
            if '#' in line:
                line = line.split('#', 1)[0].rstrip()
                if not line:
                    # Line was only a comment after stripping
                    continue

            # Variable header line detection (case-insensitive) after stripping inline comment
            if line.lower().startswith("variables:"):
                names_part = line[len("variables:") :].strip()
                if '#' in names_part:
                    # Extra safety: strip again if someone put comment after names without preceding space
                    names_part = names_part.split('#', 1)[0].rstrip()
                file_variable_names = [name.strip() for name in names_part.split(",") if name.strip()]
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

    # Determine missing combinations and apply requested policy:
    #   * If exactly one combination missing -> infer its probability so total sums to 1 (if feasible).
    #   * If more than one missing -> assign 0.0 to all missing combinations (sparse specification).
    all_combinations = set(itertools.product([0, 1], repeat=num_variables))
    provided = set(joint_probs_dict.keys())
    missing = list(all_combinations - provided)

    if len(missing) == 1:
        # Infer last probability
        remaining_prob = 1.0 - sum(joint_probs_dict.values())
        if remaining_prob < -1e-10:
            raise ValueError(
                f"Joint probabilities sum to more than 1 before inferring final value: {sum(joint_probs_dict.values())}"
            )
        joint_probs_dict[missing[0]] = max(0.0, remaining_prob)
    elif len(missing) > 1:
        # Sparse specification: fill all missing with zero.
        for combo in missing:
            joint_probs_dict[combo] = 0.0

    # Now we have a full table. Optionally normalize if modest deviation from 1.0 (user convenience).
    total_prob = sum(joint_probs_dict.values())
    if abs(total_prob - 1.0) > 1e-6:
        deviation = abs(total_prob - 1.0)
        if total_prob > 0 and deviation / total_prob <= 0.05:
            print(
                f"Warning: Joint probabilities sum to {total_prob:.9f}; auto-normalizing to 1.0."
            )
            factor = 1.0 / total_prob
            for k in list(joint_probs_dict.keys()):
                joint_probs_dict[k] *= factor
        else:
            if total_prob - 1.0 > 0:
                raise ValueError(
                    f"Joint probabilities sum to {total_prob}; deviation too large for auto-normalization"
                )

    sorted_combinations = sorted(joint_probs_dict.keys())
    joint_probs = [joint_probs_dict[combo] for combo in sorted_combinations[:-1]]

    return num_variables, joint_probs, names_to_use


def write_joint_prob_file(file_path: str, variable_names: List[str], joint_probabilities: dict):
    """Write a joint probability table to a file. The joint_probabilities dict maps binary tuples to probabilities."""
    with open(file_path, "w") as f:
        f.write("variables: " + ",".join(variable_names) + "\n")
        for i in range(2**len(variable_names)):
            binary_tuple = tuple((i >> j) & 1 for j in range(len(variable_names)))
            prob = joint_probabilities.get(binary_tuple, 0.0)
            binary_str = "".join(str(bit) for bit in binary_tuple)
            # Always save in fixed-point with 10 decimal places (no scientific notation)
            f.write(f"{binary_str}: {prob:.10f}\n")


# ----------------- Bayesian Network (.net) format support -----------------
def load_network_file(file_path: str, variable_names: Optional[List[str]] = None) -> Tuple[int, List[float], Optional[List[str]]]:
    """Parse a Bayesian network specification (.net) and return joint probability list.

    Format:
        variables: A, B, C ...
        A : None
        1: 0.3   # P(A=1)
        B : A
        1: 0.8   # P(B=1|A=1)
        0: 0.1   # P(B=1|A=0)

    For nodes with parents, each line pattern is <parent_assignment_bits>: <prob_of_child_being_1>.
    Parent assignment bits ordered according to declared parent list.
    Comments (#) allowed full-line or trailing.
    Missing parent combinations -> error.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as f:
        raw_lines = f.readlines()

    # Preprocess: strip comments and skip blanks
    cleaned = []
    for line_num, raw in enumerate(raw_lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:
            line = line.split('#',1)[0].strip()
            if not line:
                continue
        cleaned.append((line_num, line))

    if not cleaned or not cleaned[0][1].lower().startswith('variables:'):
        raise ValueError("Network file must start with 'variables:' line")

    first = cleaned[0][1]
    file_vars = [v.strip() for v in first[len('variables:'):].split(',') if v.strip()]
    if not file_vars:
        raise ValueError("No variables declared in network file")

    names_to_use = variable_names or file_vars
    num_variables = len(names_to_use)
    name_index = {n: i for i,n in enumerate(names_to_use)}

    # Parse blocks: each block starts with '<Child>: <parents or None>' then CPT lines until next block or EOF
    idx = 1
    parents_map = {}
    cpt_map = {}  # child -> dict[parent_assignment_tuple] = P(child=1 | parents)

    while idx < len(cleaned):
        line_num, line = cleaned[idx]
        if ':' not in line:
            raise ValueError(f"Invalid block header at line {line_num}: {line}")
        header_left, header_right = [x.strip() for x in line.split(':',1)]
        child = header_left
        parent_part = header_right
        if child not in name_index:
            raise ValueError(f"Unknown variable '{child}' in header at line {line_num}")
        if child in parents_map:
            raise ValueError(f"Duplicate definition for child '{child}' at line {line_num}")
        if parent_part.lower() == 'none' or parent_part == '':
            parents = []
        else:
            parents = [p.strip() for p in parent_part.split(',') if p.strip()]
            for p in parents:
                if p not in name_index:
                    raise ValueError(f"Unknown parent '{p}' for child '{child}' at line {line_num}")
                if p == child:
                    raise ValueError(f"Variable '{child}' cannot be its own parent (line {line_num})")
        parents_map[child] = parents
        idx += 1

        local_cpt = {}
        needed = 1 if len(parents) == 0 else 2 ** len(parents)

        while idx < len(cleaned):
            ln, lcontent = cleaned[idx]
            # Heuristic: a new header starts with a token that is a declared variable followed by ':' and not a pure 0/1 pattern appropriate for parent count we still need.
            if ':' in lcontent:
                candidate_left = lcontent.split(':',1)[0].strip()
                if candidate_left in name_index and (len(parents) == 0 or not (set(candidate_left) <= {'0','1'} and len(candidate_left)==len(parents))):
                    # Start of next variable block
                    break
            if ':' not in lcontent:
                break
            left, right = [x.strip() for x in lcontent.split(':',1)]
            if len(parents) == 0:
                if left not in {'0','1'}:
                    raise ValueError(f"Expected '1:' or '0:' for parentless variable {child} at line {ln}")
                try:
                    pval = float(right)
                except ValueError:
                    raise ValueError(f"Invalid probability at line {ln}: {right}")
                if not (0 <= pval <= 1):
                    raise ValueError(f"Probability out of range at line {ln}: {pval}")
                local_cpt[()] = pval if left == '1' else 1 - pval
                idx += 1
                break
            else:
                pattern = left
                if not all(ch in '01' for ch in pattern) or len(pattern) != len(parents):
                    raise ValueError(f"Invalid parent assignment pattern '{pattern}' for child {child} at line {ln}")
                try:
                    pval = float(right)
                except ValueError:
                    raise ValueError(f"Invalid probability at line {ln}: {right}")
                if not (0 <= pval <= 1):
                    raise ValueError(f"Probability out of range at line {ln}: {pval}")
                parent_tuple = tuple(int(b) for b in pattern)
                if parent_tuple in local_cpt:
                    raise ValueError(f"Duplicate CPT entry for {child} pattern {pattern} (line {ln})")
                local_cpt[parent_tuple] = pval
                idx += 1
                if len(local_cpt) == needed:
                    break

        if len(parents) == 0 and len(local_cpt) != 1:
            raise ValueError(f"Parentless variable {child} must have exactly one probability line")
        if len(parents) > 0 and len(local_cpt) != needed:
            raise ValueError(f"Incomplete CPT for {child}; expected {needed} entries, got {len(local_cpt)}")
        cpt_map[child] = local_cpt

    # Ensure every declared variable was defined
    for var in names_to_use:
        if var not in parents_map:
            raise ValueError(f"Variable '{var}' declared but no CPT provided")

    # Build joint probabilities by iterating over all assignments
    joint_probs_dict = {}
    for assignment_index in range(2 ** num_variables):
        bits = [(assignment_index >> (num_variables - i - 1)) & 1 for i in range(num_variables)]
        prob = 1.0
        for child in names_to_use:
            child_idx = name_index[child]
            child_value = bits[child_idx]
            parents = parents_map[child]
            parent_bits = tuple(bits[name_index[p]] for p in parents)
            p_child_1 = cpt_map[child][parent_bits]
            prob *= p_child_1 if child_value == 1 else (1 - p_child_1)
            if prob == 0.0:
                break
        joint_probs_dict[tuple(bits)] = prob

    # Normalize to handle rounding/consistency
    total = sum(joint_probs_dict.values())
    if total <= 0:
        raise ValueError("Total probability computed from network is zero")
    if abs(total - 1.0) > 1e-8:
        for k in joint_probs_dict:
            joint_probs_dict[k] /= total

    # Convert to list the ProbabilitySystem expects (omit last lexicographic combination)
    sorted_combinations = sorted(joint_probs_dict.keys())
    joint_probs = [joint_probs_dict[c] for c in sorted_combinations[:-1]]
    return num_variables, joint_probs, names_to_use
