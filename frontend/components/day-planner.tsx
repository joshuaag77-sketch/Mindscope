"use client";

import { Schedule } from "@/components/effort-impact-matrix";

const Q_COLOR: Record<string, string> = {
  "Do Now":   "#b34236",
  "Schedule": "#c8891a",
  "Delegate": "#2f7a52",
  "Drop":     "#6c5a4f",
};

function generateICS(blocks: Schedule["blocks"]): string {
  const today = new Date();
  const y = today.getFullYear();
  const mo = String(today.getMonth() + 1).padStart(2, "0");
  const d = String(today.getDate()).padStart(2, "0");
  const ds = `${y}${mo}${d}`;
  let ics = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//MindScope//TaskCopilot//EN\r\nCALSCALE:GREGORIAN\r\n";
  for (const b of blocks) {
    if (b.block_type !== "task" && b.block_type !== "schedule") continue;
    if (b.task === "Buffer" || b.task === "Break") continue;
    const [sh, sm] = b.start.split(":").map(Number);
    const [eh, em] = b.end.split(":").map(Number);
    const dtS = `${ds}T${String(sh).padStart(2,"0")}${String(sm).padStart(2,"0")}00`;
    const dtE = `${ds}T${String(eh).padStart(2,"0")}${String(em).padStart(2,"0")}00`;
    ics += `BEGIN:VEVENT\r\nSUMMARY:${b.task}\r\nDTSTART:${dtS}\r\nDTEND:${dtE}\r\nDESCRIPTION:${b.quadrant ?? ""} — scheduled by MindScope\r\nEND:VEVENT\r\n`;
  }
  ics += "END:VCALENDAR";
  return ics;
}

function downloadICS(ics: string) {
  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "mindscope-schedule.ics";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function DayPlanner({ schedule, onReset }: { schedule: Schedule; onReset?: () => void }) {
  const taskCount = schedule.blocks.filter(b => b.block_type === "task").length;
  const h = Math.floor(schedule.total_focus_minutes / 60);
  const m = schedule.total_focus_minutes % 60;
  const focusLabel = h > 0 ? `${h}h${m > 0 ? ` ${m}m` : ""}` : `${m}m`;

  return (
    <div className="dp-shell">
      <div className="dp-header">
        <div>
          <p className="dp-title">📆 Your Day Plan</p>
          <p className="dp-subtitle">
            {taskCount} tasks &middot; {focusLabel} focused &middot; done by {schedule.suggested_end}
          </p>
        </div>
        <div className="dp-actions">
          <button
            className="dp-export-btn"
            onClick={() => downloadICS(generateICS(schedule.blocks))}
          >
            ↓ Export .ics
          </button>
          {onReset && (
            <button className="dp-reset-btn" onClick={onReset}>
              Rebuild
            </button>
          )}
        </div>
      </div>

      <div className="dp-timeline">
        {schedule.blocks.map((block, i) => {
          if (block.block_type === "buffer" || block.block_type === "break") {
            return (
              <div key={i} className="dp-buffer-row">
                <span className="dp-buf-time">{block.start}</span>
                <span className="dp-buf-bar" />
                <span className="dp-buf-label">
                  {block.task === "Break" ? "☕ Break (10 min)" : "· · ·"}
                </span>
              </div>
            );
          }
          const color = Q_COLOR[block.quadrant ?? ""] ?? "#6c5a4f";
          return (
            <div key={i} className="dp-block" style={{ borderLeftColor: color }}>
              <div className="dp-block-times">
                <span className="dp-t-start">{block.start}</span>
                <span className="dp-t-arrow">→</span>
                <span className="dp-t-end">{block.end}</span>
              </div>
              <div className="dp-block-body">
                <span className="dp-block-name">{block.task}</span>
                <div className="dp-block-tags">
                  <span className="dp-block-tag" style={{ background: color + "1a", color }}>
                    {block.quadrant}
                  </span>
                  <span className="dp-block-tag dp-block-tag-neutral">
                    ⏱ {block.duration_minutes}min
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {schedule.note && (
        <div className="dp-note">💬 {schedule.note}</div>
      )}
    </div>
  );
}
