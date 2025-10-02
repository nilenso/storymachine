"""Common types for StoryMachine workflow."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


@dataclass
class Story:
    """A user story with title and acceptance criteria."""

    title: str
    acceptance_criteria: List[str]
    enriched_context: Optional[str] = None

    def __str__(self) -> str:
        criteria_text = "\n- ".join(self.acceptance_criteria)
        result = f"Title: {self.title}\n\nAcceptance Criteria:\n- {criteria_text}\n"
        if self.enriched_context:
            result += f"\nContext:\n{self.enriched_context}\n"
        return result


@dataclass
class WorkflowInput:
    """Input data for the story generation workflow."""

    prd_content: str
    tech_spec_content: str
    repo_path: str
    repo_context: Optional[str] = None


class FeedbackStatus(Enum):
    """Status of human feedback response in workflow."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class FeedbackResponse:
    """Captures human feedback response in workflow with status and optional comment."""

    status: FeedbackStatus
    comment: Optional[str] = None
