"use client";

import { useEffect, useRef, useState } from "react";
import { EffortImpactMatrix, MatrixTask } from "@/components/effort-impact-matrix";

interface PrioritizeResponse {
  type?: "tasks" | "message";
  tasks?: MatrixTask[];
  summary?: string;
  message?: string;
}

type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; kind: "text"; content: string }
  | { role: "assistant"; kind: "matrix"; content: PrioritizeResponse };

const WELCOME: Message = {
  role: "assistant",
  kind: "text",
  content:
    "Hey — your cognitive load is elevated right now. That's exactly when everything feels urgent at once.\n\nDump everything on your mind below — tasks, errands, worries, anything. I'll map them onto an Effort–Impact Matrix, suggest what to delegate, and build you a focused day plan. 🧠",
};

function Bubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return <div className="ctc-bubble ctc-bubble-user">{msg.content}</div>;
  }
  if (msg.kind === "text") {
    return (
      <div className="ctc-bubble ctc-bubble-bot">
        {msg.content.split("\n").map((line, i) =>
          line
            ? <p key={i} style={{ margin: "4px 0" }}>{line}</p>
            : <br key={i} />
        )}
      </div>
    );
  }
  // Matrix response
  const resp = msg.content;
  if (resp.type === "message" || (!resp.tasks && resp.message)) {
    return (
      <div className="ctc-bubble ctc-bubble-bot">
        {(resp.message ?? "").split("\n").map((line, i) =>
          line ? <p key={i} style={{ margin: "4px 0" }}>{line}</p> : <br key={i} />
        )}
      </div>
    );
  }
  return (
    <div className="ctc-bubble ctc-bubble-bot ctc-bubble-wide">
      <EffortImpactMatrix tasks={resp.tasks ?? []} summary={resp.summary} />
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
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const resp = await fetch("/api/chat/prioritize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks: text, user_id: userId }),
      });
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data: PrioritizeResponse = await resp.json();
      if (data.type === "message") {
        setMessages(prev => [...prev, { role: "assistant", kind: "text", content: data.message ?? "" }]);
      } else {
        setMessages(prev => [...prev, { role: "assistant", kind: "matrix", content: data }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant", kind: "text",
        content: "Couldn't reach the server right now. Try again in a moment.",
      }]);
    }
    setLoading(false);
  }

  return (
    <div className="ctc-shell">
      <div className="ctc-context-banner">
        <span className="ctc-banner-icon">🧠</span>
        <div>
          <strong>Task Copilot</strong>
          <p className="ctc-banner-sub">
            Brain-dump your tasks. Get an Effort–Impact Matrix + a focused day plan.
          </p>
        </div>
      </div>

      <div className="ctc-messages">
        {messages.map((m, i) => <Bubble key={i} msg={m} />)}
        {loading && (
          <div className="ctc-bubble ctc-bubble-bot ctc-typing">
            <span /><span /><span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="ctc-input-row">
        <textarea
          className="ctc-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
          placeholder="e.g. reply to Sarah's email, fix login bug, buy groceries, prepare for 3pm meeting, I'm starving..."
          rows={3}
          disabled={loading}
        />
        <button className="ctc-send-btn" onClick={submit} disabled={loading || !input.trim()}>
          {loading ? "…" : "↑"}
        </button>
      </div>
    </div>
  );
}
