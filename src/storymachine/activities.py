"""Individual workflow activities for StoryMachine."""

import itertools
import json
import sys
import time
from contextlib import contextmanager
from threading import Event, Thread
from typing import List

from openai.types.responses import (
    ToolParam,
)

from .ai import (
    get_prompt,
    call_openai_api,
    extract_reasoning_summaries,
    display_reasoning_summaries,
)
from .types import FeedbackResponse, Story, WorkflowInput, FeedbackStatus
from .logging import get_logger


@contextmanager
def spinner(text="Loading", delay=0.1, stream=sys.stderr):
    """Display a spinner while executing code."""
    stop = Event()

    def run():
        stream.write("\x1b[?25l")  # hide cursor
        for c in itertools.cycle("|/-\\"):
            if stop.is_set():
                break
            stream.write(f"\r{c} {text}")
            stream.flush()
            time.sleep(delay)

    t = Thread(target=run, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join()
        stream.write("\r\x1b[2K\x1b[?25h")  # clear line + show cursor
        stream.flush()


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
                        "enriched_context": {
                            "type": "string",
                            "description": "Additional context and details for the story from PRD and tech spec",
                        },
                    },
                    "required": ["title", "acceptance_criteria", "enriched_context"],
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
    logger = get_logger()
    stories = [
        Story(**story_data)
        for output in response.output
        if output.type == "function_call"
        for story_data in json.loads(output.arguments)["stories"]
    ]
    logger.info("stories_parsed", count=len(stories))
    return stories


def problem_break_down(
    workflow_input: WorkflowInput,
    stories: List[Story],
    comments: str = "",
) -> List[Story]:
    """Break down the problem into user stories."""
    logger = get_logger()
    is_revision = bool(stories)
    logger.info("problem_breakdown_started", is_revision=is_revision)

    if stories:
        # If stories exist, this is a revision - use iterating on stories prompt
        prompt = get_prompt("iterating_on_stories.md", comments=comments)
    else:
        # Initial story generation - use full prompt template
        prompt = get_prompt(
            "problem_break_down.md",
            prd_content=workflow_input.prd_content,
            tech_spec_content=workflow_input.tech_spec_content,
        )

    # Call OpenAI API and parse response
    response = call_openai_api(prompt, [CREATE_STORIES_TOOL])

    # Display reasoning summaries
    reasoning_summaries = extract_reasoning_summaries(response)
    display_reasoning_summaries(reasoning_summaries)

    return parse_stories_from_response(response)


def enrich_context(
    story: Story,
    workflow_input: WorkflowInput,
    comments: str = "",
) -> Story:
    """Enrich a user story with details from PRD and tech spec."""
    logger = get_logger()
    is_revision = bool(comments)
    logger.info(
        "enrich_context_started", story_title=story.title, is_revision=is_revision
    )

    # Always use enrich context prompt, with or without comments
    prompt = get_prompt(
        "enrich_context.md",
        story_title=story.title,
        acceptance_criteria="\n".join(story.acceptance_criteria),
        comments=comments,
        prd_content=workflow_input.prd_content,
        tech_spec_content=workflow_input.tech_spec_content,
    )

    # Call OpenAI API and parse response
    response = call_openai_api(prompt, [CREATE_STORIES_TOOL])

    # Display reasoning summaries
    reasoning_summaries = extract_reasoning_summaries(response)
    display_reasoning_summaries(reasoning_summaries)

    updated_stories = parse_stories_from_response(response)

    # Return the first (and should be only) story from the response
    return updated_stories[0] if updated_stories else story


def define_acceptance_criteria(
    story: Story,
    comments: str = "",
) -> Story:
    """Define acceptance criteria for a user story."""
    logger = get_logger()
    is_revision = bool(story.acceptance_criteria and comments)
    logger.info(
        "acceptance_criteria_started", story_title=story.title, is_revision=is_revision
    )

    # Always use acceptance criteria prompt, with or without comments
    user_story_text = f"Title: {story.title}\nAcceptance Criteria: {', '.join(story.acceptance_criteria)}"
    prompt = get_prompt(
        "acceptance_criteria.md", user_story=user_story_text, comments=comments
    )

    # Call OpenAI API and parse response
    response = call_openai_api(prompt, [CREATE_STORIES_TOOL])

    # Display reasoning summaries
    reasoning_summaries = extract_reasoning_summaries(response)
    display_reasoning_summaries(reasoning_summaries)

    updated_stories = parse_stories_from_response(response)

    # Return the first (and should be only) story from the response
    return updated_stories[0] if updated_stories else story


def get_human_input() -> FeedbackResponse:
    """Get user approval/rejection response from CLI."""
    while True:
        approval = input("Approve (y/n): ").strip().lower()
        if approval in ["y", "yes"]:
            return FeedbackResponse(status=FeedbackStatus.ACCEPTED)
        elif approval in ["n", "no"]:
            comment = input("Please provide comments: ").strip()
            return FeedbackResponse(status=FeedbackStatus.REJECTED, comment=comment)
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def print_story_titles(
    stories: List[Story], header: str = "Generated Stories:"
) -> None:
    """Print a list of story titles with numbers."""
    print(header)
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story.title}")
    print()


def print_story_with_criteria(story: Story, story_prefix: str = "Story:") -> None:
    """Print a single story with its acceptance criteria."""
    print(f"\n{story_prefix} {story.title}")
    print("Acceptance Criteria:")
    for j, ac in enumerate(story.acceptance_criteria, 1):
        print(f"  {j}. {ac}")
    if story.enriched_context:
        print("\nContext:")
        print(f"{story.enriched_context}")
    print()


def print_final_stories(stories: List[Story]) -> None:
    """Print final summary of all stories with acceptance criteria."""
    print("\n" + "=" * 50)
    print("FINAL USER STORIES WITH ACCEPTANCE CRITERIA")
    print("=" * 50)
    for i, story in enumerate(stories, 1):
        print(f"\n{i}. {story.title}")
        print("   Acceptance Criteria:")
        for j, ac in enumerate(story.acceptance_criteria, 1):
            print(f"     {j}. {ac}")
        if story.enriched_context:
            print("   Context:")
            print(f"     {story.enriched_context}")
