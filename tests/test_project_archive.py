import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.verify_project_archive import ArchiveError, inspect_archive, safe_name, source_hash
from scripts.verify_desktop_runtime import REQUIRED, CANONICAL_LAUNCHER


class ProjectArchiveTests(unittest.TestCase):
    def fixture(self, root, *, pointer=False, wrong_source=False, extra=None, launcher=None):
        sha = "d" * 40
        files = {"VERSION": b"0.1.0\n", "启动.bat": CANONICAL_LAUNCHER if launcher is None else launcher,
                 "frontend/src/main.ts": b"export const sample = true\n"}
        identity = source_hash({name: hashlib.sha256(data).hexdigest() for name, data in files.items()
                                if name.startswith("frontend/") or name == "VERSION"})
        manifest = {"schema": 1, "repository": "MrLaoGe/x2Stock", "version": "0.1.0",
                    "build_source_sha": sha, "source_tree_hash": "e" * 64 if wrong_source else identity,
                    "platform": "win32", "arch": "x64"}
        for name in REQUIRED:
            files[f"desktop-runtime/win-x64/{name}"] = b"synthetic-public-runtime"
        header = bytearray(64)
        header[:2] = b"MZ"
        header[60:64] = (64).to_bytes(4, "little")
        files["desktop-runtime/win-x64/x2Stock.exe"] = bytes(header) + b"PE\0\0\x64\x86"
        files["desktop-runtime/win-x64/resources/build-manifest.json"] = json.dumps(manifest).encode()
        if pointer:
            files["desktop-runtime/win-x64/x2Stock.exe"] = (
                f"version https://git-lfs.github.com/spec/v1\noid sha256:{'a' * 64}\nsize 100\n").encode()
        if extra:
            files[extra] = b"synthetic"
        archive = root / "archive.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            for name, data in files.items():
                bundle.writestr(f"x2Stock-{sha}/{name}", data)
        return archive, sha

    def test_archive_identity_and_extract_only_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, sha = self.fixture(root)
            destination = root / "out"
            result = inspect_archive(archive, sha, "0.1.0", extract=destination)
            self.assertEqual(result["runtime_files"], len(REQUIRED))
            self.assertTrue((destination / "desktop-runtime/win-x64/resources/app.asar").is_file())
            self.assertTrue((destination / "启动.bat").is_file())
            self.assertFalse((destination / "frontend").exists())

    def test_lfs_pointer_source_mismatch_private_and_unapproved_assets_fail(self):
        for kwargs in ({"pointer": True}, {"wrong_source": True}, {"extra": ".env"},
                       {"extra": "desktop-runtime/win-x64/personal.sqlite"}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temp:
                archive, sha = self.fixture(Path(temp), **kwargs)
                with self.assertRaises(ArchiveError):
                    inspect_archive(archive, sha, "0.1.0")

    def test_windows_traversal_ads_devices_and_duplicate_prefixes_fail(self):
        for name in ("../escape", "/absolute", "root/file:stream", "root/NUL.txt", "root/file.", "root\\backslash"):
            with self.assertRaises(ArchiveError):
                safe_name(name)
        with tempfile.TemporaryDirectory() as temp:
            archive, sha = self.fixture(Path(temp))
            with zipfile.ZipFile(archive, "a") as bundle:
                bundle.writestr(f"x2Stock-{sha}/version", b"conflict")
            with self.assertRaises(ArchiveError):
                inspect_archive(archive, sha, "0.1.0")

    def test_private_files_at_any_depth_are_rejected(self):
        for name in (".env.production", "config/config.local.json", "backups/private.json",
                     "frontend/.env.production", "docs/data/real.sqlite-wal", "CONFIG/CONFIG.LOCAL.JSON",
                     "nested/.git/config", "nested/token.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                archive, sha = self.fixture(Path(temp), extra=name)
                with self.assertRaises(ArchiveError):
                    inspect_archive(archive, sha, "0.1.0")

    def test_launcher_is_bound_to_offline_relative_start(self):
        for launcher in (b"rem desktop-runtime\\win-x64\\x2Stock.exe\nwget https://example.com/app.exe\n",
                         CANONICAL_LAUNCHER + b"wget https://example.com/app.exe\n"):
            with tempfile.TemporaryDirectory() as temp:
                archive, sha = self.fixture(Path(temp), launcher=launcher)
                with self.assertRaises(ArchiveError):
                    inspect_archive(archive, sha, "0.1.0")


if __name__ == "__main__":
    unittest.main()
