"""Synthetic tests: no actual bot credentials, legacy imports or network access."""

import contextlib
import http.client
import io
import json
import tempfile
import unittest
import urllib.error
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from scripts import vocechat_notify as notify


def config():
    return notify.BotConfig(True, "https://example.invalid/chat", "example-bot-key", "19")


def event():
    return {
        "repository": {"full_name": "example/XXStock"}, "ref": "refs/heads/main",
        "before": "a" * 40, "after": "b" * 40, "pusher": {"name": "example-user"},
        "commits": [{"message": "docs: 更新设计\n\nLong body not sent"}],
    }


class ConfigTests(unittest.TestCase):
    def test_environment_overrides_local_settings_and_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config/config.local.json").write_text(json.dumps({"notifications": {"vocechat": {"group_id": "7"}}}))
            (root / ".env").write_text('VOCECHAT_ENABLED=true\nVOCECHAT_BASE_URL="https://example.invalid"\nVOCECHAT_API_KEY="example-file-key"\nVOCECHAT_GROUP_ID=8\n')
            result = notify.load_config({"VOCECHAT_GROUP_ID": "19", "VOCECHAT_API_KEY": "example-env-key"}, root=root)
            self.assertTrue(result.enabled)
            self.assertEqual(result.group_id, "19")
            self.assertEqual(result.api_key, "example-env-key")

    def test_default_is_disabled_and_channel_19(self):
        with tempfile.TemporaryDirectory() as directory:
            result = notify.load_config({}, root=Path(directory))
        self.assertFalse(result.enabled)
        self.assertEqual(result.group_id, "19")

    def test_summary_and_repr_hide_secrets_and_address(self):
        result = config()
        printed = json.dumps(result.summary()) + repr(result)
        self.assertNotIn(result.api_key, printed)
        self.assertNotIn(result.base_url, printed)
        self.assertEqual(result.summary()["group_id"], "19")

    def test_missing_key_does_not_send(self):
        with patch.object(notify.urllib.request, "build_opener") as opener:
            with self.assertRaises(notify.NotificationError):
                notify.send_message(replace(config(), api_key=""), "message")
        opener.assert_not_called()

    def test_invalid_urls_channels_timeouts_are_rejected(self):
        changes = [
            {"base_url": "http://example.invalid"}, {"base_url": "https://" + "user:example-password@" + "example.invalid"},
            {"base_url": "https://" + "@example.invalid"},
            {"base_url": "https://example.invalid?" + "token" + "=example-token"}, {"group_id": "19/20"},
            {"timeout_seconds": float("nan")}, {"timeout_seconds": 0}, {"api_prefix": "../api"},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(notify.NotificationError):
                replace(config(), **change).validate()

    def test_secret_file_and_conflicting_secret_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret_file = root / "secret.txt"
            secret_file.write_text("example-file-key\n")
            env = {"VOCECHAT_API_KEY_FILE": str(secret_file)}
            self.assertEqual(notify.load_config(env, root=root).api_key, "example-file-key")
            env["VOCECHAT_API_KEY"] = "example-direct-key"
            with self.assertRaises(notify.NotificationError):
                notify.load_config(env, root=root)

    def test_inline_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config/config.local.json").write_text(json.dumps({"notifications": {"vocechat": {"api_key": "example-key"}}}))
            with self.assertRaises(notify.NotificationError):
                notify.load_config({}, root=root)

    def test_dotenv_values_are_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            value = "$(not-a-command)"
            path.write_text("VOCECHAT_API_KEY='" + value + "'\nUNRELATED_PRIVATE_SETTING=ignored\n")
            result = notify.read_dotenv(path)
        self.assertEqual(result, {"VOCECHAT_API_KEY": value})


class MessageTests(unittest.TestCase):
    def test_push_reports_subject_and_links_without_body(self):
        text = notify.build_message(event(), {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1"}, config())
        self.assertIn("Git 推送通知", text)
        self.assertIn("更新设计", text)
        self.assertIn("/compare/", text)
        self.assertIn("/actions/runs/123", text)
        self.assertNotIn("Long body", text)

    def test_tag_creation_uses_commit_link(self):
        payload = event()
        payload.update(ref="refs/tags/v0.1", created=True, before="0" * 40)
        text = notify.build_message(payload, {}, config())
        self.assertIn("标签", text)
        self.assertIn("创建", text)
        self.assertIn("/commit/", text)

    def test_head_commit_fallback_and_empty_commits(self):
        payload = event()
        payload.pop("commits")
        payload["head_commit"] = {"message": "head-only"}
        self.assertIn("head-only", notify.build_message(payload, {}, config()))
        payload.pop("head_commit")
        self.assertNotIn("提交概要", notify.build_message(payload, {}, config()))

    def test_summaries_are_bounded_and_markdown_not_injected(self):
        payload = event()
        payload["commits"] = [{"message": "[link](https://example.invalid) @everyone " + "x" * 300}] * 10
        text = notify.build_message(payload, {}, config())
        self.assertIn("其余 5 项", text)
        self.assertNotIn("@everyone", text)
        self.assertIn("\\[link\\]", text)
        self.assertLess(len(text), 1800)

    def test_sensitive_content_is_redacted(self):
        payload = event()
        payload["commits"] = [{"message": "example-bot-key https://example.invalid/chat " + "sk-" + "X" * 24}]
        text = notify.build_message(payload, {}, config())
        self.assertNotIn(config().api_key, text)
        self.assertNotIn(config().base_url, text)
        self.assertNotIn("X" * 24, text)

    def test_invalid_event_and_external_link_rejected(self):
        for change in ({"repository": {"full_name": "https://external.invalid"}}, {"after": "not-a-sha"}, {"ref": "malformed"}):
            with self.subTest(change=change), self.assertRaises(notify.NotificationError):
                notify.build_message({**event(), **change}, {}, config())
        with self.assertRaises(notify.NotificationError):
            notify.build_message(event(), {"GITHUB_EVENT_NAME": "pull_request"}, config())

    def test_manual_run_is_not_labeled_as_push(self):
        text = notify.build_message(event(), {"GITHUB_EVENT_NAME": "workflow_dispatch"}, config())
        self.assertIn("非 Git 推送", text)


class SendTests(unittest.TestCase):
    def test_bot_api_body_header_and_channel_are_correct(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.status = 200
        opener = unittest.mock.MagicMock()
        opener.open.return_value = response
        with patch.object(notify.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(notify.send_message(config(), "### 测试"), 200)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.invalid/chat/api/bot/send_to_group/19")
        self.assertEqual(request.get_header("X-api-key"), config().api_key)
        self.assertEqual(request.get_header("Content-type"), "text/markdown")
        self.assertEqual(request.data.decode(), "### 测试")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)
        response.read.assert_not_called()

    def test_error_response_body_and_url_never_leak(self):
        body = io.BytesIO((config().api_key + config().base_url).encode())
        error = urllib.error.HTTPError(config().base_url, 403, config().api_key, {}, body)
        opener = unittest.mock.MagicMock()
        opener.open.side_effect = error
        with patch.object(notify.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(notify.NotificationError) as caught:
                notify.send_message(config(), "message")
        self.assertEqual(str(caught.exception), "bot_http_403")
        self.assertTrue(body.closed)
        self.assertEqual(opener.open.call_count, 1)

    def test_timeout_not_retried_or_leaked(self):
        opener = unittest.mock.MagicMock()
        opener.open.side_effect = TimeoutError(config().api_key)
        with patch.object(notify.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(notify.NotificationError) as caught:
                notify.send_message(config(), "message")
        self.assertEqual(str(caught.exception), "bot_network_failure_or_timeout")
        self.assertEqual(opener.open.call_count, 1)

    def test_redirect_is_not_followed(self):
        self.assertIsNone(notify.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.invalid"))

    def test_malformed_http_is_safe_nonzero_cli_failure(self):
        for error_type in (http.client.BadStatusLine, http.client.InvalidURL):
            with self.subTest(error_type=error_type), tempfile.TemporaryDirectory() as directory:
                event_file = Path(directory) / "event.json"
                event_file.write_text(json.dumps(event()), encoding="utf-8")
                output = io.StringIO()
                opener = unittest.mock.MagicMock()
                opener.open.side_effect = error_type(config().api_key + config().base_url)
                with patch.object(notify, "load_config", return_value=config()), patch.object(notify.urllib.request, "build_opener", return_value=opener), contextlib.redirect_stdout(output):
                    self.assertEqual(notify.main(["--event-file", str(event_file)]), 1)
                self.assertEqual(json.loads(output.getvalue())["error"], "bot_protocol_failure")
                self.assertNotIn(config().api_key, output.getvalue())
                self.assertNotIn(config().base_url, output.getvalue())

    def test_disabled_main_does_not_send_or_require_event(self):
        output = io.StringIO()
        with patch.object(notify, "load_config", return_value=notify.BotConfig()), patch.object(notify, "send_message") as sender, contextlib.redirect_stdout(output):
            self.assertEqual(notify.main([]), 0)
        sender.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["status"], "disabled")

    def test_check_config_is_redacted_and_offline(self):
        output = io.StringIO()
        with patch.object(notify, "load_config", return_value=config()), patch.object(notify, "send_message") as sender, contextlib.redirect_stdout(output):
            self.assertEqual(notify.main(["--check-config"]), 0)
        sender.assert_not_called()
        self.assertNotIn(config().api_key, output.getvalue())
        self.assertNotIn(config().base_url, output.getvalue())

    def test_cli_failure_is_safe_and_nonzero(self):
        output = io.StringIO()
        with patch.object(notify, "load_config", side_effect=notify.NotificationError("missing_bot_configuration")), contextlib.redirect_stdout(output):
            self.assertEqual(notify.main([]), 1)
        self.assertEqual(json.loads(output.getvalue())["error"], "missing_bot_configuration")


if __name__ == "__main__":
    unittest.main()
