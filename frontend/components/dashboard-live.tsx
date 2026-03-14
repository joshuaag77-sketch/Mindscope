"use client";

import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { fetchDashboardData } from "@/lib/api";
import { DashboardData, mockDashboardData } from "@/lib/mock-data";

export function DashboardLive({ userId = "joshu" }: { userId?: string }) {
  const [data, setData] = useState<DashboardData>(mockDashboardData);

  useEffect(() => {
    let active = true;

    async function refresh() {
      const latest = await fetchDashboardData(userId);
      if (active) {
        setData(latest);
      }
    }

    refresh();
    const timer = setInterval(refresh, 5000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [userId]);

  return <DashboardShell data={data} />;
}
