import requests
from bs4 import BeautifulSoup

class WebSearchTool:
    async def search(self, query: str, num_results: int = 5):
        """
        Searches the web for a given query using DuckDuckGo and returns a list of search results.
        """
        try:
            # DuckDuckGo search URL
            url = f"https://duckduckgo.com/html/?q={query}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            for result in soup.find_all("div", class_="result__body"):
                title_tag = result.find("a", class_="result__a")
                snippet_tag = result.find("a", class_="result__snippet")
                if title_tag and snippet_tag:
                    results.append({
                        "title": title_tag.text,
                        "snippet": snippet_tag.text,
                        "url": title_tag["href"]
                    })
                if len(results) >= num_results:
                    break

            return results
        except requests.exceptions.RequestException as e:
            return {"error": f"An error occurred: {e}"}
