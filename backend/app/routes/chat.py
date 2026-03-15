"""Task-prioritization chat endpoint — uses Claude API when key is available."""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Delegation ideas keyed on keyword matches
_DELEGATIONS: dict[str, str] = {
    "food": "🍕 Order via Uber Eats so you don't lose focus",
    "eat": "🍕 Uber Eats / DoorDash — offload the decision",
    "lunch": "🍕 Order delivery — remove this from your plate",
    "dinner": "🍕 Uber Eats handles it",
    "groceries": "🛒 Instacart or curbside pickup",
    "meeting": "📅 Delegate or reschedule — use Calendly",
    "email": "📧 Use a saved template or batch it for later",
    "reply": "📧 Batch all replies into one 15-min block",
    "call": "📞 Schedule it — don't let it interrupt flow",
    "research": "🔍 Ask Claude / ChatGPT to draft a summary",
    "write": "✍️ Start with an AI draft, then edit",
    "code": "💻 Pair with a teammate or use GitHub Copilot",
    "bug": "🐛 Log it and tackle when focused, not now",
    "design": "🎨 Use a Canva or Figma template",
    "admin": "📋 Batch admin tasks into a single block",
    "buy": "🛒 Add to cart and auto-buy later",
    "fix": "🔧 Schedule a focused block — not multitasking",
}

_SYSTEM_PROMPT = """You are the Task Copilot inside MindScope, a cognitive load monitor.
The user is currently experiencing elevated cognitive load and needs to clear their mental queue.

When given a brain dump of tasks (free-form text), you must:
1. Parse and list individual tasks
2. Assign Impact (High / Med / Low) and Effort (High / Med / Low) to each
3. Assign a quadrant: "Do Now" (high impact, low effort), "Schedule" (high impact, high effort),
   "Delegate" (low impact, any effort), or "Drop" (low impact, low value)
4. Suggest a practical delegation shortcut for each task (real tools: Uber Eats, Calendly, Copilot, etc.)

Rules:
- Be warm, brief, and practical
- No more than 8 tasks
- If the user mentions being hungry / needing food, always suggest Uber Eats as delegation
- Return ONLY valid JSON — no markdown fences, no extra text

Required JSON structure:
{
  "tasks": [
    {
      "task": "short task name",
      "impact": "High|Med|Low",
      "effort": "High|Med|Low",
      "quadrant": "Do Now|Schedule|Delegate|Drop",
      "delegation": "practical shortcut suggestion"
    }
  ],
  "summary": "one warm, encouraging sentence (max 20 words)"
}"""


class PrioritizeRequest(BaseModel):
    tasks: str
    user_id: str = "joshu"


def _rule_based_fallback(tasks_text: str) -> dict:
    """Simple keyword-based prioritization when Claude API is unavailable."""
    lines = [
        line.strip()
        for line in tasks_text.replace(",", "\n").split("\n")
        if line.strip()
    ][:8]

    result = []
    for i, task in enumerate(lines):
        lower = task.lower()
        delegation = "📋 Handle in a focused block when load drops"
        for kw, suggestion in _DELEGATIONS.items():
            if kw in lower:
                delegation = suggestion
                break
        if i < 2:
            quadrant, impact, effort = "Do Now", "High", "Low"
        elif i < 5:
            quadrant, impact, effort = "Schedule", "High", "High"
        else:
            quadrant, impact, effort = "Delegate", "Low", "Med"
        result.append(
            {
                "task": task,
                "impact": impact,
                "effort": effort,
                "quadrant": quadrant,
                "delegation": delegation,
            }
        )
    return {
        "tasks": result,
        "summary": "You've got this — tackle the top two, then take a real break. 🧠",
    }


@router.post("/prioritize")
async def prioritize_tasks(body: PrioritizeRequest) -> dict:
    """Prioritize a free-form task list using Claude or rule-based fallback."""

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            import anthropic  # type: ignore[import]

            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"My tasks right now:\n{body.tasks}",
                    }
                ],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if model adds them
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
            return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Claude API call failed, using fallback: %s", exc)

    return _rule_based_fallback(body.tasks)
