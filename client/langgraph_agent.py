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
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables
load_dotenv()


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
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
            api_key=self.openai_api_key,
            temperature=0.7
        )
        
        # MCP client configuration
        self.mcp_config = {
            "my-mcp-server": {
                "command": "uv",
                "args": ["--directory", current_dir, "run", "run_server.py"],
                "transport": "stdio",
            }
        }
        
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
    
    async def chat(self, message: str) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: The user's message/question
            
        Returns:
            The agent's response as a string
        """
        if not self.agent:
            await self.initialize()
        
        print(f"\n💬 User: {message}")
        print("🤔 Agent thinking...")
        
        response = await self.agent.ainvoke({"messages": [("user", message)]})
        agent_message = response["messages"][-1].content
        
        print(f"🤖 Agent: {agent_message}")
        return agent_message
    
    async def chat_with_state_graph(self, message: str) -> str:
        """
        Use the StateGraph version for more complex workflows.
        
        Args:
            message: The user's message/question
            
        Returns:
            The agent's response as a string
        """
        if not self.state_graph:
            await self.initialize()
        
        print(f"\n💬 User: {message}")
        print("🤔 StateGraph agent thinking...")
        
        response = await self.state_graph.ainvoke({"messages": [("user", message)]})
        agent_message = response["messages"][-1].content
        
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
        # print("\n🎮 Interactive mode (type 'quit' to exit):")
        # while True:
        #     user_input = input("\nYou: ").strip()
        #     if user_input.lower() in ['quit', 'exit', 'bye']:
        #         break
        #     if user_input:
        #         await agent.chat(user_input)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
