"""Pydantic schemas for OneLy tools."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ==========================================
# BUYER ACTION SCHEMAS
# ==========================================


class SearchInput(BaseModel):
    """Input schema for onely_search tool."""

    query: str = Field(..., description="Search term (e.g., 'weather api', 'image generation')")
    type: Optional[Literal["api", "standard"]] = Field(
        None, description="Filter by link type: 'api' for API endpoints, 'standard' for products"
    )
    minPrice: Optional[float] = Field(None, description="Minimum price in USD", ge=0)
    maxPrice: Optional[float] = Field(None, description="Maximum price in USD", ge=0)
    limit: int = Field(10, description="Number of results (default: 10, max: 50)", ge=1, le=50)


class GetDetailsInput(BaseModel):
    """Input schema for onely_get_details tool."""

    endpoint: str = Field(
        ..., description="API endpoint path (e.g., 'joe/weather' or '/api/link/joe/weather')"
    )


class CallInput(BaseModel):
    """Input schema for onely_call tool."""

    endpoint: str = Field(
        ..., description="API endpoint path (e.g., 'joe/weather' or '/api/link/joe/weather')"
    )
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        "GET", description="HTTP method (default: GET)"
    )
    body: Optional[dict] = Field(None, description="Request body for POST/PUT/PATCH requests")
    headers: Optional[dict] = Field(None, description="Additional headers to send")
    preferredNetwork: Optional[Literal["base", "solana"]] = Field(
        None, description="Preferred payment network (base or solana). If not set, auto-selects."
    )
    preferredAsset: Optional[Literal["USDC", "1LY"]] = Field(
        None, description="Preferred asset (USDC or 1LY on Solana). If not set, auto-selects."
    )
    allowFallback: Optional[bool] = Field(
        True, description="If true, automatically try another compatible payment method on failure."
    )


class ReviewInput(BaseModel):
    """Input schema for onely_review tool."""

    purchaseId: str = Field(..., description="Purchase ID from the API call response")
    reviewToken: str = Field(..., description="Review token from the API call response")
    positive: bool = Field(
        ..., description="Whether the review is positive (true) or negative (false)"
    )
    comment: Optional[str] = Field(
        None, description="Optional review comment (max 500 characters)", max_length=500
    )


# ==========================================
# SELLER ACTION SCHEMAS
# ==========================================


class CreateStoreInput(BaseModel):
    """Input schema for onely_create_store tool."""

    username: Optional[str] = Field(
        None,
        description="Unique username for the store (3-20 characters)",
        min_length=3,
        max_length=20,
    )
    displayName: Optional[str] = Field(
        None, description="Display name for the store (max 50 characters)", max_length=50
    )
    avatarUrl: Optional[str] = Field(None, description="URL to store avatar image")


class CreateLinkInput(BaseModel):
    """Input schema for onely_create_link tool."""

    title: str = Field(
        ..., description="Title of the API listing (1-200 characters)", min_length=1, max_length=200
    )
    url: str = Field(..., description="URL of the API endpoint to list")
    description: Optional[str] = Field(
        None, description="Description of the API (max 500 characters)", max_length=500
    )
    slug: Optional[str] = Field(
        None,
        description="URL-friendly slug (3-64 characters, lowercase alphanumeric and hyphens)",
        min_length=3,
        max_length=64,
        pattern=r"^[a-z0-9-]+$",
    )
    price: Optional[str] = Field(
        None,
        description="Price in USDC (e.g., '0.01' for 1 cent)",
        pattern=r"^\d+(\.\d{1,18})?$",
    )
    currency: Literal["USDC"] = Field("USDC", description="Currency (only USDC supported)")
    isPublic: Optional[bool] = Field(True, description="Whether the listing is publicly visible")
    isStealth: Optional[bool] = Field(False, description="Whether the listing is in stealth mode")
    webhookUrl: Optional[str] = Field(None, description="Optional webhook URL for purchase events")


class ListLinksInput(BaseModel):
    """Input schema for onely_list_links tool (no parameters required)."""

    pass


class GetStatsInput(BaseModel):
    """Input schema for onely_get_stats tool."""

    period: Optional[Literal["7d", "30d", "90d", "all"]] = Field(
        None, description="Time period for statistics (default: all)"
    )
    linkId: Optional[str] = Field(None, description="Filter statistics by specific link ID")


class WithdrawInput(BaseModel):
    """Input schema for onely_withdraw tool."""

    amount: str = Field(
        ...,
        description="Amount to withdraw in USDC (e.g., '10.50')",
        pattern=r"^\d+(\.\d{1,18})?$",
    )
    walletAddress: str = Field(
        ..., description="Destination Solana wallet address (Solana only)", min_length=26
    )
