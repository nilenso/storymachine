import argparse
import asyncio
import sys
from pathlib import Path
from .types import WorkflowInput
from .workflow import w1
from .config import Settings


def main():
    """Main CLI entry point for StoryMachine."""

    parser = argparse.ArgumentParser(
        description="StoryMachine - Generate context-enriched user stories from PRD and tech spec"
    )
    parser.add_argument(
        "--prd",
        type=str,
        required=True,
        help="Path to the Product Requirements Document (PRD) file",
    )
    parser.add_argument(
        "--tech-spec",
        type=str,
        required=True,
        help="Path to the Technical Specification file",
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="GitHub repository URL (e.g., https://github.com/owner/repo)",
    )

    args = parser.parse_args()

    prd_path = Path(args.prd)
    tech_spec_path = Path(args.tech_spec)
    repo_url = args.repo

    if not prd_path.exists():
        print(f"Error: PRD file not found: {prd_path}", file=sys.stderr)
        sys.exit(1)

    if not tech_spec_path.exists():
        print(f"Error: Tech spec file not found: {tech_spec_path}", file=sys.stderr)
        sys.exit(1)

    # Read file contents and create workflow input
    prd_content = prd_path.read_text()
    tech_spec_content = tech_spec_path.read_text()
    workflow_input = WorkflowInput(
        prd_content=prd_content,
        tech_spec_content=tech_spec_content,
        repo_url=repo_url,
    )

    # Display current configuration
    settings = Settings()  # pyright: ignore[reportCallIssue]
    print(f"Model: {settings.model}")
    print(f"Reasoning Effort: {settings.reasoning_effort}")
    print()

    asyncio.run(w1(workflow_input))


if __name__ == "__main__":
    main()
