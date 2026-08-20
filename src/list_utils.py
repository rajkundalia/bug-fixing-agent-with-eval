"""src/list_utils.py"""


def flatten(items: list) -> list:
    """Recursively flatten a nested list."""
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def remove_duplicates(items: list) -> list:
    """Return items with duplicates removed."""
    return list(set(items))
