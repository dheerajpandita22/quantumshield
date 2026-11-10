"""
QuantumShield Quantum Engine — Day 1 Integration Demo

Runs a full demonstration of the quantum prototype:
  1. RY state preparation and verification for multiple theta values
  2. Bell pair generation (all four Bell states)
  3. Quantum teleportation for multiple input states
  4. Summary report

Run directly: python -m backend.quantum_engine.demo
"""
from __future__ import annotations

import math
import sys

from backend.quantum_engine.bell_pair import BellState
from backend.quantum_engine.runner import run_bell_pair, run_ry_state_verification
from backend.quantum_engine.teleportation import run_teleportation


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def demo_ry_states() -> None:
    print_section("1. RY State Preparation and Verification")
    test_thetas = [0.0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi]
    theta_labels = ["0 (|0⟩)", "π/4", "π/2 (|+⟩)", "3π/4", "π (|1⟩)"]
    all_pass = True
    for theta, label in zip(test_thetas, theta_labels):
        result = run_ry_state_verification(theta, shots=4096)
        status = "✓ PASS" if result["overall_pass"] else "✗ FAIL"
        if not result["overall_pass"]:
            all_pass = False
        print(
            f"  θ = {label:12s} | "
            f"⟨Z⟩ meas={result['exp_z_measured']:+.4f} theory={result['exp_z_theory']:+.4f} | "
            f"⟨X⟩ meas={result['exp_x_measured']:+.4f} theory={result['exp_x_theory']:+.4f} | "
            f"{status}"
        )
    print(f"\n  RY verification overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")


def demo_bell_pairs() -> None:
    print_section("2. Bell Pair Generation")
    for bell_state in BellState:
        result = run_bell_pair(state=bell_state, shots=2048)
        print(f"  |{bell_state.value}⟩ counts: {result['counts']}")


def demo_teleportation() -> None:
    print_section("3. Quantum Teleportation")
    test_cases = [
        (0.0, 0.0, "|0⟩"),
        (math.pi, 0.0, "|1⟩"),
        (math.pi / 2, 0.0, "|+⟩"),
        (math.pi / 4, 0.0, "RY(π/4)"),
        (math.pi / 3, math.pi / 4, "RY(π/3) with phase π/4"),
    ]
    all_pass = True
    for theta, phi, label in test_cases:
        result = run_teleportation(theta=theta, phi=phi, shots=4096)
        expected_p0 = result["expected_prob_0"]
        measured_p0 = result["bob_0_fraction"]
        deviation = abs(measured_p0 - expected_p0)
        tolerance = 0.05
        passed = deviation <= tolerance
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_pass = False
        print(
            f"  State {label:22s} | "
            f"P(|0⟩) meas={measured_p0:.4f} expected={expected_p0:.4f} "
            f"dev={deviation:.4f} | {status}"
        )
    print(f"\n  Teleportation overall: {'ALL PASS' if all_pass else 'SOME FAILURES (investigate)'}")
    print(
        "\n  NOTE: Teleportation transfers a quantum state using 1 Bell pair "
        "and 2 classical bits.\n"
        "  This simulation runs on Qiskit Aer (classical computer).\n"
        "  No real quantum hardware was used."
    )


def main() -> None:
    print("QuantumShield — Day 1 Quantum Prototype Demo")
    print("DISCLAIMER: All results are from Qiskit Aer simulation.")
    print("No real quantum hardware is accessed.\n")

    try:
        demo_ry_states()
    except Exception as exc:
        print(f"  ERROR in RY demo: {exc}", file=sys.stderr)

    try:
        demo_bell_pairs()
    except Exception as exc:
        print(f"  ERROR in Bell pair demo: {exc}", file=sys.stderr)

    try:
        demo_teleportation()
    except Exception as exc:
        print(f"  ERROR in teleportation demo: {exc}", file=sys.stderr)

    print("\n" + "=" * 60)
    print("  Day 1 Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
