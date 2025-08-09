from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import os
try:
    # Try relative imports first (when run as module)
    from .dice_roller import DiceRoller
    from .social_content_creator import SocialContentCreator
    from .github_tool import GitHubTool
except ImportError:
    # Fall back to absolute imports (when run directly)
    from dice_roller import DiceRoller
    from social_content_creator import SocialContentCreator
    from github_tool import GitHubTool

load_dotenv()

mcp = FastMCP("mcp-server")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
content_creator = SocialContentCreator()
github_tool = GitHubTool(github_token=os.getenv("GITHUB_TOKEN"))

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for information about the given query"""
    search_results = client.get_search_context(query=query)
    return search_results

@mcp.tool()
def roll_dice(notation: str, num_rolls: int = 1) -> str:
    """Roll the dice with the given notation"""
    roller = DiceRoller(notation, num_rolls)
    return str(roller)

@mcp.tool()
def create_social_post(topic: str, style: str = "professional") -> str:
    """Generate a social media post with image and text for any topic"""
    return content_creator.create_social_media_post(topic, style)

@mcp.tool()
def get_slide_image(topic: str, size: str = "1920x1080") -> str:
    """Get presentation-ready images for slides and presentations"""
    return content_creator.get_presentation_image(topic, size)

@mcp.tool()
def create_quote_card(theme: str = "motivation") -> str:
    """Generate a quote card with inspirational text and background image"""
    return content_creator.create_quote_card(theme)

@mcp.tool()
def github_search_repositories(query: str, limit: int = 5) -> str:
    """Search for GitHub repositories by query (e.g., 'python machine learning', 'user:microsoft')"""
    return github_tool.search_repositories(query, limit)

@mcp.tool()
def github_get_repository_info(owner: str, repo: str) -> str:
    """Get detailed information about a specific GitHub repository"""
    return github_tool.get_repository_info(owner, repo)

@mcp.tool()
def github_get_file_content(owner: str, repo: str, file_path: str, branch: str = "main") -> str:
    """Get the content of a specific file from a GitHub repository"""
    return github_tool.get_file_content(owner, repo, file_path, branch)

@mcp.tool()
def github_list_files(owner: str, repo: str, path: str = "", branch: str = "main") -> str:
    """List files and directories in a GitHub repository path"""
    return github_tool.list_repository_files(owner, repo, path, branch)

@mcp.tool()
def github_auth_status() -> str:
    """Check GitHub authentication status and rate limits"""
    return github_tool.get_authentication_status()

if __name__ == "__main__":
    mcp.run(transport="stdio")