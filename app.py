"""
Quantum Shala (Education track): a multilingual (Marathi / English / draft Hindi) tool that teaches
superposition, entanglement and Grover search with REAL Qiskit circuits.
Learner presses a gate -> circuit is run on the Aer simulator -> histogram updates live.
Run:   python app.py                 then open http://127.0.0.1:5000
Test:  python -m unittest test_app.py
Add a language: copy lang/en.json to lang/<code>.json and translate it.
"""
import json
import os
import re
from flask import Flask, jsonify, request, send_from_directory
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
SIM = AerSimulator()
SHOTS = 1000
MAX_GATES = 30
LANG_DIR = os.path.join(HERE, "lang")
LANG_CODE = re.compile(r"^[a-z]{2,3}$")

# gate code -> (name, qubits it acts on)
GATES = {
    "h0": ("h", (0,)), "h1": ("h", (1,)),
    "x0": ("x", (0,)), "x1": ("x", (1,)),
    "z0": ("z", (0,)), "z1": ("z", (1,)),
    "cx01": ("cx", (0, 1)), "cx10": ("cx", (1, 0)),
    "cz01": ("cz", (0, 1)),
}


def build_circuit(num_qubits, gates):
    qc = QuantumCircuit(num_qubits, num_qubits)
    for g in gates:
        name, qubits = GATES[g]
        if max(qubits) >= num_qubits:
            raise ValueError(f"gate {g} needs more qubits")
        getattr(qc, name)(*qubits)
    qc.measure(range(num_qubits), range(num_qubits))
    return qc


def run_circuit(num_qubits, gates):
    qc = build_circuit(num_qubits, gates)
    counts = SIM.run(qc, shots=SHOTS).result().get_counts()
    # Qiskit prints q(n-1)...q0; learners read left-to-right as q0 q1, so reverse.
    out = {k[::-1]: v for k, v in counts.items()}
    return out, str(qc.draw("text", fold=-1))


@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")


def load_lang(code):
    if not LANG_CODE.match(code):
        return None
    path = os.path.join(LANG_DIR, code + ".json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/langs")
def api_langs():
    # Default language (Marathi) first, then the rest alphabetically.
    codes = sorted(f[:-5] for f in os.listdir(LANG_DIR) if f.endswith(".json"))
    codes.sort(key=lambda c: c != "mr")
    return jsonify(langs=[{"code": c, "label": load_lang(c)["label"]} for c in codes])


@app.get("/api/lang/<code>")
def api_lang(code):
    data = load_lang(code)
    if data is None:
        return jsonify(error="unknown language"), 404
    return jsonify(data)


@app.post("/api/run")
def api_run():
    data = request.get_json(silent=True) or {}
    num_qubits = data.get("qubits")
    gates = data.get("gates", [])
    if num_qubits not in (1, 2):
        return jsonify(error="qubits must be 1 or 2"), 400
    if not isinstance(gates, list) or len(gates) > MAX_GATES or any(g not in GATES for g in gates):
        return jsonify(error="invalid gates"), 400
    try:
        counts, diagram = run_circuit(num_qubits, gates)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(counts=counts, shots=SHOTS, diagram=diagram)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
