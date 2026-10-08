"""Synthetic checks: compiled public assets do not waive private-file rules."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_desktop_runtime import approved_name, manifest_issues, parse_pointer, verify_runtime
from scripts.verify_repository import secret_issues


class DesktopRuntimeTests(unittest.TestCase):
    def test_allowlist_keeps_private_and_unrelated_binaries_out(self):
        for name in ("desktop-runtime/win-x64/x2Stock.exe", "desktop-runtime/win-x64/resources/app.asar",
                     "desktop-runtime/win-x64/locales/zh-TW.pak"):
            self.assertTrue(approved_name(name))
        for name in ("desktop-runtime/win-x64/secret.key", "desktop-runtime/win-x64/user.sqlite",
                     "desktop-runtime/win-x64/provider.csv", "desktop-runtime/win-x64/fake.exe",
                     "desktop-runtime/win-x64/../x2Stock.exe", "desktop-runtime/win-x64/locales/arbitrary.pak",
                     "desktop-runtime/win-x64/resources/notes.json", "runtime/x2Stock.exe"):
            self.assertFalse(approved_name(name), name)

    def test_lfs_pointer_is_strict_and_not_arbitrary_secret_exception(self):
        digest = "a" * 64
        pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize 12\n".encode()
        self.assertEqual(parse_pointer(pointer), (digest, 12))
        self.assertIsNone(parse_pointer(pointer + b"payload\n"))
        self.assertIsNone(parse_pointer(pointer.replace(b"size 12", b"size 0")))
        self.assertTrue(secret_issues(digest))

    def test_manifest_rejects_wrong_version_repository_arch_and_extra_fields(self):
        value = {"schema": 1, "repository": "MrLaoGe/x2Stock", "version": "0.1.0",
                 "build_source_sha": "b" * 40, "source_tree_hash": "c" * 64, "platform": "win32", "arch": "x64"}
        self.assertEqual(manifest_issues(json.dumps(value).encode(), "0.1.0"), [])
        for field, wrong in (("repository", "other/repo"), ("version", "0.1.1"),
                             ("arch", "arm64"), ("platform", "linux"), ("build_source_sha", "HEAD")):
            self.assertTrue(manifest_issues(json.dumps({**value, field: wrong}).encode(), "0.1.0"))
        self.assertTrue(manifest_issues(json.dumps({**value, "api_key": "example"}).encode(), "0.1.0"))

    def test_ordinary_git_binary_and_missing_runtime_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "VERSION").write_text("0.1.0\n")
            path = root / "desktop-runtime/win-x64/x2Stock.exe"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"MZ" + b"data" * 100)
            def result(args, **kwargs):
                if "check-attr" in args:
                    return subprocess.CompletedProcess(args, 0, "asset: filter: lfs\n", "")
                return subprocess.CompletedProcess(args, 0, "402\n", "")
            with patch("scripts.verify_desktop_runtime.subprocess.run", side_effect=result):
                issues = verify_runtime(root, ["desktop-runtime/win-x64/x2Stock.exe"])
            self.assertTrue(any("ordinary binary" in issue for issue in issues))
            self.assertTrue(verify_runtime(root, [], materialized=True))


if __name__ == "__main__":
    unittest.main()
