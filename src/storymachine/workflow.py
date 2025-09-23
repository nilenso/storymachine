"""Top-level workflow orchestration for StoryMachine."""

from typing import List

from .activities import problem_break_down
from .types import Story, WorkflowInput


def w1(workflow_input: WorkflowInput) -> List[Story]:
    """Simple workflow: break down PRD and tech spec into user stories."""
    stories = problem_break_down(workflow_input, [], "")

    # Display story titles
    print("Generated Stories:")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story.title}")

    return stories
