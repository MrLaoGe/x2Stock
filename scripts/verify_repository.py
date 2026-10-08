"""Validate public documentation assets without network or runtime dependencies."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "LICENSE", ".env.example",
    "config/config.example.json", "docs/README.md", "docs/project-plan.md",
    "docs/architecture.md", "docs/contracts.md", "docs/configuration.md",
    "docs/ui-design.md", "docs/agents.md", "docs/roadmap.md",
    "docs/data/sources.md", "docs/data/legacy-audit.md", "docs/data/migration.md",
    "docs/modules/catalog.md", "docs/modules/data-center.md",
    "docs/development/collaboration.md", "docs/development/task-ledger.md",
    "docs/development/handoff-template.md", "docs/development/handoffs/phase-0.md",
    "docs/adr/0001-project-boundary.md", "docs/adr/0002-stack-and-deployment.md",
    "docs/adr/0003-provenance-and-migration.md", "docs/adr/0004-agent-and-execution.md",
    ".github/workflows/verify-docs.yml", "scripts/verify_repository.py",
    ".github/workflows/notify-vocechat.yml", "scripts/vocechat_notify.py",
    "tests/test_vocechat_notify.py", "docs/development/git-notifications.md",
    "VERSION", "CHANGELOG.md", ".agents/skills/README.md", ".agents/skills/registry.json",
    ".agents/skills/github-release/SKILL.md", ".agents/skills/github-release/agents/openai.yaml",
    ".agents/skills/github-release/scripts/release.py", ".agents/skills/github-release/references/release-contract.md",
    "tests/test_github_release.py", "docs/development/skills.md", "docs/development/releases.md",
    "docs/development/handoffs/skill-releases.md",
)
PRIVATE_ROOTS = {".local", ".worktrees", "runtime", "data", "logs", "outputs", "backups"}
PRIVATE_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".duckdb", ".parquet", ".csv", ".xlsx",
    ".xls", ".docx", ".pdf", ".log", ".pem", ".key",
}
TEXT_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".toml", ".example"}
DATABASE_FILE = re.compile(r"\.(?:db|sqlite|sqlite3)(?:-(?:wal|shm|journal))?$|\.duckdb(?:\.wal)?$", re.I)
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*[\"'])?\s*\)")
SECRET_RULES = (
    ("API key pattern", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b")),
    ("GitHub credential pattern", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("long hexadecimal secret or payload", re.compile(r"\b[0-9a-fA-F]{48,128}\b")),
    ("credential in URL", re.compile(r"[?&](?:token|api_key|access_token|key)=[^\s&<>\"')]+", re.I)),
    ("private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("credential in connection URI", re.compile(r"(?:postgres(?:ql)?(?:\+\w+)?|https?)://[^\s/:]+:[^\s/@]+@", re.I)),
)
SECRET_ASSIGNMENT = re.compile(
    r"(?im)[\"']?\b(?:TUSHARE_TOKEN|AI_API_KEY|OPENAI_API_KEY|VOCECHAT_API_KEY|POSTGRES_PASSWORD|api_key|access_token|password|token)"
    r"[\"']?[ \t]*[:=][ \t]*[\"']?([A-Za-z0-9_./+=:-]+)"
)
PYTHON_SECRET_ASSIGNMENT = re.compile(
    r"(?im)[\"']?\b(?:TUSHARE_TOKEN|AI_API_KEY|OPENAI_API_KEY|VOCECHAT_API_KEY|POSTGRES_PASSWORD|api_key|access_token|password|token)"
    r"[\"']?[ \t]*[:=][ \t]*[\"']([A-Za-z0-9_./+=:-]+)"
)
ENV_REFERENCES = {"TUSHARE_TOKEN", "AI_API_KEY", "OPENAI_API_KEY", "VOCECHAT_API_KEY", "POSTGRES_PASSWORD", "DATABASE_URL"}


def repository_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})


def secret_issues(text: str, python_code: bool = False) -> list[str]:
    # Only print category/line, never the credential or matching source line.
    issues = []
    for label, pattern in SECRET_RULES:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append(f"{label} at line {line}")
    assignments = PYTHON_SECRET_ASSIGNMENT if python_code else SECRET_ASSIGNMENT
    for match in assignments.finditer(text):
        value = match.group(1)
        if value in ENV_REFERENCES or value.lower().startswith(("example", "placeholder", "replace_")):
            continue
        line = text.count("\n", 0, match.start()) + 1
        issues.append(f"nonempty secret assignment at line {line}")
    return issues


def link_issues(relative: str, content: str, files: set[str]) -> list[str]:
    issues = []
    # Code examples are not rendered Markdown links.
    content = re.sub(r"```.*?```", "", content, flags=re.S)
    for match in LINK.finditer(content):
        target = match.group(1).strip("<>")
        parts = urlsplit(target)
        if parts.scheme:
            if parts.scheme not in {"http", "https", "mailto"}:
                issues.append("nonportable link scheme")
            continue
        if not parts.path:
            continue
        decoded = unquote(parts.path).replace("\\", "/")
        if decoded.startswith("/"):
            issues.append("absolute local link")
            continue
        path = (ROOT / relative).parent.joinpath(decoded).resolve()
        try:
            resolved = path.relative_to(ROOT).as_posix()
        except ValueError:
            issues.append("local link escapes repository")
            continue
        if resolved not in files or not path.is_file():
            issues.append(f"local link target missing from public assets: {resolved}")
    return issues


def config_issues(config: dict, env_text: str) -> list[str]:
    issues = []
    if set(config.get("providers", {})) != {"tushare", "eastmoney", "cailianshe"}:
        issues.append("provider set must equal approved sources")
    if config.get("deployment", {}).get("bind_host") != "127.0.0.1":
        issues.append("single-user template must bind localhost")
    ai = config.get("ai", {})
    if ai.get("enabled") is not False or ai.get("daily_budget_cny") != 0:
        issues.append("AI template must be disabled with zero budget")
    if ai.get("model") != "" or ai.get("protocol") not in {"responses", "chat_completions"}:
        issues.append("AI model must be user supplied with explicit supported protocol")
    env = {}
    for line in env_text.splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key] = value
    for key in ("POSTGRES_PASSWORD", "DATABASE_URL", "TUSHARE_TOKEN", "AI_API_KEY", "AI_MODEL", "LEGACY_SOURCE_PATH", "VOCECHAT_BASE_URL", "VOCECHAT_API_KEY"):
        if env.get(key) != "":
            issues.append(f"environment template must leave {key} empty")
    if env.get("AI_ENABLED") != "false" or env.get("AI_DAILY_BUDGET_CNY") != "0":
        issues.append("environment AI defaults must be disabled")
    identity = config.get("identity", {})
    if identity != {"local_user_id": "local", "local_workspace_id": "local"}:
        issues.append("single-user template identity must be local/local")
    bot = config.get("notifications", {}).get("vocechat", {})
    if bot.get("enabled") is not False or env.get("VOCECHAT_ENABLED") != "false":
        issues.append("public notification templates must be disabled")
    if bot.get("api_key_env") != "VOCECHAT_API_KEY" or "api_key" in bot or "base_url" in bot:
        issues.append("bot address/key templates must only reference environment variables")
    for field, env_name in (("group_id", "VOCECHAT_GROUP_ID"), ("api_prefix", "VOCECHAT_API_PREFIX"), ("timeout_seconds", "VOCECHAT_TIMEOUT_SECONDS")):
        if str(bot.get(field, "")) != env.get(env_name):
            issues.append(f"notification defaults disagree for {field}")
    for key, value in config.get("deployment", {}).get("ports", {}).items():
        env_key = {"web": "XXSTOCK_WEB_PORT", "api": "XXSTOCK_API_PORT", "dev_web": "XXSTOCK_DEV_WEB_PORT"}.get(key)
        if env_key is None or env.get(env_key) != str(value):
            issues.append(f"port defaults disagree for {key}")
    return issues


def verify() -> int:
    try:
        files = repository_files()
    except (OSError, subprocess.CalledProcessError):
        print("FAIL: verification requires a Git checkout and Git executable")
        return 1
    public = set(files)
    issues = [f"missing required asset: {name}" for name in REQUIRED if name not in public]
    for name in files:
        path = ROOT / name
        if path.is_symlink():
            issues.append(f"{name}: symlink is not a public documentation asset")
            continue
        if not path.is_file():
            issues.append(f"{name}: public asset missing from working tree")
            continue
        parts = Path(name).parts
        fixture = name.startswith("tests/fixtures/")
        if parts[0] in PRIVATE_ROOTS or "node_modules" in parts:
            issues.append(f"{name}: private/runtime path in public assets")
        if ((path.suffix.lower() in PRIVATE_SUFFIXES or DATABASE_FILE.search(path.name)) and not fixture) or path.name in {"token.json", ".env"} or ".local." in path.name:
            issues.append(f"{name}: private file type or configuration")
        if path.name.startswith(".env.") and path.name != ".env.example":
            issues.append(f"{name}: real environment file")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore", ".gitattributes", ".editorconfig"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            issues.append(f"{name}: text must be UTF-8")
            continue
        if not content.endswith("\n"):
            issues.append(f"{name}: missing final newline")
        issues.extend(f"{name}: {issue}" for issue in secret_issues(content, python_code=path.suffix.lower() == ".py"))
        if path.suffix.lower() == ".md":
            issues.extend(f"{name}: {issue}" for issue in link_issues(name, content, public))
        if path.suffix.lower() == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                issues.append(f"{name}: invalid JSON at line {exc.lineno}")
    try:
        config = json.loads((ROOT / "config/config.example.json").read_text(encoding="utf-8"))
        env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
        issues.extend(config_issues(config, env_text))
    except (OSError, ValueError, TypeError, AttributeError):
        issues.append("configuration templates are missing or malformed")
    try:
        registry = json.loads((ROOT / ".agents/skills/registry.json").read_text(encoding="utf-8"))
        if registry.get("schema_version") != 1 or not isinstance(registry.get("skills"), list):
            raise ValueError
        identifiers = set()
        for item in registry["skills"]:
            identifier = item["id"]
            expected = f".agents/skills/{identifier}/SKILL.md"
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) or identifier in identifiers:
                issues.append("Skill identifier invalid or duplicated")
            identifiers.add(identifier)
            if item["path"] != expected or expected not in public:
                issues.append("Skill registry path missing or noncanonical")
                continue
            text = (ROOT / expected).read_text(encoding="utf-8")
            frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
            if not frontmatter or not re.search(rf"^name: {re.escape(identifier)}$", frontmatter[1], re.M) or not re.search(r"^description: .+", frontmatter[1], re.M):
                issues.append(f"{expected}: invalid Skill frontmatter")
            if item["category"] not in {"development", "business"} or item["status"] not in {"active", "planned", "deprecated"} or not item["purpose"]:
                issues.append("Skill registry classification invalid")
            if not isinstance(item["dependencies"], list) or any(resource not in public for resource in item.get("resources", [])):
                issues.append("Skill dependencies/resources invalid")
        if any(dependency not in identifiers for item in registry["skills"] for dependency in item["dependencies"]):
            issues.append("Skill dependency is not registered")
        discovered = {name for name in public if name.startswith(".agents/skills/") and name.endswith("/SKILL.md")}
        if discovered != {item["path"] for item in registry["skills"]}:
            issues.append("Skill discovery and registry disagree")
        version = (ROOT / "VERSION").read_text(encoding="utf-8")
        if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\n", version):
            issues.append("VERSION must contain one canonical version and newline")
        else:
            for suffix in ("md", "json"):
                if f"docs/releases/{version.strip()}.{suffix}" not in public:
                    issues.append("Current release material missing")
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        issues.append("Skill registry or version malformed")
    if issues:
        for issue in sorted(set(issues)):
            print(f"FAIL: {issue}")
        print(f"Verification failed: {len(set(issues))} issue(s); secret values are not printed.")
        return 1
    print(f"PASS: {len(files)} public assets; links, templates and common credential patterns checked.")
    print("No network calls made. Manual publication review and data permission checks remain necessary.")
    return 0


if __name__ == "__main__":
    sys.exit(verify())
