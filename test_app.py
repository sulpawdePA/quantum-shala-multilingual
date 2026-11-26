import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app  # noqa: E402


class QuantumShalaTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def run_gates(self, qubits, gates):
        r = self.client.post("/api/run", json={"qubits": qubits, "gates": gates})
        return r.status_code, r.get_json()

    def test_no_gate_is_always_zero(self):
        _, d = self.run_gates(1, [])
        self.assertEqual(d["counts"], {"0": 1000})

    def test_x_flips(self):
        _, d = self.run_gates(1, ["x0"])
        self.assertEqual(d["counts"], {"1": 1000})

    def test_superposition_is_about_half(self):
        _, d = self.run_gates(1, ["h0"])
        self.assertAlmostEqual(d["counts"]["0"] / 1000, 0.5, delta=0.08)

    def test_h_twice_cancels(self):
        _, d = self.run_gates(1, ["h0", "h0"])
        self.assertEqual(d["counts"], {"0": 1000})

    def test_entanglement_only_00_and_11(self):
        _, d = self.run_gates(2, ["h0", "cx01"])
        self.assertEqual(set(d["counts"]), {"00", "11"})

    def test_grover_finds_11_every_time(self):
        grover = ["h0", "h1", "cz01", "h0", "h1", "x0", "x1", "cz01", "x0", "x1", "h0", "h1"]
        _, d = self.run_gates(2, grover)
        self.assertEqual(d["counts"], {"11": 1000})

    def test_language_files_have_same_structure(self):
        codes = [x["code"] for x in self.client.get("/api/langs").get_json()["langs"]]
        self.assertEqual(codes[0], "mr")
        self.assertTrue({"mr", "en", "hi"} <= set(codes))
        ref = self.client.get("/api/lang/en").get_json()
        for code in codes:
            d = self.client.get(f"/api/lang/{code}").get_json()
            self.assertEqual(set(d) - {"draft"}, set(ref) - {"draft"}, code)
            self.assertEqual(len(d["L"]), 3, code)
            self.assertEqual(set(d["gates"]), {"h", "x", "z", "cx01", "cx10", "cz01"}, code)
            for g in d["gates"].values():
                self.assertTrue(g["cap"] and g["desc"], code)
            self.assertEqual(len(d["circuit_how"]), 4, code)
            self.assertTrue(d["words_title"] and d["step_none"] and d["step_measure"], code)
            self.assertIn("{g}", d["guide_next"], code)
            self.assertIn("{k}", d["viz_landed"], code)
            self.assertEqual(len(d["viz_names"]), 2, code)
            self.assertTrue(all(d[k] for k in ("guide_done", "guide_free", "measure_once",
                                               "viz_undecided", "viz_certain", "viz_boxes")), code)
            self.assertIn("{k}", d["ins_one"], code)
            self.assertTrue("{a}" in d["ins_pair"] and "{b}" in d["ins_pair"], code)
            for lesson, ref_lesson in zip(d["L"], ref["L"]):
                self.assertEqual(set(lesson), set(ref_lesson), code)
                self.assertEqual(len(lesson["o"]), 3, code)
                self.assertEqual(lesson["a"], ref_lesson["a"], code)
                self.assertTrue(all(lesson[k] for k in ("name", "story", "task", "q", "hint", "why")), code)

    def test_unknown_or_unsafe_language_is_rejected(self):
        self.assertEqual(self.client.get("/api/lang/xx").status_code, 404)
        self.assertEqual(self.client.get("/api/lang/..%2Fapp").status_code, 404)

    def test_rejects_bad_input(self):
        self.assertEqual(self.run_gates(3, [])[0], 400)
        self.assertEqual(self.run_gates(1, ["rm -rf"])[0], 400)
        self.assertEqual(self.run_gates(1, ["cx01"])[0], 400)
        self.assertEqual(self.run_gates(1, ["h0"] * 31)[0], 400)


if __name__ == "__main__":
    unittest.main()
