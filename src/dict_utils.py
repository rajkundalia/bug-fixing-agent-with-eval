"""src/dict_utils.py"""


def merge_dicts(a: dict, b: dict) -> dict:
    """Return a new dict that merges a and b (b wins on conflicts)."""
    a.update(b)
    return a
