"""Task-prioritization chat endpoint — uses Claude API when key is available."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

_DELEGATIONS: dict[str, str] = {
    "food": "Uber Eats",
    "eat": "Uber Eats",
    "lunch": "Uber Eats / DoorDash",
    "dinner": "Uber Eats",
    "groceries": "Instacart or curbside pickup",
    "meeting": "Calendly — delegate scheduling",
    "email": "Quick template or batch reply",
    "reply": "Batch all replies into one block",
    "call": "Schedule via Calendly",
    "research": "Ask Claude / ChatGPT to draft",
    "write": "Start with an AI draft, then edit",
    "code": "GitHub Copilot or pair with teammate",
    "bug": "Log it and fix in focused block",
    "design": "Canva or Figma template",
    "admin": "Batch admin tasks together",
    "buy": "Amazon / order online",
    "fix": "Schedule a focused block",
}

_SYSTEM_PROMPT = """You are the Task Copilot inside MindScope, a cognitive load monitor. You are warm, practical, and conversational.

TWO MODES — choose based on the message:

─── MODE 1: CONVERSATION ───
When the user is chatting, venting, asking questions, or NOT listing tasks.
Return: {"type": "message", "message": "your reply (2-4 sentences, warm and concise)"}

─── MODE 2: TASK PRIORITIZATION ───
When the user gives actual tasks, a to-do list, or a brain dump.

For each task assign:
- task: clean, short task name (max 6 words)
- effort_score: 1-10 (1=trivial 5min, 10=full day hard work). Emails=2-3, coding=7-9, quick calls=2, presentations=6-8
- impact_score: 1-10 (1=barely matters, 10=critical). Be realistic.
- duration_minutes: choose from 15, 30, 45, 60, 90, 120
- quadrant: MUST follow this logic exactly:
    "Do Now"   → impact_score > 5 AND effort_score <= 5
    "Schedule" → impact_score > 5 AND effort_score > 5
    "Delegate" → impact_score <= 5 AND effort_score <= 5
    "Drop"     → impact_score <= 5 AND effort_score > 5
- delegation: specific tool/service string OR null. Use: "Uber Eats", "Instacart", "Calendly", "GitHub Copilot", "Canva", "DoorDash", etc.

SPECIAL RULES:
- Food/hunger → effort_score=1, impact_score=9, quadrant="Do Now", delegation="Uber Eats"
- Max 8 tasks
- Verify quadrant matches scores before returning

Return:
{
  "type": "tasks",
  "tasks": [
    {
      "task": "task name",
      "effort_score": 3,
      "impact_score": 8,
      "duration_minutes": 30,
      "quadrant": "Do Now",
      "delegation": null
    }
  ],
  "summary": "one warm encouraging sentence"
}

ABSOLUTE RULES: Return ONLY valid JSON. No markdown fences. No extra text."""

_SCHEDULE_PROMPT = """You are a daily schedule optimizer for someone experiencing cognitive overload.

Given tasks with durations, create a calm, achievable daily schedule.

Rules:
- Only schedule "Do Now" and "Schedule" quadrant tasks
- Order: Do Now tasks first (highest impact_score first), then Schedule tasks (highest impact_score first)
- Add 5-minute buffer between tasks
- Add 10-minute break after every 90 minutes of focus
- Don't exceed 19:00
- Round start times to nearest 5 minutes

Return ONLY valid JSON:
{
  "blocks": [
    {"task": "task name", "start": "09:00", "end": "09:30", "duration_minutes": 30, "quadrant": "Do Now", "block_type": "task"},
    {"task": "Buffer", "start": "09:30", "end": "09:35", "duration_minutes": 5, "quadrant": null, "block_type": "buffer"}
  ],
  "total_focus_minutes": 90,
  "suggested_end": "12:15",
  "note": "one warm sentence about the plan"
}"""


class PrioritizeRequest(BaseModel):
    tasks: str
    user_id: str = "joshu"


class ScheduleRequest(BaseModel):
    tasks: list[dict]
    start_time: str = "09:00"


def _rule_based_fallback(tasks_text: str) -> dict:
    lines = [l.strip() for l in tasks_text.replace(",", "\n").split("\n") if l.strip()][:8]
    result = []
    for i, task in enumerate(lines):
        lower = task.lower()
        delegation = None
        for kw, sug in _DELEGATIONS.items():
            if kw in lower:
                delegation = sug
                break
        if i < 2:
            effort_score, impact_score, quadrant, duration = 3, 8, "Do Now", 30
        elif i < 5:
            effort_score, impact_score, quadrant, duration = 7, 8, "Schedule", 60
        else:
            effort_score, impact_score, quadrant, duration = 3, 4, "Delegate", 30
        result.append({
            "task": task, "effort_score": effort_score, "impact_score": impact_score,
            "duration_minutes": duration, "quadrant": quadrant, "delegation": delegation,
        })
    return {
        "type": "tasks", "tasks": result,
        "summary": "You've got this — tackle the top two, then take a real break. 🧠",
    }


def _schedule_fallback(tasks: list[dict], start_time: str) -> dict:
    actionable = [t for t in tasks if t.get("quadrant") in ("Do Now", "Schedule")]
    actionable.sort(key=lambda t: (0 if t.get("quadrant") == "Do Now" else 1, -t.get("impact_score", 5)))
    blocks = []
    current = datetime.strptime(start_time, "%H:%M")
    focus_since_break = 0
    total_focus = 0
    for task in actionable:
        if current.hour >= 19:
            break
        duration = task.get("duration_minutes", 30)
        if focus_since_break >= 90:
            bs = current.strftime("%H:%M")
            current += timedelta(minutes=10)
            blocks.append({"task": "Break", "start": bs, "end": current.strftime("%H:%M"),
                           "duration_minutes": 10, "quadrant": None, "block_type": "buffer"})
            focus_since_break = 0
        ts = current.strftime("%H:%M")
        current += timedelta(minutes=duration)
        blocks.append({"task": task.get("task", "Task"), "start": ts, "end": current.strftime("%H:%M"),
                       "duration_minutes": duration, "quadrant": task.get("quadrant", "Schedule"), "block_type": "task"})
        total_focus += duration
        focus_since_break += duration
        bs = current.strftime("%H:%M")
        current += timedelta(minutes=5)
        blocks.append({"task": "Buffer", "start": bs, "end": current.strftime("%H:%M"),
                       "duration_minutes": 5, "quadrant": None, "block_type": "buffer"})
    return {
        "blocks": blocks, "total_focus_minutes": total_focus,
        "suggested_end": current.strftime("%H:%M"),
        "note": f"{total_focus} minutes of focused work scheduled. One task at a time — you've got this.",
    }


def _call_claude(system: str, user_content: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic  # type: ignore[import]
        client = anthropic.Anthropic(api_key=api_key)
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        response = client.messages.create(
            model=model_name, max_tokens=1500, system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
        return raw
    except Exception as exc:
        logger.warning("Claude API call failed: %s", exc)
        return None


@router.post("/prioritize")
async def prioritize_tasks(body: PrioritizeRequest) -> dict:
    raw = _call_claude(_SYSTEM_PROMPT, body.tasks)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    words = body.tasks.strip().split()
    if len(words) <= 4:
        return {"type": "message", "message": "Hey! I'm here to help. Dump your tasks or tell me what's on your mind and I'll help you prioritize. 🧠"}
    return _rule_based_fallback(body.tasks)


@router.post("/schedule")
async def schedule_tasks(body: ScheduleRequest) -> dict:
    tasks_text = json.dumps(body.tasks, indent=2)
    raw = _call_claude(_SCHEDULE_PROMPT, f"Start time: {body.start_time}\n\nTasks:\n{tasks_text}")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return _schedule_fallback(body.tasks, body.start_time)
