/**
 * Browser calls into the Next.js proxy at ``/backend/*``.
 * The proxy reads ``API_INTERNAL_URL`` on the server, so the browser never
 * needs a cross-origin API address.
 */

import type { AgentChoice, ChatResponse, HealthResponse, ToolInfo } from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
      return JSON.stringify(detail);
    }
  } catch {
    // Non-JSON bodies fall through to the status text.
  }
  return response.statusText || "Request failed";
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/backend/health");
}

export function getTools(): Promise<ToolInfo[]> {
  return requestJson<ToolInfo[]>("/backend/api/tools");
}

export function callTool(name: string, arguments_: Record<string, unknown>): Promise<{ name: string; result: string }> {
  return requestJson("/backend/api/tools/call", {
    method: "POST",
    body: JSON.stringify({ name, arguments: arguments_ }),
  });
}

export function sendChat(input: {
  message: string;
  sessionId: string | null;
  agent: AgentChoice;
}): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/backend/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message: input.message,
      session_id: input.sessionId,
      agent: input.agent,
    }),
  });
}

export function deleteSession(sessionId: string): Promise<void> {
  return requestJson<void>(`/backend/api/sessions/${sessionId}`, { method: "DELETE" });
}
