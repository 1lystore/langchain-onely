"""OneLy tools for LangChain."""

import json
from typing import Any, Dict, Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from langchain_core.tools import StructuredTool

from .client import OneLyClient
from .constants import BASE_USDC_ADDRESS, DEFAULT_TIMEOUT, SOLANA_USDC_MINT
from .schemas import (
    CallInput,
    CreateLinkInput,
    CreateStoreInput,
    GetDetailsInput,
    GetStatsInput,
    ListLinksInput,
    ReviewInput,
    SearchInput,
    WithdrawInput,
)


def _format_response(data: Dict[str, Any]) -> str:
    """Format response for LLM.

    Always returns JSON string with 'message' field for LLM
    and optional 'details' for developers.
    """
    return json.dumps(data, indent=2)


def _safe_response_json(response) -> Optional[Any]:
    """Safely parse JSON from an HTTP response."""
    try:
        return response.json()
    except ValueError:
        return None


# ==========================================
# BUYER TOOLS (No authentication required)
# ==========================================


def create_search_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_search tool."""

    def search_fn(
        query: str,
        type: Optional[str] = None,
        minPrice: Optional[float] = None,
        maxPrice: Optional[float] = None,
        limit: int = 10,
    ) -> str:
        """Search for APIs and services on the 1ly marketplace.

        Args:
            query: Search term (e.g., 'weather api', 'image generation')
            type: Filter by 'api' or 'standard'
            minPrice: Minimum price in USD
            maxPrice: Maximum price in USD
            limit: Number of results (1-50)

        Returns:
            JSON string with search results
        """
        params = {"q": query, "limit": str(limit)}
        if type:
            params["type"] = type
        if minPrice is not None:
            params["minPrice"] = str(minPrice)
        if maxPrice is not None:
            params["maxPrice"] = str(maxPrice)

        result = client.get("/api/discover", params=params)

        if result.get("error"):
            return _format_response(result)

        # Format success response
        results = result.get("results", [])
        return _format_response(
            {
                "message": f"Found {len(results)} APIs matching '{query}'",
                "results": results,
                "total": result.get("total", len(results)),
            }
        )

    return StructuredTool(
        name="onely_search",
        description="Search the 1ly marketplace by keyword with optional type and price filters. "
        "Inputs: query, type (api|standard), minPrice, maxPrice, limit. "
        "Returns listing metadata including title, description, price, and seller info.",
        func=search_fn,
        args_schema=SearchInput,
    )


def create_get_details_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_get_details tool."""

    def get_details_fn(endpoint: str) -> str:
        """Get detailed information about a specific API listing.

        Args:
            endpoint: API endpoint (e.g., 'joe/weather' or '/api/link/joe/weather')

        Returns:
            JSON string with API details, price, payment info, and reviews
        """
        # Normalize endpoint
        if not endpoint.startswith("/api/link/"):
            endpoint = f"/api/link/{endpoint}"

        result = client.get(endpoint)

        if result.get("error"):
            return _format_response(result)

        return _format_response(
            {
                "message": f"Retrieved details for {endpoint}",
                "endpoint": endpoint,
                "fullUrl": f"{client.base_url}{endpoint}",
                "details": result,
            }
        )

    return StructuredTool(
        name="onely_get_details",
        description=(
            "Get full listing details and x402 payment requirements for a specific endpoint. "
            "Input: endpoint (e.g., joe/weather). "
            "Returns price, currency, seller info, and reviews."
        ),
        func=get_details_fn,
        args_schema=GetDetailsInput,
    )


def create_call_tool(
    client: OneLyClient,
    base_wallet: Optional[Account] = None,
    solana_wallet: Optional[Any] = None,
    base_rpc_url: Optional[str] = None,
    solana_rpc_url: Optional[str] = None,
) -> StructuredTool:
    """Create onely_call tool."""

    def call_fn(
        endpoint: str,
        method: str = "GET",
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        preferredNetwork: Optional[str] = None,
        preferredAsset: Optional[str] = None,
        allowFallback: bool = True,
    ) -> str:
        """Pay for and call an API using x402 payment protocol.

        Args:
            endpoint: API endpoint (e.g., 'joe/weather')
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            body: Request body for POST/PUT/PATCH
            headers: Additional headers

        Returns:
            JSON string with API response and purchase metadata
        """
        if not base_wallet and not solana_wallet:
            return _format_response(
                {
                    "error": True,
                    "message": "Wallet not configured. Cannot make payments.",
                    "details": {
                        "code": "WALLET_NOT_CONFIGURED",
                        "solution": "Pass base_private_key or solana_private_key to OneLyToolkit",
                    },
                }
            )

        # Normalize endpoint
        if not endpoint.startswith("/api/link/"):
            endpoint = f"/api/link/{endpoint}"

        full_url = f"{client.base_url}{endpoint}"
        request_headers = {
            "Content-Type": "application/json",
            **(headers or {}),
        }

        # Make initial request
        try:
            response = client.session.request(
                method=method,
                url=full_url,
                json=body,
                headers=request_headers,
                timeout=DEFAULT_TIMEOUT,
            )

            # Handle free APIs (200 OK)
            if response.ok:
                if not response.text:
                    return _format_response(
                        {
                            "message": f"Successfully called {endpoint}",
                            "data": None,
                            "_1ly": {
                                "note": "Empty response body",
                            },
                        }
                    )
                data = _safe_response_json(response)
                if data is None:
                    return _format_response(
                        {
                            "error": True,
                            "message": "API returned non-JSON response.",
                            "details": {
                                "code": "NON_JSON_RESPONSE",
                                "status": response.status_code,
                                "response": response.text,
                            },
                        }
                    )
                return _format_response(
                    {
                        "message": f"Successfully called {endpoint}",
                        "data": data,
                        "_1ly": {
                            "note": "Free API - no payment required",
                        },
                    }
                )

            # Handle 402 Payment Required (paid API)
            if response.status_code == 402:
                # Parse payment requirements
                try:
                    payment_data = _safe_response_json(response)
                except (ValueError, json.JSONDecodeError) as e:
                    return _format_response(
                        {
                            "error": True,
                            "message": "Failed to parse 402 payment requirements",
                            "details": {"code": "INVALID_402_RESPONSE", "exception": str(e)},
                        }
                    )
                if payment_data is None:
                    return _format_response(
                        {
                            "error": True,
                            "message": "402 response was not valid JSON.",
                            "details": {
                                "code": "INVALID_402_RESPONSE",
                                "response": response.text,
                            },
                        }
                    )

                # Get payment info
                accepts = payment_data.get("accepts", [])
                if not accepts:
                    return _format_response(
                        {
                            "error": True,
                            "message": "No payment methods available",
                            "details": {"code": "NO_PAYMENT_METHODS"},
                        }
                    )

                # Calculate price
                amount = accepts[0].get("amount") or accepts[0].get("maxAmountRequired", "0")
                try:
                    price_usd = int(amount) / 1_000_000
                except (ValueError, TypeError):
                    price_usd = 0.0

                # Import payment module
                from .payment import create_payment_signature

                def accept_matches_asset(accept_entry: dict) -> bool:
                    if not preferredAsset:
                        return True
                    asset = accept_entry.get("asset")
                    if preferredAsset == "USDC":
                        return asset in {BASE_USDC_ADDRESS, SOLANA_USDC_MINT}
                    if preferredAsset == "1LY":
                        return (
                            accept_entry.get("network", "").startswith("solana:")
                            and asset != SOLANA_USDC_MINT
                        )
                    return True

                def accept_matches_network(accept_entry: dict) -> bool:
                    if not preferredNetwork:
                        return True
                    network = str(accept_entry.get("network", ""))
                    if preferredNetwork == "base":
                        return network.startswith("eip155:")
                    if preferredNetwork == "solana":
                        return network.startswith("solana:")
                    return True

                accepts_list = payment_data.get("accepts", [])
                ordered_accepts = [
                    a for a in accepts_list if accept_matches_network(a) and accept_matches_asset(a)
                ]
                if allowFallback:
                    ordered_accepts += [a for a in accepts_list if a not in ordered_accepts]

                if not ordered_accepts:
                    return _format_response(
                        {
                            "error": True,
                            "message": (
                                "No compatible payment method found for selected preferences."
                            ),
                            "details": {"code": "NO_COMPATIBLE_PAYMENT"},
                        }
                    )

                last_error = None
                for accept in ordered_accepts:
                    payment_data_one = {**payment_data, "accepts": [accept]}
                    try:
                        payment_signature = create_payment_signature(
                            payment_data=payment_data_one,
                            base_wallet=base_wallet,
                            solana_wallet=solana_wallet,
                            resource_url=full_url,
                            base_rpc_url=base_rpc_url,
                            solana_rpc_url=solana_rpc_url,
                        )
                    except Exception as e:
                        last_error = {
                            "error": True,
                            "message": f"Failed to create payment signature: {str(e)}",
                            "details": {
                                "code": "PAYMENT_SIGNATURE_FAILED",
                                "price": price_usd,
                                "exception": str(e),
                            },
                        }
                        if not allowFallback:
                            return _format_response(last_error)
                        continue

                    try:
                        paid_response = client.session.request(
                            method=method,
                            url=full_url,
                            json=body,
                            headers={
                                **request_headers,
                                "payment-signature": payment_signature,
                            },
                            timeout=DEFAULT_TIMEOUT,
                        )

                        if not paid_response.ok:
                            error_text = paid_response.text
                            last_error = {
                                "error": True,
                                "message": f"Payment failed: {paid_response.status_code}",
                                "details": {
                                    "code": "PAYMENT_FAILED",
                                    "status": paid_response.status_code,
                                    "response": error_text,
                                    "price": price_usd,
                                },
                            }
                            if not allowFallback:
                                return _format_response(last_error)
                            continue

                        # Success! Parse response
                        if not paid_response.text:
                            response_data = None
                        else:
                            response_data = _safe_response_json(paid_response)
                            if response_data is None:
                                return _format_response(
                                    {
                                        "error": True,
                                        "message": "Paid call returned non-JSON response.",
                                        "details": {
                                            "code": "NON_JSON_RESPONSE",
                                            "status": paid_response.status_code,
                                            "response": paid_response.text,
                                        },
                                    }
                                )

                        # Extract purchase metadata if available
                        purchase_metadata = (response_data or {}).get("_1ly", {})
                        purchase_id = purchase_metadata.get("purchaseId")
                        review_token = purchase_metadata.get("reviewToken")

                        success_message = (
                            f"Successfully called {endpoint} for ${price_usd:.4f} USDC"
                        )
                        return _format_response(
                            {
                                "message": success_message,
                                "data": response_data,
                                "_1ly": {
                                    "paid": True,
                                    "price": price_usd,
                                    "currency": "USDC",
                                    "purchaseId": purchase_id,
                                    "reviewToken": review_token,
                                    "note": (
                                        "Use purchaseId and reviewToken to "
                                        "leave a review with onely_review"
                                    ),
                                },
                            }
                        )

                    except Exception as e:
                        last_error = {
                            "error": True,
                            "message": f"Paid request failed: {str(e)}",
                            "details": {
                                "code": "PAID_REQUEST_FAILED",
                                "exception": str(e),
                                "price": price_usd,
                            },
                        }
                        if not allowFallback:
                            return _format_response(last_error)
                        continue

                return _format_response(
                    last_error
                    or {
                        "error": True,
                        "message": "Payment failed with all available methods.",
                        "details": {"code": "PAYMENT_FAILED_ALL"},
                    }
                )

            # Other HTTP errors
            error_data = _safe_response_json(response)
            if error_data is None:
                error_data = {"raw": response.text} if response.text else {}
            return _format_response(
                {
                    "error": True,
                    "message": f"API call failed: {response.status_code}",
                    "details": {
                        "code": "API_ERROR",
                        "status": response.status_code,
                        "response": error_data,
                    },
                }
            )

        except Exception as e:
            return _format_response(
                {
                    "error": True,
                    "message": f"Request failed: {str(e)}",
                    "details": {
                        "code": "REQUEST_FAILED",
                        "exception": str(e),
                    },
                }
            )

    return StructuredTool(
        name="onely_call",
        description="Pay for and call an API using x402. "
        "Inputs: endpoint, method, body, headers, preferredNetwork (base|solana), "
        "preferredAsset (USDC|1LY), allowFallback (true|false). "
        "Requires: Base or Solana wallet. "
        "Returns API response plus purchaseId and reviewToken for reviews.",
        func=call_fn,
        args_schema=CallInput,
    )


def create_review_tool(
    client: OneLyClient,
    base_wallet: Optional[Account] = None,
    solana_wallet: Optional[Any] = None,
) -> StructuredTool:
    """Create onely_review tool."""

    def review_fn(
        purchaseId: str,
        reviewToken: str,
        positive: bool,
        comment: Optional[str] = None,
    ) -> str:
        """Leave a review after purchasing an API.

        Args:
            purchaseId: Purchase ID from API call response
            reviewToken: Review token from API call response
            positive: Whether review is positive (true) or negative (false)
            comment: Optional review comment (max 500 chars)

        Returns:
            JSON string with review confirmation
        """
        # Determine which wallet to use based on what's available
        wallet_address = None
        if base_wallet:
            wallet_address = base_wallet.address
        elif solana_wallet:
            # Solana wallet - get base58 pubkey
            if hasattr(solana_wallet, "pubkey"):
                wallet_address = str(solana_wallet.pubkey())
            elif hasattr(solana_wallet, "public_key"):
                wallet_address = str(solana_wallet.public_key)

        if not wallet_address:
            return _format_response(
                {
                    "error": True,
                    "message": "Wallet not configured. Cannot submit reviews.",
                    "details": {
                        "code": "WALLET_NOT_CONFIGURED",
                    },
                }
            )

        review_data = {
            "purchaseId": purchaseId,
            "wallet": wallet_address,
            "token": reviewToken,
            "positive": positive,
        }
        if comment:
            review_data["comment"] = comment

        result = client.post("/api/reviews", json_data=review_data)

        if result.get("error"):
            return _format_response(result)

        return _format_response(
            {
                "message": f"Review posted successfully ({'positive' if positive else 'negative'})",
                "review": result,
            }
        )

    return StructuredTool(
        name="onely_review",
        description="Leave a review for a purchased API. "
        "Inputs: purchaseId, reviewToken, positive, comment. "
        "Requires: Base or Solana wallet.",
        func=review_fn,
        args_schema=ReviewInput,
    )


# ==========================================
# SELLER TOOLS (Require API key)
# ==========================================


def create_create_store_tool(
    client: OneLyClient,
    base_wallet: Optional[Account] = None,
) -> StructuredTool:
    """Create onely_create_store tool."""

    def create_store_fn(
        username: Optional[str] = None,
        displayName: Optional[str] = None,
        avatarUrl: Optional[str] = None,
    ) -> str:
        """Create a store on 1ly marketplace using wallet signature.

        Args:
            username: Unique username (3-20 chars, optional)
            displayName: Display name (max 50 chars, optional)
            avatarUrl: Avatar image URL (optional)

        Returns:
            JSON string with store details and API key
        """
        if not base_wallet:
            return _format_response(
                {
                    "error": True,
                    "message": "Wallet not configured. Cannot create store.",
                    "details": {
                        "code": "WALLET_NOT_CONFIGURED",
                    },
                }
            )

        wallet_address = base_wallet.address

        # Get nonce for signature
        nonce_response = client.post(
            "/api/agent/auth/nonce",
            json_data={"address": wallet_address, "chain": "base"},
        )

        if nonce_response.get("error"):
            return _format_response(nonce_response)

        # Extract message from response
        message = nonce_response.get("data", {}).get("message")
        if not message:
            return _format_response(
                {
                    "error": True,
                    "message": "Failed to get message for signature",
                    "details": {"code": "NONCE_ERROR", "response": nonce_response},
                }
            )

        # Sign message using EIP-191
        message_encoded = encode_defunct(text=message)
        signed_message = base_wallet.sign_message(message_encoded)

        # Create store
        store_data: Dict[str, Any] = {
            "address": wallet_address,
            "chain": "base",
            "signature": signed_message.signature.hex(),
            "message": message,
        }
        if username:
            store_data["username"] = username
        if displayName:
            store_data["displayName"] = displayName
        if avatarUrl:
            store_data["avatarUrl"] = avatarUrl

        result = client.post("/api/agent/signup", json_data=store_data)

        if result.get("error"):
            return _format_response(result)

        # Extract data from response
        response_data = result.get("data", {})
        api_key = response_data.get("apiKey")
        store = response_data.get("store", {})

        return _format_response(
            {
                "message": "Store created successfully! Save the API key for seller actions.",
                "details": {
                    "store": store,
                    "apiKey": api_key,
                },
                "instructions": (
                    "IMPORTANT: Save this API key! "
                    "Use it to initialize OneLyToolkit for seller actions."
                ),
            }
        )

    return StructuredTool(
        name="onely_create_store",
        description="Create a seller store and return an API key for seller actions. "
        "Inputs: username, displayName, avatarUrl. "
        "Requires: Base wallet.",
        func=create_store_fn,
        args_schema=CreateStoreInput,
    )


def create_create_link_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_create_link tool."""

    def create_link_fn(
        title: str,
        url: str,
        description: Optional[str] = None,
        slug: Optional[str] = None,
        price: Optional[str] = None,
        currency: str = "USDC",
        isPublic: bool = True,
        isStealth: bool = False,
        webhookUrl: Optional[str] = None,
    ) -> str:
        """List a new API for sale on your 1ly store.

        Args:
            title: API listing title (1-200 chars)
            url: URL of your API endpoint
            description: API description (max 500 chars, optional)
            slug: URL-friendly slug (optional, auto-generated if not provided)
            price: Price in USDC (e.g., '0.01', optional for free APIs)
            currency: Currency (only 'USDC' supported)
            isPublic: Whether listing is publicly visible (default: true)
            isStealth: Whether listing is in stealth mode (default: false)
            webhookUrl: Webhook URL for purchase notifications (optional)

        Returns:
            JSON string with listing details and endpoint
        """
        if not client.api_key:
            return _format_response(
                {
                    "error": True,
                    "message": "API key required. Create a store first using onely_create_store.",
                    "details": {"code": "API_KEY_REQUIRED"},
                }
            )

        link_data: Dict[str, Any] = {
            "title": title,
            "url": url,
            "currency": currency,
            "isPublic": isPublic,
            "isStealth": isStealth,
        }
        if description:
            link_data["description"] = description
        if slug:
            link_data["slug"] = slug
        if price:
            link_data["price"] = price
        if webhookUrl:
            link_data["webhookUrl"] = webhookUrl

        result = client.post("/api/v1/links", json_data=link_data)

        if result.get("error"):
            return _format_response(result)

        link_data = result.get("data", {})
        return _format_response(
            {
                "message": f"API '{title}' listed successfully!",
                "details": {
                    "slug": link_data.get("slug"),
                    "fullUrl": link_data.get("fullUrl"),
                    "price": link_data.get("price"),
                    "currency": link_data.get("currency"),
                    "id": link_data.get("id"),
                },
            }
        )

    return StructuredTool(
        name="onely_create_link",
        description="List a new API for sale. "
        "Inputs: title, url, price, optional description/slug/webhook. "
        "Requires: ONELY_API_KEY.",
        func=create_link_fn,
        args_schema=CreateLinkInput,
    )


def create_list_links_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_list_links tool."""

    def list_links_fn() -> str:
        """View all your API listings.

        Returns:
            JSON string with all listings and their stats
        """
        if not client.api_key:
            return _format_response(
                {
                    "error": True,
                    "message": "API key required.",
                    "details": {"code": "API_KEY_REQUIRED"},
                }
            )

        result = client.get("/api/v1/links")

        if result.get("error"):
            return _format_response(result)

        links = result.get("data", {}).get("links", [])
        return _format_response(
            {
                "message": f"Found {len(links)} listings",
                "links": links,
            }
        )

    return StructuredTool(
        name="onely_list_links",
        description="List all your API listings and basic stats. " "Requires: ONELY_API_KEY.",
        func=list_links_fn,
        args_schema=ListLinksInput,
    )


def create_get_stats_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_get_stats tool."""

    def get_stats_fn(
        period: Optional[str] = None,
        linkId: Optional[str] = None,
    ) -> str:
        """Check your earnings and sales statistics.

        Args:
            period: Time period ('7d', '30d', '90d', 'all', default: all)
            linkId: Filter by specific link ID (optional)

        Returns:
            JSON string with revenue, purchases, and top-performing links
        """
        if not client.api_key:
            return _format_response(
                {
                    "error": True,
                    "message": "API key required.",
                    "details": {"code": "API_KEY_REQUIRED"},
                }
            )

        params = {}
        if period:
            params["period"] = period
        if linkId:
            params["linkId"] = linkId

        result = client.get("/api/v1/stats", params=params)

        if result.get("error"):
            return _format_response(result)

        stats = result.get("data", {})
        total_revenue = stats.get("totalRevenue", "0.00")
        total_purchases = stats.get("totalPurchases", 0)
        return _format_response(
            {
                "message": f"Total revenue: ${total_revenue} from {total_purchases} purchases",
                "stats": stats,
            }
        )

    return StructuredTool(
        name="onely_get_stats",
        description="Fetch earnings and sales statistics. "
        "Inputs: period (7d/30d/90d/all), linkId. "
        "Requires: ONELY_API_KEY.",
        func=get_stats_fn,
        args_schema=GetStatsInput,
    )


def create_withdraw_tool(client: OneLyClient) -> StructuredTool:
    """Create onely_withdraw tool."""

    def withdraw_fn(
        amount: str,
        walletAddress: str,
    ) -> str:
        """Withdraw earnings to your Solana wallet.

        Args:
            amount: Amount in USDC to withdraw (e.g., '10.50')
            walletAddress: Destination Solana wallet address

        Returns:
            JSON string with transaction details
        """
        if not client.api_key:
            return _format_response(
                {
                    "error": True,
                    "message": "API key required.",
                    "details": {"code": "API_KEY_REQUIRED"},
                }
            )

        withdraw_data = {
            "amount": amount,
            "walletAddress": walletAddress,
            "chain": "solana",  # Solana only for withdrawals
        }

        result = client.post("/api/v1/withdrawals", json_data=withdraw_data)

        if result.get("error"):
            return _format_response(result)

        return _format_response(
            {
                "message": f"Withdrawal of ${amount} USDC initiated to {walletAddress[:8]}...",
                "transaction": result.get("data", {}).get("transaction"),
            }
        )

    return StructuredTool(
        name="onely_withdraw",
        description="Withdraw earnings to a Solana wallet. "
        "Inputs: amount, walletAddress. "
        "Requires: ONELY_API_KEY. Solana only.",
        func=withdraw_fn,
        args_schema=WithdrawInput,
    )
