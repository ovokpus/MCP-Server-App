"""
Simple example showing how to use the LangGraph MCP Agent

This script demonstrates basic usage of the MCPLangGraphAgent
with your custom MCP server tools.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.langgraph_agent import MCPLangGraphAgent


async def quick_examples():
    """Quick examples to test the MCP + LangGraph integration."""
    
    print("🎯 Quick LangGraph + MCP Examples")
    print("=" * 40)
    
    # Initialize the agent
    agent = MCPLangGraphAgent()
    
    try:
        # Examples that combine multiple tools
        examples = [
            "Roll a d20 for me and tell me what it means for my luck today",
            "Search for recent AI news and create a professional social media post about it",
            "Create a quote card about technology and innovation",
            "I need a presentation slide image about 'digital transformation' - can you help?",
        ]
        
        for example in examples:
            print(f"\n🔹 Testing: {example}")
            result = await agent.chat(example)
            print("✅ Completed!")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.close()


async def interactive_mode():
    """Interactive mode for testing."""
    
    print("🎮 Interactive LangGraph + MCP Agent")
    print("=" * 40)
    print("Type your requests and the agent will use MCP tools to help!")
    print("Examples:")
    print("  - 'Roll 3d6 dice'")
    print("  - 'Search for Python news'") 
    print("  - 'Create a LinkedIn post about AI'")
    print("  - 'Get me slide images for machine learning'")
    print("Type 'quit' to exit.\n")
    
    agent = MCPLangGraphAgent()
    
    try:
        await agent.initialize()
        
        while True:
            user_input = input("💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            try:
                await agent.chat(user_input)
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        await agent.close()


async def compare_react_vs_stategraph():
    """Compare ReAct agent vs StateGraph for the same task."""
    
    print("⚖️ Comparing ReAct vs StateGraph")
    print("=" * 40)
    
    agent = MCPLangGraphAgent()
    
    try:
        await agent.initialize()
        
        task = "Roll 2d10, search for AI news, and create a social post about it"
        
        print("🔹 Using ReAct Agent:")
        await agent.chat(task)
        
        print("\n🔹 Using StateGraph Agent:")
        await agent.chat_with_state_graph(task)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.close()


if __name__ == "__main__":
    print("🚀 LangGraph + MCP Integration Examples")
    print("Choose what to run:")
    print("1. Quick Examples")
    print("2. Interactive Mode") 
    print("3. Compare ReAct vs StateGraph")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(quick_examples())
    elif choice == "2":
        asyncio.run(interactive_mode())
    elif choice == "3":
        asyncio.run(compare_react_vs_stategraph())
    else:
        print("Invalid choice. Running quick examples...")
        asyncio.run(quick_examples())
