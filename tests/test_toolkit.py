from eth_account import Account

from langchain_onely.toolkit import OneLyToolkit


def test_toolkit_default():
    toolkit = OneLyToolkit()
    assert toolkit.base_wallet is None
    assert toolkit.solana_wallet is None
    assert toolkit.api_key is None
    assert not toolkit.has_base_wallet
    assert not toolkit.has_solana_wallet
    assert not toolkit.has_seller_tools


def test_toolkit_base_private_key():
    pk = "0x59c6995e998f97a5a0044966f0945388cfb62d9b9b7f6a11ad6b3f07b6a5f0fb"
    toolkit = OneLyToolkit(base_private_key=pk)
    assert toolkit.base_wallet is not None
    assert toolkit.has_base_wallet


def test_toolkit_api_key_enables_seller_tools():
    pk = "0x59c6995e998f97a5a0044966f0945388cfb62d9b9b7f6a11ad6b3f07b6a5f0fb"
    toolkit = OneLyToolkit(base_private_key=pk, api_key="1ly_live_test")
    assert toolkit.has_seller_tools


def test_toolkit_tools_count():
    pk = "0x59c6995e998f97a5a0044966f0945388cfb62d9b9b7f6a11ad6b3f07b6a5f0fb"
    buyer_toolkit = OneLyToolkit(base_private_key=pk)
    buyer_tools = buyer_toolkit.get_tools()
    assert len(buyer_tools) == 5

    seller_toolkit = OneLyToolkit(base_private_key=pk, api_key="1ly_live_test")
    seller_tools = seller_toolkit.get_tools()
    assert len(seller_tools) == 9
