"""Launch the shipped canonical BAT from a private, offline Windows QA copy."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from urllib.parse import unquote, urlsplit

try:
    from scripts.verify_desktop_runtime import canonical_launcher, hash_file, REQUIRED, RUNTIME_ROOT
except ModuleNotFoundError:
    from verify_desktop_runtime import canonical_launcher, hash_file, REQUIRED, RUNTIME_ROOT


def owned_pids(executable: Path, env: dict) -> list[int]:
    query_env = {**env, "X2STOCK_SMOKE_EXE": str(executable)}
    command = ("@(Get-CimInstance Win32_Process -Filter \"Name='x2Stock.exe'\" | "
               "Where-Object { [string]::Equals($_.ExecutablePath,$env:X2STOCK_SMOKE_EXE,[StringComparison]::OrdinalIgnoreCase) } | "
               "ForEach-Object { [int]$_.ProcessId }) | ConvertTo-Json -Compress")
    raw = subprocess.check_output(["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", command], env=query_env, timeout=15)
    value = json.loads(raw) if raw.strip() else []
    return [value] if type(value) is int else value


def smoke(root: Path) -> dict:
    if os.name != "nt":
        raise ValueError("Windows QA host required")
    root = root.resolve(strict=True)
    launcher = root / "启动.bat"
    runtime = root / RUNTIME_ROOT
    if not canonical_launcher(launcher.read_bytes()) or not runtime.is_dir():
        raise ValueError("Complete canonical project required")
    files = {path.relative_to(runtime).as_posix() for path in runtime.rglob("*") if path.is_file()}
    if files != REQUIRED or any(path.is_symlink() for path in runtime.rglob("*")):
        raise ValueError("Exact regular runtime resources required")
    expected = {name: hash_file(runtime / name) for name in REQUIRED}
    temp = Path(tempfile.gettempdir()).resolve(strict=True)
    realm = Path(tempfile.mkdtemp(prefix="x2stock-fixture-", dir=temp)).resolve(strict=True)
    if realm.parent != temp or not realm.name.startswith("x2stock-fixture-"):
        raise ValueError("Unsafe QA realm")
    executable = realm / "中文 空格项目" / RUNTIME_ROOT / "x2Stock.exe"
    env = os.environ.copy()
    # Development URLs and helper modes must never leak into the packaged QA.
    for key in ("X2STOCK_DEV_SERVER_URL", "ELECTRON_RUN_AS_NODE"):
        env.pop(key, None)
    process = None
    try:
        project = realm / "中文 空格项目"
        project.mkdir()
        shutil.copytree(runtime, project / RUNTIME_ROOT)
        shutil.copy2(launcher, project / "启动.bat")
        nonce = secrets.token_hex(32)
        (realm / ".x2stock-test-fixture.json").write_text(json.dumps({"schema": 1, "root": str(realm), "nonce": nonce}), encoding="utf-8")
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        env.update({"X2STOCK_TEST_REALM": str(realm), "X2STOCK_TEST_NONCE": nonce,
                    "X2STOCK_TEST_CDP_PORT": str(port), "X2STOCK_TEST_OFFLINE": "1"})
        process = subprocess.Popen([os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "启动.bat"],
                                   cwd=project, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        process.wait(timeout=15)
        if process.returncode:
            raise ValueError("Root BAT failed")
        deadline = time.monotonic() + 40
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise ValueError("Isolated renderer did not start")
            time.sleep(0.2)
        raw = subprocess.check_output(["node", str(Path(__file__).with_suffix(".mjs")), str(port)], env=env, timeout=40, stderr=subprocess.PIPE)
        result = json.loads(raw)
        if result["pid"] not in owned_pids(executable, env):
            raise ValueError("Renderer does not belong to the copied QA executable")
        page_url = urlsplit(result["url"])
        actual_page = Path(unquote(page_url.path).removeprefix("/")).resolve()
        expected_page = (project / RUNTIME_ROOT / "resources/app.asar/renderer/index.html").resolve()
        if page_url.scheme != "file" or page_url.netloc or actual_page != expected_page:
            raise ValueError("Renderer URL is not the copied packaged page")
        if result.get("offlineRulesVerified") is not True or result.get("offlineUpdaterVerified") is not True:
            raise ValueError("Offline DNS resolver was not verified")
        profile_root = realm / "state/appdata"
        if (profile_root / "XXStock").exists() or not (profile_root / "x2Stock/profile").is_dir():
            raise ValueError("Fresh isolated profile branch was not used")
        if any(hash_file(project / RUNTIME_ROOT / name) != digest for name, digest in expected.items()):
            raise ValueError("QA mutated shipped runtime")
        result.update({"offline_fixture": True, "fresh_profile_verified": True, "runtime_files": len(files), "exe_sha256": expected["x2Stock.exe"]})
        return result
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        for pid in owned_pids(executable, env):
            subprocess.run(["taskkill.exe", "/PID", str(pid), "/T", "/F"], creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
        # Only the checked private child of OS temp is ever recursively removed.
        if realm.parent == temp and realm.name.startswith("x2stock-fixture-") and not owned_pids(executable, env):
            for attempt in range(10):
                try:
                    shutil.rmtree(realm)
                    break
                except OSError:
                    if attempt == 9:
                        raise
                    time.sleep(0.2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        result = smoke(args.root)
        if args.receipt:
            args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: root BAT started owned packaged renderer offline ({result['rootLength']} chars, {result['runtime_files']} runtime files)")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print("FAIL: isolated Windows root BAT / packaged renderer acceptance failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
