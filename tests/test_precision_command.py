from probs_core import ProbabilitySystem
import probs_cli

def test_precision_command_changes_output(tmp_path, capsys):
    # Simple 1-variable distribution: P(A=1)=0.123456789 (implied remainder)
    p = tmp_path / "onevar.inp"
    p.write_text("""variables: A
1: 0.123456789
""")
    ps = ProbabilitySystem.from_file(str(p))

    # Default precision (should be 6) for a numeric return via execute_command
    out = probs_cli.execute_command(ps, "P(A)")
    assert abs(out - 0.123456789) < 1e-9

    # Change precision
    msg = probs_cli.execute_command(ps, "precision 4")
    assert "Precision set" in msg

    # Print joint table and inspect formatting (capture stdout)
    probs_cli.execute_command(ps, "joint_probs")
    captured = capsys.readouterr().out
    # Expect a line with 0.1235 (rounded to 4 decimals)
    assert "0.1235" in captured

    # Show precision command
    msg2 = probs_cli.execute_command(ps, "precision")
    assert msg2.endswith("4")
