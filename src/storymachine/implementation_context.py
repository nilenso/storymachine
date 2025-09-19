import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, cast

from openai import OpenAI
from openai.types.responses import ResponseInputParam, ToolParam

from .story_generator import Story, supports_reasoning_parameters

ImplementationContextStatus = Literal["ok", "none_identified", "unreadable", "disabled"]


@dataclass
class ImplementationContext:
    """Structured implementation context for a story.

    Attributes:
        status: Status of the context generation.
        files: A list of repo-relative file paths to touch.
        notes: Brief instructions or pointers to implementation details.
    """

    status: ImplementationContextStatus
    files: List[str]
    notes: str


def render_context_enriched_story(
    story: Story, impl_ctx: Optional[ImplementationContext], include_block: bool
) -> str:
    """Render a story with an optional <implementation_context> block.

    If include_block is False, returns the plain story representation. When True, includes a block that
    reflects the status in ``impl_ctx``.
    """
    base = f"<user_story>\n{story}\n</user_story>"
    if not include_block:
        return base

    assert impl_ctx is not None  # include_block implies a context instance is provided

    lines: List[str] = [base.rstrip(), "", "<implementation_context>"]

    if impl_ctx.status == "ok" and impl_ctx.files:
        lines.append("Potentially relevant files:")
        for f in impl_ctx.files:
            lines.append(f"- {f}")
        if impl_ctx.notes.strip():
            lines.append("")
            lines.append("Notes:")
            for note_line in impl_ctx.notes.strip().splitlines():
                lines.append(f"{note_line.strip()}")
    elif impl_ctx.status == "none_identified":
        lines.append("None identified.")
    elif impl_ctx.status == "unreadable":
        msg = impl_ctx.notes or "Repository unreadable"
        lines.append(f"Repository unreadable: {msg}")
    elif impl_ctx.status == "disabled":
        # Should not occur when include_block is True, but keep safe fallback
        lines.append("Context generation disabled.")
    else:
        # Unknown state fallback
        lines.append("None identified.")

    lines.append("</implementation_context>")
    lines.append("")
    return "\n".join(lines)


def generate_implementation_context(
    *,
    client: OpenAI,
    model: str,
    story: Story,
    tech_spec_content: str,
    repo_root: str,
    max_tool_calls: int = 20,
) -> ImplementationContext:
    """Generate implementation context for a story using model + tools.

    Handles four cases per acceptance criteria via status:
    - ok: repo readable and at least one relevant file identified
    - none_identified: repo readable but no relevant files found
    - unreadable: repo path invalid or unreadable (errors captured)
    - disabled: not used here; reserved for callers that skip generation
    """
    root = Path(repo_root)

    # Pre-validate repository path readability
    try:
        if not root.exists() or not root.is_dir():
            return ImplementationContext(
                status="unreadable",
                files=[],
                notes="Path does not exist or is not a directory",
            )
        # Attempt to list once to trigger permission errors early
        _ = next(root.iterdir(), None)
    except (OSError, PermissionError) as exc:
        return ImplementationContext(status="unreadable", files=[], notes=str(exc))

    # Tool-calling orchestration
    messages: List[Any] = [
        {
            "role": "user",
            "content": _build_impl_prompt(story, tech_spec_content),
        }
    ]

    tools: List[ToolParam] = [
        _tool_list_paths(),
        _tool_read_file(),
        _tool_emit_impl_context(),
    ]

    observed_paths: List[str] = []

    for _ in range(max_tool_calls):
        request_params = {
            "model": model,
            "tools": tools,
            "input": cast(ResponseInputParam, messages),
            "tool_choice": "auto",
        }
        if supports_reasoning_parameters(model):
            request_params["reasoning"] = {"effort": "low"}
            request_params["text"] = {"verbosity": "low"}

        response = client.responses.create(**request_params)  # type: ignore[reportCallIssue]
        # 2) Accumulate model output items back into the input list
        if hasattr(response, "output"):
            messages.extend(getattr(response, "output"))

        tool_calls = [
            item
            for item in getattr(response, "output", [])
            if getattr(item, "type", "") == "function_call"
        ]
        if not tool_calls:
            break

        for call in tool_calls:
            name = getattr(call, "name", "")
            try:
                args = json.loads(getattr(call, "arguments", "{}"))
            except json.JSONDecodeError:
                args = {}

            if name == "list_paths":
                result = _exec_list_paths(root, args)
                paths: List[str] = cast(List[str], result.get("paths", []))
                observed_paths.extend(paths)
                call_id = getattr(call, "call_id", None)
                if call_id:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps(result),
                        }
                    )
            elif name == "read_file":
                result = _exec_read_file(root, args)
                call_id = getattr(call, "call_id", None)
                if call_id:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps(result),
                        }
                    )
            elif name == "emit_implementation_context":
                files = [
                    p for p in args.get("files", []) if isinstance(p, str) and p.strip()
                ]
                notes = str(args.get("notes", ""))
                status: ImplementationContextStatus = (
                    "ok" if files else "none_identified"
                )
                return ImplementationContext(status=status, files=files, notes=notes)
            else:
                # Unknown tool name; respond with a no-op output only if call_id exists
                call_id = getattr(call, "call_id", None)
                if call_id:
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps({"ignored": True}),
                        }
                    )

        # Loop continues with updated messages (messages already extended)

    if observed_paths:
        unique = []
        for p in observed_paths:
            if p not in unique:
                unique.append(p)
        return ImplementationContext(
            status="ok", files=unique[:5], notes="Observed during tool calls"
        )

    return ImplementationContext(status="none_identified", files=[], notes="")


def _build_impl_prompt(story: Story, tech_spec: str) -> str:
    return f"""
<task>
Given the story card, and relevant sections tech spec, can you come up with an detailed implementation strategy?
</task>

<context_gathering>
Use list_paths and read_file to explore under the provided repository root.
Select a minimal set of concrete files that need to be changed.
When done, call emit_implementation_context with files and notes.
</context_gathering>

<sources>
<story>
{story}
</story>

<tech_spec>
{tech_spec}
</tech_spec>
</sources>

<desired_result>
The implementation strategy should be fairly high level: do not suggest code changes directly, instead explain at a high level where one must investigate to make the changes required to meet the acceptance criteria. It must focus on "what is the needed to be done" rather than "how to do it".

Also include the documentation that needs to be looked up and studied to correctly implement the changes.
</desired_result>
"""


def _relativize(root: Path, p: Path | str) -> str:
    try:
        return str(Path(p).relative_to(root))
    except ValueError:
        return str(p)


def _heuristic_candidates(root: Path) -> List[Path]:
    preferred_dirs = [
        "src",
        "app",
        "server",
        "api",
        "routes",
        "models",
        "schemas",
        "services",
        "tests",
    ]
    filenames = {"cli.py", "story_generator.py", "pyproject.toml"}
    ignore_dirs = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}

    results: List[Path] = []
    for base in preferred_dirs:
        base_path = root / base
        if not base_path.exists():
            continue
        for path, _, files in os.walk(base_path):
            rel = Path(path)
            parts = set(rel.parts)
            if parts & ignore_dirs:
                continue
            depth = len(rel.relative_to(root).parts)
            if depth > 6:
                continue
            for f in files:
                if f.startswith("."):
                    continue
                if f in filenames or f.endswith(".py"):
                    results.append(Path(path) / f)
            if len(results) >= 200:
                return results
    # Also check project root for key files
    for f in filenames:
        p = root / f
        if p.exists():
            results.append(p)
    return results


def _tool_list_paths() -> ToolParam:
    return cast(
        ToolParam,
        {
            "type": "function",
            "name": "list_paths",
            "strict": True,
            "description": "List repo-relative paths under a directory.",
            "parameters": {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": ["directory"],
                "additionalProperties": False,
            },
        },
    )


def _tool_read_file() -> ToolParam:
    return cast(
        ToolParam,
        {
            "type": "function",
            "name": "read_file",
            "strict": True,
            "description": "Read a repo-relative file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    )


def _tool_emit_impl_context() -> ToolParam:
    return cast(
        ToolParam,
        {
            "type": "function",
            "name": "emit_implementation_context",
            "strict": True,
            "description": "Emit the final implementation context and stop tool-calling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": ["files", "notes"],
                "additionalProperties": False,
            },
        },
    )


def _safe_join(root: Path, part: str) -> Optional[Path]:
    p = (root / part).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    return p


def _exec_list_paths(root: Path, args: Dict[str, object]) -> Dict[str, object]:
    directory = str(args.get("directory", ""))
    max_results = 200
    max_depth = 6

    base = _safe_join(root, directory) if directory else root
    if base is None or not base.exists() or not base.is_dir():
        return {"paths": []}

    ignore_dirs = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
    results: List[str] = []
    for path, dirs, files in os.walk(base):
        rel = Path(path)
        # Filter ignored dirs in-place to prune traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        depth = len(rel.relative_to(root).parts)
        if depth > max_depth:
            continue
        names: Iterable[str] = files
        for name in names:
            if name.startswith("."):
                continue
            p = Path(path) / name
            rp = _relativize(root, p)
            results.append(rp)
            if len(results) >= max_results:
                return {"paths": results}
    return {"paths": results}


def _exec_read_file(root: Path, args: Dict[str, object]) -> Dict[str, object]:
    rel_path = str(args.get("path", ""))

    target = _safe_join(root, rel_path)
    if target is None or not target.exists() or not target.is_file():
        return {"content": "", "truncated": False}

    try:
        text = target.read_text(errors="ignore")
    except (OSError, PermissionError):
        return {"content": "", "truncated": False}

    truncated = False
    encoded = text.encode("utf-8")
    max_bytes = 65536
    if len(encoded) > max_bytes:
        truncated = True
        # Truncate by bytes boundary roughly
        text = encoded[:max_bytes].decode("utf-8", errors="ignore")

    return {"content": text, "truncated": truncated}
