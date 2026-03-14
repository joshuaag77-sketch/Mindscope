export type AlertStatus = {
  alertActive: boolean;
  consecutiveHighWindows: number;
  consecutiveCriticalWindows: number;
  triggeredRule: string | null;
};

export type DashboardData = {
  userId: string;
  timestampLabel: string;
  source: string;
  overloadScore: number;
  stateBand: string;
  fragmentationScore: number;
  focusInstabilityScore: number;
  interruptionScore: number;
  nearestScenario: string;
  topDrivers: string[];
  trendScores: number[];
  trendLabels: string[];
  summary: {
    windowsTracked: number;
    avgScore: number;
    maxScore: number;
    highRiskWindows: number;
    latestBand: string;
  };
  alertStatus: AlertStatus;
};

export const mockDashboardData: DashboardData = {
  userId: "demo-user",
  timestampLabel: "Tuesday, March 10 at 9:40 AM",
  source: "synthetic_fallback",
  overloadScore: 82,
  stateBand: "Sustained Overload Risk",
  fragmentationScore: 84,
  focusInstabilityScore: 77,
  interruptionScore: 63,
  nearestScenario: "overload",
  topDrivers: [
    "App switching is 113% above baseline",
    "Focus streak is 67% below baseline",
    "Work context entropy is 58% above baseline",
  ],
  trendScores: [32, 38, 42, 57, 64, 73, 81, 82],
  trendLabels: ["1", "2", "3", "4", "5", "6", "7", "8"],
  summary: {
    windowsTracked: 8,
    avgScore: 58,
    maxScore: 82,
    highRiskWindows: 3,
    latestBand: "Sustained Overload Risk",
  },
  alertStatus: {
    alertActive: true,
    consecutiveHighWindows: 3,
    consecutiveCriticalWindows: 1,
    triggeredRule: "high_3x",
  },
};
