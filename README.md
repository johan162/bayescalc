# Bayesian Network Calculator

Interactive Bayesian network analysis for learning, teaching, and quick “back‑of‑the‑napkin” reasoning.


## Overview

BayesCalc is a bsic command‑line tool and Python library for exploring joint and conditional probabilities over Bayesian networks. Load a model, ask questions like `P(Disease|Test)` or `IsCondIndep(A,B|C)`, and get immediate numerical answers. Use it interactively, via CLI batch commands, or as a library.
In terms of system size there is no hard upper limit but in practice given the speed of Python and the naive implementation (it calcuates the full JPT and does not employ more advanced techniques such as  Gibbs sampling) there is a practical limit with around ~10-15 variables for Boolean systems and 7-10 variables for multi-valued networks depending on the specific cardinality.

This is primarily a basic tool for learning and teaching and in that context the practical size limitations are not a problem.

Quick links:
| Doc | Description |
|-----|-------------|
| **[User Guide](docs/Userguide.md)**  | Tutorial and reference |
| **[ Developer Guide](docs/DEVELOPER_GUIDE.md)** |  Organization of code and how to add features |
| **[ Technical Details](docs/ARCHITECTURE.md)** | Implementation specifics and architecture |
| **[ Contributing](CONTRIBUTING.md)** | How to contribute |
| | |


## License

MIT License. See [LICENSE](LICENSE) file.


## Features

- Interactive *Read-Eval-Print-Loop* (REPL) with tab completion for commands, variable names, and variable values
- Supports standard mathematical notations, e.g expressions such as "`P(A|B,C) * P(B|C )* P(C)`" or "`P(~A)`"
- Multi‑valued variables and boolean variables (with `~`/`Not()` negation)
- Two file input formats:
  - `.net`: readable Bayesian network specific with Conditional Probability Tables (CPT), supports variables with cardinality > 2
  - `.inp`: explicit joint probability tables (JPT), only supports variables with cardinality=2 (boolean)
- Built‑in analyses: marginals, joints, conditionals, independence tests, entropy, mutual information, etc.
- Pretty tables: `marginals`, `cond_probs(i,j)`, `list`, `networks`, etc.

## Installation

- Python 3.7+
- Recommended: Python 3.13+

Unpack the *.tar.gz file into a directory. The program requires no specific installation or dependencies to run. 


## Quick Start

Load the classical counterintuitive medical test example. The test is for a disease that 1% of the population has, (i.e. `P(Sickness) = 0.01`, (also known as the prevalence)

The test have:
- 95% sensitivity = probabiity that it detects a disease when the disese is present, i.e. `P(Test|Sickness) = 0.95` (true positive)
- 94% specificity, i.e. 100-94=6% probability that it gives a false positive when the disease is absent, i.e. `P(Test|~Sickness) = 0.06` (false positive)

Then the question is; If you get a test result that indicates you have the disease, what is the probability that you actually have the disease? A common (but wrong!) answer is "95%".


```bash
python bayescalc.py inputs/medical_test.inp
# Try:
P(Sickness|Test)
marginals
networks net
```

Tip: Use `--cmds` for batch mode, e.g.:
```bash
python bayescalc.py inputs/medical_test.inp --cmds "P(Sickness|Test);marginals;exit"
```

## Command Line Usage (Quick Reference)

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
  python bayescalc.py    # interactive (manual input prompt)
  python bayescalc.py inputs/medical_test.inp
  python bayescalc.py inputs/medical_test.inp --names Sickness Test
    python bayescalc.py --help
```

Non-interactive batch example (run specified commands then quit):
```bash
  python bayescalc.py inputs/medical_test.inp --cmds "P(Sickness|Test);odds_ratio(Sickness,Test);exit"
```



## Example networks

Run `networks` (or `networks net` / `networks inp`) to list all included models with descriptions. 

In the current version around 20 example networks are included

```bash
  python bayescalc.py inputs/medical_test.inp --cmds "networks;exit"
```

A few highlights:
- Sprinkler (net): classic Cloudy→{Sprinkler,Rain}→WetGrass
- Student performance (net): multi‑valued; Intelligence & Difficulty → Grade → Letter
- Weather picnic (net): multi‑valued; Weather & Forecast → Picnic
- Medical test (inp): rare disease screening with imperfect sensitivity/specificity
- Burglury, Earthquake, Alarm (inp/net) network, boolean network common in course materials


### A note on performance

The tool enumerates the full joint distribution. Boolean models scale as `2^N`; multi‑valued models scale by the product of state counts. 
Practical range: ~7–10 variables depending on cardinalities. Pure boolean variables scale up to ~15 variables.


## Usage Examples

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

### Typical commands and expressions

Some final examples will give a sense of what can be calculated (this is not an exhaustive list)

1. `P(A)` — Marginal probability that variable `A` equals 1.
2. `P(~A)` or `P(Not(A))` — Marginal probability that `A` equals 0 (negation supported with `~`).
3. `P(A,B)` — Joint probability that `A=1` and `B=1`.
4. `P(A=0,B=1)` — Joint probability using explicit value notation.
5. `P(A|B)` — Conditional probability P(A=1 | B=1).
6. `P(A,B|C)` — Joint probability of `A` and `B` given `C` (conditional joint).
7. `IsIndep(A,B)` — Test whether `A` and `B` are independent.
8. `IsCondIndep(A,B|C)` — Test conditional independence given `C`.
9. `P(A) + P(B)` — Arithmetic on probability values.
10. `P(A) * P(B|C) / P(D)` — Mixed arithmetic with conditional and marginal probabilities.
11. `P(~A) + P(B|~C)` — Combine negation and conditional queries in arithmetic expressions.
12. `cond_probs(1,2)` - Print a table of all possible combinations of `P(X1=x1|X2=x2,X3=x3)`
13. `marginals` - Print a table of all marginal probabilitites
14. `contingency_table` - Print the contigency table (supports up to four variables)