"""Validate the public x2Stock product boundary without network access."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from scripts.verify_desktop_runtime import approved_name, canonical_launcher, COMPILED_SUFFIXES, verify_runtime
except ModuleNotFoundError:
    from verify_desktop_runtime import approved_name, canonical_launcher, COMPILED_SUFFIXES, verify_runtime

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md", "CONTRIBUTING.md", "LICENSE", ".env.example", "VERSION", "CHANGELOG.md",
    "启动.bat", "config/config.example.json", "docs/README.md", "docs/repository-boundary.md",
    "docs/architecture.md", "docs/contracts.md", "docs/configuration.md", "docs/data/sources.md",
    "docs/releases/0.1.1.md", "docs/releases/0.1.1.json", "scripts/verify_repository.py",
    "scripts/verify_desktop_runtime.py", "scripts/verify_project_archive.py",
}
PRIVATE_PREFIXES = (".agents/", ".github/", "docs/adr/", "docs/development/", "docs/modules/", ".worktrees/", ".local/")
PRIVATE_ROOTS = {".local", ".worktrees", "runtime", "data", "logs", "outputs", "backups"}
PRIVATE_FILES = {"AGENTS.md", "docs/project-plan.md", "docs/roadmap.md", "docs/ui-design.md", "docs/agents.md"}
PRIVATE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".duckdb", ".parquet", ".csv", ".xlsx", ".xls", ".docx", ".pdf", ".log", ".pem", ".key"}
DATABASE_FILE = re.compile(r"\.(?:db|sqlite|sqlite3)(?:-(?:wal|shm|journal))?$|\.duckdb(?:\.wal)?$", re.I)
TEXT_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".toml", ".example", ".ts", ".tsx", ".js", ".jsx", ".css", ".html", ".cjs", ".mjs", ".bat", ".ps1", ".txt"}
SECRET_RULES = (
    ("API key pattern", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b")),
    ("GitHub credential pattern", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("long hexadecimal secret", re.compile(r"\b[0-9a-fA-F]{48,128}\b")),
    ("credential in URL", re.compile(r"[?&](?:token|api_key|access_token|key)=[^\s&<>\"')]+", re.I)),
    ("private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)
ASSIGNMENT = re.compile(r"(?im)[\"']?\b(?:TUSHARE_TOKEN|AI_API_KEY|OPENAI_API_KEY|VOCECHAT_API_KEY|POSTGRES_PASSWORD|api_key|access_token|password|token)[\"']?[ \t]*[:=][ \t]*[\"']?([A-Za-z0-9_./+=:-]+)")
ENV_NAMES = {"TUSHARE_TOKEN", "AI_API_KEY", "OPENAI_API_KEY", "VOCECHAT_API_KEY", "POSTGRES_PASSWORD", "DATABASE_URL"}
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*[\"'])?\s*\)")


def files() -> list[str]:
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, check=True, capture_output=True)
    return sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})


def secret_issues(text: str, python_code: bool = False) -> list[str]:
    """Return category/line findings without returning credential values."""
    issues = []
    for label, pattern in SECRET_RULES:
        for match in pattern.finditer(text):
            issues.append(f"{label} at line {text.count(chr(10), 0, match.start()) + 1}")
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1)
        if value in ENV_NAMES or value.lower() in {"token", "api_key", "access_token"}:
            continue
        if value.lower().startswith(("example", "placeholder", "replace_")):
            continue
        issues.append(f"nonempty secret assignment at line {text.count(chr(10), 0, match.start()) + 1}")
    return issues


def link_issues(name: str, content: str, known: set[str]) -> list[str]:
    issues = []
    content = re.sub(r"```.*?```", "", content, flags=re.S)
    for match in LINK.finditer(content):
        target = match.group(1).strip("<>")
        parts = urlsplit(target)
        if parts.scheme:
            if parts.scheme not in {"http", "https", "mailto"}: issues.append("nonportable link scheme")
            continue
        if not parts.path: continue
        decoded = unquote(parts.path).replace("\\", "/")
        if decoded.startswith("/"): issues.append("absolute local link"); continue
        path = (ROOT / name).parent.joinpath(decoded).resolve()
        try: resolved = path.relative_to(ROOT).as_posix()
        except ValueError: issues.append("local link escapes repository"); continue
        if resolved not in known or not path.is_file(): issues.append(f"missing public link target: {resolved}")
    return issues


def config_issues() -> list[str]:
    issues = []
    try:
        config = json.loads((ROOT / "config/config.example.json").read_text(encoding="utf-8"))
        env = {}
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1); env[key] = value
        if set(config.get("providers", {})) != {"tushare", "eastmoney", "cailianshe"}: issues.append("provider set is not the approved public set")
        if config.get("deployment", {}).get("bind_host") != "127.0.0.1": issues.append("template must bind localhost")
        if config.get("ai", {}).get("enabled") is not False or config.get("ai", {}).get("daily_budget_cny") != 0: issues.append("AI template must be disabled with zero budget")
        for key in ("POSTGRES_PASSWORD", "DATABASE_URL", "TUSHARE_TOKEN", "AI_API_KEY", "AI_MODEL", "LEGACY_SOURCE_PATH", "VOCECHAT_BASE_URL", "VOCECHAT_API_KEY"):
            if env.get(key) != "": issues.append(f"environment template must leave {key} empty")
        if env.get("AI_ENABLED") != "false": issues.append("AI_ENABLED must default false")
    except (OSError, ValueError, TypeError): issues.append("configuration templates are missing or malformed")
    return issues


def verify() -> int:
    try: names = files()
    except (OSError, subprocess.CalledProcessError): print("FAIL: verification requires Git"); return 1
    known = set(names); issues = [f"missing required public asset: {x}" for x in REQUIRED if x not in known]
    for name in names:
        path = ROOT / name
        if name in PRIVATE_FILES or name.startswith(PRIVATE_PREFIXES): issues.append(f"private inner-box asset present: {name}"); continue
        if path.is_symlink() or not path.is_file(): issues.append(f"invalid public asset: {name}"); continue
        if (path.suffix.lower() in PRIVATE_SUFFIXES or path.name in {".env", "token.json"} or ".local." in path.name) and not name.startswith("tests/fixtures/"):
            issues.append(f"private file type or configuration: {name}")
        if name.startswith("desktop-runtime/"):
            if not approved_name(name): issues.append(f"unapproved runtime asset: {name}")
            continue
        if path.suffix.lower() in COMPILED_SUFFIXES and not name.startswith("tests/fixtures/"): issues.append(f"compiled asset outside runtime: {name}")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore", ".gitattributes", ".editorconfig"}: continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeError: issues.append(f"not UTF-8 text: {name}"); continue
        if not text.endswith("\n"): issues.append(f"missing final newline: {name}")
        for label, pattern in SECRET_RULES:
            if pattern.search(text): issues.append(f"{name}: {label}")
        for match in ASSIGNMENT.finditer(text):
            value = match.group(1)
            lhs = text[max(0, match.start() - 40):match.end()].lower()
            if value not in ENV_NAMES and value.lower() not in {"token", "api_key", "access_token"} and not value.lower().startswith(("example", "placeholder", "replace_")) and not re.search(r"(?:self\.)?\b" + re.escape(value.lower()) + r"\s*$", lhs):
                issues.append(f"{name}: nonempty secret assignment")
        if path.suffix.lower() == ".md": issues.extend(f"{name}: {x}" for x in link_issues(name, text, known))
        if path.suffix.lower() == ".json":
            try: json.loads(text)
            except json.JSONDecodeError as exc: issues.append(f"{name}: invalid JSON line {exc.lineno}")
        if name == "启动.bat" and not canonical_launcher(path.read_bytes()): issues.append("root launcher differs from canonical launcher")
    try: issues.extend(verify_runtime(ROOT, names))
    except (OSError, ValueError, subprocess.SubprocessError): issues.append("desktop runtime verification failed")
    issues.extend(config_issues())
    if issues:
        for issue in sorted(set(issues)): print(f"FAIL: {issue}")
        print(f"Verification failed: {len(set(issues))} issue(s); secret values are not printed."); return 1
    print(f"PASS: {len(names)} public assets; outer-box boundary, links, templates and runtime checked.")
    return 0


if __name__ == "__main__": sys.exit(verify())
