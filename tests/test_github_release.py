"""Release lifecycle tests use temporary repositories and an in-memory remote."""
import contextlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from scripts import vocechat_notify as notify

SPEC = importlib.util.spec_from_file_location("xxstock_release", Path(__file__).resolve().parents[1] / ".agents/skills/github-release/scripts/release.py")
release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release
SPEC.loader.exec_module(release)
REPO = "example/XXStock"
NOTES = "建立项目设计和发布能力，尚无业务应用。\n\n## 新增功能\n\n- 项目 Skill 与中文发布说明。\n\n## 验证结果\n\n- 合成场景验证通过；真实远端验收由工作流完成。\n"


class FakeAPI:
    def __init__(self):
        self.tags = {}
        self.releases = {}
        self.calls = []
        self.fail_release = False

    def request(self, method, path, payload=None, missing_ok=False):
        self.calls.append((method, path, payload))
        if path.startswith("/git/ref/tags/"):
            sha = self.tags.get(path.rsplit("/", 1)[1])
            return {"object": {"type": "commit", "sha": sha}} if sha else None
        if path.startswith("/releases/tags/"):
            return self.releases.get(path.rsplit("/", 1)[1])
        if method == "POST" and path == "/git/refs":
            self.tags[payload["ref"].removeprefix("refs/tags/")] = payload["sha"]
            return {}
        if method == "POST" and path == "/releases":
            if self.fail_release:
                raise release.ReleaseError("Synthetic release failure")
            record = {**payload, "html_url": f"https://github.com/{REPO}/releases/tag/{payload['tag_name']}"}
            self.releases[payload["tag_name"]] = record
            return record
        raise AssertionError((method, path))


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = self.directory / "repo"
        self.root.mkdir()
        for args in (("init", "-b", "main"), ("config", "user.name", "Example"), ("config", "user.email", "example@example.invalid"),
                     ("remote", "add", "origin", f"https://github.com/{REPO}.git")):
            release.git(self.root, *args)
        (self.root / "README.md").write_text("Example\n", encoding="utf-8")
        self.base = self.commit()
        self.source = self.directory / "notes.md"
        self.source.write_text(NOTES, encoding="utf-8")
        self.api = FakeAPI()

    def commit(self):
        release.git(self.root, "add", ".")
        release.git(self.root, "commit", "-m", "Synthetic batch")
        return release.git(self.root, "rev-parse", "HEAD")

    def batch(self, **kwargs):
        release.prepare(self.root, self.source, **kwargs)
        sha = self.commit()
        event_path = self.directory / "event.json"
        event_path.write_text(json.dumps({"before": self.base, "after": sha, "ref": "refs/heads/main", "repository": {"full_name": REPO}}), encoding="utf-8")
        return {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": sha,
                "GITHUB_REPOSITORY": REPO, "GITHUB_EVENT_PATH": str(event_path)}

    def test_first_prepare_is_local_and_canonical(self):
        with patch.object(release.urllib.request, "build_opener") as network:
            result = release.prepare(self.root, self.source)
        network.assert_not_called()
        self.assertEqual(result["version"], "0.1.0")
        self.assertEqual(release.git(self.root, "rev-parse", "HEAD"), self.base)
        info = release.check(self.root, self.base)
        self.assertEqual(info["compare_url"], f"https://github.com/{REPO}/commits/v0.1.0")
        self.assertTrue(info["notes"].endswith("\n"))

    def test_default_patch_and_integer_ordering(self):
        release.prepare(self.root, self.source)
        self.assertEqual(release.prepare(self.root, self.source)["version"], "0.1.1")
        self.assertGreater(release.Version.parse("0.1.10"), release.Version.parse("0.1.9"))
        self.assertEqual(str(release.Version.parse("0.1.9").next_patch()), "0.1.10")

    def test_explicit_upgrade_requires_flag_and_reason(self):
        release.prepare(self.root, self.source)
        for kwargs in ({"requested": "1.0.0"}, {"requested": "0.2.0", "allow_version_change": True}, {"requested": "0.1.0"}, {"requested": "0.1.01"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(release.ReleaseError):
                release.prepare(self.root, self.source, **kwargs)
        result = release.prepare(self.root, self.source, requested="1.0.0", allow_version_change=True, reason="用户明确指定 1.0.0")
        self.assertEqual(result["change"], "explicit")
        release.check(self.root)

    def test_existing_materials_not_overwritten(self):
        release.prepare(self.root, self.source)
        (self.root / "docs/releases/0.1.1.md").write_text("Existing\n", encoding="utf-8")
        with self.assertRaises(release.ReleaseError):
            release.prepare(self.root, self.source)
        self.assertEqual((self.root / "VERSION").read_text(), "0.1.0\n")

    def test_missing_bump_fails_main_check(self):
        env = self.batch()
        with self.assertRaises(release.ReleaseError):
            release.check(self.root, env["GITHUB_SHA"])

    def test_material_mismatch_and_secret_notes_rejected(self):
        release.prepare(self.root, self.source)
        note = self.root / "docs/releases/0.1.0.md"
        note.write_text(note.read_text(encoding="utf-8").replace("# XXStock 0.1.0", "# XXStock 0.1.1"), encoding="utf-8")
        with self.assertRaises(release.ReleaseError):
            release.check(self.root)
        for text in (NOTES.replace("新增功能", "待填写"), NOTES + "\n" + "sk-" + "X" * 24):
            with self.assertRaises(release.ReleaseError):
                release.validate_notes(release.Version(0, 1, 0), "# XXStock 0.1.0\n\n" + text)

    def test_publish_exact_sha_prerelease_not_latest_and_reuse(self):
        env = self.batch()
        result = release.publish(self.root, env, self.api)
        record = self.api.releases["v0.1.0"]
        self.assertEqual(record["target_commitish"], env["GITHUB_SHA"])
        self.assertEqual(self.api.tags["v0.1.0"], env["GITHUB_SHA"])
        self.assertTrue(record["prerelease"])
        self.assertEqual(record["make_latest"], "false")
        self.assertFalse(result["reused"])
        writes = len([call for call in self.api.calls if call[0] == "POST"])
        self.assertTrue(release.publish(self.root, env, self.api)["reused"])
        self.assertEqual(len([call for call in self.api.calls if call[0] == "POST"]), writes)

    def test_wrong_tag_and_conflicting_release_stop_without_writes(self):
        env = self.batch()
        self.api.tags["v0.1.0"] = self.base
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, env, self.api)
        self.assertFalse(any(call[0] == "POST" for call in self.api.calls))
        self.api.tags.clear()
        release.publish(self.root, env, self.api)
        self.api.releases["v0.1.0"]["body"] += "Changed"
        self.api.calls.clear()
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, env, self.api)
        self.assertFalse(any(call[0] == "POST" for call in self.api.calls))

    def test_tag_created_release_failed_recovers_same_version(self):
        env = self.batch()
        self.api.fail_release = True
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, env, self.api)
        self.assertEqual(self.api.tags["v0.1.0"], env["GITHUB_SHA"])
        self.api.fail_release = False
        release.publish(self.root, env, self.api)
        self.assertEqual((self.root / "VERSION").read_text(), "0.1.0\n")
        self.assertEqual(sum(call[1] == "/git/refs" for call in self.api.calls), 1)

    def test_previous_release_required_and_notes_immutable(self):
        first = self.batch()
        release.publish(self.root, first, self.api)
        self.base = first["GITHUB_SHA"]
        second = self.batch()
        previous = self.api.releases.pop("v0.1.0")
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, second, self.api)
        self.api.releases["v0.1.0"] = previous
        release.publish(self.root, second, self.api)
        self.assertIn("v0.1.0...v0.1.1", self.api.releases["v0.1.1"]["body"])
        self.base = second["GITHUB_SHA"]
        third = self.batch()
        previous_notes = self.root / "docs/releases/0.1.1.md"
        previous_notes.write_text(previous_notes.read_text(encoding="utf-8") + "Changed\n", encoding="utf-8")
        changed_sha = self.commit()
        event_path = Path(third["GITHUB_EVENT_PATH"])
        payload = json.loads(event_path.read_text())
        payload["after"] = changed_sha
        event_path.write_text(json.dumps(payload))
        third["GITHUB_SHA"] = changed_sha
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, third, self.api)

    def test_non_main_wrong_sha_dirty_checkout_rejected(self):
        env = self.batch()
        for changes in ({"GITHUB_ACTIONS": "false"}, {"GITHUB_REF": "refs/heads/dev"}, {"GITHUB_EVENT_NAME": "pull_request"}, {"GITHUB_SHA": self.base}, {"GITHUB_REPOSITORY": "other/repo"}):
            with self.subTest(changes=changes), self.assertRaises(release.ReleaseError):
                release.publish(self.root, {**env, **changes}, self.api)
        (self.root / "README.md").write_text("Dirty\n")
        with self.assertRaises(release.ReleaseError):
            release.publish(self.root, env, self.api)
        self.assertFalse(any(call[0] == "POST" for call in self.api.calls))

    def test_rewritten_history_rejected_before_remote_writes(self):
        first = self.batch()
        release.publish(self.root, first, self.api)
        self.base = first["GITHUB_SHA"]
        files = {name: (self.root / name).read_bytes() for name in release.git(self.root, "ls-files").splitlines()}
        release.git(self.root, "checkout", "--orphan", "rewritten")
        release.git(self.root, "rm", "-rf", ".")
        for name, contents in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        second = self.batch()
        self.api.calls.clear()
        with self.assertRaisesRegex(release.ReleaseError, "history was rewritten"):
            release.publish(self.root, second, self.api)
        self.assertFalse(any(call[0] == "POST" for call in self.api.calls))

    def test_historical_metadata_cannot_change_or_disappear(self):
        first = self.batch()
        release.publish(self.root, first, self.api)
        self.base = first["GITHUB_SHA"]
        second = self.batch()
        path = self.root / "docs/releases/0.1.0.json"
        path.unlink()
        sha = self.commit()
        event_path = Path(second["GITHUB_EVENT_PATH"])
        event = json.loads(event_path.read_text())
        event["after"] = sha
        event_path.write_text(json.dumps(event))
        second["GITHUB_SHA"] = sha
        self.api.calls.clear()
        with self.assertRaisesRegex(release.ReleaseError, "Historical release materials"):
            release.publish(self.root, second, self.api)
        self.assertFalse(any(call[0] == "POST" for call in self.api.calls))

    def test_release_identity_conflicts_never_overwritten(self):
        env = self.batch()
        release.publish(self.root, env, self.api)
        original = dict(self.api.releases["v0.1.0"])
        for changes in ({"name": "Wrong"}, {"tag_name": "v0.1.1"}, {"prerelease": False}, {"draft": True}):
            self.api.releases["v0.1.0"] = {**original, **changes}
            self.api.calls.clear()
            with self.subTest(changes=changes), self.assertRaises(release.ReleaseError):
                release.publish(self.root, env, self.api)
            self.assertFalse(any(call[0] == "POST" for call in self.api.calls))


class SafetyTests(unittest.TestCase):
    def test_annotated_tag_resolves_to_commit(self):
        api = MagicMock()
        api.request.side_effect = [{"object": {"type": "tag", "sha": "a" * 40}}, {"object": {"type": "commit", "sha": "b" * 40}}]
        self.assertEqual(release.tag_commit(api, "v0.1.0"), "b" * 40)
    def test_github_protocol_and_http_errors_do_not_leak_or_retry(self):
        key = "example-private-key"
        api = release.GitHubAPI(REPO, key)
        for error in (http.client.BadStatusLine(key), TimeoutError(key), urllib.error.HTTPError("https://example.invalid", 403, key, {}, io.BytesIO(key.encode()))):
            opener = MagicMock()
            opener.open.side_effect = error
            with self.subTest(error=type(error)), patch.object(release.urllib.request, "build_opener", return_value=opener):
                with self.assertRaises(release.ReleaseError) as caught:
                    api.request("GET", "/releases")
            self.assertNotIn(key, str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)
        self.assertIsNone(release.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.invalid"))

    def receipt(self):
        return {"version": "0.1.0", "repository": REPO, "sha": "a" * 40, "tag": "v0.1.0",
                "release_url": f"https://github.com/{REPO}/releases/tag/v0.1.0", "compare_url": f"https://github.com/{REPO}/commits/v0.1.0",
                "notes": "# XXStock 0.1.0\n\n" + NOTES}

    def test_release_message_links_summary_identity_and_redaction(self):
        bot = notify.BotConfig(True, "https://example.invalid", "example-key")
        receipt = self.receipt()
        receipt["notes"] += "\n- example-key @everyone [inject](https://example.invalid)\n"
        env = {"GITHUB_REPOSITORY": REPO, "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2"}
        text = notify.build_release_message(receipt, env, bot)
        for expected in ("0.1.0 已发布", "项目 Skill", "/releases/tag/v0.1.0", "commits/v0.1.0", "123，尝试 2"):
            self.assertIn(expected, text)
        self.assertNotIn("example-key", text)
        self.assertNotIn("@everyone", text)
        for changes in ({"release_url": "https://other.invalid"}, {"sha": "b" * 40}, {"tag": "v0.1.1"}, {"compare_url": f"https://github.com/{REPO}/commits/v0.1.1"}):
            with self.subTest(changes=changes), self.assertRaises(notify.NotificationError):
                notify.build_release_message({**receipt, **changes}, env, bot)

    def test_push_routing_main_version_tags_suppressed_others_retained(self):
        for ref in ("refs/heads/main", "refs/tags/v0.1.0", "refs/tags/v1.0.10"):
            self.assertFalse(notify.should_notify_push(ref))
        for ref in ("refs/heads/dev", "refs/tags/vendor", "refs/tags/v-next", "refs/tags/v0.1"):
            self.assertTrue(notify.should_notify_push(ref))

    def test_disabled_release_notification_fails_instead_of_claiming_sent(self):
        output = io.StringIO()
        with patch.object(notify, "load_config", return_value=notify.BotConfig()), patch.object(notify, "send_message") as sender, contextlib.redirect_stdout(output):
            self.assertEqual(notify.main(["--release-file", "unused.json"]), 1)
        sender.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["error"], "release_notification_disabled")

    def test_suppressed_main_cli_does_not_send(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({"ref": "refs/heads/main"}))
            with patch.object(notify, "load_config", return_value=notify.BotConfig(True)), patch.object(notify, "send_message") as sender, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(notify.main(["--event-file", str(event)]), 0)
            sender.assert_not_called()


if __name__ == "__main__":
    unittest.main()
