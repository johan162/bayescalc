# Probability System Documentation

## 1. Overview

### Function and Usage

The `probs.py` script is a comprehensive probabilistic statistics calculator designed for working with boolean random variables and their joint probability distributions. It implements a Bayesian contingency table system that enables users to compute various types of probabilities and perform statistical independence tests.

The input data can either be specified interactively (which is tedious) or read from a file that can either have the format of a joint probability table (possible sparse) or as a number of conditional probability tables which specifies a Bayesian network. The Bayesian network format is often the simplest way to specify larger networks
as it allows the sanme data to be specified in a more conscise format. The precise format is described in later sections in this document. Internally both input methods will establish a complete joint distribution table of size 2^N where N is the number of variables.

The scipt provides both public APIs as well as a CLI interface for interactive experiments.

Some quick examples to give a sense of what can be calculated (this is not an exhaustive list)

1. `P(A)` — Marginal probability that variable `A` equals 1.
2. `P(~A)` or `P(Not(A))` — Marginal probability that `A` equals 0 (negation supported with `~`).
3. `P(A,B)` — Joint probability that `A=1` and `B=1`.
4. `P(A=0,B=1)` — Joint probability using explicit value notation.
5. `P(A|B)` — Conditional probability P(A=1 | B=1).
6. `P(A,B|C)` — Joint probability of `A` and `B` given `C` (conditional joint).
7. `IsIndep(A,B)` — Test whether `A` and `B` are independent.
8. `IsCondIndep(A,B|C)` — Test conditional independence given `C`.
9. `P(A)+P(B)` — Arithmetic on probability values (addition supported).
10. `P(A)*P(B|C)/P(D)` — Mixed arithmetic with conditional and marginal probabilities.
11. `P(~A) + P(B|~C)` — Combine negation and conditional queries in arithmetic expressions.
12. `cond_probs(1,2)` - Print a table of all possible combinations of `P(X1=x1|X2=x2,X3=x3)`
13. `marginals` - Print a table of all marginal probabilitites

Notes:
- Variable names may be single letters (`A`,`B`,...) or custom names specified in input files (`Rain`, `Sickness`, ...).
- Whitespace and simple parentheses are supported inside `P(...)` queries. Use `~` as a concise negation operator or `Not(...)` for clarity.

### Background: Bayesian Contingency Tables with Joint Probabilities

A contingency table (also known as a cross-tabulation) is a matrix that displays the frequency distribution of variables. In the context of Bayesian probability, this system works with:

- **Boolean random variables**: Each variable can take only two values (0 or 1, typically representing false/true or absence/presence)
- **Joint probability distributions**: The complete probability distribution over all possible combinations of variable values
- **Bayesian inference**: The ability to compute conditional probabilities and test statistical relationships

The system is particularly useful for:
- Analyzing relationships between binary events
- Computing conditional probabilities in Bayesian networks
- Testing for statistical independence between variables
- Educational purposes in probability theory and statistics

### Command Line Arguments

The script supports the following command line arguments:

- `file` (optional): Path to a file containing joint probabilities. If not provided, the system runs in interactive mode for manual input
- `--names`, `-n` (optional): Custom variable names to use with the input file, specified as space-separated values

**Usage Examples:**
```bash
# Interactive mode (manual input)
python probs.py

# Load from file with default variable names
python probs.py input.txt

# Load from file with custom variable names
python probs.py input.txt --names Rain Sprinkler WetGrass
```

## 2. Input File Format

### File Structure

The input file contains joint probability data in a simple text format with the following structure:

1. **Optional header line** for custom variable names
2. **Probability entries** - one per line
3. **Comments** and empty lines are ignored

### Format Specification

#### Variable Names Header (Optional)
```
variables: Name1,Name2,Name3,...
```

- Must start with "variables:" (case-insensitive)
- Variable names separated by commas
- Names can contain spaces (will be trimmed)
- If omitted, defaults to A, B, C, ...

#### Probability Entries
```
binary_pattern: probability_value
```

- `binary_pattern`: String of 0s and 1s representing variable values
- `probability_value`: Floating-point number between 0 and 1
- Leftmost bit corresponds to the first variable
- Must provide either 2^n-1 or 2^n entries (last probability auto-calculated if missing)

### Example File (2 variables)

```
variables: Rain, Sprinkler
# Joint probabilities for weather example
00: 0.25
01: 0.25
10: 0.25
11: 0.25
```

### Example File (3 variables)

```
variables: Fever, Cough, COVID
000: 0.6
001: 0.1
010: 0.1
011: 0.05
100: 0.05
101: 0.03
110: 0.03
# Last probability (111) will be auto-calculated as 0.04
```

### Validation Rules

1. **Binary patterns**: Must contain only 0s and 1s
2. **Probability values**: Must be between 0 and 1
3. **Completeness / Missing Entries Policy**:
  - If you provide all 2^n combinations, they are used directly (with optional auto-normalization if the sum is close to 1.0).
  - If exactly 2^n - 1 combinations are provided, the single missing combination's probability is inferred as (1 - sum(provided)). If the provided sum exceeds 1, it's an error.
  - If more than one combination is missing, all missing combinations are assigned probability 0.0 (sparse specification). Optionally, a near-1.0 total will be auto-normalized.
4. **Sum constraint**: After applying the above rules, if the full table sum deviates modestly (≤5% relative) from 1.0 it is auto-normalized; otherwise sums >1 trigger an error.
5. **Consistency**: All binary patterns must have the same length

### Comments and Formatting

- Lines starting with `#` are treated as comments.
- Empty lines are ignored.
- Extra whitespace around colons and commas is automatically trimmed.
- Trailing inline comments are supported after probability entries and the variable header. Anything after a `#` on a data line is ignored.

Example with inline comments and single omitted last line (auto-inferred):
```
variables: Rain,Sprinkler  # two variables
00: 0.25  # neither
01: 0.25  # Sprinkler only
10: 0.25  # Rain only
# Last one omitted; 11 auto-computed as 0.25
```
- File can have any number of comment lines interspersed with data.

### Alternative Format: Bayesian Network Files (`*.net`)

In addition to raw joint tables (`*.inp`), you can specify a Bayesian network structure and its conditional probability tables using a `.net` file. The system will expand it into the full joint distribution internally.

#### Structure
```
variables: Var1, Var2, Var3, ...
Child: Parent1, Parent2, ...   # or 'Child: None' if no parents
<CPT lines>
```

Rules:
- Exactly one block per variable, order of blocks can be arbitrary but all declared variables must appear.
- Parentless variable block uses one line either `1: p` (interpreted as P(X=1)=p) or `0: q` (interpreted as P(X=0)=q, so P(X=1)=1-q).
- For a variable with k parents, provide 2^k lines, one per parent bit pattern (in the order parents are listed) giving `pattern: p` meaning P(child=1 | parents=pattern).
- Patterns are strings of 0/1 characters whose length equals number of listed parents.
- Missing or duplicate CPT patterns trigger an error.
- Comments (starting `#`) allowed full-line or trailing; inline comments after probabilities are ignored.
- After reading all CPTs, the joint is computed as the product:  Π_i P(X_i | Parents(X_i)). A final normalization is applied if the product joint sums to ~1 (floating tolerance).

#### Example (`explaining_away_alarm.net`):
```
variables: B,E,A,J,M
B: None
1: 0.01

E: None
1: 0.002

A: B,E
11: 0.99
10: 0.99
01: 0.99
00: 0.0005

J: A
1: 0.90
0: 0.05

M: A
1: 0.70
0: 0.01
```

You can load this with:
```bash
python probs.py examples/explaining_away_alarm.net
```

From Python:
```python
ps = ProbabilitySystem.from_file('examples/explaining_away_alarm.net')
print(ps.get_marginal_probability([0],[1]))  # P(B=1)
```

This produces a joint distribution consistent with the supplied CPTs and enables all standard queries and derived statistics.

### Error Handling

The system provides detailed error messages for:
- Invalid file paths
- Malformed binary patterns
- Invalid probability values
- Inconsistent pattern lengths
- Sum exceeding 1.0
- Missing or extra probability entries (handled by the missing entries policy: single missing inferred; multiple missing -> zeros)

## 3. Statistical Utilities

The `ProbabilitySystem` also includes several information-theoretic and epidemiological utilities:

- `entropy(variables=None, base=2)` — Shannon entropy for specified variables. If `variables` is `None`, entropy over the full joint distribution is returned. Units are in `base` (bits when base=2).
- `conditional_entropy(target_vars, given_vars, base=2)` — conditional entropy H(target|given).
- `mutual_information(var1, var2, base=2)` — mutual information I(var1;var2).
- `odds_ratio(exposure, outcome)` — compute odds ratio for two binary variables (returns `None` if computation not possible due to zero cells).
- `relative_risk(exposure, outcome)` — compute relative risk (returns `None` if denominator is zero).
- `sample(n=1)` — draw samples (tuples of 0/1 values) from the joint distribution.

### Usage examples (Python):

```python
# Recommended: import the core API directly from the probs_core package
from probs_core import ProbabilitySystem

# Load example
ps = ProbabilitySystem.from_file('inputs/medical_test.inp')

# Entropy of Sickness variable (bits)
H_s = ps.entropy([0])

# Mutual information between Sickness and Test
I = ps.mutual_information(0, 1)

# Odds ratio between Sickness (exposure) and Test (outcome)
or_val = ps.odds_ratio(0, 1)

# Relative risk
rr = ps.relative_risk(0, 1)

# Draw 10 samples
samples = ps.sample(10)
```

More epidemiology examples (Python):

```python
# Odds ratio and relative risk examples
or_val = ps.odds_ratio(0, 1)
if or_val is None:
  print("Odds ratio undefined (division by zero)")
else:
  print(f"Odds ratio: {or_val:.3f}")

rr = ps.relative_risk(0, 1)
if rr is None:
  print("Relative risk undefined (zero baseline risk)")
else:
  print(f"Relative risk: {rr:.3f}")

# Sampling example
print(ps.sample(5))  # -> [(0,0), (1,0), ...]
```

### Interpreting Odds Ratio (OR) and Relative Risk (RR) in Medical Context

When evaluating associations between an exposure (e.g. a risk factor or diagnostic test result) and an outcome (e.g. disease), OR and RR quantify different—but related—concepts. The system returns `None` when a quantity is undefined due to structural zeros (e.g. division by zero cells).

#### Definitions (2x2 table)
Let exposure variable `E` (0/1) and outcome variable `D` (0/1). Using cell probabilities (or counts normalized):

|        | D=1           | D=0           |
|--------|---------------|---------------|
| E=1    | a             | b             |
| E=0    | c             | d             |

Constraint: a + b + c + d = 1 (if probabilities) or total N (if raw counts).

- Risk among exposed: `Risk_exposed = a / (a + b)` = P(D=1 | E=1)
- Risk among unexposed: `Risk_unexposed = c / (c + d)` = P(D=1 | E=0)
- Relative Risk: `RR = Risk_exposed / Risk_unexposed`
- Odds among exposed: `Odds_exposed = a / b`
- Odds among unexposed: `Odds_unexposed = c / d`
- Odds Ratio: `OR = (a/b) / (c/d) = ad / bc`

#### Practical Interpretation
| Value | Relative Risk Meaning | Odds Ratio Meaning |
|-------|-----------------------|--------------------|
| 1.0   | No risk difference    | No difference in odds |
| 2.0   | Risk doubles          | Odds double (approx risk doubling only if outcome is rare) |
| 0.5   | Risk halves           | Odds halve |
| >>1   | Strong positive association | Strong positive association |
| <<1   | Protective factor     | Protective (reduced odds) |

#### Rare Outcome Approximation
For uncommon outcomes (say P(D=1) < 10%), `OR ≈ RR` because odds `p/(1-p)` ≈ `p` when `p` is small. For common outcomes they diverge; OR will overstate effect size relative to RR (e.g. RR=2 may correspond to OR>2 for moderate/high baseline risk).

#### Worked Example (Medical Test as Exposure)
Using the medical test joint distribution (`Sickness`=D, `Test`=E):

From the table:
- a = P(Test=1, Sickness=1) = 0.0095
- b = P(Test=1, Sickness=0) = 0.0594
- c = P(Test=0, Sickness=1) = 0.0005
- d = P(Test=0, Sickness=0) = 0.9306

Compute:
```
Risk_exposed   = a / (a + b) = 0.0095 / 0.0689  = 0.1379   (P(Sickness=1 | Test=1))
Risk_unexposed = c / (c + d) = 0.0005 / 0.9311  = 0.000537 (P(Sickness=1 | Test=0))
RR = 0.1379 / 0.000537 ≈ 256.8

Odds_exposed   = a / b = 0.0095 / 0.0594 ≈ 0.1599
Odds_unexposed = c / d = 0.0005 / 0.9306 ≈ 0.000537
OR = 0.1599 / 0.000537 ≈ 297.8  (also ad/bc = (0.0095*0.9306)/(0.0594*0.0005))
```

Interpretation:
- A positive test increases risk from ~0.05% to ~13.8% (huge absolute and relative increase).
- RR ≈ 257 means the probability of disease is about 257 times higher after a positive test compared to a negative test.
- OR ≈ 298 is larger than RR because the post-test probability (13.8%) is no longer extremely rare; the odds inflate relative risk magnitude.

#### Choosing RR vs OR
- Use RR when cohort/incidence interpretation exists (prospective studies, risk communication to clinicians/patients).
- Use OR in case-control designs where true risks not directly estimable or in logistic regression outputs.
- For patient-facing communication prefer absolute risks (e.g. "from 0.05% to 13.8%") alongside RR; avoid presenting OR alone when effect is large to prevent misinterpretation.

#### When Values Are Undefined
- If any denominator term is zero (e.g. no unexposed without outcome) the corresponding odds or risk measure can be undefined; the system returns `None` for OR/RR in those edge cases. Consider adding a small continuity correction (e.g., +0.5 to each cell count) only if statistically justified and documented.

#### Sanity Checks
- Verify `P(D=1) = a + c` and `P(E=1) = a + b`.
- Confirm `OR = RR` closely only when both `Risk_exposed` and `Risk_unexposed` are small.

These interpretations help translate numeric outputs into actionable medical reasoning.


## 4. CLI: Entropy and information-theoretic commands

The interactive CLI also exposes information-theoretic commands directly. These commands can be used from the REPL after loading a joint-probability file:

Examples (entered at the `Query:` prompt):

- `entropy` — Entropy of the full joint distribution (base 2 by default).
- `entropy(A)` — Entropy of a single variable named `A`.
- `entropy(A,B)` — Joint entropy of variables `A` and `B`.
- `entropy(A,B base=10)` — Use a different logarithm base (here base 10).
- `cond_entropy(A|B)` or `conditional_entropy(A|B)` — Compute H(A|B).
- `mutual_info(A,B)` or `mutual_information(A,B)` — Compute I(A;B).

- `odds_ratio(A,B)` — Compute the odds ratio for exposure/outcome variables A and B.
- `relative_risk(A,B)` — Compute the relative risk (risk ratio).
- `sample(n=1)` — Draw n samples (tuples) from the joint distribution.

Example session:

```
$ python probs.py inputs/medical_test.inp
Successfully loaded probability system from file: inputs/medical_test.inp
Using variable names: Sickness, Test
Joint Probability Table:
 ...
Query: entropy(Sickness)
--> 0.0808
Query: mutual_info(Sickness,Test)
--> 0.0103
Query: cond_entropy(Sickness|Test)
--> 0.0705
```

These commands are useful for quick exploratory analysis from the CLI without dropping into a Python interpreter.


Project layout and recommended imports

The codebase is now organized so the computational core is provided by the `probs_core` package. Key modules:

- `probs_core/probability.py` — `ProbabilitySystem` (high-level API and query evaluation)
- `probs_core/io.py` — File parsing and writing helpers for joint probability files
- `probs_core/ui.py` — Pretty-print/display helpers used by the CLI
- `probs_core/parsing.py` — Parser utilities and regex helpers for `P(...)`, `IsIndep(...)`, and negation forms
- `probs_core/stats.py` — Pure statistical routines (entropy, mutual information, sampling, odds/rr)

Recommended usage pattern for programmatic access:

```python
from probs_core import ProbabilitySystem

ps = ProbabilitySystem.from_file('inputs/medical_test.inp')
```

The top-level `probs.py` script remains a thin compatibility wrapper so `python probs.py` still works for interactive use.

These utilities are implemented directly from the joint probability table and work with custom variable names (use index 0..n-1 in the API calls above).

Compatibility / Migration note
-----------------------------

Historically there was a monolithic `probs_core.py` file in the project. The codebase has been refactored into a small package `probs_core/` containing `probability.py`, `io.py`, `ui.py`, `parsing.py`, and `stats.py`.

To preserve older workflows, a legacy copy of the original monolithic implementation is available in `probs_core_legacy.py`. New code, tests, and examples should import the modular package API:

```python
from probs_core import ProbabilitySystem

ps = ProbabilitySystem.from_file('inputs/medical_test.inp')
```

If you have scripts that import `probs_core` directly, update them to import from the package (above) so they use the canonical, modular implementation.



## Appendix A: Classical Medical Test Example

### Scenario Description

This appendix demonstrates the probability system using a classical medical testing scenario that illustrates the importance of conditional probability and base rates in decision-making.

**Problem Setup:**
- **Variables**: Sickness (0=healthy, 1=sick), Test (0=negative, 1=positive)
- **Base Rate**: Sickness occurs in 1% of the population
- **Test Sensitivity**: Correctly identifies sick person with 95% probability
- **Test Specificity**: Wrongly identifies healthy person as sick in 6% of cases

### Contingency Table Construction

Using the given probabilities, we can construct the joint probability distribution:

| Sickness | Test | Probability | Calculation |
|----------|------|-------------|-------------|
| 0 (Healthy) | 0 (Negative) | 0.9306 | 0.99 × (1-0.06) = 0.99 × 0.94 |
| 0 (Healthy) | 1 (Positive) | 0.0594 | 0.99 × 0.06 |
| 1 (Sick) | 0 (Negative) | 0.0005 | 0.01 × (1-0.95) = 0.01 × 0.05 |
| 1 (Sick) | 1 (Positive) | 0.0095 | 0.01 × 0.95 |

**Input File (`medical_test.inp`):**
```
variables: Sickness, Test
00: 0.9306
01: 0.0594
10: 0.0005
11: 0.0095
```

### Running the Analysis

Execute the system with the medical test data:

```bash
# The top-level wrapper is still available for compatibility:
python probs.py medical_test.inp
```

### Key Probability Calculations

**Joint Probability Table Output:**
```
Joint Probability Table:
========================

Sickness | Test | Probability
-----------------------------
0 | 0 | 0.930600
0 | 1 | 0.059400
1 | 0 | 0.000500
1 | 1 | 0.009500
```

**Query Results:**
- `P(Sickness=1|Test=1)` = **0.1379** (13.8%)
- `P(Test=1)` = 0.0689
- `P(Sickness=1)` = 0.0100 (1%)
- `P(Test=1|Sickness=1)` = 0.9500 (95%)
- Independence test: **False** (variables are dependent)

### Determining P(Sickness|Test)

The conditional probability P(Sickness|Test) represents the probability that a person is actually sick given that they tested positive. This is calculated using Bayes' theorem:

**P(Sickness=1|Test=1) = P(Test=1|Sickness=1) × P(Sickness=1) / P(Test=1)**

**Manual Calculation:**
- P(Test=1|Sickness=1) = 0.95 (test sensitivity)
- P(Sickness=1) = 0.01 (base rate)
- P(Test=1) = 0.0689 (total positive test rate)
- Result: (0.95 × 0.01) / 0.0689 = 0.0095 / 0.0689 = **0.1379**

### System Query Examples

```bash
# Direct conditional probability query
P(Sickness|Test)

# Component probabilities
P(Sickness)
P(Test)
P(Test|Sickness)

# Joint probability
P(Sickness,Test)

# Independence test
IsIndep(Sickness,Test)
```

Note: The parser accepts two forms of negation. You can write explicit negation using `Not(...)`,
for example `P(Not(Sickness))`, or use the inline tilde `~` as a shorthand (common in mathematical
notation), for example `P(~Sickness)` or `IsIndep(~Sickness,Test)`. Tab-completion also works when
you type a leading `~` (e.g., type `~S` and press Tab to complete `~Sickness`).

### Interpretation and Insights

**Counterintuitive Result:** Despite the test being 95% accurate, a positive test result only indicates a 13.8% probability of actually being sick. This demonstrates:

1. **Base Rate Neglect**: The low prevalence of the disease (1%) heavily influences the result
2. **Bayesian Reasoning**: Conditional probability depends on both test accuracy and prior probability
3. **Medical Decision Making**: Positive test results should not be interpreted in isolation

**Practical Implications:**
- Medical tests should consider population prevalence
- False positives can be common even with accurate tests when base rates are low
- This example illustrates why mass screening for rare conditions can be problematic

### Sequential Testing: How a Second Test Improves Accuracy

One powerful application of Bayesian reasoning is **sequential testing**, where the result of one test becomes the prior probability for the next test. This dramatically improves diagnostic accuracy.

#### Second Test Scenario

Suppose our patient tests positive on the first test (P(Sickness|Test₁) = 13.8%). Now they take a second identical test. We can use the posterior from the first test (13.8%) as the new prior for the second test.

**Mathematical Framework:**
- **Prior (from first test)**: P(Sickness) = 0.138
- **Test characteristics remain the same**:
  - P(Test₂=1|Sickness=1) = 0.95 (sensitivity)
  - P(Test₂=1|Sickness=0) = 0.06 (false positive rate)

**Second Test Calculations:**
- P(Test₂=1) = P(Test₂=1|Sickness=1) × P(Sickness=1) + P(Test₂=1|Sickness=0) × P(Sickness=0)
- P(Test₂=1) = (0.95 × 0.138) + (0.06 × 0.862) = 0.1311 + 0.05172 = 0.18282

- **P(Sickness=1|Test₂=1)** = P(Test₂=1|Sickness=1) × P(Sickness=1) / P(Test₂=1)
- **P(Sickness=1|Test₂=1)** = 0.95 × 0.138 / 0.18282 = 0.1311 / 0.18282 = **0.717** (71.7%)

#### Dramatic Improvement

|Test Scenario|P(Sickness Positive Test)|Improvement|
|---|---|---|
|Single test| 13.8% | -  |
| Two positive tests | 71.7% | **5.2× higher** |

&nbsp;

**If both tests are negative:**
- P(Sickness=0|Test₂=0) = P(Test₂=0|Sickness=0) × P(Sickness=0) / P(Test₂=0)
- P(Sickness=0|Test₂=0) = 0.94 × 0.862 / (0.94 × 0.862 + 0.05 × 0.138)
- P(Sickness=0|Test₂=0) = 0.81028 / 0.81714 = **0.9916** (99.16% certainty of being healthy)

### General Principle: Posterior Becomes Prior

This example illustrates the fundamental Bayesian principle of **sequential updating**:

#### The General Framework

1. **Start with Prior**: P(H) - initial belief about hypothesis H
2. **Observe Evidence**: E - new data or test result
3. **Calculate Posterior**: P(H|E) = P(E|H) × P(H) / P(E)
4. **Update Belief**: Use P(H|E) as the new prior P(H) for next evidence
5. **Repeat**: Process additional evidence sequentially

#### Mathematical Foundation

**Single Update:**
```
P(H|E₁) = P(E₁|H) × P(H) / P(E₁)
```

**Sequential Updates:**
```
P(H|E₁,E₂) = P(E₂|H,E₁) × P(H|E₁) / P(E₂)
             = P(E₂|H) × P(H|E₁) / P(E₂)  [if conditionally independent]
```

**Multiple Updates:**
```
P(H|E₁,E₂,...,Eₙ) ∝ P(H) × ∏ᵢ P(Eᵢ|H)
```

#### Key Insights

1. **Accumulation of Evidence**: Each new piece of evidence refines our beliefs
2. **Conditional Independence**: Evidence can be processed sequentially if conditionally independent
3. **Convergence to Truth**: With sufficient evidence, posterior approaches true probability
4. **Base Rate Evolution**: Initial uncertainty gets resolved through evidence accumulation

#### Applications Beyond Medicine

- **Spam Filtering**: Each email characteristic updates spam probability
- **Quality Control**: Sequential testing improves defect detection
- **Financial Risk**: Multiple indicators refine investment risk assessments
- **Weather Prediction**: Sequential observations improve forecast accuracy

This classical example demonstrates the power of the probability system for analyzing real-world decision-making scenarios involving uncertainty and conditional probabilities.

**Interactive Demonstration:**
Run `python sequential_demo.py` to see a live demonstration of sequential Bayesian updating with the medical test scenario.</content>

---

## Appendix B: Additional Example Input Files

This appendix summarizes several illustrative joint probability distributions included under `inputs/`.
Each file is self-documented with inline comments explaining why the scenario is interesting and what
pitfalls or statistical phenomena it highlights.

### 1. `xor_triplet.inp` (XOR Triplet)
Variables: `A, B, C` with `C = A XOR B` and `A, B` uniform.

Key Properties:
- All three pairwise variable pairs are independent: `I(A;B)=I(A;C)=I(B;C)=0`.
- The triple is not mutually independent because `C` is a deterministic parity constraint.
- Demonstrates that pairwise independence does NOT imply mutual independence.

Suggested Queries:
- `IsIndep(A,C)` (expect True) vs. `P(C|A,B)` (shows determinism).
- `entropy(A,B,C)` vs. `entropy(A)+entropy(B)+entropy(C)` (a gap appears due to dependency).

### 2. `simpsons_paradox.inp` (Simpson's Paradox)
Variables: `Gender (0=Female,1=Male)`, `Treatment (0=Control,1=Drug)`, `Recovery (0=No,1=Yes)`.

Key Properties:
- Within each gender treatment improves recovery probability.
- Aggregated over genders treatment appears *worse* (reversal of association).
- Classic example of a lurking/stratifying variable reversing a trend.

Suggested Queries:
- `P(Recovery=1|Treatment=1)` vs. `P(Recovery=1|Treatment=0)`.
- Stratify: `P(Recovery=1|Treatment=1,Gender=0)` vs. `P(Recovery=1|Treatment=0,Gender=0)` (and for `Gender=1`).
- Mutual information: `mutual_info(Treatment,Recovery)` vs. `mutual_info(Treatment,Recovery|Gender)` (conceptually via conditioning).

### 3. `berkson_bias.inp` (Berkson's / Collider Bias)
Variables: `Disease1 (D1)`, `Disease2 (D2)`, `Admission (A)`.

Key Properties:
- (Approximate) marginal independence between `D1` and `D2`.
- Conditioning on the collider `Admission` induces *negative* association (`selection bias`).
- Highlights why selecting only on admitted cases (A=1) can mislead analyses.

Suggested Queries:
- `IsIndep(D1,D2)` (may be near False depending on approximate values).
- `P(D1=1|D2=1,A=1)` vs. `P(D1=1|D2=0,A=1)` (shows induced dependence).
- Compare to unconditional `P(D1=1|D2=1)` vs. `P(D1=1|D2=0)`.

### 4. `markov_chain4.inp` (Length-4 Markov Chain)
Variables: `A -> B -> C -> D`.

Key Properties:
- Exhibits Markov property: `A ⟂ C | B`, `B ⟂ D | C`, and long-range separation `A ⟂ D | C`.
- Endpoints `A` and `D` are marginally dependent but become (closer to) independent when conditioning on mediating variables.

Suggested Queries:
- `IsCondIndep(A,C|B)` and `IsCondIndep(B,D|C)`.
- Compare `P(D|A)` vs. `P(D|A,C)`.
- Entropy chain: compute `entropy(A,B,C,D)` and decompose via conditional entropies.

### 5. `parity5.inp` (5-Variable Parity / Higher-Order Dependence)
Variables: `X1, X2, X3, X4, Parity` with `Parity = X1 XOR X2 XOR X3 XOR X4` and the first four bits uniform.

Key Properties:
- Any proper subset of the first four variables gives *no* information about `Parity` (low-order independence).
- Full set determines `Parity` (deterministic constraint) — strong higher-order dependence.
- Useful for illustrating why pairwise or low-order statistics can miss structure (relevant in coding theory / cryptography).

Suggested Queries:
- `IsIndep(X1,Parity)` (True) versus `P(Parity|X1,X2,X3,X4)` (deterministic).
- Mutual information growth: compute `mutual_info(Parity,X1)` then `mutual_info(Parity,(X1,X2,X3,X4))` conceptually by manual queries.
- Entropy: `entropy(Parity)` vs. `entropy(X1,X2,X3,X4,Parity)`.

### 6. `monty_hall.inp` (Monty Hall Simplified)
Variables: `Hit`, `SwitchWin` where `SwitchWin = 1 - Hit`.

Key Properties:
- Captures the core result: switching wins with probability 2/3.
- Deterministic complement relation reduces joint entropy.
- Useful minimalist demonstration of conditional update without enumerating all doors.

Suggested Queries:
- `P(Hit)` (≈ 1/3), `P(SwitchWin)` (≈ 2/3).
- `IsIndep(Hit,SwitchWin)` (False).
- `entropy(Hit,SwitchWin)` vs `entropy(Hit)`.

### 7. `explaining_away_alarm.inp` (Explaining Away / Collider)
Variables: `Burglary (B)`, `Earthquake (E)`, `Alarm (A)`, `JohnCalls (J)`, `MaryCalls (M)`.

Key Properties:
- Classic Bayesian network structure B -> A <- E with downstream observers J, M.
- Observing Alarm induces dependence between B and E (collider at A).
- Additional evidence (e.g. learning Burglary=1) can lower belief in Earthquake=1 (explaining away).

Suggested Queries:
- `P(B=1|A=1)`, `P(E=1|A=1)` then `P(E=1|A=1,B=1)`.
- Compare `P(B=1|J=1,M=1)` vs `P(B=1|J=1,M=1,E=1)`.
- Mutual information style reasoning: inclusion/exclusion of collider observations.

### 8. `sprinkler.net` (Cloudy / Sprinkler / Rain / WetGrass)
Variables: `Cloudy (C)`, `Sprinkler (S)`, `Rain (R)`, `WetGrass (W)`.

Structure (classic textbook BN):

```
   C
  / \
 S   R
  \ /
   W
```

Key Properties:
- Fork structure at `C`: given `C`, `S` and `R` become (approximately) conditionally independent.
- Converging influences at `W` (a collider): conditioning on (or observing) `WetGrass` induces dependence between `Sprinkler` and `Rain`.
- Demonstrates how explaining wet grass can raise probability of either cause while lowering the other once one is known (competition under collider conditioning).

Interesting Investigations:
- `IsCondIndep(S,R|C)` (expect True) vs `IsCondIndep(S,R|W)` (expect False).
- Compute `P(R=1|W=1)` vs `P(R=1)` to see diagnostic evidence flow up.
- Compare `P(S=1|W=1,R=1)` vs `P(S=1|W=1,R=0)` (explain-away effect at collider `W`).
- Entropy reduction: `entropy(R)` vs `entropy(R|W)`.

### 9. `cancer.net` (Pollution / Smoker / Cancer / Xray / Dyspnea)
Variables: `Pollution (P)` (1=low), `Smoker (S)`, `Cancer (C)`, `Xray (X)`, `Dyspnea (D)`.

Structure:

```
 P     S
  \   /
    C
   / \
  X   D
```

Key Properties:
- Competing causes / parents (`P`, `S`) jointly influence `Cancer`.
- Two conditionally independent symptom variables (`X`, `D`) given `Cancer` provide **synergistic diagnostic evidence** when observed together.
- Observing both `X=1` and `D=1` sharply raises posterior `P(C=1)` vs observing either alone (evidence accumulation).
- Provides a clean example of how multiple findings combine probabilistically, not additively.

Interesting Investigations:
- Prior vs posterior: `P(C=1)` then `P(C=1|X=1)`, `P(C=1|D=1)`, `P(C=1|X=1,D=1)`.
- Explaining away partial: condition on `C=1` then check dependence of `X` and `D`: `IsIndep(X,D)` vs `IsCondIndep(X,D|C)`.
- Influence of risk factors: `P(C=1|S=1)` vs `P(C=1|S=0)`; similarly for pollution states.
- Information gain: compare `entropy(C)` and `conditional_entropy(C|X)` and with both findings.

### 10. `traffic.net` (RushHour / Accident / Traffic / Late)
Variables: `RushHour (RH)`, `Accident (A)`, `Traffic (T)`, `Late (L)`.

Structure:

```
  RH --> A
   \      \
    \      v
     ----> T --> L
```

Key Properties:
- Two upstream influences on congestion: `RushHour` and `Accident` (with `RH` also influencing accident likelihood). This creates a converging causal pattern into `Traffic` with an additional upstream dependency.
- Diagnostic vs predictive reasoning: observing `Traffic=1` increases belief in both `RH` and `A`; learning additionally that `RH=1` can modulate how much `A` is believed (partial explaining away via shared effect `T`).
- Downstream propagation: `Traffic` strongly mediates effect on `Late`.

Interesting Investigations:
- `P(L=1)` baseline vs `P(L=1|RH=1)` vs `P(L=1|RH=1,A=1)`.
- `P(A=1|T=1)` vs `P(A=1)` (diagnostic lift) and then `P(A=1|T=1,RH=1)` (does knowledge of rush hour reduce incremental surprise?).
- Conditional independence checks: `IsCondIndep(RH,A|T)` (expect False due to direct edge) vs `IsCondIndep(RH,L|T)` (should move toward independence when conditioning on mediator `T`).
- Entropy pathway: `entropy(L)` vs `conditional_entropy(L|T)` to quantify predictive value of traffic status.

---

## Appendix C: CLI Commands

<!-- CLI_HELP_START -->
**NOTE:** This section is auto-generated from the source code. Do not edit it manually; instead update the code or run the generator.

## CLI Commands

Below are the supported CLI commands and their arguments:

### `help`

Show this help message with all commands

### `marginals`

Print all marginal probabilities

### `joint_probs | joint_table`

Print joint probability table

### `independence`

Print independence table for all pairs

### `cond_independence`

Print conditional independence table for all triples

### `cond_probs(n,m)`

Print conditional probabilities for n-tuples given m-tuples

Parameters:

- `n`: size of target tuple (int)
- `m`: size of condition tuple (int)

Examples:

- `cond_probs(1,1)`

### `entropy [vars] [base=<b>]`

Compute Shannon entropy. No args -> full joint.

Parameters:

- `vars`: optional comma-separated variable list (e.g. A,B)
- `base`: optional logarithm base (float, default 2.0)

Examples:

- `entropy`
- `entropy(A)`
- `entropy(A,B base=10)`

### `cond_entropy(A|B) [base=<b>]`

Conditional entropy H(A|B)

Parameters:

- `A`: target variable(s) (comma-separated)
- `B`: conditioning variable(s) (comma-separated)
- `base`: optional logarithm base (float, default 2.0)

Examples:

- `cond_entropy(A|B)`

### `mutual_info(A,B) [base=<b>]`

Mutual information I(A;B)

Parameters:

- `A`: first variable
- `B`: second variable
- `base`: optional logarithm base (float, default 2.0)

Examples:

- `mutual_info(A,B)`

### `precision <n>`

Set or display the probability display precision (number of decimal places for output formatting).

Parameters:

- `n`: integer precision (0–12). If omitted, the current precision is shown.

Examples:

- `precision` (shows current setting)
- `precision 4` (sets precision to 4 decimal places)

### `odds_ratio(A,B)`

Odds ratio for exposure and outcome (returns 'Undefined' if not computable)

Examples:

- `odds_ratio(A,B)`

### `relative_risk(A,B)`

Relative risk (risk ratio) for exposure and outcome (returns 'Undefined' if not computable)

Examples:

- `relative_risk(A,B)`

### `sample(n=1)`

Draw n samples from the joint distribution (returns list of tuples)

Examples:

- `sample`
- `sample(5)`
- `sample(n=10)`

### `save <filename>`

Save the current joint probability table to a file using fixed-point formatting with exactly 10 decimal places for every probability (no scientific notation). Example line: `010: 0.1250000000`.

If the target file already exists, the CLI will prompt for confirmation:

```
save model.inp
File 'model.inp' exists. Overwrite? [y/N]:
```
Respond with `y` or `yes` (case-insensitive) to overwrite; any other response cancels the save.

### `open <filename>`

Load a new probability specification from a `.inp` joint table file or a `.net` Bayesian network file without restarting the program. Replaces the current in-memory system (variables and joint probabilities).

Rules:
- File must exist.
- Extension must be `.inp` or `.net`.
- On success, the current system context is replaced and subsequent commands operate on the newly loaded distribution.

Tab Completion:
- After typing `open ` you can press Tab to complete file and directory names.
- Only `.inp` / `.net` files are suggested; directories appear with a trailing `/` so you can descend further.

Examples:
- `open inputs/medical_test.inp`
- `open inputs/explaining_away_alarm.net`

### `quit | exit`

Exit the program

<!-- CLI_HELP_END -->

## Appendix D: Methodology & Internal Mechanics

This appendix documents how the system parses inputs, constructs internal joint probability tables, and evaluates queries.

### D.1 Parsing `.inp` Joint Tables

1. Read `variables:` header (if absent, auto-generate `A,B,C,...`).
2. Collect lines of the form `<bitpattern>: <float>` (ignoring comments `# ...`).
3. Detect number of variables `n` from bitpattern length.
4. Missing Entries Policy:
  - If exactly one of the 2^n patterns omitted: infer its probability as the residual `1 - sum(provided)` (error if residual < 0).
  - If more than one omitted: assign zero to all missing patterns (sparse specification).
5. Normalization:
  - If total sum within 5% of 1.0, scale all probabilities so the sum is exactly 1.0 (avoids floating drift).
  - If sum >> 1 (beyond tolerance) -> error.
6. Store final vector (length 2^n) in row-major order (bitstring interpreted as binary number with leftmost bit as most significant).

### D.2 Parsing `.net` Bayesian Network Files

1. Read declared variable set from `variables:` (order preserved for output display; actual block order may differ).
2. For each variable block:
  - Parse parent list after `Var:` (or `None`).
  - Collect CPT lines: pattern -> probability interpreted as `P(Var=1 | parents=pattern)`.
  - For parentless variables: allow either `1: p` (then `P(Var=0)=1-p`) or `0: q` (then `P(Var=1)=1-q`). If both provided, prefer explicit `1:` and validate consistency.
3. Validate coverage: must supply all 2^k patterns for k parents; duplicates or missing -> error.
4. Build factor objects storing parent index list and probability vector for `Var=1` given parents.
5. Generate joint by iterating all assignments (0..2^n-1): multiply appropriate conditional for each variable (lookup parent bits) to produce unnormalized joint; final normalization ensures exact stochasticity.

### D.3 Query Evaluation Pipeline

Supported expression forms (examples): `P(A)`, `P(A,B|C)`, `IsIndep(A,B)`, arithmetic like `P(A)*P(B|C)/P(D)`.

Steps:
1. Tokenization: recognize identifiers, operators (`+ - * / ( ) , | ~`), reserved keywords (`P`, `IsIndep`, `IsCondIndep`, `Not`).
2. Parse into an AST distinguishing probability nodes vs arithmetic nodes.
3. For `P(...)` nodes: decompose argument into (target variables with optional explicit value indicators) and optional condition variables.
4. Evaluate a probability node by summing relevant joint entries:
  - Build masks for fixed variables (1 or 0) in numerator.
  - If conditional: compute numerator sum and divide by denominator sum over conditioning context.
5. Independence tests:
  - `IsIndep(X,Y)`: compare `P(X,Y)` with `P(X)P(Y)` under tolerance (e.g. absolute diff < 1e-9 nominal, configurable internally).
  - `IsCondIndep(X,Y|Z)`: verify for all assignments of Z that `P(X,Y|Z=z)` ≈ `P(X|Z=z) P(Y|Z=z)` (skip contexts with zero support).
6. Arithmetic nodes: recursively evaluate child expressions to floats then apply operator in left-associative order, respecting parentheses.

### D.4 Entropy & Information Computation

Given a variable subset S:
1. Marginalize joint to S via summing over other axes (implemented by iterating joint once and accumulating into a small array of size 2^{|S|}).
2. Shannon entropy: `H(S) = -∑ p log_base p` (skip zero probabilities).
3. Conditional entropy `H(A|B)` derived from joint of `A,B` and marginal of `B` via: `H(A|B)=H(A,B)-H(B)`.
4. Mutual information `I(A;B) = H(A)+H(B)-H(A,B)`.

### D.5 Sampling

1. Precompute cumulative distribution array from joint.
2. For each sample: draw uniform u in [0,1), binary search cumulative array to find index.
3. Decode index into bit pattern (variable assignment tuple).

### D.6 Performance Considerations

- The system targets small/medium n (demo / teaching). Joint enumeration is O(2^n); practical up to ~18–20 vars depending on usage.
- Probability queries operate in O(2^n) worst-case but reuse partial computations for repeated marginalization (future optimization: memoization / bitset transforms).
- Entropy / MI computations share marginalization logic; caching could be added if profiling indicates hotspots.

### D.7 Numerical Stability

- All probabilities stored as Python floats; normalization mitigates mild drift.
- Independence comparisons use absolute tolerance; could be extended to relative tolerance for very small probabilities.
- Division by zero in conditional probabilities triggers explicit error messages; for odds ratio / relative risk undefined contexts return `None`.

### D.8 Extensibility Roadmap (Ideas)

- Add support for multi-valued (non-binary) variables via per-variable cardinality metadata.
- Implement variable elimination or junction tree for large sparse networks instead of full joint expansion.
- Introduce log-space computations for extremely small probabilities.
- Add `KL(P||Q)` divergence between two loaded distributions.

## Appendix E: Quick Query Cheat Sheet

Purpose: fast recall of common patterns without scanning the full documentation.

### E.1 Probability & Conditioning
| Task | Example | Notes |
|------|---------|-------|
| Marginal | `P(A)` | P(A=1) |
| Explicit value | `P(A=0)` | Works inside joint/conditional too |
| Joint | `P(A,B)` | Both A=1, B=1 |
| Conditional | `P(A|B)` | P(A=1 | B=1) |
| Mixed joint conditional | `P(A,B\|C,D)` | All left vars =1 given right vars =1 |
| Mixed explicit values | `P(A=0,B\|C=0)` | Any combination of explicit 0/1 |
| Negation shorthand | `P(~A)` | Same as `P(A=0)` |
| Nested negation | `P(A\|~B)` | Conditioning with negation |

### E.2 Independence
| Task | Example | Interpretation |
|------|---------|----------------|
| Test independence | `IsIndep(A,B)` | True if P(A,B)=P(A)P(B) |
| Conditional independence | `IsCondIndep(A,B\|C)` | Checks all assignments of C |

### E.3 Arithmetic & Composition
| Task | Example | Notes |
|------|---------|-------|
| Sum of probabilities | `P(A)+P(B)` | Adds numeric results |
| Product with conditional | `P(A\|B)*P(B)` | Chain rule component |
| Bayes ratio | `P(B\|A)*P(A)/P(B)` | Derivation of P(A|B) |

### E.4 Information Measures
| Task | Example | Notes |
|------|---------|-------|
| Entropy (joint) | `entropy(A,B)` | Base 2 unless overridden |
| Full joint entropy | `entropy` | All variables |
| Conditional entropy | `cond_entropy(A\|B)` | H(A|B) |
| Mutual information | `mutual_info(A,B)` | I(A;B)=H(A)+H(B)-H(A,B) |

### E.5 Epidemiology Utilities
| Task | Example | Notes |
|------|---------|-------|
| Odds ratio | `odds_ratio(A,B)` | Exposure A, outcome B |
| Relative risk | `relative_risk(A,B)` | Returns 'Undefined' when baseline zero |

### E.6 Sampling
| Task | Example | Notes |
|------|---------|-------|
| Draw n samples | `sample(5)` | Returns list of tuples |

### E.7 Workflow Tips
| Goal | Pattern |
|------|---------|
| Check normalization | `P(A)+P(~A)` (expect 1) |
| Diagnose dependency | Compare `P(A\|B)` vs `P(A)` |
| Explaining away | Compare `P(Cause1\|Effect)` vs `P(Cause1\|Effect,Cause2)` |
| Value of evidence | `entropy(A)` vs `cond_entropy(A\|B)` |
| Posterior update sequence | Use arithmetic: `P(Test\|Disease)*P(Disease)/P(Test)` |

### E.8 Common Pitfalls
- Forgetting that `P(A,B|C)` assumes `A=B=1` unless explicit 0 given.
- Using `IsIndep` when supports are tiny—floating noise may mislead; inspect raw probabilities.
- Confusing `P(~A)` with `1-P(A)` (they're equal, but direct query avoids accumulation error when P(A) computed by summing many small cells).

---
Use this sheet interactively: after loading a file, you can paste lines directly (one at a time) into the CLI.
