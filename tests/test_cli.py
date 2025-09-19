"""Tests for cli module."""

import io
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from storymachine.cli import get_context_enriched_stories, main, slugify, spinner


def test_slugify_function() -> None:
    """Test the slugify function directly with various inputs."""

    test_cases = [
        ("As a [User], I want to Sign-Up!", "as-a-user-i-want-to-sign-up"),
        ("As a User\nI want Multiple Lines", "as-a-user"),
        ("Special@Characters#Here & There", "specialcharactershere-there"),
        ("Extra   Spaces   Here", "extra-spaces-here"),
        ("---Multiple---Dashes---", "multiple-dashes"),
    ]

    for input_title, expected_slug in test_cases:
        assert slugify(input_title) == expected_slug


class TestSpinner:
    """Tests for spinner context manager."""

    def test_spinner_starts_and_stops(self, monkeypatch) -> None:
        """Test that spinner starts and stops properly."""
        output = io.StringIO()

        with monkeypatch.context():
            monkeypatch.setattr("time.sleep", lambda _: None)
            with spinner("Testing", delay=0.01, stream=output):
                time.sleep(0.05)

        result = output.getvalue()
        assert "Testing" in result

    def test_spinner_handles_exception(self, monkeypatch) -> None:
        """Test that spinner stops properly even when exception occurs."""
        output = io.StringIO()

        with monkeypatch.context():
            monkeypatch.setattr("time.sleep", lambda _: None)
            with pytest.raises(ValueError):
                with spinner("Error Test", delay=0.01, stream=output):
                    raise ValueError("Test exception")

        # Spinner should still clean up (cursor should be shown again)
        result = output.getvalue()
        assert "Error Test" in result

    def test_spinner_custom_text_and_delay(self, monkeypatch) -> None:
        """Test spinner with custom text and delay."""
        output = io.StringIO()
        custom_text = "Custom Loading Message"

        with monkeypatch.context():
            monkeypatch.setattr("time.sleep", lambda _: None)
            with spinner(custom_text, delay=0.01, stream=output):
                time.sleep(0.05)

        result = output.getvalue()
        assert custom_text in result


class TestGetContextEnrichedStories:
    """Tests for get_context_enriched_stories function."""

    def test_get_context_enriched_stories_success(
        self,
        mock_openai_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful story generation and file creation."""

        prd_file = tmp_path / "prd.md"
        tech_spec_file = tmp_path / "tech_spec.md"

        prd_file.write_text("PRD content")
        tech_spec_file.write_text("Tech spec content")

        result = get_context_enriched_stories(
            mock_openai_client, str(prd_file), str(tech_spec_file), str(tmp_path)
        )
        written_files = list(tmp_path.iterdir())

        assert len(result) == 2
        assert (
            result[0]["filename"]
            == "01-as-a-new-user-i-want-to-register-with-my-email.md"
        )
        assert (
            result[1]["filename"]
            == "02-as-a-registered-user-i-want-to-login-to-my-account.md"
        )

        # Verify files were actually written to disk
        assert (
            len(
                [
                    f
                    for f in written_files
                    if f.suffix == ".md" and f.stem.startswith("01-")
                ]
            )
            == 1
        )
        assert (
            len(
                [
                    f
                    for f in written_files
                    if f.suffix == ".md" and f.stem.startswith("02-")
                ]
            )
            == 1
        )

        mock_openai_client.responses.create.assert_called_once()

    def test_get_context_enriched_stories_includes_block_when_repo(
        self,
        mock_openai_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Ensure implementation context block is included when repo provided."""

        prd_file = tmp_path / "prd.md"
        tech_file = tmp_path / "tech.md"
        prd_file.write_text("PRD")
        tech_file.write_text("TECH")

        repo = tmp_path / "repo"
        src = repo / "src" / "storymachine"
        src.mkdir(parents=True)
        (src / "cli.py").write_text("# placeholder\n")

        create = MagicMock()
        create.type = "function_call"
        create.name = "create_stories"
        create.arguments = json.dumps(
            {
                "stories": [
                    {
                        "title": "As a user",
                        "acceptance_criteria": ["A", "B"],
                    }
                ]
            }
        )

        emit = MagicMock()
        emit.type = "function_call"
        emit.name = "emit_implementation_context"
        emit.arguments = json.dumps(
            {"files": ["src/storymachine/cli.py"], "notes": "Edit CLI"}
        )

        mock_openai_client.responses.create.side_effect = [
            MagicMock(output=[create]),
            MagicMock(output=[emit]),
        ]

        result = get_context_enriched_stories(
            mock_openai_client,
            str(prd_file),
            str(tech_file),
            str(tmp_path),
            "gpt-test",
            str(repo),
        )

        assert len(result) >= 1
        content = result[0]["content"]
        assert "<implementation_context>" in content
        assert "src/storymachine/cli.py" in content


def test_main_parses_args_and_ingests_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test main() argument parsing and end-to-end ingestion/printing path."""
    prd_file = tmp_path / "prd.md"
    tech_spec_file = tmp_path / "tech_spec.md"
    prd_file.write_text("PRD content")
    tech_spec_file.write_text("Tech spec content")

    fake_stories = [
        {"filename": "01-as-a-user.md", "content": "Story 1 content"},
        {"filename": "02-as-another-user.md", "content": "Story 2 content"},
    ]
    called: dict[str, str] = {}

    def fake_get_context_enriched_stories(
        client,
        prd_path: str,
        tech_spec_path: str,
        target_dir: str = ".",
        model: str = "gpt-5",
    ) -> list[dict[str, str]]:
        called["client"] = str(type(client))
        called["prd_path"] = prd_path
        called["tech_spec_path"] = tech_spec_path
        called["target_dir"] = target_dir
        called["model"] = model
        return fake_stories

    with monkeypatch.context():
        # Provide required API key and avoid constructing a real OpenAI client
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("MODEL", "gpt-test")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        # Stub story generation to isolate argument parsing + ingestion
        monkeypatch.setattr(
            "storymachine.cli.get_context_enriched_stories",
            fake_get_context_enriched_stories,
        )
        # Simulate CLI args
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(tech_spec_file),
                "--target-dir",
                str(tmp_path),
            ],
        )

        main()

    out = capsys.readouterr().out

    # Ensure arguments were parsed and forwarded correctly
    assert called["prd_path"] == str(prd_file)
    assert called["tech_spec_path"] == str(tech_spec_file)
    assert called["target_dir"] == str(tmp_path)
    assert called["model"] == "gpt-test"

    # Verify expected output structure
    assert "Successfully created:" in out
    assert "1. 01-as-a-user.md" in out
    assert "2. 02-as-another-user.md" in out
    assert "01-as-a-user.md" in out
    assert "~" * len("01-as-a-user.md") in out
    assert "Story 1 content" in out
    assert "Story 2 content" in out


def test_main_parses_repo_and_forwards(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure repo argument is forwarded to story generation."""
    called: dict[str, object] = {}

    def fake_get_context_enriched_stories(
        client: object,
        prd_path: str,
        tech_spec_path: str,
        target_dir: str,
        model: str,
        repo_path: str | None = None,
    ) -> list[dict[str, str]]:
        called["client"] = str(type(client))
        called["prd_path"] = prd_path
        called["tech_spec_path"] = tech_spec_path
        called["target_dir"] = target_dir
        called["model"] = model
        called["repo_path"] = repo_path
        return [
            {"filename": "01-a.md", "content": "Story 1"},
            {"filename": "02-b.md", "content": "Story 2"},
        ]

    prd_file = tmp_path / "prd.md"
    tech_spec_file = tmp_path / "tech_spec.md"
    repo_dir = tmp_path / "repo"
    prd_file.write_text("PRD")
    tech_spec_file.write_text("TECH")
    repo_dir.mkdir()

    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("MODEL", "gpt-test")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            "storymachine.cli.get_context_enriched_stories",
            fake_get_context_enriched_stories,
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(tech_spec_file),
                "--target-dir",
                str(tmp_path),
                "--repo",
                str(repo_dir),
            ],
        )

        main()

    assert called["repo_path"] == str(repo_dir)


def test_main_missing_required_args_shows_usage(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits with usage when required args are missing."""
    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(sys, "argv", ["storymachine"])

        with pytest.raises(SystemExit) as excinfo:
            main()

    # Argparse uses exit code 2 for parsing errors
    assert excinfo.value.code != 0

    err = capsys.readouterr().err.lower()
    assert "usage:" in err
    assert "--prd" in err
    assert "--tech-spec" in err


def test_main_missing_prd_file_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits when PRD file is missing."""
    # Only create tech spec file
    tech_spec_file = tmp_path / "tech_spec.md"
    tech_spec_file.write_text("Tech spec content")

    missing_prd = tmp_path / "prd.md"

    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(missing_prd),
                "--tech-spec",
                str(tech_spec_file),
                "--target-dir",
                str(tmp_path),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert f"Error: PRD file not found: {missing_prd}" in err


def test_main_missing_tech_spec_file_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits when tech spec file is missing."""
    # Only create PRD file
    prd_file = tmp_path / "prd.md"
    prd_file.write_text("PRD content")

    missing_tech = tmp_path / "tech_spec.md"

    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(missing_tech),
                "--target-dir",
                str(tmp_path),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert f"Error: Tech spec file not found: {missing_tech}" in err


def test_main_nonexistent_target_dir_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits when target directory doesn't exist."""
    # Create both input files
    prd_file = tmp_path / "prd.md"
    tech_spec_file = tmp_path / "tech_spec.md"
    prd_file.write_text("PRD content")
    tech_spec_file.write_text("Tech spec content")

    # Use non-existent target directory
    nonexistent_dir = tmp_path / "nonexistent"

    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(tech_spec_file),
                "--target-dir",
                str(nonexistent_dir),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert f"Error: Target directory not found: {nonexistent_dir}" in err


def test_main_target_is_file_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits when target path is a file, not a directory."""
    # Create both input files
    prd_file = tmp_path / "prd.md"
    tech_spec_file = tmp_path / "tech_spec.md"
    target_file = tmp_path / "target.txt"

    prd_file.write_text("PRD content")
    tech_spec_file.write_text("Tech spec content")
    target_file.write_text("This is a file, not a directory")

    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setattr(
            "storymachine.cli.OpenAI", MagicMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(tech_spec_file),
                "--target-dir",
                str(target_file),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert f"Error: Target path is not a directory: {target_file}" in err
