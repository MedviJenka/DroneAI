import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Config(BaseSettings):
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')


Config = Config()
