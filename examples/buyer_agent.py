"""Buyer agent example for langchain-onely.

Install dependencies:
    pip install "langchain-onely[examples]"
    # OR
    pip install -r examples/requirements.txt
"""

import os
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI  # Requires: pip install langchain-openai
from langchain.agents import create_react_agent, AgentExecutor

from langchain_onely import OneLyToolkit


def main() -> None:
    load_dotenv()

    toolkit = OneLyToolkit(
        base_private_key=os.getenv("BASE_PRIVATE_KEY"),
        solana_private_key=os.getenv("SOLANA_PRIVATE_KEY"),
    )
    tools = toolkit.get_tools()

    llm = ChatOpenAI(model="gpt-4")
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    result = executor.invoke({
        "input": "Find a weather API under $0.10 and get weather for San Francisco"
    })

    print(result)


if __name__ == "__main__":
    main()
