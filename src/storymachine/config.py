from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field(..., frozen=True, alias="OPENAI_API_KEY")
