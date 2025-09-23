"""AI utilities and OpenAI abstraction for StoryMachine."""

from pathlib import Path
from typing import Any, List

from openai import OpenAI
from openai.types.responses import (
    ResponseInputParam,
    ToolParam,
)

from .config import Settings


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
    settings = Settings(_env_file=".env")  # pyright: ignore[reportCallIssue]
    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.model

    input_list: ResponseInputParam = [{"role": "user", "content": prompt}]

    request_params = {
        "model": model,
        "tools": tools,
        "input": input_list,
        "tool_choice": "required",
    }

    if supports_reasoning_parameters(model):
        request_params["reasoning"] = {"effort": "medium"}
        request_params["text"] = {"verbosity": "low"}

    response = client.responses.create(**request_params)

    return response
