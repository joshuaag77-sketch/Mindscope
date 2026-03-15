"use client";

import { useEffect, useRef, useState } from "react";

interface Task {
  task: string;
  impact: "High" | "Med" | "Low";
  effort: "High" | "Med" | "Low";
  quadrant: "Do Now" | "Schedule" | "Delegate" | "Drop";
  delegation: string;
}

interface PrioritizeResponse {
  tasks: Task[];
  summary: string;
}

type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; kind: "text"; content: string }
  | { role: "assistant"; kind: "tasks"; content: PrioritizeResponse };

const QUADRANT_STYLE: Record<string, { bg: string; color: string; icon: string }> = {
  "Do Now":  { bg: "rgba(179,66,54,0.1)",  color: "#b34236", icon: "🔥" },
  "Schedule":{ bg: "rgba(200,137,26,0.1)", color: "#c8891a", icon: "📅" },
  "Delegate":{ bg: "rgba(47,122,82,0.1)",  color: "#2f7a52", icon: "🤝" },
  "Drop":    { bg: "rgba(108,90,79,0.1)",  color: "#6c5a4f", icon: "🗑️" },
};

const IMPACT_COLOR: Record<string, string> = {
  High: "#b34236", Med: "#c8891a", Low: "#2f7a52",
};

const WELCOME: Message = {
  role: "assistant",
  kind: "text",
  content:
    "Hey — your cognitive load is elevated right now. That's exactly when your mental queue gets overwhelming.\n\nDump everything on your mind below — tasks, errands, worries, anything. I'll prioritize it by impact & effort and suggest what to delegate so you can focus on what actually matters. 🧠",
};

function TaskCard({ t, index }: { t: Task; index: number }) {
  const style = QUADRANT_STYLE[t.quadrant] ?? QUADRANT_STYLE["Schedule"];
  return (
    <div className="ctc-task-card" style={{ animationDelay: `${index * 60}ms` }}>
      <div className="ctc-task-top">
        <span className="ctc-task-name">{t.task}</span>
        <span
          className="ctc-task-quadrant"
          style={{ background: style.bg, color: style.color }}
        >
          {style.icon} {t.quadrant}
        </span>
      </div>
      <div className="ctc-task-meta">
        <span style={{ color: IMPACT_COLOR[t.impact] }}>
          Impact: <strong>{t.impact}</strong>
        </span>
        <span className="muted">·</span>
        <span className="muted">
          Effort: <strong>{t.effort}</strong>
        </span>
      </div>
      <div className="ctc-task-delegation">{t.delegation}</div>
    </div>
  );
}

function Bubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return <div className="ctc-bubble ctc-bubble-user">{msg.content}</div>;
  }
  if (msg.kind === "text") {
    return (
      <div className="ctc-bubble ctc-bubble-bot">
        {msg.content.split("\n").map((line, i) =>
          line ? <p key={i} style={{ margin: "4px 0" }}>{line}</p> : <br key={i} />
        )}
      </div>
    );
  }
  const resp = msg.content;
  return (
    <div className="ctc-bubble ctc-bubble-bot ctc-bubble-wide">
      <p className="ctc-intro">Here&apos;s your prioritized task list:</p>
      <div className="ctc-task-list">
        {resp.tasks.map((t, i) => (
          <TaskCard key={i} t={t} index={i} />
        ))}
      </div>
      {resp.summary && (
        <div className="ctc-summary">💬 {resp.summary}</div>
      )}
    </div>
  );
}

export function ChatTab({ userId = "joshu" }: { userId?: string }) {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function submit() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const resp = await fetch("/api/chat/prioritize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks: text, user_id: userId }),
      });
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: PrioritizeResponse = await resp.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", kind: "tasks", content: data },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          kind: "text",
          content: "Couldn't reach the server right now. Try again in a moment.",
        },
      ]);
    }
    setLoading(false);
  }

  return (
    <div className="ctc-shell">
      {/* context banner */}
      <div className="ctc-context-banner">
        <span className="ctc-banner-icon">🧠</span>
        <div>
          <strong>Task Copilot</strong>
          <p className="ctc-banner-sub">
            Brain-dump your mental queue. We&apos;ll prioritize by impact &amp;
            effort and suggest smart shortcuts.
          </p>
        </div>
      </div>

      {/* message feed */}
      <div className="ctc-messages">
        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}
        {loading && (
          <div className="ctc-bubble ctc-bubble-bot ctc-typing">
            <span /><span /><span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* input */}
      <div className="ctc-input-row">
        <textarea
          className="ctc-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="e.g. reply to Sarah's email, fix login bug, buy groceries, prepare for 3pm meeting, I haven't eaten yet..."
          rows={3}
          disabled={loading}
        />
        <button
          className="ctc-send-btn"
          onClick={submit}
          disabled={loading || !input.trim()}
        >
          {loading ? "…" : "↑"}
        </button>
      </div>
    </div>
  );
}
