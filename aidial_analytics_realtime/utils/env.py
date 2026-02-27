import os


def get_env(name: str) -> str:
    if (val := os.getenv(name)) is not None:
        return val
    raise Exception(f"{name} env variable is not set")
