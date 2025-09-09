# StoryMachine Makefile
# Self-documenting makefile - targets include usage descriptions

.DEFAULT_GOAL := help
.PHONY: help setup run clean build

help: ## Display this help message
	@echo "StoryMachine - Available targets:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install uv if not present and sync dependencies
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "Please restart your shell or run: source ~/.bashrc"; \
	else \
		echo "uv is already installed"; \
	fi
	uv sync

run: ## Run storymachine CLI (modify PRD and tech-spec paths as needed)
	@echo "Example run - modify paths as needed:"
	@echo "uv run storymachine --prd path/to/your/prd.md --tech-spec path/to/your/tech-spec.md"
	@echo
	@echo "Usage: uv run storymachine --help"
	uv run storymachine --help

clean: ## Remove Python cache files and build artifacts
	@echo "Cleaning up Python artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage dist/ .ruff_cache/
	@echo "Clean complete"

build: clean ## Clean, format, check types/lint, and run tests
	@echo "Running build pipeline..."
	uv run --frozen ruff format .
	uv run --frozen ruff check . --fix
	uv run --frozen pyright
	uv run --frozen pytest
	@echo "Build complete"