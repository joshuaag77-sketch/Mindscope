# Running Mindscope safely

This is a single-owner local application. Both servers bind to 127.0.0.1. Do not publish them or enable a tunnel. A remote deployment needs HTTPS, a real identity provider and persistent, shared rate limiting.

## Private configuration

The launchers read `%LOCALAPPDATA%\Mindscope\config\mindscope.env` on Windows, or `~/.config/Mindscope/config/mindscope.env` on other systems. Override that path with `MINDSCOPE_CONFIG_FILE` if needed. Keep it outside Git, cloud-sync folders and web roots. Restrict directory permissions to your own account (Windows ACL; mode 700 on Unix) and file permissions to the owner (600 on Unix).

Copy `backend/.env.example` there, generate two independent random secrets of at least 32 characters for `MINDSCOPE_API_TOKEN` and `MINDSCOPE_WEB_PASSWORD`, and set `MINDSCOPE_USER_ID` to the owner of this instance. The browser prompts for username `owner` and the web password. The API token is only used between local servers; never put it in `NEXT_PUBLIC_*` variables. The original `.env.demo` is retired and contains placeholders only.

Run `python start_backend.py` and `python start_frontend.py` (or `start_demo.bat`). Use a currently supported, patched Python and Node.js runtime. Opening http://127.0.0.1:3000 prompts for the private web password. Direct API clients must supply `Authorization: Bearer <MINDSCOPE_API_TOKEN>`.

SMTP defaults to mock delivery, ingestion to off, and chat falls back to local rules until a new API key is configured. Set these explicitly in the private file after account credentials are secured. Existing private state is preserved during startup; restarting no longer deletes history or kills arbitrary processes listening on port 8000.

## Security boundaries

Every backend request requires the token, including health and baseline data. Any supplied user ID must equal `MINDSCOPE_USER_ID`. Browser APIs require the web password independently of middleware. Cross-origin requests are rejected. Requests are limited to 32 KiB, 180 authenticated requests/minute and 10 chat/alert mutation requests/minute per backend process. Chat input is additionally limited to 8,000 characters and 20 scheduled tasks. Limits reset on process restart; these controls target a single local owner, not shared hosting.

## Previously committed credentials

Deleting a secret from the current branch does not revoke it or remove copies from Git history, forks, caches or OneDrive history. Revoke the exposed Gmail app password in the owning Google account and replace the affected Anthropic key in its provider console before reuse. Do not paste replacements into Git, chat or terminal command arguments. History cleanup is a separate coordinated action after revocation.

## Checks

Run `python -m pytest` from `backend`; run `npm ci --ignore-scripts`, `npm run build`, and `npm audit --omit=dev` from `frontend`. The secret guard runs in CI and can be run locally with `python scripts/check_secrets.py`. Enable GitHub secret scanning and push protection for this repository, and use a protected default branch. The guard supplements provider scanning and cannot prove that a repository is secret-free.
