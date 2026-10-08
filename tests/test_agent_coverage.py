"""Coverage validation rejects broken routing rather than matching prose."""
import copy
import json
from pathlib import Path
import unittest

from scripts.verify_repository import coverage_issues

ROOT = Path(__file__).resolve().parents[1]


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.catalog = (ROOT / "docs/modules/catalog.md").read_text(encoding="utf-8")
        self.coverage = json.loads((ROOT / "docs/development/agent-coverage.json").read_text(encoding="utf-8"))

    def test_full_routing(self):
        self.assertEqual(coverage_issues(self.catalog, self.coverage), [])

    def test_missing_and_duplicate_capability(self):
        for change in (lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[0]))):
            candidate = copy.deepcopy(self.coverage)
            change(candidate["capabilities"])
            self.assertTrue(coverage_issues(self.catalog, candidate))

    def test_unknown_role(self):
        self.coverage["capabilities"][0]["business_role_ids"] = ["unknown"]
        self.assertTrue(coverage_issues(self.catalog, self.coverage))

    def test_implementer_cannot_self_accept(self):
        item = self.coverage["capabilities"][0]
        item["acceptance_role_ids"] = item["implementation_role_ids"][:]
        self.assertTrue(coverage_issues(self.catalog, self.coverage))

    def test_missing_contract_and_self_reviewer(self):
        role = self.coverage["roles"][0]
        role["reviewer_role_ids"] = [role["id"]]
        role["outputs"] = []
        self.assertGreaterEqual(len(coverage_issues(self.catalog, self.coverage)), 2)


if __name__ == "__main__":
    unittest.main()
