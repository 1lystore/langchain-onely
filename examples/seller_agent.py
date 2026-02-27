"""Seller agent example for langchain-onely.

Install dependencies:
    pip install "langchain-onely[examples]"
    # OR
    pip install -r examples/requirements.txt
"""

import os
from dotenv import load_dotenv

from langchain_onely import OneLyToolkit


def main() -> None:
    load_dotenv()

    base_private_key = os.getenv("BASE_PRIVATE_KEY")
    api_key = os.getenv("ONELY_API_KEY")

    if not base_private_key:
        raise SystemExit("BASE_PRIVATE_KEY is required for seller actions")

    # Create store if no API key yet
    if not api_key:
        toolkit = OneLyToolkit(base_private_key=base_private_key)
        create_store_tool = [t for t in toolkit.get_tools() if t.name == "onely_create_store"][0]
        result = create_store_tool.invoke({
            "username": "mystore",
            "displayName": "My API Store",
        })
        print(result)
        print("Save the returned API key as ONELY_API_KEY and re-run this script.")
        return

    # List an API
    toolkit = OneLyToolkit(
        base_private_key=base_private_key,
        solana_private_key=os.getenv("SOLANA_PRIVATE_KEY"),
        api_key=api_key,
    )
    create_link_tool = [t for t in toolkit.get_tools() if t.name == "onely_create_link"][0]
    result = create_link_tool.invoke({
        "title": "Weather API",
        "url": "https://api.example.com/weather",
        "price": "0.05",
        "description": "Real-time weather data for any city",
    })

    print(result)


if __name__ == "__main__":
    main()
