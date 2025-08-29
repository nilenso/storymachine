"""Tests for story_machine module."""

from unittest.mock import MagicMock

from openai.types.responses import ResponseFunctionToolCall

from storymachine.story_machine import (
    Story,
    stories_from_project_sources,
    stories_from_tool_call,
)


class TestStory:
    """Tests for Story dataclass."""

    def test_story_string_representation(self) -> None:
        """Test Story string representation formatting."""
        title = "As a user, I want to register"
        criteria = [
            "User can enter email",
            "Email validation occurs",
            "User receives confirmation",
        ]

        story = Story(title=title, acceptance_criteria=criteria)
        result = str(story)

        assert title in result
        assert "Acceptance Criteria:" in result
        assert "- User can enter email" in result
        assert "- Email validation occurs" in result
        assert "- User receives confirmation" in result


class TestStoriesFromToolCall:
    """Tests for stories_from_tool_call function."""

    def test_stories_from_tool_call_success(
        self, mock_tool_call: ResponseFunctionToolCall
    ) -> None:
        """Test successful parsing of tool call to stories."""
        stories = stories_from_tool_call(mock_tool_call)

        assert len(stories) == 2
        assert isinstance(stories[0], Story)
        assert isinstance(stories[1], Story)
        assert stories[0].title == "As a new user, I want to register with my email"
        assert stories[1].title == "As a registered user, I want to login to my account"


class TestStoriesFromProjectSources:
    """Tests for stories_from_project_sources function."""

    def test_stories_from_project_sources_success(
        self,
        mock_openai_client: MagicMock,
        sample_prd_content: str,
        sample_tech_spec_content: str,
    ) -> None:
        """Test successful story generation from project sources."""

        stories = stories_from_project_sources(
            mock_openai_client,
            sample_prd_content,
            sample_tech_spec_content,
            "gpt-test",
        )

        assert len(stories) == 2
        assert all(isinstance(story, Story) for story in stories)

        mock_openai_client.responses.create.assert_called_once()
        call_args = mock_openai_client.responses.create.call_args

        assert call_args.kwargs["model"] == "gpt-test"
        assert call_args.kwargs["tool_choice"] == "required"
        assert call_args.kwargs["tools"][0]["name"] == "create_stories"

    def test_stories_from_project_sources_prompt_content(
        self,
        mock_openai_client: MagicMock,
        sample_prd_content: str,
        sample_tech_spec_content: str,
    ) -> None:
        """Test that prompt contains project content."""

        stories_from_project_sources(
            mock_openai_client,
            sample_prd_content,
            sample_tech_spec_content,
            "gpt-test",
        )

        call_args = mock_openai_client.responses.create.call_args
        prompt_content = call_args.kwargs["input"][0]["content"]

        assert sample_prd_content in prompt_content
        assert sample_tech_spec_content in prompt_content
