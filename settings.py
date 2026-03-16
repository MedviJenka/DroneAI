import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Config(BaseSettings):
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')
    LOGFIRE_TOKEN:  str = os.getenv('LOGFIRE_TOKEN')


Config = Config()
