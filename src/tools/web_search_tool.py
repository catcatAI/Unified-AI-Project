import requests
from bs4 import BeautifulSoup

def search_web(query):
    """
    Searches the web for a given query.

    Args:
        query: The query to search for.

    Returns:
        A list of search results.
    """
    url = f"https://www.google.com/search?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for g in soup.find_all('div', class_='r'):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0]['href']
            title = g.find('h3').text
            item = {
                "title": title,
                "link": link
            }
            results.append(item)
    return results
