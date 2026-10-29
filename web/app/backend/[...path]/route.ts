/**
 * Same-origin proxy to the FastAPI process.
 *
 * ``API_INTERNAL_URL`` is read at request time so Docker can point at
 * ``http://api:8000`` without rebuilding the Next.js bundle. The browser
 * only ever calls ``/backend/...`` on this app.
 */

import { NextRequest, NextResponse } from "next/server";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

type RouteContext = { params: Promise<{ path: string[] }> };

function apiBase(): string {
  const configured = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/$/, "");
}

function forwardHeaders(source: Headers): Headers {
  const headers = new Headers();
  source.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}

async function proxy(request: NextRequest, path: string[]): Promise<NextResponse> {
  const target = `${apiBase()}/${path.join("/")}${request.nextUrl.search}`;
  const method = request.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method,
      headers: forwardHeaders(request.headers),
      body,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "The chat API is not reachable. Start it with `uv run python run_api.py` or Docker Compose." },
      { status: 502 },
    );
  }

  if (upstream.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  return new NextResponse(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: forwardHeaders(upstream.headers),
  });
}

export async function GET(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function POST(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function DELETE(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const { path } = await context.params;
  return proxy(request, path);
}
