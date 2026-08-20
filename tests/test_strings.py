"""tests/test_strings.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.strings import is_palindrome, count_words


# --- is_palindrome ---

def test_palindrome_normal():
    assert is_palindrome("racecar") is True

def test_palindrome_not():
    assert is_palindrome("hello") is False

def test_palindrome_single_char():
    assert is_palindrome("a") is True

def test_palindrome_two_chars_same():
    assert is_palindrome("aa") is True

def test_palindrome_empty():
    assert is_palindrome("") is True


# --- count_words ---

def test_count_words_normal():
    assert count_words("hello world") == 2

def test_count_words_empty():
    assert count_words("") == 0

def test_count_words_single():
    assert count_words("hello") == 1
