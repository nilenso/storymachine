"""Individual workflow activities for StoryMachine."""

import json
from typing import List

from openai.types.responses import (
    ToolParam,
)

from .ai import get_prompt
from .types import Story, WorkflowInput


CREATE_STORIES_TOOL: ToolParam = {
    "type": "function",
    "name": "create_stories",
    "description": "Create a list of user stories",
    "parameters": {
        "type": "object",
        "properties": {
            "stories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the user story",
                        },
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The acceptance criteria for the user story",
                        },
                    },
                    "required": ["title", "acceptance_criteria"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["stories"],
        "additionalProperties": False,
    },
    "strict": True,
}


def parse_stories_from_response(response) -> List[Story]:
    """Parse stories from OpenAI response."""
    return [
        Story(**story_data)
        for output in response.output
        if output.type == "function_call"
        for story_data in json.loads(output.arguments)["stories"]
    ]


def problem_break_down(
    workflow_input: WorkflowInput,
    stories: List[Story],
    comments: str = "",
) -> List[Story]:
    """Break down the problem into user stories."""
    # Load and format prompt template
    prompt = get_prompt(
        "problem_break_down.md",
        prd_content=workflow_input.prd_content,
        tech_spec_content=workflow_input.tech_spec_content,
    )

    # Call OpenAI API and parse response
    response = call_openai_api(prompt, [CREATE_STORIES_TOOL])
    return parse_stories_from_response(response)
