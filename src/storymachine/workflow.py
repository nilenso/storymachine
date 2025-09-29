"""Top-level workflow orchestration for StoryMachine."""

from typing import List

from .activities import (
    get_human_input,
    problem_break_down,
    define_acceptance_criteria,
    spinner,
)
from .types import FeedbackStatus, Story, WorkflowInput


def w1(workflow_input: WorkflowInput) -> List[Story]:
    """Simple workflow: break down PRD and tech spec into user stories."""
    with spinner("Machining Stories"):
        stories = problem_break_down(workflow_input, [], "")

    while True:
        # Display story titles
        print("Generated Stories:")
        for i, story in enumerate(stories, 1):
            print(f"{i}. {story.title}")
        print()

        # Get user feedback
        response = get_human_input()

        if response.status == FeedbackStatus.ACCEPTED:
            print("Stories approved!")
            break
        else:
            print(f"Stories rejected. Comments: {response.comment}")
            print("\nRevising stories based on feedback...\n")

            with spinner("Revising Stories"):
                stories = problem_break_down(
                    workflow_input, stories, response.comment or ""
                )

    # Define acceptance criteria for each story
    for i, story in enumerate(stories):
        print(f"\n--- Defining Acceptance Criteria for Story {i + 1} ---")

        with spinner("Defining Acceptance Criteria"):
            updated_story = define_acceptance_criteria(story, "")

        while True:
            # Display story and its ACs
            print(f"\nStory: {updated_story.title}")
            print("Acceptance Criteria:")
            for j, ac in enumerate(updated_story.acceptance_criteria, 1):
                print(f"  {j}. {ac}")
            print()

            # Get user feedback for this story's ACs
            response = get_human_input()

            if response.status == FeedbackStatus.ACCEPTED:
                print("Acceptance criteria approved!")
                stories[i] = updated_story  # Update the story in the list
                break
            else:
                print(f"Acceptance criteria rejected. Comments: {response.comment}")
                print("\nRevising acceptance criteria based on feedback...\n")

                with spinner("Revising Acceptance Criteria"):
                    updated_story = define_acceptance_criteria(
                        updated_story, response.comment or ""
                    )

    # Print final list of all stories with their ACs
    print("\n" + "=" * 50)
    print("FINAL USER STORIES WITH ACCEPTANCE CRITERIA")
    print("=" * 50)
    for i, story in enumerate(stories, 1):
        print(f"\n{i}. {story.title}")
        print("   Acceptance Criteria:")
        for j, ac in enumerate(story.acceptance_criteria, 1):
            print(f"     {j}. {ac}")

    return stories
