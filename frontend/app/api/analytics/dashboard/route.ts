import { NextResponse } from "next/server";

const API_BASE = process.env.MINDSCOPE_API_URL ?? "http://127.0.0.1:8000";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get("user_id");
  const limit = searchParams.get("limit") ?? "48";
  const queryUser = userId ? `user_id=${encodeURIComponent(userId)}&` : "";
  const url = `${API_BASE}/api/v1/analytics/dashboard?${queryUser}limit=${encodeURIComponent(limit)}&ingest_if_needed=true`;
  try {
    const response = await fetch(url, { cache: "no-store" });
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: `Proxy failed: ${error instanceof Error ? error.message : "unknown"}` },
      { status: 502 },
    );
  }
}
