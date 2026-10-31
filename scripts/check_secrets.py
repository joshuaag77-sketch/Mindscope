"""Reject common credential assignments without ever displaying their values."""
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
patterns = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"(?m)^[ \t]*(?:MINDSCOPE_SMTP_PASSWORD|ANTHROPIC_API_KEY|MINDSCOPE_API_TOKEN|MINDSCOPE_WEB_PASSWORD)[ \t]*=[ \t]*[^\s#]+"),
]
failed = []
for name in filter(None, paths):
    path = root / name
    if not path.is_file() or path.stat().st_size > 2_000_000:
        continue
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeError:
        continue
    if any(pattern.search(content) for pattern in patterns):
        failed.append(name)
if failed:
    print("Potential credentials found (values suppressed):\n" + "\n".join(failed))
    sys.exit(1)
print("No matching credential patterns in tracked files.")
