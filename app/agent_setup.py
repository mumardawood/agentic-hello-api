"""AI Agent configuration - kept separate from the API layer."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.models.ollama_provider import get_model

from agents import Agent, Runner, function_tool


@function_tool
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}! Welcome to Agentic AI Hub!"


agent = Agent(
    name="Hello Agent",
    instructions=(
        "You are a friendly greeter. "
        "Use the greet tool when someone tells you their name. "
        "Be warm and concise."
    ),
    model=get_model(),
    tools=[greet],
)


async def run_agent(history: list[dict], new_message: str) -> str:
    """Run the agent with prior history plus a new user message."""
    
    input_list = history + [{"role": "user", "content": new_message}]

    result = await Runner.run(agent, input_list)
    return result.final_output
