"""Top-level workflow orchestration for StoryMachine."""

from typing import List

from .activities import (
    get_human_input,
    problem_break_down,
    define_acceptance_criteria,
    spinner,
    print_story_titles,
    print_story_with_criteria,
    print_final_stories,
)
from .types import FeedbackStatus, Story, WorkflowInput
from .logging import get_logger


def w1(workflow_input: WorkflowInput) -> List[Story]:
    """Simple workflow: break down PRD and tech spec into user stories."""
    logger = get_logger()
    logger.info("workflow_started")

    # Set default empty states
    stories: List[Story] = []
    comments = ""

    while True:
        # Generate or revise stories based on current state
        spinner_text = "Machining Stories" if not stories else "Revising Stories"
        with spinner(spinner_text):
            stories = problem_break_down(workflow_input, stories, comments)

        log_event = "stories_generated" if not comments else "stories_revised"
        logger.info(log_event, count=len(stories))

        # Display story titles
        print_story_titles(stories)

        # Get user feedback
        response = get_human_input()

        if response.status == FeedbackStatus.ACCEPTED:
            logger.info("stories_approved")
            print("Stories approved!")
            break
        else:
            logger.info("stories_rejected", comment=response.comment)
            print(f"Stories rejected. Comments: {response.comment}")
            print("\nRevising stories based on feedback...\n")
            comments = response.comment or ""

    # Define acceptance criteria for each story
    for i, story in enumerate(stories):
        print(f"\n--- Defining Acceptance Criteria for Story {i + 1} ---")

        # Set default empty states for acceptance criteria
        updated_story = story
        ac_comments = ""

        while True:
            # Generate or revise acceptance criteria based on current state
            spinner_text = (
                "Defining Acceptance Criteria"
                if not ac_comments
                else "Revising Acceptance Criteria"
            )
            with spinner(spinner_text):
                updated_story = define_acceptance_criteria(updated_story, ac_comments)

            # Display story and its ACs
            print_story_with_criteria(updated_story)

            # Get user feedback for this story's ACs
            response = get_human_input()

            if response.status == FeedbackStatus.ACCEPTED:
                logger.info("acceptance_criteria_approved", story_index=i)
                print("Acceptance criteria approved!")
                stories[i] = updated_story  # Update the story in the list
                break
            else:
                logger.info(
                    "acceptance_criteria_rejected",
                    story_index=i,
                    comment=response.comment,
                )
                print(f"Acceptance criteria rejected. Comments: {response.comment}")
                print("\nRevising acceptance criteria based on feedback...\n")
                ac_comments = response.comment or ""

    # Print final list of all stories with their ACs
    print_final_stories(stories)

    return stories
