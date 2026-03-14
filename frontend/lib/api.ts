import { DashboardData, mockDashboardData } from "@/lib/mock-data";

type DashboardResponse = {
  source: string;
  current: {
    timestamp_start: string;
    user_id: string;
    overload_score: number;
    state_band: string;
    fragmentation_score: number;
    focus_instability_score: number;
    interruption_score: number;
    nearest_scenario: string;
    top_drivers: string[];
    alert_state?: {
      alert_active: boolean;
      consecutive_high_windows: number;
      consecutive_critical_windows: number;
      triggered_rule: string | null;
    };
  };
  history: Array<{
    timestamp_start: string;
    overload_score: number;
  }>;
  summary: {
    windows_tracked: number;
    avg_score: number;
    max_score: number;
    high_risk_windows: number;
    latest_band: string;
  };
};

function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    return "";
  }
  return process.env.MINDSCOPE_API_URL ?? "http://127.0.0.1:8000";
}

async function fetchJsonWithTimeout<T>(url: string, timeoutMs = 4000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatTrendLabel(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export async function fetchDashboardData(userId?: string): Promise<DashboardData> {
  const baseUrl = getApiBaseUrl();
  try {
    const queryUser = userId ? `user_id=${encodeURIComponent(userId)}&` : "";
    const endpoint =
      typeof window === "undefined"
        ? `${baseUrl}/api/v1/analytics/dashboard?${queryUser}limit=48&ingest_if_needed=true`
        : `/api/analytics/dashboard?${queryUser}limit=48`;
    const payload = await fetchJsonWithTimeout<DashboardResponse>(endpoint);
    const history = payload.history ?? [];
    const scores = history.map((item) => item.overload_score);
    const labels = history.map((item) => formatTrendLabel(item.timestamp_start));
    return {
      userId: payload.current.user_id,
      timestampLabel: formatTimestamp(payload.current.timestamp_start),
      source: payload.source,
      overloadScore: payload.current.overload_score,
      stateBand: payload.current.state_band,
      fragmentationScore: payload.current.fragmentation_score,
      focusInstabilityScore: payload.current.focus_instability_score,
      interruptionScore: payload.current.interruption_score,
      nearestScenario: payload.current.nearest_scenario,
      topDrivers: payload.current.top_drivers,
      trendScores: scores.length > 0 ? scores : mockDashboardData.trendScores,
      trendLabels: labels.length > 0 ? labels : mockDashboardData.trendLabels,
      summary: {
        windowsTracked: payload.summary.windows_tracked,
        avgScore: payload.summary.avg_score,
        maxScore: payload.summary.max_score,
        highRiskWindows: payload.summary.high_risk_windows,
        latestBand: payload.summary.latest_band,
      },
      alertStatus: {
        alertActive: payload.current.alert_state?.alert_active ?? false,
        consecutiveHighWindows:
          payload.current.alert_state?.consecutive_high_windows ?? 0,
        consecutiveCriticalWindows:
          payload.current.alert_state?.consecutive_critical_windows ?? 0,
        triggeredRule: payload.current.alert_state?.triggered_rule ?? null,
      },
    };
  } catch {
    return mockDashboardData;
  }
}
