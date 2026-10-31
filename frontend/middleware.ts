import { NextRequest, NextResponse } from "next/server";
import { authorize } from "./lib/security";

export async function middleware(request: NextRequest) {
  const denied = await authorize(request);
  if (denied) return denied;
  const response = NextResponse.next();
  response.headers.set("Cache-Control", "no-store");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}

export const config = { matcher: "/:path*" };
