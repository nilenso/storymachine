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
        criteria_text = "\n- ".join(self.acceptance_criteria)
        return f"Title: {self.title}\n\nAcceptance Criteria:\n- {criteria_text}\n"


def parse_stories_from_response(tool_call: ResponseFunctionToolCall) -> List[Story]:
    story_args = json.loads(tool_call.arguments)["stories"]
    return [Story(**story_arg) for story_arg in story_args]


def model_supports_reasoning(model: str) -> bool:
    """Check if the model supports reasoning and text parameters.

    Args:
        model: The OpenAI model name

    Returns:
        True if the model supports reasoning parameters, False otherwise
    """
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
    prompt = f"""<task>
From the sources below, produce a list of user stories via the `create_stories` tool.
</task>

<sources>
<project_requirements_document>
{prd_content}
</project_requirements_document>
<technical_specification_document>
{tech_spec_content}
</technical_specification_document>
</sources>

<coverage_plan>
- Extract personas that appear in sources.
- Extract all user-facing functional requirements and acceptance tests from sources into a capability list.
- Remove items marked Non-goals or clearly NFR-only.
- Produce one minimal, independent story per capability until all are covered. Split list vs detail, view vs edit, read vs write.
- Include role/permission behaviors where specified (e.g., Admin vs Viewer) inside AC of relevant stories.
- Treat PRD “Acceptance tests” as must-cover behaviors in stories or AC.
- If tech spec adds user-visible behavior not in PRD, include it only if corroborated; otherwise exclude.
</coverage_plan>

<quality_bar>
- Follow Mike Cohn’s user story principles and the INVEST heuristic.
- Use real end-user personas that appear in the sources. No system/app/stakeholder actors.
- Scope each story to one user-facing capability with clear business value.
- Do not invent requirements. If something is not supported by the sources, omit it.
- Keep stories independent and non-duplicative. Prefer vertical slices.
</quality_bar>

<acceptance_criteria_rules>
- Use Given/When/Then. Behavior-focused only. No implementation details.
- Metrics only if explicitly in sources. No arbitrary thresholds.
- Cover primary flow and the key edge cases stated in sources.
</acceptance_criteria_rules>

<format>
Return only a `create_stories` tool call with:
- `title`: "As a <persona>, I want <capability> so that <benefit>."
- `acceptance_criteria`: 3–6 items, each a single Given/When/Then line.
No extra commentary or prose outside the tool call.
</format>

<controls>
- Reason strictly from sources; use their terms.
- Prefer smaller vertical slices. Avoid duplicates and overlaps.
- For every story you include, be able to point to the exact source clause internally (do not output references).
- Do not create stories for pure NFRs or release criteria; if an NFR shapes behavior, reflect it as observable behavior only.
- Do not stop generating until every user-facing capability from the coverage_plan is represented by at least one story.
</controls>

<self_reflection>
Internally check before emitting:
1) Coverage: every user-facing capability and acceptance test from sources appears in exactly one story (or a clearly split pair) with no gaps.
2) Persona: each title uses a real end-user persona from sources.
3) Title: states capability and benefit.
4) AC: behavioral, testable, grounded in sources; permissions included where specified.
5) No duplicates/overlaps; split or merge as needed to satisfy INVEST.
Do not output this reflection.
</self_reflection>
"""

    stories_tool_schema: ToolParam = {
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

    request_params = {
        "model": model,
        "tools": [stories_tool_schema],
        "input": input_list,
        "tool_choice": "required",
    }

    if model_supports_reasoning(model):
        request_params["reasoning"] = {"effort": "medium"}
        request_params["text"] = {"verbosity": "low"}

    response = client.responses.create(**request_params)

    tool_calls = [
        response for response in response.output if response.type == "function_call"
    ]

    stories = [
        story
        for tool_call in tool_calls
        for story in parse_stories_from_response(tool_call)
    ]

    return stories
