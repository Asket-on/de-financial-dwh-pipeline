import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PagesWorkflowContractTest(unittest.TestCase):
    def test_pages_workflow_publishes_dashboard_as_index(self) -> None:
        workflow = (
            PROJECT_ROOT / ".github" / "workflows" / "pages.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("python scripts/build_dashboard.py --check", workflow)
        self.assertIn("cp docs/dashboard.html _site/index.html", workflow)
        self.assertIn("actions/upload-pages-artifact", workflow)
        self.assertIn("actions/deploy-pages", workflow)
        self.assertIn("pages: write", workflow)
