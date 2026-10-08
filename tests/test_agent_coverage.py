"""Coverage validation rejects broken routing rather than matching prose."""
import copy
import json
from pathlib import Path
import unittest

from scripts.verify_repository import coverage_issues, coverage_reference_issues

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

    def test_role_pool_cannot_replace_specialist_with_generic_group(self):
        self.coverage["roles"][0]["group"] = "generic"
        self.assertIn("approved role pool coverage incomplete", coverage_issues(self.catalog, self.coverage))

    def test_implementer_cannot_self_accept(self):
        item = self.coverage["capabilities"][0]
        item["acceptance_role_ids"] = item["implementation_role_ids"][:]
        self.assertTrue(coverage_issues(self.catalog, self.coverage))

    def test_missing_contract_and_self_reviewer(self):
        role = self.coverage["roles"][0]
        role["reviewer_role_ids"] = [role["id"]]
        role["outputs"] = []
        self.assertGreaterEqual(len(coverage_issues(self.catalog, self.coverage)), 2)

    def test_stage_zero_is_valid_but_ambiguous_stage_is_rejected(self):
        candidate = copy.deepcopy(self.coverage)
        candidate["roles"][0]["stage"] = 0
        self.assertNotIn("role stage must be an integer from 0 to 5", coverage_issues(self.catalog, candidate))
        for stage in ("2/3", "0-5", -1, 6, True):
            candidate["roles"][0]["stage"] = stage
            self.assertIn("role stage must be an integer from 0 to 5", coverage_issues(self.catalog, candidate))

    def test_human_routing_and_template_references(self):
        matrix = (ROOT / "docs/development/agent-coverage.md").read_text(encoding="utf-8")
        templates = (ROOT / ".agents/skills/multi-dialogue-development/references/roles.md").read_text(encoding="utf-8")
        self.assertEqual(coverage_reference_issues(self.coverage, matrix, templates), [])
        altered = matrix.replace("`engineering.backend_api`", "`engineering.database`", 1)
        self.assertIn("human coverage matrix disagrees with JSON routing",
                      coverage_reference_issues(self.coverage, altered, templates))
        role = self.coverage["roles"][0]
        role["template_ref"] += "-missing"
        self.assertIn("role template reference missing, duplicated or noncanonical",
                      coverage_reference_issues(self.coverage, matrix, templates))
        role["template_ref"] = role["template_ref"].removesuffix("-missing")
        anchor = role["id"].replace(".", "-").replace("_", "-")
        duplicated = templates + f'\n<a id="{anchor}"></a>\n'
        self.assertIn("role template reference missing, duplicated or noncanonical",
                      coverage_reference_issues(self.coverage, matrix, duplicated))


if __name__ == "__main__":
    unittest.main()
