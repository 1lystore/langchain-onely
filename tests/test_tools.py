import json

from langchain_onely.tools import (
    create_search_tool,
    create_get_details_tool,
    create_call_tool,
    create_review_tool,
    create_create_store_tool,
    create_create_link_tool,
    create_list_links_tool,
    create_get_stats_tool,
    create_withdraw_tool,
)


class DummyClient:
    def __init__(self, base_url="https://1ly.store", api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def get(self, endpoint, params=None):
        if endpoint == "/api/discover":
            return {"results": [{"title": "Weather"}], "total": 1}
        if endpoint.startswith("/api/link/"):
            return {"id": "link123"}
        if endpoint == "/api/v1/links":
            return {"data": {"links": [{"id": "1"}]}}
        if endpoint == "/api/v1/stats":
            return {"data": {"totalRevenue": "1.00", "totalPurchases": 2}}
        return {"error": True, "message": "not found"}

    def post(self, endpoint, json_data=None):
        if endpoint == "/api/agent/auth/nonce":
            return {"data": {"message": "sign this"}}
        if endpoint == "/api/agent/signup":
            return {"data": {"apiKey": "1ly_live_x", "store": {"id": "s1"}}}
        if endpoint == "/api/v1/links":
            return {"data": {"id": "l1", "slug": "weather", "fullUrl": "https://1ly.store/api/link/weather"}}
        if endpoint == "/api/v1/withdrawals":
            return {"data": {"transaction": "tx123"}}
        if endpoint == "/api/reviews":
            return {"id": "r1"}
        return {"error": True, "message": "not found"}


def test_search_tool():
    tool = create_search_tool(DummyClient())
    result = json.loads(tool.invoke({"query": "weather"}))
    assert "results" in result
    assert result["total"] == 1


def test_get_details_tool():
    tool = create_get_details_tool(DummyClient(base_url="https://custom"))
    result = json.loads(tool.invoke({"endpoint": "joe/weather"}))
    assert result["fullUrl"].startswith("https://custom")


def test_call_tool_requires_wallet():
    tool = create_call_tool(DummyClient())
    result = json.loads(tool.invoke({"endpoint": "joe/weather"}))
    assert result["error"] is True
    assert "WALLET_NOT_CONFIGURED" in result["details"]["code"]


def test_review_tool_requires_wallet():
    tool = create_review_tool(DummyClient())
    result = json.loads(tool.invoke({"purchaseId": "1", "reviewToken": "t", "positive": True}))
    assert result["error"] is True


def test_create_store_requires_wallet():
    tool = create_create_store_tool(DummyClient())
    result = json.loads(tool.invoke({"username": "store"}))
    assert result["error"] is True


def test_create_link_requires_api_key():
    tool = create_create_link_tool(DummyClient())
    result = json.loads(tool.invoke({"title": "x", "url": "https://api.example.com"}))
    assert result["error"] is True


def test_list_links_requires_api_key():
    tool = create_list_links_tool(DummyClient())
    result = json.loads(tool.invoke({}))
    assert result["error"] is True


def test_get_stats_requires_api_key():
    tool = create_get_stats_tool(DummyClient())
    result = json.loads(tool.invoke({}))
    assert result["error"] is True


def test_withdraw_requires_api_key():
    tool = create_withdraw_tool(DummyClient())
    result = json.loads(tool.invoke({"amount": "1.00", "walletAddress": "9xQeWvG816bUx9EPf3XxWcQW8tkoLhY8QzAVdHk6pY3k"}))
    assert result["error"] is True
