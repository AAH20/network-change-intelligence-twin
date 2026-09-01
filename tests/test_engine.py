import json,tempfile,unittest
from pathlib import Path
from netchange.engine import compile_change,path
from netchange.kpis import scorecard
from netchange.render import write

def fixture(): return json.loads(Path("examples/multicloud-bgp-change.json").read_text())

class EngineTests(unittest.TestCase):
    def test_baseline_passes_and_change_is_blocked(self):
        report=compile_change(fixture());self.assertTrue(report["baseline"][0]["passed"]);self.assertEqual(report["decision"]["status"],"hold")
    def test_change_exposes_unencrypted_high_latency_path(self):
        report=compile_change(fixture());self.assertIn("encryption",report["candidate"][0]["violations"]);self.assertIn("latency",report["candidate"][0]["violations"])
    def test_economics_are_explicit(self):
        report=compile_change(fixture());self.assertEqual(report["economics"]["revenue_at_risk_usd"],43200)
    def test_receipt_is_deterministic(self): self.assertEqual(compile_change(fixture())["receipt_sha256"],compile_change(fixture())["receipt_sha256"])
    def test_scorecard_retains_gaps(self):
        raw=fixture();report=compile_change(raw);k=scorecard(report,raw["kpi_observations"]);self.assertEqual(len(k["metrics"]),25);self.assertTrue(any(not x["passed"] for x in k["metrics"]))
    def test_artifacts_render(self):
        raw=fixture();report=compile_change(raw);report["kpi_scorecard"]=scorecard(report,raw["kpi_observations"])
        with tempfile.TemporaryDirectory() as d: write(report,Path(d));self.assertTrue((Path(d)/"change-decision.json").exists())

if __name__=="__main__":unittest.main()
