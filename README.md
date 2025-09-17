# Bayesian Network Calculator

Interactive Bayesian network analysis primarily developed for education (may also find some limited use in research as a quick back-of-the-napkin kind of calculations).

## Overview

BayesCalc is a command-line tool for exploring Bayesian probability distributions and conditional reasoning. 
Define probability models and ask natural language questions like `P(Disease|Test)` or `IsIndep(A,B)` to get 
immediate numerical answers. It can be used both interactively, as a library with a public API, or in batch mode.

The command examples below will give a sense of what can be calculated and what type of expression are supported 
(this is not an exhaustive list, see the user guide for a complete list of available commands)

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
14. `networks` - List all included Bayesian networks
15. `list` - List all variables and theire states

Notes:
- Variable names may be single letters (`A`,`B`,...) or custom names specified in input files (`Rain`, `Sickness`, ...).
- Whitespace and simple parentheses are supported inside `P(...)` queries. Use `~` as a concise negation operator or `Not(...)` for clarity.


## Quick Start

The scipt provides both public APIs (for use in other scripts) as well as a CLI interface for interactive experiments. The public API is documented in the user guide.
The main entry point is `probs.py` and the easiest way to get started is to use the calculator interactively with and one of the included examples. 

As quick example using the included medical test data will help to understand the capabilities of the calculator:


```txt
> python probs.py inputs/medical_test.inp 
Successfully loaded probability system from file: inputs/medical_test.inp
Using variable names: Sickness, Test

Joint Probability Table:
========================

Sickness | Test | Probability
-----------------------------
0        | 0    | 0.930600
0        | 1    | 0.059400
1        | 0    | 0.000500
1        | 1    | 0.009500

Tab completion enabled. Type the first few letters of a variable name and press Tab to complete it. 

Example Queries:
Examples: P(Sickness), P(Sickness,Test), P(Sickness|Test)
          IsIndep(Sickness,Test)
Type 'help' to see available commands, 'quit' (or 'exit') to exit.


Query: P(Sickness|Test)
--> 0.1379

Query: IsIndep(Sickness,Test)  
--> False

Query: entropy(Sickness)
--> 0.0808

Query: exit

Thank you for using the Probability System. Goodbye!
```

Note: *Tab-completion*

For ease of use the calculator supports tab-completion of

- Variable names
- Variable values
- Commands
- File names (for loading and saving)


## Specifying the network (or model)

The network to be analyzed can either be specified interactively or perhaps more commonly read from a file that can be in either one of the two supported formats indicated by the file suffix.

- **`*.inp`** The first format is for usage with boolean variables only (binary enumeration), it is a specification of the of a joint probability table (JPT) (possibly sparse). The details of the format are described in the user guide. A number of example JPT input files are specified in `inputs/*.inp`.

- **`*.net`** The second format is for usage with a number of conditional probability tables (CPT) specifying a Bayesian network.  The Bayesian network format is often the simplest way to specify the system as it allows the same information to be specified as the JPT but in a much more conscise format. The details of the format are described in the user guide. A number of example networks are specified in `inputs/*.net`.

A complete list and explanation of all example networks can be found in the user guide.

### A note on performance

Internally all input methods will calculate the joint distribution table of size 2^N for boolean variables (binary enumeration) where N is the number of variables. In terms of performance the system can work with networks up to 18-20 boolean variables on a 8GB RAM computer. 

Anything above 20 variables is not practical as for the minimum case of boolean variables it will create a JPT with roughly one million entries and for multi-valued variables it will be grow combinatorically. For example, assuming each variable have four states then the 20 variable system would have a multiplicative factor of one million more rows, i.e. the total would be 1,000,000,000,000 rows which is clearly not a tractable size of a python script regardless of available memory. The calculator is primarily targeting systems with a maximum of 7 - 10 variables.


## Command Line Usage Quick Reference

You can see these options anytime with `python probs.py --help` (or by supplying a file then `--help`). 

```txt
usage: probs.py [-h] [--names NAMES [NAMES ...]] [--cmds CMDS] [file]

Positional arguments:
  file                  Optional path to a input file (.inp or .net). If omitted  you'll be prompted 
                        or can explore interactively.

Optional arguments:
  -h, --help            Show help and exit.
  --names, -n           One or more custom variable names to apply when loading a joint table (.inp). 
                        Provide space-separated names (must match variable count). 
                        Ignored for multi-valued .net that already declare variables.
  --cmds CMDS           Semicolon-separated list of commands to execute non-interactively after 
                        loading the file, then exit (unless a REPL-only command requires interaction). 
                        Example: --cmds "P(A);entropy;networks;exit".
```

Examples:

```bash
  python probs.py    # interactive (manual input prompt)
  python probs.py inputs/medical_test.inp
  python probs.py inputs/medical_test.inp --names Sickness Test
  python probs.py inputs/weather_picnic.net --cmds "P(Weather=Sunny);entropy;exit"
  python probs.py --help
```

Non-interactive batch example (run commands then quit):
```bash
  python probs.py inputs/medical_test.inp --cmds "P(Sickness|Test);odds_ratio(Sickness,Test);exit"
```

Tip: Use `--cmds` in scripts/CI to capture deterministic output without driving the REPL.


## Basic Usage Examples

**Load and explore a probability distribution:**
```bash
python probs.py inputs/sprinkler.net
> marginals                    # View all marginal probabilities
> P(Rain|WetGrass)             # Conditional probability
> IsCondIndep(Sprinkler,Rain|Cloudy)  # Test conditional independence
```

**Information theory analysis:**
```bash
> entropy()                    # Joint entropy of all variables
> mutual_info(Rain,Sprinkler)  # Shared information
> cond_entropy(Rain|WetGrass)  # Remaining uncertainty
```

**Explore classic probability paradoxes:**
```bash
python probs.py inputs/simpsons_paradox.inp    # Simpson's paradox
python probs.py inputs/monty_hall.inp          # Monty Hall problem
python probs.py inputs/berkson_bias.inp        # Selection bias
```

## Included example data

See `inputs/` directory for examples or run `networks` command to list all available networks/system.

Included Networks/Models:


|File                        | Vars | Description |
|----------------------------|------|-------------|
alarm_subset.net            |    5 | ALARM subset: ventilator machine/tube affect Press & CO2 which trigger Alarm; showcases cascading and converging medi...
berkson_bias.inp            |    3 | Berkson's Bias (Collider Bias) Example Variables: Disease1 (D1), Disease2 (D2), Admission (A) A patient is admitted (...
cancer.net                  |    5 | Cancer diagnosis BN: Pollution & Smoker influence Cancer which drives Xray and Dyspnea; dual findings combine for str...
explaining_away_alarm.inp   |    5 | Explaining-away alarm network: Burglary and Earthquake converge on Alarm; observing Alarm induces dependence and call...
explaining_away_alarm.net   |    5 | The standard example of a bayesian network with a Simplified Alarm Network This is the same as "explaining_away_alarm...
inp2.inp                    |    2 | (No description)
insurance_network.net       |   27 | Full insurance BN variant: richer demographic/vehicle factors cascading to accident, damage, and medical cost outcome...
insurance_network_small.net |   10 | Simplified insurance BN: demographics & car features influence accidents then damage & medical costs (medium-scale de...
markov_chain4.inp           |    4 | 4-node Markov chain A->B->C->D: endpoints marginally dependent yet conditionally separated via intermediates (classic...
medical_diagnosis_mini.net  |    5 | Medical diagnosis mini: staged Disease drives test & symptoms; Treatment depends on combined evidence (multi-valued d...
medical_test.inp            |    2 | Classic medical screening example: rare disease (1% prevalence) with 95% sensitivity and 94% specificity illustrating...
monty_hall.inp              |    2 | Monty Hall Problem (Simplified Boolean Representation) Classic puzzle: Three doors, one prize. Player picks a door. H...
parity5.inp                 |    5 | 5-Variable Parity Example Variables: X1, X2, X3, X4, Parity Parity = X1 XOR X2 XOR X3 XOR X4 (deterministic). Distrib...
simpsons_paradox.inp        |    3 | Simpson's Paradox: Treatment helps within each gender but looks harmful when genders are aggregated due to differing ...
sprinkler.net               |    4 | Classic Sprinkler network: Cloudy influences Sprinkler & Rain; both cause WetGrass (collider for explaining-away demo...
student_performance.net     |    5 | Student performance BN: Intelligence & Difficulty influence Prep and Grade; Grade drives Letter recommendation (multi...
traffic.net                 |    4 | Traffic delay network: RushHour and Accident raise Traffic which drives Late arrival; shows converging and downstream...
weather_picnic.net          |    3 | Weather-Picnic BN: Weather influences Forecast; both affect Picnic decision (showing multi-valued causal + decision i...
xor_triplet.inp             |    3 | XOR Triplet Example (A, B, C) where C = A XOR B. Interesting because: A and B are independent; A and C are independen...



## Documentation

- **[📖 User Guide](docs/Userguide.md)** - Complete tutorial and reference
- **[🔧 Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and contributing
- **[🏗️ Technical Details](docs/ARCHITECTURE.md)** - Implementation specifics


## Requirements

- Tested with `Python 3.13+`

