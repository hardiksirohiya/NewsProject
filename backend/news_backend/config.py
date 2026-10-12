import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def setting(name: str, default=None, required: bool = False):
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env and configure it."
        )
    return value


def int_setting(name: str, default: int) -> int:
    try:
        return int(setting(name, str(default)))
    except (TypeError, ValueError):
        return default
