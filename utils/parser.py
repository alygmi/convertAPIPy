def rget(data: dict, key: str, errors: list):
    try:
        return data[key], errors
    except KeyError:
        errors.append(f"Missing: {key}")
        return None, errors


def get(data: dict, key: str, default=None):
    return data.get(key, default)
