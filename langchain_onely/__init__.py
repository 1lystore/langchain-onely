"""LangChain integration for OneLy x402 marketplace.

Enable AI agents to autonomously buy AND sell APIs on the 1ly marketplace.

Example:
    ```python
    import os
    from langchain_onely import OneLyToolkit
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_react_agent, AgentExecutor

    # Initialize toolkit
    toolkit = OneLyToolkit(
        base_private_key=os.getenv("BASE_PRIVATE_KEY"),
        api_key=os.getenv("ONELY_API_KEY")  # For seller actions
    )

    # Get tools
    tools = toolkit.get_tools()

    # Create agent
    llm = ChatOpenAI(model="gpt-4")
    agent = create_react_agent(llm, tools, prompt_template)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Agent can now buy and sell APIs!
    result = executor.invoke({
        "input": "Find a weather API under $0.10 and get weather for NYC"
    })
    ```
"""

from .client import OneLyClient
from .constants import ONELY_API_BASE, PACKAGE_VERSION, SUPPORTED_NETWORKS
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
from .toolkit import OneLyToolkit

__version__ = PACKAGE_VERSION
__all__ = [
    "OneLyToolkit",
    "OneLyClient",
    "ONELY_API_BASE",
    "SUPPORTED_NETWORKS",
    "SearchInput",
    "GetDetailsInput",
    "CallInput",
    "ReviewInput",
    "CreateStoreInput",
    "CreateLinkInput",
    "ListLinksInput",
    "GetStatsInput",
    "WithdrawInput",
]
