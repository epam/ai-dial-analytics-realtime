import os
from typing import Optional


def get_env(name: str, err_msg: Optional[str] = None) -> str:
    if (val := os.getenv(name)) is not None:
        return val
    raise Exception(err_msg or f"{name} env variable is not set")
