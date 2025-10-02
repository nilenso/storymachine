"""Top-level workflow orchestration for StoryMachine."""

from typing import List

from .activities import (
    get_human_input,
    get_codebase_context,
    problem_break_down,
    define_acceptance_criteria,
    enrich_context,
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

    # Get codebase context questions
    print("\n--- Getting Codebase Context ---\n")
    with spinner("Analyzing codebase needs"):
        codebase_questions = get_codebase_context(workflow_input)

    # Display the questions
    print("\n📋 Codebase Context Questions:")
    print("─" * 60)
    print(codebase_questions)
    print("─" * 60)
    print("\n[Temporary exit - workflow will continue in next iteration]\n")
    return []

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

    # Define acceptance criteria and enrich context for each story
    for i, story in enumerate(stories):
        print(f"\n--- Detailing Story {i + 1} ---")

        # Set default empty states
        updated_story = story
        comments = ""

        while True:
            # Generate or revise acceptance criteria based on current state
            spinner_text = (
                "Defining Acceptance Criteria"
                if not comments
                else "Revising Acceptance Criteria"
            )
            with spinner(spinner_text):
                updated_story = define_acceptance_criteria(updated_story, comments)

            # Enrich context with PRD and tech spec details
            spinner_text = (
                "Detailing the story" if not comments else "Revising the story"
            )
            with spinner(spinner_text):
                updated_story = enrich_context(updated_story, workflow_input, comments)

            # Display story and its ACs
            print_story_with_criteria(updated_story)

            # Get user feedback for this story
            response = get_human_input()

            if response.status == FeedbackStatus.ACCEPTED:
                logger.info("story_approved", story_index=i)
                print("Story approved!")
                stories[i] = updated_story  # Update the story in the list
                break
            else:
                logger.info(
                    "story_rejected",
                    story_index=i,
                    comment=response.comment,
                )
                print(f"Story rejected. Comments: {response.comment}")
                print("\nRevising story based on feedback...\n")
                comments = response.comment or ""

    # Print final list of all stories with their ACs
    print_final_stories(stories)

    return stories
