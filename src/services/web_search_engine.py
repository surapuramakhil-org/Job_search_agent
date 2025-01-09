from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from turtle import st
from typing import Any, Dict, List, Optional, Union
import requests
from abc import ABC, abstractmethod
import src.config as config
from src.config import ALLOWED_SEARCH_ENGINES, GOOGLE, BING, BRAVE
from src.logger import logger

@dataclass
class SearchResult:
    """
    Represents an individual search result item.
    Note: 'engine_name' is moved to PaginatedSearchResponse.
    """
    title: str
    link: str
    snippet: str
    raw_data: Optional[Dict[str, Any]] = field(default=None)


@dataclass
class PaginatedSearchResponse:
    """
    Holds a list of SearchResult items plus offset-based pagination info
    and the 'engine_name' to identify which engine provided these results.
    """
    results: List[SearchResult] = field(default_factory=list)
    engine_name: str = ""
    offset: int = 0
    limit: int = 10
    total_results: Optional[int] = None

class SearchTimeRange(Enum):
    LAST_24_HOURS = "last_24_hours"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"

#TODO: add custom range later
@dataclass
class CustomTimeRange:
    start_time: datetime
    end_time: datetime

@dataclass
class UnifiedQuery:
    """
    Represents a unified search query that can be translated into platform-specific queries.
    """
    keywords: Optional[List[str]] = field(default_factory=list)
    blacklist: Optional[List[str]] = field(default_factory=list)
    whitelist: Optional[List[str]] = field(default_factory=list)
    date_range: Optional[SearchTimeRange] = None
    gl: Optional[str] = None 

class WebSearchEngine(ABC):
    """
    Abstract base class for web search engines. Each subclass's search
    method returns a PaginatedSearchResponse object.
    """
    @abstractmethod
    def search(self, query: str, params: dict, offset: int = 0, limit: int = 10) -> PaginatedSearchResponse:
        """
        Perform an offset-based search with the specified limit (number
        of results per request).
        """
        pass

    @abstractmethod
    def build_query(self, query : UnifiedQuery) -> str:
        """
        Returns a UnifiedQuery object that can be translated into platform-specific queries.
        """
        pass    

class SearchQueryBuilder:
    """
    A builder class for creating unified search queries.

    blacklist => (-blacklistitem1 OR -blacklistitem2 OR ...)
    whitelist => (whitelistitem1 OR whitelistitem2 OR ...)
    keywords => keyworditem1 keyworditem2 keyworditem3 

    final query will be = keyword blacklist whitelist
    i.e keyworditem1 keyworditem2 keyworditem3 (whitelistitem1 OR whitelistitem2 OR ...) (-blacklistitem1 OR -blacklistitem2 OR ...) 

    use double quotes "" for exact match
    """

    def __init__(self):
        self.keywords = []
        self.blacklist = []
        self.whitelist = []
        self.date_range = None
        self.gl = None

    @staticmethod
    def create():
        return SearchQueryBuilder()

    def add_to_blacklist(self, term: Union[str, List[str]]):
        if isinstance(term, list):
            self.blacklist.extend(term)
        else:
            self.blacklist.append(term)
        return self

    def add_to_whitelist(self, term: Union[str, List[str]]):
        if isinstance(term, list):
            self.whitelist.extend(term)
        else:
            self.whitelist.append(term)
        return self

    def add_to_keywords(self, term: Union[str, List[str]]):
        if isinstance(term, list):
            self.keywords.extend(term)
        else:
            self.keywords.append(term)
        return self

    def set_date_range(self, date_range: SearchTimeRange):
        if not isinstance(date_range, SearchTimeRange):
            raise ValueError("date_range must be an instance of SearchTimeRange Enum")
        self.date_range = date_range
        return self

    def set_geolocation(self, gl: str):
        self.gl = gl
        return self

    def build(self) -> UnifiedQuery:
        """
        Builds and returns a UnifiedQuery object.
        """
        return UnifiedQuery(
            keywords=self.keywords,
            blacklist=self.blacklist,
            whitelist=self.whitelist,
            date_range=self.date_range,
            gl=self.gl
        )

class GoogleSearchEngine(WebSearchEngine):
    GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
    DEFAULT_SEARCH_LIMIT = 10

    def __init__(self):
        self.api_key = config.GOOGLE_API_KEY
        self.search_engine_id = config.GOOGLE_SEARCH_ENGINE_ID

    def search(self, query: str, params : dict = {}, offset: int = 0, limit: int = DEFAULT_SEARCH_LIMIT) -> PaginatedSearchResponse:
        """
        Google uses 'start' to represent offset. 
        If offset is 0, start=1. If offset is 10, start=11, etc.
        """
        start = offset + 1
        params.update({
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "start": start,
            "num": limit
        })
        response = requests.get(self.GOOGLE_SEARCH_URL, params=params)
        response.raise_for_status()
        return self._parse_response(response.json(), offset, limit)

    def _parse_response(
        self,
        response: Dict[str, Any],
        offset: int,
        limit: int
    ) -> PaginatedSearchResponse:
        results: List[SearchResult] = []
        for item in response.get("items", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
                raw_data=item
            ))

        # Extract totalResults from "searchInformation"
        search_info = response.get("searchInformation", {})
        total_str = search_info.get("totalResults")
        total_results = int(total_str) if total_str and total_str.isdigit() else None

        return PaginatedSearchResponse(
            results=results,
            engine_name="Google",
            offset=offset,
            limit=limit,
            total_results=total_results
        )
    
    def build_query(self, query : UnifiedQuery) -> str:
        raise NotImplementedError("Google search engine does not support QueryBuilder")

        """
        Returns a query string specific to the search engine.
        """
        base_query = query.baseQuery
        blacklist = query.blacklist
        whitelist = query.whitelist
        date_range = query.date_range

        if date_range is not None:
            if isinstance(date_range, SearchTimeRange):
                if date_range == SearchTimeRange.LAST_24_HOURS:
                    base_query += " daterange:day"
                elif date_range == SearchTimeRange.LAST_WEEK:
                    base_query += " daterange:week"
                elif date_range == SearchTimeRange.LAST_MONTH:
                    base_query += " daterange:month"
            elif isinstance(date_range, CustomTimeRange):
                start_time = date_range.start_time.strftime("%Y-%m-%d")
                end_time = date_range.end_time.strftime("%Y-%m-%d")
                base_query += f" daterange:{start_time}-{end_time}"

        if blacklist:
            for term in blacklist:
                base_query += f" -{term}"
        
        if whitelist:
            for term in whitelist:
                base_query += f" {term}"

        return base_query



#TODO: blocker unifed query mechanism
class BingSearchEngine(WebSearchEngine):
    BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
    DEFAULT_SEARCH_LIMIT = 50

    def __init__(self):
        self.api_key = config.BING_API_KEY

    def search(self, query: str, params: dict = {}, offset: int = 0, limit: int = DEFAULT_SEARCH_LIMIT) -> PaginatedSearchResponse:
        """
        Bing uses 'offset' in addition to 'count' (our limit).
        """
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params.update({
            "q": query,
            "offset": offset,
            "count": limit
        })
        response = requests.get(self.BING_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return self._parse_response(response.json(), offset, limit)

    def _parse_response(
        self,
        response: Dict[str, Any],
        offset: int,
        limit: int
    ) -> PaginatedSearchResponse:
        results: List[SearchResult] = []
        web_pages = response.get("webPages", {})
        for item in web_pages.get("value", []):
            results.append(SearchResult(
                title=item.get("name", ""),
                link=item.get("url", ""),
                snippet=item.get("snippet", ""),
                raw_data=item
            ))

        total_estimated = web_pages.get("totalEstimatedMatches")
        total_results = total_estimated if isinstance(total_estimated, int) else None

        return PaginatedSearchResponse(
            results=results,
            engine_name="Bing",
            offset=offset,
            limit=limit,
            total_results=total_results
        )
    
    def build_query(self, query : UnifiedQuery) -> str:
        raise NotImplementedError("Bing search engine does not support custom queries")

#TODO: blocker unifed query mechanism
class BraveSearchEngine(WebSearchEngine):
    BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
    DEFAULT_SEARCH_LIMIT = 20

    def __init__(self):
        self.api_key = config.BRAVE_API_KEY

    def search(self, query: str, params: dict = {}, offset: int = 0, limit: int = DEFAULT_SEARCH_LIMIT) -> PaginatedSearchResponse:
        """
        Brave also supports 'offset' (number of items to skip) and 'limit'.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params.update({
            "q": query,
            "offset": offset,
            "limit": limit
        })
        response = requests.get(self.BRAVE_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return self._parse_response(response.json(), offset, limit)

    def _parse_response(
        self,
        response: Dict[str, Any],
        offset: int,
        limit: int
    ) -> PaginatedSearchResponse:
        results: List[SearchResult] = []
        web_data = response.get("web", {})
        for item in web_data.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                link=item.get("url", ""),
                snippet=item.get("description", ""),
                raw_data=item
            ))
        # Brave often doesn’t provide total results
        total_results = None

        return PaginatedSearchResponse(
            results=results,
            engine_name="Brave",
            offset=offset,
            limit=limit,
            total_results=total_results
        )
    
    def build_query(self, query : UnifiedQuery) -> str:
        raise NotImplementedError("Brave search engine does not support custom queries")


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
            instance = GoogleSearchEngine()
        elif engine_name == BING:
            instance = BingSearchEngine()
        elif engine_name == BRAVE:
            instance = BraveSearchEngine()
        else:
            raise ValueError(f"Unknown search engine: {engine_name}")

        WebSearchEngineFactory._instances[engine_name] = instance
        return instance
    

