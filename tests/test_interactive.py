import sys
from types import SimpleNamespace


def test_main_invokes_repl(monkeypatch):
    """Ensure `probs.py` main() uses run_interactive_loop when stdin is a TTY.

    We monkeypatch `probs_cli.run_interactive_loop` and `sys.stdin.isatty` to
    simulate an interactive environment and confirm the REPL is invoked.
    """
    import probs_cli

    called = {}

    def fake_run_interactive_loop(ps):
        called['invoked'] = True

    monkeypatch.setattr(probs_cli, 'run_interactive_loop', fake_run_interactive_loop)

    # Simulate that stdin is a TTY so the CLI will not skip the REPL
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(isatty=lambda: True))

    # Run main with a test file; this should call our fake REPL
    monkeypatch.setattr(sys, 'argv', ['probs.py', 'inputs/medical_test.inp'])
    probs_cli.main()

    assert called.get('invoked', False) is True