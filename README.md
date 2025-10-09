# StoryMachine

StoryMachine is a CLI tool that generates context-enriched user stories from Product Requirements Documents (PRDs) and Technical Specifications using AI-powered processing.

> No more machine, that meant no more pictures, no more stories.
Elliot was blue.
Until he found something else, and that’s when he realised something very important…
it wasn’t the machine that was making stories… it was him.
… and he was really rather good at it.

From [Tom McLaughlin's book, The Story Machine](https://www.youtube.com/watch?v=yXVqCCeCPAU&t=9s).


## Features

- Generate user stories from PRD and technical specification documents
- AI-powered context enrichment for better story understanding
- CLI interface for easy access and integration into workflows
- Structured output with acceptance criteria following best practices

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd storymachine
```

2. Install dependencies using uv (required):
```bash
uv sync
```

3. Set up your API keys in a `.env` file:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
# For GitHub repositories:
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
# For GitLab repositories:
echo "GITLAB_TOKEN=glpat_your_token_here" >> .env
```

   **Token Requirements:**
   - **GitHub**: Create a Personal Access Token with `repo` scope (Settings → Developer settings → Personal access tokens)
   - **GitLab**: Create a Personal Access Token with `read_api` and `read_repository` scopes (User Settings → Access Tokens)

## Usage

Run StoryMachine with your PRD, technical specification, and repository URL:

**For GitHub repositories:**
```bash
uv run storymachine --prd path/to/your/prd.md --tech-spec path/to/your/tech-spec.md --repo https://github.com/owner/repo
```

**For GitLab repositories:**
```bash
uv run storymachine --prd path/to/your/prd.md --tech-spec path/to/your/tech-spec.md --repo https://gitlab.com/owner/repo
```

The tool will generate user stories with acceptance criteria based on the provided documents, work with your feedback through a workflow, and output well specified stories to the console.

## Development

This project uses:
- Python 3.13+
- uv for package management
- OpenAI API for story generation
- pydantic-settings for configuration

### Code Quality

Follow the guidelines in AGENTS.md:
- Use uv for package management
- Maintain type hints for all code
- Follow existing patterns exactly
- Run formatters before committing

### Running Tests

```bash
uv run --frozen pytest
```

## Example Output

StoryMachine generates stories in the following format:

```
Title: Generate user stories from PRD and technical specifications

Acceptance Criteria:
- The system should parse PRD documents in markdown format
- The system should parse technical specification documents in markdown format
- The system should generate user stories with clear titles
- Each user story should include relevant acceptance criteria
```
