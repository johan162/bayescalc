import os
import builtins
from probs_core import ProbabilitySystem
import probs_cli


def test_save_overwrite_confirmation(tmp_path, monkeypatch):
    ps = ProbabilitySystem(1, [0.3])  # two probs: 0.3, 0.7 implied
    target = tmp_path / "table.inp"

    # First save (file does not exist yet)
    ps.save_to_file(str(target))
    assert target.exists()
    original_mtime = target.stat().st_mtime

    # Attempt overwrite with 'n' response
    inputs = iter(["n"])  # simulate user declines overwrite

    def fake_input(prompt=""):
        return next(inputs)

    monkeypatch.setattr(builtins, "input", fake_input)

    # Use CLI execute_command save path which triggers prompt
    msg = probs_cli.execute_command(ps, f"save {target}")
    assert "cancelled" in msg.lower()
    assert target.stat().st_mtime == original_mtime  # unchanged

    # Now confirm overwrite
    inputs2 = iter(["y"])  # simulate user agrees
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs2))
    msg2 = probs_cli.execute_command(ps, f"save {target}")
    assert "saved" in msg2.lower()
    assert target.stat().st_mtime >= original_mtime
