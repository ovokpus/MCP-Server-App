from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import os
try:
    # Try relative imports first (when run as module)
    from .dice_roller import DiceRoller
    from .social_content_creator import SocialContentCreator
except ImportError:
    # Fall back to absolute imports (when run directly)
    from dice_roller import DiceRoller
    from social_content_creator import SocialContentCreator

load_dotenv()

mcp = FastMCP("mcp-server")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
content_creator = SocialContentCreator()

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

if __name__ == "__main__":
    mcp.run(transport="stdio")