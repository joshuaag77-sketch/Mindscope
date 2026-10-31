import { authorize, backendHeaders } from "@/lib/security";
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.MINDSCOPE_API_URL ?? "http://127.0.0.1:8000";

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const denied = await authorize(_req);
  if (denied) return denied;
  const { userId } = await params;
  try {
    const resp = await fetch(
      `${BACKEND}/api/v1/alerts/fire-demo/${encodeURIComponent(userId)}`,
      { method: "POST", headers: backendHeaders(), signal: AbortSignal.timeout(15000) }
    );
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 });
  }
}
