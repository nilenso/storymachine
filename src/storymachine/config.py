from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # TODO: memoize settings so it's only ever read once
    openai_api_key: str = Field(..., frozen=True, alias="OPENAI_API_KEY")
    model: str = Field("gpt-5", alias="MODEL")
    reasoning_effort: str = Field("low", alias="REASONING_EFFORT")

    class Config:
        env_file = ".env"
