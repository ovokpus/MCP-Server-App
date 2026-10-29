"use client";

import { FormEvent, useEffect, useId, useState } from "react";
import { ApiError, callTool, deleteSession, getHealth, getTools, sendChat } from "../lib/api";
import type { AgentChoice, BackendName, ChatMessage, HealthResponse, ToolInfo } from "../lib/types";
import { RichText } from "./rich-text";

const SUGGESTIONS = [
  "Roll 2d6",
  "Roll a d20 and create a quote card about shipping",
  "Create a LinkedIn post about Python",
  "Get a slide image about robots",
  "Search GitHub for langgraph",
];

const DICE_ARGUMENTS = '{\n  "notation": "2d6",\n  "num_rolls": 1\n}';

const TOOL_TEMPLATES: Record<string, string> = {
  roll_dice: DICE_ARGUMENTS,
  web_search: '{\n  "query": "model context protocol"\n}',
  create_social_post: '{\n  "topic": "shipping software",\n  "style": "professional"\n}',
  get_slide_image: '{\n  "topic": "robots",\n  "size": "1920x1080"\n}',
  create_quote_card: '{\n  "theme": "motivation"\n}',
  github_search_repositories: '{\n  "query": "langgraph",\n  "limit": 3\n}',
  github_get_repository_info: '{\n  "owner": "octocat",\n  "repo": "Hello-World"\n}',
  github_get_file_content: '{\n  "owner": "octocat",\n  "repo": "Hello-World",\n  "file_path": "README",\n  "branch": "master"\n}',
  github_list_files: '{\n  "owner": "octocat",\n  "repo": "Hello-World",\n  "path": ""\n}',
  github_auth_status: "{}",
};

function templateFor(name: string): string {
  return TOOL_TEMPLATES[name] ?? "{}";
}

function agentLabel(agent: AgentChoice): string {
  switch (agent) {
    case "react":
      return "ReAct";
    case "state_graph":
      return "State graph";
    default: {
      const unexpected: never = agent;
      return unexpected;
    }
  }
}

function backendLabel(backend: BackendName): string {
  switch (backend) {
    case "local":
      return "Local tools";
    case "openai":
      return "LangGraph";
    default: {
      const unexpected: never = backend;
      return unexpected;
    }
  }
}

function roleLabel(role: ChatMessage["role"]): string {
  switch (role) {
    case "user":
      return "You";
    case "assistant":
      return "Agent";
    default: {
      const unexpected: never = role;
      return unexpected;
    }
  }
}

export function ChatApp() {
  const messageId = useId();
  const toolArgsId = useId();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [banner, setBanner] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [agent, setAgent] = useState<AgentChoice>("react");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [selectedTool, setSelectedTool] = useState("roll_dice");
  const [toolArguments, setToolArguments] = useState(DICE_ARGUMENTS);
  const [toolResult, setToolResult] = useState<string | null>(null);
  const [toolError, setToolError] = useState<string | null>(null);
  const [runningTool, setRunningTool] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadWorkshop() {
      try {
        const [nextHealth, nextTools] = await Promise.all([getHealth(), getTools()]);
        if (cancelled) {
          return;
        }
        setHealth(nextHealth);
        setTools(nextTools);
        if (nextTools.some((tool) => tool.name === "roll_dice")) {
          setSelectedTool("roll_dice");
        } else if (nextTools[0]) {
          setSelectedTool(nextTools[0].name);
        }
      } catch (error) {
        if (!cancelled) {
          setBanner(error instanceof Error ? error.message : "Could not reach the API.");
        }
      }
    }
    void loadWorkshop();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || sending) {
      return;
    }
    setSending(true);
    setBanner(null);
    try {
      const response = await sendChat({ message, sessionId, agent });
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        { role: "user", content: message, toolCalls: [] },
        {
          role: "assistant",
          content: response.reply,
          toolCalls: response.tool_calls,
          backend: response.backend,
          agent: response.agent,
        },
      ]);
      setDraft("");
    } catch (error) {
      setBanner(error instanceof ApiError ? error.message : "The message could not be sent.");
    } finally {
      setSending(false);
    }
  }

  async function onNewChat() {
    setBanner(null);
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch {
        // The server may already have forgotten the session. Clear the screen anyway.
      }
    }
    setSessionId(null);
    setMessages([]);
    setDraft("");
  }

  async function onRunTool(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setToolError(null);
    setToolResult(null);
    let parsed: Record<string, unknown>;
    try {
      const value: unknown = JSON.parse(toolArguments || "{}");
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        setToolError("Arguments must be a JSON object.");
        return;
      }
      parsed = value as Record<string, unknown>;
    } catch {
      setToolError("Arguments must be valid JSON.");
      return;
    }
    setRunningTool(true);
    try {
      const response = await callTool(selectedTool, parsed);
      setToolResult(response.result);
    } catch (error) {
      setToolError(error instanceof ApiError ? error.message : "The tool call failed.");
    } finally {
      setRunningTool(false);
    }
  }

  function chooseAgent(next: AgentChoice) {
    setAgent(next);
  }

  return (
    <div className="page">
      <header className="masthead">
        <img
          className="banner"
          src="/banner.jpg"
          alt="Brass hub connector with braided cables fanning out to many plugs"
        />
        <div className="masthead-copy">
          <p className="eyebrow">MCP Server App</p>
          <h1>Talk to the tools</h1>
          <p className="lede">
            Chat with the LangGraph agent, or run a tool yourself. Dice rolls work immediately.
            Open-ended answers show up once an OpenAI key is configured.
          </p>
          <p className="status" role="status">
            <span className={health?.ready === false ? "pill warn" : "pill"}>{health ? backendLabel(health.backend) : "Connecting"}</span>
            <span>{health ? health.detail : "Checking the API…"}</span>
          </p>
        </div>
      </header>

      {banner ? (
        <p className="banner-error" role="alert">
          {banner}
        </p>
      ) : null}

      <div className="layout">
        <aside className="panel tools">
          <h2>Tools</h2>
          <ul>
            {tools.map((tool) => (
              <li key={tool.name}>
                <button
                  type="button"
                  className={tool.name === selectedTool ? "tool selected" : "tool"}
                  aria-pressed={tool.name === selectedTool}
                  onClick={() => {
                    setSelectedTool(tool.name);
                    setToolArguments(templateFor(tool.name));
                    setToolResult(null);
                    setToolError(null);
                  }}
                >
                  <span className="tool-name">{tool.name}</span>
                  <span className="tool-description">{tool.description}</span>
                </button>
              </li>
            ))}
          </ul>
          {tools.length === 0 ? <p className="muted">Tools will appear here once the API answers.</p> : null}

          <form className="tool-runner" onSubmit={onRunTool}>
            <h2>Run a tool</h2>
            <label htmlFor={toolArgsId}>
              Arguments for <span className="tool-name">{selectedTool}</span>
            </label>
            <textarea
              id={toolArgsId}
              value={toolArguments}
              onChange={(event) => setToolArguments(event.target.value)}
              spellCheck={false}
              rows={5}
            />
            <button type="submit" className="secondary" disabled={runningTool || tools.length === 0}>
              {runningTool ? "Running…" : "Run tool"}
            </button>
            {toolError ? (
              <p className="inline-error" role="alert">
                {toolError}
              </p>
            ) : null}
            {toolResult ? (
              <pre className="tool-output">
                <RichText text={toolResult} />
              </pre>
            ) : null}
          </form>
        </aside>

        <section className="panel chat" aria-label="Chat">
          <div className="chat-toolbar">
            <fieldset>
              <legend>Agent</legend>
              <label>
                <input
                  type="radio"
                  name="agent"
                  checked={agent === "react"}
                  onChange={() => chooseAgent("react")}
                />
                ReAct
              </label>
              <label>
                <input
                  type="radio"
                  name="agent"
                  checked={agent === "state_graph"}
                  onChange={() => chooseAgent("state_graph")}
                />
                State graph
              </label>
            </fieldset>
            <button type="button" className="secondary" onClick={() => void onNewChat()}>
              New chat
            </button>
          </div>

          <div className="transcript" aria-live="polite">
            {messages.length === 0 ? (
              <div className="empty">
                <p>Try one of these, or write your own.</p>
                <div className="suggestions">
                  {SUGGESTIONS.map((suggestion) => (
                    <button key={suggestion} type="button" className="suggestion" onClick={() => setDraft(suggestion)}>
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
                  <p className="who">{roleLabel(message.role)}</p>
                  <div className="body">
                    <RichText text={message.content} />
                  </div>
                  {message.role === "assistant" && message.backend ? (
                    <p className="meta">
                      {backendLabel(message.backend)}
                      {message.agent ? ` · ${agentLabel(message.agent)}` : ""}
                    </p>
                  ) : null}
                  {message.toolCalls.length > 0 ? (
                    <details className="traces">
                      <summary>
                        {message.toolCalls.length === 1
                          ? `Tool: ${message.toolCalls[0].name}`
                          : `${message.toolCalls.length} tool calls`}
                      </summary>
                      {message.toolCalls.map((trace, traceIndex) => (
                        <div key={`${trace.name}-${traceIndex}`} className="trace">
                          <p className="tool-name">{trace.name}</p>
                          <pre>{JSON.stringify(trace.arguments, null, 2)}</pre>
                          <pre>
                            <RichText text={trace.result} />
                          </pre>
                        </div>
                      ))}
                    </details>
                  ) : null}
                </article>
              ))
            )}
          </div>

          <form className="composer" onSubmit={onSubmit}>
            <label htmlFor={messageId}>Message</label>
            <textarea
              id={messageId}
              value={draft}
              placeholder="Roll 2d6, or ask for a quote card about shipping"
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              rows={3}
            />
            <button type="submit" disabled={sending || draft.trim().length === 0}>
              {sending ? "Sending…" : "Send"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
