def test_probs_import_exposes_probability_system():
    import bayescalc

    # The wrapper should expose ProbabilitySystem
    assert hasattr(bayescalc, "ProbabilitySystem")
