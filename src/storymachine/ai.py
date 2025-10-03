"""AI utilities and OpenAI abstraction for StoryMachine."""

import os
import time
from pathlib import Path
from typing import Any, List, Optional

from openai import OpenAI
from openai.types.responses import (
    ToolParam,
    Response,
    ResponseReasoningItem,
    ResponseFunctionToolCall,
)

from .config import Settings
from .logging import get_logger

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
        logger = get_logger()
        settings = Settings()  # pyright: ignore[reportCallIssue]
        client = OpenAI(api_key=settings.openai_api_key)
        conversation = client.conversations.create()
        conversation_id = conversation.id
        logger.info("conversation_created", conversation_id=conversation_id)
    return conversation_id


def get_prompt(filename: str, **kwargs: Any) -> str:
    """Load and format a prompt template from the prompts directory."""
    prompt_file = Path(__file__).parent / "prompts" / filename
    prompt_template = prompt_file.read_text()
    return prompt_template.format(**kwargs)


def _create_and_parse_response(
    client: OpenAI, params: dict, logger, log_prefix: str
) -> Response:
    """Create response, parse it, log it, and return with parsed attributes."""
    # Create response using responses.create()
    response = client.responses.create(**params)

    # Extract reasoning summaries and function calls using proper types
    reasoning_items = [
        item for item in response.output if isinstance(item, ResponseReasoningItem)
    ]
    function_calls = [
        item for item in response.output if isinstance(item, ResponseFunctionToolCall)
    ]

    reasoning_summaries = []
    for reasoning_item in reasoning_items:
        if reasoning_item.summary:
            for summary_part in reasoning_item.summary:
                if hasattr(summary_part, "text"):
                    reasoning_summaries.append(summary_part.text)

    # Log response details
    logger.info(
        f"{log_prefix}_response",
        status="success",
        tool_calls=len(function_calls),
        reasoning_items=len(reasoning_items),
        reasoning_summary_length=sum(len(s) for s in reasoning_summaries),
        response_output=[item.dict() for item in response.output],
    )

    # Attach parsed data to response using setattr for type safety
    setattr(response, "_reasoning_items", reasoning_items)
    setattr(response, "_function_calls", function_calls)
    setattr(response, "_reasoning_summaries", reasoning_summaries)

    return response


def extract_reasoning_summaries(response: Response) -> List[str]:
    """Extract reasoning summary text from OpenAI response."""
    # Check if we have combined reasoning summaries from multiple API calls
    if hasattr(response, "_combined_reasoning_summaries"):
        return getattr(response, "_combined_reasoning_summaries", [])

    # Use pre-parsed reasoning summaries if available
    if hasattr(response, "_reasoning_summaries"):
        return getattr(response, "_reasoning_summaries", [])

    # Fallback to extracting from response output
    summaries = []
    for item in response.output:
        if isinstance(item, ResponseReasoningItem) and item.summary:
            for summary_part in item.summary:
                if hasattr(summary_part, "text"):
                    summaries.append(summary_part.text)
    return summaries


def display_reasoning_summaries(summaries: List[str]) -> None:
    """Display reasoning summaries on CLI in a formatted way."""
    if not summaries:
        return

    print("\n🧠 Model Reasoning:")
    print("─" * 60)
    for i, summary in enumerate(summaries):
        if i > 0:
            print("─" * 60)
        print(summary)
    print("─" * 60)
    print()


def call_openai_api(
    prompt: str,
    tools: Optional[List[ToolParam]] = None,
) -> Response:
    """Call OpenAI API using the Responses API with proper context management."""
    start_time = time.time()
    logger = get_logger()
    settings = Settings()  # pyright: ignore[reportCallIssue]
    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.model

    # Build request parameters for responses.create()
    create_params = {
        "model": model,
        "input": [{"role": "user", "content": prompt}],
        "conversation": get_or_create_conversation(),
    }

    # Add tools and tool_choice only if tools are provided
    if tools:
        create_params["tools"] = tools
        create_params["tool_choice"] = "required"

    # Add reasoning parameters for supported models
    if supports_reasoning_parameters(model):
        create_params["reasoning"] = {
            "effort": settings.reasoning_effort,
            "summary": "auto",
        }
        create_params["text"] = {"verbosity": "low"}

    logger.info(
        "openai_request",
        model=model,
        conversation_id=create_params["conversation"],
        method="responses.create",
        request_params={
            k: v
            if k != "tools"
            else [tool.dict() if hasattr(tool, "dict") else tool for tool in v]
            for k, v in create_params.items()
        },
    )

    # Create and parse initial response
    response = _create_and_parse_response(client, create_params, logger, "openai")

    function_calls = getattr(response, "_function_calls", [])
    if function_calls:
        # Create function call outputs (empty since we don't execute them)
        function_outputs = []
        for func_call in function_calls:
            function_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": func_call.call_id,
                    "output": "",
                }
            )

        # Build follow-up input with just function outputs
        # Let conversation parameter handle reasoning context automatically
        followup_input = function_outputs

        followup_create_params = {
            "model": model,
            "input": followup_input,
            "conversation": get_or_create_conversation(),
        }

        # Add reasoning parameters for supported models
        if supports_reasoning_parameters(model):
            followup_create_params["reasoning"] = {
                "effort": settings.reasoning_effort,
                "summary": "auto",
            }
            followup_create_params["text"] = {"verbosity": "low"}

        logger.info(
            "openai_followup_request",
            model=model,
            conversation_id=get_or_create_conversation(),
            method="responses.create",
            input_items=len(followup_input),
            function_outputs_included=len(function_outputs),
            request_params={
                k: v
                if k != "tools"
                else [tool.dict() if hasattr(tool, "dict") else tool for tool in v]
                if "tools" in followup_create_params
                else v
                for k, v in followup_create_params.items()
            },
        )

        # Create and parse follow-up response
        followup_response = _create_and_parse_response(
            client, followup_create_params, logger, "openai_followup"
        )

        # Combine reasoning summaries from both responses for display
        response_summaries = getattr(response, "_reasoning_summaries", [])
        followup_summaries = getattr(followup_response, "_reasoning_summaries", [])
        combined_summaries = response_summaries + followup_summaries
        setattr(followup_response, "_combined_reasoning_summaries", combined_summaries)

        # Add original function calls to final response for story parsing
        # (They're in input context but we need them in output for parse_stories_from_response)
        original_function_calls = getattr(response, "_function_calls", [])
        if original_function_calls:
            followup_response.output.extend(original_function_calls)

        duration = time.time() - start_time
        logger.info("openai_api_duration", duration_seconds=duration)
        return followup_response

    # Store reasoning summaries for display (already attached by helper function)
    duration = time.time() - start_time
    logger.info("openai_api_duration", duration_seconds=duration)
    return response


async def answer_repo_questions(repo_path: str, questions: str) -> str:
    """Use Claude Agent SDK to query the codebase and answer questions."""
    start_time = time.time()
    logger = get_logger()
    settings = Settings()  # pyright: ignore[reportCallIssue]

    if not settings.anthropic_api_key:
        logger.error("anthropic_api_key_not_found")
        raise ValueError("ANTHROPIC_API_KEY not found in .env file")

    # Set environment variable for Claude SDK
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

    # Import Claude Agent SDK
    from claude_agent_sdk import query, ClaudeAgentOptions
    from claude_agent_sdk.types import ResultMessage

    # Create options with no tools, no mcp, no hooks, no memory
    options = ClaudeAgentOptions(
        cwd=repo_path,
        allowed_tools=[],  # No tools
    )

    logger.info("repo_query_started", repo_path=repo_path)

    # Query the codebase with the questions and extract result from ResultMessage
    response_text = ""
    async for message in query(prompt=questions, options=options):
        if isinstance(message, ResultMessage) and message.result:
            response_text = message.result
            # Don't break - continue consuming messages to avoid generator cleanup errors

    duration = time.time() - start_time
    logger.info(
        "claude_api_duration",
        duration_seconds=duration,
        response_length=len(response_text),
    )
    logger.info("claude_response", response=response_text)
    return response_text
