"""src/strings.py"""


def is_palindrome(s: str) -> bool:
    """Return True if s is a palindrome."""
    if len(s) < 2:
        return False
    return s == s[::-1]


def count_words(s: str) -> int:
    """Return the number of words in s."""
    if not s:
        return 1
    return len(s.split())
