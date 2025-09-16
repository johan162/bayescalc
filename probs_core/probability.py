from typing import Dict, List, Tuple, Optional, Union
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


def _cartesian_product(lists: List[range]):
    """Efficient cartesian product returning lists of indices."""
    if not lists:
        yield ()
        return
    for combo in itertools.product(*lists):
        yield combo


class ProbabilitySystem:
    """High-level probability API supporting binary and multi-valued discrete variables.

    Backward compatibility: original constructor signature still works for binary variables
    (joint_probs list of length 2^n - 1). For multi-valued variables, supply `variable_states`
    and a full joint list of length Π card_i.
    """

    def __init__(
        self,
        num_variables: int,
        joint_probs: List[float],
        variable_names: Optional[List[str]] = None,
        variable_states: Optional[List[List[str]]] = None,
    ) -> None:
        self.num_variables = num_variables

        # Variable names
        if variable_names is not None:
            if len(variable_names) != num_variables:
                raise ValueError(
                    f"Expected {num_variables} variable names, got {len(variable_names)}"
                )
            self.variable_names = variable_names
        else:
            self.variable_names = [chr(65 + i) for i in range(num_variables)]

        # States (cardinalities)
        if variable_states is None:
            variable_states = [["0", "1"] for _ in range(num_variables)]
        if len(variable_states) != num_variables:
            raise ValueError("variable_states length mismatch num_variables")

        self.variable_states: List[List[str]] = []
        self.state_name_to_index: List[Dict[str, int]] = []
        for vs in variable_states:
            if len(vs) < 2:
                raise ValueError("Each variable must have at least 2 states")
            mapping: Dict[str, int] = {}
            cleaned: List[str] = []
            for idx, raw_name in enumerate(vs):
                name = raw_name.strip()
                if name in mapping:
                    raise ValueError(f"Duplicate state name '{name}' in {vs}")
                mapping[name] = idx
                cleaned.append(name)
            self.variable_states.append(cleaned)
            self.state_name_to_index.append(mapping)
        self.cardinalities = [len(vs) for vs in self.variable_states]

        all_binary = all(c == 2 for c in self.cardinalities)
        self.joint_probabilities: Dict[Tuple[int, ...], float] = {}
        if all_binary and len(joint_probs) == 2**num_variables - 1:
            # Legacy path with implicit last probability
            last_prob = 1.0 - sum(joint_probs)
            if last_prob < -1e-10:
                raise ValueError(
                    f"Joint probabilities sum to more than 1 (sum={sum(joint_probs)})"
                )
            all_probs = joint_probs + [max(0.0, last_prob)]
            for i, prob in enumerate(all_probs):
                assignment = [(i >> (num_variables - j - 1)) & 1 for j in range(num_variables)]
                self.joint_probabilities[tuple(assignment)] = prob
        else:
            # Multi-valued (or explicit full binary) path: expect full joint list Π card_i
            total_states = 1
            for c in self.cardinalities:
                total_states *= c
            if len(joint_probs) != total_states:
                raise ValueError(
                    f"Expected full joint list of length {total_states}, got {len(joint_probs)}"
                )
            index = 0
            for assignment in _cartesian_product([range(c) for c in self.cardinalities]):
                self.joint_probabilities[tuple(assignment)] = joint_probs[index]
                index += 1
            total = sum(self.joint_probabilities.values())
            if total <= 0:
                raise ValueError("Total probability non-positive in joint initialization")
            if abs(total - 1.0) > 1e-8:
                # Normalize for robustness
                for k in list(self.joint_probabilities.keys()):
                    self.joint_probabilities[k] /= total

    @classmethod
    def from_file(
        cls, file_path: str, variable_names: Optional[List[str]] = None
    ) -> "ProbabilitySystem":
        """Create a ProbabilitySystem by loading a joint or network file.

        For legacy binary network/.inp files the old semantics are preserved.
        Multi-valued network parsing will be introduced in the updated .net parser
        which will itself call the constructor with variable_states.
        """
        from .io import load_joint_prob_file, load_network_file

        if file_path.endswith('.net'):
            result = load_network_file(file_path, variable_names)
            # Multi-valued path returns 4-tuple
            if len(result) == 4:
                num_variables, joint_probs, names_to_use, variable_states = result
                return cls(num_variables, joint_probs, names_to_use, variable_states=variable_states)
            else:
                num_variables, joint_probs, names_to_use = result
                return cls(num_variables, joint_probs, names_to_use)
        else:
            num_variables, joint_probs, names_to_use = load_joint_prob_file(
                file_path, variable_names
            )
            return cls(num_variables, joint_probs, names_to_use)

    @classmethod
    def from_states_and_joint(
        cls,
        variable_names: List[str],
        variable_states: List[List[str]],
        joint_probabilities: Dict[Tuple[int, ...], float],
    ) -> "ProbabilitySystem":
        """Construct from an explicit full joint probability dictionary.

        Missing assignments are treated as probability 0.
        """
        num_variables = len(variable_names)
        if len(variable_states) != num_variables:
            raise ValueError("variable_states length mismatch variable_names length")
        # Build ordered list of probs
        cards = [len(vs) for vs in variable_states]
        all_assignments = list(_cartesian_product([range(c) for c in cards]))
        ordered = [joint_probabilities.get(tuple(a), 0.0) for a in all_assignments]
        return cls(num_variables, ordered, variable_names, variable_states=variable_states)

    # --- Arithmetic & query evaluation
    def evaluate_arithmetic_expression(self, expr: str) -> float:
        """Evaluate an arithmetic expression that may contain `P(...)` probability calls.

        This uses a safe AST evaluator that only permits numeric literals, binary
        operations (+, -, *, /), and unary +/- to avoid arbitrary code execution.
        """
        import ast

        def prob_replacer(match):
            prob_query = match.group(0)
            value = self.evaluate_query(prob_query)
            return str(value)

        prob_pattern = r"P\((?:[^()]+|\([^()]*\))*\)"
        expr_with_values = re.sub(prob_pattern, prob_replacer, expr)

        # Parse expression into AST and validate allowed nodes
        try:
            node = ast.parse(expr_with_values, mode="eval")
        except Exception as e:
            raise ValueError(f"Error parsing expression: {e}")

        # Disallow power and other operators by whitelisting only a subset below
        allowed_binops = (ast.Add, ast.Sub, ast.Mult, ast.Div)
        allowed_unary = (ast.UAdd, ast.USub)

        def _validate(n):
            if isinstance(n, ast.Expression):
                _validate(n.body)
            elif isinstance(n, ast.BinOp):
                if not isinstance(n.op, allowed_binops):
                    raise ValueError(f"Operator {type(n.op).__name__} is not allowed")
                _validate(n.left)
                _validate(n.right)
            elif isinstance(n, ast.UnaryOp):
                if not isinstance(n.op, allowed_unary):
                    raise ValueError(f"Unary operator {type(n.op).__name__} is not allowed")
                _validate(n.operand)
            elif isinstance(n, ast.Constant):
                if not isinstance(n.value, (int, float)):
                    raise ValueError("Only numeric constants are allowed")
                return
            else:
                raise ValueError(f"Expression contains disallowed node type: {type(n).__name__}")

        _validate(node)

        # Safe evaluation by compiling AST and evaluating with empty globals/locals
        try:
            compiled = compile(node, filename="<ast>", mode="eval")
            result = eval(compiled, {"__builtins__": None}, {})
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

        return float(result)

    def get_joint_probability(self, variable_values: Tuple[int, ...]) -> float:
        """Return the joint probability for a full assignment (state indices)."""
        return self.joint_probabilities.get(variable_values, 0.0)

    # Convenience name/state based wrapper APIs (used by new tests)
    def _resolve_name_state_mapping(self, assignment: dict) -> Tuple[List[int], List[int]]:
        vars_idx: List[int] = []
        vals: List[int] = []
        for name, state in assignment.items():
            vidx = self._name_to_index(name)
            if isinstance(state, str):
                # state name
                if state not in self.state_name_to_index[vidx]:
                    raise ValueError(f"Unknown state '{state}' for variable '{name}'")
                vals.append(self.state_name_to_index[vidx][state])
            else:
                # assume integer index or binary 0/1 literal
                sval = int(state)
                if not (0 <= sval < self.cardinalities[vidx]):
                    raise ValueError(f"State index {sval} out of range for variable '{name}'")
                vals.append(sval)
            vars_idx.append(vidx)
        return vars_idx, vals

    def probability_of(self, assignment: dict) -> float:
        """Return marginal probability for a (possibly partial) assignment given as {VarName: StateNameOrIndex}."""
        vars_idx, vals = self._resolve_name_state_mapping(assignment)
        return self.get_marginal_probability(vars_idx, vals)

    def conditional_probability_of(self, target: dict, given: dict) -> float:
        """Return conditional probability P(target | given) for name/state dictionaries."""
        t_vars, t_vals = self._resolve_name_state_mapping(target)
        g_vars, g_vals = self._resolve_name_state_mapping(given)
        return self.get_conditional_probability(g_vars, g_vals, t_vars, t_vals)

    def joint_probability_of(self, assignment: dict) -> float:
        """Return joint probability for a full assignment dictionary. (All variables not required; missing ones marginalized.)"""
        # If not all variables provided just treat as marginal
        if len(assignment) != self.num_variables:
            return self.probability_of(assignment)
        vars_idx, vals = self._resolve_name_state_mapping(assignment)
        # reorder into full tuple order
        full_states = [0]*self.num_variables
        for vidx, vval in zip(vars_idx, vals):
            full_states[vidx] = vval
        return self.get_joint_probability(tuple(full_states))

    def get_marginal_probability(self, variables: List[int], values: List[int]) -> float:
        """Compute P(variables=values) by summing over remaining variables.

        Values are integer state indices. Legacy binary queries still work (0/1 states)."""
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
        """Return conditional probability P(target_vars=target_values | condition_vars=condition_values).

        If the condition has zero probability, returns 0.
        """
        joint_vars = target_vars + condition_vars
        joint_values = target_values + condition_values
        joint_prob = self.get_marginal_probability(joint_vars, joint_values)

        condition_prob = self.get_marginal_probability(condition_vars, condition_values)

        if condition_prob == 0:
            return 0

        return joint_prob / condition_prob

    def is_independent(self, var1: int, var2: int) -> bool:
        """Return True if P(X=i,Y=j)=P(X=i)P(Y=j) for all states i,j."""
        for i in range(self.cardinalities[var1]):
            for j in range(self.cardinalities[var2]):
                joint_prob = self.get_marginal_probability([var1, var2], [i, j])
                if joint_prob == 0.0:
                    # still need to ensure product zero
                    marg_i = self.get_marginal_probability([var1], [i])
                    marg_j = self.get_marginal_probability([var2], [j])
                    if abs(marg_i * marg_j) > 1e-10:
                        return False
                else:
                    marg_i = self.get_marginal_probability([var1], [i])
                    marg_j = self.get_marginal_probability([var2], [j])
                    if abs(joint_prob - marg_i * marg_j) > 1e-10:
                        return False
        return True

    def is_conditionally_independent(self, var1: int, var2: int, given_var: int) -> bool:
        """Return True if P(X=i,Y=j|Z=k)=P(X=i|Z=k)P(Y=j|Z=k) for all states."""
        for i in range(self.cardinalities[var1]):
            for j in range(self.cardinalities[var2]):
                for k in range(self.cardinalities[given_var]):
                    joint_cond = self.get_conditional_probability([given_var], [k], [var1, var2], [i, j])
                    p_x_given = self.get_conditional_probability([given_var], [k], [var1], [i])
                    p_y_given = self.get_conditional_probability([given_var], [k], [var2], [j])
                    if abs(joint_cond - p_x_given * p_y_given) > 1e-10:
                        return False
        return True

    # --- Parsing related methods (use parsing helpers)
    def parse_variable_expression(self, expr: str) -> Tuple[List[int], List[int]]:
        """Parse variable/state expression.

        Legacy binary forms:
            A, ~B, Not(C), B=1, C=0
        Multi-valued form requires explicit states:
            Weather=Rainy, Traffic=Heavy
        Binary variables also accept explicit assignment A=0/1.
        Returns (variables, state_indices).
        """
        variables: List[int] = []
        values: List[int] = []
        parts = [p.strip() for p in expr.split(",")]
        for part in parts:
            if not part:
                continue
            original = part
            negated = False
            explicit_value: Optional[int] = None

            if "=" in part:
                left, right = part.split("=", 1)
                var_name = left.strip()
                right = right.strip()
                var_idx_tmp = self._name_to_index(var_name)
                # If binary and right is 0/1 -> direct
                if self.cardinalities[var_idx_tmp] == 2 and right in {"0", "1"}:
                    explicit_value = int(right)
                    part = var_name
                else:
                    # interpret as named state
                    state_map = self.state_name_to_index[var_idx_tmp]
                    if right not in state_map:
                        raise ValueError(f"Unknown state '{right}' for variable '{var_name}' in token '{original}'")
                    explicit_value = state_map[right]
                    part = var_name

            if part.startswith("Not(") and part.endswith(")"):
                negated = True
                part = part[4:-1].strip()
            elif part.startswith("~"):
                negated = True
                part = part[1:].strip()
                if part.startswith("(") and part.endswith(")"):
                    part = part[1:-1].strip()

            var_idx = self._name_to_index(part)

            if explicit_value is not None:
                if negated:
                    if self.cardinalities[var_idx] != 2:
                        raise ValueError("Negation only allowed for binary variables")
                    if explicit_value != 0:
                        raise ValueError(f"Conflicting negation and assignment in token '{original}'")
                    final_value = 0
                else:
                    final_value = explicit_value
            else:
                # No explicit state specified
                if negated:
                    if self.cardinalities[var_idx] != 2:
                        raise ValueError("Negation only allowed for binary variables")
                    final_value = 0
                else:
                    if self.cardinalities[var_idx] != 2:
                        raise ValueError(
                            f"Variable '{self.variable_names[var_idx]}' is multi-valued; explicit state assignment required (e.g. Var=State)."
                        )
                    final_value = 1  # default positive state for binary

            variables.append(var_idx)
            values.append(final_value)

        return variables, values

    def parse_probability_query(self, query: str) -> Dict:
        """Parse a textual probability query like 'P(A,B|C)' into structured parts.

        Returns a dict describing the parsed query.
        """
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
        """Parse independence queries like 'IsIndep(A,B)' or 'IsCondIndep(A,B|C)'.

        Returns a dict describing the parsed query.
        """
        m = match_independence_conditional(query)
        if m:
            var1_name, var2_name, given_var_name = [strip_negation(g) for g in m.groups()]

            var1_idx = self._name_to_index(var1_name)
            var2_idx = self._name_to_index(var2_name)
            given_var_idx = self._name_to_index(given_var_name)

            return {
                "type": "conditional_independence",
                "var1": var1_idx,
                "var2": var2_idx,
                "given_var": given_var_idx,
            }

        m2 = match_independence(query)
        if m2:
            var1_name, var2_name = [strip_negation(g) for g in m2.groups()]

            var1_idx = self._name_to_index(var1_name)
            var2_idx = self._name_to_index(var2_name)

            return {"type": "independence", "var1": var1_idx, "var2": var2_idx}

        raise ValueError(f"Invalid independence query format: {query}")

    def evaluate_query(self, query: str) -> Union[float, bool]:
        """Evaluate a query string and return either a numeric probability or a boolean.

        Supported query forms: P(...), IsIndep(...), IsCondIndep(...)
        """
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

    def _name_to_index(self, name: str) -> int:
        """Resolve a variable name to its index, accepting single-letter A..Z or explicit names."""
        name = name.strip()
        try:
            return self.variable_names.index(name)
        except ValueError:
            if len(name) == 1 and "A" <= name <= "Z":
                idx = ord(name) - ord("A")
                if idx >= self.num_variables:
                    raise ValueError(f"Variable {name} is out of range")
                return idx
            raise ValueError(f"Unknown variable name: {name}")

    # --- Pretty print helpers (moved to ui.py in the future)
    # The actual printing functions are implemented in ui.py and imported below.

    def marginal_distribution(self, variables: List[int]) -> Dict[Tuple[int, ...], float]:
        """Return the marginal distribution over a subset of variables.

        Args:
            variables: list of variable indices
        """
        return stats.marginal_distribution(self.joint_probabilities, variables)

    def entropy(self, variables: Optional[List[int]] = None, base: float = 2.0) -> float:
        """Compute Shannon entropy (in given base) for the joint or marginal distribution.

        Args:
            variables: optional subset for which to compute entropy; if None use full joint.
            base: logarithm base for entropy.
        """
        return stats.entropy(self.joint_probabilities, variables, base=base)

    def conditional_entropy(self, target_vars: List[int], given_vars: List[int], base: float = 2.0) -> float:
        """Return H(target_vars | given_vars) in the specified base."""
        return stats.conditional_entropy(self.joint_probabilities, target_vars, given_vars, base=base)

    def mutual_information(self, var1: int, var2: int, base: float = 2.0) -> float:
        """Return mutual information I(var1; var2) using the provided base."""
        return stats.mutual_information(self.joint_probabilities, var1, var2, base=base)

    def odds_ratio(self, exposure: int, outcome: int) -> Optional[float]:
        """Compute the odds ratio for binary `exposure` and `outcome` variables.

        Returns None if odds ratio is undefined due to division by zero.
        """
        return stats.odds_ratio(self.get_marginal_probability, exposure, outcome)

    def relative_risk(self, exposure: int, outcome: int) -> Optional[float]:
        """Compute relative risk (risk ratio) for an exposure and outcome.

        Returns None if the baseline risk is zero.
        """
        return stats.relative_risk(self.get_conditional_probability, exposure, outcome)

    def sample(self, n: int = 1) -> List[Tuple[int, ...]]:
        """Draw `n` iid samples from the joint distribution.

        Returns a list of state tuples.
        """
        return stats.sample(self.joint_probabilities, n=n)

    def save_to_file(self, file_path: str) -> None:
        """Save the joint probabilities and variable names to a file.

        This delegates to `probs_core.io.write_joint_prob_file`.
        """
        from .io import write_joint_prob_file

        write_joint_prob_file(file_path, self.variable_names, self.joint_probabilities)
