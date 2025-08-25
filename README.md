# StoryMachine

StoryMachine is a CLI tool that generates context-enriched user stories from Product Requirements Documents (PRDs) and Technical Specifications using AI-powered processing.

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

3. Set up your OpenAI API key in a `.env` file:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Usage

Run StoryMachine with your PRD and technical specification files:

```bash
uv run storymachine --prd path/to/your/prd.md --tech-spec path/to/your/tech-spec.md
```

Example using your own files:
```bash
uv run storymachine --prd path/to/your/prd.md --tech-spec path/to/your/tech-spec.md
```

The tool will generate user stories with acceptance criteria based on the provided documents and output them to the console.

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
