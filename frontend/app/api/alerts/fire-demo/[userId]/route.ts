import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.MINDSCOPE_API_URL ?? "http://127.0.0.1:8000";

export async function POST(
  _req: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const resp = await fetch(
      `${BACKEND}/api/v1/alerts/fire-demo/${encodeURIComponent(params.userId)}`,
      { method: "POST" }
    );
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 502 });
  }
}
