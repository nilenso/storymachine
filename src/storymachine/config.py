from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # TODO: memoize settings so it's only ever read once
    openai_api_key: str = Field(..., frozen=True, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(None, frozen=True, alias="ANTHROPIC_API_KEY")
    github_token: str | None = Field(None, frozen=True, alias="GITHUB_TOKEN")
    gitlab_token: str | None = Field(None, frozen=True, alias="GITLAB_TOKEN")
    model: str = Field("gpt-5", alias="MODEL")
    reasoning_effort: str = Field("low", alias="REASONING_EFFORT")

    class Config:
        env_file = ".env"
