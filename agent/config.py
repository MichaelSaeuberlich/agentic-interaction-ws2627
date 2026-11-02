"""Configuration: reads .env and environment variables. No default values in code."""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REQUIRED = ("OPENAI_BASE_URL", "MODEL", "OPENAI_API_KEY", "DATA_BASE_URL")


@dataclass(frozen=True)
class Config:
    base_url: str
    model: str
    api_key: str
    data_base_url: str


def load_config() -> Config:
    # The .env file lives in the repository root (one level above agent/).
    env_file = Path(__file__).resolve().parent.parent / ".env"
    # override=False (the default): variables that are already set take precedence.
    load_dotenv(env_file)

    values = {name: os.environ.get(name, "").strip() for name in REQUIRED}
    # An empty value counts as missing.
    missing = [name for name, value in values.items() if not value]
    if missing:
        print(
            f"Error: missing settings: {', '.join(missing)}\n"
            "Define them in .env (template: .env.example) or set them as environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    return Config(
        base_url=values["OPENAI_BASE_URL"],
        model=values["MODEL"],
        api_key=values["OPENAI_API_KEY"],
        # Strip a trailing slash to avoid double slashes when building URLs.
        data_base_url=values["DATA_BASE_URL"].rstrip("/"),
    )