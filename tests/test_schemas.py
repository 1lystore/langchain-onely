import pytest
from pydantic import ValidationError

from langchain_onely.schemas import (
    SearchInput,
    GetDetailsInput,
    CallInput,
    ReviewInput,
    CreateStoreInput,
    CreateLinkInput,
    GetStatsInput,
    WithdrawInput,
)


def test_search_defaults():
    data = SearchInput(query="weather api")
    assert data.query == "weather api"
    assert data.limit == 10


def test_search_price_bounds():
    data = SearchInput(query="weather", minPrice=0.01, maxPrice=1.0, limit=20)
    assert data.minPrice == 0.01
    assert data.maxPrice == 1.0
    assert data.limit == 20


def test_get_details():
    data = GetDetailsInput(endpoint="joe/weather")
    assert data.endpoint == "joe/weather"


def test_call_defaults():
    data = CallInput(endpoint="joe/weather")
    assert data.method == "GET"


def test_review_schema():
    data = ReviewInput(purchaseId="123", reviewToken="token123", positive=True)
    assert data.positive is True
    assert data.comment is None


def test_create_store_validation():
    data = CreateStoreInput(username="mystore", displayName="My Store")
    assert data.username == "mystore"
    assert data.displayName == "My Store"


def test_create_link_schema():
    data = CreateLinkInput(title="Weather API", url="https://api.example.com/weather")
    assert data.title == "Weather API"
    assert data.currency == "USDC"


def test_create_link_slug_validation():
    with pytest.raises(ValidationError):
        CreateLinkInput(title="X", url="https://api.example.com", slug="Bad Slug")


def test_withdraw_schema():
    data = WithdrawInput(amount="10.50", walletAddress="9xQeWvG816bUx9EPf3XxWcQW8tkoLhY8QzAVdHk6pY3k")
    assert data.amount == "10.50"


def test_stats_schema():
    data = GetStatsInput(period="30d")
    assert data.period == "30d"
