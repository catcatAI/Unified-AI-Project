"""
Web search tool using DuckDuckGo
"""
import os
import logging
from typing import List, Dict, Any
try:
    import requests
except ImportError:
    requests = None
    
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool for agents"""
    
    def __init__(self):
        self.name = "web_search"
        self.description = "Searches the web for information"
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'system_config.yaml')
        try:
            if yaml:
                with open(config_path, 'r', encoding='utf-8') as f:
                    all_configs = yaml.safe_load(f)
                    self.config = all_configs.get('web_search_tool', {})
            else:
                self.config = {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            self.config = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
        
        self.search_url_template = self.config.get(
            'search_url_template', 
            "https://duckduckgo.com/html/?q={query}"
        )
        self.user_agent = self.config.get(
            'user_agent',
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Searches the web for a given query using DuckDuckGo.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not requests:
            return [{"error": "requests library not installed"}]
        
        if not BeautifulSoup:
            return [{"error": "BeautifulSoup library not installed"}]
        
        try:
            url = self.search_url_template.format(query=query)
            headers = {"User-Agent": self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.find_all("div", class_="result__body"):
                title_tag = result.find("a", class_="result__a")
                snippet_tag = result.find("a", class_="result__snippet")
                
                if title_tag and snippet_tag:
                    results.append({
                        "title": title_tag.text.strip(),
                        "snippet": snippet_tag.text.strip(),
                        "url": title_tag.get("href", "")
                    })
                
                if len(results) >= num_results:
                    break
            
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Web search failed: {e}")
            return [{"error": f"Search failed: {str(e)}"}]
        except Exception as e:
            logger.error(f"Unexpected error in web search: {e}")
            return [{"error": f"Unexpected error: {str(e)}"}]
    
    def execute(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Execute web search (sync wrapper)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(self.search(query, num_results))
        return {"success": True, "results": results}
