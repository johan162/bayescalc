def test_probs_import_exposes_probability_system():
    import probs

    # The wrapper should expose ProbabilitySystem
    assert hasattr(probs, "ProbabilitySystem")
