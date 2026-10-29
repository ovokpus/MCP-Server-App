/** Shapes returned by the FastAPI chat service. */

export type AgentChoice = "react" | "state_graph";

export type BackendName = "local" | "openai";

export type ToolInfo = {
  name: string;
  description: string;
};

export type ToolTrace = {
  name: string;
  arguments: Record<string, unknown>;
  result: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  toolCalls: ToolTrace[];
  backend?: BackendName;
  agent?: AgentChoice;
};

export type HealthResponse = {
  status: "ok" | "degraded";
  backend: BackendName;
  ready: boolean;
  detail: string;
  tool_count: number;
  model: string | null;
};

export type ChatResponse = {
  session_id: string;
  reply: string;
  backend: BackendName;
  agent: AgentChoice;
  tool_calls: ToolTrace[];
};
