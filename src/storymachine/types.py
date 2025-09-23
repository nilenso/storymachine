"""Common types for StoryMachine workflow."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ResponseStatus(Enum):
    """Status of human response in workflow."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class Story:
    """A user story with title and acceptance criteria."""

    title: str
    acceptance_criteria: List[str]

    def __str__(self) -> str:
        criteria_text = "\n- ".join(self.acceptance_criteria)
        return f"Title: {self.title}\n\nAcceptance Criteria:\n- {criteria_text}\n"


@dataclass
class WorkflowInput:
    """Input data for the story generation workflow."""

    prd_content: str
    tech_spec_content: str


# TODO: rename this appropriately, perhaps to FeedbackResponse?
@dataclass
class Response:
    """Captures human response in workflow with status and optional comment."""

    status: ResponseStatus
    comment: Optional[str] = None
