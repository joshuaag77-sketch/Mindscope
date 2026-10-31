import { NextRequest, NextResponse } from "next/server";

async function equal(left: string, right: string) {
  const bytes = new TextEncoder();
  const [a, b] = await Promise.all([left, right].map(value => crypto.subtle.digest("SHA-256", bytes.encode(value))));
  const x = new Uint8Array(a), y = new Uint8Array(b);
  let difference = 0;
  for (let i = 0; i < x.length; i++) difference |= x[i] ^ y[i];
  return difference === 0;
}

export async function authorize(request: NextRequest) {
  const password = process.env.MINDSCOPE_WEB_PASSWORD ?? "";
  if (password.length < 32) return NextResponse.json({ error: "Authentication is not configured" }, { status: 503 });
  const expected = `Basic ${btoa(`${process.env.MINDSCOPE_WEB_USERNAME ?? "owner"}:${password}`)}`;
  if (!(await equal(request.headers.get("authorization") ?? "", expected))) {
    return new NextResponse("Authentication required", { status: 401, headers: { "WWW-Authenticate": 'Basic realm="Mindscope", charset="UTF-8"', "Cache-Control": "no-store" } });
  }
  const origin = request.headers.get("origin");
  const allowed = ["http://127.0.0.1:3000", "http://localhost:3000"];
  if ((origin && !allowed.includes(origin)) || request.headers.get("sec-fetch-site") === "cross-site") {
    return NextResponse.json({ error: "Origin not permitted" }, { status: 403 });
  }
  if (Number(request.headers.get("content-length")) > 32768) return NextResponse.json({ error: "Request too large" }, { status: 413 });
  return null;
}

export function backendHeaders() {
  const token = process.env.MINDSCOPE_API_TOKEN ?? "";
  if (token.length < 32) throw new Error("Backend authentication is not configured");
  return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
}

export async function boundedJson(request: NextRequest) {
  const reader = request.body?.getReader();
  if (!reader) throw new Error("Missing body");
  const chunks: Uint8Array[] = [];
  let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.length;
    if (length > 32768) { await reader.cancel(); throw new Error("Request too large"); }
    chunks.push(value);
  }
  const combined = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { combined.set(chunk, offset); offset += chunk.length; }
  return JSON.parse(new TextDecoder().decode(combined));
}
