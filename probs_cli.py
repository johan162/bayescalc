#!/usr/bin/env python3
"""
CLI and interactive utilities for the ProbabilitySystem.
"""

import sys
import re
from typing import List
from probs_core import ProbabilitySystem
from probs_core import ui as probs_ui
import tempfile
import os

# Module-level flag to ensure the goodbye message is emitted exactly once even
# if multiple exit paths are taken (e.g., REPL exit vs. higher-level fallback).
_GOODBYE_EMITTED = False


def _print_goodbye_once():
    """Print the goodbye message once (idempotent)."""
    global _GOODBYE_EMITTED
    if _GOODBYE_EMITTED:
        return
    print("\nThank you for using the Probability System. Goodbye!")
    try:
        sys.stdout.flush()
    except Exception:
        pass
    _GOODBYE_EMITTED = True


# Structured command descriptor used to generate help text programmatically.
# Each entry contains: 'cmd' (short name or usage), 'summary', and optional 'examples'.
COMMANDS = [
    {
        "cmd": "help",
        "summary": "Show this help message with all commands",
    },
    {"cmd": "marginals", "summary": "Print all marginal probabilities"},
    {
        "cmd": "joint_probs",
        "summary": "Print joint probability table (first 64 rows)",
    },
    {
        "cmd": "joint_table",
        "summary": "Print complete joint probability table (all rows)",
    },
    {
        "cmd": "table",
        "summary": "Alias for joint_table (print complete joint probability table)",
    },
    {"cmd": "independence", "summary": "Print independence table for all pairs"},
    {
        "cmd": "cond_independence",
        "summary": "Print conditional independence table for all triples",
    },
    {
        "cmd": "cond_probs(n,m)",
        "summary": "Print conditional probabilities for n-tuples given m-tuples",
        "params": [
            {"name": "n", "desc": "size of target tuple (int)"},
            {"name": "m", "desc": "size of condition tuple (int)"},
        ],
        "examples": ["cond_probs(1,1)"]
    },
        {
            "cmd": "precision <n>",
            "summary": "Set probability display precision (0-12). Type 'precision' alone to show current precision.",
        },
    {
        "cmd": "entropy [vars] [base=<b>]",
        "summary": "Compute Shannon entropy. No args -> full joint.",
        "params": [
            {"name": "vars", "desc": "optional comma-separated variable list (e.g. A,B)"},
            {"name": "base", "desc": "optional logarithm base (float, default 2.0)"},
        ],
        "examples": ["entropy", "entropy(A)", "entropy(A,B base=10)"]
    },
    {
        "cmd": "cond_entropy(A|B) [base=<b>]",
        "summary": "Conditional entropy H(A|B)",
        "params": [
            {"name": "A", "desc": "target variable(s) (comma-separated)"},
            {"name": "B", "desc": "conditioning variable(s) (comma-separated)"},
            {"name": "base", "desc": "optional logarithm base (float, default 2.0)"},
        ],
        "examples": ["cond_entropy(A|B)"]
    },
    {
        "cmd": "mutual_info(A,B) [base=<b>]",
        "summary": "Mutual information I(A;B)",
        "params": [
            {"name": "A", "desc": "first variable"},
            {"name": "B", "desc": "second variable"},
            {"name": "base", "desc": "optional logarithm base (float, default 2.0)"},
        ],
        "examples": ["mutual_info(A,B)"]
    },
    {"cmd": "odds_ratio(A,B)", "summary": "Odds ratio for exposure and outcome (returns 'Undefined' if not computable)"},
    {"cmd": "relative_risk(A,B)", "summary": "Relative risk (risk ratio) for exposure and outcome (returns 'Undefined' if not computable)"},
    {"cmd": "sample(n=1)", "summary": "Draw n samples from the joint distribution (returns list of tuples)"},
    {"cmd": "save <filename>", "summary": "Save probabilities to a file"},
    {"cmd": "open <filename>", "summary": "Open a .inp or .net file and replace current system"},
    {"cmd": "networks", "summary": "List available network input files with brief descriptions"},
    {"cmd": "list", "summary": "List all variables and their possible state values"},
    {"cmd": "quit | exit", "summary": "Exit the program"},
]



def _print_joint_table(prob_system: ProbabilitySystem):
    if hasattr(prob_system, "pretty_print_joint_table"):
        prob_system.pretty_print_joint_table()
    else:
        probs_ui.pretty_print_joint_table(prob_system.variable_names, prob_system.joint_probabilities)


def _print_joint_table_full(prob_system: ProbabilitySystem):
    """Print the full joint probability table without row limits."""
    if hasattr(prob_system, "pretty_print_joint_table_full"):
        prob_system.pretty_print_joint_table_full()
    else:
        probs_ui.pretty_print_joint_table_full(prob_system.variable_names, prob_system.joint_probabilities)


def _print_marginals(prob_system: ProbabilitySystem):
    if hasattr(prob_system, "pretty_print_marginals"):
        prob_system.pretty_print_marginals()
    else:
        probs_ui.pretty_print_marginals(prob_system.variable_names, prob_system.joint_probabilities, prob_system.get_marginal_probability)


def _print_independence_table(prob_system: ProbabilitySystem):
    if hasattr(prob_system, "pretty_print_independence_table"):
        prob_system.pretty_print_independence_table()
    else:
        probs_ui.pretty_print_independence_table(prob_system.variable_names, prob_system.num_variables, prob_system.is_independent)


def _print_conditional_independence_table(prob_system: ProbabilitySystem):
    if hasattr(prob_system, "pretty_print_conditional_independence_table"):
        prob_system.pretty_print_conditional_independence_table()
    else:
        probs_ui.pretty_print_conditional_independence_table(prob_system.variable_names, prob_system.num_variables, prob_system.is_conditionally_independent)


def _print_conditional_probabilities(prob_system: ProbabilitySystem, n: int, m: int):
    if hasattr(prob_system, "pretty_print_conditional_probabilities"):
        prob_system.pretty_print_conditional_probabilities(n, m)
    else:
        probs_ui.pretty_print_conditional_probabilities(prob_system.variable_names, prob_system.num_variables, prob_system.get_conditional_probability, n, m)


def _read_single_char():
    """Read a single character from stdin in raw mode.

    This helper temporarily places the terminal into raw mode to read one
    character. If the user types Ctrl-C while in raw mode this function
    raises KeyboardInterrupt so callers can handle interrupts consistently.
    """
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # Allow Ctrl-C to be delivered as KeyboardInterrupt even in raw mode
        if ch == "\x03":
            raise KeyboardInterrupt()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
def _completion_candidates(buffer: str, cursor_pos: int, variable_names: List[str], variable_states_map=None):
    """Return (candidates, word_start, stripped_current, function_like_set).

    Pure helper: computes completion candidates and context information.

    Returns a tuple of:
      - candidates: ordered list of completion strings
      - word_start: integer index in the buffer where the current word begins
      - stripped_current: the current word with any leading negation markers removed
      - function_like_set: set of tokens that should be treated as functions
        (i.e. when inserted they should append a '(' ).
    """

    # Find start of current word
    current_word = ""
    word_start = 0
    for i in range(cursor_pos - 1, -1, -1):
        if buffer[i] in " ,()=|":
            word_start = i + 1
            break
        current_word = buffer[i] + current_word

    stripped_current = current_word.lstrip("~")

    # Function-like tokens (completions that should append '(' when selected)
    function_like = set(["P", "IsIndep", "IsCondIndep", "Not", "entropy", "cond_entropy", "mutual_info"])

    # If we are inside parentheses of a known function, suggest variable names
    suggest_variables = False
    # look backwards to see if immediately preceded by '(' which itself is after a function name
    idx = word_start - 1
    while idx >= 0 and buffer[idx].isspace():
        idx -= 1
    if idx >= 0 and buffer[idx] == "(":
        # find token before '('
        j = idx - 1
        token = ""
        while j >= 0 and buffer[j] not in " ,()=|":
            token = buffer[j] + token
            j -= 1
        if token in function_like:
            suggest_variables = True

    # Assignment value completion: detect pattern VarName=PartialState and suggest state names
    if variable_states_map is not None:
        # Scan backwards for '=' that starts the current token value context.
        eq_idx = -1
        i = cursor_pos - 1
        # Stop scanning if we hit a delimiter that would end variable name region
        delimiters = set(" ,()|")
        while i >= 0:
            ch = buffer[i]
            if ch == '=':
                eq_idx = i
                break
            if ch in delimiters:\
                # Hit a delimiter before an '=', so not in an assignment value
                break
            i -= 1
        if eq_idx != -1:
            # Extract variable name left of '='
            j = eq_idx - 1
            while j >= 0 and buffer[j] not in delimiters and buffer[j] != '=':
                j -= 1
            var_name = buffer[j+1:eq_idx].strip()
            if var_name in (variable_states_map.keys() if hasattr(variable_states_map, 'keys') else []):
                # Suggest states for this variable
                state_candidates = list(variable_states_map[var_name])
                # Provide completion only of states (no function-like semantics)
                return (state_candidates, word_start, stripped_current, function_like)

    if suggest_variables:
        return (list(variable_names), word_start, stripped_current, function_like)

    # File completion for 'open ' prefix
    before_text = buffer[:word_start]
    open_prefix = buffer[:word_start].lstrip()
    if open_prefix.startswith('open '):
        import os
        partial = buffer[word_start:cursor_pos]
        # Determine directory portion if any
        dir_part, partial_name = os.path.split(partial)
        search_dir = dir_part if dir_part else '.'
        try:
            entries = os.listdir(search_dir)
        except Exception:
            entries = []
        cand_files = []
        for name in entries:
            full_path = os.path.join(search_dir, name)
            if os.path.isdir(full_path):
                # allow directory continuation if it matches partial
                if name.startswith(partial_name):
                    cand_files.append(os.path.join(dir_part, name) + '/')
            else:
                if name.startswith(partial_name) and (name.endswith('.inp') or name.endswith('.net')):
                    cand_files.append(os.path.join(dir_part, name) if dir_part else name)
        # Sort with directories first then files
        cand_files.sort()
        return (cand_files, word_start, stripped_current, function_like)

    # Build general candidates: variables plus commands and common function tokens if at line start
    candidates = list(variable_names)
    before = buffer[:word_start]
    at_start = before.strip() == ""
    if at_start:
        for ent in COMMANDS:
            token = ent["cmd"].split()[0]
            token = token.split("|")[0]
            token = token.split("(")[0]
            candidates.append(token)
        for fn in function_like:
            candidates.append(fn)

    # dedupe preserving order
    seen = set()
    norm = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            norm.append(c)

    return (norm, word_start, stripped_current, function_like)


def tab_complete_input(prompt, variable_names: List[str], variable_states_map=None):
    """Prompt for a line from the user with simple tab-completion.

    This is a small line-editor that supports backspace, left/right arrows
    and Tab-based completion using the project's variable names and common
    command/function tokens. It's intentionally lightweight so it can be
    exercised from unit tests by calling the completion helper directly.

    Args:
      prompt: prompt string to display (no trailing newline will be printed).
      variable_names: list of variable names used for completing expressions.

    Returns:
      The full input line entered by the user as a Python string.
    """

    # If stdin is *not* a TTY (e.g., under a PTY test harness writing bytes programmatically),
    # fall back to the built-in input() which will correctly read the full line.
    # This ensures automated tests that feed entire lines (rather than interactive keystrokes)
    # still exercise the REPL logic without needing to emulate character-level events.
    try:
        if not sys.stdin.isatty():
            # Use standard input path; this will still display the prompt text.
            return input(prompt)
    except Exception:
        # If isatty() check fails for any reason, continue with manual editor.
        pass

    print(prompt, end="", flush=True)

    buffer = ""
    cursor_pos = 0

    while True:
        char = _read_single_char()

        # Enter/Return -> finish
        if char == "\r" or char == "\n":
            print()
            return buffer

        # Tab -> completion
        if char == "\t":
            candidates, word_start, stripped_current, function_like = _completion_candidates(buffer, cursor_pos, variable_names, variable_states_map)

            if not candidates:
                print("\a", end="", flush=True)
                continue

            matches = [c for c in candidates if c.lower().startswith(stripped_current.lower())]
            if not matches:
                print("\a", end="", flush=True)
                continue

            if len(matches) == 1:
                match = matches[0]
                if match in function_like:
                    completion = match[len(stripped_current) :] + "("
                else:
                    completion = match[len(stripped_current) :]
                buffer = buffer[:cursor_pos] + completion + buffer[cursor_pos:]
                cursor_pos += len(completion)
                print(completion, end="", flush=True)
            else:
                # multiple matches: show common prefix and list
                common_prefix = matches[0]
                for m in matches[1:]:
                    i = 0
                    while i < len(common_prefix) and i < len(m) and common_prefix[i].lower() == m[i].lower():
                        i += 1
                    common_prefix = common_prefix[:i]

                if len(common_prefix) > len(stripped_current):
                    completion = common_prefix[len(stripped_current) :]
                    buffer = buffer[:cursor_pos] + completion + buffer[cursor_pos:]
                    cursor_pos += len(completion)
                    print(completion, end="", flush=True)

                print()
                print("Matches:")
                for m in matches:
                    display = m + ("(" if m in function_like else "")
                    print("  " + display)
                print(prompt + buffer, end="", flush=True)

        # Backspace/Delete
        elif char == "\x7f" or char == "\b":
            if cursor_pos > 0:
                buffer = buffer[: cursor_pos - 1] + buffer[cursor_pos:]
                cursor_pos -= 1
                # visually remove char and redraw rest
                rest = buffer[cursor_pos:]
                print("\b \b", end="", flush=True)
                if rest:
                    print(rest + ("\x1b[{}D".format(len(rest))), end="", flush=True)

        # Escape sequences (arrows)
        elif char == "\x1b":
            try:
                next_char = _read_single_char()
                if next_char == "[":
                    direction = _read_single_char()
                    if direction == "C":  # right
                        if cursor_pos < len(buffer):
                            print("\x1b[C", end="", flush=True)
                            cursor_pos += 1
                    elif direction == "D":  # left
                        if cursor_pos > 0:
                            print("\x1b[D", end="", flush=True)
                            cursor_pos -= 1
            except Exception:
                pass

        # Printable characters
        elif 32 <= ord(char) <= 126:
            buffer = buffer[:cursor_pos] + char + buffer[cursor_pos:]
            # print the inserted char and the remainder, then move cursor back over remainder
            rest = buffer[cursor_pos + 1 :]
            print(char + rest, end="", flush=True)
            if rest:
                print("\x1b[{}D".format(len(rest)), end="", flush=True)
            cursor_pos += 1

        elif char == "\x7f" or char == "\b":
            if cursor_pos > 0:
                buffer = buffer[: cursor_pos - 1] + buffer[cursor_pos:]
                cursor_pos -= 1
                print("\b \b", end="", flush=True)

        elif char == "\x1b":
            try:
                next_char = _read_single_char()
                if next_char == "[":
                    direction = _read_single_char()
            except:
                pass

        elif ord(char) >= 32 and ord(char) <= 126:
            buffer = buffer[:cursor_pos] + char + buffer[cursor_pos:]
            cursor_pos += 1
            print(char, end="", flush=True)


def print_help():
    """Print a concise help message describing available CLI commands.

    This uses the `COMMANDS` table to generate aligned usage lines and
    includes a few curated examples demonstrating probability and
    information-theory queries.
    """

    print("\nAvailable commands:")
    # determine max cmd width for alignment
    max_width = max(len(e["cmd"]) for e in COMMANDS)
    for ent in COMMANDS:
        cmd = ent["cmd"]
        summary = ent.get("summary", "")
        print(f"  {cmd.ljust(max_width)}  - {summary}")

    # Print examples grouped for CLI queries
    print("\nExamples:")
    print("  Typical probability queries:")
    print("    P(A), P(A,B|C), IsIndep(A,B), IsCondIndep(A,B|C)")
    print("  Arithmetic expressions using probabilities:")
    print("    P(A) + P(B|C) * 2")
    print("  Entropy / information examples:")
    print("    entropy, entropy(A), entropy(A,B base=10), cond_entropy(A|B), mutual_info(A,B)")
    print("  Epidemiology / sampling examples:")
    print("    odds_ratio(A,B), relative_risk(A,B), sample(5)")


def print_examples_with_variable_names(prob_system: ProbabilitySystem):
    """Print example queries using the current probability system's variable names.

    This helps new users by showing realistic `P(...)` and independence queries
    that use the actual variable names configured in the loaded probability table.
    """

    print("\nExample Queries:")
    examples = []
    if prob_system.num_variables >= 1:
        examples.append(f"P({prob_system.variable_names[0]})")
    if prob_system.num_variables >= 2:
        examples.append(
            f"P({prob_system.variable_names[0]},{prob_system.variable_names[1]})"
        )
        examples.append(
            f"P({prob_system.variable_names[0]}|{prob_system.variable_names[1]})"
        )
        examples.append(
            f"IsIndep({prob_system.variable_names[0]},{prob_system.variable_names[1]})"
        )
    if prob_system.num_variables >= 3:
        examples.append(
            f"IsCondIndep({prob_system.variable_names[0]},{prob_system.variable_names[1]}|{prob_system.variable_names[2]})"
        )

    print("Examples:", ", ".join(examples[:3]))
    if len(examples) > 3:
        print("          " + ", ".join(examples[3:]))


def run_interactive_loop(prob_system: ProbabilitySystem):
    """Run the REPL loop for the provided ProbabilitySystem.

    This function handles prompting, tab-completion, and dispatching the
    entered query string to `execute_command`. It intentionally does not
    attempt to parse or evaluate queries itself so tests can exercise the
    command execution logic via `execute_command` directly.
    """

    print(
        "\nTab completion enabled. Type the first few letters of a variable name and press Tab to complete it."
    )

    print_examples_with_variable_names(prob_system)

    print("Type 'help' to see available commands, 'quit' (or 'exit') to exit.")

    while True:
        try:
            # Build variable->states mapping for value completion
            states_map = {name: prob_system.variable_states[i] for i, name in enumerate(prob_system.variable_names)} if hasattr(prob_system, 'variable_states') else {name: ['0','1'] for name in prob_system.variable_names}
            query = tab_complete_input("\nQuery: ", prob_system.variable_names, states_map)
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting gracefully.")
            sys.exit(0)

        try:
            output = execute_command(prob_system, query)
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting gracefully.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            continue

        if output is None:
            # Silent action that is not exit.
            continue
        if output == "__EXIT__":
            _print_goodbye_once()
            return
        else:
            # Normal returned value: print it appropriately
            if isinstance(output, bool):
                print(f"--> {output}")
            elif isinstance(output, float):
                from probs_core.formatting import fmt
                print(f"--> {fmt(output)}")
            else:
                # String or other printable output
                print(output)

    # Normal loop termination (should be rare unless break used without exit/quit)
    _print_goodbye_once()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Probability System for probabilistic statistics calculations."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Optional path to a file containing joint probabilities. If not provided, you will be prompted for manual input.",
    )
    parser.add_argument(
        "--names",
        "-n",
        nargs="+",
        help="Optional custom variable names to use with the input file. Specify names separated by spaces.",
    )
    parser.add_argument(
        "--cmds",
        help="Optional semicolon-separated list of commands to execute non-interactively after loading the file (e.g. --cmds 'P(A);P(B|A);exit').",
    )

    args = parser.parse_args()

    if args.file:
        try:
            variable_names = args.names if args.names else None
            prob_system = ProbabilitySystem.from_file(args.file, variable_names)
            print(f"Successfully loaded probability system from file: {args.file}")
            print(f"Using variable names: {', '.join(prob_system.variable_names)}")
            # Use wrapper to print joint table (handles older/newer ProbabilitySystem variants)
            _print_joint_table(prob_system)
            # If --cmds provided, execute them sequentially (split on ';')
            if args.cmds:
                commands = [c.strip() for c in args.cmds.split(';') if c.strip()]
                for cmd in commands:
                    out = execute_command(prob_system, cmd)
                    if out == "__EXIT__":
                        _print_goodbye_once()
                        return
                    if out is None:
                        continue
                    if isinstance(out, bool):
                        print(f"--> {out}")
                    elif isinstance(out, float):
                        from probs_core.formatting import fmt
                        print(f"--> {fmt(out)}")
                    else:
                        print(out)
                # If no explicit exit encountered, print goodbye and return
                _print_goodbye_once()
                return
            # If stdin is not a TTY (e.g., running under CI/test) and no --cmds, avoid REPL
            if not sys.stdin.isatty():
                print("Non-interactive stdin detected; skipping REPL (no --cmds provided).")
                return
            run_interactive_loop(prob_system)
            _print_goodbye_once()
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)
    else:
        # Fallback interactive/manual input flow
        print("Welcome to the Probability System!")
        try:
            resp = input("Enter path to a probability file, or press Enter to input probabilities manually: ").strip()
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            sys.exit(0)

        if resp:
            try:
                prob_system = ProbabilitySystem.from_file(resp, args.names if args.names else None)
                _print_joint_table(prob_system)
                run_interactive_loop(prob_system)
                _print_goodbye_once()
                return
            except Exception as e:
                print(f"Error loading file: {e}")
                sys.exit(1)

        # Manual input mode: accept lines in the same format as input files
        print("Enter joint-probability lines (e.g. 'variables: A,B' then lines like '00: 0.5').")
        print("Finish input with a blank line (press Enter on an empty line).")

        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nInterrupted. Exiting.")
                sys.exit(0)
            if line.strip() == "":
                break
            lines.append(line)

        if not lines:
            print("No input provided. Exiting.")
            sys.exit(0)

        # Write to a temporary file and load via existing parser
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("\n".join(lines))
            temp_path = tf.name

        try:
            prob_system = ProbabilitySystem.from_file(temp_path, args.names if args.names else None)
            _print_joint_table(prob_system)
            run_interactive_loop(prob_system)
            _print_goodbye_once()
        except Exception as e:
            print(f"Error parsing manual input: {e}")
            sys.exit(1)
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
def execute_command(prob_system: ProbabilitySystem, query: str):
    """Parse and execute a single CLI command string against the provided ProbabilitySystem.

    Returns:
      - None: when the command either already printed output or performed a control action (like save) or when quitting.
      - float: numeric result for probability/arithmetic queries.
      - bool: boolean result for independence queries.
      - str: textual output to print.
    """
    if query is None:
        return None

    q = query.strip()
    if q == "":
        return ""

    low = q.lower()

    if low == "quit" or low == "exit":
        return "__EXIT__"
    if low == "help":
        print_help()
        return None
    if low.startswith("open ") or low == "open":
        parts = q.split(maxsplit=1)
        if len(parts) == 1:
            return "Error: Usage: open <file.inp|file.net>"
        path = parts[1].strip()
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        if not (path.endswith('.inp') or path.endswith('.net')):
            return "Error: Unsupported file type. Use .inp or .net"
        try:
            new_ps = ProbabilitySystem.from_file(path)
        except Exception as e:
            return f"Error loading file: {e}"
        # Mutate the existing object's internal state so references remain valid.
        prob_system.num_variables = new_ps.num_variables
        prob_system.variable_names = new_ps.variable_names
        prob_system.joint_probabilities = new_ps.joint_probabilities
        return f"Opened {path} ({prob_system.num_variables} variables)"
    if low.startswith("precision"):
        # Forms:
        #   precision          -> show current precision
        #   precision 8        -> set to 8
        parts = q.split()
        from probs_core.formatting import get_precision, set_precision
        if len(parts) == 1:
            return f"Current precision: {get_precision()}"
        elif len(parts) == 2:
            try:
                new_p = int(parts[1])
                set_precision(new_p)
                return f"Precision set to {new_p}"
            except Exception as e:
                return f"Error: {e}"
        else:
            return "Error: Usage: precision <int>"
    if low == "marginals":
        _print_marginals(prob_system)
        return None
    if low == "independence":
        _print_independence_table(prob_system)
        return None
    if low == "cond_independence":
        _print_conditional_independence_table(prob_system)
        return None
    if low.startswith("cond_probs(") and q.endswith(")"):
        try:
            params = q[len("cond_probs(") : -1]
            n_value, m_value = map(int, params.split(","))
            _print_conditional_probabilities(prob_system, n_value, m_value)
        except ValueError:
            return "Error: Invalid format. Use 'cond_probs(n,m)' where n and m are positive integers."
        except Exception as e:
            return f"Error: {e}"
        return None
    if low.startswith("save"):
        parts = q.split()
        if len(parts) == 2:
            filename = parts[1]
        else:
            try:
                filename = input("Enter filename to save probabilities: ").strip()
            except KeyboardInterrupt:
                raise
        try:
            if os.path.exists(filename):
                # Ask for confirmation
                try:
                    reply = input(f"File '{filename}' exists. Overwrite? [y/N]: ").strip().lower()
                except KeyboardInterrupt:
                    raise
                if reply not in ("y", "yes"):
                    return f"Save cancelled; file '{filename}' not overwritten."
            prob_system.save_to_file(filename)
            return f"Probabilities saved to {filename}"
        except Exception as e:
            return f"Error saving file: {e}"
    if low.startswith("list"):
        # Optional argument: variable name filter
        parts = q.split(maxsplit=1)
        filter_var = None
        if len(parts) == 2:
            candidate = parts[1].strip()
            # Validate variable exists (case sensitive match to existing names)
            if candidate not in prob_system.variable_names:
                return f"Error: Unknown variable '{candidate}'"
            filter_var = candidate
        # Determine state lists; fall back to binary implicit if not present
        if hasattr(prob_system, 'variable_states'):
            var_states_full = prob_system.variable_states
        else:
            var_states_full = [["0","1"] for _ in prob_system.variable_names]
        if filter_var:
            names = [filter_var]
            idx = prob_system.variable_names.index(filter_var)
            var_states = [var_states_full[idx]]
        else:
            names = prob_system.variable_names
            var_states = var_states_full
        # Compute widths based on subset if filtered
        name_col_w = max(len("Variable"), *(len(n) for n in names))
        states_strs = [", ".join(states) for states in var_states]
        _ = max(len("States"), *(len(s) for s in states_strs))  # retained for potential future alignment
        header = f"{'Variable'.ljust(name_col_w)} | {'Card'.rjust(4)} | {'States'}"
        max_row_len = 0
        for name, states_repr, states in zip(names, states_strs, var_states):
            row_len = len(f"{name.ljust(name_col_w)} | {str(len(states)).rjust(4)} | {states_repr}")
            if row_len > max_row_len:
                max_row_len = row_len
        full_width = max(len(header), max_row_len)
        sep = '-' * full_width
        title = "Variable:" if filter_var else "Variables:";
        print(f"\n{title}")
        print(sep)
        print(header)
        print(sep)
        for name, states, s_repr in zip(names, var_states, states_strs):
            line = f"{name.ljust(name_col_w)} | {str(len(states)).rjust(4)} | {s_repr}"
            if len(line) < full_width:
                line += ' ' * (full_width - len(line))
            print(line)
        print(sep)
        return None
    if low.startswith("networks"):
        # Scan inputs/ directory for .inp and .net files; extract first contiguous block of comment lines at top
        import glob
        input_dir = os.path.join(os.path.dirname(__file__), 'inputs')
        # Optional filter argument: 'net' or 'inp'
        parts = q.split()
        ext_filter = None
        if len(parts) == 2:
            arg = parts[1].strip().lower()
            if arg in ("net", "inp"):
                ext_filter = '.' + arg
            else:
                return "Error: Unsupported networks filter. Use 'networks', 'networks net', or 'networks inp'"
        patterns = []
        if ext_filter in (None, '.inp'):
            patterns.append(os.path.join(input_dir, '*.inp'))
        if ext_filter in (None, '.net'):
            patterns.append(os.path.join(input_dir, '*.net'))
        files = []
        for pat in patterns:
            files.extend(glob.glob(pat))
        files.sort()
        rows = []  # (filename, var_count, description)
        for path in files:
            rel_name = os.path.basename(path)
            desc_lines = []
            var_count = None
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    for line in fh:
                        if line.strip() == '':
                            # stop at first blank line after collecting any comment lines
                            break
                        if line.lstrip().startswith('#'):
                            # strip leading '#' and whitespace
                            cleaned = line.lstrip()[1:].strip()
                            if cleaned:
                                desc_lines.append(cleaned)
                            else:
                                # allow empty comment line to terminate
                                break
                        else:
                            # first non-comment, non-blank line ends header extraction
                            break
                # Second pass to detect variable declarations
                with open(path, 'r', encoding='utf-8') as fh2:
                    for line in fh2:
                        ls = line.strip()
                        if not ls:
                            continue
                        # .inp / legacy .net variable header style
                        if ls.lower().startswith('variables:'):
                            after = ls.split(':',1)[1]
                            names = [n.strip() for n in after.replace(',', ' ').split() if n.strip()]
                            var_count = len(names)
                            break
                        # multi-valued .net declarations start with 'variable '
                        if ls.startswith('variable '):
                            # gather all consecutive 'variable ' lines
                            multi_vars = []
                            # read current line var name
                            mline = ls[len('variable '):].strip()
                            if ' ' in mline:
                                name = mline.split('{',1)[0].strip()
                            else:
                                name = mline
                            multi_vars.append(name)
                            # continue scanning for more variable lines
                            for l2 in fh2:
                                s2 = l2.strip()
                                if s2.startswith('variable '):
                                    mline2 = s2[len('variable '):].strip()
                                    if ' ' in mline2:
                                        name2 = mline2.split('{',1)[0].strip()
                                    else:
                                        name2 = mline2
                                    multi_vars.append(name2)
                                    continue
                                else:
                                    break
                            var_count = len(multi_vars)
                            break
            except Exception as e:
                desc_lines = [f"(Error reading file: {e})"]
            description = ' '.join(desc_lines) if desc_lines else '(No description)'
            # Truncate overly long descriptions for table aesthetics
            if len(description) > 160:
                description = description[:157] + '...'
            rows.append((rel_name, var_count if var_count is not None else 0, description))
        if not rows:
            print("No network files found in inputs/ directory.")
            return None
        # Compute column widths
        name_col_w = max(len('File'), *(len(r[0]) for r in rows))
        vars_col_w = max(len('Vars'), *(len(str(r[1])) for r in rows))
        desc_col_w = max(len('Description'), *(len(r[2]) for r in rows))
        # Bound description width to avoid overly wide tables
        max_desc_width = 120
        if desc_col_w > max_desc_width:
            desc_col_w = max_desc_width
        header = f"{'File'.ljust(name_col_w)} | {'Vars'.rjust(vars_col_w)} | Description"
        sep = '-' * max(len(header), name_col_w + 3 + vars_col_w + 3 + desc_col_w)
        title = "Available Networks" if ext_filter is None else f"Available {ext_filter} Networks"
        print(f"\n{title}:")
        print(sep)
        print(header)
        print(sep)
        for fname, vcount, desc in rows:
            if len(desc) > desc_col_w:
                desc = desc[:desc_col_w-3] + '...'
            print(f"{fname.ljust(name_col_w)} | {str(vcount).rjust(vars_col_w)} | {desc}")
        print(sep)
        return None
    if low == "joint_probs":
        _print_joint_table(prob_system)
        return None
    if low == "joint_table":
        _print_joint_table_full(prob_system)
        return None
    if low == "table":
        _print_joint_table_full(prob_system)
        return None

    # Entropy command: entropy, entropy(A), entropy(A,B base=2)
    if low.startswith("entropy"):
        # extract inside parentheses if present
        m = re.match(r"^entropy\s*(?:\(\s*([^)]*?)\s*(?:base=(\d+(?:\.\d+)?))?\s*\))?(?:\s+base=(\d+(?:\.\d+)?))?$", q, re.I)
        if not m:
            return "Error: invalid entropy command. Examples: 'entropy', 'entropy(A)', 'entropy(A,B base=2)'"
        vars_text = m.group(1)
        base_text_inside = m.group(2)
        base_text_outside = m.group(3)
        base_text = base_text_inside or base_text_outside
        base = float(base_text) if base_text else 2.0
        try:
            if not vars_text or vars_text.strip() == "":
                value = prob_system.entropy(None, base=base)
            else:
                var_names = [v.strip() for v in vars_text.split(",") if v.strip()]
                indices = [prob_system._name_to_index(name) for name in var_names]
                value = prob_system.entropy(indices, base=base)
            return float(value)
        except Exception as e:
            return f"Error: {e}"

    # Conditional entropy: cond_entropy(A|B) or conditional_entropy(A|B base=2)
    if low.startswith("cond_entropy") or low.startswith("conditional_entropy"):
        m = re.match(r"^(?:cond_entropy|conditional_entropy)\s*\(\s*([^|)]+)\s*\|\s*([^\)]+?)\s*(?:base=(\d+(?:\.\d+)?))?\s*\)(?:\s+base=(\d+(?:\.\d+)?))?$", q, re.I)
        if not m:
            return "Error: invalid conditional entropy command. Example: 'cond_entropy(A|B)'"
        target_text = m.group(1).strip()
        given_text = m.group(2).strip()
        base_text_inside = m.group(3)
        base_text_outside = m.group(4)
        base_text = base_text_inside or base_text_outside
        base = float(base_text) if base_text else 2.0
        try:
            target_vars = [v.strip() for v in target_text.split(",") if v.strip()]
            given_vars = [v.strip() for v in given_text.split(",") if v.strip()]
            t_idx = [prob_system._name_to_index(name) for name in target_vars]
            g_idx = [prob_system._name_to_index(name) for name in given_vars]
            value = prob_system.conditional_entropy(t_idx, g_idx, base=base)
            return float(value)
        except Exception as e:
            return f"Error: {e}"

    # Mutual information: mutual_info(A,B) or mutual_information(A,B)
    if low.startswith("mutual_info") or low.startswith("mutual_information"):
        m = re.match(r"^(?:mutual_info|mutual_information)\s*\(\s*([^,\)]+)\s*,\s*([^\)]+?)\s*(?:base=(\d+(?:\.\d+)?))?\s*\)(?:\s+base=(\d+(?:\.\d+)?))?$", q, re.I)
        if not m:
            return "Error: invalid mutual information command. Example: 'mutual_info(A,B)'"
        a_text = m.group(1).strip()
        b_text = m.group(2).strip()
        base_text_inside = m.group(3)
        base_text_outside = m.group(4)
        base_text = base_text_inside or base_text_outside
        base = float(base_text) if base_text else 2.0
        try:
            a_idx = prob_system._name_to_index(a_text)
            b_idx = prob_system._name_to_index(b_text)
            value = prob_system.mutual_information(a_idx, b_idx, base=base)
            return float(value)
        except Exception as e:
            return f"Error: {e}"

    # Odds ratio: odds_ratio(A,B)
    if low.startswith("odds_ratio"):
        m = re.match(r"^odds_ratio\s*\(\s*([^,\)]+)\s*,\s*([^\)]+)\s*\)\s*$", q, re.I)
        if not m:
            return "Error: invalid odds_ratio command. Example: 'odds_ratio(A,B)'"
        a_text = m.group(1).strip()
        b_text = m.group(2).strip()
        try:
            a_idx = prob_system._name_to_index(a_text)
            b_idx = prob_system._name_to_index(b_text)
            val = prob_system.odds_ratio(a_idx, b_idx)
            return val if val is None else float(val)
        except Exception as e:
            return f"Error: {e}"

    # Relative risk: relative_risk(A,B)
    if low.startswith("relative_risk"):
        m = re.match(r"^relative_risk\s*\(\s*([^,\)]+)\s*,\s*([^\)]+)\s*\)\s*$", q, re.I)
        if not m:
            return "Error: invalid relative_risk command. Example: 'relative_risk(A,B)'"
        a_text = m.group(1).strip()
        b_text = m.group(2).strip()
        try:
            a_idx = prob_system._name_to_index(a_text)
            b_idx = prob_system._name_to_index(b_text)
            val = prob_system.relative_risk(a_idx, b_idx)
            return val if val is None else float(val)
        except Exception as e:
            return f"Error: {e}"

    # Sampling: sample(n=1)
    if low.startswith("sample"):
        # Accept 'sample' or 'sample(n)' or 'sample(n=10)'
        m = re.match(r"^sample\s*(?:\(\s*(?:n\s*=\s*)?(\d+)\s*\))?\s*$", q, re.I)
        if not m:
            return "Error: invalid sample command. Example: 'sample', 'sample(5)' or 'sample(n=5)'"
        n_text = m.group(1)
        n = int(n_text) if n_text else 1
        try:
            samples = prob_system.sample(n)
            return samples
        except Exception as e:
            return f"Error: {e}"

    if any(op in q for op in ["+", "-", "*", "/"]):
        # Try arithmetic expression
        try:
            result = prob_system.evaluate_arithmetic_expression(q)
            return float(result)
        except Exception as e:
            return f"Error: {e}"

    # Independence / conditional independence queries. We explicitly check both
    # patterns here instead of relying only on the default evaluate_query
    # branch because evaluate_query historically only guarded on IsIndep( and
    # line-wrapping or user edits could introduce lowercase variants or spacing.
    low_nospace = q.replace(" ", "")
    if low_nospace.startswith("IsIndep(") or low_nospace.startswith("IsCondIndep("):
        try:
            return prob_system.evaluate_query(low_nospace)
        except Exception as e:
            return f"Error: {e}"

    # Default: try as probability or independence query
    try:
        result = prob_system.evaluate_query(q)
        return result
    except Exception as e:
        return f"Error: {e}"


if __name__ == '__main__':
    main()
