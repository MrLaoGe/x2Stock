"""Synthetic checks: compiled public assets do not waive private-file rules."""
import json
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_desktop_runtime import approved_name, canonical_source_hash, manifest_issues, parse_pointer, verify_runtime, REQUIRED, FLAT_FILES, LOCALES
from scripts.verify_repository import secret_issues


class DesktopRuntimeTests(unittest.TestCase):
    def staged_fixture(self, root):
        def git(*args, data=None):
            return subprocess.check_output(["git", *args], cwd=root, input=data, stderr=subprocess.DEVNULL)
        git("init", "-q")
        (root / "VERSION").write_bytes(b"0.1.0\n")
        (root / "frontend").mkdir()
        (root / "frontend/main.ts").write_bytes(b"export const synthetic = true\n")
        (root / ".gitattributes").write_bytes(b"/desktop-runtime/win-x64/** filter=lfs diff=lfs merge=lfs -text\n")
        git("add", "VERSION", "frontend", ".gitattributes")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=none", "commit", "-qm", "synthetic source")
        sha = git("rev-parse", "HEAD").decode().strip()
        value = {"schema": 1, "repository": "MrLaoGe/x2Stock", "version": "0.1.0",
                 "build_source_sha": sha, "source_tree_hash": canonical_source_hash(root), "platform": "win32", "arch": "x64"}
        names = [f"desktop-runtime/win-x64/{name}" for name in sorted(REQUIRED)]
        objects = {}
        lines = []
        header = bytearray(64)
        header[:2] = b"MZ"
        header[60:64] = (64).to_bytes(4, "little")
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = (json.dumps(value).encode() if name.endswith("build-manifest.json") else
                    bytes(header) + b"PE\0\0\x64\x86" if name.endswith("x2Stock.exe") else b"synthetic resource")
            path.write_bytes(data)
            pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{hashlib.sha256(data).hexdigest()}\nsize {len(data)}\n".encode()
            if pointer not in objects:
                objects[pointer] = git("hash-object", "-w", "--stdin", data=pointer).decode().strip()
            lines.append(f"100644 {objects[pointer]}\t{name}\n")
        git("update-index", "--index-info", data="".join(lines).encode())
        return names, value, git

    def restage_manifest(self, root, value, git):
        data = json.dumps(value).encode()
        (root / "desktop-runtime/win-x64/resources/build-manifest.json").write_bytes(data)
        pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{hashlib.sha256(data).hexdigest()}\nsize {len(data)}\n".encode()
        oid = git("hash-object", "-w", "--stdin", data=pointer).decode().strip()
        git("update-index", "--cacheinfo", f"100644,{oid},desktop-runtime/win-x64/resources/build-manifest.json")

    def test_materialized_objects_source_identity_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            names, value, git = self.staged_fixture(root)
            self.assertEqual(verify_runtime(root, names, materialized=True), [])
            self.restage_manifest(root, {**value, "source_tree_hash": "f" * 64}, git)
            self.assertTrue(any("source identity" in issue for issue in verify_runtime(root, names)))
            self.restage_manifest(root, {**value, "build_source_sha": "f" * 40}, git)
            self.assertTrue(any("project history" in issue for issue in verify_runtime(root, names)))
            self.restage_manifest(root, value, git)
            (root / "frontend/main.ts").write_bytes(b"changed after build\n")
            self.assertTrue(any("source identity" in issue for issue in verify_runtime(root, names)))

    def test_materialization_and_object_corruption_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            names, _, git = self.staged_fixture(root)
            name = "desktop-runtime/win-x64/resources/app.asar"
            (root / name).write_bytes(git("show", f":{name}"))
            self.assertEqual(verify_runtime(root, names), [])
            self.assertTrue(any("not been downloaded" in issue for issue in verify_runtime(root, names, materialized=True)))
            (root / name).write_bytes(b"modified object")
            self.assertTrue(any("disagree" in issue for issue in verify_runtime(root, names)))

    def test_complete_runtime_requires_all_canonical_resources(self):
        self.assertEqual(len(REQUIRED), 73)
        self.assertEqual(REQUIRED, FLAT_FILES | {f"locales/{locale}.pak" for locale in LOCALES})
        for required in REQUIRED:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "VERSION").write_text("0.1.0\n")
                names = [f"desktop-runtime/win-x64/{name}" for name in REQUIRED - {required}]
                issues = verify_runtime(root, names)
                self.assertIn(f"runtime required file missing: {required}", issues)

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
            with patch("scripts.verify_desktop_runtime.staged_pointers", return_value={"desktop-runtime/win-x64/x2Stock.exe": None}), patch("scripts.verify_desktop_runtime.subprocess.check_output", return_value=b"desktop-runtime/win-x64/x2Stock.exe\0filter\0lfs\0"):
                issues = verify_runtime(root, ["desktop-runtime/win-x64/x2Stock.exe"])
            self.assertTrue(any("ordinary binary" in issue for issue in issues))
            self.assertTrue(verify_runtime(root, [], materialized=True))


if __name__ == "__main__":
    unittest.main()
