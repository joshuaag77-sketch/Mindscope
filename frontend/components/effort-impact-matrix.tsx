"use client";

import { useState } from "react";
import { DayPlanner } from "@/components/day-planner";

export interface MatrixTask {
  task: string;
  effort_score: number;
  impact_score: number;
  duration_minutes: number;
  quadrant: "Do Now" | "Schedule" | "Delegate" | "Drop";
  delegation?: string | null;
}

interface Block {
  task: string;
  start: string;
  end: string;
  duration_minutes: number;
  quadrant: string | null;
  block_type: "task" | "buffer";
}

export interface Schedule {
  blocks: Block[];
  total_focus_minutes: number;
  suggested_end: string;
  note: string;
}

const Q_CFG = {
  "Do Now":   { color: "#b34236", bg: "rgba(179,66,54,0.07)",   border: "rgba(179,66,54,0.22)",  icon: "🔥", sub: "High Impact · Low Effort" },
  "Schedule": { color: "#c8891a", bg: "rgba(200,137,26,0.07)",  border: "rgba(200,137,26,0.22)", icon: "📅", sub: "High Impact · High Effort" },
  "Delegate": { color: "#2f7a52", bg: "rgba(47,122,82,0.07)",   border: "rgba(47,122,82,0.22)",  icon: "🤝", sub: "Low Impact · Low Effort" },
  "Drop":     { color: "#6c5a4f", bg: "rgba(108,90,79,0.05)",   border: "rgba(108,90,79,0.15)",  icon: "🗑️", sub: "Low Impact · High Effort" },
} as const;

function MiniScoreBar({ value, max = 10, color }: { value: number; max?: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5, flex: 1 }}>
      <div style={{ flex: 1, height: 3, background: "rgba(0,0,0,0.08)", borderRadius: 99, overflow: "hidden" }}>
        <div style={{ width: `${(value / max) * 100}%`, height: "100%", background: color, borderRadius: 99 }} />
      </div>
      <span style={{ fontSize: 10, color, fontWeight: 700, minWidth: 14 }}>{value}</span>
    </div>
  );
}

function MatrixTaskCard({ task, qColor, qBorder }: { task: MatrixTask; qColor: string; qBorder: string }) {
  return (
    <div className="mx-card">
      <div className="mx-card-name">{task.task}</div>
      <div className="mx-card-scores">
        <div className="mx-card-score-row">
          <span style={{ fontSize: 10, color: "#6c5a4f", minWidth: 12 }}>I</span>
          <MiniScoreBar value={task.impact_score} color="#b34236" />
        </div>
        <div className="mx-card-score-row">
          <span style={{ fontSize: 10, color: "#6c5a4f", minWidth: 12 }}>E</span>
          <MiniScoreBar value={task.effort_score} color="#c8891a" />
        </div>
      </div>
      <div className="mx-card-footer">
        <span className="mx-card-duration">⏱ {task.duration_minutes}min</span>
        {task.delegation && (
          <span className="mx-card-delegation" style={{ borderColor: qBorder, color: qColor }}>
            → {task.delegation}
          </span>
        )}
      </div>
    </div>
  );
}

function Quadrant({ q, tasks }: { q: keyof typeof Q_CFG; tasks: MatrixTask[] }) {
  const cfg = Q_CFG[q];
  return (
    <div className="mx-quadrant" style={{ background: cfg.bg, borderColor: cfg.border }}>
      <div className="mx-q-header" style={{ color: cfg.color }}>
        <span className="mx-q-icon">{cfg.icon}</span>
        <div>
          <span className="mx-q-label">{q}</span>
          <span className="mx-q-sub">{cfg.sub}</span>
        </div>
        {tasks.length > 0 && (
          <span className="mx-q-count" style={{ background: cfg.color + "22", color: cfg.color }}>
            {tasks.length}
          </span>
        )}
      </div>
      <div className="mx-cards-list">
        {tasks.length === 0
          ? <span className="mx-empty">None</span>
          : tasks.map((t, i) => <MatrixTaskCard key={i} task={t} qColor={cfg.color} qBorder={cfg.border} />)
        }
      </div>
    </div>
  );
}

export function EffortImpactMatrix({ tasks, summary }: { tasks: MatrixTask[]; summary?: string }) {
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(false);

  const byQ = (q: keyof typeof Q_CFG) => tasks.filter(t => t.quadrant === q);
  const actionable = byQ("Do Now").length + byQ("Schedule").length;

  async function optimizeDay() {
    setLoading(true);
    try {
      const now = new Date();
      const h = now.getHours();
      const m = Math.ceil(now.getMinutes() / 15) * 15;
      const start_time = `${String(h).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
      const resp = await fetch("/api/chat/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks, start_time }),
      });
      const data: Schedule = await resp.json();
      setSchedule(data);
      setTimeout(() => {
        document.getElementById("mx-planner-anchor")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch {
      // silent fail
    }
    setLoading(false);
  }

  return (
    <div className="mx-shell">
      {/* Header */}
      <div className="mx-header">
        <div>
          <p className="mx-title">⚡ Effort – Impact Matrix</p>
          <p className="mx-subtitle">{tasks.length} tasks · {actionable} to action today</p>
        </div>
      </div>

      {/* Axis labels */}
      <div className="mx-axis-row">
        <div className="mx-y-axis">
          <span>High Impact ↑</span>
          <span>Low Impact ↓</span>
        </div>
        <div className="mx-main">
          <div className="mx-x-labels">
            <span>← Low Effort</span>
            <span>High Effort →</span>
          </div>
          {/* 2×2 grid */}
          <div className="mx-grid">
            <Quadrant q="Do Now"   tasks={byQ("Do Now")} />
            <Quadrant q="Schedule" tasks={byQ("Schedule")} />
            <Quadrant q="Delegate" tasks={byQ("Delegate")} />
            <Quadrant q="Drop"     tasks={byQ("Drop")} />
          </div>
        </div>
      </div>

      {summary && <div className="ctc-summary">💬 {summary}</div>}

      {/* Optimize button */}
      {!schedule && actionable > 0 && (
        <button className="mx-optimize-btn" onClick={optimizeDay} disabled={loading}>
          {loading ? "⏳ Building your day plan…" : "✨ Optimize My Day →"}
        </button>
      )}

      {/* Day planner */}
      <div id="mx-planner-anchor">
        {schedule && <DayPlanner schedule={schedule} onReset={() => setSchedule(null)} />}
      </div>
    </div>
  );
}
