"""Allows us to take all the environment variables and map them into a Python object that we can use
and reference throughout the code

Make sure that the environment file and the config file match OR your code will not run properly"""


# Prepare the environment
from typing import List
from pydantic_settings import BaseSettings #Python library that allows for advanced type handling and map data into Python object
from pydantic import field_validator

# A class that inherit from the base settings from pydantic
class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str

    ALLOWED_ORIGINS: str = ""
    OPENAI_API_KEY: str

    # Replaces whatever we had before with the field validated allowed origins which will be either an empty list of
    # a list containing the allowed origins that were separated by commas
    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v:str) -> List[str]:
        return v.split(",") if v else []

    # Setting the configuration file so that Python knows how to correctly load the environment variable file
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()