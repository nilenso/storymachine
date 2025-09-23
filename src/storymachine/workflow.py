"""Top-level workflow orchestration for StoryMachine."""

from typing import List

from .activities import *
from .types import Story, WorkflowInput


def w1(workflow_input: WorkflowInput) -> List[Story]:
    """Simple workflow: break down PRD and tech spec into user stories."""
    with spinner("Machining Stories"):
        stories = problem_break_down(workflow_input, [], "")

    # Display story titles
    print("Generated Stories:")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story.title}")
    print()

    # Get user feedback
    response = get_human_input()

    if response.status == FeedbackStatus.ACCEPTED:
        print("Stories approved!")
    else:
        print(f"Stories rejected. Comments: {response.comment}")

    return stories
