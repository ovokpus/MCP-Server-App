"""
Pytest tests to verify that server/main.py is working correctly.

This tests the MCP server by importing it directly and verifying:
1. The server can be instantiated
2. Tools are properly registered  
3. Basic tool functionality works (without requiring API keys)
"""

import sys
import os
import pytest

# Add parent directory to path to import server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import main as server_main


class TestMCPServer:
    """Test suite for MCP Server functionality."""
    
    def test_server_instance_exists(self):
        """Test that the MCP server instance is properly created."""
        assert hasattr(server_main, 'mcp'), "MCP server instance not found"
        assert server_main.mcp is not None, "MCP server instance is None"
    
    @pytest.mark.asyncio
    async def test_tools_are_registered(self):
        """Test that all expected tools are properly registered."""
        tools = await server_main.mcp.list_tools()
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "web_search", 
            "roll_dice", 
            "create_social_post", 
            "get_slide_image", 
            "create_quote_card",
            "github_search_repositories",
            "github_get_repository_info", 
            "github_get_file_content",
            "github_list_files",
            "github_auth_status"
        ]
        
        for tool in expected_tools:
            assert tool in tool_names, f"Expected tool '{tool}' not found in {tool_names}"
            
        # Verify we have the right number of tools
        assert len(tool_names) == len(expected_tools), f"Expected {len(expected_tools)} tools, got {len(tool_names)}"
    
    @pytest.mark.asyncio
    async def test_dice_rolling_tool(self):
        """Test that the dice rolling tool works correctly (no API keys needed)."""
        # Test basic 1d6 roll
        result = await server_main.mcp.call_tool("roll_dice", {"notation": "1d6"})
        
        # Verify we get a result
        assert result is not None, "Dice roll returned None"
        
        # The result should be a tuple with content and metadata
        assert isinstance(result, tuple), f"Expected tuple result, got {type(result)}"
        assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
        
        content, metadata = result
        assert content is not None, "Dice roll content is None"
        assert metadata is not None, "Dice roll metadata is None"
        
        # Test the metadata contains the result
        assert 'result' in metadata, "No 'result' key in metadata"
        assert 'ROLLS:' in metadata['result'], "Result doesn't contain roll information"
    
    @pytest.mark.asyncio
    async def test_dice_rolling_different_notation(self):
        """Test dice rolling with different notations."""
        test_cases = [
            "2d6",      # Two six-sided dice
            "1d20",     # One twenty-sided die
            "3d4",      # Three four-sided dice
        ]
        
        for notation in test_cases:
            result = await server_main.mcp.call_tool("roll_dice", {"notation": notation})
            assert result is not None, f"Dice roll for {notation} returned None"
            
            _, metadata = result
            assert 'result' in metadata, f"No 'result' key in metadata for {notation}"
            assert 'ROLLS:' in metadata['result'], f"Result for {notation} doesn't contain roll information"
    
    @pytest.mark.asyncio
    async def test_dice_rolling_with_multiple_rolls(self):
        """Test dice rolling with multiple rolls."""
        result = await server_main.mcp.call_tool("roll_dice", {
            "notation": "1d6", 
            "num_rolls": 3
        })
        
        assert result is not None, "Multiple dice rolls returned None"
        _, metadata = result
        assert 'result' in metadata, "No 'result' key in metadata for multiple rolls"
    
    @pytest.mark.asyncio
    async def test_github_repository_search(self):
        """Test GitHub repository search functionality."""
        result = await server_main.mcp.call_tool("github_search_repositories", {
            "query": "python", 
            "limit": 2
        })
        
        assert result is not None, "GitHub search returned None"
        _, metadata = result
        assert 'result' in metadata, "No 'result' key in metadata for GitHub search"
        
        # Check that the result contains expected GitHub search elements
        search_result = metadata['result']
        assert "GitHub Repository Search Results" in search_result, "Missing search results header"
        assert "Stars:" in search_result, "Missing star count in results"
    
    @pytest.mark.asyncio
    async def test_github_repository_info(self):
        """Test GitHub repository info functionality."""
        result = await server_main.mcp.call_tool("github_get_repository_info", {
            "owner": "octocat", 
            "repo": "Hello-World"
        })
        
        assert result is not None, "GitHub repo info returned None"
        _, metadata = result
        assert 'result' in metadata, "No 'result' key in metadata for GitHub repo info"
        
        # Check that the result contains expected repository info
        repo_info = metadata['result']
        assert "Repository Information" in repo_info, "Missing repo info header"
        assert "octocat/Hello-World" in repo_info, "Missing repository name"


# Backwards compatibility: keep the main function for direct execution
async def main():
    """Legacy main function for backwards compatibility."""
    print("🔧 Running tests via pytest is recommended!")
    print("   Use: uv run pytest tests/test_server.py -v")
    print("")
    print("🔧 Running basic test manually...")
    
    try:
        # Basic verification
        assert hasattr(server_main, 'mcp'), "MCP server instance not found"
        print("✅ MCP server instance found")
        
        tools = await server_main.mcp.list_tools()
        tool_names = [tool.name for tool in tools]
        print(f"✅ Available tools: {tool_names}")
        
        dice_result = await server_main.mcp.call_tool("roll_dice", {"notation": "1d6"})
        print(f"✅ Dice roll result: {dice_result}")
        
        print("\n🎉 Basic tests passed! Run full test suite with pytest.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)