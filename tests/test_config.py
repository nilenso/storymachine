"""Tests for config module."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from storymachine.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_with_valid_api_key(self, monkeypatch) -> None:
        """Test Settings creation with valid API key from environment."""
        test_key = "sk-test-key-123"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        settings = Settings()  # pyright: ignore[reportCallIssue]

        assert settings.openai_api_key == test_key

    def test_settings_missing_api_key_raises_validation_error(
        self, monkeypatch
    ) -> None:
        """Test that missing API key raises ValidationError."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()  # pyright: ignore[reportCallIssue]

        error_str = str(exc_info.value)
        assert "OPENAI_API_KEY" in error_str or "Field required" in error_str

    def test_settings_from_env_file(self, tmp_path: Path) -> None:
        """Test Settings loading from .env file."""
        env_file = tmp_path / ".env"
        test_key = "sk-env-file-key-456"
        env_file.write_text(f"OPENAI_API_KEY={test_key}")

        # Change to temp directory so .env is found
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            settings = Settings(_env_file=str(env_file))  # pyright: ignore[reportCallIssue]
            assert settings.openai_api_key == test_key
        finally:
            os.chdir(original_cwd)

    def test_settings_env_var_overrides_env_file(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        """Test that environment variable takes precedence over .env file."""
        env_var_key = "sk-env-var-key-789"
        env_file_key = "sk-env-file-key-123"

        # Set up .env file
        env_file = tmp_path / ".env"
        env_file.write_text(f"OPENAI_API_KEY={env_file_key}")

        # Set environment variable
        monkeypatch.setenv("OPENAI_API_KEY", env_var_key)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            settings = Settings(_env_file=str(env_file))  # pyright: ignore[reportCallIssue]
            assert settings.openai_api_key == env_var_key
        finally:
            os.chdir(original_cwd)

    def test_settings_field_is_frozen(self, monkeypatch) -> None:
        """Test that openai_api_key field is frozen (immutable)."""
        test_key = "sk-test-key-frozen"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        settings = Settings()  # pyright: ignore[reportCallIssue]

        with pytest.raises(ValidationError) as exc_info:
            settings.openai_api_key = "sk-new-key"  # type: ignore[misc]

        assert "frozen" in str(exc_info.value).lower()

    def test_settings_field_alias(self, monkeypatch) -> None:
        """Test that the field alias works correctly."""
        test_key = "sk-alias-test-key"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        settings = Settings()  # pyright: ignore[reportCallIssue]

        # Verify the field is accessible by its actual name
        assert settings.openai_api_key == test_key

        # Verify the field uses the OPENAI_API_KEY environment variable
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            # Should fail because OPENAI_API_KEY is not set
            Settings()  # pyright: ignore[reportCallIssue]

    def test_settings_empty_api_key_creates_settings(self, monkeypatch) -> None:
        """Test that empty API key creates settings (Pydantic allows empty strings)."""
        monkeypatch.setenv("OPENAI_API_KEY", "")

        settings = Settings()  # pyright: ignore[reportCallIssue]

        assert settings.openai_api_key == ""

    def test_settings_whitespace_only_api_key_creates_settings(
        self, monkeypatch
    ) -> None:
        """Test that whitespace-only API key creates settings (Pydantic allows whitespace)."""
        monkeypatch.setenv("OPENAI_API_KEY", "   ")

        settings = Settings()  # pyright: ignore[reportCallIssue]
        assert settings.openai_api_key == "   "
