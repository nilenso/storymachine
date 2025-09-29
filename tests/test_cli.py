"""Tests for cli module."""

import sys
from pathlib import Path

import pytest

from storymachine.cli import main


def test_main_parses_args_and_ingests_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test main() argument parsing and end-to-end ingestion/printing path."""
    prd_file = tmp_path / "prd.md"
    tech_spec_file = tmp_path / "tech_spec.md"
    prd_file.write_text("PRD content")
    tech_spec_file.write_text("Tech spec content")

    called: dict[str, str] = {}

    def fake_w1(workflow_input):
        called["prd_content"] = str("PRD content" in workflow_input.prd_content)
        called["tech_spec_content"] = str(
            "Tech spec content" in workflow_input.tech_spec_content
        )
        return []

    with monkeypatch.context():
        # Provide required API key and avoid constructing a real OpenAI client
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("MODEL", "gpt-test")
        # Stub workflow to isolate argument parsing
        monkeypatch.setattr(
            "storymachine.cli.w1",
            fake_w1,
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
            ],
        )

        main()

    out = capsys.readouterr().out

    # Ensure arguments were parsed and workflow was called with content
    assert called["prd_content"] == "True"
    assert called["tech_spec_content"] == "True"

    # Verify expected output structure
    assert "Model:" in out


def test_main_missing_required_args_shows_usage(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main() exits with usage when required args are missing."""
    with monkeypatch.context():
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
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
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(missing_prd),
                "--tech-spec",
                str(tech_spec_file),
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
            sys,
            "argv",
            [
                "storymachine",
                "--prd",
                str(prd_file),
                "--tech-spec",
                str(missing_tech),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert f"Error: Tech spec file not found: {missing_tech}" in err
