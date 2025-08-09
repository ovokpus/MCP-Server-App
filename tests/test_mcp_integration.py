"""
Test file for MCP integration

This module contains tests for the MCP server and client integration.
"""

import sys
import os
import asyncio
import pytest

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from client.langgraph_agent import MCPLangGraphAgent


class TestMCPIntegration:
    """Test class for MCP integration functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test that the MCP agent can be initialized."""
        # Skip if no OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")
        
        agent = MCPLangGraphAgent()
        await agent.initialize()
        
        # Check that tools are loaded
        assert len(agent.tools) > 0
        assert agent.agent is not None
        
        await agent.close()
    
    def test_mcp_server_import(self):
        """Test that server modules can be imported."""
        from server.dice_roller import DiceRoller
        from server.social_content_creator import SocialContentCreator
        
        # Test dice roller
        roller = DiceRoller("2d6")
        assert roller.notation == "2d6"
        
        # Test content creator
        creator = SocialContentCreator()
        assert creator is not None
    
    @pytest.mark.asyncio
    async def test_basic_tool_usage(self):
        """Test basic MCP tool usage through LangGraph."""
        # Skip if no API keys
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
            pytest.skip("Required API keys not available")
        
        agent = MCPLangGraphAgent()
        
        try:
            # Test dice rolling
            result = await agent.chat("Roll 2d6")
            assert "rolled" in result.lower() or "roll" in result.lower()
            
        finally:
            await agent.close()


def run_integration_tests():
    """Run integration tests manually (for when pytest is not available)."""
    import asyncio
    
    async def test_basic_functionality():
        print("🧪 Testing MCP Integration...")
        
        # Test imports
        try:
            from server.dice_roller import DiceRoller
            from server.social_content_creator import SocialContentCreator
            print("✅ Server modules import successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return
        
        # Test dice roller
        try:
            roller = DiceRoller("2d6")
            result = roller.roll_dice()
            print(f"✅ Dice roller works: {result}")
        except Exception as e:
            print(f"❌ Dice roller error: {e}")
        
        # Test content creator
        try:
            creator = SocialContentCreator()
            quote = creator.get_random_quote()
            print(f"✅ Content creator works: {quote['author']}")
        except Exception as e:
            print(f"❌ Content creator error: {e}")
        
        # Test LangGraph agent (if API keys available)
        if os.getenv("OPENAI_API_KEY") and os.getenv("TAVILY_API_KEY"):
            try:
                from client.langgraph_agent import MCPLangGraphAgent
                agent = MCPLangGraphAgent()
                await agent.initialize()
                print(f"✅ LangGraph agent initialized with {len(agent.tools)} tools")
                await agent.close()
            except Exception as e:
                print(f"❌ LangGraph agent error: {e}")
        else:
            print("⚠️ Skipping LangGraph test - API keys not available")
        
        print("🎉 Integration tests completed!")
    
    asyncio.run(test_basic_functionality())


if __name__ == "__main__":
    run_integration_tests()
