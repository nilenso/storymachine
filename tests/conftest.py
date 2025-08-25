"""Shared fixtures and mocks for StoryMachine tests."""

import json
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest
from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall

from storymachine.story_machine import Story


@pytest.fixture
def sample_prd_content() -> str:
    """Sample PRD content for testing."""
    return """# Product Requirements Document

## Project Overview
Build a user authentication system for our web application.

## Features
- User registration with email validation
- User login with secure password handling
- Password reset functionality
- User profile management

## Success Criteria
- Users can register with valid email addresses
- Password requirements are enforced
- Secure session management is implemented
"""


@pytest.fixture
def sample_tech_spec_content() -> str:
    """Sample tech spec content for testing."""
    return """# Technical Specification

## Architecture
- RESTful API using FastAPI
- PostgreSQL database for user data
- JWT tokens for authentication
- Redis for session management

## Endpoints
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/reset-password
- GET /user/profile
- PUT /user/profile

## Database Schema
Users table with fields: id, email, password_hash, created_at, updated_at
"""


@pytest.fixture
def sample_stories() -> List[Story]:
    """Sample Story objects for testing."""
    return [
        Story(
            title="As a new user, I want to register with my email",
            acceptance_criteria=[
                "User can enter email and password on registration form",
                "Email validation is performed",
                "Password strength requirements are enforced",
                "Confirmation email is sent upon successful registration",
            ],
        ),
        Story(
            title="As a registered user, I want to login to my account",
            acceptance_criteria=[
                "User can enter email and password on login form",
                "Credentials are validated against database",
                "JWT token is generated for valid login",
                "User is redirected to dashboard upon successful login",
            ],
        ),
    ]


@pytest.fixture
def mock_openai_client(mock_openai_response) -> MagicMock:
    """Mock OpenAI client for testing."""
    mock_client = MagicMock(spec=OpenAI)
    mock_client.responses.create.return_value = mock_openai_response
    return mock_client


@pytest.fixture
def mock_tool_call() -> ResponseFunctionToolCall:
    """Mock OpenAI tool call response."""
    mock_tool_call = MagicMock(spec=ResponseFunctionToolCall)
    mock_tool_call.arguments = json.dumps(
        {
            "stories": [
                {
                    "title": "As a new user, I want to register with my email",
                    "acceptance_criteria": [
                        "User can enter email and password on registration form",
                        "Email validation is performed",
                        "Password strength requirements are enforced",
                    ],
                },
                {
                    "title": "As a registered user, I want to login to my account",
                    "acceptance_criteria": [
                        "User can enter email and password on login form",
                        "Credentials are validated against database",
                        "JWT token is generated for valid login",
                    ],
                },
            ]
        }
    )
    return mock_tool_call


@pytest.fixture
def mock_openai_response(mock_tool_call: ResponseFunctionToolCall) -> MagicMock:
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.output = [mock_tool_call]
    mock_tool_call.type = "function_call"
    return mock_response


@pytest.fixture
def temp_prd_file(tmp_path: Path, sample_prd_content: str) -> Path:
    """Create temporary PRD file for testing."""
    prd_file = tmp_path / "prd.md"
    prd_file.write_text(sample_prd_content)
    return prd_file


@pytest.fixture
def temp_tech_spec_file(tmp_path: Path, sample_tech_spec_content: str) -> Path:
    """Create temporary tech spec file for testing."""
    tech_spec_file = tmp_path / "tech_spec.md"
    tech_spec_file.write_text(sample_tech_spec_content)
    return tech_spec_file
