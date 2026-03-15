"use client";

import { useEffect, useRef, useState } from "react";

import { ChatTab } from "@/components/chat-tab";
import { DashboardShell } from "@/components/dashboard-shell";
import { fetchDashboardData } from "@/lib/api";
import { DashboardData, mockDashboardData } from "@/lib/mock-data";

type Tab = "monitor" | "copilot";

function useTabFromUrl(): [Tab, (t: Tab) => void] {
  const [tab, setTabState] = useState<Tab>("monitor");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("tab") === "copilot") setTabState("copilot");
  }, []);

  function setTab(t: Tab) {
    setTabState(t);
    const url = new URL(window.location.href);
    if (t === "copilot") url.searchParams.set("tab", "copilot");
    else url.searchParams.delete("tab");
    window.history.replaceState(null, "", url.toString());
  }

  return [tab, setTab];
}

export function DashboardLive({ userId = "joshu" }: { userId?: string }) {
  const [data, setData] = useState<DashboardData>(mockDashboardData);
  const [tab, setTab] = useTabFromUrl();
  const [firing, setFiring] = useState(false);
  const [fireResult, setFireResult] = useState<string | null>(null);
  const fireTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let active = true;
    async function refresh() {
      const latest = await fetchDashboardData(userId);
      if (active) setData(latest);
    }
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [userId]);

  async function fireDemoAlert() {
    if (firing) return;
    setFiring(true);
    setFireResult(null);
    try {
      const resp = await fetch(
        `/api/alerts/fire-demo/${encodeURIComponent(userId)}`,
        { method: "POST" }
      );
      const state = await resp.json();
      if (state.alert_active) {
        setFireResult("✅ Alert fired — check your inbox!");
      } else {
        setFireResult("⚠️ Trigger sent but alert_active=false — check backend logs.");
      }
    } catch {
      setFireResult("❌ Could not reach backend.");
    }
    setFiring(false);
    if (fireTimerRef.current) clearTimeout(fireTimerRef.current);
    fireTimerRef.current = setTimeout(() => setFireResult(null), 8000);
  }

  return (
    <div>
      {/* ── Tab Bar ── */}
      <div className="demo-tab-bar">
        <div className="demo-tab-group">
          <button
            className={`demo-tab-btn${tab === "monitor" ? " demo-tab-active" : ""}`}
            onClick={() => setTab("monitor")}
          >
            📊 Live Monitor
          </button>
          <button
            className={`demo-tab-btn${tab === "copilot" ? " demo-tab-active" : ""}`}
            onClick={() => setTab("copilot")}
          >
            🧠 Task Copilot
          </button>
        </div>

        <div className="demo-fire-group">
          {fireResult && (
            <span className="demo-fire-result">{fireResult}</span>
          )}
          <button
            className="demo-fire-btn"
            onClick={fireDemoAlert}
            disabled={firing}
            title="Reset alert state then immediately send a real overload email"
          >
            {firing ? "Sending…" : "🔥 Fire Demo Alert"}
          </button>
        </div>
      </div>

      {/* ── Tab Content ── */}
      {tab === "monitor" && <DashboardShell data={data} />}
      {tab === "copilot" && <ChatTab userId={userId} />}
    </div>
  );
}
