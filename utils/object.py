# utils/object.py
from typing import Any


def IsString(val: Any) -> bool:
    """Check if value is a string."""
    return isinstance(val, str)


def IsNumber(val: Any) -> bool:
    """Check if value is int or float."""
    return isinstance(val, (int, float))


def IsBool(val: Any) -> bool:
    """Check if value is a boolean."""
    return isinstance(val, bool)


def IsDict(val: Any) -> bool:
    """Check if value is a dictionary."""
    return isinstance(val, dict)


def IsList(val: Any) -> bool:
    """Check if value is a list."""
    return isinstance(val, list)
