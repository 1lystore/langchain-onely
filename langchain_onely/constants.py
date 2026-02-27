"""Constants for langchain-onely package."""

# Package version
PACKAGE_VERSION = "0.1.1"

# API Base URL
ONELY_API_BASE = "https://1ly.store"

# Supported Networks (mainnet only)
SUPPORTED_NETWORKS = ["base-mainnet", "solana-mainnet"]

# Chain IDs
BASE_CHAIN_ID = 8453  # Base mainnet
SOLANA_CLUSTER = "mainnet-beta"

# Currency
SUPPORTED_CURRENCY = "USDC"

# Stable asset identifiers (for payment selection)
BASE_USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SOLANA_USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Tool Names
TOOL_SEARCH = "onely_search"
TOOL_GET_DETAILS = "onely_get_details"
TOOL_CALL = "onely_call"
TOOL_REVIEW = "onely_review"
TOOL_CREATE_STORE = "onely_create_store"
TOOL_CREATE_LINK = "onely_create_link"
TOOL_LIST_LINKS = "onely_list_links"
TOOL_GET_STATS = "onely_get_stats"
TOOL_WITHDRAW = "onely_withdraw"

# HTTP
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # exponential backoff multiplier
