"""Send GitHub push notifications to a configurable VoceChat bot channel."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class NotificationError(RuntimeError):
    """Carries only a safe category, never request/response or credential text."""


@dataclass(frozen=True)
class BotConfig:
    enabled: bool = False
    base_url: str = field(default="", repr=False)
    api_key: str = field(default="", repr=False)
    group_id: str = "19"
    api_prefix: str = "/api/bot"
    timeout_seconds: float = 15

    def missing(self) -> list[str]:
        return [name for name in ("base_url", "api_key") if not getattr(self, name)]

    def validate(self) -> None:
        if self.missing():
            raise NotificationError("missing_bot_configuration")
        parsed = urlsplit(self.base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
            raise NotificationError("invalid_bot_base_url_use_https_without_credentials")
        if any(character in self.base_url + self.api_key for character in "\r\n"):
            raise NotificationError("invalid_bot_configuration")
        if not re.fullmatch(r"[1-9][0-9]*", self.group_id):
            raise NotificationError("invalid_bot_channel")
        prefix = self.api_prefix.strip("/")
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", prefix):
            raise NotificationError("invalid_bot_api_prefix")
        if not math.isfinite(self.timeout_seconds) or not 1 <= self.timeout_seconds <= 120:
            raise NotificationError("invalid_bot_timeout")

    def summary(self) -> dict:
        return {
            "enabled": self.enabled,
            "base_url_configured": bool(self.base_url),
            "api_key_configured": bool(self.api_key),
            "group_id": self.group_id,
            "timeout_seconds": self.timeout_seconds,
            "missing": self.missing(),
        }


def read_dotenv(path: Path) -> dict[str, str]:
    """Read only notification variables; never execute/interpolate file contents."""
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        key, value = key.strip(), value.strip()
        if not re.fullmatch(r"VOCECHAT_[A-Z_]+", key):
            continue
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise NotificationError("invalid_notification_env_file") from None
            if not isinstance(value, str):
                raise NotificationError("invalid_notification_env_file")
        elif value.startswith("'"):
            if not value.endswith("'"):
                raise NotificationError("invalid_notification_env_file")
            value = value[1:-1]
        result[key] = value
    return result


def load_config(env: dict[str, str] | None = None, env_file: Path | None = None, root: Path = ROOT) -> BotConfig:
    environment = dict(os.environ if env is None else env)
    values = read_dotenv(env_file or root / ".env")
    values.update({key: value for key, value in environment.items() if value})
    settings = {}
    for name in ("config.example.json", "config.local.json"):
        path = root / "config" / name
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                section = payload.get("notifications", {}).get("vocechat", {})
                if not isinstance(section, dict):
                    raise ValueError
                if any(key in section for key in ("api_key", "api_key_file")):
                    raise NotificationError("inline_bot_secret_not_allowed_use_environment")
                settings.update(section)
            except (ValueError, AttributeError):
                raise NotificationError("invalid_notification_json_config") from None

    def get(name: str, fallback=""):
        env_name = settings.get(name + "_env", "VOCECHAT_" + name.upper())
        return values.get(env_name) or settings.get(name, fallback)

    key_env = settings.get("api_key_env", "VOCECHAT_API_KEY")
    key, key_file = values.get(key_env, ""), values.get(key_env + "_FILE", "")
    if key and key_file:
        raise NotificationError("conflicting_bot_secret_sources")
    if key_file:
        try:
            key = Path(key_file).read_text(encoding="utf-8-sig").strip()
        except (OSError, UnicodeError):
            raise NotificationError("bot_secret_file_unreadable") from None
    enabled = str(get("enabled", False)).lower()
    if enabled not in {"true", "false", "1", "0"}:
        raise NotificationError("invalid_notification_enabled_setting")
    try:
        return BotConfig(
            enabled=enabled in {"true", "1"}, base_url=str(get("base_url")).strip().rstrip("/"),
            api_key=key, group_id=str(get("group_id", "19")).strip(),
            api_prefix=str(get("api_prefix", "/api/bot")), timeout_seconds=float(get("timeout_seconds", 15)),
        )
    except (TypeError, ValueError):
        raise NotificationError("invalid_notification_configuration") from None


def redact(text: str, config: BotConfig) -> str:
    for secret in (config.api_key, config.base_url):
        if secret:
            text = text.replace(secret, "[redacted]")
    text = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[a-fA-F0-9]{48,128})\b", "[redacted]", text)
    text = re.sub(r"(?i)([?&](?:token|api_key|access_token|key)=)[^\s&]+", r"\1[redacted]", text)
    return text


def safe_label(value: object, config: BotConfig, limit: int = 160) -> str:
    text = redact(str(value), config).replace("\r", " ").replace("\n", " ")[:limit]
    text = "".join(character for character in text if character.isprintable()).replace("@", "＠")
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>])", r"\\\1", text)


def build_message(event: dict, env: dict[str, str], config: BotConfig) -> str:
    repository = (event.get("repository") or {}).get("full_name") or env.get("GITHUB_REPOSITORY", "")
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise NotificationError("invalid_github_repository")
    event_name = env.get("GITHUB_EVENT_NAME", "push")
    if event_name not in {"push", "workflow_dispatch"}:
        raise NotificationError("unsupported_notification_event")
    ref = event.get("ref") or env.get("GITHUB_REF", "")
    if not isinstance(ref, str) or not ref.startswith(("refs/heads/", "refs/tags/")):
        raise NotificationError("invalid_github_ref")
    ref_type = "标签" if ref.startswith("refs/tags/") else "分支"
    short_ref = ref.split("/", 2)[2]
    before = event.get("before", "")
    after = event.get("after") or env.get("GITHUB_SHA", "")
    if not isinstance(after, str) or not re.fullmatch(r"[a-fA-F0-9]{40}", after):
        raise NotificationError("invalid_github_commit")
    actor = (event.get("pusher") or {}).get("name") or env.get("GITHUB_ACTOR", "unknown")
    operation = "删除" if event.get("deleted") else "创建" if event.get("created") else "强制更新" if event.get("forced") else "更新"
    title = "Git 推送通知" if event_name == "push" else "通知链路手动验证（非 Git 推送）"
    lines = [f"### x2Stock {title}", "", f"- 仓库：{repository}",
             f"- {ref_type}：{safe_label(short_ref, config)}", f"- 操作：{operation}",
             f"- 推送者：{safe_label(actor, config)}", f"- 提交：`{after[:12]}`"]
    commits = event.get("commits") or []
    if not isinstance(commits, list):
        raise NotificationError("invalid_github_commits")
    if not commits and event.get("head_commit"):
        commits = [event["head_commit"]]
    if commits:
        lines.extend(["", "提交概要："])
        for commit in commits[-5:]:
            if not isinstance(commit, dict):
                raise NotificationError("invalid_github_commit_entry")
            subject = str(commit.get("message", "")).splitlines()
            lines.append("- " + safe_label(subject[0] if subject else "（无标题）", config))
        if len(commits) > 5:
            lines.append(f"- 其余 {len(commits) - 5} 项见变更链接")
    base = "https://github.com/" + repository
    if event.get("deleted"):
        link = base
    elif isinstance(before, str) and re.fullmatch(r"[a-fA-F0-9]{40}", before) and set(before) != {"0"}:
        link = base + "/compare/" + before + "..." + after
    else:
        link = base + "/commit/" + after
    lines.extend(["", f"[查看 Git 变更]({link})"])
    run_id = env.get("GITHUB_RUN_ID", "")
    if run_id.isdigit():
        lines.append(f"[查看通知运行]({base}/actions/runs/{run_id})")
        lines.append(f"通知标识：{run_id}，尝试 {safe_label(env.get('GITHUB_RUN_ATTEMPT', '1'), config, 8)}")
    return redact("\n".join(lines), config)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def should_notify_push(ref: str) -> bool:
    """Main and canonical version tags are covered by the release workflow."""
    return ref != "refs/heads/main" and re.fullmatch(r"refs/tags/v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", ref) is None


def build_release_message(receipt: dict, env: dict[str, str], config: BotConfig) -> str:
    repository = receipt.get("repository", "")
    version = receipt.get("version", "")
    sha = receipt.get("sha", "")
    if (not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or repository != env.get("GITHUB_REPOSITORY") or not isinstance(version, str)
            or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version)
            or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != env.get("GITHUB_SHA")):
        raise NotificationError("invalid_release_identity")
    base = "https://github.com/" + repository
    release_url = f"{base}/releases/tag/v{version}"
    comparison = receipt.get("compare_url", "")
    if (receipt.get("tag") != "v" + version or receipt.get("release_url") != release_url
            or not isinstance(comparison, str) or not re.fullmatch(re.escape(base) + r"/(?:commits/v[0-9]+\.[0-9]+\.[0-9]+|compare/v[0-9]+\.[0-9]+\.[0-9]+\.\.\.v[0-9]+\.[0-9]+\.[0-9]+)", comparison)
            or not comparison.endswith("v" + version)):
        raise NotificationError("invalid_release_links")
    notes = receipt.get("notes", "")
    if not isinstance(notes, str) or not notes.startswith(f"# x2Stock {version}\n"):
        raise NotificationError("invalid_release_notes")
    body = notes.splitlines()[2:]
    overview = next((line for line in body if line.strip() and not line.startswith("#")), "")
    bullets = [line[2:] for line in body if line.startswith("- ")][:5]
    lines = [f"### x2Stock {version} 已发布", "", safe_label(overview, config, 400), "", "更新摘要："]
    lines.extend("- " + safe_label(item, config, 240) for item in bullets)
    lines.extend(["", f"- 提交：`{sha[:12]}`", f"[查看 Release]({release_url})", f"[查看版本差异／首次提交历史]({comparison})"])
    run_id = env.get("GITHUB_RUN_ID", "")
    if not run_id.isdigit():
        raise NotificationError("missing_release_run_identity")
    lines.extend([f"[查看发布运行]({base}/actions/runs/{run_id})",
                  f"通知标识：{run_id}，尝试 {safe_label(env.get('GITHUB_RUN_ATTEMPT', '1'), config, 8)}"])
    return redact("\n".join(lines), config)


def send_message(config: BotConfig, message: str) -> int:
    config.validate()
    if not message.strip():
        raise NotificationError("empty_notification")
    url = config.base_url + "/" + config.api_prefix.strip("/") + "/send_to_group/" + quote(config.group_id, safe="")
    request = urllib.request.Request(url, data=message.encode("utf-8"), method="POST", headers={
        "Content-Type": "text/markdown", "x-api-key": config.api_key, "User-Agent": "x2stock-git-notifier/1.0",
    })
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=config.timeout_seconds) as response:
            status = response.status
            # Do not print, persist or return the upstream response body.
            if not 200 <= status < 300:
                raise NotificationError("bot_http_" + str(status))
            return status
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise NotificationError("bot_http_" + str(status)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        # Ambiguous timeouts are not retried: the bot API has no idempotency key.
        raise NotificationError("bot_network_failure_or_timeout") from None
    except http.client.HTTPException:
        raise NotificationError("bot_protocol_failure") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--event-file", type=Path)
    parser.add_argument("--release-file", type=Path)
    args = parser.parse_args(argv)
    try:
        config = load_config(env_file=args.env_file)
        if args.check_config:
            if config.enabled:
                config.validate()
            print(json.dumps(config.summary(), ensure_ascii=False))
            return 0
        if not config.enabled and not args.dry_run:
            if args.release_file:
                raise NotificationError("release_notification_disabled")
            print(json.dumps({"status": "disabled", "channel": config.group_id}))
            return 0
        if args.release_file:
            receipt = json.loads(args.release_file.read_text(encoding="utf-8"))
            message = build_release_message(receipt, dict(os.environ), config)
        else:
            event_path = args.event_file or (Path(os.environ["GITHUB_EVENT_PATH"]) if os.environ.get("GITHUB_EVENT_PATH") else None)
            if event_path is None:
                raise NotificationError("missing_github_event_file")
            event = json.loads(event_path.read_text(encoding="utf-8"))
            if not isinstance(event, dict):
                raise NotificationError("invalid_github_event_file")
            ref = event.get("ref") or os.environ.get("GITHUB_REF", "")
            if not should_notify_push(ref):
                print(json.dumps({"status": "covered_by_release_workflow", "channel": config.group_id}))
                return 0
            message = build_message(event, dict(os.environ), config)
        if args.dry_run:
            print(json.dumps({"status": "dry_run", "channel": config.group_id, "markdown": message}, ensure_ascii=False))
            return 0
        status = send_message(config, message)
        print(json.dumps({"status": "sent", "channel": config.group_id, "http_status": status}))
        return 0
    except NotificationError as error:
        print(json.dumps({"status": "failed", "error": str(error)}))
        return 1
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
        print(json.dumps({"status": "failed", "error": "invalid_notification_input"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
