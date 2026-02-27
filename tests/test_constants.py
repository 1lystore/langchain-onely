from langchain_onely.constants import (
    ONELY_API_BASE,
    SUPPORTED_NETWORKS,
    BASE_CHAIN_ID,
    SOLANA_CLUSTER,
    SUPPORTED_CURRENCY,
    TOOL_SEARCH,
    TOOL_GET_DETAILS,
    TOOL_CALL,
    TOOL_REVIEW,
    TOOL_CREATE_STORE,
    TOOL_CREATE_LINK,
    TOOL_LIST_LINKS,
    TOOL_GET_STATS,
    TOOL_WITHDRAW,
)


def test_api_base():
    assert ONELY_API_BASE == "https://1ly.store"
    assert ONELY_API_BASE.startswith("https://")
    assert not ONELY_API_BASE.endswith("/")


def test_supported_networks():
    assert len(SUPPORTED_NETWORKS) == 2
    assert "base-mainnet" in SUPPORTED_NETWORKS
    assert "solana-mainnet" in SUPPORTED_NETWORKS
    assert "base-sepolia" not in SUPPORTED_NETWORKS
    assert "solana-devnet" not in SUPPORTED_NETWORKS


def test_chain_constants():
    assert BASE_CHAIN_ID == 8453
    assert SOLANA_CLUSTER == "mainnet-beta"
    assert SUPPORTED_CURRENCY == "USDC"


def test_tool_names():
    tools = [
        TOOL_SEARCH,
        TOOL_GET_DETAILS,
        TOOL_CALL,
        TOOL_REVIEW,
        TOOL_CREATE_STORE,
        TOOL_CREATE_LINK,
        TOOL_LIST_LINKS,
        TOOL_GET_STATS,
        TOOL_WITHDRAW,
    ]
    for tool in tools:
        assert tool.startswith("onely_")
        assert "_" in tool
        assert tool.islower()
