"""Start authenticated backend on loopback using private configuration."""
import subprocess
import sys
from pathlib import Path
from local_config import load_environment

if __name__ == "__main__":
    raise SystemExit(subprocess.call(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=Path(__file__).parent / "backend", env=load_environment(),
    ))
