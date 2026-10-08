"""Synthetic GitHub asset publication; no credentials or network access."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import urllib.error

from scripts.publish_update_metadata import GitHubAPI, MetadataError, NoRedirect, decode_metadata, publish_metadata

SHA = "a" * 40
VERSION = "0.1.4"


def metadata():
    return {"schema": 1, "repository": "MrLaoGe/x2Stock", "version": VERSION,
            "source_sha": SHA, "source_tree_hash": "b" * 64, "archive_sha256": "c" * 64,
            "archive_size": 1234, "archive_url": f"https://codeload.github.com/MrLaoGe/x2Stock/zip/{SHA}",
            "runtime_subdir": "desktop-runtime/win-x64"}


def receipt():
    return {"repository": "MrLaoGe/x2Stock", "version": VERSION, "sha": SHA,
            "tag": f"v{VERSION}", "release_url": f"https://github.com/MrLaoGe/x2Stock/releases/tag/v{VERSION}", "notes": "synthetic notes"}


class FakeAPI:
    def __init__(self, raw, assets=None):
        self.raw = raw
        self.assets = copy.deepcopy(assets or [])
        self.calls = []
        self.sha = SHA
        self.release = {"id": 4, "tag_name": f"v{VERSION}", "html_url": receipt()["release_url"],
                        "draft": False, "prerelease": True, "body": "synthetic notes"}

    def asset(self):
        return {"id": 9, "name": f"x2Stock-{VERSION}-update.json", "state": "uploaded", "size": len(self.raw),
                "digest": "sha256:" + hashlib.sha256(self.raw).hexdigest()}

    def request(self, method, path, payload=None, *, upload=False):
        self.calls.append((method, path, upload))
        if path.startswith("/git/ref/"):
            return {"object": {"type": "commit", "sha": self.sha}}
        if path.startswith("/releases/tags/"):
            return self.release
        if path == "/releases/4/assets?per_page=100":
            return copy.deepcopy(self.assets)
        if method == "POST":
            assert path.startswith("/releases/4/assets?name=x2Stock-") and upload
            assert payload == self.raw
            asset = self.asset()
            self.assets.append(asset)
            return asset
        if path == "/releases/assets/9":
            return copy.deepcopy(self.assets[0])
        raise AssertionError(path)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.raw = (json.dumps(metadata(), indent=2) + "\n").encode()

    def test_upload_and_remote_digest_verification(self):
        api = FakeAPI(self.raw)
        result = publish_metadata(self.raw, receipt(), SHA, VERSION, api)
        self.assertFalse(result["reused"])
        self.assertEqual(sum(method == "POST" for method, _, _ in api.calls), 1)
        self.assertIn(("GET", "/releases/assets/9", False), api.calls)

    def test_same_exact_bytes_reuse_without_upload(self):
        api = FakeAPI(self.raw)
        api.assets = [api.asset()]
        self.assertTrue(publish_metadata(self.raw, receipt(), SHA, VERSION, api)["reused"])
        self.assertFalse(any(method != "GET" for method, _, _ in api.calls))

    def test_conflicting_existing_digest_or_missing_digest_not_overwritten(self):
        for digest in (None, "sha256:" + "d" * 64):
            api = FakeAPI(self.raw)
            api.assets = [{**api.asset(), "digest": digest}]
            with self.assertRaises(MetadataError):
                publish_metadata(self.raw, receipt(), SHA, VERSION, api)
            self.assertFalse(any(method != "GET" for method, _, _ in api.calls))

    def test_duplicate_metadata_and_other_version_rejected(self):
        for duplicate in (f"x2Stock-{VERSION}-update.json", "x2Stock-9.9.9-update.json"):
            api = FakeAPI(self.raw)
            api.assets = [api.asset(), {**api.asset(), "id": 10, "name": duplicate}]
            with self.assertRaises(MetadataError):
                publish_metadata(self.raw, receipt(), SHA, VERSION, api)

    def test_wrong_receipt_or_tag_or_release_fail_before_upload(self):
        wrong = {**receipt(), "sha": "e" * 40}
        with self.assertRaises(MetadataError):
            publish_metadata(self.raw, wrong, SHA, VERSION, FakeAPI(self.raw))
        api = FakeAPI(self.raw)
        api.sha = "e" * 40
        with self.assertRaises(MetadataError):
            publish_metadata(self.raw, receipt(), SHA, VERSION, api)
        for key, value in (("draft", True), ("body", "different"), ("html_url", "https://example.invalid"), ("prerelease", False)):
            api = FakeAPI(self.raw)
            api.release[key] = value
            with self.assertRaises(MetadataError):
                publish_metadata(self.raw, receipt(), SHA, VERSION, api)
            self.assertFalse(any(method == "POST" for method, _, _ in api.calls))

    def test_uploaded_digest_must_verify(self):
        class BadUpload(FakeAPI):
            def asset(self):
                return {**super().asset(), "digest": "sha256:" + "0" * 64}
        with self.assertRaises(MetadataError):
            publish_metadata(self.raw, receipt(), SHA, VERSION, BadUpload(self.raw))

    def test_nine_field_metadata_binding_and_limits(self):
        for key, value in (("schema", True), ("archive_url", "https://example.invalid"), ("source_sha", "f" * 40),
                           ("archive_size", -1), ("archive_size", True), ("source_tree_hash", "not-a-hash"),
                           ("runtime_subdir", "../../"), ("repository", "other/repository"), ("version", "9.9.9")):
            with self.subTest(key=key, value=value), self.assertRaises(MetadataError):
                decode_metadata(json.dumps({**metadata(), key: value}).encode(), SHA, VERSION)
        with self.assertRaises(MetadataError):
            decode_metadata(json.dumps({**metadata(), "extra": "field"}).encode(), SHA, VERSION)
        with self.assertRaises(MetadataError):
            decode_metadata(b" " * 16385, SHA, VERSION)

    def test_remote_errors_do_not_expose_provider_body_or_credentials_or_retry(self):
        opener = unittest.mock.Mock()
        opener.open.side_effect = urllib.error.URLError("synthetic private provider body")
        with patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaises(MetadataError) as failure:
                GitHubAPI("synthetic-secret-token").request("POST", "/releases/4/assets?name=synthetic.json", b"{}", upload=True)
        self.assertNotIn("synthetic private", str(failure.exception))
        self.assertNotIn("synthetic-secret", str(failure.exception))
        self.assertEqual(opener.open.call_count, 1)
        self.assertIsNone(NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_final_duplicate_asset_is_rejected_after_upload(self):
        class ConcurrentDuplicate(FakeAPI):
            def request(self, method, path, payload=None, *, upload=False):
                result = super().request(method, path, payload, upload=upload)
                if path == "/releases/assets/9":
                    self.assets.append({**self.asset(), "id": 10})
                return result
        with self.assertRaises(MetadataError):
            publish_metadata(self.raw, receipt(), SHA, VERSION, ConcurrentDuplicate(self.raw))


if __name__ == "__main__":
    unittest.main()
