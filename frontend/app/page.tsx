import { DashboardLive } from "@/components/dashboard-live";

export const dynamic = "force-dynamic";

export default function DashboardPage() {
  const userId = process.env.MINDSCOPE_USER_ID || process.env.USERNAME || "local-user";
  return <DashboardLive userId={userId} />;
}
