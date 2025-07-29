def is_string(val):
    return isinstance(val, str)


def is_number(val):
    return isinstance(val, int) or isinstance(val, float)


def is_bool(val):
    return isinstance(val, bool)
