#!/usr/bin/env python3
"""
Sequential Medical Testing Demonstration
Shows how posterior becomes prior in Bayesian updating
"""

from probs_core import ProbabilitySystem
from probs_core import ui as probs_ui


def demonstrate_sequential_testing():
    print("=== SEQUENTIAL MEDICAL TESTING DEMONSTRATION ===\n")

    # Load the original medical test data
    prob_system = ProbabilitySystem.from_file('inputs/medical_test.inp')

    print("Original Joint Probability Table:")
    # Use the UI helper from the package; ProbabilitySystem in the package doesn't
    # include instance pretty-print methods in this refactor.
    probs_ui.pretty_print_joint_table(prob_system.variable_names, prob_system.joint_probabilities)
    print()

    # First test results
    print("=== FIRST TEST ANALYSIS ===")
    # Assuming variable ordering: [Sickness, Test]
    # P(Sickness|Test=1)
    p_sick_given_positive = prob_system.get_conditional_probability([1], [1], [0], [1])
    p_positive = prob_system.get_marginal_probability([1], [1])
    p_sick = prob_system.get_marginal_probability([0], [1])

    print(f"P(Sickness|Test₁) = {p_sick_given_positive:.1%}")
    print(f"P(Test₁) = {p_positive:.6f}")
    print(f"P(Sickness) = {p_sick:.6f}")
    print()

    # Sequential testing simulation
    print("=== SEQUENTIAL TESTING SIMULATION ===")
    print("Assuming patient tests POSITIVE on first test...")
    print(f"New prior P(Sickness) = {p_sick_given_positive:.1%}")
    print()

    # Second test calculations
    prior_sick = p_sick_given_positive  # Posterior becomes prior
    prior_healthy = 1 - prior_sick

    # Test characteristics (same as first test)
    sensitivity = 0.95  # P(Test=1|Sick=1)
    false_positive = 0.06  # P(Test=1|Healthy=1)

    print("Second test with same characteristics:")
    print(f"Sensitivity: {sensitivity:.1%}")
    print(f"False positive rate: {false_positive:.1%}")
    print()

    # Calculate P(Test2=1)
    p_positive_2 = (sensitivity * prior_sick) + (false_positive * prior_healthy)
    print(f"P(Test₂=1) = {p_positive_2:.6f}")
    print()

    # Calculate updated posterior
    p_sick_given_two_positives = (sensitivity * prior_sick) / p_positive_2
    print("=== RESULT: TWO POSITIVE TESTS ===")
    print(f"P(Sickness|Test₁=1,Test₂=1) = {p_sick_given_two_positives:.1%}")
    print(f"Previous: P(Sickness|Test₁=1) = {p_sick_given_positive:.1%}")
    print()

    # Show the improvement
    improvement_factor = p_sick_given_two_positives / p_sick_given_positive
    print(f"Improvement factor: {improvement_factor:.1f}x more confident")
    print()

    # Also show what happens with two negative tests
    print("=== TWO NEGATIVE TESTS SCENARIO ===")
    specificity = 1 - false_positive  # P(Test=0|Healthy=0)
    false_negative = 1 - sensitivity  # P(Test=0|Sick=0)

    p_negative_2 = (specificity * prior_healthy) + (false_negative * prior_sick)
    p_healthy_given_two_negatives = (specificity * prior_healthy) / p_negative_2

    print(f"P(Test₂=0) = {p_negative_2:.6f}")
    print(f"P(Healthy|Sickness|Test₁=1,Test₂=0) = {p_healthy_given_two_negatives:.1%}")
    print()

    print("=== BAYESIAN LEARNING PRINCIPLE ===")
    print("Each new piece of evidence updates our beliefs:")
    print("1. Start with prior belief")
    print("2. Observe new evidence")
    print("3. Calculate posterior probability")
    print("4. Use posterior as new prior for next evidence")
    print("5. Repeat process with additional evidence")


if __name__ == "__main__":
    demonstrate_sequential_testing()