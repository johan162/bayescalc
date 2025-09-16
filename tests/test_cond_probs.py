from probs_core import ProbabilitySystem
from probs_core import ui


def test_cond_probs_prints_expected_entries(capsys):
    # 3-variable system; provide 7 probabilities (last inferred)
    ps = ProbabilitySystem(3, [0.05] * 7)

    # Call the UI helper directly (as the CLI delegates to it)
    ui.pretty_print_conditional_probabilities(
        ps.variable_names, ps.num_variables, ps.get_conditional_probability, 1, 1
    )

    captured = capsys.readouterr()
    out = captured.out

    assert "Conditional Probabilities Table" in out
    # Should include at least one conditional probability expression using default names
    assert "P(A=0 | B=0)" in out or "P(A=1 | B=1)" in out


def test_cond_probs_combined_size_error(capsys):
    ps = ProbabilitySystem(3, [0.1] * 7)

    # target_size + condition_size > num_variables should print an error
    ui.pretty_print_conditional_probabilities(
        ps.variable_names, ps.num_variables, ps.get_conditional_probability, 2, 2
    )

    captured = capsys.readouterr()
    assert "Combined size" in captured.out
