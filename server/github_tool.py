"""
GitHub Integration Tool for MCP Server

Provides GitHub repository search, file access, and repository information.
Uses GitHub's public API - no authentication required for public repositories.
"""

import requests
import json
from typing import Dict, List, Optional
import base64


class GitHubTool:
    """GitHub integration tool for repository operations."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        # Set a user agent for GitHub API requests
        headers = {
            "User-Agent": "MCP-Server-App/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Add authentication if token is provided
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            self.authenticated = True
        else:
            self.authenticated = False
            
        self.session.headers.update(headers)
    
    def get_authentication_status(self) -> str:
        """
        Check authentication status and rate limits.
        
        Returns:
            Status information about authentication and rate limits
        """
        try:
            url = f"{self.base_url}/rate_limit"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            rate_limit = data.get("rate", {})
            
            if self.authenticated:
                # Get user info
                user_url = f"{self.base_url}/user"
                user_response = self.session.get(user_url)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    username = user_data.get("login", "Unknown")
                    user_type = user_data.get("type", "User")
                    
                    result = f"🔐 **GitHub Authentication Status: AUTHENTICATED**\n"
                    result += f"👤 User: {username} ({user_type})\n"
                    result += f"🔑 Access: Private & Public repositories\n"
                else:
                    result = f"🔐 **GitHub Authentication Status: TOKEN PROVIDED**\n"
                    result += f"🔑 Access: Should have private & public repositories\n"
            else:
                result = f"🔓 **GitHub Authentication Status: NOT AUTHENTICATED**\n"
                result += f"🔑 Access: Public repositories only\n"
            
            result += f"\n📊 **Rate Limits:**\n"
            result += f"   Remaining: {rate_limit.get('remaining', 'Unknown')}/{rate_limit.get('limit', 'Unknown')}\n"
            result += f"   Reset time: {rate_limit.get('reset', 'Unknown')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error checking authentication status: {str(e)}"
    
    def search_repositories(self, query: str, limit: int = 5) -> str:
        """
        Search for GitHub repositories.
        
        Args:
            query: Search query (e.g., "python machine learning", "user:microsoft")
            limit: Maximum number of results to return (default: 5)
            
        Returns:
            Formatted string with repository information
        """
        try:
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": query,
                "sort": "stars", 
                "order": "desc",
                "per_page": min(limit, 10)  # GitHub API limit
            }
            
            # Add private repo access note for authenticated users
            auth_note = " (including private repos)" if self.authenticated else " (public repos only)"
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            repositories = data.get("items", [])
            
            if not repositories:
                return f"No repositories found for query: '{query}'{auth_note}"
            
            result = f"🔍 GitHub Repository Search Results for '{query}'{auth_note}:\n\n"
            
            for i, repo in enumerate(repositories, 1):
                result += f"{i}. **{repo['full_name']}**\n"
                result += f"   ⭐ Stars: {repo['stargazers_count']:,}\n"
                result += f"   🍴 Forks: {repo['forks_count']:,}\n"
                result += f"   📝 Language: {repo['language'] or 'Not specified'}\n"
                result += f"   📄 Description: {repo['description'] or 'No description'}\n"
                result += f"   🔗 URL: {repo['html_url']}\n"
                result += f"   📅 Updated: {repo['updated_at'][:10]}\n\n"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return f"❌ Error searching repositories: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    def get_repository_info(self, owner: str, repo: str) -> str:
        """
        Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            
        Returns:
            Formatted string with detailed repository information
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            result = f"📊 Repository Information: {data['full_name']}\n\n"
            result += f"📝 Description: {data['description'] or 'No description'}\n"
            result += f"🏷️  Language: {data['language'] or 'Not specified'}\n"
            result += f"⭐ Stars: {data['stargazers_count']:,}\n"
            result += f"🍴 Forks: {data['forks_count']:,}\n"
            result += f"👁️  Watchers: {data['watchers_count']:,}\n"
            result += f"📂 Size: {data['size']} KB\n"
            result += f"🔓 Visibility: {'Public' if not data['private'] else 'Private'}\n"
            result += f"📅 Created: {data['created_at'][:10]}\n"
            result += f"🔄 Updated: {data['updated_at'][:10]}\n"
            result += f"🔗 URL: {data['html_url']}\n"
            
            if data.get('homepage'):
                result += f"🌐 Homepage: {data['homepage']}\n"
            
            if data.get('topics'):
                result += f"🏷️  Topics: {', '.join(data['topics'])}\n"
            
            return result
            
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return f"❌ Repository '{owner}/{repo}' not found or is private"
            return f"❌ Error getting repository info: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    def get_file_content(self, owner: str, repo: str, file_path: str, branch: str = "main") -> str:
        """
        Get the content of a specific file from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to the file (e.g., "README.md", "src/main.py")
            branch: Branch name (default: "main")
            
        Returns:
            File content or error message
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            params = {"ref": branch}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("type") != "file":
                return f"❌ '{file_path}' is not a file (it's a {data.get('type', 'unknown')})"
            
            # Decode base64 content
            content = base64.b64decode(data["content"]).decode("utf-8")
            
            result = f"📄 File Content: {owner}/{repo}/{file_path} (branch: {branch})\n"
            result += f"📏 Size: {data['size']} bytes\n\n"
            result += "```\n"
            result += content
            result += "\n```"
            
            return result
            
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                # Try with master branch if main fails
                if branch == "main":
                    try:
                        return self.get_file_content(owner, repo, file_path, "master")
                    except:
                        pass
                return f"❌ File '{file_path}' not found in '{owner}/{repo}' (tried branches: main, master)"
            return f"❌ Error getting file content: {str(e)}"
        except UnicodeDecodeError:
            return f"❌ Cannot decode file '{file_path}' - it may be a binary file"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    def list_repository_files(self, owner: str, repo: str, path: str = "", branch: str = "main") -> str:
        """
        List files and directories in a repository path.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path (default: root)
            branch: Branch name (default: "main")
            
        Returns:
            Formatted list of files and directories
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            params = {"ref": branch}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                return f"❌ '{path}' is not a directory"
            
            result = f"📁 Directory Listing: {owner}/{repo}/{path or 'root'} (branch: {branch})\n\n"
            
            # Separate directories and files
            directories = [item for item in data if item["type"] == "dir"]
            files = [item for item in data if item["type"] == "file"]
            
            # List directories first
            if directories:
                result += "📁 **Directories:**\n"
                for item in directories:
                    result += f"   📂 {item['name']}/\n"
                result += "\n"
            
            # Then list files
            if files:
                result += "📄 **Files:**\n"
                for item in files:
                    size = f" ({item['size']} bytes)" if item.get('size') else ""
                    result += f"   📄 {item['name']}{size}\n"
            
            if not directories and not files:
                result += "📭 Directory is empty\n"
            
            return result
            
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                # Try with master branch if main fails
                if branch == "main":
                    try:
                        return self.list_repository_files(owner, repo, path, "master")
                    except:
                        pass
                return f"❌ Path '{path}' not found in '{owner}/{repo}' (tried branches: main, master)"
            return f"❌ Error listing directory: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
