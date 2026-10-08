"""Check the narrowly approved Windows runtime and its Git LFS representation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

RUNTIME_ROOT = "desktop-runtime/win-x64/"
FLAT_FILES = {
    "x2Stock.exe", "chrome_100_percent.pak", "chrome_200_percent.pak",
    "d3dcompiler_47.dll", "dxcompiler.dll", "dxil.dll", "ffmpeg.dll",
    "icudtl.dat", "LICENSE.electron.txt", "LICENSES.chromium.html",
    "resources.pak", "snapshot_blob.bin", "v8_context_snapshot.bin",
    "vk_swiftshader_icd.json", "vk_swiftshader.dll", "vulkan-1.dll",
    "resources/build-manifest.json", "resources/app.asar",
}
LOCALES = set("af am ar bg bn ca cs da de el en-GB en-US es-419 es et fa fi fil fr gu he hi hr hu id it ja kn ko lt lv ml mr ms nb nl pl pt-BR pt-PT ro ru sk sl sr sv sw ta te th tr uk ur vi zh-CN zh-TW".split())
REQUIRED = {"x2Stock.exe", "resources/app.asar", "LICENSE.electron.txt",
            "LICENSES.chromium.html", "resources/build-manifest.json", "locales/en-US.pak",
            "locales/zh-CN.pak", "locales/zh-TW.pak"}
POINTER = re.compile(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([1-9][0-9]*)\n")
COMPILED_SUFFIXES = {".exe", ".dll", ".asar", ".pak", ".bin", ".dat", ".pdb"}


def approved_name(name: str) -> bool:
    if not name.startswith(RUNTIME_ROOT):
        return False
    relative = name[len(RUNTIME_ROOT):]
    parts = PurePosixPath(relative).parts
    if "\\" in relative or ".." in parts or not relative or relative.startswith("/"):
        return False
    return relative in FLAT_FILES or (len(parts) == 2 and parts[0] == "locales"
                                    and parts[1].endswith(".pak") and parts[1][:-4] in LOCALES)


def parse_pointer(data: bytes) -> tuple[str, int] | None:
    match = POINTER.fullmatch(data)
    return (match[1].decode("ascii"), int(match[2])) if match else None


def manifest_issues(data: bytes, expected_version: str) -> list[str]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        return ["runtime build manifest must be valid UTF-8 JSON"]
    if not isinstance(value, dict):
        return ["runtime build manifest must be an object"]
    expected = {"schema", "repository", "version", "build_source_sha", "source_tree_hash", "platform", "arch"}
    if set(value) != expected:
        return ["runtime build manifest has unexpected or missing fields"]
    issues = []
    if value["schema"] != 1 or value["repository"] != "MrLaoGe/x2Stock":
        issues.append("runtime build manifest has wrong schema or repository")
    if value["version"] != expected_version or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", str(value["version"])):
        issues.append("runtime version must match root VERSION")
    if value["platform"] != "win32" or value["arch"] != "x64":
        issues.append("runtime must target Windows x64")
    if not isinstance(value["build_source_sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["build_source_sha"]):
        issues.append("runtime build source SHA is invalid")
    if not isinstance(value["source_tree_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", value["source_tree_hash"]):
        issues.append("runtime source tree hash is invalid")
    return issues


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_runtime(root: Path, files: list[str], *, materialized: bool = False) -> list[str]:
    runtime_files = [name for name in files if name.startswith("desktop-runtime/")]
    if not runtime_files:
        return ["approved desktop runtime is missing"] if materialized else []
    issues = []
    present = {name[len(RUNTIME_ROOT):] for name in runtime_files if approved_name(name)}
    for required in sorted(REQUIRED - present):
        issues.append(f"runtime required file missing: {required}")
    expected_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    for name in runtime_files:
        if not approved_name(name):
            issues.append(f"{name}: unapproved runtime asset")
            continue
        path = root / name
        if path.is_symlink() or not path.is_file():
            issues.append(f"{name}: runtime must be a regular file")
            continue
        attr = subprocess.run(["git", "check-attr", "filter", "--", name], cwd=root,
                              capture_output=True, text=True)
        if attr.returncode or not attr.stdout.rstrip().endswith(": filter: lfs"):
            issues.append(f"{name}: runtime must be covered by committed Git LFS attributes")
        size = subprocess.run(["git", "cat-file", "-s", f":{name}"], cwd=root,
                              capture_output=True, text=True)
        if size.returncode:
            issues.append(f"{name}: runtime must be staged before verification")
            continue
        if not size.stdout.strip().isdigit() or int(size.stdout.strip()) > 256:
            issues.append(f"{name}: index contains ordinary binary data instead of an LFS pointer")
            continue
        stored = subprocess.run(["git", "show", f":{name}"], cwd=root, capture_output=True)
        pointer = parse_pointer(stored.stdout) if stored.returncode == 0 else None
        if pointer is None:
            issues.append(f"{name}: invalid staged LFS pointer")
            continue
        with path.open("rb") as source:
            head = source.read(256)
        local_pointer = parse_pointer(head)
        if local_pointer:
            if local_pointer != pointer:
                issues.append(f"{name}: working pointer disagrees with staged pointer")
            if materialized:
                issues.append(f"{name}: LFS object has not been downloaded")
            continue
        if path.stat().st_size != pointer[1] or hash_file(path) != pointer[0]:
            issues.append(f"{name}: runtime bytes disagree with staged LFS object")
        if name.endswith("/build-manifest.json"):
            issues.extend(manifest_issues(path.read_bytes(), expected_version))
        if name.endswith("/x2Stock.exe"):
            with path.open("rb") as source:
                header = source.read(64)
                if len(header) < 64 or header[:2] != b"MZ":
                    issues.append("runtime x2Stock.exe is not a Windows executable")
                    continue
                source.seek(int.from_bytes(header[60:64], "little"))
                pe = source.read(6)
            if pe[:4] != b"PE\0\0" or pe[4:] != b"\x64\x86":
                issues.append("runtime x2Stock.exe is not a Windows x64 PE")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--materialized", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode("utf-8").split("\0")
    issues = verify_runtime(root, [name for name in names if name], materialized=args.materialized)
    for issue in issues:
        print(f"FAIL: {issue}")
    print("FAIL: desktop runtime verification failed" if issues else "PASS: controlled runtime names, LFS pointers and available objects verified")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
