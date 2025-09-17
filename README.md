# Bayesian Network Calculator

Interactive Bayesian network analysis for learning, teaching, and quick “back‑of‑the‑napkin” reasoning.


## Overview

BayesCalc is a command‑line tool and Python library for exploring joint and conditional probabilities over Bayesian networks. Load a model, ask questions like `P(Disease|Test)` or `IsCondIndep(A,B|C)`, and get immediate answers. Use it interactively, via CLI batch commands, or as a library.

Quick links:
| Doc | Description |
|-----|-------------|
| **[User Guide](docs/Userguide.md)**  | Complete tutorial and reference |
| **[ Developer Guide](docs/DEVELOPER_GUIDE.md)** |  Organization of code and how to add features |
| **[ Technical Details](docs/ARCHITECTURE.md)** | Implementation specifics and architecture |
| **[ Contributing](CONTRIBUTING.md)** | How to contribute |
| | |


## License

MIT License. See [LICENSE](LICENSE) file.


## Features

- Interactive REPL with tab completion for commands, variable names, and variable values
- Multi‑valued variables and boolean variables (with `~`/`Not()` negation)
- Two input formats:
  - `.net`: readable Bayesian network CPTs (multi‑valued)
  - `.inp`: explicit joint probability tables (boolean)
- Built‑in analyses: marginals, joints, conditionals, independence tests, entropy, mutual information
- Pretty tables: `marginals`, `cond_probs(i,j)`, `list`, `networks`, etc.

## Installation

- Python 3.7+
- Recommended: Python 3.13+
  - macOS
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt` (or `pip install -e .` if provided)

## Quick Start

```bash
python probs.py inputs/medical_test.inp
# Try:
P(Sickness|Test)
marginals
networks net
```

Tip: Use `--cmds` for batch mode, e.g.:
```bash
python probs.py inputs/medical_test.inp --cmds "P(Sickness|Test);marginals;exit"
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

# File input formats

- `.inp` (boolean JPT): explicit joint table; concise for small boolean systems
- `.net` (CPT network): human‑readable BN with parent links and per‑state CPT rows; supports multi‑valued variables

A complete list and explanation of all example networks can be found in the user guide.


## Example networks

Run `networks` (or `networks net` / `networks inp`) to list all included models with descriptions. A few highlights:
- Sprinkler (net): classic Cloudy→{Sprinkler,Rain}→WetGrass
- Student performance (net): multi‑valued; Intelligence & Difficulty → Grade → Letter
- Weather picnic (net): multi‑valued; Weather & Forecast → Picnic
- Medical test (inp): rare disease screening with imperfect sensitivity/specificity

### A note on performance

The tool enumerates the full joint distribution. Boolean models scale as `2^N`; multi‑valued models scale by the product of state counts. Practical range: ~7–10 variables depending on cardinalities.


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
