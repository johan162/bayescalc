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
10. [APPENDIX: Quick Reference](#quick-reference)

---

## Introduction

BayesCalc is an interactive command-line tool for exploring Bayesian probability distributions, conditional probabilities, and information-theoretic quantities. It supports both joint probability tables and Bayesian network specifications, making it useful for:

- **Educational exploration** of probabilistic reasoning
- **Research analysis** of dependency structures
- **Statistical modeling** validation and interpretation
- **Interactive learning** of Bayesian concepts

The system provides a natural query interface where you can ask questions like `P(Disease|Test)` or `IsIndep(A,B)` and get immediate numerical answers along with supporting analysis.

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
python probs.py inputs/medical_test.inp
```

### First Steps
Once launched, try these basic commands:
```
marginals           # View all marginal probabilities
P(Sickness|Test)     # Conditional probability query
IsIndep(A,B)         # Test independence
entropy             # Information content
help                # Show all commands
```

---

## File Formats

BayesCalc supports two primary input formats for defining probability distributions.

### Joint Probability Tables (.inp)

The `.inp` format specifies joint probability distributions directly through enumeration of all possible variable assignments.

#### Basic Structure
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
There is two variants of allowed input file

  1. For multi-valued variables (also works for Boolean)
  2. A simplified format for boolean variables (**does NOT** work for multi-values variables)

#### Variant 1 - Multi values variables

All cihld/parent states are explicitly specified. 

```txt
# Alarm network, variant 1 - Multi-values variable format
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

**Key Features:**
- **Variable Declaration**: Defines all variables in display order
- **Parent Specification**: Lists parents for each variable (or `None` for roots)
- **Conditional Tables**: Each pattern specifies P(Variable=1|Parents=pattern)
- **Complete Coverage**: Must specify probabilities for all parent combinations


#### Variant 2 - Boolean variables

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
> For boolean variable networks either style can be used


#### Example: Alarm Network with long variable names

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
> The child value is always implicitly assumed to be "True" using variant 2 (i.e. Boolean format)

### Multi-Valued Variables

BayesCalc also supports variables with more than two states (cardinality > 2), specified in the `.net` format using explicit state names.

#### Example: Weather Forecast
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

---

## Interactive CLI

The heart of BayesCalc is its interactive command-line interface that provides natural language queries for probabilistic reasoning.

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

The system uses numerical tolerance (default 1e-9) to account for floating-point precision when testing independence.

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

This approach is fundamental to machine learning, signal processing, and scientific inference.

---

## Example Walkthrough: Medical Testing

This comprehensive example demonstrates key concepts through a realistic medical testing scenario.

### Scenario Setup

Consider a medical test for a rare disease with the following characteristics:
- **Disease prevalence**: 1% in the population (base rate)
- **Test sensitivity**: 95% (detects disease when present)
- **Test specificity**: 94% (negative when disease absent)
- **False positive rate**: 6% (positive when disease absent)

### File Specification

Use the existing `inputs/medical_test.inp`:
```
variables: Sickness, Test
# P(Sickness=1) = 0.01, P(Test=1|Sickness=1) = 0.95, P(Test=1|Sickness=0) = 0.06

00: 0.930500  # P(Sickness=0, Test=0) = 0.99 × 0.94 = 0.9306
01: 0.059400  # P(Sickness=0, Test=1) = 0.99 × 0.06 = 0.0594  
10: 0.000500  # P(Sickness=1, Test=0) = 0.01 × 0.05 = 0.0005
11: 0.009500  # P(Sickness=1, Test=1) = 0.01 × 0.95 = 0.0095
```

### Interactive Analysis

Load the scenario and explore:
```bash
python probs.py inputs/medical_test.inp
```

#### Basic Probabilities
```bash
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

<!-- CLI_HELP_END -->

---

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
python probs.py inputs/sprinkler.net
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

**Key Insights**: 
- Fork at Cloudy: Sprinkler and Rain independent given Cloudy
- Collider at WetGrass: Sprinkler and Rain dependent given WetGrass

**Suggested Queries**:
```bash
IsCondIndep(Sprinkler,Rain|Cloudy)     # True (d-separated)
IsCondIndep(Sprinkler,Rain|WetGrass)   # False (collider)
P(Rain|WetGrass,Sprinkler=0)          # Explaining away
```

#### 4. **Explaining Away (Alarm)** (`explaining_away_alarm.net`)
**Variables**: Burglary, Earthquake, Alarm, JohnCalls, MaryCalls

**Key Insights**: Observing alarm makes burglary and earthquake dependent. Learning about one cause reduces belief in the other.

**Suggested Queries**:
```bash
P(Burglary|Alarm)                    # Diagnostic reasoning
P(Earthquake|Alarm,Burglary=1)       # Explaining away effect
P(Burglary|JohnCalls,MaryCalls)      # Evidence accumulation
```

### Statistical Phenomena

#### 5. **Berkson's Bias** (`berkson_bias.inp`)
**Variables**: Disease1, Disease2, Admission

**Key Insight**: Conditioning on a collider (hospital admission) induces spurious negative correlation between independent diseases.

**Suggested Queries**:
```bash
IsIndep(Disease1,Disease2)                    # Marginal independence
P(Disease1|Disease2=1,Admission=1)           # Induced dependence
P(Disease1|Disease2=0,Admission=1)           # Selection bias
```

#### 6. **Markov Chain** (`markov_chain4.inp`)
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

#### 7. **XOR Triplet** (`xor_triplet.inp`)
**Variables**: A, B, C (where C = A XOR B)

**Key Insight**: All pairwise independent but not mutually independent. Demonstrates limitation of pairwise analysis.

**Suggested Queries**:
```bash
IsIndep(A,C)            # True (pairwise independent)
IsIndep(B,C)            # True (pairwise independent)
P(C|A,B)                # Deterministic constraint
entropy(A,B,C)          # Less than H(A)+H(B)+H(C)
```

#### 8. **Higher-Order Dependence** (`parity5.inp`)
**Variables**: X1, X2, X3, X4, Parity (where Parity = X1⊕X2⊕X3⊕X4)

**Key Insight**: Low-order statistics miss high-order structure. Individual variables provide no information about parity, but all four together determine it.

**Suggested Queries**:
```bash
IsIndep(X1,Parity)              # True (no individual information)
mutual_info(X1,Parity)          # Zero mutual information
P(Parity|X1,X2,X3,X4)          # Deterministic given all
```

### Multi-Valued Networks

#### 9. **Weather Picnic** (`weather_picnic.net`)
**Variables**: Weather{Sunny,Cloudy,Rainy}, Forecast{Sunny,Cloudy,Rainy}, Picnic{Yes,No}

**Key Insight**: Multi-state variables with imperfect forecasting and decision-making under uncertainty.

**Suggested Queries**:
```bash
P(Weather=Rainy)                    # Prior weather probability
P(Picnic=Yes|Forecast=Sunny)        # Decision based on forecast
P(Weather=Sunny|Forecast=Sunny)     # Forecast reliability
```

#### 10. **Medical Diagnosis** (`medical_diagnosis_mini.net`)
**Variables**: Disease{None,Mild,Severe}, TestResult{Negative,WeakPos,StrongPos}, SymptomA{Absent,Mild,Strong}, SymptomB{Absent,Present}, Treatment{None,Basic,Aggressive}

**Key Insight**: Multi-stage diagnostic reasoning with severity levels and treatment decisions.

**Suggested Queries**:
```bash
P(Disease=Severe|TestResult=StrongPos)                  # Diagnostic accuracy
P(Treatment=Aggressive|Disease=Mild,SymptomA=Strong)    # Treatment decisions
P(Disease=Severe|SymptomA=Strong,SymptomB=Present)     # Symptom-based diagnosis
```

### Complex Networks

#### 11. **Cancer Network** (`cancer.net`)
**Variables**: Pollution, Smoker, Cancer, Xray, Dyspnea

**Structure**: Competing causes with multiple symptoms providing synergistic evidence.

**Key Insights**:
- Multiple risk factors (pollution, smoking) jointly influence cancer
- Independent symptoms (X-ray, dyspnea) provide additive diagnostic value

**Suggested Queries**:
```bash
P(Cancer)                           # Prior cancer probability
P(Cancer|Xray=1,Dyspnea=1)         # Combined symptom evidence
P(Cancer|Smoker=1)                 # Smoking risk factor
P(Xray=1|Cancer=1)                 # Symptom sensitivity
```

#### 12. **Insurance Network** (`insurance_network_small.net`)
**Variables**: Age, SocioEcon, GoodStudent, MakeModel, CarValue, Antilock, Airbag, Accident, ThisCarDam, MedCost

**Key Insight**: Complex multi-layer dependencies modeling real-world insurance risk assessment.

**Suggested Queries**:
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

## APPENDIX: Quick Reference

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