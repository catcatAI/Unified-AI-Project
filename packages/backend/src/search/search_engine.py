class SearchEngine:
    """
    A class for searching for models and tools.
    """

    def __init__(self):
        pass

    def search(self, query):
        """
        Searches for models and tools that match a query.

        Args:
            query: The query to search for.

        Returns:
            A list of models and tools that match the query.
        """
        results = []
        results.extend(self._search_huggingface(query))
        results.extend(self._search_github(query))
        return results

    def _search_huggingface(self, query):
        """
        Searches for models on Hugging Face.

        Args:
            query: The query to search for.

        Returns:
            A list of models that match the query.
        """
        from huggingface_hub import HfApi
        api = HfApi()
        models = api.list_models(search=query)
        return [model.modelId for model in models]

    def _search_github(self, query):
        """
        Searches for tools on GitHub.

        Args:
            query: The query to search for.

        Returns:
            A list of tools that match the query.
        """
        from github import Github
        g = Github()
        repos = g.search_repositories(query=query)
        return [repo.full_name for repo in repos]
