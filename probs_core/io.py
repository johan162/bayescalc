import os
import itertools
from typing import List, Optional, Tuple, Dict, Any
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
def load_network_file(file_path: str, variable_names: Optional[List[str]] = None):  # dynamic return signature for compatibility
    """Dispatch to legacy binary network parser or new multi-valued parser based on syntax.

    New multi-valued markers: '{{' in variable line or '<-' parent specification lines.
    Returns either (num_variables, joint_probs, variable_names) for legacy or
    (num_variables, joint_probs_full, variable_names, variable_states) for multi-valued
    where joint_probs_full enumerates full joint (Π card_i entries) for constructor path.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        raw = f.read()
    # Simple detection, this a bit heuristic but should be reliable enough
    if '<-' in raw and not 'variables:' in raw:
        return _load_network_file_multivalued(raw, variable_names)
    else:
        return _load_network_file_binary(raw, variable_names)


def _load_network_file_binary(raw_text: str, variable_names: Optional[List[str]]):
    """Previous binary-only implementation extracted and adapted for dispatch."""
    raw_lines = raw_text.splitlines()
    cleaned = []
    file_vars = []
    for line_num, raw in enumerate(raw_lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:
            line = line.split('#',1)[0].strip()
            if not line:
                continue
        if line.lower().startswith('variable '):
            var_name = line[len('variable '):].split()[0].strip()
            if var_name:
                file_vars.append(var_name)
            continue
        cleaned.append((line_num, line))
    if cleaned and cleaned[0][1].lower().startswith('variables:'):
        first = cleaned[0][1]
        file_vars = [v.strip() for v in first[len('variables:'):].split(',') if v.strip()]
        cleaned = cleaned[1:]
    if not file_vars:
        raise ValueError("No variables declared in network file (use 'variable NAME' or 'variables: ...')")
    names_to_use = variable_names or file_vars
    num_variables = len(names_to_use)
    name_index = {n: i for i,n in enumerate(names_to_use)}
    idx = 0
    parents_map = {}
    cpt_map = {}
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
            if ':' in lcontent:
                candidate_left = lcontent.split(':',1)[0].strip()
                if candidate_left in name_index and (len(parents) == 0 or not (set(candidate_left) <= {'0','1'} and len(candidate_left)==len(parents))):
                    break
            if len(parents) == 0:
                if ':' in lcontent:
                    left, right = [x.strip() for x in lcontent.split(':',1)]
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
                    try:
                        pval = float(lcontent)
                    except ValueError:
                        raise ValueError(f"Invalid probability at line {ln}: {lcontent}")
                    if not (0 <= pval <= 1):
                        raise ValueError(f"Probability out of range at line {ln}: {pval}")
                    local_cpt[()] = pval
                    idx += 1
                    break
            else:
                if ':' not in lcontent:
                    break
                left, right = [x.strip() for x in lcontent.split(':',1)]
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
    for var in names_to_use:
        if var not in parents_map:
            raise ValueError(f"Variable '{var}' declared but no CPT provided")
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
    total = sum(joint_probs_dict.values())
    if total <= 0:
        raise ValueError("Total probability computed from network is zero")
    if abs(total - 1.0) > 1e-8:
        for k in joint_probs_dict:
            joint_probs_dict[k] /= total
    sorted_combinations = sorted(joint_probs_dict.keys())
    joint_probs = [joint_probs_dict[c] for c in sorted_combinations[:-1]]
    return len(names_to_use), joint_probs, names_to_use


def _load_network_file_multivalued(raw_text: str, variable_names: Optional[List[str]]):
    """Parse new multi-valued network syntax.

    Syntax summary:
        variable VarName {state1, state2, ...}
        variable BoolVar            # implies binary {0,1}
        Child <- None
        Child <- (Parent1, Parent2)
        CPT lines root: state: prob
        CPT lines child: (child_state | p1_state, p2_state, ...) : prob
    For each parent assignment, probabilities over child states must sum to 1 (missing entries contribute 0).
    """
    lines_raw = raw_text.splitlines()
    # Strip comments and retain (lineno, content)
    processed: List[Tuple[int,str]] = []
    for ln, raw in enumerate(lines_raw, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:
            line = line.split('#',1)[0].strip()
            if not line:
                continue
        processed.append((ln, line))

    # First pass: variable declarations
    variable_states: Dict[str, List[str]] = {}
    order: List[str] = []
    remaining: List[Tuple[int,str]] = []
    for ln, line in processed:
        if line.lower().startswith('variable '):
            rest = line[len('variable '):].strip()
            if '{' in rest and '}' in rest:
                name, states_part = rest.split('{',1)
                name = name.strip()
                states_str = states_part.split('}',1)[0]
                states = [s.strip() for s in states_str.split(',') if s.strip()]
                if len(states) < 2:
                    raise ValueError(f"Variable {name} must have at least two states at line {ln}")
                if name in variable_states:
                    raise ValueError(f"Duplicate variable declaration {name} line {ln}")
                variable_states[name] = states
                order.append(name)
            else:
                name = rest.split()[0]
                if name in variable_states:
                    raise ValueError(f"Duplicate variable declaration {name} line {ln}")
                variable_states[name] = ["0","1"]  # implicit boolean
                order.append(name)
        else:
            remaining.append((ln,line))
    if not order:
        raise ValueError("No variables declared in multi-valued network file. Have you added a ':' by mistake after the 'variable' keyword?")
    if variable_names:
        # Optionally override order subset (must match length)
        if len(variable_names) != len(order):
            raise ValueError("Provided variable_names length mismatch in network parse")
        order = variable_names
    name_index = {n:i for i,n in enumerate(order)}

    # Second pass: parent declarations and CPTs
    parents: Dict[str, List[str]] = {}
    cpt_entries: Dict[str, Dict[Tuple[int, ...], Dict[int,float]]] = {}
    # structure: child -> parent_state_index_tuple -> {child_state_index: prob}
    current_child = None
    for ln, line in remaining:
        if '<-' in line:
            left, right = [x.strip() for x in line.split('<-',1)]
            child = left
            if child not in name_index:
                raise ValueError(f"Unknown child '{child}' at line {ln}")
            if child in parents:
                raise ValueError(f"Duplicate parent assignment for {child} (line {ln})")
            right = right.strip()
            if right.lower() == 'none':
                plist: List[str] = []
            else:
                if not (right.startswith('(') and right.endswith(')')):
                    raise ValueError(f"Parent list for {child} must be in parentheses at line {ln}")
                inner = right[1:-1].strip()
                plist = [p.strip() for p in inner.split(',') if p.strip()]
                for p in plist:
                    if p not in name_index:
                        raise ValueError(f"Unknown parent '{p}' for child {child} (line {ln})")
                    if p == child:
                        raise ValueError(f"Variable {child} cannot be its own parent (line {ln})")
            parents[child] = plist
            cpt_entries[child] = {}
            current_child = child
            continue
        # CPT line expected
        if current_child is None:
            raise ValueError(f"CPT line without preceding child declaration at line {ln}: {line}")
        # Root variable line: state: prob
        if line.startswith('('):
            # (child_state | parent_state1, parent_state2, ...) : prob
            if ')' not in line or ':' not in line:
                raise ValueError(f"Invalid CPT tuple line at {ln}: {line}")
            tuple_part, prob_part = line.split(':',1)
            prob_str = prob_part.strip()
            try:
                pval = float(prob_str)
            except ValueError:
                raise ValueError(f"Invalid probability '{prob_str}' at line {ln}")
            inside = tuple_part.strip()[1:-1].strip()  # remove parentheses
            if '|' not in inside:
                raise ValueError(f"Missing '|' in CPT entry at line {ln}")
            left_state, right_states = [x.strip() for x in inside.split('|',1)]
            child_state = left_state
            parent_state_tokens = [t.strip() for t in right_states.split(',') if t.strip()]
            plist = parents[current_child]
            if len(parent_state_tokens) != len(plist):
                raise ValueError(f"Parent state count mismatch at line {ln}")
            # Map state names to indices
            child_state_idx = _state_index(variable_states, current_child, child_state, ln)
            parent_state_indices = []
            for p_name, s_name in zip(plist, parent_state_tokens):
                parent_state_indices.append(_state_index(variable_states, p_name, s_name, ln))
            parent_tuple = tuple(parent_state_indices)
            slot = cpt_entries[current_child].setdefault(parent_tuple, {})
            if child_state_idx in slot:
                raise ValueError(f"Duplicate CPT probability for {current_child} state {child_state} at line {ln}")
            if not (0 <= pval <= 1):
                raise ValueError(f"Probability out of range at line {ln}")
            slot[child_state_idx] = pval
        else:
            # Assume root variable line: state: prob
            if ':' not in line:
                raise ValueError(f"Invalid root CPT line at {ln}: {line}")
            state_part, prob_part = [x.strip() for x in line.split(':',1)]
            plist = parents.get(current_child, [])
            if plist:
                raise ValueError(f"Non-parenthesized CPT line but {current_child} has parents (line {ln})")
            child_state = state_part
            pval = float(prob_part)
            child_state_idx = _state_index(variable_states, current_child, child_state, ln)
            slot = cpt_entries[current_child].setdefault((), {})
            if child_state_idx in slot:
                raise ValueError(f"Duplicate root CPT entry for state {child_state} line {ln}")
            if not (0 <= pval <= 1):
                raise ValueError(f"Probability out of range at line {ln}")
            slot[child_state_idx] = pval
    # Ensure each variable has a parent declaration
    for v in order:
        if v not in parents:
            raise ValueError(f"Variable {v} declared but no parent specification '<-' found")
    # Validate probability sums per parent combination (must sum to 1.0)
    for child, parent_dict in cpt_entries.items():
        card_child = len(variable_states[child])
        plist = parents[child]
        parent_cards = [len(variable_states[p]) for p in plist]

        if plist:
            all_parent_assignments = list(itertools.product(*[range(c) for c in parent_cards]))
        else:
            all_parent_assignments = [()]

        for pt in all_parent_assignments:
            probs_map = parent_dict.get(pt, {})

            # Check if all variables are boolean.
            all_boolean = all(len(states) == 2 for states in variable_states.values())

            if all_boolean and card_child == 2:
                # Compact CPT logic for boolean variables
                p0_present = 0 in probs_map
                p1_present = 1 in probs_map

                if p0_present and p1_present:
                    # Both provided, check if they sum to 1.0
                    if abs(probs_map[0] + probs_map[1] - 1.0) > 1e-8:
                        raise ValueError(f"Probabilities for {child} given parents {plist} assignment {pt} do not sum to 1.0")
                elif p0_present:
                    probs_map[1] = 1.0 - probs_map[0]
                elif p1_present:
                    probs_map[0] = 1.0 - probs_map[1]
                else:
                    raise ValueError(f"Incomplete CPT for {child} given parents {plist} assignment {pt}. Exactly one of P(0|...) or P(1|...) must be specified for boolean networks.")
            else:
                # Original logic for non-boolean or mixed networks
                total_p = sum(probs_map.get(s, 0.0) for s in range(card_child))
                if abs(total_p - 1.0) > 1e-8:
                    raise ValueError(f"Probabilities for {child} given parents {plist} assignment {pt} sum to {total_p}, not 1.0")

    # Build joint distribution via factorization (enumerate all assignments)
    cards = [len(variable_states[v]) for v in order]
    all_assignments = itertools.product(*[range(c) for c in cards])
    name_to_states = {v: variable_states[v] for v in order}
    joint: Dict[Tuple[int,...], float] = {}
    for assignment in all_assignments:
        prob = 1.0
        for vidx, var_name in enumerate(order):
            state_idx = assignment[vidx]
            plist = parents[var_name]
            parent_state_indices = tuple(assignment[order.index(p)] for p in plist)
            # fetch p(child_state | parent_tuple)
            entry = cpt_entries[var_name].get(parent_state_indices, {})
            p_state = entry.get(state_idx, 0.0)
            prob *= p_state
            if prob == 0.0:
                break
        joint[assignment] = prob
    total = sum(joint.values())
    if total <= 0:
        raise ValueError("Total joint probability zero; check CPTs")
    # Normalize minor deviation
    if abs(total - 1.0) > 1e-8:
        for k in list(joint.keys()):
            joint[k] /= total
    joint_list = [joint[a] for a in sorted(joint.keys())]
    # Return extended signature
    variable_states_ordered = [variable_states[v] for v in order]
    return len(order), joint_list, order, variable_states_ordered


def _state_index(var_states: Dict[str, List[str]], var: str, state: str, ln: int) -> int:
    if var not in var_states:
        raise ValueError(f"Unknown variable '{var}' at line {ln}")
    states = var_states[var]
    if state not in states:
        raise ValueError(f"Unknown state '{state}' for variable '{var}' (line {ln})")
    return states.index(state)
