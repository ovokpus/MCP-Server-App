import requests
import random
import os
from typing import Dict, Optional


class SocialContentCreator:
    """A class to create social media content using free APIs."""
    
    def __init__(self):
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.quotable_base_url = "https://api.quotable.io"
        self.unsplash_base_url = "https://api.unsplash.com"
        
    def get_random_quote(self, min_length: int = 50, max_length: int = 140) -> Dict:
        """Get a random inspirational quote from Quotable API."""
        try:
            params = {
                "minLength": min_length,
                "maxLength": max_length,
                "tags": "inspirational|motivational|success|wisdom"
            }
            response = requests.get(f"{self.quotable_base_url}/random", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Fallback quotes if API fails
            fallback_quotes = [
                {"content": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
                {"content": "Innovation distinguishes between a leader and a follower.", "author": "Steve Jobs"},
                {"content": "Stay hungry, stay foolish.", "author": "Steve Jobs"},
                {"content": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"}
            ]
            return random.choice(fallback_quotes)
    
    def search_unsplash_images(self, query: str, per_page: int = 10) -> Dict:
        """Search for images on Unsplash."""
        if not self.unsplash_access_key:
            # Return Lorem Picsum fallback if no Unsplash key
            return {
                "results": [
                    {
                        "urls": {
                            "regular": f"https://picsum.photos/1080/1080?random=1",
                            "small": f"https://picsum.photos/400/400?random=1"
                        },
                        "alt_description": f"Random image related to {query}",
                        "user": {"name": "Lorem Picsum"},
                        "links": {"html": "https://picsum.photos"}
                    }
                ]
            }
        
        try:
            headers = {"Authorization": f"Client-ID {self.unsplash_access_key}"}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            }
            response = requests.get(f"{self.unsplash_base_url}/search/photos", 
                                  headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Fallback to Lorem Picsum
            return {
                "results": [
                    {
                        "urls": {
                            "regular": f"https://picsum.photos/1080/1080?random={random.randint(1, 1000)}",
                            "small": f"https://picsum.photos/400/400?random={random.randint(1, 1000)}"
                        },
                        "alt_description": f"Random image related to {query}",
                        "user": {"name": "Lorem Picsum"},
                        "links": {"html": "https://picsum.photos"}
                    }
                ]
            }
    
    def create_social_media_post(self, topic: str, style: str = "professional") -> str:
        """Generate a complete social media post with image and text."""
        # Get a relevant image
        image_results = self.search_unsplash_images(topic)
        
        if not image_results.get("results"):
            return "❌ No images found for the given topic."
        
        # Pick the first image
        image = image_results["results"][0]
        image_url = image["urls"]["regular"]
        image_credit = image["user"]["name"]
        image_link = image["links"]["html"]
        
        # Get an inspirational quote
        quote_data = self.get_random_quote()
        quote = quote_data["content"]
        author = quote_data["author"]
        
        # Create different styles of posts
        if style.lower() == "motivational":
            post_text = f'🌟 "{quote}" - {author}\n\n💪 Let this inspire your {topic} journey today!\n\n#motivation #inspiration #{topic.replace(" ", "").lower()}'
        elif style.lower() == "professional":
            post_text = f'💡 Reflecting on {topic} today:\n\n"{quote}" - {author}\n\n#leadership #growth #{topic.replace(" ", "").lower()}'
        elif style.lower() == "casual":
            post_text = f'Hey everyone! 👋\n\n💭 "{quote}" - {author}\n\nThis really resonates with my thoughts on {topic}. What do you think?\n\n#{topic.replace(" ", "").lower()} #quotes #dailyinspiration'
        else:
            post_text = f'"{quote}" - {author}\n\n#{topic.replace(" ", "").lower()} #inspiration'
        
        # Format the complete post
        result = f"""🎨 SOCIAL MEDIA POST GENERATED 🎨

📝 POST TEXT:
{post_text}

🖼️ IMAGE:
URL: {image_url}
Credit: Photo by {image_credit} on Unsplash
Link: {image_link}

📊 POST STATS:
- Character count: {len(post_text)}
- Hashtags: {len([word for word in post_text.split() if word.startswith('#')])}
- Style: {style.title()}
- Topic: {topic.title()}

💡 TIP: Copy the image URL and post text to create your social media content!"""
        
        return result
    
    def get_presentation_image(self, topic: str, size: str = "1920x1080") -> str:
        """Get a high-quality image suitable for presentations."""
        # Parse size
        try:
            width, height = map(int, size.split('x'))
        except ValueError:
            width, height = 1920, 1080
        
        # Search for images
        image_results = self.search_unsplash_images(topic)
        
        if not image_results.get("results"):
            return f"❌ No images found for '{topic}'. Try a different search term."
        
        # Get multiple options
        images = image_results["results"][:3]  # Top 3 results
        
        result = f"🖼️ PRESENTATION IMAGES FOR '{topic.upper()}'\n\n"
        
        for i, image in enumerate(images, 1):
            # Get the best quality URL available
            image_url = image["urls"].get("regular", image["urls"].get("small", ""))
            
            # Modify URL for custom size if using Lorem Picsum
            if "picsum.photos" in image_url:
                image_url = f"https://picsum.photos/{width}/{height}?random={random.randint(1, 1000)}"
            
            credit = image["user"]["name"]
            description = image.get("alt_description", f"Image related to {topic}")
            
            result += f"""📷 OPTION {i}:
URL: {image_url}
Description: {description}
Credit: {credit}
Size: {size} (or original ratio)

"""
        
        result += f"""💡 USAGE TIPS:
- Right-click and 'Save Image As' to download
- These images are free to use (check Unsplash license)
- Always credit the photographer when possible
- For presentations, Option 1 is typically the best quality"""
        
        return result
    
    def create_quote_card(self, theme: str = "motivation") -> str:
        """Generate a quote card perfect for social media sharing."""
        # Get a themed quote
        quote_data = self.get_random_quote(min_length=30, max_length=120)
        quote = quote_data["content"]
        author = quote_data["author"]
        
        # Get a background image
        search_terms = {
            "motivation": "inspiration motivation success",
            "business": "business office success",
            "technology": "technology innovation digital",
            "nature": "nature landscape peaceful",
            "abstract": "abstract minimal clean"
        }
        
        search_term = search_terms.get(theme.lower(), theme)
        image_results = self.search_unsplash_images(search_term)
        
        if image_results.get("results"):
            bg_image = image_results["results"][0]
            bg_url = bg_image["urls"]["regular"]
            bg_credit = bg_image["user"]["name"]
        else:
            bg_url = f"https://picsum.photos/1080/1080?random={random.randint(1, 1000)}"
            bg_credit = "Lorem Picsum"
        
        result = f"""💬 QUOTE CARD GENERATED 💬

✨ QUOTE:
"{quote}"
- {author}

🎨 DESIGN SUGGESTIONS:
Theme: {theme.title()}
Background: {bg_url}
Credit: {bg_credit}

📱 RECOMMENDED LAYOUT:
- Center the quote text
- Use white/light text with dark overlay on image
- Author name in smaller text below quote
- Square format (1080x1080) for Instagram
- Consider adding your logo/watermark

📋 COPY-READY TEXT:
"{quote}" - {author}

#{theme.lower()}quotes #inspiration #motivation #dailyquote

🔧 TOOLS TO CREATE:
- Canva (use background image URL)
- Figma (import background image)
- PowerPoint/Keynote (insert background image)
- Any design tool that accepts image URLs"""
        
        return result
