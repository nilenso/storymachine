"""Tests for implementation_context module."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from storymachine.implementation_context import (
    generate_implementation_context,
    render_context_enriched_story,
)
from storymachine.story_generator import Story


def _mk_tool_call(name: str, arguments: dict) -> MagicMock:
    call = MagicMock()
    call.type = "function_call"
    call.name = name
    call.arguments = json.dumps(arguments)
    return call


def _mk_response(*tool_calls: MagicMock) -> MagicMock:
    resp = MagicMock()
    resp.output = list(tool_calls)
    return resp


@pytest.fixture
def sample_story() -> Story:
    return Story(
        title="As a developer, I want implementation context",
        acceptance_criteria=[
            "Given a readable repo, when generating, then include files",
            "Given no matches, then state none identified",
        ],
    )


def test_repo_unreadable_returns_unreadable(sample_story: Story) -> None:
    client = MagicMock()
    ctx = generate_implementation_context(
        client=client,
        model="gpt-test",
        story=sample_story,
        tech_spec_content="Tech",
        repo_root="/definitely/not/a/real/path",
    )

    assert ctx.status == "unreadable"
    content = render_context_enriched_story(sample_story, ctx, include_block=True)
    assert "<implementation_context>" in content
    assert "Repository unreadable" in content


def test_none_identified_when_model_emits_empty(
    tmp_path: Path, sample_story: Story
) -> None:
    # Empty repo root
    client = MagicMock()
    emit = _mk_tool_call(
        "emit_implementation_context", {"files": [], "notes": "No files"}
    )
    client.responses.create.return_value = _mk_response(emit)

    ctx = generate_implementation_context(
        client=client,
        model="gpt-test",
        story=sample_story,
        tech_spec_content="Tech",
        repo_root=str(tmp_path),
    )

    assert ctx.status == "none_identified"
    rendered = render_context_enriched_story(sample_story, ctx, include_block=True)
    assert "None identified." in rendered


def test_with_files_when_model_emits_paths(tmp_path: Path, sample_story: Story) -> None:
    # Create a plausible file in repo
    src_dir = tmp_path / "src" / "storymachine"
    src_dir.mkdir(parents=True)
    (src_dir / "cli.py").write_text("print('ok')\n")

    client = MagicMock()
    # Simulate tool loop: list_paths first, then emit
    list_call = _mk_tool_call("list_paths", {"directory": "src"})
    emit = _mk_tool_call(
        "emit_implementation_context",
        {"files": ["src/storymachine/cli.py"], "notes": "Touch CLI and wiring"},
    )
    client.responses.create.side_effect = [_mk_response(list_call), _mk_response(emit)]

    ctx = generate_implementation_context(
        client=client,
        model="gpt-test",
        story=sample_story,
        tech_spec_content="Tech",
        repo_root=str(tmp_path),
    )

    assert ctx.status == "ok"
    assert any(p.endswith("cli.py") for p in ctx.files)
    rendered = render_context_enriched_story(sample_story, ctx, include_block=True)
    assert "<implementation_context>" in rendered
    assert "Potentially relevant files:" in rendered
    assert "src/storymachine/cli.py" in rendered


def test_render_without_block_when_no_repo(sample_story: Story) -> None:
    rendered = render_context_enriched_story(sample_story, None, include_block=False)
    assert "<implementation_context>" not in rendered
    assert sample_story.title in rendered


def test_tool_loop_execution_list_read_emit(
    tmp_path: Path, sample_story: Story
) -> None:
    # Create a file to be read
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)
    fpath = src_dir / "example.py"
    fpath.write_text("# example file\nprint('x')\n")

    client = MagicMock()
    list_call = _mk_tool_call("list_paths", {"directory": "src", "glob": "*.py"})
    read_call = _mk_tool_call("read_file", {"path": "src/example.py", "max_bytes": 64})
    emit = _mk_tool_call(
        "emit_implementation_context",
        {"files": ["src/example.py"], "notes": "Focus here"},
    )
    client.responses.create.side_effect = [
        _mk_response(list_call),
        _mk_response(read_call),
        _mk_response(emit),
    ]

    ctx = generate_implementation_context(
        client=client,
        model="gpt-test",
        story=sample_story,
        tech_spec_content="Tech",
        repo_root=str(tmp_path),
    )

    assert ctx.status == "ok"
    assert ctx.files == ["src/example.py"]
