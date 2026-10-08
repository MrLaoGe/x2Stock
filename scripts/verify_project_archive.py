"""Verify the actual exact-SHA GitHub source archive before update publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata
import urllib.request
import zipfile

try:
    from scripts.verify_desktop_runtime import approved_name, canonical_launcher, manifest_issues, parse_pointer, REQUIRED, RUNTIME_ROOT, COMPILED_SUFFIXES
    from scripts.verify_repository import PRIVATE_ROOTS, PRIVATE_SUFFIXES, DATABASE_FILE
except ModuleNotFoundError:
    from verify_desktop_runtime import approved_name, canonical_launcher, manifest_issues, parse_pointer, REQUIRED, RUNTIME_ROOT, COMPILED_SUFFIXES
    from verify_repository import PRIVATE_ROOTS, PRIVATE_SUFFIXES, DATABASE_FILE

REPOSITORY = "MrLaoGe/x2Stock"
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_EXPANDED = 1200 * 1024 * 1024


class ArchiveError(Exception):
    """Safe archive failure; do not report arbitrary remote contents."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def source_file(name: str) -> bool:
    return (name == "VERSION" or name.startswith(("frontend/", "desktop/"))) and not (
        set(name.split("/")) & {"node_modules", "dist", "release", "renderer", "build", "__pycache__"}
    ) and not name.endswith((".pyc", ".tsbuildinfo"))


def source_hash(hashes: dict[str, str]) -> str:
    lines = "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes, key=lambda value: value.encode("utf-8")))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def safe_name(name: str) -> str:
    value = name.removesuffix("/")
    parts = value.split("/")
    if not value or len(value) > 240 or any(ch in name for ch in "\\:\0<>\"|?*") or any(ord(ch) < 32 for ch in name) or unicodedata.normalize("NFC", value) != value:
        raise ArchiveError("invalid archive path")
    if any(not part or part in {".", ".."} or part.endswith((".", " ")) or
           re.match(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", part, re.I) for part in parts):
        raise ArchiveError("unsafe Windows archive path")
    return value


def inspect_archive(archive: Path, sha: str, version: str, *, extract: Path | None = None) -> dict:
    if not re.fullmatch(r"[a-f0-9]{40}", sha) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise ArchiveError("invalid exact SHA or version")
    prefix = f"x2Stock-{sha}"
    hashes, runtime, seen, contents = {}, {}, set(), {}
    expanded = source_expanded = 0
    with zipfile.ZipFile(archive) as bundle:
        if len(bundle.infolist()) > 5000:
            raise ArchiveError("too many archive entries")
        for entry in bundle.infolist():
            value = safe_name(entry.filename)
            key = value.casefold()
            if key in seen:
                raise ArchiveError("duplicate Windows archive path")
            seen.add(key)
            mode = entry.external_attr >> 16 & 0o170000
            if mode not in {0, 0o040000, 0o100000} or entry.flag_bits & 1:
                raise ArchiveError("unsupported archive entry")
            if value.split("/")[0] != prefix:
                raise ArchiveError("archive prefix does not bind exact SHA")
            if entry.is_dir():
                continue
            name = value[len(prefix) + 1:]
            parts = name.lower().split("/")
            basename = parts[-1]
            if (not name or parts[0] in PRIVATE_ROOTS or set(parts) & {".git", "node_modules"} or
                Path(basename).suffix in PRIVATE_SUFFIXES or DATABASE_FILE.search(basename) or
                basename in {"token.json", ".env"} or ".local." in basename or
                (basename.startswith(".env.") and basename != ".env.example")):
                raise ArchiveError("private or unexpected archive path")
            if Path(basename).suffix in COMPILED_SUFFIXES and not approved_name(name):
                raise ArchiveError("compiled asset outside approved runtime")
            expanded += entry.file_size
            if entry.file_size > MAX_ARCHIVE or expanded > MAX_EXPANDED:
                raise ArchiveError("archive expanded size limit exceeded")
            if source_file(name) and entry.file_size > 8 * 1024 * 1024:
                raise ArchiveError("source file exceeds size limit")
            if source_file(name):
                source_expanded += entry.file_size
                if source_expanded > 64 * 1024 * 1024:
                    raise ArchiveError("source tree exceeds size limit")
            digest = hashlib.sha256()
            head = bytearray()
            destination = None
            if name.startswith("desktop-runtime/"):
                if not approved_name(name):
                    raise ArchiveError("unapproved runtime asset in archive")
                if extract:
                    destination = extract / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
            if name in {"VERSION", "启动.bat", "desktop-runtime/win-x64/resources/build-manifest.json"}:
                if entry.file_size > 16384:
                    raise ArchiveError("manifest or launcher too large")
                contents[name] = bundle.read(entry)
            output = destination.open("xb") if destination else None
            try:
                with bundle.open(entry) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                        if len(head) < 256:
                            head.extend(chunk[:256 - len(head)])
                        if output:
                            output.write(chunk)
            finally:
                if output:
                    output.close()
            if name.startswith(RUNTIME_ROOT):
                if parse_pointer(bytes(head)):
                    raise ArchiveError("source archive contains LFS pointer instead of executable resources")
                runtime[name[len(RUNTIME_ROOT):]] = {"size": entry.file_size, "sha256": digest.hexdigest()}
            if source_file(name):
                hashes[name] = digest.hexdigest()
    if REQUIRED - set(runtime) or "VERSION" not in contents or "启动.bat" not in contents:
        raise ArchiveError("project archive lacks complete runtime, version or root launcher")
    if contents["VERSION"].decode("utf-8").strip() != version:
        raise ArchiveError("archive VERSION mismatch")
    manifest_bytes = contents["desktop-runtime/win-x64/resources/build-manifest.json"]
    if manifest_issues(manifest_bytes, version):
        raise ArchiveError("invalid runtime build manifest")
    manifest = json.loads(manifest_bytes)
    identity = source_hash(hashes)
    if manifest["source_tree_hash"] != identity:
        raise ArchiveError("bundled runtime does not match archived source tree")
    with zipfile.ZipFile(archive) as bundle, bundle.open(f"{prefix}/{RUNTIME_ROOT}x2Stock.exe") as executable:
        header = executable.read(64)
        offset = int.from_bytes(header[60:64], "little")
        if len(header) != 64 or header[:2] != b"MZ" or not 64 <= offset <= 1024 * 1024:
            raise ArchiveError("archive executable is not a bounded Windows PE")
        executable.read(offset - 64)
        if executable.read(6) != b"PE\0\0\x64\x86":
            raise ArchiveError("archive executable is not Windows x64")
    if not canonical_launcher(contents["启动.bat"]):
        raise ArchiveError("launcher must run shipped runtime without network or build tools")
    if extract:
        (extract / "启动.bat").write_bytes(contents["启动.bat"])
    return {"source_tree_hash": identity, "runtime_files": len(runtime), "expanded_bytes": expanded}


def download(sha: str, destination: Path) -> tuple[str, int]:
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ArchiveError("invalid exact SHA")
    url = f"https://codeload.github.com/{REPOSITORY}/zip/{sha}"
    request = urllib.request.Request(url, headers={"User-Agent": "x2stock-archive-verifier"})
    digest, size = hashlib.sha256(), 0
    started = time.monotonic()
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response, destination.open("xb") as output:
        if response.status != 200:
            raise ArchiveError("official archive download failed")
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            if time.monotonic() - started > 600:
                raise ArchiveError("archive download deadline exceeded")
            size += len(chunk)
            if size > MAX_ARCHIVE:
                raise ArchiveError("project archive exceeds download limit")
            digest.update(chunk)
            output.write(chunk)
    return digest.hexdigest(), size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    try:
        if args.download:
            digest, size = download(args.sha, args.archive)
        else:
            digest, size = hashlib.sha256(args.archive.read_bytes()).hexdigest(), args.archive.stat().st_size
        if size > MAX_ARCHIVE:
            raise ArchiveError("project archive exceeds download limit")
        result = inspect_archive(args.archive, args.sha, args.version, extract=args.extract)
        if args.metadata:
            metadata = {"schema": 1, "repository": REPOSITORY, "version": args.version,
                        "source_sha": args.sha, "source_tree_hash": result["source_tree_hash"],
                        "archive_url": f"https://codeload.github.com/{REPOSITORY}/zip/{args.sha}",
                        "archive_sha256": digest, "archive_size": size, "runtime_subdir": "desktop-runtime/win-x64"}
            args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: exact-SHA source archive contains {result['runtime_files']} materialized runtime files and matching source identity")
        return 0
    except (ArchiveError, OSError, ValueError, zipfile.BadZipFile):
        print("FAIL: source archive validation failed; no updater metadata accepted")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
