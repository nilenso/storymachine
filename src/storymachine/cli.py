import argparse
import itertools
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from .types import WorkflowInput
from .workflow import w1
from .config import Settings


@contextmanager
def spinner(text="Loading", delay=0.1, stream=sys.stderr):
    stop = Event()

    def run():
        stream.write("\x1b[?25l")  # hide cursor
        for c in itertools.cycle("|/-\\"):
            if stop.is_set():
                break
            stream.write(f"\r{c} {text}")
            stream.flush()
            time.sleep(delay)

    t = Thread(target=run, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join()
        stream.write("\r\x1b[2K\x1b[?25h")  # clear line + show cursor
        stream.flush()


def slugify(title: str) -> str:
    slug = (
        title.split("\n")[0].lower().replace(" ", "-").replace("[", "").replace("]", "")
    )
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    return "-".join(filter(None, slug.split("-")))


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

    args = parser.parse_args()

    prd_path = Path(args.prd)
    tech_spec_path = Path(args.tech_spec)

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
    )

    # Display current configuration
    settings = Settings()  # pyright: ignore[reportCallIssue]
    print(f"Model: {settings.model}")
    print(f"Reasoning Effort: {settings.reasoning_effort}")
    print()

    w1(workflow_input)


if __name__ == "__main__":
    main()
