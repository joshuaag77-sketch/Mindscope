import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const METRICS = [
  { key: "app_switch_count", label: "App Switches", unit: "/ 10 min", overload_direction: "high", description: "Switching between applications frequently signals fragmented attention." },
  { key: "distinct_app_count", label: "Distinct Apps Open", unit: "apps", overload_direction: "high", description: "More apps open in parallel correlates with multitasking overload." },
  { key: "focus_streak_minutes", label: "Focus Streak", unit: "min", overload_direction: "low", description: "Longer unbroken focus streaks indicate healthy deep-work capacity." },
  { key: "afk_count", label: "AFK Events", unit: "events", overload_direction: "high", description: "Frequent away-from-keyboard breaks suggest interruption overload." },
  { key: "afk_minutes", label: "AFK Time", unit: "min", overload_direction: "high", description: "Time spent away from the keyboard in each 10-minute window." },
  { key: "work_context_entropy", label: "Context Entropy", unit: "bits", overload_direction: "high", description: "High entropy means attention is spread thinly across many contexts." },
  { key: "work_reentry_count", label: "Work Re-entries", unit: "/ 10 min", overload_direction: "high", description: "Returning to a task after switching away — a fragmentation signal." },
] as const;

function stripQuotes(v: string) {
  return v.replace(/"/g, "").trim();
}

function parseCsv(text: string) {
  const clean = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  const lines = clean.split("\n").map(l => l.trim()).filter(Boolean);
  const headers = lines[0].split(",").map(stripQuotes);
  return lines.slice(1).map(line => {
    const vals = line.split(",");
    const row: Record<string, string> = {};
    headers.forEach((h, i) => { row[h] = stripQuotes(vals[i] ?? ""); });
    return row;
  });
}

function avg(arr: number[]) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

export async function GET() {
  try {
    const csvPath = path.resolve(process.cwd(), "..", "backend", "data", "baseline_profile.csv");
    if (!fs.existsSync(csvPath)) {
      return NextResponse.json({ error: "baseline_profile.csv not found at " + csvPath, row_count: 0, metrics: [], hourly: [] });
    }
    const rows = parseCsv(fs.readFileSync(csvPath, "utf-8"));
    const meanTotals: Record<string, number[]> = {};
    const stdTotals: Record<string, number[]> = {};
    const hourlyMap: Record<number, Record<string, number[]>> = {};

    for (const row of rows) {
      const hour = parseInt(row["hour_of_day"], 10);
      if (!hourlyMap[hour]) hourlyMap[hour] = {};
      for (const m of METRICS) {
        const mv = parseFloat(row[m.key + "_mean"] ?? "0") || 0;
        const sv = parseFloat(row[m.key + "_std"] ?? "0") || 0;
        if (!meanTotals[m.key]) { meanTotals[m.key] = []; stdTotals[m.key] = []; }
        meanTotals[m.key].push(mv);
        stdTotals[m.key].push(sv);
        if (!hourlyMap[hour][m.key]) hourlyMap[hour][m.key] = [];
        hourlyMap[hour][m.key].push(mv);
      }
    }

    const metrics = METRICS.map(m => ({
      ...m,
      mean: parseFloat(avg(meanTotals[m.key] ?? [0]).toFixed(3)),
      std: parseFloat(avg(stdTotals[m.key] ?? [1]).toFixed(3)),
    }));

    const hourly = Object.keys(hourlyMap).map(Number).sort((a, b) => a - b).map(hour => {
      const entry: Record<string, number> = { hour };
      for (const m of METRICS) entry[m.key] = parseFloat(avg(hourlyMap[hour][m.key] ?? [0]).toFixed(3));
      return entry;
    });

    return NextResponse.json({ row_count: rows.length, metrics, hourly });
  } catch (error) {
    return NextResponse.json({ error: String(error), row_count: 0, metrics: [], hourly: [] }, { status: 500 });
  }
}
