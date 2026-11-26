"""
Noise-model simulation, circuit-depth stats and a simple error-mitigation demo.

Circuits: Bell pair (lesson 2) and Grover search for n = 2, 3, 4 qubits (lesson 3,
same construction as baseline.py).

Noise model (illustrative, NOT calibrated to a real IBM device):
  - 1-qubit gates (sx, x):  depolarizing error 0.1%
  - 2-qubit gate  (cx)   :  depolarizing error 1.0%
  - readout               :  2% chance of flipping each measured bit

Mitigation: readout-error mitigation by inverting the measured confusion matrix.

Run:  python noise_analysis.py
"""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

from baseline import grover_circuit

SHOTS = 4000
SEED = 7
BASIS = ["cx", "rz", "sx", "x"]
P_1Q, P_2Q, P_READ = 0.001, 0.01, 0.02


def make_noise_model():
    nm = NoiseModel(basis_gates=BASIS)
    nm.add_all_qubit_quantum_error(depolarizing_error(P_1Q, 1), ["sx", "x"])
    nm.add_all_qubit_quantum_error(depolarizing_error(P_2Q, 2), ["cx"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - P_READ, P_READ], [P_READ, 1 - P_READ]]))
    return nm


def bell_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def probs(counts, n):
    total = sum(counts.values())
    return np.array([counts.get(format(i, f"0{n}b"), 0) / total for i in range(2 ** n)])


def confusion_matrix(n, sim):
    """Column j = measured distribution when basis state j is prepared."""
    m = np.zeros((2 ** n, 2 ** n))
    for j in range(2 ** n):
        qc = QuantumCircuit(n, n)
        for q, bit in enumerate(reversed(format(j, f"0{n}b"))):
            if bit == "1":
                qc.x(q)
        qc.measure(range(n), range(n))
        t = transpile(qc, basis_gates=BASIS, optimization_level=0)
        counts = sim.run(t, shots=SHOTS, seed_simulator=SEED).result().get_counts()
        m[:, j] = probs(counts, n)
    return m


def mitigate(p_noisy, conf):
    p = np.linalg.solve(conf, p_noisy)
    p = np.clip(p, 0, None)
    return p / p.sum()


def analyse(name, qc, n, good_states, ideal_sim, noisy_sim):
    """good_states: list of bitstrings counted as a correct outcome."""
    t = transpile(qc, basis_gates=BASIS, optimization_level=1, seed_transpiler=SEED)
    ops = t.count_ops()
    p_ideal = probs(ideal_sim.run(t, shots=SHOTS, seed_simulator=SEED).result().get_counts(), n)
    p_noisy = probs(noisy_sim.run(t, shots=SHOTS, seed_simulator=SEED).result().get_counts(), n)
    p_mit = mitigate(p_noisy, confusion_matrix(n, noisy_sim))
    idx = [int(s, 2) for s in good_states]
    return {
        "name": name, "depth": t.depth(), "cx": ops.get("cx", 0),
        "gates": sum(v for g, v in ops.items() if g != "measure"),
        "ideal": p_ideal[idx].sum(),
        "noisy": p_noisy[idx].sum(),
        "mitigated": p_mit[idx].sum(),
    }


if __name__ == "__main__":
    ideal_sim = AerSimulator()
    noisy_sim = AerSimulator(noise_model=make_noise_model())

    rows = [analyse("Bell pair (00+11)", bell_circuit(), 2, ["00", "11"], ideal_sim, noisy_sim)]
    for n in (2, 3, 4):
        qc, rounds = grover_circuit(n)
        rows.append(analyse(f"Grover n={n} ({rounds} rd)", qc, n, ["1" * n], ideal_sim, noisy_sim))

    print(f"Noise: 1q {P_1Q:.1%}, 2q {P_2Q:.1%}, readout {P_READ:.0%}; {SHOTS} shots; basis {BASIS}")
    print(f"{'Circuit':<20} {'Depth':>6} {'Gates':>6} {'CX':>5} {'Ideal':>8} {'Noisy':>8} {'Mitigated':>10}")
    for r in rows:
        print(f"{r['name']:<20} {r['depth']:>6} {r['gates']:>6} {r['cx']:>5} "
              f"{r['ideal']:>8.1%} {r['noisy']:>8.1%} {r['mitigated']:>10.1%}")
