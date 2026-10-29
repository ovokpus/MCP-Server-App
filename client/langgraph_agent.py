"""
LangGraph Agent with MCP Server Integration

This module demonstrates how to create a LangGraph agent that can interact
with your custom MCP server, using all the tools we've built:
- Web search (via Tavily)
- Dice rolling 
- Social media content creation
- Slide image generation
- Quote card creation
"""

import asyncio
import json
import os
import shlex
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables
load_dotenv()


def build_mcp_config(project_root: str | None = None) -> dict[str, Any]:
    """Build the stdio connection dict for the in-repo MCP server.

    ``MCP_COMMAND`` and ``MCP_ARGS`` override the local ``uv run`` default.
    Docker sets ``MCP_COMMAND=python`` and ``MCP_ARGS=run_server.py`` because
    the image does not need a second copy of uv on the PATH.

    The LangChain MCP adapter replaces the child environment when ``env`` is
    omitted (it keeps only ``PATH``). Forward the parent environment so API
    keys injected by Docker Compose reach the tool process. ``load_dotenv``
    inside the server is a fallback for a ``.env`` file on disk, not a
    substitute for those variables.
    """
    root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    command = os.getenv("MCP_COMMAND", "uv").strip() or "uv"
    raw_args = os.getenv("MCP_ARGS", "").strip()
    if not raw_args:
        args = ["--directory", root, "run", "run_server.py"]
    elif raw_args.startswith("["):
        parsed = json.loads(raw_args)
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError("MCP_ARGS JSON must be a list of strings.")
        args = parsed
    else:
        args = shlex.split(raw_args)

    env = {key: value for key, value in os.environ.items() if isinstance(value, str)}
    return {
        "my-mcp-server": {
            "command": command,
            "args": args,
            "transport": "stdio",
            "cwd": root,
            "env": env,
        }
    }


def message_text(content: Any) -> str:
    """Flatten a LangChain message body into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                parts.append(text if isinstance(text, str) else str(block))
            else:
                text = getattr(block, "text", None)
                parts.append(text if isinstance(text, str) else str(block))
        return "\n".join(parts)
    return str(content)


def _coerce_args(args: Any) -> dict[str, Any]:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except json.JSONDecodeError:
            return {"value": args}
        if isinstance(parsed, dict):
            return parsed
    return {}


def extract_tool_traces(messages: list[Any]) -> list[dict[str, Any]]:
    """Pair assistant tool calls with the tool messages that answered them."""
    pending: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for call in tool_calls:
            if not isinstance(call, dict):
                call = {
                    "id": getattr(call, "id", None),
                    "name": getattr(call, "name", "tool"),
                    "args": getattr(call, "args", {}),
                }
            call_id = str(call.get("id") or f"call-{len(ordered)}")
            entry = {
                "name": str(call.get("name") or "tool"),
                "arguments": _coerce_args(call.get("args")),
                "result": "",
            }
            pending[call_id] = entry
            ordered.append(entry)
        if getattr(msg, "type", None) == "tool":
            call_id = str(getattr(msg, "tool_call_id", "") or "")
            text = message_text(getattr(msg, "content", ""))
            if call_id and call_id in pending:
                pending[call_id]["result"] = text
            else:
                ordered.append(
                    {
                        "name": str(getattr(msg, "name", None) or "tool"),
                        "arguments": {},
                        "result": text,
                    }
                )
    return ordered


class MCPLangGraphAgent:
    """A LangGraph agent that connects to your MCP server."""
    
    def __init__(self, openai_api_key: str = None, server_path: str = None):
        """
        Initialize the MCP LangGraph Agent.
        
        Args:
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            server_path: Absolute path to your server.py file
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass it directly.")
        
        # Get the project root directory and construct server path
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_path = server_path or os.path.join(current_dir, "server", "main.py")
        
        # Initialize the language model. OPENAI_MODEL lets Docker and local
        # runs pick a model without editing this file.
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.openai_api_key,
            temperature=0.7
        )
        
        # MCP client configuration. ``current_dir`` is the project root.
        self.mcp_config = build_mcp_config(current_dir)
        
        self.client = None
        self.tools = []
        self.agent = None
        self.state_graph = None
    
    async def initialize(self):
        """Initialize the MCP client and load tools."""
        print("🔌 Connecting to MCP server...")
        
        self.client = MultiServerMCPClient(self.mcp_config)
        self.tools = await self.client.get_tools()
        
        print(f"✅ Connected! Loaded {len(self.tools)} tools:")
        for tool in self.tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Create the ReAct agent
        self.agent = create_react_agent(self.llm, self.tools)
        
        # Also create a StateGraph version for more advanced use cases
        self._create_state_graph()
        
        print("🤖 LangGraph agent initialized and ready!")
    
    def _create_state_graph(self):
        """Create a StateGraph version of the agent for advanced workflows."""
        def call_model(state: MessagesState):
            response = self.llm.bind_tools(self.tools).invoke(state["messages"])
            return {"messages": response}
        
        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            tools_condition,
        )
        builder.add_edge("tools", "call_model")
        self.state_graph = builder.compile()
    
    async def chat_detailed(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        use_state_graph: bool = False,
    ) -> dict[str, Any]:
        """Run one turn and return the reply plus MCP tool traces.

        ``history`` contains earlier user and assistant text. The new
        ``message`` is appended as the latest user turn. Tool messages from
        previous turns are not replayed; the model sees the text it already
        wrote.

        Args:
            message: The latest user message.
            history: Prior ``{"role", "content"}`` turns, oldest first.
            use_state_graph: Use the StateGraph runner instead of ReAct.

        Returns:
            A dict with ``reply`` (str) and ``tool_calls`` (list of
            name/arguments/result dicts).
        """
        if use_state_graph:
            if not self.state_graph:
                await self.initialize()
        elif not self.agent:
            await self.initialize()

        messages: list[tuple[str, str]] = []
        for item in history or []:
            role = item.get("role", "user")
            content = item.get("content", "")
            if role not in {"user", "assistant"} or not content:
                continue
            messages.append((role, content))
        messages.append(("user", message))

        runner = self.state_graph if use_state_graph else self.agent
        response = await runner.ainvoke({"messages": messages})
        response_messages = response["messages"]
        return {
            "reply": message_text(response_messages[-1].content),
            "tool_calls": extract_tool_traces(response_messages),
        }

    async def chat(self, message: str, history: list[dict[str, str]] | None = None) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: The user's message/question
            history: Optional prior user/assistant turns for multi-turn chat.
            
        Returns:
            The agent's response as a string
        """
        if not self.agent:
            await self.initialize()
        
        print(f"\n💬 User: {message}")
        print("🤔 Agent thinking...")
        
        detailed = await self.chat_detailed(message, history=history, use_state_graph=False)
        agent_message = detailed["reply"]
        
        print(f"🤖 Agent: {agent_message}")
        return agent_message
    
    async def chat_with_state_graph(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Use the StateGraph version for more complex workflows.
        
        Args:
            message: The user's message/question
            history: Optional prior user/assistant turns for multi-turn chat.
            
        Returns:
            The agent's response as a string
        """
        if not self.state_graph:
            await self.initialize()
        
        print(f"\n💬 User: {message}")
        print("🤔 StateGraph agent thinking...")
        
        detailed = await self.chat_detailed(message, history=history, use_state_graph=True)
        agent_message = detailed["reply"]
        
        print(f"🤖 StateGraph Agent: {agent_message}")
        return agent_message
    
    async def run_examples(self):
        """Run example interactions to demonstrate capabilities."""
        examples = [
            "Roll 2d20 and keep the highest",
            "Search the web for the latest news about AI",
            "Create a professional LinkedIn post about machine learning",
            "Get me an image for a presentation slide about 'future of work'",
            "Create a motivational quote card",
        ]
        
        print("\n🎯 Running example interactions:")
        print("=" * 50)
        
        for example in examples:
            try:
                await self.chat(example)
                print("-" * 50)
                await asyncio.sleep(1)  # Brief pause between examples
            except Exception as e:
                print(f"❌ Error with example '{example}': {e}")
                print("-" * 50)
    
    async def close(self):
        """Clean up resources."""
        if self.client:
            # The MultiServerMCPClient will handle cleanup automatically
            pass
        print("🔌 MCP connection closed.")


async def main():
    """Main function to demonstrate the MCP LangGraph integration."""
    print("🚀 MCP + LangGraph Integration Demo")
    print("=" * 40)
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key in your .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    # Create and initialize the agent
    agent = MCPLangGraphAgent()
    
    try:
        await agent.initialize()
        
        # Run example interactions
        await agent.run_examples()
        
        # Interactive mode (uncomment for live testing)
        print("\n🎮 Interactive mode (type 'quit' to exit):")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            if user_input:
                await agent.chat(user_input)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
