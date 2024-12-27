import pytest
from unittest.mock import patch, MagicMock
from src.services.web_search_engine import GoogleSearchEngine, BingSearchEngine, BraveSearchEngine

# Unit test for GoogleSearchEngine
@patch("requests.get")
@patch("src.config.GOOGLE_API_KEY", "mock_api_key")  # Mocking the Google API key
def test_google_search_engine(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": ["result1", "result2"]}
    mock_get.return_value = mock_response

    search_engine = GoogleSearchEngine("mock_id")
    result = search_engine.search("test query")

    assert result == {"items": ["result1", "result2"]}
    mock_get.assert_called_once_with(
        "https://www.googleapis.com/customsearch/v1",
        params={"key": "mock_api_key", "cx": "mock_id", "q": "test query", "start": 1},
    )

# Unit test for BingSearchEngine
@patch("requests.get")
@patch("src.config.BING_API_KEY", "mock_bing_api_key")  # Mocking the Bing API key
def test_bing_search_engine(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"webPages": {"value": ["result1", "result2"]}}
    mock_get.return_value = mock_response

    search_engine = BingSearchEngine()
    result = search_engine.search("test query")

    assert result == {"webPages": {"value": ["result1", "result2"]}}
    mock_get.assert_called_once_with(
        "https://api.bing.microsoft.com/v7.0/search",
        headers={"Ocp-Apim-Subscription-Key": "mock_bing_api_key"},
        params={"q": "test query", "count": 10, "offset": 0},
    )

# Unit test for BraveSearchEngine
@patch("requests.get")
@patch("src.config.BRAVE_API_KEY", "mock_brave_api_key")  # Mocking the Brave API key
def test_brave_search_engine(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": ["result1", "result2"]}
    mock_get.return_value = mock_response

    search_engine = BraveSearchEngine()
    result = search_engine.search("test query")

    assert result == {"results": ["result1", "result2"]}
    mock_get.assert_called_once_with(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Authorization": "Bearer mock_brave_api_key"},
        params={"q": "test query", "offset": 0, "limit": 10},
    )
