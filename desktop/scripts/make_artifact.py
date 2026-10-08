from pathlib import Path
import hashlib
import shutil
import subprocess
import zipfile

source = Path(__file__).parents[1] / "release" / "win-unpacked"
repository = Path(__file__).parents[2]
output = Path(r"E:/XXStock/.local/artifacts/windows-preview")
output.mkdir(parents=True, exist_ok=True)
source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
artifact_stem = f"x2Stock-preview-{source_sha[:8]}-win-x64"
stage = output / artifact_stem
archive = output / f"{artifact_stem}.zip"
readme = output / f"{artifact_stem}.README.txt"
checksum_file = output / f"{artifact_stem}.zip.sha256"
if stage.exists():
    raise FileExistsError(f"refusing to replace existing artifact directory: {stage}")
if archive.exists():
    raise FileExistsError(f"refusing to replace existing artifact archive: {archive}")
if readme.exists():
    raise FileExistsError(f"refusing to replace existing artifact notes: {readme}")
if checksum_file.exists():
    raise FileExistsError(f"refusing to replace existing checksum: {checksum_file}")
shutil.copytree(source, stage)
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
    for path in stage.rglob("*"):
        if path.is_file():
            bundle.write(path, path.relative_to(stage))

digest = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum_file.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
tree_hash = hashlib.sha256()
for base in (repository / "frontend", repository / "desktop"):
    for path in sorted(base.rglob("*")):
        if path.is_file() and not any(part in {"node_modules", "dist", "release", "renderer"} for part in path.parts):
            tree_hash.update(path.relative_to(repository).as_posix().encode("utf-8"))
            tree_hash.update(path.read_bytes())
source_tree_sha = tree_hash.hexdigest()
readme.write_text(
    f"""x2Stock Windows preview
=======================

Source Git SHA: {source_sha}
Frontend and desktop source tree SHA-256: {source_tree_sha}
Target: Windows x64, Electron 44.7.0, electron-builder 26.15.3
Artifact: {archive.name}
SHA-256: {digest}

Usage: extract the zip, then double-click x2Stock.exe. No Node, Python, Docker, database, or installer is required at runtime. This is a preview build and is unsigned. Automatic updates are not included in this artifact; do not treat it as a release asset.

Included files are the Electron runtime and asar application resources. New installs use %APPDATA%/x2Stock with separate profile, session, cache and downloads directories. Existing previews safely reuse %APPDATA%/XXStock when a legacy profile/session exists, preserving language and settings; that directory is never deleted or copied. Do not run old and renamed previews concurrently against the same legacy profile. The physical E:/XXStock artifact location is retained by request.
""",
    encoding="utf-8",
)
print(archive, archive.stat().st_size, digest)
