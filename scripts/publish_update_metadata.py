"""Publish immutable update metadata after the exact-SHA Windows archive gate."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "MrLaoGe/x2Stock"
MAX_METADATA = 16384
FIELDS = {"schema", "repository", "version", "source_sha", "source_tree_hash", "archive_url", "archive_sha256", "archive_size", "runtime_subdir"}


class MetadataError(Exception):
    """Safe failure: never include provider content or credentials."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubAPI:
    def __init__(self, token: str):
        if not token or any(ch in token for ch in "\r\n"):
            raise MetadataError("missing GitHub credential")
        self.token = token

    def request(self, method: str, path: str, payload: bytes | None = None, *, upload=False):
        host = "https://uploads.github.com" if upload else "https://api.github.com"
        request = urllib.request.Request(f"{host}/repos/{REPOSITORY}{path}", data=payload,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"}, method=method)
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise MetadataError("GitHub response too large")
            return json.loads(raw)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException, ValueError):
            raise MetadataError("GitHub operation failed or outcome uncertain; inspect remote state before rerun") from None


def decode_metadata(raw: bytes, sha: str, version: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{40}", sha) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise MetadataError("invalid exact commit or canonical version")
    if len(raw) > MAX_METADATA:
        raise MetadataError("metadata exceeds size limit")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise MetadataError("invalid metadata JSON") from None
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise MetadataError("metadata must use the nine-field contract")
    if (type(value["schema"]) is not int or value["schema"] != 1 or
        value["repository"] != REPOSITORY or value["version"] != version or value["source_sha"] != sha or
        value["archive_url"] != f"https://codeload.github.com/{REPOSITORY}/zip/{sha}" or
        value["runtime_subdir"] != "desktop-runtime/win-x64" or
        type(value["archive_size"]) is not int or not 0 < value["archive_size"] <= 512 * 1024 * 1024):
        raise MetadataError("metadata identity or archive limits do not match the gated commit")
    for key in ("source_tree_hash", "archive_sha256"):
        if not isinstance(value[key], str) or not re.fullmatch(r"[a-f0-9]{64}", value[key]):
            raise MetadataError("metadata digest is invalid")
    return value


def exact_tag(api, tag: str) -> str:
    ref = api.request("GET", f"/git/ref/tags/{urllib.parse.quote(tag, safe='')}")
    obj = ref.get("object", {})
    for _ in range(5):
        sha = obj.get("sha", "")
        if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
            break
        if obj.get("type") == "commit":
            return sha
        if obj.get("type") != "tag":
            break
        obj = api.request("GET", f"/git/tags/{sha}").get("object", {})
    raise MetadataError("release tag could not be verified")


def verify_asset(asset: dict, name: str, raw: bytes) -> None:
    if (not isinstance(asset, dict) or asset.get("name") != name or asset.get("state") != "uploaded" or
        type(asset.get("id")) is not int or asset["id"] <= 0 or
        asset.get("size") != len(raw) or asset.get("digest") != "sha256:" + hashlib.sha256(raw).hexdigest()):
        raise MetadataError("existing or uploaded metadata asset conflicts; no overwrite allowed")


def publish_metadata(raw: bytes, receipt: dict, sha: str, version: str, api) -> dict:
    decode_metadata(raw, sha, version)
    tag = f"v{version}"
    url = f"https://github.com/{REPOSITORY}/releases/tag/{tag}"
    if (not isinstance(receipt, dict) or not isinstance(receipt.get("notes"), str) or receipt.get("repository") != REPOSITORY or receipt.get("sha") != sha or
        receipt.get("version") != version or receipt.get("tag") != tag or receipt.get("release_url") != url):
        raise MetadataError("release receipt does not match exact metadata commit")
    if exact_tag(api, tag) != sha:
        raise MetadataError("release tag does not match exact metadata commit")
    release = api.request("GET", f"/releases/tags/{tag}")
    if not isinstance(release, dict):
        raise MetadataError("invalid release response")
    release_id = release.get("id")
    if (type(release_id) is not int or release_id <= 0 or release.get("tag_name") != tag or
        release.get("draft") is not False or release.get("prerelease") is not version.startswith("0.") or
        release.get("html_url") != url or release.get("body") != receipt.get("notes")):
        raise MetadataError("release identity conflicts with publication receipt")
    name = f"x2Stock-{version}-update.json"
    assets = api.request("GET", f"/releases/{release_id}/assets?per_page=100")
    if not isinstance(assets, list) or len(assets) >= 100 or any(not isinstance(asset, dict) for asset in assets):
        raise MetadataError("unexpected release asset listing")
    matches = [asset for asset in assets if asset.get("name") == name]
    # There must be a single metadata contract for this release, never another version's updater payload.
    if len(matches) > 1 or any(asset.get("name", "").endswith("-update.json") and asset.get("name") != name for asset in assets):
        raise MetadataError("duplicate or conflicting updater metadata assets")
    reused = bool(matches)
    if matches:
        asset = matches[0]
    else:
        asset = api.request("POST", f"/releases/{release_id}/assets?name={urllib.parse.quote(name, safe='')}", raw, upload=True)
    verify_asset(asset, name, raw)
    verified = api.request("GET", f"/releases/assets/{asset['id']}")
    verify_asset(verified, name, raw)
    final_assets = api.request("GET", f"/releases/{release_id}/assets?per_page=100")
    if not isinstance(final_assets, list) or len(final_assets) >= 100 or any(not isinstance(asset, dict) for asset in final_assets):
        raise MetadataError("unexpected final release asset listing")
    matching = [item for item in final_assets if item.get("name", "").endswith("-update.json")]
    if len(matching) != 1 or matching[0].get("id") != asset["id"]:
        raise MetadataError("final updater metadata identity is not unique")
    verify_asset(matching[0], name, raw)
    if exact_tag(api, tag) != sha:
        raise MetadataError("release tag changed during metadata publication")
    return {"asset": name, "release_id": release_id, "sha": sha, "reused": reused}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--release-receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        env = os.environ
        if env.get("GITHUB_ACTIONS") != "true" or env.get("GITHUB_EVENT_NAME") != "push" or env.get("GITHUB_REF") != "refs/heads/main" or env.get("GITHUB_REPOSITORY") != REPOSITORY:
            raise MetadataError("metadata publication only allowed in the main push workflow")
        sha = env.get("GITHUB_SHA", "")
        if not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise MetadataError("invalid workflow commit")
        root = Path(__file__).resolve().parents[1]
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        if head != sha or event.get("after") != sha or event.get("ref") != "refs/heads/main" or event.get("deleted") or event.get("repository", {}).get("full_name") != REPOSITORY:
            raise MetadataError("event and checkout must bind the exact main commit")
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
            raise MetadataError("invalid canonical version")
        if args.metadata.stat().st_size > MAX_METADATA or args.release_receipt.stat().st_size > 2_000_000:
            raise MetadataError("publication materials too large")
        result = publish_metadata(args.metadata.read_bytes(), json.loads(args.release_receipt.read_text(encoding="utf-8")), sha, version, GitHubAPI(env.get("GITHUB_TOKEN", "")))
        print(f"PASS: verified immutable update metadata {result['asset']} (reused={result['reused']})")
        return 0
    except (MetadataError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("FAIL: update metadata publication rejected; no overwrite or retry performed; inspect Actions and remote asset state")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
