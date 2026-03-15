"""Start the MindScope backend with .env.demo vars loaded."""
import os
import subprocess

env_path = os.path.join(os.path.dirname(__file__), "backend", ".env.demo")
env = dict(os.environ)

with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip()

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
subprocess.run(
    ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    cwd=backend_dir,
    env=env,
)
