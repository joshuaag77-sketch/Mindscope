"""Single-owner authentication and bounded requests for the local application."""
from collections import deque
import hmac
import json
import os
import time
from urllib.parse import parse_qs

from starlette.responses import JSONResponse


class SecurityMiddleware:
    """Authenticate before buffering; limit memory, request rate, and user scope."""
    def __init__(self, app):
        self.app = app
        self.requests = deque()
        self.expensive_requests = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def deny(status, message):
            await JSONResponse({"detail": message}, status_code=status)(scope, receive, send)

        headers = dict(scope.get("headers", []))
        token = os.getenv("MINDSCOPE_API_TOKEN", "")
        if len(token) < 32:
            return await deny(503, "Authentication is not configured")
        supplied = headers.get(b"authorization", b"").decode("latin-1")
        if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
            return await deny(401, "Authentication required")
        origin = headers.get(b"origin")
        if origin and origin not in (b"http://localhost:3000", b"http://127.0.0.1:3000"):
            return await deny(403, "Origin not permitted")

        now = time.monotonic()
        expensive = scope["path"].startswith("/api/v1/chat/") or (
            scope["method"] == "POST" and scope["path"].startswith("/api/v1/alerts/"))
        queues = [(self.requests, 180)]
        if expensive:
            queues.append((self.expensive_requests, 10))
        for queue, maximum in queues:
            while queue and queue[0] <= now - 60:
                queue.popleft()
            if len(queue) >= maximum:
                return await deny(429, "Rate limit exceeded; retry in one minute")
        # Reserve before the first body read so concurrent requests cannot bypass the cap.
        for queue, _ in queues:
            queue.append(now)

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 32768:
                return await deny(413, "Request body exceeds 32 KiB")
            if not message.get("more_body", False):
                break
        owner = os.getenv("MINDSCOPE_USER_ID") or os.getenv("USERNAME") or "local-user"
        user_ids = parse_qs(scope.get("query_string", b"").decode("utf-8", "replace")).get("user_id", [])
        if body:
            try:
                payload = json.loads(body)
                if isinstance(payload, dict) and "user_id" in payload:
                    user_ids.append(payload["user_id"])
            except (ValueError, UnicodeError):
                return await deny(400, "Invalid JSON body")
        parts = scope["path"].rstrip("/").split("/")
        if len(parts) == 6 and parts[1:4] == ["api", "v1", "alerts"]:
            user_ids.append(parts[-1])
        if any(user_id != owner for user_id in user_ids):
            return await deny(403, "This instance only permits its configured owner")
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
