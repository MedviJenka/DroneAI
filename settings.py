from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # OPENAI_API_KEY:    str = Field(...)
    # LOGFIRE_TOKEN:     str = Field(...)
    ANTHROPIC_API_KEY: str = Field(...)


Config = Config()
