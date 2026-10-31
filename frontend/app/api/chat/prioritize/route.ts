import { authorize, backendHeaders, boundedJson } from "@/lib/security";
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.MINDSCOPE_API_URL ?? "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  const denied = await authorize(req);
  if (denied) return denied;
  try {
    const body = await boundedJson(req);
    const resp = await fetch(`${BACKEND}/api/v1/chat/prioritize`, {
      method: "POST",
      headers: backendHeaders(),
      signal: AbortSignal.timeout(30000),
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    return NextResponse.json({ error: "Request failed or upstream unavailable" }, { status: 502 });
  }
}
