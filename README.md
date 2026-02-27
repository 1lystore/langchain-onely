# langchain-onely

LangChain integration for the 1ly marketplace. This package provides production-ready tools that allow AI agents to discover, purchase, and monetize APIs using the x402 micropayment protocol on Base and Solana.

## Installation

```bash
pip install langchain-onely
```

**Requirements:**
- Python 3.9+
- A LangChain LLM provider (e.g., `langchain-openai`, `langchain-anthropic`)

**Install with examples:**
```bash
# Includes langchain-openai, langchain-anthropic, python-dotenv
pip install "langchain-onely[examples]"
```

**Install for development:**
```bash
# Includes pytest, black, ruff, python-dotenv
pip install "langchain-onely[dev]"
```

## Quick Start

### Buyer (discover and call APIs)

```python
import os
from langchain import hub
from langchain_onely import OneLyToolkit
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor

# Initialize toolkit with a wallet for payments
# Provide Base OR Solana (or both)
toolkit = OneLyToolkit(
    base_private_key=os.getenv("BASE_PRIVATE_KEY"),
    solana_private_key=os.getenv("SOLANA_PRIVATE_KEY")
)

tools = toolkit.get_tools()

llm = ChatOpenAI(model="gpt-4")
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

result = executor.invoke({
    "input": "Find a weather API under $0.10 and get weather for San Francisco"
})
```

Note: The example above uses `langchain-openai`. Install the provider package you prefer for your LLM.

## Examples

See `examples/` for complete, runnable scripts:
- `examples/buyer_agent.py` - Discover and call APIs
- `examples/seller_agent.py` - Create a store and list APIs

### Seller (create a store and list APIs)

```python
import os
from langchain_onely import OneLyToolkit

# Step 1: Create a store (one-time)
create_store_toolkit = OneLyToolkit(
    base_private_key=os.getenv("BASE_PRIVATE_KEY")
)
create_store_tool = [t for t in create_store_toolkit.get_tools() if t.name == "onely_create_store"][0]
store_result = create_store_tool.invoke({
    "username": "mystore",
    "displayName": "My API Store"
})

# Save the returned API key as ONELY_API_KEY

# Step 2: List an API
seller_toolkit = OneLyToolkit(
    base_private_key=os.getenv("BASE_PRIVATE_KEY"),
    solana_private_key=os.getenv("SOLANA_PRIVATE_KEY"),
    api_key=os.getenv("ONELY_API_KEY")
)
create_link_tool = [t for t in seller_toolkit.get_tools() if t.name == "onely_create_link"][0]
link_result = create_link_tool.invoke({
    "title": "Weather API",
    "url": "https://api.example.com/weather",
    "price": "0.05",
    "description": "Real-time weather data for any city"
})
```

## Configuration

Create a `.env` file (or set environment variables directly):

```bash
# Base wallet (EVM) for payments and store creation
BASE_PRIVATE_KEY=0x1234...

# Solana wallet for withdrawals
SOLANA_PRIVATE_KEY=5J3mN...

# Optional: custom RPC endpoints (recommended for production)
BASE_RPC_URL=https://mainnet.base.org
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Seller API key (after onely_create_store)
ONELY_API_KEY=1ly_live_...
```

## Tools

All tools return a JSON string with a `message` field and, when applicable, a `details` or `data` payload. Errors include `error: true` and a structured `details` object with a `code`.

### Buyer tools

`onely_search`
- Purpose: Search marketplace listings.
- Inputs: `query` (string), `type` ("api" or "standard"), `minPrice` (float), `maxPrice` (float), `limit` (1-50).
- Output: `results`, `total`.

`onely_get_details`
- Purpose: Fetch full listing details and x402 payment requirements.
- Inputs: `endpoint` (string, e.g., `joe/weather`).
- Output: `details`, `fullUrl`.

`onely_call`
- Purpose: Pay for and call a listing using x402.
- Inputs: `endpoint`, `method`, `body`, `headers`, `preferredNetwork`, `preferredAsset`, `allowFallback`.
- Requires: Base or Solana wallet.
- Output: `data` plus purchase metadata (`purchaseId`, `reviewToken`) for reviews.
- Notes: `preferredNetwork` = `base` or `solana`. `preferredAsset` = `USDC` or `1LY` (Solana only).

`onely_review`
- Purpose: Leave a review for a paid call.
- Inputs: `purchaseId`, `reviewToken`, `positive`, `comment`.
- Requires: Base or Solana wallet. The wallet used must match the wallet that paid for the purchase.

### Seller tools

`onely_create_store`
- Purpose: Create a marketplace store and get an API key.
- Inputs: `username`, `displayName`, `avatarUrl`.
- Requires: Base wallet.
- Output: `apiKey` and store details.

`onely_create_link`
- Purpose: List a paid or free API.
- Inputs: `title`, `url`, `description`, `slug`, `price`, `currency`, `isPublic`, `isStealth`, `webhookUrl`.
- Requires: `ONELY_API_KEY`.

`onely_list_links`
- Purpose: List all your API listings.
- Inputs: none.
- Requires: `ONELY_API_KEY`.

`onely_get_stats`
- Purpose: Revenue and sales stats.
- Inputs: `period` ("7d" | "30d" | "90d" | "all"), `linkId`.
- Requires: `ONELY_API_KEY`.

`onely_withdraw`
- Purpose: Withdraw earnings to Solana.
- Inputs: `amount`, `walletAddress`.
- Requires: `ONELY_API_KEY`.

## Security Notes

- Never commit private keys or API keys.
- Keep wallet balances minimal for testing.
- Use custom RPC endpoints for reliability and rate-limit protection.
- This toolkit is non-custodial; keys are used only for signing.

## Payment Preferences

You can explicitly choose the payment network and asset per call:

```python
call_tool.invoke({
    "endpoint": "agent/emoji-hub",
    "method": "GET",
    "preferredNetwork": "base",   # or "solana"
    "preferredAsset": "USDC",     # or "1LY" (Solana only)
    "allowFallback": True         # try another compatible method on failure
})
```

## Development

```bash
pip install -e ".[dev]"
ruff check langchain_onely/
black --check langchain_onely/
```

## Testing

```bash
pytest tests/
```

## License

MIT License. See `LICENSE`.
