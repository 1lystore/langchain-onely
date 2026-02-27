# Examples

This directory contains working examples demonstrating langchain-onely usage.

## Installation

Install example dependencies:

```bash
# Option 1: Install with examples extras
pip install "langchain-onely[examples]"

# Option 2: Install from requirements.txt
pip install -r examples/requirements.txt

# Option 3: Install specific provider only
pip install langchain-onely langchain-openai python-dotenv
```

## Configuration

Create a `.env` file in the project root (or set environment variables):

```bash
# Required for buyer examples
BASE_PRIVATE_KEY=0x...
SOLANA_PRIVATE_KEY=5J3mN...  # Optional, for multi-chain support

# Required for seller examples
ONELY_API_KEY=1ly_live_...  # Get this from onely_create_store

# Required for LangChain agents
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

## Examples

### Buyer Agent (`buyer_agent.py`)

Demonstrates how to build an AI agent that can:
- Search for APIs on the marketplace
- Get pricing and details
- Automatically pay for and call APIs
- Leave reviews

**Run:**
```bash
python examples/buyer_agent.py
```

### Seller Agent (`seller_agent.py`)

Demonstrates how to:
- Create a store on the marketplace
- List APIs for sale
- Check earnings and statistics
- Withdraw funds

**Run:**
```bash
python examples/seller_agent.py
```

## Troubleshooting

### Import errors in VS Code

If you see `Import "langchain_openai" could not be resolved`:

1. **Install dependencies:**
   ```bash
   pip install "langchain-onely[examples]"
   ```

2. **Select correct Python interpreter:**
   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Python: Select Interpreter"
   - Choose the interpreter where you installed the packages

3. **Reload VS Code window:**
   - Press `Cmd+Shift+P` / `Ctrl+Shift+P`
   - Type "Developer: Reload Window"

### Missing API keys

Ensure your `.env` file exists and contains all required keys. The examples use `python-dotenv` to load environment variables.

## Notes

- Examples use `langchain-openai` by default
- You can substitute with `langchain-anthropic` or any other LangChain LLM provider
- The core `langchain-onely` package doesn't require a specific LLM provider
- Examples are optional and not included in the main package installation
