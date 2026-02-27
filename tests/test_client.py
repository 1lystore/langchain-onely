from typing import Any

from langchain_onely.client import OneLyClient
from langchain_onely.constants import ONELY_API_BASE


class DummyResponse:
    def __init__(self, status_code: int = 200, json_data: Any = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.ok = 200 <= status_code < 300

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class DummySession:
    def __init__(self, response: DummyResponse):
        self._response = response
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


def test_client_defaults():
    client = OneLyClient()
    assert client.base_url == ONELY_API_BASE
    assert client.api_key is None


def test_client_api_key():
    client = OneLyClient(api_key="test_key")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer test_key"


def test_client_custom_base_url():
    client = OneLyClient(base_url="https://custom.com/")
    assert client.base_url == "https://custom.com"


def test_make_request_success_json(monkeypatch):
    client = OneLyClient()
    client.session = DummySession(DummyResponse(json_data={"success": True}, text="{}"))
    result = client.get("/api/test")
    assert result == {"success": True}


def test_make_request_non_json(monkeypatch):
    client = OneLyClient()
    client.session = DummySession(DummyResponse(json_data=ValueError("bad"), text="not json"))
    result = client.get("/api/test")
    assert result["error"] is True
    assert "NON_JSON_RESPONSE" in result["details"]["code"]


def test_make_request_http_error(monkeypatch):
    client = OneLyClient()
    client.session = DummySession(DummyResponse(status_code=404, json_data={"message": "nope"}, text="{}"))
    result = client.get("/api/test")
    assert result["error"] is True
    assert result["details"]["status"] == 404


def test_make_request_rate_limit(monkeypatch):
    client = OneLyClient()
    client.session = DummySession(DummyResponse(status_code=429, json_data={}, text="{}"))
    result = client.get("/api/test")
    assert result["error"] is True
    assert "Rate limit" in result["message"]
