# Quantum Shala: Learn Quantum Computing in Your Own Language

**QFF 2026 Quantum for Humanity Hackathon | Track: Education**

Quantum Shala is an interactive, multilingual (Marathi / English, plus a draft Hindi) web tool that teaches
three core quantum ideas: **superposition**, **entanglement** and **Grover search**.
The learner presses a gate, a real Qiskit circuit runs on a laptop simulator, and the
measurement histogram updates live. No GPU, no cloud account, no hardware needed.

## Deliverables vs. the case-study brief

| Required | Status | Where |
|---|---|---|
| Working demo in 2+ languages | Done: Marathi, English, draft Hindi | `python app.py`, [`lang/`](lang) |
| 3 guided lessons with quizzes | Done: superposition, entanglement, Grover | `index.html`, `lang/*.json` |
| Real Qiskit circuits on a laptop simulator | Done: Qiskit + Aer, live histogram | `app.py` |
| Open-source repo | Done: MIT licence | [`LICENSE`](LICENSE) |
| **Stretch Goal: Accessibility & Low-Bandwidth Mode** | **Done: Screen-reader ARIA live region, Low-Bandwidth Lite mode, High Contrast** | `index.html`, `lang/*.json` |
| Evidence from a quick learner test (3 people) | **Open: test sheet ready, results not yet collected** | Kept outside the repo |
| 3-minute pitch | Script ready; learner-test numbers still to be filled in | Kept outside the repo |

## 1. The problem

Quantum education is mostly in English, heavy on mathematics and often tied to
expensive hardware. Learners who study in regional languages are left out of the field.

## 2. Our approach

| Lesson | Everyday story | What the learner does |
|---|---|---|
| 1. Superposition | A spinning coin | Presses **H** and sees a ~50/50 histogram; presses **H** again and the result returns to 0 |
| 2. Entanglement | Two magic gloves, one in Mumbai and one in Pune | Builds a Bell pair (**H** + **CX**) and sees only `00` and `11` |
| 3. Grover search | A prize hidden in 1 of 4 boxes | Runs Grover and finds box `11` in a single round |

Each lesson has a short story, a task, a short note explaining the gates used, a
one-question quiz (a wrong answer shows a hint), and a "see the real circuit" panel
showing the Qiskit circuit diagram.

**Beginner-friendly features**

- **Guided first step.** A banner names the next gate to press and the button glows while
  the others are dimmed (lesson 1: H, H; lesson 2: H, CX; lesson 3: Run Grover). After the
  steps it switches to free play; **Clear** restarts the guide.
- **Simple 2D animation** (plain CSS, no 3D, no extra dependency), drawn from the measured counts:
  a coin that spins while the result is undecided (lessons 1 and 2, with Mumbai and Pune coins
  for the entangled pair) and four boxes that light up in proportion to how often each is
  found (lesson 3). **Measure once** lands the coin or opens one box, picked at random from
  the 1000 real shots.
- Animations respect the browser's "reduce motion" setting.
- **Accessibility & Low-Bandwidth mode (Stretch Goal)**:
  - **Screen-Reader Friendly (`aria-live="polite"`):** Live region announces circuit gate additions and simulated measurement probabilities in real-time. Full ARIA roles (`role="tab"`, `role="progressbar"`) and accessible button labels.
  - **Low-Bandwidth / Lite Mode (`⚡`):** Disables animations and heavy render passes; ultra-lightweight text/table display optimized for 2G/low-end school hardware.
  - **High-Contrast Mode (`👁`):** WCAG AAA compliant high-contrast theme for low-vision learners.

**Architecture**

```
Browser (index.html)  <-- lang/*.json via GET /api/langs, /api/lang/<code>
   |  POST /api/run  {qubits, gates[]}
   v
Flask server (app.py)  ->  validates input (whitelisted gates, max 30)
   |
   v
Qiskit QuantumCircuit  ->  AerSimulator (1000 shots)  ->  counts + circuit diagram
   |
   v
Browser draws the histogram
```

## 3. How to run

Developed and tested on Python 3.14 with the pinned versions in `requirements.txt`.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows;  use: source .venv/bin/activate  on Linux/macOS
pip install -r requirements.txt
python app.py                   # open http://127.0.0.1:5000
```

Run the tests and the classical-vs-quantum comparison:

```bash
python -m unittest test_app.py -v
python baseline.py
```

## 4. Results

### 4.1 Lesson correctness (automated tests, 9/9 passing)

| Test | Expected | Result |
|---|---|---|
| No gate | always `0` | pass |
| X gate | always `1` | pass |
| H gate | about 50% `0` | pass |
| H applied twice | back to always `0` | pass |
| H + CX | only `00` and `11` | pass |
| Grover (2 qubits) | `11` in 100% of shots | pass |
| Invalid input (3 qubits, unknown gate, 31 gates) | HTTP 400 | pass |
| All language files have the same lesson structure and UI strings (incl. guide and animation text) | same keys, 3 lessons, same answers | pass |
| Unknown or unsafe language code | HTTP 404 | pass |

### 4.1.1 Adding a language

Translations are plain JSON files in [`lang/`](lang). To add one, copy `lang/en.json` to
`lang/<code>.json` (2 to 3 lowercase letters, for example `ta`), translate the values and
set `"label"` to the language name. Add `"draft": true` until a native speaker has reviewed
it; the tool then shows a "draft translation" notice. No code change is needed, and the
tests check that the new file has the same structure as the English one.

### 4.2 Classical baseline vs Grover search

One marked item among N. The classical baseline checks items one by one in random
order (20,000 trials). Grover runs on Qiskit Aer (2,000 shots, ideal simulator, no noise).

| Items N | Qubits | Classical avg. checks | Grover rounds | Grover success rate |
|---|---|---|---|---|
| 4 | 2 | 2.50 | 1 | 100.0% |
| 8 | 3 | 4.49 | 2 | 93.9% |
| 16 | 4 | 8.49 | 3 | 95.7% |

The classical cost grows like N/2, while Grover needs about (pi/4)*sqrt(N) rounds.
For the small sizes used in teaching the difference is small; it grows with N.

### 4.3 Learner test

The test sheet is kept outside this repo. Results: **TO BE FILLED after testing with 3 learners.**

## 5. Honest limitations

- This is a **teaching tool**, not a demonstration of quantum advantage. With 4 to 16
  items, a classical computer is just as fast in real time.
- Everything runs on an **ideal simulator**. We did not run on IBM hardware, and
  we do not claim anything about noise behaviour.
- Only 1 to 2 qubits are exposed in the interface; Grover is shown as a preset sequence.
- The animations are an illustration of the idea, not a physical model (no Bloch sphere or 3D view, by design, to keep it simple for beginners). They have been checked by script against the API but not yet by learners.
- The Marathi text has not yet been reviewed by an educator or a native-speaker teacher.
  The Hindi text is a machine-assisted draft and is marked as such in the interface.
- The learner test is small (3 people) and is not a statistically meaningful study.

## 6. Next steps

- Have the Marathi and Hindi text reviewed by teachers; add Tamil and other languages through `lang/*.json`.
- Run on IBM Quantum hardware to show real noise as a lesson of its own ("why results are not perfect").
- Add lessons on quantum teleportation and the Bernstein-Vazirani algorithm.
- Work with teachers to test in a classroom and refine the stories.

## 7. Ethics and data

No personal data is collected. The server stores nothing. The learner test (if run) is
anonymous.

## 8. Credits

- [Qiskit](https://github.com/Qiskit/qiskit) and [Qiskit Aer](https://github.com/Qiskit/qiskit-aer) (Apache 2.0)
- [Flask](https://flask.palletsprojects.com/) (BSD 3-Clause)
- Concepts taught in the IBM Qiskit Fall Fest 2026 sessions (Day 1 Live Lab and Day 2 circuits/algorithms)

## 9. License

MIT, see [`LICENSE`](LICENSE).
