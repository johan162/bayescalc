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


class ProbabilitySystem:
    """High-level probability API: creation, probability computation, and query evaluation."""

    def __init__(
        self,
        num_variables: int,
        joint_probs: List[float],
        variable_names: Optional[List[str]] = None,
    ) -> None:
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

        self.joint_probabilities: Dict[Tuple[int, ...], float] = {}
        for i, prob in enumerate(all_probs):
            binary = [(i >> (num_variables - j - 1)) & 1 for j in range(num_variables)]
            self.joint_probabilities[tuple(binary)] = prob

    @classmethod
    def from_file(
        cls, file_path: str, variable_names: Optional[List[str]] = None
    ) -> "ProbabilitySystem":
        """Create a ProbabilitySystem by loading a joint-probability file.

        Args:
            file_path: path to the input file
            variable_names: optional list of variable names to override file values

        Returns:
            A configured `ProbabilitySystem` instance.
        """
        # delegate to io.load_joint_prob_file to parse the file
        from .io import load_joint_prob_file, load_network_file

        if file_path.endswith('.net'):
            num_variables, joint_probs, names_to_use = load_network_file(file_path, variable_names)
        else:
            num_variables, joint_probs, names_to_use = load_joint_prob_file(
                file_path, variable_names
            )
        return cls(num_variables, joint_probs, names_to_use)

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
        """Return the joint probability for a full assignment represented by a tuple of 0/1 values.

        Args:
            variable_values: tuple of 0/1 values with length == num_variables
        """
        return self.joint_probabilities.get(variable_values, 0.0)

    def get_marginal_probability(self, variables: List[int], values: List[int]) -> float:
        """Compute marginal probability P(vars=values) by summing the joint distribution.

        Args:
            variables: list of variable indices
            values: list of 0/1 values matching `variables`
        """
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
        """Test whether two variables are (pairwise) independent.

        Returns True if P(X,Y)=P(X)P(Y) for all binary assignments.
        """
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
        """Test whether var1 and var2 are conditionally independent given `given_var`.

        Returns True if P(X,Y|Z)=P(X|Z)P(Y|Z) for all binary assignments.
        """
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
        """Parse a variable expression like 'A, ~B, C' into indices and binary values.

        Returns (variables, values) where values are 1 for presence and 0 for negation.
        """
        variables = []
        values = []

        parts = [p.strip() for p in expr.split(",")]

        for part in parts:
            if not part:
                continue

            original = part
            negated = False
            explicit_value = None

            # Support explicit assignments like A=1, B=0 (possibly with spaces)
            if "=" in part:
                left, right = part.split("=", 1)
                part = left.strip()
                right = right.strip()
                if right not in {"0", "1"}:
                    raise ValueError(f"Invalid assignment value in token '{original}'")
                explicit_value = int(right)

            # Detect negation forms (~A, ~(A), Not(A))
            if part.startswith("Not(") and part.endswith(")"):
                negated = True
                part = part[4:-1].strip()
            else:
                if part.startswith("~"):
                    negated = True
                    part = part[1:].strip()
                    if part.startswith("(") and part.endswith(")"):
                        part = part[1:-1].strip()

            var_idx = self._name_to_index(part)

            # Resolve final value precedence and conflict detection
            if explicit_value is not None:
                if negated:
                    # ~A implies value 0; Not(A) likewise. Disallow contradiction like ~A=1
                    implied = 0
                    if explicit_value != implied:
                        raise ValueError(
                            f"Conflicting negation and assignment in token '{original}'"
                        )
                    final_value = explicit_value
                else:
                    final_value = explicit_value
            else:
                final_value = 0 if negated else 1

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
