# BayesCalc

Interactive Bayesian probability analysis for education and research.

## What is BayesCalc?

BayesCalc is a command-line tool for exploring Bayesian probability distributions and conditional reasoning. Define probability models and ask natural language questions like `P(Disease|Test)` or `IsIndep(A,B)` to get immediate numerical answers.

**Purpose:** Educational exploration of probabilistic reasoning, Bayesian inference, and information theory concepts through hands-on experimentation.

## Quick Start

```bash
# Install
pip install -r requirements-dev.txt

# Run with example
python probs.py inputs/medical_test.inp

# Try basic queries
> P(Sickness|Test)
0.1379
> IsIndep(Sickness,Test)  
False
> entropy(Sickness)
0.0808
```

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

## Input Formats

- **`.inp` files**: Joint probability tables (binary enumeration)
- **`.net` files**: Bayesian networks (conditional probability tables)
- **Multi-valued**: Support for variables with >2 states

See `inputs/` directory for examples or run `networks` command to list available models.

## Documentation

- **[📖 User Guide](docs/Userguide.md)** - Complete tutorial and reference
- **[🔧 Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and contributing
- **[🏗️ Technical Details](docs/ARCHITECTURE.md)** - Implementation specifics

## Requirements

- Python 3.7+
- Dependencies: `click`, `pytest`
