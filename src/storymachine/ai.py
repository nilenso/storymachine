"""AI utilities and OpenAI abstraction for StoryMachine."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.responses import (
    ToolParam,
)

from .config import Settings

# Global conversation state
conversation_id: Optional[str] = None


def supports_reasoning_parameters(model: str) -> bool:
    """Check if the model supports reasoning and text parameters."""
    reasoning_capable_models = {
        "o1-preview",
        "o1-mini",
        "o1",
        "o3-mini",
        "o3",
        "o4-mini",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "codex-mini-latest",
    }

    return (
        model in reasoning_capable_models
        or model.startswith("o1-")
        or model.startswith("o3-")
        or model.startswith("o4-")
        or model.startswith("codex-")
        or (model.startswith("gpt-5") and not model.startswith("gpt-5-chat"))
    )


def get_or_create_conversation() -> str:
    """Get existing conversation ID or create a new one."""
    global conversation_id
    if conversation_id is None:
        settings = Settings()  # pyright: ignore[reportCallIssue]
        client = OpenAI(api_key=settings.openai_api_key)
        conversation = client.conversations.create()
        conversation_id = conversation.id
    return conversation_id


def get_prompt(filename: str, **kwargs: Any) -> str:
    """Load and format a prompt template from the prompts directory."""
    prompt_file = Path(__file__).parent / "prompts" / filename
    prompt_template = prompt_file.read_text()
    return prompt_template.format(**kwargs)


def call_openai_api(
    prompt: str,
    tools: List[ToolParam],
):
    """Call OpenAI API and return the response."""
    settings = Settings()  # pyright: ignore[reportCallIssue]
    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.model

    input_messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]

    request_params = {
        "model": model,
        "tools": tools,
        "input": input_messages,
        "tool_choice": "required",
        "conversation": get_or_create_conversation(),
    }

    if supports_reasoning_parameters(model):
        request_params["reasoning"] = {"effort": settings.reasoning_effort}
        request_params["text"] = {"verbosity": "low"}

    response = client.responses.create(**request_params)

    # Process tool calls and send results back
    for tool_call in response.output:
        if tool_call.type != "function_call":
            continue

        # Add the original tool call to conversation history
        input_messages.append(
            {
                "type": "function_call",
                "call_id": tool_call.call_id,
                "name": tool_call.name,
                "arguments": tool_call.arguments,
            }
        )

        # Add the tool call output
        input_messages.append(
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": "",
            }
        )

    # If there were tool calls, make a second API call with the results
    if any(tool_call.type == "function_call" for tool_call in response.output):
        request_params["input"] = input_messages
        request_params.pop("tool_choice", None)  # Remove tool_choice for follow-up call
        _response = client.responses.create(**request_params)

    return response
