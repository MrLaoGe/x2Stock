"""Verify the generated public tree without private development dependencies."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_desktop_runtime import verify_runtime

PRIVATE_ROOTS = {'.agents', '.local', '.worktrees', 'runtime', 'data', 'logs', 'outputs', 'backups'}
PRIVATE_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.duckdb', '.parquet', '.csv', '.xlsx',
                    '.xls', '.docx', '.pdf', '.log', '.pem', '.key'}
DATABASE_FILE = re.compile(r'\.(?:db|sqlite|sqlite3)(?:-(?:wal|shm|journal))?$|\.duckdb(?:\.wal)?$', re.I)
BINARY_ASSETS = {'docs/assets/readme-header.jpg'}
SECRET_ASSIGNMENT = re.compile(
    r"(?im)[\"']?\b(?:TUSHARE_TOKEN|AI_API_KEY|OPENAI_API_KEY|VOCECHAT_API_KEY|POSTGRES_PASSWORD|api_key|access_token|password|token)"
    r"[\"']?[ \t]*[:=][ \t]*[\"']?([A-Za-z0-9_./+=:-]+)"
)
PYTHON_SECRET_ASSIGNMENT = re.compile(
    r"(?im)[\"']?\b(?:TUSHARE_TOKEN|AI_API_KEY|OPENAI_API_KEY|VOCECHAT_API_KEY|POSTGRES_PASSWORD|api_key|access_token|password|token)"
    r"[\"']?[ \t]*[:=][ \t]*[\"']([A-Za-z0-9_./+=:-]+)"
)
ENV_REFERENCES = {'TUSHARE_TOKEN', 'AI_API_KEY', 'OPENAI_API_KEY', 'VOCECHAT_API_KEY',
                  'POSTGRES_PASSWORD', 'DATABASE_URL'}


def secret_issues(text, python_code=False):
    """Public static scan; no private configuration or development imports."""
    rules = [r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b',
             r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b',
             r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
             r'\b[0-9a-fA-F]{48,128}\b',
             r'[?&](?:token|api_key|access_token|key)=[^\s&<>]+']
    issues = ['credential pattern'] if any(re.search(rule, text) for rule in rules) else []
    assignments = PYTHON_SECRET_ASSIGNMENT if python_code else SECRET_ASSIGNMENT
    for match in assignments.finditer(text):
        value = match.group(1)
        if value in ENV_REFERENCES or value.lower().startswith(('example', 'placeholder', 'replace_')):
            continue
        issues.append('nonempty credential assignment')
    return issues


def content_issues(name, data):
    if name in BINARY_ASSETS:
        return [] if data.startswith((b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n')) else ['approved image is not JPEG or PNG']
    try:
        return secret_issues(data.decode('utf-8'), python_code=name.endswith('.py'))
    except UnicodeError:
        return ['ordinary public content must be UTF-8']


def main():
    manifest = json.loads((ROOT / '.x2stock-export.json').read_text(encoding='utf-8'))
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    names = set(filter(None, names))
    expected = set(manifest['files']) | {'.x2stock-export.json'}
    issues = []
    if (manifest.get('schema') != 1 or manifest.get('repository') != 'MrLaoGe/x2Stock' or
            hashlib.sha256((json.dumps(manifest['files'], ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()).hexdigest() != manifest.get('content_sha256')):
        issues.append('invalid public manifest identity or digest')
    if names != expected:
        issues.append('tracked tree differs from managed public manifest')
    for name, record in manifest['files'].items():
        path = ROOT / name
        if (not path.resolve().is_relative_to(ROOT) or not path.is_file() or
                any(part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400) for part in [path, *path.parents])):
            issues.append('public file is missing or linked')
            continue
        # Git blob bytes avoid text checkout line-ending conversion.
        data = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
        if name.startswith('desktop-runtime/'):
            continue
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            issues.append('public blob digest differs from export manifest')
        # Inspect committed and working bytes so an accidentally filled local env
        # example cannot be hidden by an unchanged committed digest.
        issues.extend(content_issues(name, data))
        issues.extend(content_issues(name, path.read_bytes()))
    issues.extend(verify_runtime(ROOT, sorted(names), materialized=True))
    print('FAIL: generated public tree rejected' if issues else 'PASS: generated public tree and materialized runtime verified')
    return bool(issues)


if __name__ == '__main__':
    raise SystemExit(main())
