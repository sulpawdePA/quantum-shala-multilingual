"""
Classical baseline vs Grover search (comparison table for the README).

Problem: one marked item among N = 2^n. The marked item is |11...1>.
  - Classical: check items one by one in random order -> expected (N+1)/2 checks.
  - Grover   : floor(pi/4 * sqrt(N)) rounds, then measure once (run on Qiskit Aer).

Run:  python baseline.py
"""
import math
import random
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

SHOTS = 2000
TRIALS = 20000


def grover_circuit(n):
    qc = QuantumCircuit(n, n)
    qc.h(range(n))
    rounds = max(1, math.floor(math.pi / 4 * math.sqrt(2 ** n)))
    for _ in range(rounds):
        # oracle: flip the phase of |11...1>  (multi-controlled Z)
        qc.h(n - 1); qc.mcx(list(range(n - 1)), n - 1); qc.h(n - 1)
        # diffuser: reflect about the average
        qc.h(range(n)); qc.x(range(n))
        qc.h(n - 1); qc.mcx(list(range(n - 1)), n - 1); qc.h(n - 1)
        qc.x(range(n)); qc.h(range(n))
    qc.measure(range(n), range(n))
    return qc, rounds


def classical_avg_checks(N, rng):
    total = 0
    for _ in range(TRIALS):
        order = list(range(N))
        rng.shuffle(order)
        total += order.index(N - 1) + 1
    return total / TRIALS


if __name__ == "__main__":
    sim, rng = AerSimulator(), random.Random(42)
    print(f"{'Items N':>8} {'Qubits':>7} {'Classical avg checks':>21} {'Grover rounds':>14} {'Grover success':>15}")
    for n in (2, 3, 4):
        N = 2 ** n
        qc, rounds = grover_circuit(n)
        counts = sim.run(qc, shots=SHOTS, seed_simulator=7).result().get_counts()
        success = counts.get("1" * n, 0) / SHOTS
        print(f"{N:>8} {n:>7} {classical_avg_checks(N, rng):>21.2f} {rounds:>14} {success:>14.1%}")
