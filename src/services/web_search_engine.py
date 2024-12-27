import requests
from abc import ABC, abstractmethod
import src.config as config
from src.config import ALLOWED_SEARCH_ENGINES, GOOGLE, BING, BRAVE

class WebSearchEngine(ABC):
    """
    Abstract base class for web search engines.
    """
    @abstractmethod
    def search(self, query, page=1):
        pass


class GoogleSearchEngine(WebSearchEngine):
    GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, search_engine_id):
        self.search_engine_id = search_engine_id

    def search(self, query, page=1):
        api_key = config.GOOGLE_API_KEY
        start = (page - 1) * 10 + 1
        params = {
            "key": api_key,
            "cx": self.search_engine_id,
            "q": query,
            "start": start
        }
        response = requests.get(self.GOOGLE_SEARCH_URL, params=params)
        response.raise_for_status()
        return response.json()


class BingSearchEngine(WebSearchEngine):
    BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self):
        pass

    def search(self, query, page=1):
        api_key = config.BING_API_KEY
        offset = (page - 1) * 10
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": 10,
            "offset": offset
        }
        response = requests.get(self.BING_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


class BraveSearchEngine(WebSearchEngine):
    BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self):
        pass

    def search(self, query, page=1):
        api_key = config.BRAVE_API_KEY
        offset = (page - 1) * 10
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "q": query,
            "offset": offset,
            "limit": 10
        }
        response = requests.get(self.BRAVE_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


class WebSearchEngineFactory:
    _instances = {}

    @staticmethod
    def get_search_engine(engine_name=None):
        if engine_name is None:
            # For now, just pick the first allowed search engine
            engine_name = ALLOWED_SEARCH_ENGINES[0]

        engine_name = engine_name.lower()
        
        if engine_name not in ALLOWED_SEARCH_ENGINES:
            raise ValueError(f"Search engine {engine_name} is not allowed. Allowed engines: {ALLOWED_SEARCH_ENGINES}")

        if engine_name in WebSearchEngineFactory._instances:
            return WebSearchEngineFactory._instances[engine_name]

        if engine_name == GOOGLE:
            search_engine_id = config.GOOGLE_SEARCH_ENGINE_ID
            instance = GoogleSearchEngine(search_engine_id)
        elif engine_name == BING:
            instance = BingSearchEngine()
        elif engine_name == BRAVE:
            instance = BraveSearchEngine()
        else:
            raise ValueError(f"Unknown search engine: {engine_name}")

        WebSearchEngineFactory._instances[engine_name] = instance
        return instance
    

