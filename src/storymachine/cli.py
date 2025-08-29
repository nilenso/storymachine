import argparse
import itertools
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from typing import List

from openai import OpenAI

from .config import Settings
from .story_machine import stories_from_project_sources


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


def get_context_enriched_stories(
    client: OpenAI,
    prd_path: str,
    tech_spec_path: str,
    target_dir: str = ".",
    model: str = "gpt-5",
) -> List[dict[str, str]]:
    """
    Process PRD and tech spec files to generate context-enriched stories.

    Args:
        client: OpenAI client instance
        prd_path: Path to the PRD file
        tech_spec_path: Path to the tech spec file
        target_dir: Target directory for generated story files (default: current directory)
        model: The model to use (default: ``gpt-5``)

    Returns:
        List of generated story file names
    """

    prd_content = Path(prd_path).read_text()
    tech_spec_content = Path(tech_spec_path).read_text()

    stories = stories_from_project_sources(
        client, prd_content, tech_spec_content, model
    )

    def create_story_file(index: int, story) -> dict[str, str]:
        filename = f"{index:02d}-{slugify(story.title)}.md"
        target_path = Path(target_dir) / filename
        target_path.write_text(str(story))
        return {"filename": filename, "content": str(story)}

    created_files = [create_story_file(i, story) for i, story in enumerate(stories, 1)]

    return created_files


def main():
    """Main CLI entry point for StoryMachine."""

    # initialize settings
    settings = Settings(_env_file=".env")  # pyright: ignore[reportCallIssue]

    client = OpenAI(api_key=settings.openai_api_key)

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
        "--target-dir",
        type=str,
        default=".",
        help="Target directory for generated story files (default: current directory)",
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

    with spinner("Machining Stories"):
        created_stories = get_context_enriched_stories(
            client,
            str(prd_path),
            str(tech_spec_path),
            args.target_dir,
            settings.model,
        )

    for story in created_stories:
        print(story["filename"])
        print("~" * len(story["filename"]))
        print()
        print(story["content"])
        print()

    print("Successfully created:")
    for i, story in enumerate(created_stories, 1):
        print(f"{i}. {story['filename']}")


if __name__ == "__main__":
    main()
