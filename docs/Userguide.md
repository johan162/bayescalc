# BayesCalc User Guide

A comprehensive guide to using BayesCalc for Bayesian probability analysis, statistical reasoning, and interactive exploration of probabilistic relationships.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation & Quick Start](#installation--quick-start)
3. [File Formats](#file-formats)
   - [Joint Probability Tables (.inp)](#joint-probability-tables-inp)
   - [Bayesian Networks (.net)](#bayesian-networks-net)
   - [Multi-Valued Variables](#multi-valued-variables)
4. [Interactive CLI](#interactive-cli)
   - [Basic Probability Queries](#basic-probability-queries)
   - [Independence Testing](#independence-testing)
   - [Statistical Utilities](#statistical-utilities)
   - [Information Theory](#information-theory)
   - [Workflow Commands](#workflow-commands)
5. [Mathematical Background](#mathematical-background)
   - [Bayesian Reasoning](#bayesian-reasoning)
   - [Information Theory](#information-theory-1)
   - [Sequential Updates](#sequential-updates)
6. [Example Walkthrough: Medical Testing](#example-walkthrough-medical-testing)
7. [CLI Commands Reference](#cli-commands-reference)
8. [Example Networks Library](#example-networks-library)
9. [Advanced Usage](#advanced-usage)
   - [Sampling](#sampling)
   - [Precision Control](#precision-control)
   - [Epidemiological Measures](#epidemiological-measures)
10. [APPENDIX A: Example Networks Library](#appendix-a-example-networks-library)
11. [APPENDIX B: Command Quick Reference](#appendix-b-command-quick-reference)
12. [APPENDIX C: Classical Medical Test Example](#appendix-c-classical-medical-test-example)


---

## Introduction

BayesCalc is an interactive command-line tool for exploring Bayesian probability distributions, conditional probabilities, and information-theoretic quantities. It supports both joint probability tables and Bayesian network specifications, making it useful for:

- **Educational exploration** of probabilistic reasoning
- **Research analysis** of dependency structures
- **Statistical modeling** validation and interpretation
- **Interactive learning** of Bayesian concepts

The system provides a natural query interface where you can ask questions like `P(Disease|Test)` or `IsIndep(A,B)` and get immediate numerical answers along with supporting analysis.

Among other things it allows

 - calculations to be done directly using standard mathematical notations like `P(A|B,C) * P(C)`
 - easy definition of network from either JPT (Joint Probability) or CPT (Conditional Probability) tables.
 - the usage of both boolean and multi-valued variables
 - the definition of custom variable and statenames
 
The main entry point is `bayescalc.py` and the easiest way to start using the calculator and one of the 
included examples. As quick example using the included medical Bayesian network data is by running:

```bash
> python bayescalc.py inputs/medical_test.inp
...
Query: 
```

---

## Installation & Quick Start

### Prerequisites
- Python 3.7 or later
- Required packages for development: `click`, `pytest`

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd bayescalc

# Install dependencies
pip install -r requirements-dev.txt

# Run with an example
python bayescalc.py inputs/medical_test.inp
```

### First Steps
Once launched, try these basic commands:
```
marginals            # View all marginal probabilities
P(Sickness|Test)     # Conditional probability query
IsIndep(A,B)         # Test independence
entropy              # Information content
help                 # Show all commands
```


> [!NOTE]
> The parser accepts two forms of negation. You can write explicit negation using `Not(...)`,
> for example `P(Not(Sickness))`, or use the inline tilde `~` as a shorthand (common in 
> mathematical notation), for example `P(~Sickness)` or `IsIndep(~Sickness,Test)`. 
> Tab-completion also works when you type a leading `~` (e.g., type `~S` and press Tab to 
> complete `~Sickness`).


# Command Line Usage Quick Reference

You can see these options anytime with `python bayescalc.py --help` (or by supplying a file then `--help`). Below is an inlined copy of the main CLI arguments for convenience.

```
usage: bayescalc.py [-h] [--names NAMES [NAMES ...]] [--cmds CMDS] [file]

Positional arguments:
  file                  Optional path to a probability specification file (.inp joint table or .net Bayesian network). If omitted you'll be prompted or can explore interactively.

Optional arguments:
  -h, --help            Show help and exit.
  --names, -n           One or more custom variable names to apply when loading a joint table (.inp). Provide space-separated names (must match variable count). Ignored for multi-valued .net that already declare variables.
  --cmds CMDS           Semicolon-separated list of commands to execute non-interactively after loading the file, then exit (unless a REPL-only command requires interaction). Example: --cmds "P(A);entropy;networks;exit".
```

**Usage Examples:**
```bash
# Interactive mode (manual input)
python bayescalc.py

# Load from file with default variable names
python bayescalc.py input.txt

# Load from file with custom variable names
python bayescalc.py input.txt --names Rain Sprinkler WetGrass

# Load from file and run batch commands (then quit)
python bayescalc.py inputs/weather_picnic.net --cmds "P(Weather=Sunny);entropy;exit"

# Non-interactive batch example (run commands then quit):
python bayescalc.py inputs/medical_test.inp --cmds "P(Sickness|Test);odds_ratio(Sickness,Test);exit"

# Show help
python bayescalc.py --help
```

> [!TIP]
> Use `--cmds` in scripts/CI to capture deterministic output without driving the REPL.


The input data can either be specified interactively (which is a bit tedious) or read from a file that can either have the format of a joint probability table (possibly sparse) or as a number of conditional probability tables which specifies a Bayesian network. The Bayesian network format is often the simplest way to specify the system
as it allows the same information to be specified in a more conscise format. The precise format is described in later sections in this document. Internally both input methods will establish a complete joint distribution table of size 2^N where N is the number of variables. In terms of performance the system can easily work with networks up to 20 variables on a 8GB RAM computer.

The scipt provides both public APIs as well as a CLI interface for interactive experiments.


## File Formats

BayesCalc supports two primary input formats for defining probability distributions.

### Joint Probability Tables (.inp)

The `.inp` format specifies joint probability distributions directly through enumeration of all possible variable assignments.

#### Basic Structure

```txt
variables: <VARIABLES>
binary_pattern1: <PROBABILITY>
binary_pattern2: <PROBABILITY>
...
```

**Variables Rules**

- Must start with "variables:" (case-insensitive)
- Variable names separated by commas
- Names can contain spaces (will be trimmed)
- If omitted, defaults to A, B, C, ..

**Binary pattern Rules**

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
variables: A, B, C
# Joint probability table
000: 0.125   # P(A=0, B=0, C=0)
001: 0.125   # P(A=0, B=0, C=1)
010: 0.125   # P(A=0, B=1, C=0)
011: 0.125   # P(A=0, B=1, C=1)
100: 0.125  # P(A=1, B=0, C=0)
101: 0.125  # P(A=1, B=0, C=1)
110: 0.125  # P(A=1, B=1, C=0)
111: 0.125  # P(A=1, B=1, C=1)
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
- File can have any number of comment lines interspersed with data.



#### Key Features
- **Variable Declaration**: Optional `variables:` header (auto-generates A,B,C,... if omitted)
- **Bit Patterns**: Each line maps a binary pattern to its probability
- **Comments**: Lines starting with `#` are ignored
- **Missing Entries**: 
  - If exactly one pattern omitted: inferred as residual (1 - sum of others)
  - If multiple omitted: assigned probability 0 (sparse specification)
- **Auto-normalization**: Sums within 5% of 1.0 are normalized to exactly 1.0

#### Example: Medical Test
```
variables: Sickness, Test
# Base rate: P(Sickness=1) = 0.01 (1% prevalence)
# Test accuracy: 95% sensitivity, 6% false positive rate

00: 0.930500  # P(Sickness=0, Test=0) = healthy, negative
01: 0.059400  # P(Sickness=0, Test=1) = healthy, positive  
10: 0.000500  # P(Sickness=1, Test=0) = sick, negative
11: 0.009500  # P(Sickness=1, Test=1) = sick, positive
```

### Bayesian Networks (.net)

The `.net` format defines probability distributions through conditional probability tables (CPTs) in a Bayesian network structure.
There are two variants of allowed input file

  1. For multi-valued variables (also works for Boolean)
  2. A simplified format for boolean variables (**does NOT** work for multi-values variables)

The enhanced `.net` format allows each variable to have an arbitrary discrete state space instead of assuming all variables are binary.

Key elements:

1. Variable declaration
  - One variable statement per roe 
  - Multi-valued: `variable Weather {Sunny, Rainy, Cloudy}`
  - Boolean (implicit states `0,1`): `variable Alarm`
2. Parent specification
  - `Alarm <- None` (root)
  - `Traffic <- (Weather)`
  - `Risk <- (Age, Habits)`
3. CPT lines
  - Root variable states: one line per state: `Sunny: 0.6`, `Rainy: 0.4`, `Cloudy: 0.0` (must sum to 1.0 including any zeros)
  - Child variable: `(ChildState | parent_state1, parent_state2, ...) : probability`
    Example: `(Heavy | Rainy): 0.8`
4. Probability validation
  - For every parent state combination, the probabilities across all child states must sum to 1.0 (missing states treated as 0 before validation, so if sum < 1 it triggers an error).
5. Queries
  - Multi-valued variables require explicit assignments: `P(Weather=Rainy)`
  - Boolean variables still accept `P(Rain)` (meaning state 1) and negation `P(~Rain)` / `P(Not(Rain))`.
  - Mixed: `P(Traffic=Heavy|Weather=Sunny)` works as expected.

> [!NOTE] 
> - Variable names may be single letters (`A`,`B`,...) or custom names specified in input files (`Rain`, `Sickness`, ...).
> - Whitespace and simple parentheses are supported inside `P(...)` queries. Use `~` as a concise negation operator or `Not(...)` for clarity.


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



#### EXAMPLE 1: - Five Boolean variables in *.net files using the multi-value syntax

All cihld/parent states are explicitly specified. 

```txt
# Alarm network, variant 1 - Multi-values variable format with Boolean variables
variable B    # Burglery
variable E    # Earthquake
variable A    # Alarm
variable J    # John calls
variable M    # Mary calls

B <- None
1: 0.001 # P(B)
0: 0.999

E <- None
1: 0.002 # P(E)
0: 0.998

A <- (B, E) 
(1 | 1,1): 0.95
(0 | 1,1): 0.05
(1 | 1,0): 0.94
(0 | 1,0): 0.06
(1 | 0,1): 0.29
(0 | 0,1): 0.71
(1 | 0,0): 0.001
(0 | 0,0): 0.999

J <- (A) 
(1|1): 0.9
(1|0): 0.05
(0|1): 0.1
(0|0): 0.95

M <- (A) 
(1|1): 0.7
(1|0): 0.01
(0|1): 0.3
(0|0): 0.99

```

You can load this with:
```bash
python bayescalc.py inputs/explaining_away_alarm.net
```

From Python:
```python
ps = ProbabilitySystem.from_file('exainputs/explaining_away_alarm.net')
print(ps.get_marginal_probability([0],[1]))  # P(B=1)
```


**Key Features:**
- **Variable Declaration**: Defines all variables in display order
- **Parent Specification**: Lists parents for each variable (or `None` for roots)
- **Conditional Tables**: Each pattern specifies P(Variable=1|Parents=pattern)
- **Complete Coverage**: Must specify probabilities for all parent combinations


#### EXAMPLE 2: - Five Boolean variables in *.net files using the binary-value syntax

For boolean only network a simplified `*.net` file can be made. Again the same example as previously
but this time we can use that all variables are boolean and use the simplified format:

```
# Alarm network, variant 2 - Boolean-value variables
variables: B, E, A, J, M

B : None
0.001 # P(B)

E: None
0.002 # P(E)

A: B, E
11: 0.95
10: 0.94
01: 0.29
00: 0.001

J: A
1: 0.9
0: 0.05

M: A
1: 0.7
0: 0.01
```

**Key Features:**
- **Variable Declaration**: Defines all variables in display order in one line
- **Parent Specification**: Lists parents for each variable (or `None` for roots)
- **CPT for True values only:** Only the rows in the CPT for the true value needs to be specified
- **Complete Coverage Autocalculated**: Missing values are automatically calculated 

> [!TIP]
> For boolean variable networks either style can be used but the binary syntax requires a lot less input


#### Example 3: Five variable Alarm Network with long variable names using the binary-value syntax

This is again he same example as before but this time with long variable names

```
# Alarm network, variant 2 - Boolean-value long variables 
variables: Burglary, Earthquake, Alarm, JohnCalls, MaryCalls

Burglary:
parents: None
1: 0.001

Earthquake:
parents: None  
1: 0.002

Alarm:
parents: Burglary, Earthquake
00: 0.001   # P(Alarm=1|B=0,E=0)
01: 0.290   # P(Alarm=1|B=0,E=1) 
10: 0.940   # P(Alarm=1|B=1,E=0)
11: 0.950   # P(Alarm=1|B=1,E=1)

JohnCalls:
parents: Alarm
0: 0.050    # P(JohnCalls=1|Alarm=0)
1: 0.900    # P(JohnCalls=1|Alarm=1)

MaryCalls:
parents: Alarm
0: 0.010    # P(MaryCalls=1|Alarm=0)
1: 0.700    # P(MaryCalls=1|Alarm=1)
```

> [!IMPORTANT]
> The child value is always implicitly assumed to be "True" when using binary format.

### Multi-Valued Variables

The `.net`format also supports variables with more than two states (cardinality > 2), using explicit state names.
Here the main differenc is that each varaiable is specified on separate rows using the keyword `variable` , for example as

```txt
variable Weather {Sunny, Cloudy, Rainy}
```

Each staet in thebBN is then specified as

```
Child <- None    # Root node no parent
```

or

```
Child <- (Parent1, Parent2, ... ParentN)   # Node with N parents
```


#### Example: 3 Multi valus Variables  - Weather Forecast
```
# Weather-Picnic BN: Weather influences Forecast; both affect Picnic decision (showing multi-valued causal + decision interplay).

variable Weather {Sunny, Cloudy, Rainy}
variable Forecast {Sunny, Cloudy, Rainy}
variable Picnic {Yes, No}

# Root
Weather <- None
Sunny: 0.5
Cloudy: 0.3
Rainy: 0.2

# Forecast depends on Weather
Forecast <- (Weather)
(Sunny | Sunny): 0.7
(Cloudy | Sunny): 0.2
(Rainy | Sunny): 0.1
(Sunny | Cloudy): 0.2
(Cloudy | Cloudy): 0.6
(Rainy | Cloudy): 0.2
(Sunny | Rainy): 0.1
(Cloudy | Rainy): 0.2
(Rainy | Rainy): 0.7

# Picnic decision depends on Weather & Forecast
Picnic <- (Weather, Forecast)
(Yes | Sunny,Sunny): 0.9
(No  | Sunny,Sunny): 0.1
(Yes | Sunny,Cloudy): 0.8
(No  | Sunny,Cloudy): 0.2
(Yes | Sunny,Rainy): 0.4
(No  | Sunny,Rainy): 0.6
(Yes | Cloudy,Sunny): 0.7
(No  | Cloudy,Sunny): 0.3
(Yes | Cloudy,Cloudy): 0.5
(No  | Cloudy,Cloudy): 0.5
(Yes | Cloudy,Rainy): 0.3
(No  | Cloudy,Rainy): 0.7
(Yes | Rainy,Sunny): 0.4
(No  | Rainy,Sunny): 0.6
(Yes | Rainy,Cloudy): 0.3
(No  | Rainy,Cloudy): 0.7
(Yes | Rainy,Rainy): 0.1
(No  | Rainy,Rainy): 0.9
```


## Interactive CLI

The heart of BayesCalc is its interactive command-line interface that provides natural language queries for probabilistic reasoning.
After the script have been started it will enter a "Read-Evaluate-Print-Loop" (REPL) where commands can be given. 

The following sectino gives a few examples

### Basic Probability Queries

#### Marginal Probabilities
```bash
P(A)              # P(A=1) - probability that A is true
P(A=0)            # P(A=0) - explicit value specification
P(~A)             # P(A=0) - negation shorthand
```

#### Joint Probabilities
```bash
P(A,B)            # P(A=1, B=1) - both variables true
P(A=0,B)          # P(A=0, B=1) - mixed values
P(~A,B)           # P(A=0, B=1) - negation shorthand
```

#### Conditional Probabilities
```bash
P(A|B)            # P(A=1|B=1) - A given B
P(A|B=0)          # P(A=1|B=0) - A given B false
P(A|~B)           # P(A=1|B=0) - negation shorthand
P(A,B|C)          # P(A=1,B=1|C=1) - joint conditional
P(A=0|B,C=0)      # P(A=0|B=1,C=0) - mixed conditions
```

#### Arithmetic Operations
```bash
P(A) + P(B)               # Sum of probabilities
P(A|B) * P(B)             # Chain rule application
P(B|A) * P(A) / P(B)      # Bayes' theorem manual
1 - P(A)                  # Complement probability
```

### Independence Testing

#### Marginal Independence
```bash
IsIndep(A,B)      # Tests if P(A,B) = P(A)×P(B)
```

#### Conditional Independence
```bash
IsCondIndep(A,B|C)    # Tests if A ⊥ B | C
                      # Checks all assignments of C
```

> [!NOTE]
> The system uses numerical tolerance (default 1e-9) to account for floating-point precision when testing independence.

### Statistical Utilities

#### Epidemiological Measures
```bash
odds_ratio(Exposure,Outcome)     # Odds ratio calculation
relative_risk(Exposure,Outcome)  # Relative risk (risk ratio)
```

Both functions return `'Undefined'` when denominators are zero or calculations are not meaningful.

#### Sampling
```bash
sample()          # Draw one sample from joint distribution
sample(5)         # Draw 5 samples
sample(n=10)      # Named parameter form
```

Returns list of tuples representing variable assignments.

### Information Theory

#### Entropy Measures
```bash
entropy()                # H(all variables) - joint entropy
entropy(A)              # H(A) - marginal entropy
entropy(A,B)            # H(A,B) - joint entropy of subset
entropy(A base=10)      # Entropy with log base 10
```

#### Conditional Entropy
```bash
cond_entropy(A|B)           # H(A|B) conditional entropy
cond_entropy(A|B base=e)    # Natural logarithm base
```

#### Mutual Information
```bash
mutual_info(A,B)            # I(A;B) mutual information
mutual_info(A,B base=10)    # Different logarithm base
```

### Workflow Commands

#### File Operations
```bash
open filename.inp          # Load new distribution
save output.inp            # Save current distribution
networks                   # List available examples
networks inp               # Filter by file type
```

#### Display Control
```bash
marginals                  # Show all marginal probabilities
joint_probs                # Show joint table (limited to 64 rows)
joint_table                # Show complete joint table (unlimited)
table                      # Alias for joint_table
independence               # All pairwise independence tests
cond_independence          # All conditional independence tests
precision 4                # Set display precision
precision                  # Show current precision
```

#### System Commands
```bash
help                       # Show command reference
quit                       # Exit program
exit                       # Exit program (alias)
```

---

## Mathematical Background

### Bayesian Reasoning

Bayesian reasoning provides a principled framework for updating beliefs in the presence of new evidence. The core relationship is **Bayes' theorem**:

**P(H|E) = P(E|H) × P(H) / P(E)**

which alternatively can be written

**P(H|E) = P(H,E) / P(E)**'

the core insight this give is how tio "flip" a conditional probability. 

Where:
- **P(H|E)**: Posterior probability - updated belief in hypothesis H given evidence E
- **P(E|H)**: Likelihood - probability of observing evidence E if hypothesis H is true  
- **P(H)**: Prior probability - initial belief in hypothesis H
- **P(E)**: Marginal likelihood - total probability of observing evidence E

#### Key Concepts

**Prior Distribution**: Represents initial beliefs before observing evidence. Can be:
- **Informative**: Based on domain knowledge or previous studies
- **Non-informative**: Uniform or minimally constraining when knowledge is limited

**Posterior Distribution**: Updated beliefs after incorporating evidence. Becomes the new prior for subsequent evidence.

**Likelihood Function**: Connects hypotheses to observable data through the probability model P(data|hypothesis).

### Information Theory

Information theory quantifies uncertainty and the value of information using entropy-based measures.

#### Shannon Entropy
**H(X) = -∑ P(x) log P(x)**

- Measures average uncertainty in variable X
- Higher entropy indicates more uncertainty/randomness
- Measured in bits (log base 2), nats (natural log), or other units

#### Conditional Entropy
**H(X|Y) = ∑ P(y) H(X|Y=y) = H(X,Y) - H(Y)**

- Average uncertainty in X given knowledge of Y
- Reduction in entropy represents information gain

#### Mutual Information
**I(X;Y) = H(X) - H(X|Y) = H(Y) - H(Y|X) = H(X) + H(Y) - H(X,Y)**

- Measures information shared between X and Y
- I(X;Y) = 0 if and only if X and Y are independent
- Always non-negative; higher values indicate stronger dependence

### Sequential Updates

One of the most powerful applications of Bayesian reasoning is sequential updating, where evidence is incorporated incrementally:

1. **Start with prior**: P(H)
2. **Observe evidence E₁**: P(H|E₁) = P(E₁|H) × P(H) / P(E₁)
3. **Use posterior as new prior**: P(H) ← P(H|E₁)
4. **Observe evidence E₂**: P(H|E₁,E₂) = P(E₂|H) × P(H|E₁) / P(E₂)
5. **Continue iteratively**

This approach is fundamental to machine learning, signal processing, and scientific inference. The script `scripts/sequential_demo.py` when run
demonstrates the strength of this operation.

---

## Example Walkthrough: Medical Testing

This comprehensive example demonstrates key concepts through a realistic medical testing scenario.

### Scenario Setup

Consider a medical test for a rare disease with the following characteristics:
- **Disease prevalence**: 1% in the population (base rate)
- **Test sensitivity**: 95% (detects disease when present)
- **Test specificity**: 94% (negative when disease absent)
- **False positive rate**: 6% (positive when disease absent, calculated as (1 - specificity))

### File Specification

Use the existing `inputs/medical_test.inp`:

- **Variables**: Sickness (0=healthy, 1=sick), Test (0=negative, 1=positive)
- **Base Rate**: Sickness occurs in 1% of the population
- **Test Sensitivity**: Correctly identifies sick person with 95% probability
- **Test Specificity**: Wrongly identifies healthy person as sick in 6% of cases

***Contingency Table Construction**

Using the given probabilities, we can now construct the joint probability distribution and use that to create the input file.

| Sickness | Test | Probability | Calculation |
|----------|------|-------------|-------------|
| 0 (Healthy) | 0 (Negative) | 0.9306 | 0.99 × (1-0.06) = 0.99 × 0.94 |
| 0 (Healthy) | 1 (Positive) | 0.0594 | 0.99 × 0.06 |
| 1 (Sick) | 0 (Negative) | 0.0005 | 0.01 × (1-0.95) = 0.01 × 0.05 |
| 1 (Sick) | 1 (Positive) | 0.0095 | 0.01 × 0.95 |


```
# Input File: `inputs/medical_test.inp`
variables: Sickness, Test
00: 0.930500  # P(Sickness=0, Test=0) = 0.99 × 0.94 = 0.9306
01: 0.059400  # P(Sickness=0, Test=1) = 0.99 × 0.06 = 0.0594  
10: 0.000500  # P(Sickness=1, Test=0) = 0.01 × 0.05 = 0.0005
11: 0.009500  # P(Sickness=1, Test=1) = 0.01 × 0.95 = 0.0095
```

### Interactive Analysis

Load the scenario and explore:
```bash
python bayescalc.py inputs/medical_test.inp
```

#### Basic Probabilities
```bash
contingency_table     # Show contingency table
P(Sickness)           # Result: 0.0100 (1% base rate)
P(Test)               # Result: 0.0689 (6.89% positive tests)
P(Test|Sickness)      # Result: 0.9500 (95% sensitivity)
```

#### The Counterintuitive Result
```bash
P(Sickness|Test)      # Result: 0.1379 (13.79%)
```

**Interpretation**: Despite the test being 95% accurate, a positive result only indicates 13.8% probability of actually having the disease! 
This demonstrates the critical importance of base rates in Bayesian reasoning.

#### Manual Verification (Bayes' Theorem)
```bash
P(Test|Sickness) * P(Sickness) / P(Test)    # Result: 0.1379
# Calculation: (0.95 × 0.01) / 0.0689 = 0.0095 / 0.0689 ≈ 0.1379
```

#### Understanding the Joint Distribution
```bash
joint_table                    # Show complete probability table
marginals                     # View marginal distributions
IsIndep(Sickness,Test)        # Result: False (dependent as expected)
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


### Sequential Testing Analysis

What happens if a patient tests positive twice? Sequential Bayesian updating dramatically improves accuracy.

#### First Test Result
After first positive test: P(Sickness|Test₁⁺) = 13.8%

#### Second Test Calculation
Use 13.8% as new prior probability:
- New prior: P(Sickness) = 0.138
- Same test characteristics: P(Test₂⁺|Sickness) = 0.95, P(Test₂⁺|~Sickness) = 0.06

**Manual calculation**:
- P(Test₂⁺) = 0.95 × 0.138 + 0.06 × 0.862 = 0.1311 + 0.0517 = 0.1828
- P(Sickness|Test₂⁺) = (0.95 × 0.138) / 0.1828 = 0.1311 / 0.1828 = **71.7%**

#### Dramatic Improvement Summary

| Test Scenario | P(Disease\|Positive) | Improvement |
|---------------|---------------------|-------------|
| Single test   | 13.8%              | -           |
| Two tests     | 71.7%              | 5.2× higher |

This demonstrates the power of accumulating evidence in Bayesian reasoning.

> [!TIP]
> The program inlcudes a script `scripts/sequential_demo.py` which you can run to see the dramatic increase when running the
> test multiple times.


This example illustrates why understanding Bayesian reasoning is crucial for medical decision-making, quality control, and any domain involving probabilistic evidence.

---

## CLI Commands Reference

<!-- CLI_HELP_START -->
> [!WARNING]
> This section is auto-generated from the source code. Do not edit it manually; instead update the code or run the generator.

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

### `networks [inp|net]`
List example network files in the `inputs/` directory with a brief description (taken from the file's leading comment block up to the first blank or data line). Shows a `Vars` column with detected variable count.

Optional filter argument limits results by extension:

- `networks` (all `.inp` and `.net`)
- `networks inp` (only joint table `.inp` files)
- `networks net` (only Bayesian network `.net` files)

Examples:
```
networks
networks net
networks inp
```


---

# APPENDIX A: Example Networks Library

<!-- CLI_HELP_END -->


## Example Networks Library

BayesCalc includes a comprehensive library of example networks that illustrate important concepts in probability theory, statistics, and machine learning. These examples are located in the `inputs/` directory and can be loaded using the `open` command or by specifying them when starting the program.

### Usage

```bash
# List all available examples
networks

# Filter by type
networks inp    # Joint probability tables
networks net    # Bayesian networks

# Load an example
open inputs/medical_test.inp
```

### Classic Probability Paradoxes

#### 1. **Simpson's Paradox** (`simpsons_paradox.inp`)
**Variables**: Gender, Treatment, Recovery

**Key Insight**: Treatment appears harmful when aggregated across groups but beneficial within each gender group. Demonstrates how lurking variables can reverse statistical associations.

**Suggested Queries**:
```bash
P(Recovery|Treatment)           # Aggregate (misleading)
P(Recovery|Treatment,Gender=0)  # Within female group
P(Recovery|Treatment,Gender=1)  # Within male group
```

#### 2. **Monty Hall Problem** (`monty_hall.inp`)
**Variables**: Hit, SwitchWin

**Key Insight**: Simplified representation showing switching wins 2/3 of the time. Demonstrates counter-intuitive conditional probability.

**Suggested Queries**:
```bash
P(Hit)         # Initial choice success: 1/3
P(SwitchWin)   # Switching success: 2/3
IsIndep(Hit,SwitchWin)  # False (perfect negative correlation)
```

### Bayesian Network Structures

#### 3. **Sprinkler Network** (`sprinkler.net`)
**Variables**: Cloudy, Sprinkler, Rain, WetGrass

**Structure**: Classic fork-collider pattern demonstrating d-separation principles.

Structure (classic textbook BN):

```
   C
  / \
 S   R
  \ /
   W
```


**Key Insights**: 
- Fork at Cloudy: Sprinkler and Rain independent given Cloudy
- Collider at WetGrass: Sprinkler and Rain dependent given WetGrass
- Converging influences at `W` (a collider): conditioning on (or observing) `WetGrass` induces dependence between `Sprinkler` and `Rain`.
- Demonstrates how explaining wet grass can raise probability of either cause while lowering the other once one is known (competition under collider conditioning).


**Suggested Queries**:
```bash
IsCondIndep(Sprinkler,Rain|Cloudy)     # True (d-separated)
IsCondIndep(Sprinkler,Rain|WetGrass)   # False (collider)
P(Rain|WetGrass,Sprinkler=0)          # Explaining away
```

#### 4. **Explaining Away (Alarm)** (`explaining_away_alarm.net`)
**Variables**: Burglary, Earthquake, Alarm, JohnCalls, MaryCalls

**Key Insights**: Observing alarm makes burglary and earthquake dependent. Learning about one cause reduces belief in the other.
- Classic Bayesian network structure B -> A <- E with downstream observers J, M.
- Observing Alarm induces dependence between B and E (collider at A).
- Additional evidence (e.g. learning Burglary=1) can lower belief in Earthquake=1 (explaining away).


**Suggested Queries**:
```bash
P(Burglary|Alarm)                    # Diagnostic reasoning
P(Earthquake|Alarm,Burglary=1)       # Explaining away effect
P(Burglary|JohnCalls,MaryCalls)      # Evidence accumulation
```

#### 5. **Traffics and Accidents** (`traffic.net`)
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


### Statistical Phenomena

#### 6. **Berkson's Bias** (`berkson_bias.inp`)
**Variables**: Disease1, Disease2, Admission

**Key Insight**: Conditioning on a collider (hospital admission) induces spurious negative correlation between independent diseases.

**Suggested Queries**:
```bash
IsIndep(Disease1,Disease2)                    # Marginal independence
P(Disease1|Disease2=1,Admission=1)           # Induced dependence
P(Disease1|Disease2=0,Admission=1)           # Selection bias
```

#### 7. **Markov Chain** (`markov_chain4.inp`)
**Variables**: A → B → C → D

**Key Insight**: Demonstrates Markov property where variables are conditionally independent of non-adjacent variables given their neighbors.

**Suggested Queries**:
```bash
IsCondIndep(A,C|B)      # Markov property
IsCondIndep(A,D|C)      # Long-range separation
P(D|A)                  # Marginal dependence
P(D|A,C)                # Conditional independence
```

### Information Theory Examples

#### 8. **XOR Triplet** (`xor_triplet.inp`)
**Variables**: A, B, C (where C = A XOR B)

**Key Insight**: All pairwise independent but not mutually independent. Demonstrates limitation of pairwise analysis.

**Suggested Queries**:
```bash
IsIndep(A,C)            # True (pairwise independent)
IsIndep(B,C)            # True (pairwise independent)
P(C|A,B)                # Deterministic constraint
entropy(A,B,C)          # Less than H(A)+H(B)+H(C)
```

#### 9. **Higher-Order Dependence** (`parity5.inp`)
**Variables**: X1, X2, X3, X4, Parity (where Parity = X1⊕X2⊕X3⊕X4)

**Key Insight**: Low-order statistics miss high-order structure. Individual variables provide no information about parity, but all four together determine it.

**Suggested Queries**:
```bash
IsIndep(X1,Parity)              # True (no individual information)
mutual_info(X1,Parity)          # Zero mutual information
P(Parity|X1,X2,X3,X4)          # Deterministic given all
```

### Multi-Valued Networks

#### 10. **Weather Picnic** (`weather_picnic.net`)
**Variables**: Weather{Sunny,Cloudy,Rainy}, Forecast{Sunny,Cloudy,Rainy}, Picnic{Yes,No}

**Key Insight**: Multi-state variables with imperfect forecasting and decision-making under uncertainty.

**Suggested Queries**:
```bash
P(Weather=Rainy)                    # Prior weather probability
P(Picnic=Yes|Forecast=Sunny)        # Decision based on forecast
P(Weather=Sunny|Forecast=Sunny)     # Forecast reliability
```

#### 11. **Medical Diagnosis** (`medical_diagnosis_mini.net`)
**Variables**: Disease{None,Mild,Severe}, TestResult{Negative,WeakPos,StrongPos}, SymptomA{Absent,Mild,Strong}, SymptomB{Absent,Present}, Treatment{None,Basic,Aggressive}

**Key Insight**: Multi-stage diagnostic reasoning with severity levels and treatment decisions.

**Suggested Queries**:
```bash
P(Disease=Severe|TestResult=StrongPos)                  # Diagnostic accuracy
P(Treatment=Aggressive|Disease=Mild,SymptomA=Strong)    # Treatment decisions
P(Disease=Severe|SymptomA=Strong,SymptomB=Present)     # Symptom-based diagnosis
```

### Complex Networks

#### 12. **Cancer Network** (`cancer.net`)
**Variables**: Pollution, Smoker, Cancer, Xray, Dyspnea

**Structure**: Competing causes with multiple symptoms providing synergistic evidence.

Structure:

```
 P     S
  \   /
    C
   / \
  X   D
```


**Key Insights**:
- Multiple risk factors (pollution, smoking) jointly influence cancer
- Independent symptoms (X-ray, dyspnea) provide additive diagnostic value
- Competing causes / parents (`P`, `S`) jointly influence `Cancer`.
- Two conditionally independent symptom variables (`X`, `D`) given `Cancer` provide **synergistic diagnostic evidence** when observed together.
- Observing both `X=1` and `D=1` sharply raises posterior `P(C=1)` vs observing either alone (evidence accumulation).
- Provides a clean example of how multiple findings combine probabilistically, not additively.


**Suggested Queries**:
 Prior vs posterior: `P(C=1)` then `P(C=1|X=1)`, `P(C=1|D=1)`, `P(C=1|X=1,D=1)`.
- Explaining away partial: condition on `C=1` then check dependence of `X` and `D`: `IsIndep(X,D)` vs `IsCondIndep(X,D|C)`.
- Influence of risk factors: `P(C=1|S=1)` vs `P(C=1|S=0)`; similarly for pollution states.
- Information gain: compare `entropy(C)` and `conditional_entropy(C|X)` and with both findings.

```bash
P(Cancer)                           # Prior cancer probability
P(Cancer|Xray=1,Dyspnea=1)         # Combined symptom evidence
P(Cancer|Smoker=1)                 # Smoking risk factor
P(Xray=1|Cancer=1)                 # Symptom sensitivity
```

#### 13. **Insurance Network** (`insurance_network_small.net`)
**Variables**: Age, SocioEcon, GoodStudent, MakeModel, CarValue, Antilock, Airbag, Accident, ThisCarDam, MedCost

**Key Insight**: Complex multi-layer dependencies modeling real-world insurance risk assessment.
- A simplified version of the well-known Insurance Bayesian network used in AI research for benchmarking inference algorithms.
- Models relationships between demographics (Age, SocioEcon), vehicle characteristics (MakeModel, CarValue, safety features), driving behavior, accidents, and insurance costs.
- Demonstrates complex multi-layer dependencies: demographics influence vehicle choices and student status, vehicle features affect accident probability, accidents determine damage and medical costs.
- Contains multiple types of relationships: causal chains, common causes, and converging evidence patterns.
- Useful for testing scalability with moderate-sized networks (2^10 = 1024 joint probability entries).


**Suggested Queries**:
- Demographics and costs: `P(MedCost=1|Age=0)` vs `P(MedCost=1|Age=1)` (young vs adult medical costs)
- Safety features effectiveness: `P(Accident=1|Antilock=1)` vs `P(Accident=1|Antilock=0)`
- Vehicle value impact: `P(ThisCarDam=1|CarValue=1,Accident=1)` vs `P(ThisCarDam=1|CarValue=0,Accident=1)`
- Independence checks: `IsIndep(Age,MakeModel)` vs `IsCondIndep(Accident,MedCost|Age)`

```bash
P(Accident|Age=0)                          # Young driver risk
P(MedCost|Accident=1,Age=0)               # Age-related medical costs
P(ThisCarDam|CarValue=1,Accident=1)       # Vehicle value impact
P(Accident|Antilock=1)                    # Safety feature effectiveness
```

### Network Exploration Tips

1. **Start with structure**: Use `marginals` to understand base rates
2. **Test independence**: Use `IsIndep()` and `IsCondIndep()` to validate structural assumptions
3. **Explore causality**: Compare `P(Effect|Cause)` with `P(Effect)`
4. **Evidence accumulation**: Combine multiple pieces of evidence in conditional queries
5. **Information analysis**: Use `entropy()` and `mutual_info()` to quantify relationships

---

## Advanced Usage

### Sampling

Generate random samples from the joint distribution for simulation studies:

```bash
sample()           # Single sample: (0, 1, 0)
sample(100)        # 100 samples for statistical analysis
sample(n=1000)     # Named parameter form
```

Applications:
- **Monte Carlo simulation**: Approximate complex probabilities
- **Bootstrap analysis**: Assess sampling variability
- **Validation**: Compare theoretical vs empirical distributions

### Precision Control

Control numerical display precision for probability outputs:

```bash
precision          # Show current setting (default: 4)
precision 6        # Set to 6 decimal places
precision 2        # Reduce to 2 decimal places for readability
```

Useful for:
- **Publication**: Consistent formatting across outputs
- **Analysis**: Higher precision for detecting small differences
- **Display**: Lower precision for cleaner presentation

### Epidemiological Measures

Specialized functions for medical and epidemiological analysis:

#### Odds Ratio
```bash
odds_ratio(Exposure,Outcome)
```

Calculates: **OR = (a×d)/(b×c)** from 2×2 contingency table

| | Outcome=1 | Outcome=0 |
|---|---|---|
| **Exposure=1** | a | b |
| **Exposure=0** | c | d |

#### Relative Risk
```bash
relative_risk(Exposure,Outcome)
```

Calculates: **RR = P(Outcome=1|Exposure=1) / P(Outcome=1|Exposure=0)**

Both measures return `'Undefined'` when denominators are zero.

**Example Application**:
```bash
# Load smoking-cancer data
open inputs/smoking_cancer.inp

# Calculate effect sizes
odds_ratio(Smoking,Cancer)        # Odds ratio
relative_risk(Smoking,Cancer)     # Relative risk

# Compare interpretations
P(Cancer|Smoking=1)              # Risk in exposed group
P(Cancer|Smoking=0)              # Risk in unexposed group
```

---

# APPENDIX B: Command Quick Reference

### Query Patterns
| Task | Example | Notes |
|------|---------|-------|
| Marginal | `P(A)` | P(A=1) |
| Joint | `P(A,B)` | P(A=1,B=1) |
| Conditional | `P(A\|B)` | P(A=1\|B=1) |
| Negation | `P(~A)` | P(A=0) |
| Explicit values | `P(A=0,B\|C=1)` | Mixed specifications |
| Independence | `IsIndep(A,B)` | Marginal independence |
| Conditional independence | `IsCondIndep(A,B\|C)` | All Z assignments |
| Arithmetic | `P(A)*P(B\|A)` | Chain rule |

### Information Theory
| Measure | Command | Interpretation |
|---------|---------|----------------|
| Entropy | `entropy(A)` | Uncertainty in A |
| Joint entropy | `entropy(A,B)` | Joint uncertainty |
| Conditional entropy | `cond_entropy(A\|B)` | Uncertainty in A given B |
| Mutual information | `mutual_info(A,B)` | Shared information |

### Workflow Commands
| Action | Command | Purpose |
|--------|---------|---------|
| Load file | `open filename.inp` | Switch distributions |
| List examples | `networks` | Browse available files |
| Show probabilities | `marginals` | Overview of distribution |
| Show joint table | `joint_table` | Complete enumeration |
| Show contingency table | `contingency_table` | Prints full contingency table up to four variables |
| Test all pairs | `independence` | Dependency structure |
| Save distribution | `save output.inp` | Export current state |
| Set precision | `precision 6` | Control display format |
| Draw samples | `sample(100)` | Monte Carlo simulation |


### Common Patterns
| Goal | Pattern |
|------|---------|
| Validate normalization | `P(A) + P(~A)` (expect 1.0) |
| Test Bayes' theorem | `P(A\|B) * P(B) / P(A)` vs `P(B\|A)` |
| Explaining away | Compare `P(Cause1\|Effect)` vs `P(Cause1\|Effect,Cause2)` |
| Information gain | `entropy(A)` vs `cond_entropy(A\|B)` |
| Sequential updating | Use arithmetic for posterior → prior transitions |

### Troubleshooting
| Issue | Solution |
|-------|---------|
| "File not found" | Check path, use `networks` to list available files |
| "Division by zero" | Conditioning variable has zero probability |
| "Variable not found" | Check spelling, variables are case-sensitive |
| Unexpected independence | Use `joint_table` to inspect probability distribution |
| Large output | Use `precision` to reduce decimal places |

This user guide provides comprehensive coverage of BayesCalc's capabilities for interactive Bayesian analysis. For additional technical details, see the Architecture documentation in `docs/ARCHITECTURE.md`.

# APPENDIX C: Classical Medical Test Example

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
