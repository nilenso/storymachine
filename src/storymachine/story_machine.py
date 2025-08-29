import json
from dataclasses import dataclass
from typing import List

from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseInputParam,
    ToolParam,
)


@dataclass
class Story:
    title: str
    acceptance_criteria: List[str]

    def __str__(self) -> str:
        return f"Title: {self.title}\n\nAcceptance Criteria:\n- {'\n- '.join(self.acceptance_criteria)}\n"


def stories_from_tool_call(tool_call: ResponseFunctionToolCall) -> List[Story]:
    story_args = json.loads(tool_call.arguments)["stories"]
    return [Story(**story_arg) for story_arg in story_args]


def stories_from_project_sources(
    client: OpenAI, prd_content: str, tech_spec_content: str, model: str
) -> List[Story]:
    """Generate stories from project sources.

    Args:
        prd_content (str): The content of the project requirements document.
        tech_spec_content (str): The content of the technical specification document.
        model (str): The OpenAI model to use for story generation.
    Returns:
        List[Story]: A list of generated stories.
    """
    prompt = f"""Given the following project sources:

<project_requirements_document>
{prd_content}
</project_requirements_document>

<technical_specification_document>
{tech_spec_content}
</technical_specification_document>

Create a list of user stories using the create_stories tool.

Ensure that the stories follow the principles laid out in Mike Cohn's 'User Stories Applied'.
"""
    create_stories_tool: ToolParam = {
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

    input_list: ResponseInputParam = [{"role": "user", "content": prompt}]
    response = client.responses.create(
        model=model,
        tools=[create_stories_tool],
        input=input_list,
        tool_choice="required",
    )

    tool_calls = [
        response for response in response.output if response.type == "function_call"
    ]

    stories = [
        story for tool_call in tool_calls for story in stories_from_tool_call(tool_call)
    ]

    return stories
