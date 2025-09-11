"""Tests for story_machine module."""

from unittest.mock import MagicMock

from openai.types.responses import ResponseFunctionToolCall

from storymachine.story_machine import (
    Story,
    supports_reasoning_parameters,
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


class TestSupportsReasoningParameters:
    """Tests for _supports_reasoning_parameters function."""

    def test_reasoning_capable_models_exact_match(self) -> None:
        """Test that exact reasoning model names return True."""
        reasoning_models = [
            "o1-preview",
            "o1-mini",
            "o1",
            "o3-mini",
            "o3",
            "o4-mini",
            "codex-mini-latest",
        ]

        for model in reasoning_models:
            assert supports_reasoning_parameters(model), (
                f"Model {model} should support reasoning"
            )

    def test_regular_chat_models_return_false(self) -> None:
        """Test that regular chat models return False."""
        regular_models = [
            "gpt-4o",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "text-davinci-003",
            "text-davinci-002",
        ]

        for model in regular_models:
            assert not supports_reasoning_parameters(model), (
                f"Model {model} should not support reasoning"
            )

    def test_prefix_matching_reasoning_models(self) -> None:
        """Test that prefix matching works for reasoning model families."""
        prefix_models = [
            "o1-custom",
            "o1-future-version",
            "o3-preview",
            "o3-custom",
            "o4-preview",
            "codex-custom",
        ]

        for model in prefix_models:
            assert supports_reasoning_parameters(model), (
                f"Model {model} should support reasoning via prefix"
            )

    def test_edge_cases(self) -> None:
        """Test edge cases and invalid inputs."""
        edge_cases = [
            "",
            "unknown-model",
            "gpt-4o1",
            "gpt-5-chat",
            "gpt-5-mini",
            "gpt-5-nano",
            "o2-preview",
            "codex",
        ]

        for model in edge_cases:
            assert not supports_reasoning_parameters(model), (
                f"Model {model} should not support reasoning"
            )
