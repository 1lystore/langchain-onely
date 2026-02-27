"""OneLy toolkit for LangChain."""

from typing import List, Optional

import base58
from eth_account import Account
from langchain_core.tools import BaseTool, BaseToolkit
from solders.keypair import Keypair

from .client import OneLyClient
from .tools import (
    create_call_tool,
    create_create_link_tool,
    create_create_store_tool,
    create_get_details_tool,
    create_get_stats_tool,
    create_list_links_tool,
    create_review_tool,
    create_search_tool,
    create_withdraw_tool,
)


class OneLyToolkit(BaseToolkit):
    """Toolkit for OneLy marketplace - buy and sell APIs with AI agents.

    Enables AI agents to autonomously:
    - Buy APIs: Search, get details, pay with USDC, leave reviews
    - Sell APIs: Create stores, list APIs, check earnings, withdraw funds

    Example:
        ```python
        import os
        from langchain_onely import OneLyToolkit

        # As buyer (4 tools)
        toolkit = OneLyToolkit(
            base_private_key=os.getenv("BASE_PRIVATE_KEY")
        )

        # As seller (9 tools)
        toolkit = OneLyToolkit(
            base_private_key=os.getenv("BASE_PRIVATE_KEY"),
            solana_private_key=os.getenv("SOLANA_PRIVATE_KEY"),
            api_key=os.getenv("ONELY_API_KEY")
        )

        tools = toolkit.get_tools()
        ```

    Attributes:
        base_wallet: Web3 Account for Base network (for payments)
        solana_wallet: Solana Keypair (for withdrawals)
        base_private_key: Base private key string (alternative to base_wallet)
        solana_private_key: Solana private key string (alternative to solana_wallet)
        api_key: OneLy API key for seller actions (from create_store)
    """

    model_config = {"arbitrary_types_allowed": True}

    base_wallet: Optional[Account] = None
    solana_wallet: Optional[Keypair] = None
    base_private_key: Optional[str] = None
    solana_private_key: Optional[str] = None
    api_key: Optional[str] = None
    base_rpc_url: Optional[str] = None
    solana_rpc_url: Optional[str] = None

    def __init__(
        self,
        base_wallet: Optional[Account] = None,
        solana_wallet: Optional[Keypair] = None,
        base_private_key: Optional[str] = None,
        solana_private_key: Optional[str] = None,
        api_key: Optional[str] = None,
        base_rpc_url: Optional[str] = None,
        solana_rpc_url: Optional[str] = None,
    ):
        """Initialize OneLy toolkit.

        Args:
            base_wallet: Pre-created Web3 Account for Base (optional)
            solana_wallet: Pre-created Solana Keypair (optional)
            base_private_key: Base private key string (alternative, will create Account)
            solana_private_key: Solana private key string (alternative, will create Keypair)
            api_key: OneLy API key for seller actions (optional)
            base_rpc_url: Custom Base RPC URL (optional, defaults to public RPC)
            solana_rpc_url: Custom Solana RPC URL (optional, defaults to public RPC)
        """
        super().__init__()
        self.api_key = api_key
        self.base_rpc_url = base_rpc_url
        self.solana_rpc_url = solana_rpc_url

        # Handle Base wallet
        if base_wallet:
            self.base_wallet = base_wallet
        elif base_private_key:
            # Remove 0x prefix if present
            pk = base_private_key[2:] if base_private_key.startswith("0x") else base_private_key
            self.base_wallet = Account.from_key(f"0x{pk}")

        # Handle Solana wallet
        if solana_wallet:
            self.solana_wallet = solana_wallet
        elif solana_private_key:
            # Try base58 string first (standard format)
            try:
                self.solana_wallet = Keypair.from_base58_string(solana_private_key)
            except (ValueError, TypeError):
                # Fall back to bytes format
                try:
                    secret_key = base58.b58decode(solana_private_key)
                    self.solana_wallet = Keypair.from_bytes(secret_key)
                except Exception as e:
                    raise ValueError(f"Invalid Solana private key format: {e}")

    def get_tools(self) -> List[BaseTool]:
        """Get OneLy tools.

        Returns 5 tools (4 buyer + create_store) if no API key,
        or 9 tools (all buyer + seller) if API key provided.

        Returns:
            List of LangChain tools
        """
        client = OneLyClient(api_key=self.api_key)
        tools = []

        # Buyer tools (always available)
        tools.extend(
            [
                create_search_tool(client),
                create_get_details_tool(client),
                create_call_tool(
                    client,
                    self.base_wallet,
                    self.solana_wallet,
                    self.base_rpc_url,
                    self.solana_rpc_url,
                ),
                create_review_tool(client, self.base_wallet, self.solana_wallet),
            ]
        )

        # Store creation (always available - needed to GET api key)
        tools.append(create_create_store_tool(client, self.base_wallet))

        # Other seller tools (only if API key provided)
        if self.api_key:
            tools.extend(
                [
                    create_create_link_tool(client),
                    create_list_links_tool(client),
                    create_get_stats_tool(client),
                    create_withdraw_tool(client),
                ]
            )

        return tools

    @property
    def has_seller_tools(self) -> bool:
        """Check if seller tools are available (API key provided)."""
        return self.api_key is not None

    @property
    def has_base_wallet(self) -> bool:
        """Check if Base wallet is configured."""
        return self.base_wallet is not None

    @property
    def has_solana_wallet(self) -> bool:
        """Check if Solana wallet is configured."""
        return self.solana_wallet is not None
