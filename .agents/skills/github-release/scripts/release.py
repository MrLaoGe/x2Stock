"""Local release preparation and exact-commit GitHub Actions publication (stdlib)."""
from __future__ import annotations

import argparse
import http.client
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.verify_repository import secret_issues


class ReleaseError(Exception):
    """Safe diagnostic; never include remote response bodies or credentials."""


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> Version:
        if not isinstance(value, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value):
            raise ReleaseError("Invalid three-part version")
        return cls(*map(int, value.split(".")))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def next_patch(self) -> Version:
        return Version(self.major, self.minor, self.patch + 1)


def git(root: Path, *args: str, optional: bool = False, raw: bool = False) -> str | None:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, encoding="utf-8")
    if result.returncode:
        if optional:
            return None
        raise ReleaseError("Git validation failed")
    return result.stdout if raw else result.stdout.strip()


def repo_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ReleaseError("Invalid repository identity")
    return value


def origin_repo(root: Path) -> str:
    origin = git(root, "remote", "get-url", "origin")
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?", origin or "")
    if not match:
        raise ReleaseError("Expected GitHub origin")
    return repo_name(match[1])


def current_version(root: Path) -> Version | None:
    path = root / "VERSION"
    return Version.parse(path.read_text(encoding="utf-8").strip()) if path.exists() else None


def compare_url(repo: str, previous: Version | None, version: Version) -> str:
    base = f"https://github.com/{repo}"
    return f"{base}/compare/v{previous}...v{version}" if previous else f"{base}/commits/v{version}"


def transition(previous: Version | None, version: Version, explicit: bool, reason: str) -> str:
    if previous is None:
        if version != Version(0, 1, 0):
            raise ReleaseError("First release must be 0.1.0")
        return "initial"
    if version <= previous:
        raise ReleaseError("Version must increase")
    if version == previous.next_patch():
        return "patch"
    if not explicit or not reason.strip():
        raise ReleaseError("Non-patch version changes require explicit authorization and reason")
    return "explicit"


def release_title(version: Version, notes: str) -> str:
    """Read the canonical title; the published initial release keeps its old name."""
    current = f"x2Stock {version}"
    if notes.startswith(f"# {current}\n"):
        return current
    if version == Version(0, 1, 0) and notes.startswith(f"# XXStock {version}\n"):
        return f"XXStock {version}"
    raise ReleaseError("Release note title does not match VERSION or project name")


def validate_notes(version: Version, notes: str) -> None:
    if not isinstance(notes, str):
        raise ReleaseError("Release note title does not match VERSION")
    release_title(version, notes)
    if re.search(r"\bTODO\b|\bTBD\b|待填写|占位", notes, re.I):
        raise ReleaseError("Release notes contain placeholders")
    if "## 验证结果" not in notes or not any(f"## {name}" in notes for name in ("新增功能", "优化改进", "问题修复", "兼容与升级说明")):
        raise ReleaseError("Release notes require actual changes and verification")
    if secret_issues(notes):
        raise ReleaseError("Release notes failed public asset checks")


def prepare(root: Path, source: Path, repository: str | None = None, requested: str | None = None,
            allow_version_change: bool = False, reason: str = "") -> dict:
    previous = current_version(root)
    version = Version.parse(requested) if requested else previous.next_patch() if previous else Version(0, 1, 0)
    change = transition(previous, version, allow_version_change, reason)
    repository = repo_name(repository) if repository else origin_repo(root)
    directory = root / "docs/releases"
    note_path, meta_path = directory / f"{version}.md", directory / f"{version}.json"
    if note_path.exists() or meta_path.exists():
        raise ReleaseError("Release materials already exist; recover instead of overwriting")
    notes = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    title = f"# x2Stock {version}"
    if notes.startswith(title + "\n"):
        notes = notes[len(title):].lstrip()
    notes = f"{title}\n\n{notes}\n\n[版本比较／提交历史]({compare_url(repository, previous, version)})\n"
    validate_notes(version, notes)
    if secret_issues(reason):
        raise ReleaseError("Version reason failed public asset checks")
    metadata = {"version": str(version), "previous_version": str(previous) if previous else None,
                "change": change, "reason": reason, "repository": repository}
    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else "# 更新记录\n\n每次正式主线更新均保存版本摘要及中文说明。\n"
    overview = next((line.strip() for line in notes.splitlines()[2:] if line.strip() and not line.startswith("#")), "")[:600]
    entry = f"## {version}\n\n{overview}\n\n[完整说明](docs/releases/{version}.md) · [版本比较／提交历史]({compare_url(repository, previous, version)})\n\n"
    split = changelog.find("\n## ")
    position = split + 1 if split >= 0 else len(changelog)
    changelog = changelog[:position].rstrip() + "\n\n" + entry + changelog[position:]
    directory.mkdir(parents=True, exist_ok=True)
    note_path.write_text(notes, encoding="utf-8", newline="\n")
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    changelog_path.write_text(changelog.rstrip() + "\n", encoding="utf-8", newline="\n")
    (root / "VERSION").write_text(f"{version}\n", encoding="utf-8", newline="\n")
    return metadata


def check(root: Path, base_sha: str | None = None) -> dict:
    version = current_version(root)
    if version is None:
        raise ReleaseError("VERSION is required")
    directory = root / "docs/releases"
    meta = json.loads((directory / f"{version}.json").read_text(encoding="utf-8"))
    previous = Version.parse(meta["previous_version"]) if meta["previous_version"] is not None else None
    if meta["version"] != str(version) or meta["change"] != transition(previous, version, meta["change"] == "explicit", meta["reason"]):
        raise ReleaseError("Release metadata and version transition disagree")
    repository = repo_name(meta["repository"])
    notes = (directory / f"{version}.md").read_text(encoding="utf-8")
    validate_notes(version, notes)
    comparison = compare_url(repository, previous, version)
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if comparison not in notes or f"## {version}\n" not in changelog or f"(docs/releases/{version}.md)" not in changelog:
        raise ReleaseError("Release note comparison or changelog index missing")
    if secret_issues(meta["reason"]):
        raise ReleaseError("Version reason failed public asset checks")
    if base_sha is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
            raise ReleaseError("Invalid base SHA")
        if base_sha != "0" * 40:
            git(root, "cat-file", "-e", f"{base_sha}^{{commit}}")
            old = git(root, "show", f"{base_sha}:VERSION", optional=True)
        else:
            old = None
        base_version = Version.parse(old) if old is not None else None
        if base_version != previous:
            raise ReleaseError("Main update omitted a new version or has an incorrect previous version")
    return {"version": version, "previous": previous, "repository": repository, "notes": notes, "compare_url": comparison}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubAPI:
    def __init__(self, repository: str, token: str):
        self.repository = repo_name(repository)
        if not token or "\n" in token or "\r" in token:
            raise ReleaseError("Missing or invalid GitHub credential")
        self._token = token

    def request(self, method: str, path: str, payload: dict | None = None, missing_ok: bool = False):
        request = urllib.request.Request(f"https://api.github.com/repos/{self.repository}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None,
            headers={"Authorization": f"Bearer {self._token}", "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"}, method=method)
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ReleaseError("GitHub response too large")
            return json.loads(raw)
        except urllib.error.HTTPError as error:
            error.close()
            if error.code == 404 and missing_ok:
                return None
            raise ReleaseError(f"GitHub request failed (HTTP {error.code}); inspect Actions and recover") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ReleaseError("GitHub request outcome uncertain; inspect remote state before rerun") from None
        except http.client.HTTPException:
            raise ReleaseError("GitHub protocol failure; inspect remote state before rerun") from None
        except (ValueError, UnicodeError):
            raise ReleaseError("Invalid GitHub response") from None


def tag_commit(api, tag: str) -> str | None:
    ref = api.request("GET", f"/git/ref/tags/{urllib.parse.quote(tag, safe='')}", missing_ok=True)
    if ref is None:
        return None
    obj = ref["object"]
    for _ in range(5):
        if obj["type"] == "commit" and re.fullmatch(r"[0-9a-f]{40}", obj["sha"]):
            return obj["sha"]
        if obj["type"] != "tag" or not re.fullmatch(r"[0-9a-f]{40}", obj["sha"]):
            break
        obj = api.request("GET", f"/git/tags/{obj['sha']}")["object"]
    raise ReleaseError("Invalid or deeply nested release tag")


def validate_release(release: dict, version: Version, notes: str) -> None:
    expected = {"tag_name": f"v{version}", "name": release_title(version, notes), "body": notes,
                "draft": False, "prerelease": version.major == 0}
    if any(release.get(key) != value for key, value in expected.items()):
        raise ReleaseError("Existing Release conflicts with canonical materials; no overwrite allowed")


def publish(root: Path, environment: dict, api=None) -> dict:
    if environment.get("GITHUB_ACTIONS") != "true" or environment.get("GITHUB_EVENT_NAME") != "push" or environment.get("GITHUB_REF") != "refs/heads/main":
        raise ReleaseError("Publish only allowed inside the main push workflow")
    event = json.loads(Path(environment["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    sha = environment.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != git(root, "rev-parse", "HEAD") or sha != event.get("after") or event.get("ref") != "refs/heads/main" or event.get("deleted") or event.get("before") == sha:
        raise ReleaseError("Workflow, event and checked-out commit must match")
    if git(root, "status", "--porcelain"):
        raise ReleaseError("Publishing requires a clean checkout")
    info = check(root, event["before"])
    if event["before"] != "0" * 40:
        if git(root, "merge-base", "--is-ancestor", event["before"], sha, optional=True) is None:
            raise ReleaseError("Main history was rewritten; publication stopped")
        # Published notes and metadata are immutable, including older versions.
        historical = git(root, "ls-tree", "-r", "--name-only", event["before"], "docs/releases").splitlines()
        for path in historical:
            if git(root, "show", f"{event['before']}:{path}", raw=True) != git(root, "show", f"{sha}:{path}", raw=True, optional=True):
                raise ReleaseError("Historical release materials were modified or removed")
    repo, version, previous, notes = info["repository"], info["version"], info["previous"], info["notes"]
    if repo != environment.get("GITHUB_REPOSITORY") or repo != event.get("repository", {}).get("full_name"):
        raise ReleaseError("Workflow repository does not match release metadata")
    api = api or GitHubAPI(repo, environment.get("GITHUB_TOKEN", ""))
    if previous is not None:
        prior_sha = tag_commit(api, f"v{previous}")
        if prior_sha is None or git(root, "merge-base", "--is-ancestor", prior_sha, event["before"], optional=True) is None:
            raise ReleaseError("Previous release tag is missing or outside this history")
        if git(root, "show", f"{prior_sha}:VERSION") != str(previous):
            raise ReleaseError("Previous tag version conflicts")
        prior_notes = git(root, "show", f"{prior_sha}:docs/releases/{previous}.md", raw=True)
        if prior_notes != git(root, "show", f"{sha}:docs/releases/{previous}.md", raw=True):
            raise ReleaseError("Previously released notes were modified")
        prior_release = api.request("GET", f"/releases/tags/v{previous}", missing_ok=True)
        if prior_release is None:
            raise ReleaseError("Previous publication incomplete; rerun its original workflow first")
        validate_release(prior_release, previous, prior_notes)
    tag = f"v{version}"
    existing_sha = tag_commit(api, tag)
    if existing_sha is not None and existing_sha != sha:
        raise ReleaseError("Existing tag points to a different commit; no overwrite allowed")
    release = api.request("GET", f"/releases/tags/{tag}", missing_ok=True)
    reused = release is not None
    if release is not None:
        validate_release(release, version, notes)
        if existing_sha is None:
            raise ReleaseError("Existing Release has no verified tag")
    else:
        if existing_sha is None:
            api.request("POST", "/git/refs", {"ref": f"refs/tags/{tag}", "sha": sha})
        if tag_commit(api, tag) != sha:
            raise ReleaseError("Tag verification failed")
        api.request("POST", "/releases", {"tag_name": tag, "target_commitish": sha, "name": f"x2Stock {version}",
            "body": notes, "draft": False, "prerelease": version.major == 0, "make_latest": "false" if version.major == 0 else "true"})
    release = api.request("GET", f"/releases/tags/{tag}")
    validate_release(release, version, notes)
    url = f"https://github.com/{repo}/releases/tag/{tag}"
    if tag_commit(api, tag) != sha or release.get("html_url") != url:
        raise ReleaseError("Published release identity verification failed")
    return {"version": str(version), "repository": repo, "sha": sha, "tag": tag,
            "release_url": url, "compare_url": info["compare_url"], "notes": release["body"], "reused": reused}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--notes-file", type=Path, required=True)
    preparation.add_argument("--repository")
    preparation.add_argument("--version")
    preparation.add_argument("--allow-version-change", action="store_true")
    preparation.add_argument("--reason", default="")
    validation = commands.add_parser("check")
    validation.add_argument("--base-sha")
    publication = commands.add_parser("publish")
    publication.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(ROOT, args.notes_file, args.repository, args.version, args.allow_version_change, args.reason)
        elif args.command == "check":
            result = check(ROOT, args.base_sha)
        else:
            result = publish(ROOT, dict(os.environ))
            args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: str(value) if isinstance(value, Version) else value for key, value in result.items() if key != "notes"}, ensure_ascii=False))
        return 0
    except ReleaseError as error:
        print(f"Release failed: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        print("Release failed: invalid or missing input; no sensitive details logged", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
