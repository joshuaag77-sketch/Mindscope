"""Load local secrets from a private directory, never from the checkout."""
import os
from pathlib import Path


def config_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config"))
    return Path(os.environ.get("MINDSCOPE_CONFIG_FILE", root / "Mindscope/config/mindscope.env"))


def load_environment() -> dict[str, str]:
    env = dict(os.environ)
    source = config_path()
    if not source.is_file():
        raise SystemExit(f"Create private configuration first; see SECURITY.md. Expected: {source}")
    for line in source.read_text(encoding="utf-8-sig").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip())
    for name in ("MINDSCOPE_API_TOKEN", "MINDSCOPE_WEB_PASSWORD"):
        if len(env.get(name, "")) < 32:
            raise SystemExit(f"{name} must contain at least 32 characters. See SECURITY.md.")
    return env
