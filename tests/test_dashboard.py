import unittest

from scripts.build_dashboard import build_dashboard_html


class DashboardArtifactTest(unittest.TestCase):
    def test_dashboard_contains_mart_metrics_and_quality_results(self) -> None:
        dashboard = build_dashboard_html()

        self.assertIn("Financial DWH Metrics Dashboard", dashboard)
        self.assertIn("$413.15", dashboard)
        self.assertIn("$92.65", dashboard)
        self.assertIn("Join Fanout Rows", dashboard)
        self.assertIn("0 failures", dashboard)
        self.assertIn("2024-01-01 to 2024-01-02", dashboard)


if __name__ == "__main__":
    unittest.main()
