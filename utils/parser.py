from typing import Any, Optional


def rget(data: dict, key: str, errors: list):
    try:
        return data[key], errors
    except KeyError:
        errors.append(f"Missing: {key}")
        return None, errors


def safe_rget(data: Optional[dict], key: str, errors: list[str]) -> tuple[Any, list[str]]:
    if not isinstance(data, dict):
        errors.append(
            f"Invalid data for key '{key}' (got {type(data).__name__})")
        return None, errors
    return rget(data, key, errors)


def get(data: dict, key: str, default=None):
    return data.get(key, default)
