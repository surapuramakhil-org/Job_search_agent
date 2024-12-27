from unittest.mock import patch

import pytest
from src.services.web_search_engine import BingSearchEngine, BraveSearchEngine, GoogleSearchEngine, WebSearchEngineFactory

@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.GOOGLE_SEARCH_ENGINE_ID", "mock_id")
@patch("src.config.GOOGLE_API_KEY", "mock_api_key")
@patch("src.config.BING_API_KEY", "mock_bing_api_key")
@patch("src.config.BRAVE_API_KEY", "mock_brave_api_key")
def test_web_search_engine_factory(mock_allowed_engines, mock_google_id, mock_google_key, mock_bing_key, mock_brave_key):
    # Test GoogleSearchEngine creation
    google_engine = WebSearchEngineFactory.get_search_engine("google")
    assert isinstance(google_engine, GoogleSearchEngine)

    # Test BingSearchEngine creation
    bing_engine = WebSearchEngineFactory.get_search_engine("bing")
    assert isinstance(bing_engine, BingSearchEngine)

    # Test BraveSearchEngine creation
    brave_engine = WebSearchEngineFactory.get_search_engine("brave")
    assert isinstance(brave_engine, BraveSearchEngine)

    # Test default search engine creation
    default_engine = WebSearchEngineFactory.get_search_engine()
    assert isinstance(default_engine, GoogleSearchEngine)

    # Test invalid search engine
    with pytest.raises(ValueError):
        WebSearchEngineFactory.get_search_engine("invalid_engine")

@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.GOOGLE_SEARCH_ENGINE_ID", "mock_id")
@patch("src.config.GOOGLE_API_KEY", "mock_api_key")
@patch("src.config.BING_API_KEY", "mock_bing_api_key")
@patch("src.config.BRAVE_API_KEY", "mock_brave_api_key")
def test_web_search_engine_factory_singleton(mock_allowed_engines, mock_google_id, mock_google_key, mock_bing_key, mock_brave_key):
    # Test GoogleSearchEngine singleton
    google_engine_1 = WebSearchEngineFactory.get_search_engine("google")
    google_engine_2 = WebSearchEngineFactory.get_search_engine("google")
    assert google_engine_1 is google_engine_2

    # Test BingSearchEngine singleton
    bing_engine_1 = WebSearchEngineFactory.get_search_engine("bing")
    bing_engine_2 = WebSearchEngineFactory.get_search_engine("bing")
    assert bing_engine_1 is bing_engine_2

    # Test BraveSearchEngine singleton
    brave_engine_1 = WebSearchEngineFactory.get_search_engine("brave")
    brave_engine_2 = WebSearchEngineFactory.get_search_engine("brave")
    assert brave_engine_1 is brave_engine_2

@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.ALLOWED_SEARCH_ENGINES", ["google", "bing", "brave"])
@patch("src.config.GOOGLE_SEARCH_ENGINE_ID", "mock_id")
@patch("src.config.GOOGLE_API_KEY", "mock_api_key")
@patch("src.config.BING_API_KEY", "mock_bing_api_key")
@patch("src.config.BRAVE_API_KEY", "mock_brave_api_key")
def test_web_search_engine_factory_allowed_engines(mock_allowed_engines, mock_google_id, mock_google_key, mock_bing_key, mock_brave_key):
    # Test allowed search engines
    for engine_name in ["google", "bing", "brave"]:
        engine = WebSearchEngineFactory.get_search_engine(engine_name)
        assert engine is not None

    # Test disallowed search engine
    with pytest.raises(ValueError):
        WebSearchEngineFactory.get_search_engine("duckduckgo")



