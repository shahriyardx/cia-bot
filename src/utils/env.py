import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(".env")


@dataclass
class Env:
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    TOKEN: str = os.environ["TOKEN"]
    API_HOST: str = os.environ["API_HOST"]
    API_PORT: str = os.environ["API_PORT"]


env = Env()
