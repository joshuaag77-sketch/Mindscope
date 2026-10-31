"""Start password-protected UI on loopback using private configuration."""
import shutil
import subprocess
from pathlib import Path
from local_config import load_environment

if __name__ == "__main__":
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise SystemExit("Install a supported, patched Node.js release first.")
    raise SystemExit(subprocess.call([npm, "run", "dev"], cwd=Path(__file__).parent / "frontend", env=load_environment()))
